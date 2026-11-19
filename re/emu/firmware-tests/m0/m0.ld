/*
 * M0 spike linker script — generic STM32H743 memory map as modelled by
 * Renode's platforms/cpus/stm32h7.repl (flash bank1 1 MiB @ 0x08000000,
 * AXI SRAM 512 KiB @ 0x24000000).
 *
 * The top 4 KiB of AXI SRAM (0x2407F000..0x2407FFFF) is reserved OUTSIDE
 * the linker's RAM region for the fixed M0 results block, so the Renode
 * harness can read it and set watchpoints at absolute addresses without
 * needing symbol lookup. The stack grows down from _estack = 0x2407F000.
 *
 * Clean-room: this is our own test firmware. No vendor code.
 */

MEMORY
{
  FLASH (rx) : ORIGIN = 0x08000000, LENGTH = 1024K
  RAM  (rwx) : ORIGIN = 0x24000000, LENGTH = 0x7F000  /* 508K; last 4K reserved */
}

_estack = 0x2407F000;   /* top of usable RAM = base of the results block */

SECTIONS
{
  .isr_vector :
  {
    KEEP(*(.isr_vector))
  } > FLASH

  .text :
  {
    *(.text*)
    *(.rodata*)
    . = ALIGN(4);
  } > FLASH

  _sidata = LOADADDR(.data);

  .data :
  {
    . = ALIGN(4);
    _sdata = .;
    *(.data*)
    . = ALIGN(4);
    _edata = .;
  } > RAM AT > FLASH

  .bss :
  {
    . = ALIGN(4);
    _sbss = .;
    *(.bss*)
    *(COMMON)
    . = ALIGN(4);
    _ebss = .;
  } > RAM

  . = ALIGN(8);
  _end = .;
}
