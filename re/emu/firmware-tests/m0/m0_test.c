/*
 * m0_test.c — G7250-emu milestone M0 platform-spike test firmware.
 *
 * CLEAN-ROOM: this is our own test program. It contains no vendor code and
 * is derived from no vendor image. Its only purpose is to exercise the
 * Cortex-M7 features the stock G7250 firmware relies on, so the M0 spike can
 * decide whether Renode's cortex-m7 model is a GO for the project:
 *
 *   - double-precision FPU (VDIV.F64 / VADD.F64)   -> fpu_dp_ok
 *   - single-precision FPU                          -> fpu_sp_ok
 *   - MPU register model (16 regions on the H7)     -> mpu_ok / mpu_type_dregion
 *   - DWT CYCCNT cycle counter                      -> dwt_cyccnt_delta
 *   - cache-maintenance register writes as no-ops   -> cache_ok
 *   - MMIO throughput via a GPIO bit-bang loop       -> gpio_iters
 *
 * Results are written to a fixed block at the top of AXI SRAM so the Renode
 * harness can read them over the monitor and set watchpoints at known
 * addresses. Two "event" fields (phase, done) are written as single stores so
 * the harness can place watchpoints on them to timestamp the GPIO loop.
 */

#include <stdint.h>

/* ---- fixed results block: top 4 KiB of AXI SRAM (see m0.ld) ------------- */
#define M0_RESULTS_BASE 0x2407F000u

typedef struct {
    volatile uint32_t magic;             /* 0x00  'M','0','R','0' */
    volatile uint32_t phase;             /* 0x04  watchpoint: 1 = GPIO loop start */
    volatile uint32_t done;              /* 0x08  watchpoint: 0xD09E ok / 0xFA17 fault */
    volatile uint32_t gpio_iters;        /* 0x0C  MMIO writes performed */
    volatile uint32_t dwt_cyccnt_delta;  /* 0x10  cycles over the GPIO loop */
    volatile uint32_t fpu_dp_ok;         /* 0x14  */
    volatile uint32_t fpu_sp_ok;         /* 0x18  */
    volatile uint32_t mpu_ok;            /* 0x1C  */
    volatile uint32_t mpu_type_dregion;  /* 0x20  MPU_TYPE DREGION field */
    volatile uint32_t cache_ok;          /* 0x24  */
    volatile uint32_t fault_code;        /* 0x28  faulting exception number, if any */
    volatile uint32_t fpu_dp_bits_lo;    /* 0x2C  low  word of the dp result */
    volatile uint32_t fpu_dp_bits_hi;    /* 0x30  high word of the dp result */
} m0_results_t;

#define R (*(m0_results_t *)M0_RESULTS_BASE)

/* ---- Cortex-M7 / STM32H7 register addresses (from ARM/ST, public) ------- */
#define CPACR    (*(volatile uint32_t *)0xE000ED88u)   /* FPU access control */
#define DEMCR    (*(volatile uint32_t *)0xE000EDFCu)   /* bit24 TRCENA */
#define DWT_CTRL (*(volatile uint32_t *)0xE0001000u)   /* bit0 CYCCNTENA */
#define DWT_CYCCNT (*(volatile uint32_t *)0xE0001004u)

#define MPU_TYPE (*(volatile uint32_t *)0xE000ED90u)
#define MPU_CTRL (*(volatile uint32_t *)0xE000ED94u)
#define MPU_RNR  (*(volatile uint32_t *)0xE000ED98u)
#define MPU_RBAR (*(volatile uint32_t *)0xE000ED9Cu)
#define MPU_RASR (*(volatile uint32_t *)0xE000EDA0u)

/* ARMv7-M cache-maintenance registers in the SCB (no-ops on a model) */
#define SCB_ICIALLU  (*(volatile uint32_t *)0xE000EF50u)
#define SCB_DCCIMVAC (*(volatile uint32_t *)0xE000EF70u)
#define SCB_DCCISW   (*(volatile uint32_t *)0xE000EF74u)

/* GPIOA on the H7 is at 0x58020000; ODR at +0x14 (public ST reference) */
#define GPIOA_ODR (*(volatile uint32_t *)0x58020014u)

#ifndef GPIO_ITERS
#define GPIO_ITERS 20000000u
#endif

/* ---- tiny barriers (real Cortex-M instructions) ------------------------ */
static inline void dsb(void) { __asm volatile("dsb" ::: "memory"); }
static inline void isb(void) { __asm volatile("isb" ::: "memory"); }

/* Measurement markers: the Renode harness puts a PC hook on each of these
 * (one-shot) to timestamp host wall time and read ExecutedInstructions at the
 * exact start and end of the GPIO loop. noinline + used so they keep a stable
 * address and are never merged away. */
__attribute__((noinline, used)) void m0_mark_loop_start(void) { __asm volatile(""); }
__attribute__((noinline, used)) void m0_mark_done(void)       { __asm volatile(""); }

/* ---- linker symbols ---------------------------------------------------- */
extern uint32_t _sidata, _sdata, _edata, _sbss, _ebss, _estack;

void Reset_Handler(void);
void Default_Handler(void);
void Fault_Handler(void);
int  main(void);

/* ---- vector table ------------------------------------------------------ */
__attribute__((section(".isr_vector"), used))
void (*const g_vectors[])(void) = {
    (void (*)(void))(&_estack),  /* 0: initial SP */
    Reset_Handler,               /* 1: reset */
    Default_Handler,             /* 2: NMI */
    Fault_Handler,               /* 3: HardFault */
    Fault_Handler,               /* 4: MemManage */
    Fault_Handler,               /* 5: BusFault */
    Fault_Handler,               /* 6: UsageFault */
    0, 0, 0, 0,                  /* 7..10 reserved */
    Default_Handler,             /* 11: SVCall */
    Default_Handler,             /* 12: DebugMon */
    0,                           /* 13 reserved */
    Default_Handler,             /* 14: PendSV */
    Default_Handler,             /* 15: SysTick */
};

/* A fault writes a marker so the harness can tell a fault from a hang.
 * IPSR low 9 bits hold the exception number of the active fault. */
void Fault_Handler(void)
{
    uint32_t ipsr;
    __asm volatile("mrs %0, ipsr" : "=r"(ipsr));
    R.fault_code = ipsr & 0x1FFu;
    R.done = 0xFA17u;            /* "FAIL" marker */
    for (;;) { }
}

void Default_Handler(void) { for (;;) { } }

void Reset_Handler(void)
{
    /* copy .data from flash to RAM */
    uint32_t *src = &_sidata, *dst = &_sdata;
    while (dst < &_edata) { *dst++ = *src++; }
    /* zero .bss */
    for (dst = &_sbss; dst < &_ebss; ) { *dst++ = 0u; }
    (void)main();
    for (;;) { }
}

/* ---- the actual spike -------------------------------------------------- */
int main(void)
{
    R.magic = 0x3052304Du;   /* "M0R0" */
    R.done  = 0u;
    R.phase = 0u;
    R.fault_code = 0u;

    /* 1. enable the FPU (full access to CP10/CP11) before any FP op */
    CPACR |= (0xFu << 20);
    dsb(); isb();

    /* 2. DWT cycle counter */
    DEMCR    |= (1u << 24);   /* TRCENA */
    DWT_CYCCNT = 0u;
    DWT_CTRL  |= 1u;          /* CYCCNTENA */

    /* 3a. single-precision FPU */
    {
        volatile float a = 0.0f;
        for (int i = 1; i <= 50000; i++) a += 1.0f / (float)i;
        R.fpu_sp_ok = (a > 9.0f && a < 14.0f) ? 1u : 0u;
    }

    /* 3b. double-precision FPU (VDIV.F64 / VADD.F64). If the model lacks the
     *     dp-FPU these become undefined instructions -> UsageFault/HardFault
     *     -> Fault_Handler sets done = 0xFA17. */
    {
        volatile double acc = 0.0;
        for (int i = 1; i <= 100000; i++) acc += 1.0 / (double)i;
        union { double d; uint32_t w[2]; } u;
        u.d = acc;
        R.fpu_dp_bits_lo = u.w[0];
        R.fpu_dp_bits_hi = u.w[1];
        /* sum_{1..100000} 1/i ~= 12.0901 */
        R.fpu_dp_ok = (acc > 11.5 && acc < 12.7) ? 1u : 0u;
    }

    /* 4. MPU: confirm the model exposes regions and honours enable/disable */
    {
        R.mpu_type_dregion = (MPU_TYPE >> 8) & 0xFFu;
        MPU_RNR  = 0u;
        MPU_RBAR = 0x24000000u;                 /* AXI SRAM base */
        MPU_RASR = (0x10u << 1) | 1u;           /* SIZE=512KB(ish), ENABLE */
        MPU_CTRL = (1u << 2) | 1u;              /* PRIVDEFENA | ENABLE */
        dsb(); isb();
        uint32_t ok = ((MPU_CTRL & 1u) != 0u) && (R.mpu_type_dregion > 0u);
        MPU_CTRL = 0u;                          /* disable again, no side effects */
        dsb(); isb();
        R.mpu_ok = ok ? 1u : 0u;
    }

    /* 5. cache-maintenance register writes must be accepted (no-op) */
    {
        SCB_ICIALLU  = 0u;
        SCB_DCCIMVAC = 0x24000000u;
        SCB_DCCISW   = 0u;
        dsb(); isb();
        R.cache_ok = 1u;   /* reached here = no fault on the cache ops */
    }

    /* 6. MMIO throughput: GPIO bit-bang loop (dominant workload) */
    R.phase = 1u;
    uint32_t c0 = DWT_CYCCNT;
    m0_mark_loop_start();         /* PC hook: harness records host t0 + instr0 */
    for (uint32_t i = 0; i < GPIO_ITERS; i++) {
        GPIOA_ODR = i & 0xFFFFu;  /* one MMIO store per iteration; ODR is 16-bit */
    }
    uint32_t c1 = DWT_CYCCNT;
    R.gpio_iters       = GPIO_ITERS;
    R.dwt_cyccnt_delta = c1 - c0;

    /* 7. signal completion. The PC hook on m0_mark_done records host t1 +
     *    instr1 and pauses the emulation, so the measurement ends exactly here
     *    (no idle/WFI instructions pollute the counts, and there is no RunFor
     *    stall waiting on virtual time while the core is idle). */
    R.done = 0xD09Eu;             /* "DONE" marker */
    m0_mark_done();

    for (;;) { __asm volatile("wfi"); }
    return 0;
}
