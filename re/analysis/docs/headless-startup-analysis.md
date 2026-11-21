# Main-unit startup and headless operation

Static analysis of the official G7250 main firmware v1.0.1, prepared with
`scripts/prepare_firmware.py` and decompiled with the repository's Ghidra scripts.
No modified firmware was produced or flashed, and no behavior was tested on a radio.

**Once the main application is entered, its startup path initializes the network
without waiting for a control-head packet. Whether connecting DC with the head
absent reaches that application remains unproven.** The update omits an explicitly
referenced bootloader at `0x08000000`, and the electrical power/latch circuit is
unknown.

The image examined has decrypted SHA-256
`6e9e65198dd12bcdf1286f7ab3986cc53230530d9283c9a73976c84fb23b237e`,
load address `0x08020000`, and reset entry `0x08024554` (Thumb vector value
`0x08024555`). Addresses below are MCU addresses; subtract `0x08020000` for decrypted
file offsets. C line numbers refer to the current
[`decompiled.c`](../analysis/generated/main/decompiled.c) export and can move after
another analysis pass. Function addresses are the stable reference.

## Startup that is present in the update

| Evidence | Location | Consequence |
|---|---|---|
| Reset initializes clocks/FPU/vector location, copies `.data`, clears `.bss`, runs constructors, calls main | `0x08024554`, C 7749–7772; system setup `0x08023bd0`, C 7043 | No head-presence or PH5 wait is visible in this entry path. |
| Main initializes GPIO/peripherals, raises PH9, waits, initializes the AXP223 rails, waits, then initializes radio parameters and LAN | `0x0802239c`, C 2282–2365 | Application startup proceeds through local hardware initialization before processing head settings. |
| Settings loader reads backup SRAM/EEPROM but is invoked with its force-reset argument `1` | `0x08022544`, `0x0803c08c`, C 2322 and 28327–28461 | Saved main-unit settings do not simply become the active boot configuration. |
| Main explicitly assigns IP `192.168.3.199`, gateway `192.168.3.1`, mask `255.255.255.0`, port `50001`, and network mode `0` | `0x08022556`–`0x080225aa`, C 2325–2348 | The no-head startup default is the HDSDR path. Mode `1` selects wfview. |
| Main starts the selected service and later services LAN, controller packets and radio processing repeatedly | C 2350–2365 and 2597–2652 | No main-loop condition requires a head to have connected first. This does not prove every RF/audio function works without it. |
| A valid head settings packet replaces IP, gateway, mask, port, mode and credentials | `controller_link_service_inferred`, `0x08041ef4`, C 33289–33341 | A connected head remains an authority for network settings. |

The application also provides explicit receive defaults. `0x0803e2f4` enters the
RX path at `0x0803d03c` and initializes radio/audio processing. Later, main selects
VFO A and assigns **14.270 MHz, USB** before applying the frequency and mode to the
radio (`0x08022918`–`0x08022942`, C 2563–2575). The frequency literal is `0x00d9be30`;
mode `2` is identified by the mode-name pointer table at initialized RAM
`0x240007d0`, whose index 2 points to the `USB` string at `0x0807d8b0`.
This is a configured receive path, not merely a listening network interface. It
does not establish actual reception, audio gain, calibration validity or successful
hardware initialization on a particular radio.

The controller-offline flag at `0x24004839` is initially `1` in `.data` (source
offset `0x690a5`); the packet countdown at `0x2401770c` starts at zero in `.bss`.
A valid packet clears the flag and reloads the countdown. Expiry clears the built-in
PTT, serial key and tune-request flags, marks the head offline, logs the event and
returns (C 33701–33713). This branch does not request shutdown, restart LAN or halt
the main loop. The recovered direct references to the offline flag contain no
startup gate. Unrecognized indirect accesses remain a limitation of static analysis.

## Power input and shutdown

GPIO helpers at `0x0802afbc` and `0x0802afc8` read `IDR` and write `BSRR` respectively.
`0x58021c00` is GPIOH according to [ST's STM32H723 register
definitions](https://raw.githubusercontent.com/STMicroelectronics/cmsis-device-h7/master/Include/stm32h723xx.h).
The GPIO initializer at `0x08021470` configures PH5 as an input with pull-up
(C 1473–1477).

The periodic routine at `0x08037c10` reads PH5, arms after first seeing a high level,
then sets shutdown flag `0x24004fed` after more than 100 consecutive low samples.
A high sample resets the press counter. The actual sample rate was not independently
established here. Its caller is TIM6's interrupt handler `0x080239e0`. This is strong
evidence for an active-low power-button input, but does not identify a CTRL-connector
pin or prove the physical connection to the head. A floating input subject only to
the configured pull-up would not request shutdown.

The main loop responds to that flag by:

1. Calling `0x08049948`, which sets bit 2 of the outgoing state word at
   `0x24017f20`.
2. Delaying 100 ms, then calling the shutdown routine at `0x08021edc`.
3. Disabling several GPIO-controlled outputs and setting DAC/control values to zero;
   optionally saving calibration and ATU data to EEPROM; muting/clearing audio state;
   and reducing the AXP223 enabled rails.
4. Disabling interrupts, waiting for PH5 to return high, then writing `0x05fa0004`
   to `SCB_AIRCR` to request system reset (`0x08021fc2`–`0x08021fd4`).

Packet type `03` carries the outgoing state word to the head. Its transmitter is
serviced by the TIM7 interrupt chain (`0x08023a48` → `0x08037a94` → `0x0804995c`),
so the notification can be sent during the 100 ms delay. The head's corresponding
handler sets its shutdown flag and PCA9557 output bit 5; its shutdown path saves
`config.ini` and later clears that output bit. This is a software correlation,
not evidence that PCA9557 bit 5 is wired to main-unit PH5. The main shutdown path
does not visibly wait for a head acknowledgement.

The AXP223 helper at `0x0804a854` writes register/value pairs `10:02`, `12:00`,
`13:01` at I2C address `0x68` in HAL's shifted-address convention. Initialization at
`0x0804a8e8` uses these values first, sets voltages, then writes `10:6e`, `12:08`.
The [Linux AXP22x register definitions](https://raw.githubusercontent.com/torvalds/linux/master/include/linux/mfd/axp20x.h)
and [regulator driver](https://raw.githubusercontent.com/torvalds/linux/master/drivers/regulator/axp20x-regulator.c)
identify `0x10` bit 1 as DCDC1's enable. The shutdown writes therefore preserve
DCDC1 while disabling the other normally enabled outputs controlled here. They do
not request global PMIC power-off. Which radio circuits each rail supplies is
unknown; intended execution after these writes does not establish actual board
power behavior.

There is no explicit persistent boot-mode marker or RTC/backup-SRAM write in the
observed shutdown path. Its optional EEPROM saves cover calibration at `0x800`
and ATU records at `0x1800`. Its ordinary RAM flags will be cleared by the next
application reset handler. GPIO writes might affect an external latch, but the
schematic is needed to interpret them.

## What the missing bootloader prevents us from concluding

The separate routine `0x0802200c` explicitly logs a jump to the bootloader, sets
`VTOR = 0x08000000`, loads the stack from `0x08000000` and calls the vector at
`0x08000004` (C 2001–2115). The supplied main update begins at `0x08020000`, so this
bootloader's contents are absent.

The application shutdown requests reset after waiting for button release. It does
not implement a visible low-power wait for the next press. The omitted bootloader,
MCU boot configuration and external power circuitry could determine what happens
next. We have not established that the bootloader waits for PH5, that the MCU is
running before the head's button is pressed, or that DC alone starts LAN. There is
also no application-side PH5 startup wait that can be removed to settle this.

## A narrow application patch candidate

If hardware tests establish that the main application can start without the head,
changing the default network mode to wfview is a small, identifiable experiment.
At `0x08022588` the instruction `strb.w r2,[r5,#0x182]` writes mode zero to
`0x24013d8e`. At that point `r2 = 0`, while `r0 = 0x801` from `0x0802256a` remains
unchanged, so using `r0` as the store source would write the byte `1`.

For this exact decrypted image, the original instruction is `85 f8 82 21`; the
candidate is `85 f8 82 01` (one changed byte at file offset `0x258b`). This identifies
a candidate, not a tested or complete headless firmware. No binary has been changed.
It leaves the other defaults intact, does not implement wake-on-LAN, and can still
be overridden by a later head packet. Existing HDSDR protocol capabilities should
be tested before deciding a mode patch is necessary.

The mode change is insufficient for a usable headless transmit setup. Separate
network analysis found that the wfview close callback does not clear the shared
CI-V PTT flag, while the transmit-state logic continues to use it; losing the
network audio source can fall back to codec input. Network disconnect/heartbeat
handling must release network-requested PTT before headless transmission is
considered. See [the IP protocol analysis](ip-protocol-coverage.md) for that path.

Before building a flashable experiment, establish cold-start behavior, verify the
selected network service with receive-only traffic, understand update integrity
checks and recovery, and retain the original firmware. A boot-stage power gate,
if present, would need separate analysis of a bootloader dump or board circuitry.
Changing this application byte would not bypass such a gate. Packaging, integrity
checks and update acceptance for a modified image have not been validated; an AES
decrypt/encrypt round trip alone does not demonstrate that the updater will accept it.

## Receive-only checks on the radio

1. With the head attached, record the firmware version and network configuration;
   establish that the legacy HDSDR receive path works. The discovery probe below
   tests this mode, not wfview. Capture network traffic so later failures can be
   distinguished from a PC/network setup issue.
2. Shut down using the head's power button while leaving DC connected. Record
   current consumption and whether the application still answers discovery. This
   measures the powered-but-off condition separately from cold DC startup.
3. Remove DC before disconnecting the head. Reapply DC without it
   and record supply current, Ethernet link and packets. Link alone proves only the
   PHY is active; a protocol response or receive samples are stronger evidence that
   the application is running.
4. For the unmodified no-head default, use an isolated `192.168.3.0/24` network and
   check `192.168.3.199`. The initialized peer value is `192.168.3.244`, making that
   a useful PC address for the HDSDR test. HDSDR discovery can replace that peer
   address, so it is not a permanent PC-address requirement. Use the existing
   receive client or the discovery probe below; do not issue PTT/tune commands.
5. Compare cold starts with the head present and absent, keeping the network and
   client the same. If cold DC without the head produces no application response,
   record that result rather than assuming a mode setting is the only obstacle.
   Recovering the bootloader or tracing the power circuit is then the next useful
   investigation; the application does not identify safe connector pins to bridge.

The standard-library Python [discovery probe](../scripts/probe_radio.py) sends
only legacy discovery requests. It prints a validated discovery reply and any
received IQ packet, without changing tuning or requesting transmission:

```sh
python3 scripts/probe_radio.py --timeout 15
```

The default destination is `192.168.3.199:50002`; use `--host` for the normal
head-connected baseline if its configured address differs. The PC must already
have an address on the appropriate subnet. Discovery temporarily directs the
receive stream to this client; avoid running another HDSDR client concurrently.
A response establishes that this application service is running. No response is
inconclusive: startup delay, a different network mode, addressing, or a firewall
can also explain it. The probe was tested entirely offline with a simulated
socket and peer, not a radio; the test did not send actual network packets.

## Retrieving the missing boot region from hardware

The first target is main-unit internal flash `0x08000000`–`0x0801ffff`, a
128 KiB region preceding the application. This range includes the explicitly
referenced boot vector; it is not a measurement of the bootloader's actual length.

The preferred first attempt is an ST-LINK/SWD connection to the **main MCU**.
Identify its exact marking and SWDIO, SWCLK, ground, target-voltage reference and
NRST connections before attaching a probe. Board pad locations and I/O voltage
are not established by this firmware. The radio's 13.8 V input is not a debug-pin
supply. Perform inspection with transmission inactive; attaching a debugger can
halt or reset the processor even without writing flash.

After the wiring and target supply are verified, STM32CubeProgrammer can display
the option bytes without programming them:

```sh
STM32_Programmer_CLI -c port=SWD mode=UR freq=1000 -ob displ
```

`UR` means connect under reset and requires NRST. If read protection and regional
protections allow flash reads, an example read-only export is:

```sh
STM32_Programmer_CLI -c port=SWD mode=UR freq=1000 -u 0x08000000 0x20000 g7250_main_boot_region.bin
```

These are prospective commands, not commands executed against a radio. Dump twice
and compare hashes; also preserve the option-byte report and, where readable, a
full internal-flash backup using the capacity of the identified part. Check the
boot vectors and compare the application portion against the known update.
See [ST's command reference](https://dev.st.com/stm32cube-docs/prog/2.23.0/en/docs/markup/CubeProg_Command_Lines.html).

**Do not use Read Unprotect, `-rdu`, mass erase or change RDP to make a dump work.**
On this STM32 family, RDP level 1 blocks external flash reads; returning it to
level 0 causes a flash mass erase. Level 2 permanently disables ordinary debug
access. Other region protections can impose additional restrictions.
[ST protection documentation](https://www.st.com/content/st_com/en/technical-documents/an5156-introduction-to-security-for-stm32-mcus-stmicroelectronics_asset/chunk-006-topic-an5156-sec-feat-read-out-protection-rdp-.html)

If external readout is protected, a possible research route is an application
patch that reads the boot region and exports it over LAN or UART. At RDP level 1,
code running normally from user flash can generally read user flash; PCROP,
secure-region configuration, updater acceptance and recovery must be checked
before treating this as feasible. This is an unimplemented alternative, not an
available dump feature.

ST's separate factory ROM loader supports UART/USB and other interfaces on the
H72x/H73x family, subject to boot configuration, pin access and protection. It is
distinct from Xiegu's flash bootloader and does not bypass read protection.
[ST AN2606](https://www.st.com/resource/en/application_note/an2606-stm32microcontroller-system-memory-boot-mode-stmicroelectronics.pdf)

The inspected application has no identified arbitrary flash-export command over
LAN or the head link. It does contain a 115200-baud USART1 diagnostic terminal
(PB6/PB7 AF7, initialization `0x08024108` / `0x08024218`), but its recovered menu
at `0x08041a94` exposes five calibration controls, not memory-address reads. The
physical UART connection is unknown. The missing Xiegu bootloader might have its
own service commands; this application analysis cannot establish them.

Read-protection and bootloader-update strings remain in the image, but no live
option-byte programming path or embedded replacement bootloader was recovered.
Their presence does not establish the radio's installed protection settings.
