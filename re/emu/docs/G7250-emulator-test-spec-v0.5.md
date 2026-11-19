# G7250 emulator and automated test infrastructure — study and specification

| | |
| --- | --- |
| Version | v0.5 (draft, desk study) |
| Date | 2026-11-18 |
| Commissioned by | ON8ST |
| Primary source | repo `g7250-base` (branch `re/round5`), clean-room RE documentation of stock firmware V1.0.1 |
| Status | No firmware or emulator has been run. No firmware image, key or key material has been read or searched for. |
| Storage | This is the first version in the repo `g7250-emu`. Drafts v0.1–v0.4 lived in a temporary folder and no longer exist; their content is fully included here. |

## Version history

| Version | Main changes |
| --- | --- |
| v0.1 | First study: platform choice, machine definitions, acceptance criteria, test layers, brick gates, HIL, clean room, roadmap |
| v0.2 | No interoperability between the new firmware and stock; the bootloader and update question moves to the firmware project (§15); boot-state modeling; a clean-room hardware interface specification (HIS) |
| v0.3 | The versions of the own Main and Control do not have to match (version negotiation, graceful degradation); own Main headless (EH) is the primary target configuration; own Control is a later, optional track; ES (own Main + stock Control connected) is only a low-priority robustness and safety test; R0 (power on without panel) as top priority |
| v0.4 | §3.8 extended: the hypotheses H1/H2 for the power supply, tier-0 observations, requirements for always-on, sleep and wake, CH394 Wake-on-LAN, a PowerModel in the emulator |
| **v0.5** | **(1) The emulator decrypts nothing.** There is no longer any decryption, key configuration, or Keychain or key-file handling. The user supplies already-decrypted application images in a local folder outside any repo; the emulator reads that folder via a configuration setting and checks each image against a manifest containing only hashes and versions. The official vendor file is only kept and hashed as provenance (§4, §7, §12, §13). **(2) Sharper tier-0 cold-start observations:** the forced network defaults of stock Main (192.168.3.199), a ping as proof that the app is running, and fixed procedure rules (dummy load, no client that can key PTT) (§3.8.3, §11.4) |

---

## 0. Reading guide

### 0.1 Confidence labels

Every claim about the G7250 carries a label and, where it concerns a fact
from the RE documentation, the path of the source document.

| Label | Meaning in this document |
| --- | --- |
| **VERIFIED** | Listed as VERIFIED in the `g7250-base` documentation. That means: verified **in the firmware analysis**, not measured on hardware. |
| **HIGH** | The docs give HIGH CONFIDENCE, or it is a strong inference by this study from VERIFIED facts or from public documentation (Renode, ST, WIZnet, WCH, OpenHPSDR, TCI). |
| **HYPOTHESIS** | Unproven. This also covers everything the docs label as MEDIUM or HYPOTHESIS; that is then noted as "(docs: MEDIUM)". Public upstream reports that we have not verified ourselves are listed as "HYPOTHESIS/MEDIUM (upstream report)". |

Statements about this specification's own design choices ("the emulator
must …") are normative and carry no label. Statements about external
tools (Renode, QEMU) are HIGH if they come from public documentation,
with the caveat that they must be confirmed on the chosen version in
milestone M0.

### 0.2 Normative words

**MUST** is a hard requirement, **MUST NOT** a prohibition, **SHOULD** a
strong recommendation, **MAY** an option.

### 0.3 Abbreviations

- **Main**: the Main Unit (RF/DSP, FPGA, CH394, codec), STM32H72x/H73x.
- **Control**: the Control Unit (front panel, display, GUI, CI-V), STM32H743. Also "panel" or "head".
- **Link**: the UART between Main and Control (USART2 on both sides). Stock runs SLIP/CRC-16 over it; the NF uses its own protocol, the **NF link**.
- **Stock**: the factory firmware from Xiegu.
- **NF**: the new, clean-room developed firmware (NF-Main, and later optionally NF-Control).
- **HIS**: the clean-room hardware interface specification (§12.2).
- **Plant**: the behavior model of the analog and RF hardware around the MCUs (PA, detectors, NTC, relays, antenna/load).
- **HIL**: hardware-in-the-loop with the real G7250 on the owner's test bench.
- **VT**: virtual time of the emulator.
- **Configs**: SS (stock+stock), EH (NF-Main headless), ES (NF-Main + stock Control connected), EE (NF-Main + NF-Control); see §3.7.

### 0.4 Summary

1. **Platform: Renode.** The emulation consists of two coupled
   machines (Main and Control) in one emulation with shared virtual time,
   with peripheral models in C# and a Python harness. Of all the options,
   Renode has the best support for multi-machine, determinism,
   GDB, logging of unmodeled registers and CI. QEMU lacks H7 and
   multi-machine synchronization; a custom emulator costs too much.
2. **Baseline first.** Phase 1 delivers a reference platform on which the
   *unmodified* stock V1.0.1 of both units runs "perfectly". The
   §6 acceptance criteria make "perfect" measurable.
3. **No decryption in the emulator.** The user supplies
   decrypted application images themselves in a local folder outside any repo.
   The emulator checks them against a manifest containing only hashes and
   rejects any mismatch (§4).
4. **Critical path:** the stock+stock baseline (SS), then NF-Main headless
   (EH, the primary target config, operated via P1 and TCI from AetherSDR
   or other SDR software), then HIL with the NF-Main. The ES setup
   (NF-Main with a connected stock Control) is only a
   low-priority robustness and safety test. An own
   Control (EE) is a later, optional track (§3.7). The biggest
   risk is whether the Main can power on without Control (R0, §3.8).
5. **Biggest technical risks:** the FPGA model (bit-banged bus at
   48 kHz, unknown sample rates), the emulation speed (550 MHz Main
   with heavy float DSP), and the correct boot state without bootloader
   (§4.3).
6. **Brick prevention on the emulator side:** the NF never touches sector 0
   (bootloader) or the option bytes; the persistent state
   remains usable for stock (rollback compatibility is tested in the
   emulator); TX safety gates. The real flash procedure and the
   update path are a dependency of the firmware project (§15).
7. **Clean room:** the emulator and the golden traces of stock belong to
   the RE side. The NF is built only from the HIS, the public
   standards (P1, TCI, CI-V), the public vendor documentation and
   black-box test results.

---

## 1. Goals, scope and principles

### 1.1 Goals

| # | Goal | Measurable via |
| --- | --- | --- |
| D1 | A coupled emulation of Main and Control on which the unmodified stock firmware runs perfectly | §6 acceptance criteria |
| D2 | That emulation is the **reference platform** (baseline) and is versioned per vendor release | §7 version matrix |
| D3 | A fully automated and self-contained test framework for the NF | §8 |
| D4 | Compute and report the quality of the NF | §9 |
| D5 | Minimize the chance of a bricked real radio | §10 |
| D6 | HIL with the real G7250 on the existing test bench, in a later phase | §11 |

### 1.2 Scope

**In scope:**
- emulation of both MCUs with all peripherals the firmware
  uses, plus the external chips and a plant model;
- the coupling between both units via the link and the CTRL cable;
- the external interfaces: CI-V (serial line), Icom-LAN (stock's
  wfview-compatible network emulation), HDSDR mode, and for
  the NF also OpenHPSDR Protocol 1 and TCI;
- **reading in and checking user-supplied,
  already-decrypted application images** and the
  boot-state modeling (direct boot of the application image);
- the system configurations stock+stock and NF-Main headless (primary),
  later and optionally own+own, plus the ES test setup (§3.7);
- test layers, fault injection, quality score, release gates and the
  HIL integration.

**Out of scope:**
- **any form of decryption** of vendor files, and any key
  or key-material handling. The emulator never parses or decrypts
  the vendor update file;
- wfview as a test client: stock is driven by own
  test scripts that speak the Icom-LAN protocol and CI-V;
- any way to bypass band or power limits;
- **the bootloader and update question:** whether the vendor bootloader accepts an
  own image, how an NF image gets onto the radio,
  packaging in the vendor update format, and the update path of the NF.
  That is work for the firmware project (§15);
- interoperability between NF and stock: mixed configurations are
  not supported and not tested as compatibility (ES is only a
  safety test);
- opening the radio, measurements on the hardware and SWD access: the
  owner only does tier-0 tests (`docs/hardware_test_plan.md`);
- cycle-accurate timing. The emulator is functionally timed (§1.4).

### 1.3 The baseline idea

The stock firmware is the **oracle for the behavior of the hardware**. If
stock does everything in the emulator that the docs describe, without faults
and without hanging polling loops, then the peripheral models are good
enough. The NF then runs on those validated models.

```
 decrypted images (local folder, from the user) --> manifest check (hashes) --> Renode: Main + Control
                                                                                      |
       g7250-base docs/CSV --> models + test data ------------------------------------+
                                                                                      v
                                                     baseline suite (par. 6) --> golden traces/screenshots
                                                                                      |
 NF build --> the same models --> conformance suite (par. 8) --> quality score (par. 9) --> gates (par. 10)
```

Three consequences:
- A model may only be called "done" once stock runs perfectly on it.
- Every new vendor release is a **regression test for the emulator**:
  if stock fails, a model is the first suspect (§7).
- The NF is tested on exactly the same hardware models. A difference
  between NF and stock is therefore a property of the firmware, not
  of the emulator. Only the content on the LinkCable differs in EE (the
  own NF protocol); the physical model (USART2, byte timing, faults)
  stays the same.

### 1.4 Principles

1. **Reproducibility.** A test run is fully determined by
   a *run manifest*:
   - the hashes of the images, the emulator build and the model versions;
   - the plant parameters;
   - the seed;
   - the input stream (recording).

   The same manifest gives the same result, bit for bit.
2. **Determinism.**
   - Virtual time only. There is no wall clock in the firmware's
     path: the RTC starts at a fixed epoch.
   - Serial, deterministic execution of both machines with a
     fixed synchronization quantum.
   - All randomness via one seed.
   - Host I/O only via a timestamped input queue (§8.6).
3. **Two lanes.**
   - The **deterministic lane** runs CI, golden traces and
     gates. All test clients run there in virtual time.
   - The **live lane** has real host network access (TAP or
     UDP) and is for interactive work. It is not deterministic, but
     every session is recorded, so that it can be replayed in the deterministic
     lane.
4. **Functional timing, no cycles.** The virtual time comes from the
   instruction count, via a configured MIPS value per core.
   Caches and dual-issue are not modeled. Timing margins from the
   emulator are therefore **indicative**; the decisive measurement happens
   in HIL (§11).
5. **Strict mode.** Every access to an address that is not modeled
   or explicitly tagged is logged. In strict mode it
   makes the test fail (§5).
6. **Data-driven.** The models and test lists read the CSVs of
   `g7250-base`. That way a correction in the RE docs changes the tests
   without a code change.
7. **No firmware in git.** Images, dumps and stock-derived
   artifacts (screenshots, traces) live outside the public repo
   (§12). The emulator knows no keys and contains no
   decryption code.

---

## 2. Platform choice

### 2.1 Platform requirements

| # | Requirement | Why (G7250-specific) |
| --- | --- | --- |
| P1 | Cortex-M7 with FPv5 double precision, MPU, NVIC with more than 130 IRQs, DWT cycle counter | Both images are linked for the multilib `thumb/v7e-m+dp/hard` (VERIFIED, `docs/libraries.md`). Main uses IRQ 129/130 (BDMA) (VERIFIED, `docs/dma.md`). The constructor enables DWT for the NR statistics (VERIFIED, `main_unit/docs/startup.md`). GT911 timeouts run on the cycle counter (VERIFIED, `control_unit/docs/peripherals.md`) |
| P2 | Two machines with **shared, deterministic virtual time** | The link runs at 460 800 Bd, with a 20 ms rhythm of `0x01` and frame skips when the TX lock is busy (VERIFIED, `docs/protocol.md`) |
| P3 | Peripheral models in a higher-level language, fast enough for ~10⁷ MMIO/s | The FPGA bus is bit-banged on GPIOE, with DRDY at 48 kHz (docs: MEDIUM) |
| P4 | GDB per machine | Debugging model gaps and the NF |
| P5 | Logging of unmodeled access and tagging of registers | Gap analysis (§5) |
| P6 | Snapshots, record and replay | Golden runs, fast forking after boot |
| P7 | Headless running and CI integration | Nightly suites |
| P8 | Network to the host (TAP or UDP) | Live lane for the CH394 |
| P9 | Framebuffer capture | GUI baseline |
| P10 | Open license | Own models freely publishable |

### 2.2 Comparison

| Criterion | Renode | QEMU (mainline / xPack) | Custom approach (Unicorn/ISS-based, or HAL rehosting à la HALucinator) |
| --- | --- | --- | --- |
| STM32H7 support | An STM32H743 platform description exists; coverage is incomplete (HIGH, to be confirmed in M0). No H72x: to be derived ourselves | No H7 board in mainline; the STM32 boards are F1/F2/F4/L4 (HIGH). xPack has a few F4 boards | Everything to be built ourselves |
| Cortex-M7 with dp FPU | Supported by Renode's Cortex-M CPU (HIGH; dp instructions to be validated in M0) | Present (HIGH) | Unicorn: yes, but without a system model |
| Multi-machine in one time base | Built in: multiple machines, global quantum, UART hub, network switch (HIGH) | Two processes with chardev sockets; no shared virtual time. `icount` per instance, synchronization to be built ourselves (HIGH) | To be built ourselves |
| Peripheral models | C# (compiled at runtime), Python peripherals, `.repl` platform descriptions (HIGH) | C in the QEMU tree; recompile per change (HIGH) | Python or Rust; quick to prototype, but everything is own work |
| GDB | A GDB server per machine (HIGH) | Excellent (HIGH) | Unicorn: no stub (Qiling does have one) |
| Logging of unmodeled registers | Warnings on unhandled access, `Tag`, per-peripheral access logging (HIGH) | With tracepoints, but cumbersome | To be built ourselves |
| Snapshot, record and replay | Saving and loading the emulation state; recording of external events (HIGH, details to be confirmed) | Record/replay with `icount`, per instance; not across two processes (HIGH) | To be built ourselves |
| Test integration and CI | Robot Framework integration, headless, containers (HIGH) | Good, but test API to be built ourselves | To be built ourselves |
| Network | Switch, TAP bridge (HIGH) | Excellent (HIGH) | To be built ourselves |
| Framebuffer | Video/framebuffer peripherals and a framebuffer tester (HIGH; LTDC and DMA2D models exist for other STM32s, H7 compatibility to be checked) | Via a custom display device | To be built ourselves |
| Speed | Moderate: dynamic translation, MMIO to C# costs per access (HIGH) | Fastest (TCG) (HIGH) | Unicorn fast; Python hooks slow |
| Faithfulness to "unmodified firmware" | Register level: yes | Register level: yes | HAL rehosting replaces HAL functions and **therefore does not run the real HAL**. It fails the baseline idea and has to find function addresses again for each vendor release |
| License | MIT (HIGH) | GPLv2 (HIGH) | own |
| Effort to "stock boot" | medium | high (first H7 SoC and 20+ peripherals in C) | high to very high |

### 2.3 Recommendation

**Renode is the primary platform** (recommendation, backed by HIGH).
The reasons, in order of weight:

1. **Multi-machine with deterministic shared time is built in.**
   That is the core of D1: two H7s plus the link, plus the CTRL cable.
   In QEMU or a custom emulator that is exactly the hardest part.
2. **The gap workflow is built in:** logging of unmodeled
   access, `Tag`, GDB, snapshots and execution tracing (§5).
3. **Developing models is fast in C#.** Prototypes can be done in
   Python, without rebuilding the platform.
4. **CI and Robot are standard**, the license is MIT, and there is an
   active community around STM32.

**Supplementary (MAY):**
- A **Unicorn-based fuzz harness** for the *NF parsers* (CI-V, P1,
  TCI, the NF link), as host-compiled or isolated functions. It
  is faster than full emulation, but it does not replace the emulator.
- **QEMU** is ruled out as the main platform. It remains an option for purely
  speed-critical NF unit tests on a generic Cortex-M7
  (for example the MPS2-AN500 machine, HIGH), without G7250 peripherals.

**Decision point M0 (spike of 1–2 weeks).** Renode remains the choice unless
the spike shows that:
- dp FPU instructions or the MPU of the M7 go wrong; or
- the speed stays below ~0.05× real time for the boot of Main without
  FPGA stream.

In that case Renode with a custom CPU backend is reconsidered, not
QEMU.

### 2.4 How the Renode features are used

| Feature | Use in G7250-emu |
| --- | --- |
| Two machines in one `.resc` | `main` (H725-derived) and `control` (H743); for EH only `main` |
| Global quantum and serial execution | Deterministic interleaving. Start with a quantum of 10 µs VT; that is smaller than one byte time on the link (21.7 µs at 460 800 Bd, 8N1) |
| UART coupling | `main.usart2` ↔ `control.usart2` via a custom **LinkCable** model, with byte timing, fault injection and a tap to the decoder |
| C# peripherals | All H7 blocks that are missing or differ, all external chips and the plant model |
| Python peripherals | Quick prototypes; then port to C# if they are in the hot path |
| GDB | Port 3333 (Main) and 3334 (Control); symbols for stock from `*/analysis/memory/function_ranges.csv` (RE side only) |
| Snapshot | A "booted" snapshot per vendor release, from which test cases fork. That saves the 3–6 s VT boot per test (§6.2) |
| Execution tracing | Coverage of the NF (with DWARF) and of stock (function ranges from the CSV) |
| Robot or pytest | Robot for the Renode-native level, pytest as the main harness via the Renode API or the monitor socket (§8) |

---

## 3. Machine definitions for Main and Control

### 3.1 MCUs and memory maps

| | Main | Control |
| --- | --- | --- |
| Family | STM32H7, Cortex-M7 (VERIFIED, `docs/mcu_identification.md`) | same |
| Part | STM32H725xG or H735xG, 1 MiB flash (docs: MEDIUM → HYPOTHESIS). Crypto is not used, so the difference is irrelevant | STM32H743xI rev V, 2 MiB flash (HIGH, `docs/mcu_identification.md`) |
| DBGMCU IDCODE | DEV_ID 0x483 expected (HYPOTHESIS, `docs/hardware_test_plan.md` T3.1) | DEV_ID 0x450, rev V. **MUST** be correct: SystemInit branches on the revision (rev-Y errata) and the GUI library checks DEV_ID 0x450 (VERIFIED, `control_unit/docs/startup.md`, `docs/mcu_identification.md`) |
| Clocks | HSE 25 MHz, PLL1 550/275/275, HCLK 275, PCLK 137.5, PLL2 100 MHz (ADC); I2S_CKIN 12.288 MHz external (VERIFIED, `main_unit/docs/flow.md`) | HSE 25 MHz, PLL1 480/96/480, HCLK 240, PCLK 120, PLL2R 240 (FMC), PLL3R 40 (LTDC), LSE, HSI48 (VERIFIED, `control_unit/docs/flow.md`) |
| Power supply | SMPS 2.5 V plus LDO, VOS0 without overdrive (VERIFIED, `main_unit/docs/flow.md`) | LDO, VOS1 plus ODEN (VERIFIED, `control_unit/docs/flow.md`) |
| Application in flash | `0x08020000`–`0x0808EA20` (VERIFIED, `main_unit/docs/memory_map.md`) | `0x08020000`–`0x080DEC10` (VERIFIED, `control_unit/docs/memory_map.md`) |
| Bootloader region | `0x08000000`–`0x0801FFFF`, **not in the image** (HIGH) | same (HIGH) |
| Reset vectors | MSP `0x24050000`, reset `0x08024554` (VERIFIED, `main_unit/docs/startup.md`) | MSP `0x24080000`, reset `0x080235AC` (VERIFIED, `control_unit/docs/startup.md`) |
| AXI SRAM | 320 KiB `0x24000000`–`0x24050000` (HIGH, `main_unit/docs/memory_map.md`) | 512 KiB `0x24000000`–`0x24080000` (VERIFIED) |
| D2 SRAM | 32 KiB `0x30000000`, MPU non-cacheable (VERIFIED) | 288 KiB, not used; MPU region 512 KiB (VERIFIED, `control_unit/docs/memory_map.md`) |
| SRAM4 (D3) | 16 KiB `0x38000000`, non-cacheable (VERIFIED) | 64 KiB, non-cacheable (VERIFIED) |
| Backup SRAM | 4 KiB `0x38800000`, strongly ordered, read only (VERIFIED, `main_unit/docs/memory_map.md`) | not used |
| TCM | not used (VERIFIED) | DTCM has an MPU region, no content (VERIFIED) |
| External memory | none; MPU guard region on FMC bank 1 `0x60000000` (VERIFIED) | SDRAM 32 MiB at `0xC0000000`: framebuffers at `0xC0000000` and `0xC012C000`, emWin pool at `0xC0800000` (VERIFIED/HIGH, `control_unit/docs/peripherals.md`, `memory_map.md`) |
| Caches | I/D on; MDMA helpers do their own cache maintenance (VERIFIED) | I/D on; no cache maintenance; DMA buffers in non-cacheable SRAM4 (HIGH) |
| RTOS | none, superloop (VERIFIED) | none, superloop (VERIFIED) |
| Fault handlers | Default handler `0x080245A4` (loop). HardFault dumps registers on USART1 and halts (VERIFIED, `main_unit/docs/startup.md`) | Default handler `0x08023600` (loop). HardFault logs one line and halts (VERIFIED, `control_unit/docs/startup.md`) |

**Consequences for the `.repl` files:**
- `g7250_main.repl` is derived from an H7 base. It gets the
  H72x memory sizes, the vector table with TIM23/24 and UART9/USART10
  (length), SMPS registers in PWR, and `Tag` regions for all
  unused blocks.
- `g7250_control.repl` starts from Renode's H743 platform description
  (if it suffices in M0), supplemented with FMC, SDRAM, LTDC,
  DMA2D, SDMMC1, OTG_FS and the external chips.
- Caches are not modelled. The cache maintenance operations
  (ICIALLU, DCISW, DCCIMVAC …) **MUST** be accepted as no-ops.

### 3.2 Fidelity levels

| Level | Definition | Typical use |
| --- | --- | --- |
| **S — stub** | The address range exists. Writes are stored, reads return the reset value or the last written value. No side effects. Every access is counted | Initialized but unused (UART4, I2C2/I2C3 on Main) |
| **R — register level** | Registers with the correct reset values, read-only/W1C semantics and status flags that let HAL polling loops succeed (ready, busy, done) | RCC, PWR, FLASH, RTC, CRC, OTG stub |
| **B — behavior level** | R, plus the functional behavior: data, timing in VT, IRQs and DMA requests, and an external interface (file, socket, test harness) | UART, SPI, I2C devices, DMA, timers, CH394, FPGA, LTDC |

"Running perfectly" (§6) requires, for each peripheral, the level stated in the
inventory. A stub must never make a firmware polling loop
hang: the hang detector guards that (§5.3).

### 3.3 Peripheral inventory — Main

| Peripheral | Role | Source | Level | What the firmware needs to run perfectly |
| --- | --- | --- | --- | --- |
| Cortex-M7 core, NVIC, SysTick, SCB, MPU | CPU, priority grouping 4, SysTick 1 kHz at priority 15 | `docs/dma.md`, `main_unit/docs/flow.md` | B | dp FPU, correct preemption per priority, MPU regions accepted (PRIVDEFENA), VTOR 0x08020000, cache ops as no-ops |
| DWT CYCCNT | CPU load meter and NR cycle statistics | `main_unit/docs/startup.md` | B | Counts in VT cycles (instructions × factor), so the load meter gives meaningful values |
| RCC | PLL1/PLL2, HSE and LSI, kernel clock muxes | `main_unit/docs/flow.md`, `analysis/clocks/clock_config.csv` | R | HSERDY, PLLxRDY, LSIRDY, SWS follows SW; read back the kernel mux values. `HAL_RCCEx_GetPeriphCLKFreq` uses the I2S_CKIN constant, so no model is needed |
| PWR | SMPS/LDO, VOS0, backup regulator | `main_unit/docs/flow.md`, `memory_map.md` | R | ACTVOSRDY and VOSRDY; **BRRDY after BREN**, otherwise a wait of up to 1 s follows when loading the settings; DBP |
| FLASH controller | Wait states | `main_unit/docs/flow.md` | R | Read back ACR latency. No unlock key in the app (VERIFIED). A guard model for programming and erasing is needed for the NF and the brick tests (§10) |
| Option bytes | RDP, BOOT_ADD, CPUFREQ_BOOST, IWDG_SW | `main_unit/docs/flow.md` | R (profile) | Values unknown (§5). The profile supplies plausible values; the app does not read them (HIGH) |
| SYSCFG, EXTI | PC13 (CH394 INT#, falling), PE10 (FPGA DRDY, rising), PH3/PH4 (CW, both edges), PH6 (PTT, both edges) | `main_unit/docs/peripherals.md` GPIO, `docs/dma.md` | B | EXTICR mapping, edge detection, pending W1C; IRQ 9/10/23/40 |
| GPIOA–H | Discrete lines: T/R (PF4, PF6, PC7, PH11), latches (PA10/11, PH10/12, PD13, PG2, PG5), CH394 CS/RST (PG15, PB5), codec reset PB10, PH5 power key (pull-up), PH9, PH13, PH15, DAC load PB12/PB14 | `main_unit/analysis/peripherals/gpio_map.csv` | B | Pin-level model with external connections to the chip models and the PowerModel (§3.8.6); every edge logged in the trace (golden) |
| GPIOE as FPGA bus | 8-bit data PE0–7 (direction via MODER), CMD PE8+PE9, STB PE9, DRDY PE10 | `main_unit/docs/peripherals.md` FPGA bus | B (**fused**) | See the FPGA model in §3.5.1; GPIOE and FPGA are one C# model for speed reasons |
| DMA1/DMA2 + DMAMUX1 | S0 I²S3 RX, S2 USART2 RX, S3 USART1 RX, S4 USART2 TX, S5 I²S3 TX, S7 ADC1; DMA2 S5 mem-to-mem (never started) | `docs/dma.md`, `analysis/peripherals/dma_map.csv` | B | Circular mode, **NDTR readable** (the RX handler reads the ring via NDTR), HT/TC IRQ, request routing via DMAMUX, width 8/16/32 |
| BDMA + DMAMUX2 | ch0 SPI6 RX, ch1 SPI6 TX | `docs/dma.md` | B | May only touch D3 memory; the model checks that buffers are in SRAM4 (fidelity check); IRQ 129/130 |
| MDMA | ch0/1/2 copy, ch4 fill, software trigger, polled | `docs/dma.md` | B (simple) | Immediate copy on start, CTCIF/BTIF set; no IRQ |
| USART1 | Console and service menu, 115 200 8N1, RX via circular DMA, TX blocking | `main_unit/docs/peripherals.md` USART1 | B | PTY or socket to the harness. **The harness MUST NOT send Enter** outside targeted RE tests: that opens the service menu, which changes the drive DAC and the SWR terms (VERIFIED). The HardFault dump is written via direct register polling, so TXE/TC must be correct |
| USART2 | The link, 460 800 8N1, DMA TX/RX, IRQ38 | `docs/protocol.md` | B | Byte timing in VT, ORE flag (the re-arm logic relies on it), IDLE not needed on Main; LinkCable coupling |
| UART4 | Initialized, unused | `docs/hardware_init.md` | S | Init succeeds |
| I2C1 | EEPROM 0x50, AIC3204 0x18, AXP223 0x34, VC6 0x68/0x6A; polled, ~400 kHz | `main_unit/docs/peripherals.md` I2C, `analysis/peripherals/i2c_devices.csv` | B | H7 I2C v2 registers (TIMINGR, CR2 SADD/NBYTES/RELOAD/AUTOEND, ISR TXIS/RXNE/TC/STOPF/NACKF); **NACK when an address is absent** (the VC6 falls back from 0x68 to 0x6A) |
| I2C2, I2C3 | Initialized, unused; I2C3 IRQs enabled but with the default handler | `docs/dma.md` | S | The model MUST NOT spontaneously raise an I2C3 IRQ: that would fall into the default loop |
| SPI1 | TX-only master; five serial-in latches | `main_unit/docs/peripherals.md` SPI1, `docs/atu.md` | B | H7 SPI v2 (CSTART, TXP, EOT, TSIZE); pass bytes to the latch models per CS/latch line |
| SPI2 | TX-only to the 8-channel 10-bit DAC (BU2506FV type) | `main_unit/docs/peripherals.md` SPI2, `analysis/peripherals/spi2_dac.csv` | B | Decode 16-bit words (4-bit address plus 10-bit value), latch on PB12, reset PB14 |
| SPI3 = I²S3 | Master full-duplex, Philips, 32 bit, 48 kHz, kernel I2S_CKIN | `main_unit/docs/peripherals.md` I²S3 | B | Frame clock in VT (48 kHz), DMA requests per word, half/complete IRQ via DMA; coupling with the codec model |
| SPI6 | CH394, master mode 0, /8 of PCLK4 (~17.19 MHz), BDMA, IRQ86 | `main_unit/docs/peripherals.md` SPI6 | B | Byte timing at 17.19 Mbit/s (for the throughput budgets), receiving in receive-only mode for register reads |
| ADC1 | 7 ranks, continuous, DMA1 S7 circular, offset and linearity calibration | `main_unit/docs/peripherals.md` ADC1 | B | ADCAL clears itself, ADRDY; conversion values from the plant model; conversion time in VT |
| DAC1 | OUT1 = RF gain voltage, OUT2 unused | same | R + tap | Values logged (trace) |
| TIM5/6/7/17 | 20 kHz DSP scheduler, 100 Hz housekeeping, 1 kHz service and SLIP status, 20 kHz sample service | `analysis/peripherals/timers.csv` | B | PSC/ARR update IRQs in VT. Timer clock 275 MHz |
| TIM4 | PWM on PD12, never started | same | S | Init succeeds |
| RTC | LSI, time reset to 2000-01-01 | `main_unit/docs/peripherals.md` RTC | R | INITF/RSF handshake. The wake-up IRQ MUST stay off: IRQ 3 leads to the dead bootloader jump (HIGH) |
| IWDG1 | Kick per superloop pass, during the CH394 wait and at shutdown; never configured | `docs/architecture.md`, `analysis/peripherals/iwdg_kicks.csv` | B | **Off** by default. Profile "hardware-started, timeout T": reset on expiry (§4.3). Main's boot takes longer than 2 s without a kick (VERIFIED), so T has to be generous |
| CRC | Initialized, unused | `docs/hardware_init.md` | S | Init succeeds |
| Backup SRAM | Copy of the settings (read only) | `main_unit/docs/memory_map.md` | B (memory) | Content via the profile (empty or filled); the app forces the defaults anyway (VERIFIED) |
| FMC bank 1 `0x60000000` | MPU guard region, nothing behind it | `main_unit/docs/memory_map.md` | — (not mapped) | Access is logged as an anomaly |
| USB OTG_HS | Not used | `main_unit/docs/peripherals.md` USB | — | Every access is an anomaly |

### 3.4 Peripheral inventory — Control

| Peripheral | Role | Source | Level | What the firmware needs |
| --- | --- | --- | --- | --- |
| Cortex-M7, NVIC, SysTick, MPU, DWT | SysTick at priority 0 also feeds the IWDG every 256 ticks | `control_unit/docs/startup.md`, `docs/dma.md` | B | As Main. **DWT CYCCNT MUST run**: the GT911 transfers use 20 ms timeouts on the cycle counter (VERIFIED) |
| DBGMCU | IDCODE | `control_unit/docs/startup.md`, `docs/mcu_identification.md` | R | DEV_ID 0x450, REV_ID rev V; otherwise the errata path runs or the GUI check fails |
| RCC, PWR, SYSCFG, FLASH | PLL1/2/3, HSE, LSE (high drive), HSI48; LDO, VOS1+ODEN; 4 WS | `control_unit/docs/flow.md` | R | All ready flags; LSERDY (otherwise the RTC init hangs); accept the conditional RCC tweak at offset 0xD4 |
| GPIOA–I | Key matrix (open-drain with pull-up), 8 GPIO encoders, SD detect PA15, panel power (PE6, PI3, PF9), GT911 INT/RST (PE2/PG14), codec reset PH2, PCA9557 reset PG3, flash CS PG13, CW keying PE3/PE4, PI6, PG9/PG10 | `control_unit/docs/peripherals.md`, `analysis/peripherals/gpio_map.csv`, `inputs.csv` | B | A pin model with **open-drain semantics and external networks** (matrix, encoders); IDR must reflect the external level |
| EXTI2 | GT911 INT on PE2, rising | same | B | IRQ8 |
| DMA1 + DMAMUX1 | S0 I²S2 RX, S1 I²S2 TX, S2 USART2 TX, S3 USART2 RX, S4 USART1 RX | `docs/dma.md` | B | Circular; **receive-to-idle** on USART2 (IDLE event plus NDTR) |
| DMA2D | Fill, copy, PFC RGB565, blend; polled | `control_unit/docs/peripherals.md` display | B (native C#) | Correct pixel operations. Performance-critical: in C#, not in Python |
| FMC + SDRAM | Bank 1, 32 MiB, command sequence, refresh 918 | same | R + memory | SDCMR commands accepted, status not-busy; RAM 32 MiB |
| LTDC | 1024×600 RGB565, 40 MHz, one layer, double buffering | same, `analysis/peripherals/display_config.csv` | B | **VSYNC status in VT (~46.9 Hz)**, because the buffer swap waits for VSYNC (VERIFIED). Layer address plus reload (SRCR), IRQ88; framebuffer capture (§3.5.12) |
| I2C1 | GT911 (0x14, fallback 0x5D), polled | `control_unit/docs/peripherals.md` GT911 | B | Address choice according to the INT level at reset (§3.5.11) |
| I2C2 | AIC3204 0x18, PCA9557 0x19, ~100 kHz | same | B | As on Main |
| SPI1 | W25Qxx NOR, 48 MHz, polled, CS PG13 | `control_unit/docs/peripherals.md` SPI1, `analysis/peripherals/spi1_flash.csv` | B | JEDEC ID, read, page program, 4 KiB sector erase, WIP status; backed by an image |
| SPI2 = I²S2 | **Slave** full-duplex, 32 bit; clock from the codec | `control_unit/docs/peripherals.md` codec | B | Frame clock from the codec model (~48.005 kHz due to the PLL quirk, docs: MEDIUM); DMA |
| SDMMC1 | SD card, 4-bit, IDMA, IRQ49, card detect PA15 | `control_unit/docs/storage.md` | B | SD protocol (init at 400 kHz, ACMD6, 48 MHz in default speed accepted); backed by an image; card detect ≥ 320 ms low |
| USART1 | Bluetooth module (AT), CI-V parser and console on one line | `control_unit/docs/peripherals.md` USART1, `docs/civ.md` | B | RX via circular DMA, TX blocking. The BT401 AT model and the CI-V injector **share** the RX; the harness demultiplexes TX (§3.5.14) |
| USART2 | The link | `docs/protocol.md` | B | As on Main, plus receive-to-idle |
| TIM2 | Encoder mode (×4), main knob | `analysis/peripherals/timers.csv` | B | **Encoder mode**: CNT follows injected quadrature edges |
| TIM3/5/13/14 | 100 Hz GT911, 20 kHz audio, 50 Hz link client, 1 kHz input | same | B | Update IRQs in VT (IRQ 29/50/44/45) |
| TIM4 | PWM CH1/CH2 (backlight), ~3.66 kHz | same | R + tap | Duty cycle logged (brightness for screenshots) |
| TIM7 | CW text keyer: ARR per WPM | same | B | Reprogramming ARR takes effect immediately or at the update (H7 ARPE) |
| TIM8 | PWM input capture on PI5 (H-22), 30 MHz | `control_unit/docs/peripherals.md` H-22, `analysis/peripherals/h22_timing.csv` | B | Reset-on-rising, CH1 period, CH2 high time, CC IRQ46 |
| RTC + backup domain | LSE, marker 0xA5A5 in backup register 0 | `control_unit/docs/peripherals.md` RTC | R | Backup registers preserved across runs (part of the state); VT-based clock |
| IWDG1 | Kicks in the superloop and in SysTick | `analysis/peripherals/iwdg_kicks.csv` | B | As on Main |
| CRC | Initialized; no use found | `docs/hardware_init.md` | **R (functional)** | A real CRC-32 computation as a precaution. STemWin builds are known for licence checks via the MCU (HYPOTHESIS) |
| USB OTG_FS | MSC device exposing the W25Qxx | `control_unit/docs/peripherals.md` USB | R (phase 1), B (later) | Phase 1: HAL_PCD_Init and the core reset succeed (AHBIDL, CSRST), no VBUS and no host. Later: an MSC function via USB/IP (HYPOTHESIS that the Renode USB/IP route is usable) |

### 3.5 External chips and behavior models

#### 3.5.1 FPGA (Intel Cyclone 10, docs: HIGH for the family)

**Interface.** A bit-banged 8-bit bus on GPIOE (VERIFIED,
`main_unit/docs/peripherals.md` FPGA bus, `analysis/peripherals/fpga_bus.csv`).
The model sits as one C# component on GPIOE and follows MODER, ODR, BSRR
and IDR. It decodes:
- a **command byte** when PE8 and PE9 pulse together;
- the **data bytes** per STB pulse on PE9;
- the **direction** from MODER of PE0–7. If the MCU reads while the model
  is not driving, that is a bus conflict, and it is logged.

| Command | Model behavior |
| --- | --- |
| `0x00` loopback | Echo of the last written byte. The boot test writes and reads 0–255 twice (VERIFIED) |
| `0x01` configuration frame (24 B) | Store and decode: status bytes, three 32-bit NCO words (big-endian) and the rate index. Tuned frequency = word × 122.88 MHz / 2³², with folding to 0–61.44 MHz and the inversion flag (VERIFIED for the word format, `main_unit/docs/peripherals.md`) |
| `0x02` status | Two flag bits (bit 0 = ADC overload to `0x03` flag bit 6, HIGH) and three 16-bit values. The meaning of the values is unknown (docs: Q9); the model returns configurable values, by default the ADC peak from the signal generator |
| `0x03` TX I/Q | Two signed 24-bit values per sample, to the **TX sink** (recording plus plant coupling) |
| `0x04` RX I/Q | Two signed 24-bit values per sample, from the **RX source**. 8/4/2/1 samples per DRDY for rate 0–3 (VERIFIED in code) |
| `0x05/0x06`, `0x09/0x0A` | Pulse commands, only logged. Init sends the "off" codes; no other sender in V1.0.1 (HIGH) |
| `0x08` version | 3 bytes, configurable. Only logged (VERIFIED) |

**DRDY (PE10).** A rising edge in VT at a configurable rate:
default 48 kHz (docs: MEDIUM → HYPOTHESIS), the same for every
rate index.

**RX source (signal generator).** A list of RF components
{frequency, level in dBFS, modulation (CW, AM, SSB from WAV, FM tone)}
plus noise (dBFS/Hz). Per sample the model computes the baseband signal
relative to the tuned NCO frequency, with the inversion flag, at the
rate from the rate index (384/192/96/48 kS/s, HYPOTHESIS). Alternatively
it plays back an I/Q file. Above a threshold the
overload status bit goes on.

**TX sink.** Records the 24-bit I/Q and supplies the plant model with the
envelope \|I+jQ\| per block (§3.5.9). The first 200 interrupts after
keying are zero (VERIFIED); that is a checkpoint in the golden
trace.

**Health oracle.** The firmware logs an FPGA bus error if the first
RX sample stays the same for more than five checks (VERIFIED). The
default source **MUST** therefore always contain noise. A fault injection
"stuck sample" tests exactly this behavior.

**Performance.** At rate 0, 8 × 6 = 48 bytes cross the bus per DRDY,
so ~2.3 MB/s at 48 kHz. With ≥ 3 MMIO accesses per byte that gives
≥ 7·10⁶ MMIO/s (derivation, HYPOTHESIS for the exact instruction mix).
Therefore GPIOE plus FPGA is **one fused C# model**; it MAY
do burst recognition (after the CMD pattern of `0x04` the next
N bytes are ready); and the default baseline runs at rate index 3, with a
separate suite at 0–2.

#### 3.5.2 CH394 ethernet (W5500-compatible register model)

**Register model** (HIGH, `main_unit/docs/peripherals.md` SPI6,
`analysis/peripherals/spi6_ch394.csv`, `ch394_network.csv`; public
WCH manual CH394, version 1.2). Every access is a CS window
(PG15) with a 16-bit offset, a control byte with block select and
write flag, and the data. Modelled are:
- **the common registers:** MODE (including RST bit 7, **WOL bit 5**,
  PING block bit 4), GWIP, SMIP, MAC (from the model profile), IP,
  IIT, **GINT/GINTE** (including the magic-packet bit MP, bit 4),
  SINT/SINTE, RTIME, RCNT, PHY_CFG (link bit, power-down via
  OPWD/OPMDC), CHIPV `0x0039` (configurable, only logged),
  CHIP_CONFIG `0x003E`;
- **8 sockets** with the W5500-compatible registers (MODE, CTRL, INT,
  STA, PORT, DIP, DPORT, buffer sizes, TX and RX pointers, INTE);
- **the pools:** 16 KB TX and 16 KB RX with the per-socket layout.

The model supports **UDP** (stock uses only UDP, VERIFIED) and
**TCP** (needed for TCI in the NF; semantics from the public
W5500 and CH394 documentation).

**Reset.** RST# on PB5, low is reset. After release a
no-access window of 12–19 ms applies according to WCH (VERIFIED, docs cite
CH394DS1). Access within the window is **ignored and logged**;
that way the boot write to `0x0039` correctly remains harmless.

**INT#** (PC13, active low) follows the interrupt flags and enables.
Stock never reads the interrupt register and writes RECV blindly
(HIGH); so the model only has to deassert correctly.

**Timing.** SEND completes after a configurable latency in VT,
by default datagram length / 100 Mbit/s plus 20 µs (HYPOTHESIS). A
fault injection "SEND hangs" leaves the command byte uncleared.

**Network backends:**

| Backend | Lane | Operation |
| --- | --- | --- |
| **VLAN** (virtual LAN, default) | deterministic | Datagrams to an in-emulation network on which the **test clients run in VT**. No ARP/IP needed: the CH394 does ARP and ICMP itself (HIGH), so the model works at socket level and answers ping itself (unless MODE bit 4 blocks it). pcapng export for Wireshark with the dissectors from `g7250-base/tools/wireshark` |
| **UDP offload** | live | Every opened socket binds a host UDP port (with a configurable offset). Incoming datagrams get the VT stamp of arrival and are recorded |
| **TAP** | live | Frame level via a Renode TAP bridge. The model itself performs ARP, ICMP echo, UDP/TCP and the magic-packet detection (like the real chip), on a separate subnet |

**Time dilation.** If the emulator runs slower than real time (§8.7),
live clients with wall-clock timeouts (stock: 5 s per
handshake step, 15 s silence, VERIFIED) MUST get a dilation factor, or
run in the deterministic lane. The harness provides `vt_now()` and
`vt_sleep()`.

#### 3.5.3 AIC3204 codecs

| Unit | Role | Model behavior |
| --- | --- | --- |
| Main, I2C1 0x18, reset PB10 | I²S **slave** of I²S3; clock from the MCU | Register file with page select (`control_unit/analysis/peripherals/aic3204_init.csv`). ADC left = the mic input, from the CTRL cable or a WAV source. The DAC output goes to the "analogue" CTRL cable and to a WAV recording. MICPGA gain trackable (VERIFIED, `main_unit/docs/peripherals.md`) |
| Control, I2C2 0x18, reset PH2 | I²S **master** of I²S2 | Generates BCLK/WCLK in VT; default 48 kHz, optionally ~48.005 kHz (PLL quirk, docs: MEDIUM). IN1L = RX audio from Main, IN1R = mic, IN2R+IN3R = line-in in digiMode; outputs to WAV sinks and the CTRL cable (`control_unit/docs/peripherals.md`) |

If the firmware reads a register back, the model returns the last
written value or the datasheet reset value.

#### 3.5.4 EEPROM 24Cxx (Main, I2C1 0x50)

- At least 24C128 (highest address `0x24A7`), 2-byte addressing,
  64-byte pages, write cycle 5 ms with NACK during the internal
  write (datasheet; the firmware waits a fixed 10 ms, VERIFIED,
  `main_unit/docs/memory_map.md`).
- Backed by a file.
- **Profiles:** empty (0xFF); "factory fresh" (one boot with an empty
  image, during which the firmware writes back the calibration defaults,
  VERIFIED); filled with variants for the calibration tests (§6.8).
- **Fault injection:** power loss in the middle of a page write
  gives a partially written page with deterministically chosen
  bytes.

#### 3.5.5 AXP223 PMIC (Main, I2C1 0x34)

Register file with reset values from the public AXP22x datasheet; the
firmware also reads back (`main_unit/analysis/peripherals/i2c_memread_callers.csv`,
HIGH). A tap logs rail voltages and enables
(`analysis/peripherals/axp223_rails.csv`). The "safe state" (only
DCDC1) is recognized and logged (VERIFIED). In the
PowerModel (§3.8.6) the rails feed the FPGA, codec and PA domains.

#### 3.5.6 VersaClock 6 (Main, I2C1 0x68 or 0x6A)

Register file 0x00–0xFF. The 112-byte burst and the 256-byte read-back
return the written values and otherwise the datasheet defaults.
The address is configurable, so that the fallback can be tested
(VERIFIED). A tap decodes the output plan into the OUT1 frequency
(`analysis/peripherals/vc6_clock_plan.csv`).

#### 3.5.7 SPI1 latches (Main): RF switching and ATU

Five latch models (HIGH, `main_unit/docs/peripherals.md` SPI1,
`docs/atu.md`):
- chain A, 8 bit: latch PA11, OE PA10; TX LPF bank and T/R bit 7;
- chain B, 24 bit: latch PH12, OE PH10; RX BPF, mode bits, PRE
  (bit 18–20) and ATT (bit 21–22);
- the ATU latches: PD13 (style, in-line, antenna), PG2 (L) and PG5 (C,
  mirrored).

Every latch value is logged with a VT stamp and passed to the plant
model.

#### 3.5.8 SPI2 DAC (BU2506FV type, Main)

The 16-bit frame is decoded: two leading bits dropped, 4-bit address
LSB-first, 10-bit value (HIGH). LD (PB12) admits the value; RESET
(PB14, active low) sets everything to VrefL. The channels according to
`analysis/peripherals/spi2_dac.csv` go to the plant model: 1 drive,
2/8/7 bias, 3 fan, 6 power reference.

#### 3.5.9 ADC inputs and the plant model (Main)

The plant model supplies the 7 ADC ranks (VERIFIED for the assignment,
`main_unit/docs/peripherals.md` ADC1, `analysis/memory/meter_fields.csv`):

| Rank | Quantity | Plant behavior (default) |
| --- | --- | --- |
| 1 | Vext | 13.8 V; converted with the document constant 0.004835 V/LSB (the divider is a HYPOTHESIS). Scenarios: 10.5 / 11.5 / 15.5 V |
| 2/3 | Forward and reflected detector | From P_fwd and Γ of the load; inverse of the documented law P = 0.003405·x + 5.557·10⁻⁶·x² (x = 2·raw), plus directivity leakage and reflection gain |
| 4 | Idd | I_static + Σ k_i · bias_i (quiescent current per stage) + I_rf(P). Parameters chosen so that the **bias trim converges at boot** (targets +0.5 A and +0.9 A, ±0.1 A; VERIFIED). A "non-converging" scenario tests the failure path |
| 5 | PA temperature | NTC model, B ≈ 3950, raw 2047 = 25 °C (VERIFIED), with a thermal time constant |
| 6/7 | EALC/ALC | Configurable, low by default |

**P_fwd** follows from: T/R in TX (chain A bit 7 plus the T/R lines), bias
on, an LPF that covers the frequency, the TX I/Q envelope, the
power reference (P_ref = (ch6/75)²) and the drive (channel 1). The
model is simple and monotonic; it claims no RF fidelity, only
consistency for control loops and oracles.

**Load model.** The antenna impedance per port (ANT1/ANT2) as a
function of frequency; the ATU latches transform it according to a
simple L-network model, so that the stock ATU (`docs/atu.md`) can
converge or fail in a targeted way. By default the load is a **50 Ω
dummy load**.

**Safety oracles.** The plant model reports: RF drive without T/R in
TX; an LPF that does not cover the TX frequency; T/R or ATU relays switching
with drive present ("hot switching"); power above the cap; TX outside
the allowed list; TX in sleep mode (§3.8.4). For stock these are
**reports** of known behavior (stock has, for example, no
explicit delay in the T/R sequence, VERIFIED,
`main_unit/docs/flow.md`). For the NF they are **hard errors** (§10.4).

#### 3.5.10 W25Qxx NOR (Control, SPI1)

JEDEC ID configurable: 0xEF4014/15/17/18 = 1/2/8/16 MiB; 0xEF4016 is
an error path of stock (VERIFIED, `control_unit/docs/peripherals.md`).
Commands 0x9F, 0x03, 0x06, 0x02, 0x20 and 0x05; WIP duration in VT. The
image is a FAT volume (`1:`) with `config.ini`, the bandstack files,
`cwcall.ini` and the memory channels (`control_unit/docs/storage.md`).
Fault injection: power loss while rewriting a sector.

#### 3.5.11 GT911 touch (Control, I2C1)

- **Address:** the model samples INT (PE2) at the moment RST
  (PG14) releases: high gives 0x14, low 0x5D (datasheet; the firmware
  drives INT high, VERIFIED).
- **Registers:** product ID, firmware version, resolution (1024×600) and a
  186-byte configuration block with a **valid checksum**; on an
  error TIM3 stays off (VERIFIED).
- **Commands 3 and 4** are accepted.
- **Injection API:** `touch(x, y, duration)` and `swipe(...)`: the ready bit and
  the points in the 42-byte status block, plus a rising edge on INT.
- **Fault injection:** 10 I2C errors in a row; the firmware then disables the
  touch IRQ (VERIFIED).

#### 3.5.12 Display and framebuffer capture

The LTDC model reads the layer address at the moment of VSYNC and supplies
a 1024×600 RGB565 frame. Capture on request, at every VSYNC after a
change, or periodically; output PNG plus the SHA-256 of the raw
pixels; the backlight duty and the panel power sequence in the metadata.
Same input and VT gives the same frame (fixed RTC epoch).

#### 3.5.13 Input injection (Control)

| Input | Model | Source |
| --- | --- | --- |
| Key matrix 5×5 plus the direct key PA0 | An electrical matrix model: when the firmware drives group B low and reads A, the model returns low on A[i] for every pressed key at (i, j), and vice versa | `control_unit/docs/peripherals.md`, `analysis/peripherals/button_map.csv` |
| Short press, hold, repeat | `press(code, ms)`; debounce requires 4 equal scans (~20–25 ms); hold ~0.84 s (docs: MEDIUM) | `control_unit/docs/gui.md` |
| 8 GPIO encoders | Quadrature generator, at least 2 samples (≥ 2 ms) per phase | `analysis/peripherals/encoder_map.csv` |
| Main knob | TIM2 encoder mode, count value injection | same |
| Touch | GT911 model (§3.5.11) | — |
| H-22 micro keyboard | Symbol generator on PI5: preamble ≥ 7 zero symbols, sync (ratio ~4), 39 data bits LSB-first (A = bits 0–19, B = bits 20–38, bits 12–19 equal). Key code = ((A>>15)&0x0F) \| ((A>>6)&0xF0). High time 200 µs by default (< ~437 µs); release = 50 ms without an edge | `control_unit/docs/peripherals.md` H-22, `analysis/peripherals/h22_keycodes.csv`, `h22_timing.csv` |
| SD card detect | PA15 low ≥ 320 ms = card present | `control_unit/docs/peripherals.md` |

#### 3.5.14 Bluetooth module and the shared USART1 (Control)

- **AT model** (BT401 dialect, docs: MEDIUM): every `AT…` line gets an
  `OK` line; the timeout is 3 s with 5 retries; in a
  fault scenario the model MAY stay silent.
- **Power supply** via PCA9557 bit 4. With the module "off" the model returns no
  OK. The CI-V parser still sees every byte (VERIFIED, `docs/civ.md`).
- **The harness TX demultiplexer:** CI-V frames (`FE FE … FD`),
  AT lines and console lines each get their own channel in the trace.
- **The stock CI-V stream in the tests** runs via this USART1, the
  only CI-V input of Control in the code (VERIFIED). On the real radio
  the USB CAT runs via the CH342; that route is unknown (HYPOTHESIS,
  `docs/hardware.md`, T0.8/T0.9). The logical endpoint **"USB-CAT"** is
  therefore coupled to Control USART1 by default, with a
  wiring option.

#### 3.5.15 PCA9557 (Control, I2C2 0x19, reset PG3)

Register model (input, output, polarity, configuration) with a
bit tap: bit 4 BT power, bit 5 shutdown pulse, bits 6/7 TX/RX audio
(roles HYPOTHESIS, behavior VERIFIED, `analysis/peripherals/pca9557_bits.csv`).
The first flush ~3 s after reset is a boot milestone (§6.2).

#### 3.5.16 SD card (Control)

An SDHC model with a FAT32 image (volume `0:`) for the
voice memories. Profiles: no card, empty card (the firmware
formats automatically), filled card.

#### 3.5.17 CTRL cable model (system level)

The CTRL cable is a 15-pin HD D-sub (VERIFIED, `docs/hardware.md`
§7). The wiring is largely unknown; the model reads
`wiring.yaml` with a confidence per connection:

| Connection | Default | Confidence |
| --- | --- | --- |
| 13.8 V-derived power supply from Main to Control (never the reverse) | connected | HIGH (owner, `docs/hardware.md` §1) |
| Main USART2 ↔ Control USART2 | connected (crossed TX/RX) | HIGH (`docs/architecture.md`) |
| Main codec DAC → Control IN1L (RX audio) | analogue, gain 0 dB | HYPOTHESIS (docs: MEDIUM) |
| Control codec output slot 1 → Main mic input | analogue | HYPOTHESIS |
| Control PE3/PE4 → Main PH3/PH4 (CW key) | connected | HYPOTHESIS (`docs/cw.md`) |
| Control PI6 → Main PH6 (PTT during voice playback) | connected | HYPOTHESIS (`control_unit/docs/voice_cw_memories.md`) |
| Power key → Main PH5 | harness-driven (PowerModel) | HYPOTHESIS (`TODO.md`) |
| Main PH9 (power hold) | to the PowerModel | HYPOTHESIS |

Tests that depend on a HYPOTHESIS connection get the tag
`wiring:hypothesis`. A HIL outcome may confirm or refute such a connection
(black-box only, §11).

### 3.6 System level: operation

| Action | Emulation |
| --- | --- |
| Power on | Via the PowerModel (§3.8.6): DC on, then a key press or auto-start depending on H1/H2. Both machines start with a configurable mutual delay. Main sends `0x03` from boot without waiting for Control (VERIFIED, `docs/protocol.md`) |
| Orderly shutdown | PH5 low > 1 s. Main sets `0x03` flag bit 2, waits 100 ms and shuts down. Control saves `config.ini` and the stores and then clears PCA9557 bit 5. Main waits until PH5 is high and then resets (VERIFIED, `main_unit/docs/flow.md`) |
| Power failure | DC removed at a chosen VT moment. Persistent media (EEPROM, NOR, SD, backup domain) keep the state of that moment, with a partial write where appropriate |
| Cable disconnected | The LinkCable interrupts TX/RX for T. After ~1000 passes (2–3 s) Main drops PTT; Control freezes (VERIFIED/docs: MEDIUM) |

### 3.7 System configurations

| Config | Main | Control | Link | Purpose | Place |
| --- | --- | --- | --- | --- | --- |
| **SS** stock+stock | stock | stock | stock SLIP | Baseline: validates the hardware models (§6) | **critical path, step 1** |
| **EH** own Main headless | NF Main | — (no machine; CTRL cable disconnected) | not connected | **Primary target config.** Operation exclusively via P1 and TCI on the network, with AetherSDR or other SDR software as host | **critical path, step 2** |
| **ES** own Main + stock Control connected | NF Main | stock (unmodified image) | physically connected; for the NF Main the link traffic of the stock panel is just unknown bytes | **Only a robustness and safety test**, not a target configuration and not a compatibility test (§8.3.6) | low priority |
| **EE** own+own | NF Main | NF Control | NF link (own design, with version negotiation) | Later, optional track: an own front panel | optional, later |

**Not supported as a functional configuration:** an NF Control with
a stock Main, and any form of cooperation between NF Main and stock
Control. The interface of the NF Main differs so much that the
stock panel cannot talk to it at all. ES exists only to
prove that a connected stock panel does not disturb the NF Main and
suffers no damage.

**Requirements on the NF Main in EH:**
- The NF Main MUST run without a Control peer: no waiting for the link,
  no error on link silence, all operation via P1, TCI and (optionally)
  CI-V over the network.
- The power supply requirements of §3.8.4 apply (PH5 ignored by default,
  always-on, sleep and wake).
- The hardware PTT (PH6) and the key inputs (PH3/PH4) are usable or disabled
  according to the NF spec; that is a choice of the NF spec,
  with a test.
- The CTRL cable is set to "disconnected" in EH. The wiring tests with
  `wiring:hypothesis` are N/A.

**Requirements on the NF Main in ES (robustness and safety; low
priority):**
- **S-ES1 — Link traffic from the panel = unknown bytes.** Everything that
  arrives on USART2 from the stock panel (the `0x01` images every
  20 ms, `0x06` requests, noise) is, for the NF Main, a stream of unknown
  bytes. It MUST ignore it robustly, as in a fuzz test: no
  crash, no hang, no memory leak, no state change, no TX.
  The stock traffic serves as a fuzz corpus in the emulator (§8.4).
- **S-ES2 — Hardware lines from the panel ignored by default.** All
  lines that can come from the panel via the CTRL cable (PTT,
  CW key, power key, audio; partly hypotheses, §3.5.17) the
  NF Main MUST ignore, unless a line is **explicitly enabled in its own
  configuration**. By default no panel line at all causes TX,
  keying, shutdown or an audio path to the
  modulator.
- **S-ES3 — Nothing to the panel that can change its persistent
  state.** The NF Main MUST NEVER write anything to the panel that
  can change the persistent state of the panel:
  - no frame that the stock decoder can read as a valid `0x03` with
    power-off bit 2: stock Control writes `config.ini`
    only on that signal (VERIFIED, `control_unit/docs/storage.md`);
  - recommended: send nothing at all on the link to the panel as long as
    there is no own panel with a valid negotiation. If the
    NF Main does send (e.g. a negotiation beacon of the NF link), then
    that framing MUST fail at the stock decoder on CRC or length (to be
    tested with the stock Control in the emulator);
  - no voltage or signal on panel lines outside the HIS specification.

  Oracle: after an ES run the NOR, the SD and the backup domain of the
  stock Control are **byte-identical** to before the run.
- An "unsupported" state on the stock panel is **not**
  pursued: the panel cannot talk to the NF Main.

### 3.8 Top priority R0: can the Main power on and operate without Control?

This is **R0**, the largest risk on the critical path (§14.2). If the
Main only powers on via the power key on the panel, and that key
runs through the CTRL cable, then EH on the real radio without a connected
panel is impossible. The stock panel then has to stay physically
connected, solely as the power-on path, under the ES rules; the power-key line
may then only be used if it is explicitly enabled in the own
configuration (S-ES2).

#### 3.8.1 Facts from the docs, the owner and public reports

| Fact | Source | Label |
| --- | --- | --- |
| The 13.8 V comes in on the Main. The Main powers the panel via the CTRL cable, never the other way round | owner; `docs/hardware.md` §1 | HIGH |
| The Main powers on by driving PH9 high, waiting 1 s and then programming and enabling the AXP223 rails (first a safe state with only DCDC1, then all rails together) | `docs/hardware_init.md`, `main_unit/docs/flow.md` (power-on 1–3), `main_unit/docs/peripherals.md` (AXP223) | VERIFIED |
| PH5 is an input with internal pull-up (the power-key sense) | `main_unit/analysis/peripherals/gpio_map.csv` | HIGH |
| The power-key logic (TIM6, 100 Hz) only arms once PH5 has been seen high. PH5 low for > 1 s gives a power-off request | `main_unit/docs/flow.md` | VERIFIED |
| Shutdown: flag in `0x03`, wait 100 ms, put everything in a safe state (T/R lines low, DAC channels 0, latch outputs off, CH394 in reset), save calibration and ATU if dirty, AXP223 to the safe state, interrupts off, **wait until PH5 is high again**, then a system reset | `main_unit/docs/flow.md` (shutdown 1–11) | VERIFIED |
| PH9 is never explicitly driven low; a power-hold line that the reset releases is a hypothesis | `main_unit/docs/flow.md`, `gpio_map.csv` | VERIFIED (code) / HYPOTHESIS (role) |
| What physically drives PH5 (a panel key via the CTRL cable?) is unknown | `TODO.md` | HYPOTHESIS |
| Stock Main loads forced defaults at every start, including for the network, and waits for `0x01` from the panel | `main_unit/docs/memory_map.md`, `docs/protocol.md` | VERIFIED |
| **The forced network defaults are IP 192.168.3.199, gateway 192.168.3.1, netmask 255.255.255.0, base port 50001** | public upstream issue #1 on `fventuri/g7250-base` | **HYPOTHESIS/MEDIUM (upstream report, not verified by us)** |
| **Network PTT is not released on loss of the session** | public upstream issue #2 on `fventuri/g7250-base` | **HYPOTHESIS/MEDIUM (upstream report, not verified by us)**. Consistent with the docs: on loss of the wfview stream, Main keeps network control for up to 60 s or three attempts (VERIFIED, `docs/protocol.md`, `main_unit/docs/network.md`) |
| The Control shutdown pulses PCA9557 bit 5 (role unknown) | `control_unit/docs/peripherals.md` | VERIFIED (behavior) / HYPOTHESIS (role) |

**What the firmware does not tell us.** Whether the Main MCU already has power before
anyone presses a key, and how the key releases the power supply. That lies
in hardware or in the bootloader, both of which fall outside the images.

#### 3.8.2 Two hypotheses

| | **H1 — hardware latch on the Main** | **H2 — MCU always powered from a standby rail** |
| --- | --- | --- |
| Operation | The key switches on the regulator via hardware; the MCU starts and holds the power supply with PH9. At the system reset at the end of the shutdown, PH9 releases and the power supply drops out | The MCU (or a standby part) is powered as long as the 13.8 V is present. The firmware (probably the bootloader) waits for PH5; PH9 switches the rails for the rest of the radio |
| Consistent with the docs | PH9 high as the first step, wait 1 s, PH9 never low, the reset as the end of the shutdown | The shutdown waits for the key to be released before the reset; otherwise a bootloader waiting on PH5 would immediately start up again. The reset ending is then "back to standby" |
| Without key (panel removed) | Nothing happens at DC on, unless (a) an **auto-start at DC on** exists in hardware, or (b) as a last resort a **key-emulation contact on the CTRL connector** (hardware modification on the outside; decision of the owner) | Everything is firmware: the NF can decide for itself (§3.8.4) |
| Hard on/off for EH | Switching the 13.8 V through the station automation, plus an auto-start (if it exists) | A switchable 13.8 V power supply in the owner's station automation, plus the firmware modes |

Both are HYPOTHESIS and are not fully mutually exclusive.

**Stock pitfall.** PH5 has an internal pull-up (HIGH); without a
panel the line first reads high and arms the power-key logic. If
something on the Main side of the CTRL connector pulls the line low as soon as the
panel is absent, stock sees a power-off request after about 1 s
(HYPOTHESIS). Stock then puts everything in a safe state, puts the CH394 in reset and
**stays stuck until PH5 goes high**, which never happens without a panel.
A link that comes up and drops after a few seconds (and stays down until DC
off and on again) is therefore an **expected** pattern. According to the
boot sequence, the link only comes up after the CH394 init, a few seconds after
DC on (PH9 + 1 s, AXP + 1 s, EEPROM, VC6, CH394; VERIFIED sequence,
`main_unit/docs/flow.md`).

#### 3.8.3 Decisive tier-0 cold-start observations (without opening the radio)

A proposal for `docs/hardware_test_plan.md`. The owner decides whether
he accepts each step as tier 0.

**Fixed procedure rules for every headless stock test** (normative):
1. **Dummy load on the antenna output** (50 Ω, ≥ 100 W), on every
   antenna port the radio can select, before DC on.
2. **No wfview and no other CI-V or LAN client that can set PTT**
   is connected or active while the test is running. Reason: the upstream
   report #2 (HYPOTHESIS/MEDIUM) that network PTT is not released on session loss,
   and the documented network control of up to 60 s (VERIFIED).
   Only passive captures, ping and ARP are allowed.
3. **Never disconnect or connect the CTRL cable with DC on.**
4. **Never press Enter on a Main console** (service menu, VERIFIED,
   `main_unit/docs/peripherals.md`).
5. **Log** with date, versions, the setup and every observation.

**What an observation proves:**
- **"The LAN link comes up"** only proves that the CH394 is out of reset.
- **A reply to a ping to 192.168.3.199** from a host in
  192.168.3.x/24 proves that the application is running: the CH394 answers
  ping by itself, but only after the app has given it the IP address. After
  a stock power-off the CH394 is in reset, so no more ping. The
  defaults come from upstream report #1 (HYPOTHESIS/MEDIUM); an
  ARP capture on the segment confirms them.

| # | Observation | Outcome → hypothesis |
| --- | --- | --- |
| T0-P1 | **Current reading of the power supply** with DC on and the radio "off" (normally switched off via the panel key, panel connected). Only read the display of the own bench power supply | ≈ 0 mA → **H1**. Tens of mA → **H2**. The display must be able to show tens of mA |
| T0-P2 | **CTRL disconnected, DC on:** does the Main's Ethernet link come up on the switch (LED or port status)? | No link → H1 without auto-start, or H2 waiting for PH5. Link up → the CH394 is out of reset (the Main has started). Link up and gone after a few seconds → the stock pitfall (§3.8.2) |
| T0-P3 | At T0-P2 with link: a host in 192.168.3.x/24 pings 192.168.3.199; a passive capture (ARP, broadcasts) | Ping reply → the application is running. No reply with link up → the app is not that far yet, or already switched off (pitfall); repeat with the time axis from DC on |
| T0-P4 | Repeat T0-P1 with CTRL disconnected | Comparison: consumption of the panel versus standby of the Main |

T0-P1 separates H1 from H2; T0-P2/T0-P3 tell whether an (auto-)start without
panel is possible and whether the app keeps running. The results go into the
HIS as HIL facts and determine F0 (§10.3).

#### 3.8.4 Requirements on the NF Main for power management

| ID | Requirement |
| --- | --- |
| P-1 | **PH5 ignored by default.** No shutdown trigger unless explicitly enabled in the configuration (S-ES2). A floating or pulled-low PH5 without a panel may never lead to a shutdown |
| P-2 | **Hold PH9.** PH9 high as the first step at boot (like stock, VERIFIED) and high in every mode except a deliberate shutdown |
| P-3 | **Always-on mode.** Configurable: fully operational after DC on, without waiting for a key. Hard on/off comes from the switchable 13.8 V power supply in the station automation |
| P-4 | **Sleep mode.** PA bias 0, drive 0, T/R on RX, latch outputs safe, FPGA and audio (codec) off or in reset, AXP rails for those parts off where the HIS allows it; **the CH394 stays awake** with the link up |
| P-5 | **Safe state on entering sleep.** First the full RX entry and the safe-state steps (bias removed before the relays, §10.4 S7); no relay switching under drive |
| P-6 | **No TX in sleep.** Every TX source (P1-MOX, TCI, CI-V, hardware PTT, VOX, key, ATU tune) is refused; TX first requires a full wake and a successful self-test |
| P-7 | **Wake over the network.** A UDP wake command restricted to the local network (and preferably authenticated), and/or **Wake-on-LAN** via the magic-packet function of the CH394 (§3.8.5) |
| P-8 | **Sleep command** via P1, TCI or own UDP management; optionally a timeout to sleep without a host |
| P-9 | **Orderly shutdown** (if requested): the same safe steps as stock, save EEPROM, AXP to the safe state; under H1 release PH9 as the last step |
| P-10 | **Status** of the power mode visible via P1, TCI and the management protocol |
| P-11 | **Network PTT drops on session loss.** As the counterpart of upstream report #2: every network TX drops within T_wd after loss of the session (§10.4 S3) |

#### 3.8.5 CH394: Wake-on-LAN and power-down (public source)

From the public CH394 manual from WCH (manual 1, version 1.2,
wch.cn) (HIGH):
- **MODE (`0x0000`) bit 5 = WOL**: with WOL on, the chip raises an
  interrupt when it receives via **UDP** a magic packet with its own MAC
  (6 × `0xFF` followed by 16 × the MAC). The same bit position
  as on the W5500 (MR bit 5).
- **GINT (`0x0015`) bit 4 = MP** (cleared by writing a 1) and
  **GINTE (`0x0016`) bit 4** as enable; the interrupt arrives on INT, on
  the G7250 PC13 (VERIFIED, `main_unit/docs/peripherals.md`).
- **PHY_CFG (`0x002E`)**: OPWD (bit 6) plus OPMDC (bits 5:3) = `110` is
  PHY power-down; not usable in sleep, because the link has to stay up.
- **Open (HYPOTHESIS):** whether a UDP socket has to be open for magic-packet
  detection (and on which port), and the
  standby consumption of the chip.

Stock never enables WOL: the driver does not write MODE (VERIFIED,
`main_unit/docs/peripherals.md`).

#### 3.8.6 Emulator model of the power state

A **PowerModel** component with the parameter `hypothese = H1 | H2`:

| Element | H1 | H2 |
| --- | --- | --- |
| DC input (harness) | on or off | on or off |
| Regulator and latch | Key (PH5 line) or the auto-start option switches the power supply on; PH9 high holds it; PH9 low or a reset with PH9 released → power supply off, MCU stops | The MCU runs as soon as DC is on (via the B2 shim, §4.3, with an optional "wait for PH5" step as a model of a bootloader); PH9 switches a rail domain for the rest |
| Rails for FPGA, codec, PA section | Follow the AXP223 registers (§3.5.5) | same, plus the PH9 domain |
| Consumption (indicative) | 0 mA off | standby value configurable |
| PH5 without panel | Configurable: pull-up high, floating, or pulled low after x ms (the stock pitfall) | same |

**Tests:**

| ID | Scenario | Expected |
| --- | --- | --- |
| PW-1 | Stock Main, H1 and H2, panel removed, PH5 variants | With PH5 high via the pull-up: stock keeps running and answers ping on the default IP (VLAN). With PH5 low after boot: power-off request after ~1 s, safe state, CH394 in reset (no link, no ping), and waiting for PH5. Prediction for T0-P2/T0-P3 |
| PW-2 | NF Main, always-on, H1 (with auto-start) and H2 | Boot to operational without a key; PH5 variants have no effect (P-1) |
| PW-3 | NF Main, sleep and wake via a UDP command | In sleep: no bias and drive, FPGA and codec domain off, CH394 link up; wake within the agreed time; self-test before TX |
| PW-4 | NF Main, sleep and Wake-on-LAN via a magic packet | MP interrupt on PC13, wake |
| PW-5 | NF Main in sleep, all TX sources tried | No TX at all; clean refusal (P-6) |
| PW-6 | Transition to sleep during TX | First a full RX entry in the correct order (P-5); no hot switching |
| PW-7 | DC removed during sleep or during an EEPROM write, then DC back | Correct boot in the configured mode; vendor records intact (E-B4) |
| PW-8 | NF Main with connected stock panel (ES), the panel sends a key press or noise on PH5 | No shutdown unless explicitly enabled (P-1, S-ES2) |

#### 3.8.7 Resolution plan, in order

1. **Boot state in the emulator** (RE side): stock Main with the
   PowerModel under H1 and H2, with the PH5 variants and without a
   Control machine (PW-1); record whether stock boots fully (A1), what
   network behavior it has with the defaults, and whether a spontaneous
   power-off follows. The outcome goes into the HIS as a hardware-fact
   hypothesis.
2. **The docs:** review `docs/hardware.md` on switching on and off;
   keep the PCA9557 bit 5 role and the PH9 role in `TODO.md` as a linked question;
   follow upstream reports #1 and #2.
3. **Tier-0 observations** T0-P1–T0-P4 of §3.8.3, under the fixed
   procedure rules. Wrap-up: DC off, the CTRL cable back, DC on, and
   check normal operation.
   - H2, or H1 with auto-start: EH is feasible on hardware; the NF Main
     implements always-on and sleep/wake (§3.8.4).
   - H1 without auto-start: the stock panel stays physically
     connected during HIL, solely to power on, under the ES rules. A
     key-emulation contact on the CTRL connector is the last
     resort (decision of the owner).
4. **Firmware project:** the final answer and the consequences for the NF Main
   are in §15 (O7).

---

## 4. Image supply and boot-state modeling

### 4.1 Principle: the emulator decrypts nothing

The emulator contains **no decryption code, no
key configuration and no key storage** (no key file, no
Keychain). It reads exclusively **already decrypted
application images** that the user supplies themselves. How the user
obtains those images falls outside the emulator and outside this
specification.

| Fact | Source | Label |
| --- | --- | --- |
| The vendor supplies encrypted update files (`.bbf` for Main, `.ctl` for Control) | `README.md`; the vendor package (§4.4) | VERIFIED |
| The application images of V1.0.1 are 453 152 B (Main) and 781 328 B (Control) | `README.md` | VERIFIED |
| Load base `0x08020000`; vectors in the image; VTOR is set by SystemInit | `main_unit/docs/startup.md`, `control_unit/docs/startup.md` | VERIFIED |
| Sector 0 (`0x08000000`, 128 KiB) contains a bootloader that is not in the images | `main_unit/docs/memory_map.md` | HIGH |
| Neither application contains update, flash-unlock or option-byte code | `main_unit/docs/peripherals.md`, `control_unit/docs/peripherals.md` | HIGH |
| The bootloader jump in Main (via RTC wake-up) is dead code in V1.0.1 | `main_unit/docs/peripherals.md` | HIGH |
| Option bytes are set in production or by the bootloader | `main_unit/docs/flow.md` | VERIFIED (absence in the app) |

### 4.2 Supply and checking of the images

**Configuration.** One setting points to the image-map, for example
`images_dir` in a local configuration of the user, or the
environment variable `G7250_EMU_IMAGES`. The directory:
- MUST lie **outside every git working tree**; the emulator refuses to
  start if the directory lies inside a git repo (check for a
  parent `.git`);
- contains the decrypted application images per release, with a free
  file name;
- MAY additionally contain the original vendor files, **only** as
  provenance (§4.4).

**Manifest** (`images/manifest.yaml` in the repo, public): **only
hashes and versions**, never content.

| Field | Content |
| --- | --- |
| `release` | e.g. `M1.0.1/C1.0.1` |
| `unit` | `main` or `control` |
| `image_sha256` | SHA-256 of the decrypted application image — **to be supplied by the user** at the first ingest (§7) |
| `image_size` | size in bytes (V1.0.1: 453 152 / 781 328) |
| `load_base` | `0x08020000` |
| `vector_check` | expected MSP and reset vector (V1.0.1: `0x24050000`/`0x08024554` Main, `0x24080000`/`0x080235AC` Control; VERIFIED) |
| `provenance` | the vendor package and the vendor files with their SHA-256 (§4.4) |

The `g7250-base` README lists the SHA-256 of the images that were
analyzed there. The user MAY use those as a check value,
but the manifest only records values that the user supplies and
confirms themselves.

**Check at every run** (normative):
1. The image exists and has the expected size.
2. The SHA-256 matches a manifest entry. On a mismatch the emulator
   **refuses** with a clear message, for example:
   "Image for main does not match the manifest (expected
   release M1.0.1, sha256 …; found sha256 …). Supply the correct
   decrypted image, or start the ingest for a new release."
3. Structural check: vector[0] in the AXI range of the unit,
   vector[1] Thumb and inside the image, the `.data` range inside the
   image, size ≤ app slot.
4. The run manifest lists the image hashes (no content).

**Protection against leaks:** pre-commit and CI checks in every repo
of the project refuse files whose hash is in the manifest,
binary files above a threshold, and the file extensions of
vendor updates.

### 4.3 Boot-state modeling

The emulator **boots the application image directly**. It does not emulate
a bootloader or an update path (those belong to the firmware project,
§15). It does, however, model the reset and handover state that a
bootloader leaves behind, so that the stock app boots correctly:
- **clocks:** RCC after reset on HSI, or a PLL that is still active;
- **VTOR, MSP and PC:** from the vector table at `0x08020000`;
- **option bytes:** a profile with plausible, readable values (RDP,
  BOOT_ADD, CPUFREQ_BOOST for 550 MHz on Main, IWDG_SW);
- **IWDG:** off, or hardware-started with timeout T;
- **NVIC and IRQ state**, possibly an armed RTC wake-up;
- **power supply:** via the PowerModel (§3.8.6).

| Strategy | Operation | Use |
| --- | --- | --- |
| **B1 — direct boot** (default) | Renode sets PC and SP from the vectors at `0x08020000`, with VTOR = `0x08020000` (SystemInit sets it again). The core and peripheral state comes from the boot-state profile | Baseline, most tests |
| **B2 — reset-vector shim** | A small clean-room stub (own code, a few instructions) at `0x08000000`: set VTOR, load MSP, jump to the app's reset vector; optionally "wait for PH5" for PowerModel H2. Explicitly **not a bootloader model** | Tests that run through a reset, Main's dead RTC wake jump, PowerModel H2 |

The NF images are booted the same way and MUST boot correctly in every
profile; they must not depend on a clock or IWDG state that
a bootloader would leave behind.

**Boot-state profiles:**

| Profile | IWDG | Clocks | NVIC and IRQ | Remark |
| --- | --- | --- | --- | --- |
| `clean` | off | reset (HSI) | all off | default |
| `iwdg-hw` | started, timeout T in {4, 8, 16, 32} s | reset | off | tests the assumption "off or several seconds" (docs: MEDIUM) |
| `pll-left-on` | off | PLL active, SYSCLK on PLL | off | SystemInit and HAL must restore that correctly |
| `rtc-wkup-armed` | off | reset | RTC WKUP IRQ on | Shows that the dead jump only fires if the bootloader leaves it armed (HIGH) |

A baseline run is only "green" if stock satisfies §6 in **all** profiles,
or if a deviation is explicitly documented as
profile-dependent.

### 4.4 Provenance: the official vendor package

The official vendor package is **only stored and hashed** as
provenance in the manifest. The emulator never parses, decrypts or uses
it.

| Item | Value |
| --- | --- |
| Package | `2026-11-09_Xiegu_G7250_V1.0.1.zip`, from radioddity.com/pages/xiegu-download |
| SHA-256 package | `70d250a1d90a0e98da35e2845eea45288b9d1dc73552293287c882fd95372af8` |
| Main update file (encrypted) | `G7250_MainUnit_Fw_V1.0.1.bbf`, 453 152 B, SHA-256 `66b97ad90de2711fcc88d8fb8c034fde57fa5cf1b483bfd75041b35edebb09d0` |
| Control update file (encrypted) | `G7250_ControlUnit_Fw_V1.0.1.ctl`, 781 328 B, SHA-256 `78b61101a968dc9d786e75adb11552a4cdabc6944a50aed7492e095df286ee2e` |
| Decrypted images | SHA-256 **to be supplied by the user** |

**Public vendor documentation in the package** (usable as a
clean-room source, because it is public and intended for users):
- a **CI-V reference, revision 1.2** (PDF): the public CI-V
  command set; source for the CI-V conformance of the NF (§8.3.4) and a
  cross-check on the black-box baseline A4/A5;
- a **wfview rig file `G7250.rig`** with CI-V address 0xA0: confirms
  the vendor's choice of the address that stock uses over LAN (VERIFIED,
  `docs/civ.md`) and answers the open question in `TODO.md` whether Xiegu supplies a
  rig file. It is documentation; wfview itself remains no
  test client;
- an **HDSDR ExtIO DLL**: usable only as a black-box client for
  HIL tests in HDSDR mode; this vendor software is not
  analyzed;
- **release notes**: source for the version matrix (§7.2).

---

## 5. Gap analysis

### 5.1 Missing knowledge for perfect emulation

Priority: **K** = critical (boot or main function depends on it),
**M** = medium, **L** = low.

| # | Gap | Prio | Source of the gap | Close with dynamic analysis in the emulator | Can HIL (tier 0) help? |
| --- | --- | --- | --- | --- | --- |
| G1 | State the bootloader leaves behind at handover | M | `main_unit/docs/peripherals.md` | Profile matrix §4.3; the read-before-write detector | No |
| G2 | Option bytes and IWDG timeout | M | `TODO.md` | IWDG profile sweep; measure boot kick interval (Main boot > 2 s without kick) | No (SWD needed) |
| G3 | FPGA: real sample rates, TX rate, status values, calibration bytes, pulse commands | **K** for the NF, M for stock | `docs/hpsdr_gap_analysis.md` Q1–Q3, Q9 | Log all FPGA transactions; count the number of samples read per DRDY for each rate index; derive what the firmware *expects* | Partly: T0.3, T0.4, T0.5 |
| G4 | DRDY rate and jitter | M | `main_unit/docs/peripherals.md` | Parameterize; measure the sensitivity (underrun, health check) at 40–56 kHz | Indirectly, via T0.3 |
| G5 | Rate of `0x03` frames (follows the FFT) | M | `docs/protocol.md` | **Fully closable in the emulator**: measure and freeze as a baseline value | No |
| G6 | CH394: CHIPV value, PHY details, SEND latency, maximum SPI clock, WOL conditions | L/M | `main_unit/docs/peripherals.md`, Q4; §3.8.5 | Log read order and polling loops; vary the SEND latency | T0.3/T0.6; T0-P3 |
| G7 | VC6 and AXP223 readback content | L | `main_unit/docs/peripherals.md` | Check whether the firmware makes decisions based on the content | No |
| G8 | GT911 configuration block, product ID, coordinate orientation | M | `control_unit/docs/peripherals.md` | Synthetic block; fit orientation with touches on known button positions | T0.1 |
| G9 | Panel legends, button and press pairs | L | `control_unit/docs/gui.md` | Not needed; the codes are known | T0.1 |
| G10 | Wiring of the CTRL cable (audio, PE3/PE4, PI6, PH5, PH9) | M | `TODO.md`, `docs/cw.md` | `wiring.yaml` plus tagged tests | T0.11, T0.9, T0-P2 |
| G11 | Content of a real EEPROM | L for the emulation, M for the twin | `TODO.md` | Defaults suffice; the firmware writes them itself (VERIFIED) | No |
| G12 | Plant parameters: Idd per bias code, detector law, NTC, load | M | — | Choose parameters so that the control loops converge; sensitivity analysis | Yes: Po and SWR via CI-V (`15 11`, `15 12`) at ≤ 5 W on the dummy load |
| G13 | Error_Handler address and the behavior on a HAL init error | M | `docs/hardware_init.md` | The hang detector finds it; then a breakpoint as a "fatal" oracle | No |
| G14 | Use of CRC and IDCODE checks by the GUI library | M | `docs/mcu_identification.md` | Log access during the GUI init | No |
| G15 | USB OTG register behavior for HAL_PCD_Init and MSC | M | `control_unit/docs/peripherals.md` | Detect polling loops; add registers step by step | T0.7 |
| G16 | SDMMC: IDMA coherence, card variants | L | `control_unit/docs/memory_map.md` | Cannot be simulated without a cache model; document as a non-emulatable risk | No |
| G17 | AT responses of the BT module | L | `control_unit/docs/peripherals.md` | The firmware ignores the responses (VERIFIED) | T0.10 |
| G18 | Cycle-accurate timing | M | — | Cannot be emulated; indicative only (§8.7) | Indirectly |
| G19 | Behavior of new vendor releases | ongoing | — | Ingest workflow §7 | — |
| G20 | Interactions the docs do not mention yet | unknown | — | Strict mode plus the access heatmap per release | — |
| G21 | The concrete values of stock Main's network defaults | L | upstream issue #1 (HYPOTHESIS/MEDIUM) | Measure in the emulator which IP stock writes into the CH394 | T0-P3 (ping/ARP) |
| G22 | How the Main powers on (H1/H2) | **K** (R0) | §3.8 | PowerModel variants | T0-P1–T0-P4 |

### 5.2 Dynamic analysis methods (RE side)

1. **Logging of unmodeled access** {VT, machine, PC, address,
   width, value, R/W}, aggregated into an **access heatmap** per
   release.
2. **Tags with deliberate reset values**, each with a reason and a source.
3. **Read-before-write detector** for registers that are sensitive to
   the handover state (G1).
4. **Hang and poll detector** (§5.3).
5. **Function coverage of stock**: an execution trace mapped onto the
   function ranges from `*/analysis/memory/function_ranges.csv` and the
   layout from `*/analysis/libs/lib_regions.csv`; the percentage of
   application functions (Main 305, Control 850; `docs/libraries.md`) that the
   baseline executes.
6. **Differential heatmap between releases** (§7).
7. **Freezing and mutating** a single model parameter to find the
   firmware's sensitivity.

All output of §5.2 is **RE-side material** and never goes
to NF development (§12).

### 5.3 Hang and poll detector

**Criterion.** A machine is "hung" if (a) the PC stays ≥ 50 ms VT in a
window of ≤ 64 bytes, or (b) the superloop IWDG kick (Main
`0x08022A80`, Control `0x080220DE`, VERIFIED,
`analysis/peripherals/iwdg_kicks.csv`) is absent for longer than T_kick (default
500 ms VT) after the boot milestone.

**Report:** the PC loop and the last 16 MMIO reads in that loop; the call
stack (frame-pointer heuristic plus the function ranges); the suggestion
"status bit X of register Y is missing".

**Known terminal loops** are oracles, not gaps: Default_Handler, the
HardFault stop, Error_Handler (G13) and the shutdown wait on PH5.

---

## 6. Acceptance criteria: "the factory firmware runs perfectly"

### 6.1 General

A release combination (Main vX + Control vY) passes when **all**
criteria A1–A12 are green in the deterministic lane, with
profile `clean` and B1 boot. A1 and A2 MUST additionally be green in all
boot-state profiles (§4.3). Times are in VT. "Baseline value"
means: measured at the first green run of V1.0.1, then frozen
with the stated tolerance.

### 6.2 A1 — Boot to the main loop, without faults

| ID | Criterion | Measurement | Threshold |
| --- | --- | --- | --- |
| A1.1 | Main reaches the superloop | First execution of the kick at `0x08022A80`; periodic thereafter | Baseline value + 10 %. Expected 3–8 s VT (HYPOTHESIS) |
| A1.2 | Main's ready flag | Watch on TRX+0x22D (`main_unit/analysis/memory/trx_runtime_fields.csv`); RE side only | Set, within A1.1 + 1 s |
| A1.3 | All Main boot steps logged in the documented order | A console parser (USART1) compares against `main_unit/docs/flow.md` step 5b, on a paraphrased key list, not on literal strings | Complete, in the correct order |
| A1.4 | Control reaches the superloop | Kick at `0x080220DE` | Baseline value + 10 % |
| A1.5 | Control: GT911 init succeeded (TIM3 active), FatFS mounted, first PCA9557 flush | Timer start TIM3; I2C2 write to 0x19 | All three; the flush ~3 s after reset (VERIFIED) ± 0.5 s |
| A1.6 | Main screen visible | Framebuffer hash after settling | Equal to the golden (§6.10) |
| A1.7 | No fault | No execution of Default_Handler (Main `0x080245A4`, Control `0x08023600`), HardFault, NMI or Error_Handler | 0 |
| A1.8 | No hang | Hang detector §5.3 | 0 reports |
| A1.9 | Strict mode | Unmodeled access | 0 outside the frozen allowlist |
| A1.10 | FPGA and codec health | Boot bus test without mismatch log; no FPGA or codec underrun in 60 s | 0 |
| A1.11 | IWDG | In profile `iwdg-hw` with T ≥ the baseline threshold: no reset | 0 resets |
| A1.12 | Network defaults | The IP that stock Main writes into the CH394 without `0x01`; ping reply in the VLAN | Equal to the frozen baseline value; compare with upstream report #1 |

### 6.3 A2 — Link timing and integrity

Measurement: the LinkCable tap plus a SLIP decoder, with
`g7250-base/tools/g7250/slip.py` as reference parser.

| ID | Criterion | Threshold |
| --- | --- | --- |
| A2.1 | `0x01` period over 120 s | Mean 20.0 ms ± 0.2 ms; p99 ≤ 21 ms, except for the documented skips caused by the TX lock (VERIFIED, `docs/protocol.md`) |
| A2.2 | `0x01` content during startup: zero images, compiled defaults, then the values from `config.ini` | Sequence present; the config values within the baseline time |
| A2.3 | `0x03` frames: rate, jitter, payload of 552 B | Rate = baseline value ± 5 % (G5); 0 CRC errors; flag word consistent with the plant |
| A2.4 | `0x06` request and response | ≤ 100 ms; 104 B; content visible on the system info page |
| A2.5 | `0x08` with an active Icom LAN client (own test script) | Within 300 ms; resends ≤ 300 ms until the ack in `0x01` byte `0x158`; seq 1–255, never 0 (VERIFIED) |
| A2.6 | Link loss: LinkCable interrupted for 5 s during CI-V PTT on Control | Main drops PTT within 2–3 s; recovery without handshake |
| A2.7 | Error-free over 1 h VT | 0 CRC, length or overrun errors without injection |
| A2.8 | Utilization: byte duration 21.7 µs | `0x01` ≈ 9.3 ms per frame (430 B), so C→M ≈ 47 % (derivation, HIGH) |

### 6.4 A3 — Every GUI page reachable

With input injection **and** a screenshot match; as RE oracle the
`selectUi` byte MAY be read (UI +0x920, `control_unit/docs/gui.md`).

| Screen | Path (`control_unit/docs/gui.md`, `analysis/peripherals/button_map.csv`) |
| --- | --- |
| 0 main screen | any exit path |
| 4 Menu 1 (2 pages × 15 items) | A0×B3; page 2 via an encoder |
| 5 Menu 2 (2 pages) | A1×B3 |
| 6 Menu 3 CW | A0×B4 on the main screen in CW mode |
| 7 System, subpages 1–7 | A2×B3; subpage 7 (factory reset): **open, do not confirm** |
| 8 Memory channels plus the name keyboard | A0×B0 or touch |
| 9 Applications: list 0 and SWR scanner 2 | A3×B1 |
| 10 Keyer memory | A3×B0 in CW/CWR |
| 11 Voice memory | A3×B0 in a voice mode |
| 12 Quick setting | hold A3×B2 |
| Overlays `windows` 1–3 | mode selection, band selection, direct frequency entry (also H-22 0x28) |
| Pop-ups | NF/NR/NB level, RIT/XIT, level bar 3 s |

| ID | Criterion | Threshold |
| --- | --- | --- |
| A3.1 | Every row reached, then back to 0 | 100 % |
| A3.2 | Screenshot per page = golden | Pixel-exact in the deterministic lane |
| A3.3 | Every matrix code (22) and every encoder (8 plus the main knob) has the documented effect | 100 % of `button_map.csv` and `encoder_map.csv` |
| A3.4 | Every H-22 code from `h22_keycodes.csv` produces the documented action | 100 % |

### 6.5 A4 — CI-V coverage (Control, USART1)

| ID | Criterion | Threshold |
| --- | --- | --- |
| A4.1 | Every command from `control_unit/analysis/protocol/civ_control.csv` (17 families) in read and, where possible, write form | 100 %; the response has the expected class (data, FB, FA, echo) |
| A4.2 | Write and read-back consistent; the value appears in the next `0x01` image and on the screen | 100 % of the writable fields |
| A4.3 | Every address is answered; `19` echoes the addressed address | compliant (VERIFIED, `docs/civ.md`) |
| A4.4 | Transceive: after turning the main knob, an unsolicited `00` frame | ≤ 1 frame per change |
| A4.5 | CI-V PTT drops after 10 s without CI-V traffic | 10 s ± 0.1 s (VERIFIED) |
| A4.6 | BT AT traffic and console on the same line do not disturb the CI-V parse | 0 errors over 10 000 commands |
| A4.7 | Cross-check against the public CI-V reference rev. 1.2 from the vendor package (§4.4) | Deviations between documented and observed behavior reported (informational, not a fail) |

### 6.6 A5 — Icom LAN sessions (Main's wfview-compatible mode) and HDSDR mode

All sessions are driven by **own test scripts**, not by
wfview.

| ID | Criterion | Threshold |
| --- | --- | --- |
| A5.1 | Handshake: are-you-there, I-am-here, ready, login, token, capabilities and conninfo, status, streaming | Complete, each step ≤ 5 s VT |
| A5.2 | Login with wrong credentials | Rejected |
| A5.3 | Keep-alive: pings on control and CI-V every 100 ms, on audio every 500 ms; idle every 100 ms (VERIFIED, `main_unit/docs/network.md`) | ± 5 % |
| A5.4 | Audio radio → PC: 20 ms rhythm, chunks ≤ 1364 B, header per `wfview_packets.csv`, LPCM 16/8-bit, 48/16 kHz | compliant |
| A5.5 | Audio PC → radio with PTT (`1C 00`) | TX path active in the plant (dummy load); TX I/Q in the FPGA sink |
| A5.6 | CI-V over LAN: all 68 rows of `main_unit/analysis/protocol/civ_main.csv`, including the quirks | 100 % |
| A5.7 | Scope: `27 10/11/14/15/16/19` per `civ_scope.csv`; waveform frames ≤ 20/s, 518 B, 475 points | compliant |
| A5.8 | Network control: `0x03` flag bit 7, the VFO block of `0x01` ignored, `0x08` push | compliant |
| A5.9 | Timeouts and recovery: 15 s silence, the recovery ladder (`main_unit/docs/network.md`) | compliant |
| A5.10 | **Session loss during network PTT** (scenario of upstream report #2) | The observed stock behavior recorded as baseline; a PTT that stays stuck is registered as a **known stock deviation** (safety-relevant, §10.4 S3 for the NF) |
| A5.11 | HDSDR mode: discover, heartbeat, LO set 0.5–108 MHz, I/Q packets of 774 B, the packet rate per span, drop after 10 s | Baseline values (expected 250/s, HYPOTHESIS) |
| A5.12 | Live mode switching: all sockets closed, network layer restarted (VERIFIED) | compliant |
| A5.13 | Link self-recovery: PHY gone > 10 s triggers a cycle (max. every 30 s), after 2 failed cycles one hard reset (VERIFIED) | compliant |

### 6.7 A6 — Persistence of settings

| ID | Criterion | Threshold |
| --- | --- | --- |
| A6.1 | `config.ini` written only on an orderly shutdown (VERIFIED, `control_unit/docs/storage.md`) | 0 writes outside that |
| A6.2 | Round trip: changes via CI-V and GUI, shutdown, cold start, same values | 100 % of ≥ 40 fields |
| A6.3 | Power loss without shutdown | Changes lost (stock behavior, VERIFIED); no crash |
| A6.4 | Band stack, CW messages, memory channels | Save, reload, equal |
| A6.5 | Voice memory on SD (16-bit, 48 kHz, mono, ≤ 30 s) | Record and play back, equal within margin |
| A6.6 | Factory reset: volume 1 formatted, the MCU reset, Main's EEPROM unchanged (VERIFIED) | compliant |
| A6.7 | Empty NOR image | Auto-format, defaults, no crash |

### 6.8 A7/A8 — Band changes and calibration block

| ID | Criterion | Threshold |
| --- | --- | --- |
| A7.1 | The bit pattern of chain A and B for a frequency grid (all edges ± 1 kHz) = the document table | 100 %; deviations only at MEDIUM edges, documented |
| A7.2 | The PRE/ATT selectors follow the VFO bytes (VERIFIED) | 100 % |
| A7.3 | The TX and RX sequence = `main_unit/docs/flow.md` | compliant |
| A7.4 | TX band enforcement (safety oracle; restrictive only): outside the enabled bands no bias and no T/R lines (VERIFIED) | compliant |
| A7.5 | ATU tune with the load models "tunable" and "impossible" (`docs/atu.md`) | compliant |
| A8.1 | Valid calibration block: loaded, the trim converges | compliant |
| A8.2 | Invalid CRC or layout id: defaults written back immediately (VERIFIED) | compliant |
| A8.3 | Bias out of range: trim, dirty, saved at shutdown (VERIFIED) | compliant |
| A8.4 | `0x02` request from a "factory tool" in the emulator (RE side): response 358 B | compliant |
| A8.5 | `0x02` set: RAM copy only (VERIFIED) | compliant |
| A8.6 | NVPARAM marker rewritten on every valid boot (VERIFIED) | compliant |

### 6.9 A9–A11 — Other functions

| ID | Criterion |
| --- | --- |
| A9.1 | Power-off sequence per §3.6 |
| A9.2 | SWR scanner: 51 points, dwell 500 and 100 ms, 5 W NFM, key via `0x15E` bit 6 (VERIFIED, `control_unit/docs/flow.md`); only on the dummy load |
| A9.3 | CW: dot = 1200/WPM ms; trainer mode without bias and T/R; sidetone on the codec |
| A9.4 | CW memory from Control (PE3/PE4) produces CW on the Main side (`wiring:hypothesis`) |
| A9.5 | RX audio end-to-end: a carrier at f_VFO + 700 Hz in USB produces 700 Hz ± 2 Hz at the Main codec output; the S-meter monotonic with the level |
| A10.1 | Bluetooth on and off: the AT sequence with 3 s timeout and 5 retries; PCA9557 bit 4 |
| A11.1 | Soak 1 h VT (nightly) and 24 h VT (weekly); 0 faults, 0 hangs, no heap growth |

### 6.10 A12 — Golden traces and screenshots

A golden trace is a canonicalized JSONL event stream per
scenario (`t_vt_ns`, `machine`, `bron`, `soort`, `data`), with
link frames, UART text, datagrams, GPIO edges, latch values,
DAC writes, I2C transactions, framebuffer hashes and
plant events.

| ID | Criterion | Threshold |
| --- | --- | --- |
| A12.1 | Determinism: three runs with the same manifest | Identical trace and screenshot hashes |
| A12.2 | Replay of a recorded live session | The same output for the parts determined by the firmware |
| A12.3 | Golden comparison | Trace = golden, with tolerance windows |
| A12.4 | Screenshot set: ≥ 1 per page from A3 plus the core scenarios | Pixel-exact |

Golden traces and screenshots are **derived from stock** and therefore private
(§12); the public repo contains only the scenario definitions and the hashes.

---

## 7. The vendor release process

### 7.1 Workflow

| Step | Action | Output | Who or what |
| --- | --- | --- | --- |
| R0 Provenance | The user stores the official vendor package in the local image-map. The emulator tooling hashes the package and the files in it (without opening or parsing them) and records them as `provenance` | Manifest provenance entry: source URL, date, file names, sizes, SHA-256 | tooling (automatic) |
| R1 Supply | The user supplies the **decrypted** application images of the new release in the image-map and confirms their SHA-256 | Manifest entry: release, unit, `image_sha256`, size, vectors | user + tooling |
| R2 Check | Hash check against the manifest and the structural check (§4.2); on a mismatch the ingest stops with a clear message | OK or rejection | emulator |
| R3 Smoke test | Boot per unit in strict mode, profile `clean`, solo and coupled with the previous release of the other unit | Boot OK or hang report; new heatmap | CI (private runner) |
| R4 Baseline suite | A1–A12 in full | Result per criterion | CI |
| R5 Behavior diff | Diff against the previous release: heatmap, link frames, CI-V and LAN responses, screenshots, console key list, and (RE side) function ranges via the `g7250-base` tooling; the release notes from the vendor package as context | Diff report (private) | CI + RE |
| R6 Triage | Every deviation: **E** emulator gap, **G** genuine behavior change, **R** regression in the vendor firmware | Triage table | RE |
| R7 Evolve models | Class E: adjust the model; **all releases in the matrix must keep passing**; release-dependent behavior only via a hardware profile | Model commit plus regression run | developer |
| R8 Update golden | Class G: record the golden with review and rationale | New golden set (private) | review |
| R9 Feed back docs | Findings to `g7250-base`, following that repo's own process | Issue or PR, only after an explicit go from the owner | RE |
| R10 Tag | Emulator release `emu-<semver>`; matrix entry "perfect" | Tag, matrix | release |

The emulator decrypts nothing in any step. If the user does not supply
decrypted images, the release stays in the matrix at
"provenance known, not tested".

### 7.2 Version matrix

`matrix/version_matrix.yaml` (public, hashes and status only):

| Column | Content |
| --- | --- |
| `vendor_release` | e.g. `M1.0.1/C1.0.1` |
| `provenance` | package name, source, date, SHA-256 of package and vendor files (§4.4) |
| `image_sha256` | per unit, supplied by the user |
| `fpga_version_reported` | from the `0x06` slave info (in V1.0.1 a compiled string, VERIFIED) |
| `emu_version_min` | the first emulator release on which this is "perfect" |
| `models` | model versions |
| `profiles_green` | the boot-state profiles that are green |
| `criteria` | A1…A12: green, red or n/a |
| `cross_pairs` | combinations with other releases of the other unit, with their status |
| `known_deviations` | documented stock quirks, including upstream reports #1/#2 once confirmed or refuted |
| `golden_set_id` | reference to the private golden set |

**Emulator versioning policy:** *major* for an incompatible
harness change, *minor* for a new vendor release or a new
model, *patch* for model corrections without a golden change.

---

## 8. Test infrastructure

### 8.1 Layers

| Layer | Purpose | Target | Typical duration | Lane |
| --- | --- | --- | --- | --- |
| L0 Static | lint, typecheck, CSV schema, image and secret scan, clean-room scan (§12.2) | repo | < 2 min | — |
| L1 Model unit tests | Each C# and Python model in isolation, against the datasheet and docs semantics | models | < 5 min | host |
| L2 Emulator integration | Small **own** test firmwares (clean-room) that exercise one peripheral: UART echo, SPI latch pattern, I2C scan, FPGA bus protocol, LTDC test image, PowerModel | emulator | < 15 min | det. |
| L3 Baseline regression | A1–A12 on stock (all releases in the matrix) | stock (SS) | 30 min to 6 h | det. |
| L4a Conformance NF-Main (critical path) | P1, TCI, optionally CI-V over the network, headless operation, power supply modes (PW-2–PW-8) | NF-Main (EH) | 30–60 min | det. |
| L4b Robustness ES (low priority) | S-ES1–S-ES3 (§8.3.6) | NF-Main + stock Control | 15–30 min | det. |
| L4c Conformance own panel (optional track) | The NF link with version negotiation, the NF-Control | NF-Main + NF-Control (EE) | 30–90 min | det. |
| L5 Property, fuzz and fault | Invariants, fuzzing of parsers, fault injection | NF (stock only as reference) | nightly and weekly | det. |
| L6 Performance and timing | Budgets (§8.7) | NF (+ stock as reference) | nightly | det. |
| L7 HIL | §11 | real radio | on request, with gates | bench |

### 8.2 L1 — Model unit tests (examples)

- **CH394:** the register semantics (RO, W1C, auto-clear of Sn_CTRL), the
  pool layout, the 8 B RX header, ignoring access in the
  reset window, the TCP state machine, WOL and the MP bit,
  PHY power-down.
- **FPGA:** the bus decoding under arbitrary MODER changes; the
  NCO folding and inversion (property test word → frequency → word);
  samples per DRDY per rate.
- **BU2506FV:** the bit order per the datasheet.
- **GT911:** the address selection per INT level; the checksum.
- **H-22 generator:** the inverse of the documented decoder.
- **SLIP/CRC:** cross-test with `g7250-base/tools/g7250/slip.py` and the
  existing tests in `tools/g7250/tests` (for the baseline only).
- **PowerModel:** H1 and H2 state diagram, the PH5 variants.
- **Plant:** monotonicity, convergence of the bias trim, and the oracles (a
  deliberately wrong T/R sequence must produce a report).
- **Image check:** rejection on a hash mismatch, on a directory inside
  a git repo, on an invalid vector table.

### 8.3 L4 — Conformance of the new firmware

**Order.** On the critical path are §8.3.2 (P1), §8.3.3 (TCI),
§8.3.4 (CI-V over the network, optional) and the power supply modes (§3.8.6),
in config EH. §8.3.6 (ES) has a low priority. §8.3.1 and §8.3.5
belong to the optional, later track of an own panel (EE).

#### 8.3.1 Own inter-unit link (NF link, config EE — optional track)

The NF link is an **own design** between NF-Main and NF-Control; no
stock SLIP and no compatibility requirement with stock. The specification belongs
to the firmware project. The physical channel is fixed by the hardware
(USART2 on PD5/PD6, HIS); baud rate and framing are chosen by the
firmware project.

| ID | Requirement on the NF link (generic, to be refined with the NF link spec) | Oracle |
| --- | --- | --- |
| C-L1 | Framing with integrity check and an explicit length; a **protocol version** and a **capability negotiation** at start and after every link recovery | LinkCable tap plus a reference decoder from the NF link spec |
| C-L2 | State synchronization within T_sync (target ≤ 500 ms) after start and after every recovery | Comparison via the external interfaces and the NF screen |
| C-L3 | Defined owner per parameter (panel, network host); no conflicting state | Concurrency scenarios (panel and P1 or TCI simultaneously) |
| C-L4 | Meter and spectrum stream Main → Control with minimum rate and bounded latency | Tap; the NF screen |
| C-L5 | Link loss: the local PTT and key sources drop within ≤ 3 s | LinkCable interruption |
| C-L6 | Recovery without manual action, ≤ 1 s after the link is restored | Fault matrix §8.5 |
| C-L7 | Orderly power-off: Control saves its state before Main releases the power supply | NOR trace and sequence |
| C-L8 | Utilization ≤ 70 % of the byte time in each direction | Tap statistics |
| C-L9 | Robust against all link faults and fuzzing | No crash or hang |
| C-L10 | **Graceful degradation between different versions.** The versions of NF-Main and NF-Control need not be equal; after negotiation only the common capabilities; unknown capabilities or message types ignored; missing functions shown on the panel as unavailable; TX safety never depends on a panel capability | A version matrix N−2…N+1 against N−2…N+1 with capabilities enabled and disabled |
| C-L11 | Negotiation fails | Both units continue to operate independently (NF-Main as in EH); no TX based on panel sources |

#### 8.3.2 OpenHPSDR Protocol 1, "G7250-P1" profile

Source: the public P1 documentation (Metis "How it works", USB protocol
V1.58, the Hermes-Lite 2 wiki; references in
`docs/hpsdr_gap_analysis.md`).

**Board id.** A new, own board id; a value not in use in the known
host apps, coordinated with their maintainers
(HYPOTHESIS that a free value exists). The profile defines the
power, SWR, voltage, current and temperature telemetry, the
control of ATU and antenna ports (C&C addresses outside the
HL2 range or a documented extension), the PA information (100 W,
cap) and the power supply mode (P-10).

| ID | Requirement | Test |
| --- | --- | --- |
| C-P1 | Discovery on UDP 1024 (`EF FE 02`); response with status, MAC, code version, board id | Reference host plus negative cases |
| C-P2 | Start/stop (`EF FE 04`) | State diagram |
| C-P3 | EP6: 1032 B datagrams, 2 × 512 B frames, sync `7F7F7F`, C0–C4, 63 × (I24, Q24, mic16) per frame; sequence numbers without gaps | Packet validator; no gaps over 10 min VT at 48 and 96 kHz |
| C-P4 | Sample rates 48 and 96 kHz mandatory; 192 kHz optional (SPI budget, `docs/hpsdr_gap_analysis.md` §2.4); 384 kHz cleanly rejected | Rate in VT ± 0.01 % |
| C-P5 | EP2: L/R audio to the codec, TX I/Q, MOX | TX I/Q in the FPGA sink; L/R in the codec sink |
| C-P6 | RX frequency, TX frequency, preamp, attenuator, antenna | NCO word, latch state; in EE also the NF panel |
| C-P7 | Drive and power | Power ≤ min(drive mapping, cap) (plant) |
| C-P8 | **Host watchdog**: TX off when no more C&C or EP2 arrives | TX off within T_wd (requirement ≤ 1 s, target ≤ 250 ms) |
| C-P9 | Status: PTT, dot/dash, ADC overload, fwd/rev, Vext, Idd, temp | Consistent with the plant |
| C-P10 | Headless operation (EH, primary); in track EE coexistence with the NF panel | EH: all C-P tests without a Control machine |
| C-P11 | Interoperability with real host software | Recorded sessions of AetherSDR and other SDR hosts pass as replay in the deterministic lane |

#### 8.3.3 TCI

Source: the public TCI specification from ExpertSDR (WebSocket,
text commands and binary I/Q and audio streams). TCI runs over
**TCP**, so the CH394 model MUST support TCP (HIGH); stock
does not use TCP.

| ID | Requirement | Test |
| --- | --- | --- |
| C-T1 | WebSocket handshake; the device and protocol message on connect | Reference client |
| C-T2 | Core commands: VFO, mode, TX enable and TRX, drive, tune, split, RIT/XIT, filter bands | 100 % of the G7250 TCI profile; unsupported commands cleanly rejected |
| C-T3 | Binary streams at the agreed rate | Rate and frame validator |
| C-T4 | Watchdog: connection gone or no ping, then TX off ≤ T_wd | Fault |
| C-T5 | Concurrency with P1 (if permitted) | No double owner of TX |
| C-T6 | Throughput budget over SPI6 and CH394 with TCP overhead | §8.7 |

#### 8.3.4 CI-V (NF)

On the critical path (EH) there is no serial CI-V; the NF-Main MAY offer CI-V
over the network. In track EE the NF-Control MAY implement the serial
route (in the stock code that is Control USART1; the
real USB CAT route is confirmed by HIL, H0). Conformance: a
command profile as a table, response classes per the Icom convention,
addressing, transceive, a PTT timeout, robustness against mixed
traffic.

**Sources:** the **public CI-V reference rev. 1.2** from the
vendor package (§4.4) is a legitimate clean-room source for the
command profile. Where the NF wants to offer external clients the same behavior as
stock, it MAY use the black-box results of A4/A5
(responses as a client sees them, no internal state).

#### 8.3.5 NF-Control (front panel, config EE — optional track)

An own front panel firmware on the Control hardware, with an own
GUI library (STemWin falls under the ST license,
`control_unit/docs/gui.md`).

| ID | Requirement | Oracle |
| --- | --- | --- |
| C-C1 | Boot to a working main screen without fault or hang, in every boot-state profile | A1-like criteria |
| C-C2 | Every input has a documented effect per the NF panel spec | Input injection plus screenshots (golden per NF build) |
| C-C3 | Every NF page reachable and back | Page list from the NF spec |
| C-C4 | Persistence; orderly power-off; power loss without blocking corruption | NOR and SD traces |
| C-C5 | Audio routing via the codec and the CTRL cable per the HIS | Codec sinks and sources |
| C-C6 | Input to screen update ≤ 100 ms (target) | Trace |
| C-C7 | VSYNC-synchronized buffer swap | Framebuffer capture |

#### 8.3.6 Robustness and safety with a connected stock panel (ES, low priority)

Not a compatibility test and not a target configuration.

| ID | Requirement on the NF-Main | Oracle |
| --- | --- | --- |
| C-S1 | The stock panel's link traffic is unknown bytes and is robustly ignored (S-ES1) | 1 h VT with a running stock panel plus mutated frames: no crash, hang or fault, no state change, no TX |
| C-S2 | Panel lines ignored unless explicitly enabled (S-ES2) | Activate each line via the CTRL cable model: by default no TX, keying, power-off or audio to the modulator |
| C-S3 | Nothing sent to the panel that can change its persistent state (S-ES3) | NOR, SD and backup domain byte-identical; the stock decoder sees 0 valid frames from the NF-Main |
| C-S4 | Power on and off with a connected panel | No undefined state; the panel receives no shutdown signal |

### 8.4 L5 — Property tests and fuzzing

| Target | Method | Oracle |
| --- | --- | --- |
| Unknown bytes on the link UART (ES) | The traffic of a running stock panel as corpus, plus random bytes and bursts | No crash, hang or state change; no TX |
| NF link frame decoder (track EE) | Grammar-based fuzzing; also as host fuzzer | No crash, hang or out-of-bounds (sanitizers on the host build) |
| CI-V parser | Random addresses, missing FD, embedded FE FE, overlong payloads | same, plus "no unwanted TX" |
| P1 packets | Mutations of C&C, wrong sequences, mixed lengths | same, plus the C-P8 watchdog keeps working |
| TCI text and WebSocket frames | Fuzzing of the framing and the syntax | same |
| Wake and management packets | Mutated wake commands and magic packets | No unintended wake outside the rules; never TX |
| Properties | "Never RF drive when T/R is in RX"; "TX frequency ∈ allowlist"; "power ≤ cap"; "no TX in sleep"; "network TX drops within T_wd after session loss" | Plant oracles; temporal properties on the trace |

### 8.5 L5 — Fault injection

| Category | Injections | Expected behavior (NF: requirement; stock: baseline documentation) |
| --- | --- | --- |
| Link | bit errors (BER 10⁻⁶ to 10⁻³), byte loss, burst noise, truncated frames, CRC errors, wrong baud rate, cable disconnected 0.1–30 s, a peer gone silent | NF: no crash, PTT sources gone ≤ 3 s. Stock: CRC logs, re-arm after ~200 ms (Main) or ~2 s (Control) (HIGH) |
| Power | DC removed at a random VT moment, with emphasis on EEPROM page writes, rewriting `config.ini`, SD writes, (NF) own writes, sleep and wake transitions | No corrupt persistent state that blocks the boot. Stock: a NOR without a valid file system is formatted automatically (VERIFIED) |
| Network | Packet loss, reordering, duplication, jitter, PHY link down and up, CH394 SEND hangs, INT# stays stuck, the hard reset fails, **session loss during network PTT** | NF: sessions resume, TX watchdog intervenes. Stock: the recovery ladder (A5.9, A5.13); the PTT behavior on session loss recorded (A5.10) |
| Silent host | P1 host, TCI client or CI-V host goes silent during MOX | TX off within T_wd (C-P8, C-T4) |
| Plant | high SWR, overtemperature, Vext 10.5 and 15.5 V, Idd runaway, FPGA stuck sample, underrun, ADC overload | NF: the safety gates (§10.4). Stock: only logs and fan, no TX inhibit (VERIFIED, `main_unit/docs/flow.md`) |
| Peripherals | I2C NACK or hang, SPI flash WIP stays stuck, SD removed during write, BT module stays silent | No hang of the superloop |
| Clock and time | DRDY rate ± 10 %, DRDY drops out, I2S clock drops out | Underrun detection, no crash |
| Power supply | PH5 pulled low without panel, PH9 loss (H1), DC dips | Stock: the pitfall reproducible (PW-1). NF: P-1, P-2 |

### 8.6 Determinism, record and replay

- **The input queue** contains every external stimulus as {VT, target, data}
  (UART RX, UDP or TCP in, input events, plant and PowerModel parameters,
  fault actions). In the deterministic lane it comes from the
  test script, in the live lane from the host with a VT stamp.
- **A recording** = the run manifest plus the input queue. Replay
  under the same manifest MUST produce bit-identical traces.
- **Snapshots** per release ("booted and idle"), valid only under
  the same manifest (checked with a hash).
- **Seeds:** one global seed; each model RNG a derived seed per
  name.
- **Forbidden in the deterministic lane:** wall-clock time,
  host sockets and unseeded randomness (detected via
  harness wrappers).

### 8.7 L6 — Performance and timing budgets

The emulator measures *functional* timing; budgets are margins in VT,
confirmed on HIL where possible.

| Budget | Definition | Target for the NF | Remark |
| --- | --- | --- | --- |
| CH394 throughput | Net payload per s, modeled with the SPI6 byte timing (17.19 Mbit/s raw) and the access overhead | P1 48 kHz: ≥ 6.3 Mbit/s EP6+EP2 with ≥ 30 % margin; 96 kHz: 9.4 Mbit/s with ≥ 15 % margin | `docs/hpsdr_gap_analysis.md` §2.4 (derivation, HIGH). The real CH394 limit is unknown (Q4); the public manual states up to 62 MHz SPI (HIGH) |
| SPI6 bus utilization | Fraction of VT that CS is active | ≤ 80 % | — |
| IRQ rates | Per source | Documented and stable | Stock reference: TIM5 and TIM17 20 kHz, TIM7 1 kHz, TIM6 100 Hz, SysTick 1 kHz, EXTI10 ~48 kHz (HYPOTHESIS), I²S DMA 250 Hz |
| ISR latency and deadline | In VT instructions | Every ISR with a deadline (FPGA DRDY 20.8 µs) ≤ 50 % | Indicative only |
| CPU load | Fraction of non-idle instructions | ≤ 70 % average, ≤ 85 % peak, at P1 96 kHz plus TX | MIPS factor per core; stock load meter as reference |
| Link utilization | Fraction of the byte time on USART2 | ≤ 70 % (track EE) | `0x03` ≈ 12.1 ms per frame at 557 B (derivation) |
| Boot duration | From DC on to operational | ≤ stock baseline + 20 % | — |
| Wake latency | From wake packet to operational | Target ≤ 3 s | New in v0.4 |
| PTT latency | From MOX to RF in the plant | ≤ 20 ms (target), ≤ 50 ms (requirement) | Stock: arbiter at 10 ms plus 200 zero samples (VERIFIED) |

**Emulator speed** (CI budget): target ≥ 0.25× real time for the
coupled emulation at rate index 3 without network streams, ≥ 0.1× at
P1 96 kHz (HYPOTHESIS, to be measured in M1).

### 8.8 CI orchestration

| Pipeline | Trigger | Content | Runner |
| --- | --- | --- | --- |
| `fast` | every push | L0, L1, L2 | public allowed (no stock needed) |
| `pr` | PR | `fast` + L3 subset + L4a core | **private** (the local image-map is needed) |
| `nightly` | daily | Full L3, L4a, L4b, L5 (1 h fuzz, fault matrix), L6, soak 1 h VT | private |
| `weekly` | weekly | L3 over the whole version matrix, soak 24 h VT, extended fuzz campaigns, all boot-state profiles, L4c (track EE) | private |
| `release-gate` | manual | Everything plus the gate evaluation (§9, §10) | private |
| `vendor-ingest` | new files in the image-map | R0–R5 (§7) | private |

A private runner reads the images exclusively from its own local
image-map (configuration setting), has no outbound network during
tests, and contains no key or decryption tool. NF tests that do not need a
stock image (L4a, EH) MAY run on public runners.

### 8.9 Artifacts

| Artifact | Format | Visibility |
| --- | --- | --- |
| Run manifest | JSON | public (hashes only) |
| Test results | JUnit XML plus JSON | public for the NF; private for stock |
| Traces | JSONL.zst plus hash | private (stock), public allowed (NF) |
| Link captures | binary plus decoded | same |
| Network captures | pcapng, with the dissectors from `g7250-base/tools/wireshark` | same |
| Screenshots | PNG plus hash | private (stock), public allowed (NF GUI) |
| Audio | WAV (codec and FPGA sinks) | same |
| Coverage | lcov/HTML (NF via DWARF); function coverage of stock (private) | — |
| Quality report | JSON plus HTML/Markdown | public for the NF |
| Recordings and snapshots | binary plus manifest | private |
| Heatmaps and diff reports | JSON/HTML | private (RE side) |

---

## 9. Quality metrics and score

### 9.1 Metrics

| Code | Metric | Calculation | Source |
| --- | --- | --- | --- |
| Q-CONF | Conformance | Per suite. Critical path: P1, TCI, EH (including the power modes) and optionally CI-V over the network; low priority: ES; optional track: NF-link and NF-Control. Σ(weight × passed) / Σ weight, weights critical 5, important 3, normal 1 | L4 |
| Q-SAFE | Safety invariants | Number of violations (plant oracles, watchdogs, caps, no TX in sleep) | L4–L6, fault |
| Q-COV | Code coverage of the NF | Line and branch coverage from the execution trace plus DWARF | all layers |
| Q-REQ | Requirement coverage | Fraction of NF requirements with ≥ 1 passed test | traceability matrix |
| Q-TIME | Timing margin | min over the budgets of (1 − measured/limit) | L6 |
| Q-FAULT | Fault recovery | Fraction of fault scenarios with the expected recovery | L5 |
| Q-FUZZ | Fuzz robustness | Unique crashes or hangs (must be 0) | L5 |
| Q-STAB | Stability | Soak hours without a fault, including sleep and wake cycles | L3/L6 |
| Q-RES | Resources | Flash, RAM, stack depth, heap watermark | build + L6 |
| Q-STAT | Static quality | Compiler warnings (= 0), new static-analysis findings | L0 |
| Q-DET | Determinism | Identical hashes over 3 runs | L3/L4 |
| Q-TWIN | Twin fidelity (HIL) | Agreement between emulator and HIL outcomes on black-box observables | L7 |

### 9.2 Score and verdict

**Hard gates** (each blocking): Q-SAFE = 0; Q-FUZZ = 0; Q-DET =
identical; all critical conformance items passed; the static
brick checks (§10.1) passed.

**Weighted score** (0–100), only if all hard gates are green:

```
score = 30·Q-CONF + 15·Q-REQ + 15·min(Q-COV_branch/0.80, 1) + 15·Q-FAULT
      + 10·clamp(Q-TIME/0.30, 0, 1) + 5·Q-STAB_norm + 5·Q-RES_norm + 5·Q-STAT_norm
```

`Q-STAB_norm` = min(soak hours / 24, 1); `Q-RES_norm` = 1 at flash ≤ 85 %,
RAM ≤ 80 % and stack margin ≥ 25 %, otherwise linear down to 0;
`Q-STAT_norm` = 1 − min(new findings / 20, 1).

| Verdict | Condition | What it permits |
| --- | --- | --- |
| **RED** | A hard gate failed | nothing |
| **AMBER** | Hard gates green, score < 75 | further development in the emulator |
| **GREEN-EMU** | score ≥ 75; Q-CONF(P1) = 100 % critical items; Q-CONF(TCI) ≥ 95 %; Q-CONF(EH) = 100 % including PW-5/PW-6; ES items C-S2/C-S3 = 100 %; Q-FAULT ≥ 90 %; Q-TIME ≥ 0.2; rollback compatibility of Main = 100 %. Track EE additionally: Q-CONF(NF-link) = 100 %, Q-CONF(NF-Control) ≥ 95 % | handover to the firmware project (gate E4) |
| **GREEN-HIL** | GREEN-EMU + score ≥ 85 + twin validation of stock passed + F0–F2 fulfilled (F3 only for track EE) | first flash of the NF-Main on the real radio (RX-only build) |
| **RELEASE** | GREEN-HIL + the HIL suite on the real radio passed in all TX steps + 24 h soak (emulator) + review | publishing the NF |

### 9.3 Report

One report per build (JSON plus HTML): summary and verdict, hard
gates, the score with contributions, the trend, failed tests with links to
the artifacts, the traceability matrix, the timing budgets, the
safety oracles per invariant, and the known-deviations register.
The report is the only form in which results go to the NF team
(§12.2).

---

## 10. Minimizing brick risk

The emulator cannot eliminate the brick risk, but it can reduce it. It
enforces what is testable on the firmware side: no writes to
sector 0 or the option bytes, a rollback-compatible persistent state,
safe defaults and TX safety. How an image gets onto the radio, and
recovery via the vendor procedure, are dependencies of the
firmware project (§10.3, §15).

**Risk profile per track.**
- **Critical path (NF-Main only):** only the Main gets an NF image;
  the Control stays stock. The recovery path must be proven for the
  Main. The stock Control must not be damaged by the NF-Main
  (S-ES3, E-B2).
- **Optional track EE:** two units flashed, with a higher
  brick risk; the recovery path must then be proven for both units.
  Different NF versions on Main and Control are allowed; the
  NF-link negotiates (C-L10).

### 10.1 Ground rules (normative for the NF and its tooling)

1. **Sector 0 and the option bytes are sacred, on every MCU with an
   NF image.** The NF MUST NOT write to or erase sector 0 (`0x08000000`–`0x0801FFFF`),
   and MUST NOT modify option bytes (RDP,
   BOOT_ADD, WRP, BOR, IWDG bits, CPUFREQ_BOOST). Reason: to current
   knowledge the vendor bootloaders are the recovery path; the
   owner does not open the radio, so SWD recovery does not exist; according
   to the docs the update logic resides entirely in the bootloaders (HIGH,
   `main_unit/docs/peripherals.md`).
   - **Dynamic check in the emulator:** the FLASH model reports every
     unlock attempt and every write or erase action on sector 0 or the
     option bytes as a hard error.
2. **No flash programming in the app.** Stock contains no flash or
   option-byte unlock key (VERIFIED, `main_unit/docs/flow.md`). The
   NF follows that: persistent data to the EEPROM (Main) or to NOR and
   SD (Control), never to the internal flash. A custom updater is a
   separate, reviewed design outside this specification (§15).
   - **Static check:** the NF images contain no FLASH_KEYR or
     OPTKEYR key patterns (literals or MOVW/MOVT pairs) and no
     writes to FLASH_CR, OPTCR or OPTSR_PRG (gate E0).
3. **The persistent state remains usable for stock.**
   - **Main (EEPROM):** the NF MUST read the vendor records but MUST NOT
     modify them: settings `0x0000`, calibration `0x0800`, NVPARAM
     `0x1000`, ATU `0x1800`–`0x24A7` (VERIFIED layout,
     `main_unit/docs/memory_map.md`). Own data only in a dedicated,
     version-tagged area above `0x24A7`, within the minimum
     EEPROM size (24C128: up to `0x3FFF`, HIGH); more space must be
     detected safely by the NF itself (HYPOTHESIS about the actual size).
   - **Control (NOR and SD; track EE and ES):** the FAT volume `1:` and the
     stock files (`config.ini`, band-stack files, `cwcall.ini`,
     memory channels; `control_unit/docs/storage.md`) remain
     unchanged; own data in own files or folders; never
     reformat (stock would automatically format a volume without a valid
     file system, VERIFIED). The backup domain (marker
     0xA5A5) remains compatible (VERIFIED).
4. **Safe defaults at every boot:** bias 0, T/R on RX, drive 0, the
   latch outputs active only after the first valid frame (as stock
   uses the OE pattern, HIGH); TX only after a passed self-test
   (I2C devices, FPGA bus test, Vext within the window, Idd at rest).
5. **Self-protection of the image.** A dedicated integrity field (CRC or
   hash in a trailer within the app slot), checked at boot.
   On a mismatch a **safe mode**: no TX, PA de-energized,
   network functional, a clear message via P1, TCI and the
   management protocol.
6. **Boot-loop protection.** A counter for consecutive
   watchdog resets in the own persistent area; after N = 3 resets
   within T, safe mode.
7. **TX safety is independent of the panel.** All
   TX safety gates (§10.4) reside in the NF-Main and do not depend
   on the presence, the version or the capabilities of a panel.

### 10.2 Emulator tests for brick prevention

| Test | Content | Requirement |
| --- | --- | --- |
| **E-B1 — Rollback compatibility Main** (critical path) | Run NF-Main (EH and ES), with EEPROM use, fault injection and power loss during its own writes; then **stock Main** in SS on the same EEPROM and the same backup SRAM | Stock passes A1 and A8; the vendor records are byte-identical |
| **E-B2 — Stock Control intact** (critical path, from ES) | After an ES run (including switching on and off and power loss) restart the stock Control in SS | Stock passes A1.4–A1.6 and A6.2 with the pre-existing `config.ini`; NOR, SD and backup domain byte-identical (C-S3) |
| **E-B3 — System rollback** (critical path) | An SS run directly after an EH or ES run on the same media | The persistence subset of A1–A12 is green |
| **E-B2c — Rollback compatibility NF-Control** (track EE) | Run NF-Control, then stock Control on the same media | No auto-format; stock files byte-identical |
| **E-B4 — Power loss during its own persistent writes** | A stratified sample across page, sector and file boundaries | The NF boots, possibly in safe mode; the vendor records intact |
| **E-B5 — Self-test fails at first boot** | Missing I2C devices, broken FPGA bus, Vext outside the window | Safe mode, TX blocked |
| **E-B6 — Different NF versions** (track EE) | Version matrix NF-Main against NF-Control (C-L10) | Graceful degradation; TX safety entirely in the NF-Main |
| **E-B7 — Flash and option-byte monitoring** | Every machine with an NF image, for the whole L3 to L6 suite | 0 unlock attempts, 0 writes to sector 0 or the option bytes |
| **E-B8 — Boot-state profiles** | The NF in all profiles of §4.3, and for the Main with the PowerModel variants (§3.8.6) | Correct boot in every profile and every variant |

**Limitation (explicit).** These tests only prove that the NF does not damage the
hardware and the persistent state, and that stock works after a
rollback. They prove nothing about the bootloaders or the update path
on the real radio. That is up to the firmware project (§15).

### 10.3 Phased gate policy

**Gates on the emulator side** (the responsibility of this project):

| Gate | Name | Content | Exit criterion |
| --- | --- | --- | --- |
| E0 | Static | Reproducible build of the NF-Main (and later the NF-Control), bit-identical in two environments; the image layout (vector table at `0x08020000`, size ≤ app slot, entry within the image); the brick scan (§10.1.2); an image and secrets scan | all green |
| E1 | Emulator: functional | L2, L4a complete in EH (including PW-2–PW-6 and PW-8 under H1 and H2); L4b safety items C-S2/C-S3; verdict ≥ GREEN-EMU. Track EE: additionally L4c | §9.2; PW-5 and PW-6 = 100 % |
| E2 | Emulator: robustness | L5 (fuzz ≥ 24 h cumulative without findings, including the ES corpus; fault matrix ≥ 90 %); E-B4, E-B5, E-B7, E-B8; PW-7; 24 h soak in EH with sleep and wake cycles. Track EE: additionally E-B6 | 100 % for the listed E-B and PW tests |
| E3 | Rollback compatibility | E-B1–E-B3. Track EE: additionally E-B2c | 100 % |
| E4 | Handover | A report package per build for the firmware project: the quality report, the gate results E0–E3 and the image hashes | complete |

**Gates on the bench with stock** (HIL, black-box):

| Gate | Name | Content | Exit criterion |
| --- | --- | --- | --- |
| H-G1 | Twin validation | §11.3 phase H1–H2: the black-box observables of the emulator match the real radio, which runs stock | Q-TWIN ≥ the threshold per observable |

**Dependencies of the firmware project** (not gates of this
project; they MUST be fulfilled before an NF image goes onto the real radio,
§15):

| ID | Dependency | What this project expects |
| --- | --- | --- |
| F0 | **R0 answered** (§3.8) | Determines whether the HIL setup is EH, or the Main with a stock panel only to power on (ES rules) |
| F1 | **Rollback drill to stock for the Main** (critical path) | On the real radio, apply the official vendor update for the Main according to the vendor procedure, then pass the stock HIL smoke. Proven before the first NF-Main flash. Track EE: the same drill for the Control before the first NF-Control flash |
| F2 | Installation path of the NF clarified | A written decision by the owner |
| F3 | **Track EE only:** a flash procedure for two units | Order, behavior with different versions, recovery of every intermediate state to stock |

**HIL with the NF-Main** (only after E0–E4, H-G1, F0, F1 and F2):

| Gate | Name | Content | Exit criterion |
| --- | --- | --- | --- |
| H-G2 | HIL dry run NF-Main, **RX-only build** | TX disabled at compile time; operation via P1 and TCI (AetherSDR or another host, and the reference host); the Control stays stock, disconnected (EH) or connected under the ES rules (according to F0); RX tests and power modes; then back to stock Main (F1 procedure) | all green + rollback passed + stock Control intact |
| H-G3 | HIL NF-Main, **low-power TX** | Cap ≤ 5 W, exclusively into the dummy load via the bench switch (§11.4); stepwise TX tests via P1 and TCI; then back to stock | all green, 0 safety incidents |
| H-G4 | NF-Main normal use | The limits of the user configuration, never wider than the band and power limits of the radio | release verdict |
| H-G5 | **Track EE:** HIL with NF-Control | As H-G2/H-G3, with F1 (also for the Control) and F3 fulfilled | same |

**Rules:** a gate is passed only with a recorded report
and an explicit go from the owner; every code or model change that
touches the NF falls back to E0; after H-G2 and H-G3 the radio is **always
back on stock** until a next scheduled session, unless the owner
decides otherwise.

### 10.4 TX safety gates (limits only)

These requirements apply to the NF. They are enforced in the emulator by
the plant oracles and in HIL by the bench measurements. They only restrict;
this specification describes no way to widen or circumvent band or power limits.

| # | Gate | Requirement |
| --- | --- | --- |
| S1 | Power cap | A compile-time build cap (RX-only = no TX; test = ≤ 5 W; normal = ≤ the nominal 100 W) plus a runtime cap ≤ the build cap; the drive is clamped |
| S2 | Permitted frequencies | TX only within the intersection of (a) the radio's own band table (calibration block, `main_unit/docs/flow.md`), (b) the configured bands and (c) the hard window of the radio. Never wider than (a) |
| S3 | Host and session watchdog | P1 and TCI: no valid traffic within T_wd (≤ 1 s, target ≤ 250 ms) and hence TX off. **Network PTT drops on every session loss** (the counterpart of upstream report #2). CI-V: a PTT timeout, not wider than stock (10 s, VERIFIED) |
| S4 | Time-out timer | Maximum continuous TX duration (default 180 s; test build 30 s) |
| S5 | SWR protection | Fold back above a threshold (e.g. 2.5:1), TX off above a higher one (e.g. 4:1). Stock does not have this (VERIFIED) |
| S6 | Temperature, Vext and Idd | TX off outside the windows, with hysteresis |
| S7 | Sequence interlock | Relays (T/R, LPF, ATU) only without drive; a minimum settle time before the drive. Stock has no explicit delay (VERIFIED) |
| S8 | LPF verification | The selected LPF covers the TX frequency, otherwise no TX |
| S9 | ATU | Tuning only with ≤ 10 W carrier (as stock, VERIFIED) and not above 54 MHz |
| S10 | Safe boot | §10.1.4–6 |
| S11 | Power modes | No TX in sleep; a safe state on entering sleep; TX only after a full wake and a self-test; PH5 ignored by default (§3.8.4) |

### 10.5 Rollback procedure

The procedure belongs to the firmware project (F1, §15). This project requires:
1. **Precondition:** the rollback drill has passed at some point for every unit
   that has received an NF image (on the critical path only the Main),
   and the official vendor package of the last known good release
   is ready locally, with a hash that matches the
   `provenance` line of the manifest (§4.4).
2. **Execution:** exclusively the official vendor procedure with the
   official vendor file.
3. **Verification:** the HIL smoke (boot, version via CI-V, CI-V basics,
   RX audio, ping to the default or configured IP).
4. **Record** in the HIL logbook: date, versions, result.

---

## 11. HIL integration (final phase)

### 11.1 Principles

- The **owner's existing test bench** is reused: multiple
  radios and antennas, a microHAM antenna switch with
  SharkRF integration, controlled by a Claude-based agent, and
  in daily use for Hermes-Lite 2, AetherSDR and AnySDR.
- **Tier-0 observations only** (`docs/hardware_test_plan.md`): the radio
  stays closed, nothing is measured on the board, no SWD.
  Observables are the external interfaces: CI-V over USB, LAN
  (Icom-LAN, HDSDR, later P1 and TCI), USB audio, RF via bench receivers,
  and the display of the bench power supply (T0-P1).
- **Low power and behind gates:** TX exclusively ≤ 5 W into a 50 Ω
  dummy load of ≥ 100 W, on an amateur band within the licence.

### 11.2 Architecture: one test API, two targets

```
        testcase (pytest, tagged @emu / @hil / @both)
                    |
            Target-interface
      +-------------+--------------+
  EmuTarget                     HilTarget (adapter to the bench agent)
  - Renode (Main, Control)      - lease of the G7250 lane via the bench's existing lease mechanism
  - VLAN, PTYs, plant           - CI-V: USB serial (CH342 port)
  - PowerModel                  - LAN: an isolated test subnet (192.168.3.x/24 for stock cold starts)
  - input injection             - audio: the radio's USB sound card
  - framebuffer                 - RF: bench receiver (e.g. an HL2 via an attenuator/sampler)
                                - switch: microHAM (dummy load or antenna), SharkRF integration
                                - power supply: switchable 13.8 V in the station automation
```

**What HIL cannot do** (remains `@emu`-only): input injection on keys,
touch and encoders; screenshots (a fixed camera MAY be used for comparison);
link taps, plant oracles and internal state.

**HIL observables with an emulator equivalent:** CI-V responses and
latencies; the LAN behavior (handshake, timing, packet rates, ping); RX audio;
the S-meter against a calibrated signal; TX power, frequency,
spectral purity and keying behavior (bench receiver); CI-V meters (Po,
SWR, Vd, Id); the supply current (if the bench power supply shows it).

In HDSDR mode the HDSDR ExtIO DLL from the vendor package (§4.4) MAY serve as a
black-box client; it is not analyzed.

### 11.3 HIL phases

| Phase | Firmware | Content | Gate |
| --- | --- | --- | --- |
| H0 | stock | Inventory (T0.1, T0.2, T0.7–T0.10): ports, VID/PID, the CI-V route; update `wiring.yaml` and the "USB-CAT" mapping. **Plus the cold-start observations T0-P1–T0-P4 for R0** (§3.8.3) | delivers F0 |
| H1 | stock, RX-only | Twin validation RX: CI-V coverage (A4, black-box), Icom-LAN (A5, own scripts), HDSDR rate per span (T0.3), I/Q orientation (T0.4) | — |
| H2 | stock, TX ≤ 5 W dummy | TX twin: power against the setting, PTT latency, CW keying, frequency set via LAN and read back via USB CI-V, RX during TX (T0.5) | H-G1 |
| — | stock (Main) | **Dependency of the firmware project:** rollback drill F1, installation path F2; the bench only verifies (stock HIL smoke) | F1, F2 |
| H3 | NF-Main, RX-only (critical path) | Setup according to F0; operation via P1 and TCI from AetherSDR or other SDR software; power modes | H-G2 |
| H4 | NF-Main, TX ≤ 5 W (critical path) | | H-G3 |
| H5 (track EE) | NF-Main + NF-Control | Only after F1 for the Control and F3 | H-G5 |

### 11.4 HIL safety protocol (bench)

**Fixed rules for every session** (supplementing §3.8.3):
- **Dummy load on every antenna output** the radio can select, unless
  a gate explicitly permits an antenna (not in this
  specification).
- **No wfview and no other CI-V or LAN client that can set PTT**,
  except the dedicated test script controlled by the bench agent
  during a scheduled TX step. With stock, upstream report #2
  (HYPOTHESIS/MEDIUM) applies here: a session loss can leave PTT
  stuck; the test script MUST therefore always be able to terminate PTT explicitly via a
  second route (USB CI-V) and by switching the power supply.
- **Never disconnect or connect the CTRL cable with DC on.**
- **Never press Enter on a Main console.**

**Procedure:**
1. **Preflight by the bench agent:** the switch on the dummy load; the
   dummy load present (SWR check at low power); the radio's power
   at the minimum (stock: 5 W via CI-V `14 0A`,
   `main_unit/analysis/protocol/civ_main.csv`); the frequency within the
   licence and the allowlist; no unauthorized client on the
   test subnet (a network scan for open sessions).
2. **Interlock:** do not switch the antenna during TX; first confirm RX
   via CI-V and the bench receiver.
3. **Abort conditions:** measured power > 1.2 × cap; SWR > 2:1 on the
   dummy; unexpected TX without a command; loss of the control interface;
   temperature rise. On an abort: PTT off via every available
   route, otherwise the 13.8 V off.
4. **Maximum TX duration per step** ≤ 10 s, with a pause between the
   steps.
5. **Logbook:** firmware versions, settings, measured values; no raw
   captures with passwords in a repo (throwaway credentials,
   `docs/hardware_test_plan.md`).

### 11.5 Feedback into the models (black-box only)

A HIL deviation leads to a hypothesis about the model (the
SEND latency of the CH394, the plant curve, the DRDY rate, the
PowerModel). The adjustment is made in the emulator; afterwards the
stock baseline must be green again. The golden sets change only via
R8 (§7).

---

## 12. Clean room and legal separation

### 12.1 Two sides

| | RE side | Specification and NF side |
| --- | --- | --- |
| Repos | `g7250-base` (private working tree plus public docs), `g7250-emu` (including the private golden sets, outside git) | `g7250-his` (hardware interface spec), `g7250-fw` (clean-room NF) |
| May use | The images supplied by the user (local, own copy), Ghidra output, the full `g7250-base` docs, heatmaps, internal traces, RAM watches, golden sets | The **HIS** (§12.2), public datasheets and protocol specs (P1, TCI, CI-V), the **public vendor documentation** (CI-V reference rev. 1.2, the rig file, the release notes; §4.4), **black-box test results**, the emulator as a **tool** with the hardware models |
| May not use | — | Decompiled or disassembled code, firmware bytes, literal firmware strings, internal traces of stock (PC, RAM, addresses), heatmaps, golden screenshots and traces, and descriptions of stock software behavior (the stock SLIP link, the stock GUI, the DSP chains) as a source for implementation choices; analysis of vendor software (e.g. the ExtIO DLL) |

**On the dropped interoperability argument.** The NF does not need to
interoperate with stock; the NF link is an original design, and
`docs/protocol.md` is not a source for the NF team. What the NF needs
is **hardware knowledge** (FPGA, CH394, PA, RF circuits, DACs, codecs,
display, input). That reaches the clean-room side exclusively via the HIS.

**On the models.** They describe **hardware**: pins, chips,
registers, the documented wiring. Each model MUST state the source per
property: datasheet, HIS section, `g7250-base` doc (RE side
only) or HIL measurement. Behavior that serves only to make stock
succeed (quirk compatibility) MUST be marked as such and may
not steer the NF.

### 12.2 Processes

1. **Information gate: the HIS.** Knowledge passes from RE to NF only via the
   HIS, a reviewed, separately versioned document (repo `g7250-his`).
   - **Content:** per hardware block the *what* and the *how to drive it*,
     as hardware fact: MCUs, clocks, memory, pins; FPGA bus and
     command set, NCO word format, I/Q format; CH394 on SPI6
     (W5500-compatible, including WOL); SPI1 latches and their bits;
     SPI2 DAC channels; ADC channels and scale; AXP223 rails, VC6,
     codecs; the power supply path (PH9/PH5, H1/H2 once decided); the
     EEPROM layout of the vendor records (only to protect them);
     display, touch, key matrix, encoders, H-22, NOR, SD, BT; the
     CTRL cable wiring with confidence; the safety-relevant
     hardware limits.
   - **Excluded:** stock software behavior that is not a hardware fact.
   - **Every HIS line** has a confidence label and a provenance
     (datasheet, public source, HIL measurement, or "RE-derived
     hardware fact", without addresses or code).
   - **Review** by a second person or agent for the omission of
     software details; `tools/check_docs.py` from `g7250-base` (rejects
     literal firmware text) also runs on the HIS and the NF repo.
2. **Agent instructions.** Agents working on the NF do not read
   RE artifacts (the private analysis output, golden sets, heatmaps).
3. **Black-box results.** The NF team sees only the
   quality report (§9.3).
4. **Provenance log.** Every NF requirement refers to its source.

### 12.3 Distribution

- **Never distributed:** vendor images in any form (decrypted or
  encrypted), vendor packages, golden screenshots and traces of stock,
  recordings with stock behavior, heatmaps.
- **Every user supplies their own** decrypted images. The
  emulator contains no key, no decryption code and no
  hint on how to obtain one; the repo contains only hashes.
- **The public `g7250-emu`** contains: the models, the harness, the
  test definitions, the hash manifest, the documentation, the own
  test firmwares and the NF results.

### 12.4 Legal points of attention

| Topic | Core | Relevance |
| --- | --- | --- |
| Directive 2009/24/EC (Software Directive), Art. 5(3) | The lawful user may observe, study and test the functioning of a program while loading or running it | The core of the emulator baseline: running one's own, lawfully obtained firmware in order to study it |
| Ibid., Art. 6 (decompilation for interoperability) | Permitted under conditions | The NF does not interoperate with stock; the external protocols of the NF (P1, TCI, CI-V) are public. What remains is the use of RE-derived **hardware knowledge** via the HIS. That runs exclusively through the reviewed HIS: hardware facts, no stock implementation (§12) |
| Ibid., Art. 7(1)(c) | Prohibition on putting into circulation or possessing for commercial purposes any means whose sole intended purpose is to circumvent technical protections | **Does not apply to our own tooling:** the emulator contains no decryption code, no key handling and no way to decrypt images; it only reads images supplied by the user and hashes the vendor package as provenance |
| Obtaining and using the images | How the user obtains and uses the decrypted images is outside the emulator | Responsibility of the user; the emulator does not decrypt, encrypt or package anything and does not distribute images |
| Directive 2001/29/EC, Art. 6 | Protection of technological measures; for software, the Software Directive applies first and foremost (Art. 1(2)(a)) | ibid. |
| Belgian law | The transposition is in the Code of Economic Law (Wetboek van economisch recht), Book XI (the title on computer programs, formerly the Act of 30 June 1994) (HIGH) | The concrete application in Belgium |
| Directive 2014/53/EU (radio equipment) | Amateur equipment that is not placed on the market, and commercial equipment modified by and for radio amateurs, fall outside the directive (Annex I) (HIGH) | Own use of the NF on one's own radio |
| License (BIPT) | TX tests within the amateur license | The HIL gates (§11.4) |
| Library licenses | STemWin only on STM32 under the ST license; HAL BSD-3; CMSIS Apache-2.0 (`docs/libraries.md`, `control_unit/docs/gui.md`) | The NF Control (track EE) MUST use its own GUI library or one with a suitable license |
| Vendor documentation | The CI-V reference, the rig file and the release notes are publicly published by the vendor | May serve as a source; do not redistribute without permission; only use the ExtIO DLL, do not analyze it |
| Trademarks | "Icom", "wfview", "Xiegu" only descriptively | No imitation of branding |

Packaging the NF in the vendor update format is a question for the
firmware project (§15). Publication follows only the umbrella rule: an
explicit approval from the owner of the repository.

---

## 13. Repository layout `g7250-emu`

### 13.1 Structure

```
g7250-emu/
├── README.md                  purpose, quickstart (without images), status per vendor release
├── CLEANROOM.md               the rules of sec. 12, for humans and agents
├── SECURITY.md                image policy (local only, only hashes in git), reporting leaks
├── LICENSE                    MIT or Apache-2.0 (own code)
├── AGENTS.md                  agent instructions (RE side; NF agents do not work in this repo)
├── pyproject.toml / Makefile
├── deps/
│   └── g7250-base.lock        pinned commit of g7250-base (docs and CSVs as data)
├── images/
│   ├── manifest.yaml          releases: image hashes (by the user), sizes, vectors, provenance (vendor package hashes)
│   └── verify.py              check of images from the local image-map; rejects on mismatch
├── platforms/
│   ├── g7250_system.resc      two machines, LinkCable, CTRL cable, VLAN (SS, ES, EE)
│   ├── g7250_main_headless.resc   Main only, CTRL cable disconnected, VLAN (EH, primary)
│   ├── g7250_main.repl        H72x-derived
│   ├── g7250_control.repl     H743-based
│   └── profiles/              boot-state profiles (clean, iwdg-hw, …), PowerModel H1/H2, hardware profiles
├── models/
│   ├── stm32h7/               RCC, PWR, FLASH, SYSCFG/EXTI, GPIO, DMA/DMAMUX/BDMA/MDMA, USART, I2C,
│   │                          SPI/I2S, ADC, DAC, TIM, RTC, IWDG, CRC, LTDC, DMA2D, FMC, SDMMC, OTG-stub, DBGMCU
│   ├── devices/               CH394, FPGA (fused with GPIOE), AIC3204, EEPROM24C, AXP223, VC6, BU2506,
│   │                          ShiftLatch, GT911, PCA9557, W25Q, SDCard, BT401, KeyMatrix, QuadEncoder, H22Mic
│   ├── system/                LinkCable, CtrlCable (wiring.yaml), PowerModel, Plant (PA, detectors, NTC,
│   │                          load, ATU network), oracles
│   └── python/                prototypes
├── harness/                   Python package `g7250emu`
│   ├── core/                  run, manifest, VT clock, snapshots, recording and replay, image-map configuration
│   ├── io/                    UART demux, VLAN, UDP offload, TAP, pcapng
│   ├── inject/                keys, encoders, touch, H-22, plant, power supply, faults
│   ├── observe/               traces, screenshots, audio, oracles, hang detector
│   ├── protocols/             slip (wrapper around g7250-base/tools/g7250; baseline only), civ, icomlan,
│   │                          hdsdr, p1host, tciclient, nflink, wake (UDP wake, magic packet)
│   ├── targets/               emu, hil (adapter to the bench agent)
│   └── report/                score, report, traceability
├── firmware-tests/            own small test firmwares (L2), clean-room
├── tests/
│   ├── unit/                  L1
│   ├── integration/           L2
│   ├── baseline/              L3 (scenarios A1–A12; require the local image-map)
│   ├── conformance/           L4a (p1, tci, civ-net, headless, power), L4b (es-robustness), L4c (nflink, nfcontrol)
│   ├── brick/                 E-B1–E-B8
│   ├── fault/ fuzz/ perf/     L5, L6
│   └── hil/                   L7 (gated)
├── matrix/version_matrix.yaml
├── ci/                        pipeline definitions
├── docs/                      design docs, this specification, model docs with source attribution
└── .private/  (gitignored)    golden sets, recordings, heatmaps, runs; alternative: a separate private artifact store
```

The image-map itself is **not** in this structure: it lives outside every
repo, at a path from the local configuration.

### 13.2 Relationships

```
            g7250-base  (RE knowledge: docs + CSV, public; private working tree with evidence)
             |      |  pinned commit (data: CSV fields, buttons, CI-V tables ...)
             |      v
             |   g7250-emu   (RE-side tooling; public: models/harness/tests/hash manifest; private: golden/heatmaps)
             |      |  delivers: emulator releases + test suites + quality reports
             v      |
         g7250-his  |  (clean-room hardware interface spec; reviewed; hardware facts only)
             |      |
             v      v
            g7250-fw    (clean-room NF: NF Main first; later optionally NF Control with the NF link;
                         reads only the HIS, public specs, public vendor docs and reports)
                +-- CI of g7250-fw calls g7250-emu (version-pinned) as a test tool
```

- `g7250-emu` depends on `g7250-base` as **data**; an update is a
  deliberate lock bump with a regression run.
- `g7250-his` is written by the RE side and is the only
  hardware source of `g7250-fw`; the models refer per property to
  the HIS section.
- The NF link specification belongs to `g7250-fw`; `g7250-emu` takes
  only the reference decoder and the conformance tests from it.
- Findings about stock go as RE docs to `g7250-base`; a push or
  PR happens only after an explicit go from the owner.
- Commits follow the owner's identity and trailer rules:
  local commits on branches, no push without a go.

---

## 14. Phased roadmap

Effort in person-weeks (pw) for one experienced developer with
agent support; rough estimates (HYPOTHESIS). M0 through M6
form phase 1 (the baseline).

| Milestone | Content | Effort | Exit criteria |
| --- | --- | --- | --- |
| **M0** Platform spike | Pin Renode; evaluate the H743 platform description; dp-FPU, MPU, DWT; measure MMIO speed; the decision point of §2.3 | 1–2 pw | Go/no-go Renode; measurement report |
| **M1** Stock Main boots to the main loop | `g7250_main.repl`; RCC, PWR, FLASH, GPIO, EXTI; DMA1, BDMA, MDMA; USART1, USART2 stub; I2C1 with EEPROM, AXP223, VC6, codec; SPI1 and SPI2 sinks; SPI6 plus a minimal CH394; TIM5/6/7/17; ADC1 plus the plant for the bias trim; DAC1; I²S3; a minimal FPGA; IWDG; PowerModel (simple); the hang detector, strict mode and heatmap; the image check from the local image-map | 4–6 pw | A1.1–A1.3, A1.7–A1.10, A1.12 for Main solo; 60 s VT without hang |
| **M2** Stock Control boots to the main screen | `g7250_control.repl`; FMC, SDRAM, LTDC, DMA2D, framebuffer capture; GT911, PCA9557, codec master, I²S2; W25Q with FatFS image; SDMMC; TIM2/3/4/5/7/8/13/14; USART1 plus BT401; USB stub; RTC plus backup domain; DBGMCU, CRC | 5–7 pw | A1.4–A1.9 for Control solo; stable screenshot of the main screen |
| **M3** Coupled system | LinkCable with byte timing; CTRL cable model; SLIP tap; power-off | 2–3 pw | A2.1–A2.4, A2.6–A2.8; A9.1 |
| **M4** Input and GUI | Key matrix, encoders, main knob, touch, H-22; screenshot pipeline | 3–4 pw | A3 complete; first golden screenshot set |
| **M5** CI-V, Icom LAN, HDSDR, RF/audio | Full CH394 (UDP), VLAN plus UDP offload; own clients (CI-V, Icom LAN, HDSDR); RX signal generator, TX sink; codec WAV I/O | 4–6 pw | A4, A5, A2.5, A9.5 |
| **M6** Baseline V1.0.1 frozen | Persistence, calibration variants, ATU, SWR scanner, CW; golden traces; determinism; nightly CI; version matrix with provenance | 3–4 pw | **Phase 1 complete:** A1–A12 green; 3 identical runs; soak 24 h VT |
| **M7** Fault injection, record and replay | §8.5, §8.6; live lane | 3 pw | Fault matrix on stock documented; A12.2 |
| **M8** Boot-state profiles and brick tests | Profiles of §4.3, B2 shim; FLASH monitoring; E0 scanner; E-B1–E-B8 with NF stand-ins | 2–3 pw | E-B1–E-B8 executable; stock green in all profiles |
| **M8b** HIS v1 | Draft the HIS from the `g7250-base` docs, with review (§12.2) | 2–3 pw (RE side, parallel) | Reviewed HIS v1 |
| **M8c** R0 investigation (critical path, early) | §3.8.7 steps 1–2: PowerModel H1/H2, stock Main without Control (PW-1); the docs; prepare the observation protocol T0-P1–T0-P4 | 1–2 pw (can start as soon as M1 is done) | Report with the emulator outcome and a ready protocol for the owner |
| **M9** Conformance framework NF Main (critical path) | Reference P1 host, TCI client, optionally CI-V over the network; EH; power modes (PW-2–PW-8); replay of AetherSDR and other host sessions (C-P11); TCP and WOL in the CH394 model; safety oracles as hard failures | 5–6 pw (parallel to NF Main development) | The suites run in EH against an NF Main stand-in |
| **M9b** ES robustness (low priority) | C-S1–C-S4; stock panel traffic as fuzz corpus; E-B2 | 1 pw | C-S2/C-S3 green against the stand-in |
| **M10** Quality score and report | §9; traceability; handover package E4 | 2 pw | One report per build; gates E0–E4 automatic |
| **M11** HIL with stock | H0–H2; twin validation; the cold-start observations for R0 | 3–4 pw (depends on the bench) | H-G1, F0 |
| — | **Dependency on the firmware project:** F1, F2 | outside this project | fulfilled |
| **M12** HIL with the NF Main (critical path) | H3–H4 | open | H-G2, H-G3 |
| **M13** Optional own-panel track (EE) | C-L1…C-L11, C-C1…C-C7; E-B2c, E-B6; then H5 after F1 (Control) and F3 | 5–7 pw (emulator side) | L4c green; H-G5 |

**Critical path:** M0 → M1 → M2 → M3 → M6 (stock+stock baseline) → M8,
M8c → M9 (NF Main headless in the emulator) → M10 → M11 → F0–F2 → M12
(HIL with the NF Main). M4, M5 and M7 strengthen the baseline and run
partly in parallel; M9b and M13 are not on the critical path.

**Total through M10** (without M13): roughly 38–54 pw. Phase 1 (M0–M6)
alone: 22–32 pw.

### 14.1 First three concrete steps

1. **M0 spike.** A pinned Renode version with an own minimal
   test firmware (clean-room) that exercises dp-FPU instructions, MPU regions, DWT
   CYCCNT, cache maintenance instructions and a GPIO bit-bang loop;
   measure MIPS and MMIO/s. Outcome: go/no-go plus the figures for §8.7.
2. **Repo skeleton plus the image check.** In `g7250-emu`, the structure
   of §13 with `CLEANROOM.md`, `SECURITY.md`, pre-commit scans
   (image hashes, binary files, vendor extensions), the
   configuration setting for the local image-map (with the refusal
   inside a git working tree), and `images/manifest.yaml` with the provenance
   of the V1.0.1 vendor package (§4.4) and empty `image_sha256` fields that
   the user fills in.
3. **`g7250_main.repl` plus the hang detector and the heatmap.** Start stock Main
   in strict mode and clear the first polling loops (RCC, PWR,
   BRRDY, I2C) until the console shows the boot status lines and
   the default IP is in the CH394 (A1.12). That is the start of M1 and
   at once the input for M8c.

### 14.2 Risks

| # | Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| **R0** | **The Main cannot power on or operate without Control** (PH5/PH9; HYPOTHESIS) — **top priority, on the critical path** | medium (unknown) | high: EH on hardware then not usable without a connected panel | §3.8.7: (1) PowerModel H1/H2 with PW-1; (2) the docs; (3) the cold-start observations without opening the radio: supply current with the radio "off" (≈ 0 mA → H1, tens of mA → H2), CTRL disconnected with DC on (link up = CH394 out of reset; ping on 192.168.3.199 = the app is running; link that drops after a few seconds = the stock pitfall), under the fixed rules (dummy load, no PTT client). Fallbacks: with H2 everything in firmware (always-on, sleep/wake, WoL); with H1 without auto-start the stock panel solely for powering on (ES rules), or as a last resort a key-emulation contact on the CTRL connector |
| R1 | The boot-state profiles do not cover the real handover state | medium | medium | Profile matrix; read-before-write detector; E-B8; HIL H1 |
| R2 | Renode's H7 coverage is disappointing (H72x, SPI/I2S v2, DMAMUX, MDMA, OTG) | medium | high | M0; own C# models |
| R3 | The emulation is too slow (FPGA bit-bang, float DSP at 550 MHz) | medium to high | medium | Fused FPGA model; rate index 3 as default; snapshots; parallel forking |
| R4 | Determinism leaks | medium | high for the golden approach | Strict separation of the lanes; CI detection; three-run checks |
| R5 | The twin deviates from the hardware | high | medium | HIL H1/H2; parametric models; Q-TWIN |
| R6 | The user cannot supply decrypted images for a new release (format change or anti-tamper at the vendor) | medium | medium | The emulator does not depend on the format; the release remains "provenance known, not tested"; older releases remain the baseline |
| R7 | An image or package leak in git or artifacts | low to medium | high (legal, trust) | Pre-commit and CI scans for hashes, binary files and extensions; the image-map outside every working tree (enforced); private runners |
| R8 | Clean-room contamination (via the HIS or artifacts) | medium | high | §12 processes, HIS review, agent instructions, provenance log, check on the NF repo |
| R9 | Legal uncertainty around obtaining and using the images, the HIS and publication | medium | high | Distribute nothing: images, packages and derived dumps stay local; the emulator decrypts nothing |
| R10 | The NF damages the persistent state, so that stock does not work properly after a rollback | low (with E-B1–E-B3) | high | §10.1.3; gate E3 |
| R11 | FPGA TX behavior unknown, so P1 TX hard to model well | high | medium | TX sink with parameters; HIL H2 with stock; TX in the NF only after H-G3 |
| R12 | The TCP or WOL behavior of the CH394 deviates from the W5500 | medium | medium | P1-first; conservative socket settings; HIL verification |
| R13 | GUI screenshots not stable | medium | low to medium | Fixed RTC epoch; capture when "idle"; masks |
| R14 | A HYPOTHESIS wiring of the CTRL cable turns out to be wrong | medium | low to medium | `wiring:hypothesis` tags; HIL feedback |
| R15 | An underestimated effort | high | medium | Phased exits; priority on the critical path; Python prototypes first |
| R16 | The NF Control doubles the test surface | medium (optional track) | medium | M13 separate from the critical path |
| R17 | A connected stock panel causes TX or loses its settings because of the NF Main | low | high | S-ES1–S-ES3; C-S1–C-S3 |
| R18 | The behavior towards real SDR hosts deviates from the reference host | medium | medium | Recording and replay (C-P11); HIL H3 |
| R19 | A hanging network PTT of stock during bench or cold-start tests (upstream report #2) | medium | high | Fixed rules: dummy load, no PTT client, a second route and the power supply as emergency stop (§3.8.3, §11.4) |

---

## 15. Out of scope: open points for the firmware project

These points belong to the firmware project (`g7250-fw`), not to the
emulator. The emulator boots the application image directly (§4.3),
decrypts nothing (§4.1) and delivers the gates E0–E4 (§10.3).

| # | Open point | Why it matters | What the emulator delivers or expects |
| --- | --- | --- | --- |
| O1 | **Does the vendor bootloader accept an own image** (Q6, `docs/hpsdr_gap_analysis.md`)? Checksum or signature? | Without an accepted image, no installation | A structurally valid image (E0) |
| O2 | **How does the image get onto the radio?** Hypotheses: a serial bootloader on the Main console (G90 precedent) or a file on the MSC drive of Control (`main_unit/docs/peripherals.md`, `docs/related_radios.md`) | Installation and rollback procedure | Nothing |
| O3 | **The update path of the NF** (vendor bootloader or an own updater) | Maintenance and recovery | The rule "no flash programming in the app" (§10.1.2) applies until the firmware project decides otherwise |
| O4 | **Rollback drill** (F1) for the Main, and for the Control in track EE | The only known recovery path without SWD | The stock HIL smoke; the hash-checked provenance of the vendor package (§4.4) |
| O5 | **Track EE only:** flash procedure for two units (F3) | Higher brick risk | E-B6 and §10.1.7 |
| O6 | **Packaging in the vendor update format** (F2) | Question for the firmware project (§15) | Nothing: the emulator does not decrypt, encrypt or package anything |
| O7 | **Top priority (R0, F0): can the Main power on and operate without Control?** | Precondition for EH on the real radio | §3.8: facts, H1/H2, PowerModel with PW-1–PW-8, cold-start observations T0-P1–T0-P4. The firmware project implements P-1–P-11 and decides on the CH394 WOL function |
| O8 | **Track EE only:** the NF link specification (framing, baud rate, synchronization, ownership, protocol version and capability negotiation) | Basis for C-L1…C-L11 | The generic requirements of §8.3.1 and the LinkCable fault injection |
| O9 | **The G7250 P1 profile and the board ID**, the TCI command set, the CI-V command profile (with the public CI-V reference rev. 1.2 as source) | Basis for C-P, C-T and the CI-V conformance | The reference clients in the harness |
| O10 | **Behavior towards a connected stock panel**: which panel lines can be explicitly enabled, and whether the NF Main stays completely silent on the link | S-ES1–S-ES3 | C-S1–C-S4 |

---

## Appendix A — Sources

**G7250 (repo `g7250-base`):**
- `README.md`, `AGENTS.md`, `TODO.md`
- `docs/architecture.md`, `docs/mcu_identification.md`,
  `docs/hardware_init.md`, `docs/protocol.md`, `docs/civ.md`,
  `docs/dma.md`, `docs/atu.md`, `docs/cw.md`, `docs/libraries.md`,
  `docs/hardware.md`, `docs/hardware_test_plan.md`,
  `docs/hpsdr_gap_analysis.md`, `docs/related_radios.md`,
  `docs/x6100_comparison.md` (partially)
- `main_unit/docs/startup.md`, `memory_map.md`, `peripherals.md`,
  `flow.md`, `network.md`, `dsp.md`
- `control_unit/docs/startup.md`, `memory_map.md`, `peripherals.md`,
  `flow.md`, `gui.md`, `storage.md`, `voice_cw_memories.md`
- CSVs under `*/analysis/` (flow, peripherals, memory, protocol,
  storage), including `hw_init_table.csv`, `i2c_devices.csv`,
  `ram_objects.csv`, `cmd01_fields.csv`, `cal02_fields.csv`,
  `band_table.csv`, `wfview_packets.csv`, `civ_scope.csv`,
  `civ_main.csv`, `civ_control.csv`, `gpio_map.csv`, `iwdg_kicks.csv`
- `tools/g7250/README.md` (the clean-room SLIP and HDSDR tools)

**Public upstream reports** (not verified by us;
HYPOTHESIS/MEDIUM):
- `fventuri/g7250-base` issue #1: the forced network defaults of
  stock Main (192.168.3.199, gateway 192.168.3.1, netmask
  255.255.255.0, base port 50001).
- `fventuri/g7250-base` issue #2: network PTT is not released
  on session loss.

**Public vendor documentation** (from the official package
`2026-11-09_Xiegu_G7250_V1.0.1.zip`, radioddity.com/pages/xiegu-download;
only as a public source, not redistributed): CI-V reference rev. 1.2
(PDF), wfview rig file `G7250.rig` (CI-V 0xA0), release notes. The
HDSDR ExtIO DLL only as a black-box client.

**Public (platform, chips, protocols; no content copied):**
- the Renode documentation (Antmicro): multi-machine, UART hub, network and
  TAP, Python and C# peripherals, GDB, Robot, state save/load, execution
  tracing;
- the QEMU documentation (Arm machines, STM32 boards, record/replay with
  `icount`);
- the ST reference manuals RM0433 (H743) and RM0468 (H72x/H73x) and the
  datasheets;
- WCH, CH394 manual 1, version 1.2 (wch.cn): MODE bit WOL,
  GINT/GINTE bit MP, PHY_CFG power-down, SPI up to 62 MHz;
- the WIZnet W5500 datasheet; WCH CH394DS1 (as cited in the
  `g7250-base` docs);
- the AIC3204, AXP22x, 5P49V6965, BU2505/2506FV, GT911, PCA9557,
  W25Qxx and 24Cxx datasheets;
- OpenHPSDR Protocol 1 (Metis "How it works", USB protocol V1.58) and the
  Hermes-Lite 2 protocol wiki;
- the ExpertSDR TCI protocol specification;
- Directives 2009/24/EC, 2001/29/EC and 2014/53/EU, and the Belgian
  Code of Economic Law, Book XI.

*End of v0.5.*
