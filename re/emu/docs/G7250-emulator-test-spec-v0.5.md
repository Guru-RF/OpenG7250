# G7250-emulator en geautomatiseerde testinfrastructuur — studie en specificatie

| | |
| --- | --- |
| Versie | v0.5 (concept, bureaustudie) |
| Datum | 2026-11-18 |
| Opdrachtgever | ON8ST |
| Primaire bron | repo `g7250-base` (branch `re/round5`), clean-room RE-documentatie van stock firmware V1.0.1 |
| Status | Er is geen firmware of emulator uitgevoerd. Er is geen firmware-image, sleutel of sleutelmateriaal gelezen of gezocht. |
| Opslag | Dit is de eerste versie in de repo `g7250-emu`. De concepten v0.1–v0.4 stonden in een tijdelijke map en bestaan niet meer; hun inhoud is hier volledig opgenomen. |

## Versiegeschiedenis

| Versie | Belangrijkste wijzigingen |
| --- | --- |
| v0.1 | Eerste studie: platformkeuze, machinedefinities, acceptatiecriteria, testlagen, brick-gates, HIL, clean-room, roadmap |
| v0.2 | Geen interoperabiliteit tussen de nieuwe firmware en stock; de bootloader- en updatekwestie verhuist naar het firmwareproject (§15); boot-toestandsmodellering; een clean-room hardware-interfacespecificatie (HIS) |
| v0.3 | De versies van de eigen Main en Control hoeven niet gelijk te zijn (versie-onderhandeling, gracieuze degradatie); eigen Main headless (EH) is de primaire doelconfiguratie; eigen Control is een latere, optionele track; ES (eigen Main + stock Control aangesloten) is alleen een robuustheids- en veiligheidstest met lage prioriteit; R0 (inschakelen zonder paneel) als topprioriteit |
| v0.4 | §3.8 uitgebreid: de hypothesen H1/H2 voor de voeding, tier-0-observaties, eisen voor always-on, slaap en wake, CH394 Wake-on-LAN, een PowerModel in de emulator |
| **v0.5** | **(1) De emulator ontsleutelt niets.** Er is geen decryptie, geen sleutelconfiguratie en geen Keychain- of sleutelbestandsafhandeling meer. De gebruiker levert reeds ontsleutelde applicatie-images aan in een lokale map buiten elke repo; de emulator leest die map via een configuratie-instelling en controleert elk image tegen een manifest met alleen hashes en versies. Het officiële vendorbestand wordt alleen bewaard en gehasht als herkomst (§4, §7, §12, §13). **(2) Scherpere tier-0-koudestartobservaties:** de geforceerde netwerkdefaults van stock Main (192.168.3.199), een ping als bewijs dat de app draait, en vaste procedureregels (dummy load, geen client die PTT kan zetten) (§3.8.3, §11.4) |

---

## 0. Leeswijzer

### 0.1 Betrouwbaarheidslabels

Elke bewering over de G7250 draagt een label en, waar het om een feit
uit de RE-documentatie gaat, het pad van het brondocument.

| Label | Betekenis in dit document |
| --- | --- |
| **VERIFIED** | Staat als VERIFIED in de `g7250-base`-documentatie. Dat betekent: geverifieerd **in de firmware-analyse**, niet gemeten op hardware. |
| **HIGH** | De docs geven HIGH CONFIDENCE, of het is een sterke afleiding van deze studie uit VERIFIED-feiten of uit publieke documentatie (Renode, ST, WIZnet, WCH, OpenHPSDR, TCI). |
| **HYPOTHESIS** | Onbewezen. Dit omvat ook alles wat de docs als MEDIUM of HYPOTHESIS labelen; dat staat er dan bij als "(docs: MEDIUM)". Publieke upstream-meldingen die wij niet zelf geverifieerd hebben, staan er als "HYPOTHESIS/MEDIUM (upstream-melding)". |

Uitspraken over eigen ontwerpkeuzes van deze specificatie ("de emulator
moet …") zijn normatief en dragen geen label. Uitspraken over externe
tools (Renode, QEMU) zijn HIGH als ze uit publieke documentatie komen,
met de kanttekening dat ze in mijlpaal M0 op de gekozen versie bevestigd
moeten worden.

### 0.2 Normatieve woorden

**MOET** is een harde eis, **MOET NIET** een verbod, **ZOU MOETEN** een
sterke aanbeveling, **MAG** een optie.

### 0.3 Afkortingen

- **Main**: de Main Unit (RF/DSP, FPGA, CH394, codec), STM32H72x/H73x.
- **Control**: de Control Unit (frontpaneel, display, GUI, CI-V), STM32H743. Ook "paneel" of "head".
- **Link**: de UART tussen Main en Control (USART2 aan beide kanten). Stock gebruikt er SLIP/CRC-16 over; de NF gebruikt een eigen protocol, de **NF-link**.
- **Stock**: de fabrieksfirmware van Xiegu.
- **NF**: de nieuwe, clean-room ontwikkelde firmware (NF-Main, en later optioneel NF-Control).
- **HIS**: de clean-room hardware-interfacespecificatie (§12.2).
- **Plant**: het gedragsmodel van de analoge en RF-hardware rond de MCU's (PA, detectoren, NTC, relais, antenne/belasting).
- **HIL**: hardware-in-the-loop met de echte G7250 op de testbank van de eigenaar.
- **VT**: virtuele tijd van de emulator.
- **Configs**: SS (stock+stock), EH (NF-Main headless), ES (NF-Main + stock Control aangesloten), EE (NF-Main + NF-Control); zie §3.7.

### 0.4 Samenvatting

1. **Platform: Renode.** De emulatie bestaat uit twee gekoppelde
   machines (Main en Control) in één emulatie met gedeelde virtuele tijd,
   met peripheral-modellen in C# en een Python-harnas. Renode heeft van
   alle opties de beste ondersteuning voor multi-machine, determinisme,
   GDB, logging van niet-gemodelleerde registers en CI. QEMU mist H7 en
   multi-machine-synchronisatie; een eigen emulator kost te veel.
2. **Baseline eerst.** Fase 1 levert een referentieplatform waarop de
   *ongewijzigde* stock V1.0.1 van beide units "perfect" draait. De
   §6-acceptatiecriteria maken "perfect" meetbaar.
3. **Geen decryptie in de emulator.** De gebruiker levert zelf
   ontsleutelde applicatie-images in een lokale map buiten elke repo.
   De emulator controleert ze tegen een manifest met alleen hashes en
   weigert elke mismatch (§4).
4. **Kritiek pad:** de stock+stock-baseline (SS), dan NF-Main headless
   (EH, de primaire doelconfig, bediend via P1 en TCI vanuit AetherSDR
   of andere SDR-software), dan HIL met de NF-Main. De opstelling ES
   (NF-Main met een aangesloten stock Control) is alleen een
   robuustheids- en veiligheidstest met lage prioriteit. Een eigen
   Control (EE) is een latere, optionele track (§3.7). Het grootste
   risico is of de Main zonder Control kan inschakelen (R0, §3.8).
5. **Grootste technische risico's:** het FPGA-model (bit-banged bus op
   48 kHz, onbekende sample rates), de emulatiesnelheid (550 MHz Main
   met zware float-DSP), en de juiste boot-toestand zonder bootloader
   (§4.3).
6. **Brick-preventie aan emulatorzijde:** de NF raakt sector 0
   (bootloader) en de option bytes nooit aan; de persistente staat
   blijft bruikbaar voor stock (terugrol-compatibiliteit wordt in de
   emulator getest); TX-veiligheidsgates. De echte flashprocedure en het
   updatepad zijn een afhankelijkheid van het firmwareproject (§15).
7. **Clean-room:** de emulator en de golden traces van stock horen bij
   de RE-kant. De NF wordt alleen gebouwd uit de HIS, de publieke
   standaarden (P1, TCI, CI-V), de publieke vendordocumentatie en
   black-box-testresultaten.

---

## 1. Doelen, scope en principes

### 1.1 Doelen

| # | Doel | Meetbaar via |
| --- | --- | --- |
| D1 | Een gekoppelde emulatie van Main en Control waarop de ongewijzigde stock firmware perfect draait | §6-acceptatiecriteria |
| D2 | Die emulatie is het **referentieplatform** (baseline) en wordt per vendor-release geversioneerd | §7 versiematrix |
| D3 | Een volledig geautomatiseerd en zelfstandig testframework voor de NF | §8 |
| D4 | Kwaliteit van de NF berekenen en rapporteren | §9 |
| D5 | De kans op een gebrickte echte radio minimaliseren | §10 |
| D6 | HIL met de echte G7250 op de bestaande testbank, in een latere fase | §11 |

### 1.2 Scope

**Binnen scope:**
- emulatie van beide MCU's met alle peripherals die de firmware
  gebruikt, plus de externe chips en een plant-model;
- de koppeling tussen beide units via de link en de CTRL-kabel;
- de externe interfaces: CI-V (seriële lijn), Icom-LAN (de
  wfview-compatibele netwerkemulatie van stock), HDSDR-modus, en voor
  de NF ook OpenHPSDR Protocol 1 en TCI;
- het **inlezen en controleren van door de gebruiker aangeleverde,
  reeds ontsleutelde applicatie-images** en de
  boot-toestandsmodellering (directe boot van het applicatie-image);
- de systeemconfiguraties stock+stock en NF-Main headless (primair),
  later en optioneel eigen+eigen, plus de testopstelling ES (§3.7);
- testlagen, fault-injectie, kwaliteitsscore, release-gates en de
  HIL-integratie.

**Buiten scope:**
- **elke vorm van decryptie** van vendorbestanden, en elke sleutel-
  of sleutelmateriaalafhandeling. De emulator parseert of ontsleutelt
  het vendor-updatebestand nooit;
- wfview als testclient: stock wordt aangestuurd door eigen
  testscripts die het Icom-LAN-protocol en CI-V spreken;
- elke manier om band- of vermogenslimieten te omzeilen;
- **de bootloader- en updatekwestie:** of de vendor-bootloader een
  eigen image aanvaardt, hoe een NF-image op de radio komt, het
  verpakken in het vendor-updateformaat, en het updatepad van de NF.
  Dat is werk voor het firmwareproject (§15);
- interoperabiliteit tussen NF en stock: gemengde configuraties worden
  niet ondersteund en niet als compatibiliteit getest (ES is alleen een
  veiligheidstest);
- het openen van de radio, metingen aan de hardware en SWD-toegang: de
  eigenaar doet alleen tier-0-tests (`docs/hardware_test_plan.md`);
- cycle-accurate timing. De emulator is functioneel getimed (§1.4).

### 1.3 Het baseline-idee

De stock firmware is het **orakel voor het gedrag van de hardware**. Als
stock in de emulator alles doet wat de docs beschrijven, zonder faults
en zonder hangende pollinglussen, dan zijn de peripheral-modellen goed
genoeg. Op die gevalideerde modellen draait daarna de NF.

```
 ontsleutelde images (lokale map, door de gebruiker) --> manifest-check (hashes) --> Renode: Main + Control
                                                                                      |
       g7250-base docs/CSV --> modellen + testdata -----------------------------------+
                                                                                      v
                                                     baseline-suite (par. 6) --> golden traces/screenshots
                                                                                      |
 NF-build --> dezelfde modellen --> conformance-suite (par. 8) --> kwaliteitsscore (par. 9) --> gates (par. 10)
```

Drie gevolgen:
- Een model mag pas "af" heten als stock er perfect op draait.
- Elke nieuwe vendor-release is een **regressietest voor de emulator**:
  faalt stock, dan ligt het eerst aan een model (§7).
- De NF wordt getest op precies dezelfde hardwaremodellen. Een verschil
  tussen NF en stock is daardoor een eigenschap van de firmware, niet
  van de emulator. Alleen de inhoud op de LinkCable verschilt in EE (het
  eigen NF-protocol); het fysieke model (USART2, byte-timing, faults)
  blijft hetzelfde.

### 1.4 Principes

1. **Reproduceerbaarheid.** Een testrun wordt volledig bepaald door
   een *run-manifest*:
   - de hashes van de images, het emulatorbuild en de modelversies;
   - de plant-parameters;
   - de seed;
   - de invoerstroom (recording).

   Hetzelfde manifest geeft hetzelfde resultaat, bit voor bit.
2. **Determinisme.**
   - Alleen virtuele tijd. Er is geen wandklok in het pad van de
     firmware: de RTC start op een vast epoch.
   - Seriële, deterministische uitvoering van beide machines met een
     vaste synchronisatie-quantum.
   - Alle randomness via één seed.
   - Host-I/O alleen via een getimestampte invoerwachtrij (§8.6).
3. **Twee rijstroken.**
   - De **deterministische rijstrook** draait CI, golden traces en
     gates. Alle testclients draaien daar in virtuele tijd.
   - De **live rijstrook** heeft echte host-netwerktoegang (TAP of
     UDP) en is voor interactief werk. Ze is niet deterministisch, maar
     elke sessie wordt opgenomen, zodat ze in de deterministische
     rijstrook afspeelbaar is.
4. **Functionele timing, geen cycli.** De virtuele tijd komt uit het
   aantal instructies, via een geconfigureerde MIPS-waarde per core.
   Caches en dual-issue worden niet gemodelleerd. Timingmarges uit de
   emulator zijn daarom **indicatief**; de beslissende meting gebeurt
   in HIL (§11).
5. **Strikte modus.** Elke toegang tot een adres dat niet gemodelleerd
   of uitdrukkelijk getagd is, wordt gelogd. In de strikte modus doet
   ze de test falen (§5).
6. **Datagedreven.** De modellen en testlijsten lezen de CSV's van
   `g7250-base`. Zo verandert een correctie in de RE-docs de tests
   zonder codewijziging.
7. **Geen firmware in git.** Images, dumps en stock-afgeleide
   artefacten (screenshots, traces) staan buiten de publieke repo
   (§12). De emulator kent geen sleutels en bevat geen
   ontsleutelingscode.

---

## 2. Platformkeuze

### 2.1 Eisen aan het platform

| # | Eis | Waarom (G7250-specifiek) |
| --- | --- | --- |
| P1 | Cortex-M7 met FPv5 double precision, MPU, NVIC met meer dan 130 IRQ's, DWT-cyclusteller | Beide images zijn gelinkt voor de multilib `thumb/v7e-m+dp/hard` (VERIFIED, `docs/libraries.md`). Main gebruikt IRQ 129/130 (BDMA) (VERIFIED, `docs/dma.md`). De constructor zet DWT aan voor de NR-statistiek (VERIFIED, `main_unit/docs/startup.md`). GT911-time-outs lopen op de cyclusteller (VERIFIED, `control_unit/docs/peripherals.md`) |
| P2 | Twee machines met **gedeelde, deterministische virtuele tijd** | De link draait op 460 800 Bd, met een 20 ms-ritme van `0x01` en frame-skips bij een bezet TX-lock (VERIFIED, `docs/protocol.md`) |
| P3 | Peripheral-modellen in een hogere taal, snel genoeg voor ~10⁷ MMIO/s | De FPGA-bus is bit-banged op GPIOE, met DRDY op 48 kHz (docs: MEDIUM) |
| P4 | GDB per machine | Debuggen van modelgaten en van de NF |
| P5 | Logging van niet-gemodelleerde toegang en tagging van registers | Gap-analyse (§5) |
| P6 | Snapshots, record en replay | Golden runs, snel forken na het booten |
| P7 | Headless draaien en CI-integratie | Nightly suites |
| P8 | Netwerk naar de host (TAP of UDP) | Live rijstrook voor de CH394 |
| P9 | Framebuffer-capture | GUI-baseline |
| P10 | Open licentie | Eigen modellen vrij te publiceren |

### 2.2 Vergelijking

| Criterium | Renode | QEMU (mainline / xPack) | Eigen aanpak (Unicorn-/ISS-gebaseerd, of HAL-rehosting à la HALucinator) |
| --- | --- | --- | --- |
| STM32H7-ondersteuning | Er bestaat een STM32H743-platformbeschrijving; de dekking is onvolledig (HIGH, te bevestigen in M0). Geen H72x: zelf af te leiden | Geen H7-board in mainline; de STM32-boards zijn F1/F2/F4/L4 (HIGH). xPack heeft enkele F4-boards | Alles zelf te bouwen |
| Cortex-M7 met dp-FPU | Ondersteund door de Cortex-M-CPU van Renode (HIGH; dp-instructies te valideren in M0) | Aanwezig (HIGH) | Unicorn: ja, maar zonder systeemmodel |
| Multi-machine in één tijdbasis | Ingebouwd: meerdere machines, globale quantum, UART-hub, netwerkswitch (HIGH) | Twee processen met chardev-sockets; geen gedeelde virtuele tijd. `icount` per instantie, synchronisatie zelf te bouwen (HIGH) | Zelf te bouwen |
| Peripheral-modellen | C# (runtime gecompileerd), Python-peripherals, `.repl`-platformbeschrijvingen (HIGH) | C in de QEMU-tree; per wijziging hercompileren (HIGH) | Python of Rust; snel te prototypen, maar alles is eigen werk |
| GDB | Per machine een GDB-server (HIGH) | Uitstekend (HIGH) | Unicorn: geen stub (Qiling wel) |
| Logging van niet-gemodelleerde registers | Waarschuwingen bij niet-afgehandelde toegang, `Tag`, per-peripheral access-logging (HIGH) | Met tracepoints, maar omslachtig | Zelf te bouwen |
| Snapshot, record en replay | Opslaan en laden van de emulatiestaat; opname van externe gebeurtenissen (HIGH, details te bevestigen) | Record/replay met `icount`, per instantie; niet over twee processen (HIGH) | Zelf te bouwen |
| Testintegratie en CI | Robot Framework-integratie, headless, containers (HIGH) | Goed, maar test-API zelf te bouwen | Zelf te bouwen |
| Netwerk | Switch, TAP-brug (HIGH) | Uitstekend (HIGH) | Zelf te bouwen |
| Framebuffer | Video-/framebuffer-peripherals en een framebuffer-tester (HIGH; LTDC- en DMA2D-modellen bestaan voor andere STM32's, H7-compatibiliteit te controleren) | Via een eigen display-device | Zelf te bouwen |
| Snelheid | Middelmatig: dynamische vertaling, MMIO naar C# kost per toegang (HIGH) | Snelst (TCG) (HIGH) | Unicorn snel; Python-hooks traag |
| Trouw aan "ongewijzigde firmware" | Registerniveau: ja | Registerniveau: ja | HAL-rehosting vervangt HAL-functies en **voert dus niet de echte HAL uit**. Het faalt op het baseline-idee en moet per vendor-release opnieuw functieadressen vinden |
| Licentie | MIT (HIGH) | GPLv2 (HIGH) | eigen |
| Inspanning tot "stock boot" | middel | hoog (eerst H7-SoC en 20+ peripherals in C) | hoog tot zeer hoog |

### 2.3 Aanbeveling

**Renode is het primaire platform** (aanbeveling, onderbouwd met HIGH).
De redenen, in volgorde van gewicht:

1. **Multi-machine met deterministische gedeelde tijd zit ingebouwd.**
   Dat is de kern van D1: twee H7's plus de link, plus de CTRL-kabel.
   In QEMU of een eigen emulator is dat precies het moeilijkste stuk.
2. **De gap-workflow zit ingebouwd:** logging van niet-gemodelleerde
   toegang, `Tag`, GDB, snapshots en execution tracing (§5).
3. **Modellen ontwikkelen gaat snel in C#.** Prototypes kunnen in
   Python, zonder het platform opnieuw te bouwen.
4. **CI en Robot zijn standaard**, de licentie is MIT, en er draait een
   actieve community rond STM32.

**Aanvullend (MAG):**
- Een **Unicorn-gebaseerd fuzz-harnas** voor de *NF-parsers* (CI-V, P1,
  TCI, de NF-link), als host-gecompileerde of geïsoleerde functies. Het
  is sneller dan volledige emulatie, maar het vervangt de emulator
  niet.
- **QEMU** valt af als hoofdplatform. Het blijft een optie voor puur
  snelheidskritische NF-unittests op een generieke Cortex-M7
  (bijvoorbeeld de MPS2-AN500-machine, HIGH), zonder G7250-peripherals.

**Beslispunt M0 (spike van 1–2 weken).** Renode blijft de keuze tenzij
de spike aantoont dat:
- dp-FPU-instructies of de MPU van de M7 fout gaan; of
- de snelheid onder ~0,05× realtime blijft voor de boot van Main zonder
  FPGA-stream.

In dat geval wordt Renode met een eigen CPU-backend heroverwogen, niet
QEMU.

### 2.4 Hoe de Renode-eigenschappen worden ingezet

| Eigenschap | Gebruik in G7250-emu |
| --- | --- |
| Twee machines in één `.resc` | `main` (H725-afgeleid) en `control` (H743); voor EH alleen `main` |
| Globale quantum en seriële uitvoering | Deterministische interleaving. Start met een quantum van 10 µs VT; dat is kleiner dan een byte-tijd op de link (21,7 µs bij 460 800 Bd, 8N1) |
| UART-koppeling | `main.usart2` ↔ `control.usart2` via een eigen **LinkCable**-model, met byte-timing, foutinjectie en een tap naar de decoder |
| C#-peripherals | Alle H7-blokken die ontbreken of afwijken, alle externe chips en het plant-model |
| Python-peripherals | Snelle prototypes; daarna porten naar C# als ze in het hete pad zitten |
| GDB | Poort 3333 (Main) en 3334 (Control); symbolen voor stock uit `*/analysis/memory/function_ranges.csv` (alleen RE-kant) |
| Snapshot | Een "geboot"-snapshot per vendor-release, waaruit testcases forken. Dat scheelt de 3–6 s VT boot per test (§6.2) |
| Execution tracing | Coverage van de NF (met DWARF) en van stock (functiebereiken uit de CSV) |
| Robot of pytest | Robot voor het Renode-native niveau, pytest als hoofdharnas via de Renode-API of de monitor-socket (§8) |

---

## 3. Machinedefinities voor Main en Control

### 3.1 MCU's en geheugenkaarten

| | Main | Control |
| --- | --- | --- |
| Familie | STM32H7, Cortex-M7 (VERIFIED, `docs/mcu_identification.md`) | idem |
| Onderdeel | STM32H725xG of H735xG, 1 MiB flash (docs: MEDIUM → HYPOTHESIS). Crypto wordt niet gebruikt, dus het verschil is irrelevant | STM32H743xI rev V, 2 MiB flash (HIGH, `docs/mcu_identification.md`) |
| DBGMCU IDCODE | DEV_ID 0x483 verwacht (HYPOTHESIS, `docs/hardware_test_plan.md` T3.1) | DEV_ID 0x450, rev V. **MOET** correct zijn: SystemInit vertakt op de revisie (rev-Y-errata) en de GUI-bibliotheek controleert DEV_ID 0x450 (VERIFIED, `control_unit/docs/startup.md`, `docs/mcu_identification.md`) |
| Kloks | HSE 25 MHz, PLL1 550/275/275, HCLK 275, PCLK 137,5, PLL2 100 MHz (ADC); I2S_CKIN 12,288 MHz extern (VERIFIED, `main_unit/docs/flow.md`) | HSE 25 MHz, PLL1 480/96/480, HCLK 240, PCLK 120, PLL2R 240 (FMC), PLL3R 40 (LTDC), LSE, HSI48 (VERIFIED, `control_unit/docs/flow.md`) |
| Voeding | SMPS 2,5 V plus LDO, VOS0 zonder overdrive (VERIFIED, `main_unit/docs/flow.md`) | LDO, VOS1 plus ODEN (VERIFIED, `control_unit/docs/flow.md`) |
| Applicatie in flash | `0x08020000`–`0x0808EA20` (VERIFIED, `main_unit/docs/memory_map.md`) | `0x08020000`–`0x080DEC10` (VERIFIED, `control_unit/docs/memory_map.md`) |
| Bootloadergebied | `0x08000000`–`0x0801FFFF`, **niet in het image** (HIGH) | idem (HIGH) |
| Reset-vectoren | MSP `0x24050000`, reset `0x08024554` (VERIFIED, `main_unit/docs/startup.md`) | MSP `0x24080000`, reset `0x080235AC` (VERIFIED, `control_unit/docs/startup.md`) |
| AXI SRAM | 320 KiB `0x24000000`–`0x24050000` (HIGH, `main_unit/docs/memory_map.md`) | 512 KiB `0x24000000`–`0x24080000` (VERIFIED) |
| D2 SRAM | 32 KiB `0x30000000`, MPU non-cacheable (VERIFIED) | 288 KiB, niet gebruikt; MPU-regio 512 KiB (VERIFIED, `control_unit/docs/memory_map.md`) |
| SRAM4 (D3) | 16 KiB `0x38000000`, non-cacheable (VERIFIED) | 64 KiB, non-cacheable (VERIFIED) |
| Backup SRAM | 4 KiB `0x38800000`, strongly ordered, alleen gelezen (VERIFIED, `main_unit/docs/memory_map.md`) | niet gebruikt |
| TCM | niet gebruikt (VERIFIED) | DTCM heeft een MPU-regio, geen inhoud (VERIFIED) |
| Extern geheugen | geen; MPU-wachtregio op FMC bank 1 `0x60000000` (VERIFIED) | SDRAM 32 MiB op `0xC0000000`: framebuffers op `0xC0000000` en `0xC012C000`, emWin-pool op `0xC0800000` (VERIFIED/HIGH, `control_unit/docs/peripherals.md`, `memory_map.md`) |
| Caches | I/D aan; MDMA-helpers doen eigen cache-onderhoud (VERIFIED) | I/D aan; geen cache-onderhoud; DMA-buffers in non-cacheable SRAM4 (HIGH) |
| RTOS | geen, superloop (VERIFIED) | geen, superloop (VERIFIED) |
| Fault-handlers | Default handler `0x080245A4` (lus). HardFault dumpt registers op USART1 en stopt (VERIFIED, `main_unit/docs/startup.md`) | Default handler `0x08023600` (lus). HardFault logt één regel en stopt (VERIFIED, `control_unit/docs/startup.md`) |

**Gevolgen voor de `.repl`-bestanden:**
- `g7250_main.repl` wordt afgeleid van een H7-basis. Het krijgt de
  H72x-geheugengroottes, de vectortabel met TIM23/24 en UART9/USART10
  (lengte), SMPS-registers in PWR, en `Tag`-regio's voor alle
  ongebruikte blokken.
- `g7250_control.repl` start van de H743-platformbeschrijving van
  Renode (als die in M0 voldoet), aangevuld met FMC, SDRAM, LTDC,
  DMA2D, SDMMC1, OTG_FS en de externe chips.
- Caches worden niet gemodelleerd. De cache-onderhoudsoperaties
  (ICIALLU, DCISW, DCCIMVAC …) **MOETEN** als no-op aanvaard worden.

### 3.2 Getrouwheidsniveaus

| Niveau | Definitie | Typisch gebruik |
| --- | --- | --- |
| **S — stub** | Het adresbereik bestaat. Schrijven wordt opgeslagen, lezen geeft de resetwaarde of de laatst geschreven waarde. Geen bijwerkingen. Elke toegang wordt geteld | Geïnitialiseerd maar ongebruikt (UART4, I2C2/I2C3 op Main) |
| **R — registerniveau** | Registers met de juiste resetwaarden, read-only/W1C-semantiek en statusvlaggen die HAL-pollinglussen laten slagen (ready, busy, done) | RCC, PWR, FLASH, RTC, CRC, OTG-stub |
| **B — gedragsniveau** | R, plus het functionele gedrag: data, timing in VT, IRQ's en DMA-verzoeken, en een externe interface (bestand, socket, testharnas) | UART, SPI, I2C-apparaten, DMA, timers, CH394, FPGA, LTDC |

"Perfect draaien" (§6) vereist voor elk peripheral het niveau dat in de
inventaris staat. Een stub mag nooit een pollinglus van de firmware
laten hangen: de hangdetector bewaakt dat (§5.3).

### 3.3 Peripheral-inventaris — Main

| Peripheral | Rol | Bron | Niveau | Wat de firmware nodig heeft om perfect te draaien |
| --- | --- | --- | --- | --- |
| Cortex-M7-core, NVIC, SysTick, SCB, MPU | CPU, prioriteitsgroepering 4, SysTick 1 kHz op prioriteit 15 | `docs/dma.md`, `main_unit/docs/flow.md` | B | dp-FPU, juiste preëmptie per prioriteit, MPU-regio's aanvaard (PRIVDEFENA), VTOR 0x08020000, cache-ops als no-op |
| DWT CYCCNT | CPU-loadmeter en NR-cyclusstatistiek | `main_unit/docs/startup.md` | B | Telt in VT-cycli (instructies × factor), zodat de load-meter zinvolle waarden geeft |
| RCC | PLL1/PLL2, HSE en LSI, kernel-klokmuxen | `main_unit/docs/flow.md`, `analysis/clocks/clock_config.csv` | R | HSERDY, PLLxRDY, LSIRDY, SWS volgt SW; de kernel-muxwaarden teruglezen. `HAL_RCCEx_GetPeriphCLKFreq` gebruikt de I2S_CKIN-constante, dus geen model nodig |
| PWR | SMPS/LDO, VOS0, backup-regulator | `main_unit/docs/flow.md`, `memory_map.md` | R | ACTVOSRDY en VOSRDY; **BRRDY na BREN**, anders volgt een wachttijd tot 1 s bij het laden van de instellingen; DBP |
| FLASH-controller | Wachttoestanden | `main_unit/docs/flow.md` | R | ACR-latency teruglezen. Geen unlock-sleutel in de app (VERIFIED). Een bewakingsmodel voor programmeren en wissen is nodig voor de NF en de brick-tests (§10) |
| Option bytes | RDP, BOOT_ADD, CPUFREQ_BOOST, IWDG_SW | `main_unit/docs/flow.md` | R (profiel) | Waarden onbekend (§5). Het profiel levert plausibele waarden; de app leest ze niet (HIGH) |
| SYSCFG, EXTI | PC13 (CH394 INT#, falling), PE10 (FPGA DRDY, rising), PH3/PH4 (CW, beide flanken), PH6 (PTT, beide flanken) | `main_unit/docs/peripherals.md` GPIO, `docs/dma.md` | B | EXTICR-mapping, flankdetectie, pending-W1C; IRQ 9/10/23/40 |
| GPIOA–H | Discrete lijnen: T/R (PF4, PF6, PC7, PH11), latches (PA10/11, PH10/12, PD13, PG2, PG5), CH394 CS/RST (PG15, PB5), codec-reset PB10, PH5 power-toets (pull-up), PH9, PH13, PH15, DAC-load PB12/PB14 | `main_unit/analysis/peripherals/gpio_map.csv` | B | Pin-niveaumodel met externe verbindingen naar de chipmodellen en het PowerModel (§3.8.6); elke flank gelogd in de trace (golden) |
| GPIOE als FPGA-bus | 8-bit data PE0–7 (richting via MODER), CMD PE8+PE9, STB PE9, DRDY PE10 | `main_unit/docs/peripherals.md` FPGA-bus | B (**gefuseerd**) | Zie het FPGA-model in §3.5.1; GPIOE en FPGA zijn uit snelheidsoverwegingen één C#-model |
| DMA1/DMA2 + DMAMUX1 | S0 I²S3 RX, S2 USART2 RX, S3 USART1 RX, S4 USART2 TX, S5 I²S3 TX, S7 ADC1; DMA2 S5 mem-to-mem (nooit gestart) | `docs/dma.md`, `analysis/peripherals/dma_map.csv` | B | Circulaire modus, **NDTR leesbaar** (de RX-handler leest de ring via NDTR), HT/TC-IRQ, request-routing via DMAMUX, breedte 8/16/32 |
| BDMA + DMAMUX2 | ch0 SPI6 RX, ch1 SPI6 TX | `docs/dma.md` | B | Mag alleen D3-geheugen raken; het model controleert dat buffers in SRAM4 staan (getrouwheidscheck); IRQ 129/130 |
| MDMA | ch0/1/2 kopiëren, ch4 vullen, softwaretrigger, gepold | `docs/dma.md` | B (eenvoudig) | Directe kopie bij start, CTCIF/BTIF gezet; geen IRQ |
| USART1 | Console en servicemenu, 115 200 8N1, RX via circulaire DMA, TX blokkerend | `main_unit/docs/peripherals.md` USART1 | B | PTY of socket naar het harnas. **Het harnas MOET NIET Enter sturen** buiten gerichte RE-tests: dat opent het servicemenu, dat de drive-DAC en de SWR-termen wijzigt (VERIFIED). De HardFault-dump wordt via directe registerpolling geschreven, dus TXE/TC moeten kloppen |
| USART2 | De link, 460 800 8N1, DMA TX/RX, IRQ38 | `docs/protocol.md` | B | Byte-timing in VT, ORE-vlag (de re-arm-logica leunt erop), IDLE niet nodig op Main; LinkCable-koppeling |
| UART4 | Geïnitialiseerd, ongebruikt | `docs/hardware_init.md` | S | Init slaagt |
| I2C1 | EEPROM 0x50, AIC3204 0x18, AXP223 0x34, VC6 0x68/0x6A; gepold, ~400 kHz | `main_unit/docs/peripherals.md` I2C, `analysis/peripherals/i2c_devices.csv` | B | H7-I2C v2-registers (TIMINGR, CR2 SADD/NBYTES/RELOAD/AUTOEND, ISR TXIS/RXNE/TC/STOPF/NACKF); **NACK als een adres afwezig is** (de VC6 valt terug van 0x68 naar 0x6A) |
| I2C2, I2C3 | Geïnitialiseerd, ongebruikt; I2C3-IRQ's aan maar met de default handler | `docs/dma.md` | S | Het model MOET NIET spontaan een I2C3-IRQ geven: dat zou in de default-lus vallen |
| SPI1 | TX-only master; vijf serieel-in-latches | `main_unit/docs/peripherals.md` SPI1, `docs/atu.md` | B | H7-SPI v2 (CSTART, TXP, EOT, TSIZE); bytes doorgeven aan de latchmodellen per CS/latchlijn |
| SPI2 | TX-only naar de 8-kanaals 10-bit DAC (BU2506FV-type) | `main_unit/docs/peripherals.md` SPI2, `analysis/peripherals/spi2_dac.csv` | B | 16-bit woorden decoderen (4-bit adres plus 10-bit waarde), latch op PB12, reset PB14 |
| SPI3 = I²S3 | Master full-duplex, Philips, 32 bit, 48 kHz, kernel I2S_CKIN | `main_unit/docs/peripherals.md` I²S3 | B | Frameklok in VT (48 kHz), DMA-verzoeken per woord, half/complete-IRQ via DMA; koppeling met het codecmodel |
| SPI6 | CH394, master mode 0, /8 van PCLK4 (~17,19 MHz), BDMA, IRQ86 | `main_unit/docs/peripherals.md` SPI6 | B | Byte-timing bij 17,19 Mbit/s (voor de doorvoerbudgetten), ontvangen in receive-only-modus voor registerreads |
| ADC1 | 7 ranks, continu, DMA1 S7 circulair, offset- en lineariteitskalibratie | `main_unit/docs/peripherals.md` ADC1 | B | ADCAL wist zich, ADRDY; conversiewaarden uit het plant-model; conversietijd in VT |
| DAC1 | OUT1 = RF-gain-spanning, OUT2 ongebruikt | idem | R + tap | Waarden gelogd (trace) |
| TIM5/6/7/17 | 20 kHz DSP-scheduler, 100 Hz housekeeping, 1 kHz service en SLIP-status, 20 kHz sample-service | `analysis/peripherals/timers.csv` | B | PSC/ARR-update-IRQ's in VT. Timerklok 275 MHz |
| TIM4 | PWM op PD12, nooit gestart | idem | S | Init slaagt |
| RTC | LSI, tijd gereset naar 2000-01-01 | `main_unit/docs/peripherals.md` RTC | R | INITF/RSF-handshake. De wake-up-IRQ MOET uit blijven: IRQ 3 leidt naar de dode bootloader-sprong (HIGH) |
| IWDG1 | Kick per superlooppassage, tijdens de CH394-wachttijd en bij shutdown; nooit geconfigureerd | `docs/architecture.md`, `analysis/peripherals/iwdg_kicks.csv` | B | Standaard **uit**. Profiel "hardware-gestart, time-out T": reset bij verloop (§4.3). De boot van Main duurt langer dan 2 s zonder kick (VERIFIED), dus T moet ruim zijn |
| CRC | Geïnitialiseerd, ongebruikt | `docs/hardware_init.md` | S | Init slaagt |
| Backup SRAM | Kopie van de instellingen (alleen lezen) | `main_unit/docs/memory_map.md` | B (geheugen) | Inhoud via het profiel (leeg of gevuld); de app forceert toch de defaults (VERIFIED) |
| FMC bank 1 `0x60000000` | MPU-wachtregio, niets erachter | `main_unit/docs/memory_map.md` | — (niet gemapt) | Toegang wordt gelogd als anomalie |
| USB OTG_HS | Niet gebruikt | `main_unit/docs/peripherals.md` USB | — | Elke toegang is een anomalie |

### 3.4 Peripheral-inventaris — Control

| Peripheral | Rol | Bron | Niveau | Wat de firmware nodig heeft |
| --- | --- | --- | --- | --- |
| Cortex-M7, NVIC, SysTick, MPU, DWT | SysTick op prioriteit 0 voedt ook de IWDG elke 256 ticks | `control_unit/docs/startup.md`, `docs/dma.md` | B | Zoals Main. **DWT CYCCNT MOET lopen**: de GT911-transfers gebruiken time-outs van 20 ms op de cyclusteller (VERIFIED) |
| DBGMCU | IDCODE | `control_unit/docs/startup.md`, `docs/mcu_identification.md` | R | DEV_ID 0x450, REV_ID rev V; anders loopt het errata-pad of faalt de GUI-controle |
| RCC, PWR, SYSCFG, FLASH | PLL1/2/3, HSE, LSE (high drive), HSI48; LDO, VOS1+ODEN; 4 WS | `control_unit/docs/flow.md` | R | Alle ready-vlaggen; LSERDY (anders hangt de RTC-init); de voorwaardelijke RCC-tweak op offset 0xD4 aanvaarden |
| GPIOA–I | Toetsmatrix (open-drain met pull-up), 8 GPIO-encoders, SD-detect PA15, paneelvoeding (PE6, PI3, PF9), GT911 INT/RST (PE2/PG14), codec-reset PH2, PCA9557-reset PG3, flash-CS PG13, CW-keying PE3/PE4, PI6, PG9/PG10 | `control_unit/docs/peripherals.md`, `analysis/peripherals/gpio_map.csv`, `inputs.csv` | B | Een pinmodel met **open-drain-semantiek en externe netwerken** (matrix, encoders); IDR moet het externe niveau weerspiegelen |
| EXTI2 | GT911 INT op PE2, rising | idem | B | IRQ8 |
| DMA1 + DMAMUX1 | S0 I²S2 RX, S1 I²S2 TX, S2 USART2 TX, S3 USART2 RX, S4 USART1 RX | `docs/dma.md` | B | Circulair; **receive-to-idle** op USART2 (IDLE-event plus NDTR) |
| DMA2D | Vullen, kopiëren, PFC RGB565, blend; gepold | `control_unit/docs/peripherals.md` display | B (native C#) | Correcte pixeloperaties. Prestatiekritisch: in C#, niet in Python |
| FMC + SDRAM | Bank 1, 32 MiB, commandovolgorde, refresh 918 | idem | R + geheugen | SDCMR-commando's aanvaard, status niet-busy; RAM 32 MiB |
| LTDC | 1024×600 RGB565, 40 MHz, één laag, dubbele buffering | idem, `analysis/peripherals/display_config.csv` | B | **VSYNC-status in VT (~46,9 Hz)**, want de bufferwissel wacht op VSYNC (VERIFIED). Laag-adres plus reload (SRCR), IRQ88; framebuffer-capture (§3.5.12) |
| I2C1 | GT911 (0x14, terugval 0x5D), gepold | `control_unit/docs/peripherals.md` GT911 | B | Adreskeuze volgens het INT-niveau bij de reset (§3.5.11) |
| I2C2 | AIC3204 0x18, PCA9557 0x19, ~100 kHz | idem | B | Zoals bij Main |
| SPI1 | W25Qxx-NOR, 48 MHz, gepold, CS PG13 | `control_unit/docs/peripherals.md` SPI1, `analysis/peripherals/spi1_flash.csv` | B | JEDEC-ID, lezen, pagina programmeren, 4 KiB sector-erase, WIP-status; met een image als achtergrond |
| SPI2 = I²S2 | **Slave** full-duplex, 32 bit; klok van de codec | `control_unit/docs/peripherals.md` codec | B | Frameklok van het codecmodel (~48,005 kHz door de PLL-quirk, docs: MEDIUM); DMA |
| SDMMC1 | SD-kaart, 4-bit, IDMA, IRQ49, card detect PA15 | `control_unit/docs/storage.md` | B | SD-protocol (init op 400 kHz, ACMD6, 48 MHz in default speed aanvaard); image als achtergrond; card detect ≥ 320 ms laag |
| USART1 | Bluetooth-module (AT), CI-V-parser en console op één lijn | `control_unit/docs/peripherals.md` USART1, `docs/civ.md` | B | RX via circulaire DMA, TX blokkerend. Het BT401-AT-model en de CI-V-injector **delen** de RX; het harnas demultiplext TX (§3.5.14) |
| USART2 | De link | `docs/protocol.md` | B | Zoals bij Main, plus receive-to-idle |
| TIM2 | Encodermodus (×4), hoofdknop | `analysis/peripherals/timers.csv` | B | **Encodermodus**: CNT volgt geïnjecteerde kwadratuurflanken |
| TIM3/5/13/14 | 100 Hz GT911, 20 kHz audio, 50 Hz link-client, 1 kHz input | idem | B | Update-IRQ's in VT (IRQ 29/50/44/45) |
| TIM4 | PWM CH1/CH2 (backlight), ~3,66 kHz | idem | R + tap | Duty-cycle gelogd (helderheid bij screenshots) |
| TIM7 | CW-tekstkeyer: ARR per WPM | idem | B | Herprogrammeren van ARR werkt meteen of bij de update (H7-ARPE) |
| TIM8 | PWM-input capture op PI5 (H-22), 30 MHz | `control_unit/docs/peripherals.md` H-22, `analysis/peripherals/h22_timing.csv` | B | Reset-op-rising, CH1 periode, CH2 hoog-tijd, CC-IRQ46 |
| RTC + backupdomein | LSE, marker 0xA5A5 in backupregister 0 | `control_unit/docs/peripherals.md` RTC | R | Backupregisters behouden over runs heen (deel van de staat); VT-gebaseerde klok |
| IWDG1 | Kicks in de superloop en in SysTick | `analysis/peripherals/iwdg_kicks.csv` | B | Zoals bij Main |
| CRC | Geïnitialiseerd; geen gebruik gevonden | `docs/hardware_init.md` | **R (functioneel)** | Uit voorzorg een echte CRC-32-berekening. STemWin-builds zijn bekend om licentiecontroles via de MCU (HYPOTHESIS) |
| USB OTG_FS | MSC-device dat de W25Qxx toont | `control_unit/docs/peripherals.md` USB | R (fase 1), B (later) | Fase 1: HAL_PCD_Init en de core reset slagen (AHBIDL, CSRST), geen VBUS en geen host. Later: een MSC-functie via USB/IP (HYPOTHESIS dat de Renode-USB/IP-route bruikbaar is) |

### 3.5 Externe chips en gedragsmodellen

#### 3.5.1 FPGA (Intel Cyclone 10, docs: HIGH voor de familie)

**Interface.** Een bit-banged 8-bit bus op GPIOE (VERIFIED,
`main_unit/docs/peripherals.md` FPGA-bus, `analysis/peripherals/fpga_bus.csv`).
Het model zit als één C#-component op GPIOE en volgt MODER, ODR, BSRR
en IDR. Het decodeert:
- een **commandobyte** als PE8 en PE9 samen pulsen;
- de **databytes** per STB-puls op PE9;
- de **richting** uit MODER van PE0–7. Leest de MCU terwijl het model
  niet drijft, dan is dat een busconflict, en dat wordt gelogd.

| Commando | Modelgedrag |
| --- | --- |
| `0x00` loopback | Echo van de laatst geschreven byte. De boottest schrijft en leest 0–255 tweemaal (VERIFIED) |
| `0x01` configuratieframe (24 B) | Opslaan en decoderen: statusbytes, drie 32-bit NCO-woorden (big-endian) en de rate-index. Tuned frequentie = woord × 122,88 MHz / 2³², met vouwing naar 0–61,44 MHz en de inversievlag (VERIFIED voor het woordformaat, `main_unit/docs/peripherals.md`) |
| `0x02` status | Twee vlagbits (bit 0 = ADC-overload naar `0x03`-vlag bit 6, HIGH) en drie 16-bit waarden. De betekenis van de waarden is onbekend (docs: Q9); het model geeft configureerbare waarden, standaard de ADC-piek uit de signaalgenerator |
| `0x03` TX-I/Q | Twee signed 24-bit waarden per sample, naar de **TX-sink** (opname plus plant-koppeling) |
| `0x04` RX-I/Q | Twee signed 24-bit waarden per sample, uit de **RX-bron**. 8/4/2/1 samples per DRDY voor rate 0–3 (VERIFIED in code) |
| `0x05/0x06`, `0x09/0x0A` | Pulscommando's, alleen gelogd. Init stuurt de "uit"-codes; geen andere zender in V1.0.1 (HIGH) |
| `0x08` versie | 3 bytes, configureerbaar. Alleen gelogd (VERIFIED) |

**DRDY (PE10).** Een rising flank in VT op een configureerbare rate:
standaard 48 kHz (docs: MEDIUM → HYPOTHESIS), bij elke rate-index
hetzelfde.

**RX-bron (signaalgenerator).** Een lijst van RF-componenten
{frequentie, niveau in dBFS, modulatie (CW, AM, SSB uit WAV, FM-toon)}
plus ruis (dBFS/Hz). Per sample berekent het model het basisbandsignaal
ten opzichte van de tuned NCO-frequentie, met de inversievlag, op de
rate uit de rate-index (384/192/96/48 kS/s, HYPOTHESIS). Alternatief
speelt het een I/Q-bestand af. Boven een drempel gaat de
overload-statusbit aan.

**TX-sink.** Neemt de 24-bit I/Q op en levert aan het plant-model de
omhullende \|I+jQ\| per blok (§3.5.9). De eerste 200 interrupts na het
intoetsen zijn nul (VERIFIED); dat is een controlepunt in de golden
trace.

**Health-orakel.** De firmware logt een FPGA-busfout als het eerste
RX-sample meer dan vijf controles lang gelijk blijft (VERIFIED). De
standaardbron **MOET** daarom altijd ruis bevatten. Een fault-injectie
"stuck sample" test dit gedrag juist.

**Prestaties.** Bij rate 0 gaan per DRDY 8 × 6 = 48 bytes over de bus,
dus ~2,3 MB/s bij 48 kHz. Met ≥ 3 MMIO-toegangen per byte geeft dat
≥ 7·10⁶ MMIO/s (afleiding, HYPOTHESIS voor de exacte instructiemix).
Daarom is GPIOE plus FPGA **één gefuseerd C#-model**; het MAG
burst-herkenning doen (na het CMD-patroon van `0x04` staan de volgende
N bytes klaar); en de standaardbaseline draait op rate-index 3, met een
aparte suite op 0–2.

#### 3.5.2 CH394-ethernet (W5500-compatibel registermodel)

**Registermodel** (HIGH, `main_unit/docs/peripherals.md` SPI6,
`analysis/peripherals/spi6_ch394.csv`, `ch394_network.csv`; publieke
WCH-handleiding CH394, versie 1.2). Elke toegang is een CS-venster
(PG15) met een 16-bit offset, een controlebyte met blokselectie en
schrijfvlag, en de data. Gemodelleerd worden:
- **de gewone registers:** MODE (inclusief RST bit 7, **WOL bit 5**,
  PING-blokkering bit 4), GWIP, SMIP, MAC (uit het modelprofiel), IP,
  IIT, **GINT/GINTE** (inclusief het magic-packet-bit MP, bit 4),
  SINT/SINTE, RTIME, RCNT, PHY_CFG (link-bit, power-down via
  OPWD/OPMDC), CHIPV `0x0039` (configureerbaar, alleen gelogd),
  CHIP_CONFIG `0x003E`;
- **8 sockets** met de W5500-compatibele registers (MODE, CTRL, INT,
  STA, PORT, DIP, DPORT, buffergroottes, TX- en RX-pointers, INTE);
- **de pools:** 16 KB TX en 16 KB RX met de indeling per socket.

Het model ondersteunt **UDP** (stock gebruikt alleen UDP, VERIFIED) en
**TCP** (nodig voor TCI in de NF; semantiek uit de publieke
W5500- en CH394-documentatie).

**Reset.** RST# op PB5, laag is reset. Na het loslaten geldt een
niet-toegangsvenster van 12–19 ms volgens WCH (VERIFIED, docs citeren
CH394DS1). Toegang binnen het venster wordt **genegeerd en gelogd**;
zo blijft de boot-schrijfactie naar `0x0039` correct onschadelijk.

**INT#** (PC13, actief laag) volgt de interruptvlaggen en -enables.
Stock leest het interruptregister nooit en schrijft RECV blind
(HIGH); het model moet dus alleen correct deasserten.

**Timing.** SEND voltooit na een configureerbare latentie in VT,
standaard datagramlengte / 100 Mbit/s plus 20 µs (HYPOTHESIS). Een
fault-injectie "SEND hangt" laat de commandobyte niet wissen.

**Netwerkbackends:**

| Backend | Rijstrook | Werking |
| --- | --- | --- |
| **VLAN** (virtueel LAN, standaard) | deterministisch | Datagrammen naar een in-emulatie-netwerk waarop de **testclients in VT** draaien. Geen ARP/IP nodig: de CH394 doet ARP en ICMP zelf (HIGH), dus het model werkt op socketniveau en beantwoordt zelf ping (tenzij MODE-bit 4 het blokkeert). pcapng-export voor Wireshark met de dissectors uit `g7250-base/tools/wireshark` |
| **UDP-offload** | live | Elke geopende socket bindt een host-UDP-poort (met een configureerbare offset). Inkomende datagrammen krijgen de VT-stempel van aankomst en worden opgenomen |
| **TAP** | live | Frame-niveau via een Renode-TAP-brug. Het model voert zelf ARP, ICMP-echo, UDP/TCP en de magic-packet-detectie uit (zoals de echte chip), op een apart subnet |

**Tijdsdilatatie.** Draait de emulator langzamer dan realtime (§8.7),
dan MOETEN live-clients met wandklok-time-outs (stock: 5 s per
handshakestap, 15 s stilte, VERIFIED) een dilatatiefactor krijgen, of in
de deterministische rijstrook draaien. Het harnas biedt `vt_now()` en
`vt_sleep()`.

#### 3.5.3 AIC3204-codecs

| Eenheid | Rol | Modelgedrag |
| --- | --- | --- |
| Main, I2C1 0x18, reset PB10 | I²S-**slave** van I²S3; klok van de MCU | Registerbestand met paginaselectie (`control_unit/analysis/peripherals/aic3204_init.csv`). ADC links = de mic-ingang, vanuit de CTRL-kabel of een WAV-bron. De DAC-uitgang gaat naar de "analoge" CTRL-kabel en naar een WAV-opname. MICPGA-gain volgbaar (VERIFIED, `main_unit/docs/peripherals.md`) |
| Control, I2C2 0x18, reset PH2 | I²S-**master** van I²S2 | Genereert BCLK/WCLK in VT; standaard 48 kHz, optioneel ~48,005 kHz (PLL-quirk, docs: MEDIUM). IN1L = RX-audio van Main, IN1R = mic, IN2R+IN3R = line-in in digiMode; uitgangen naar WAV-sinks en de CTRL-kabel (`control_unit/docs/peripherals.md`) |

Leest de firmware een register terug, dan geeft het model de laatst
geschreven waarde of de datasheet-resetwaarde.

#### 3.5.4 EEPROM 24Cxx (Main, I2C1 0x50)

- Ten minste 24C128 (hoogste adres `0x24A7`), 2-byte adressering,
  64-byte pagina's, schrijfcyclus 5 ms met NACK tijdens het interne
  schrijven (datasheet; de firmware wacht vast 10 ms, VERIFIED,
  `main_unit/docs/memory_map.md`).
- Een bestand als achtergrond.
- **Profielen:** leeg (0xFF); "fabrieksvers" (één boot met een leeg
  image, waarbij de firmware de kalibratiedefaults terugschrijft,
  VERIFIED); gevuld met varianten voor de kalibratietests (§6.8).
- **Fault-injectie:** stroomverlies midden in een paginaschrijfactie
  geeft een gedeeltelijk geschreven pagina met deterministisch gekozen
  bytes.

#### 3.5.5 AXP223-PMIC (Main, I2C1 0x34)

Registerbestand met resetwaarden uit de publieke AXP22x-datasheet; de
firmware leest ook terug (`main_unit/analysis/peripherals/i2c_memread_callers.csv`,
HIGH). Een tap logt railspanningen en enables
(`analysis/peripherals/axp223_rails.csv`). De "veilige toestand" (alleen
DCDC1) wordt herkend en gelogd (VERIFIED). De rails voeden in het
PowerModel (§3.8.6) de FPGA-, codec- en PA-domeinen.

#### 3.5.6 VersaClock 6 (Main, I2C1 0x68 of 0x6A)

Registerbestand 0x00–0xFF. De burst van 112 bytes en het teruglezen van
256 bytes geven de geschreven waarden en verder de datasheet-defaults.
Het adres is configureerbaar, zodat de terugval getest kan worden
(VERIFIED). Een tap decodeert het uitgangsplan naar de OUT1-frequentie
(`analysis/peripherals/vc6_clock_plan.csv`).

#### 3.5.7 SPI1-latches (Main): RF-schakelingen en ATU

Vijf latchmodellen (HIGH, `main_unit/docs/peripherals.md` SPI1,
`docs/atu.md`):
- keten A, 8 bit: latch PA11, OE PA10; TX-LPF-bank en T/R-bit 7;
- keten B, 24 bit: latch PH12, OE PH10; RX-BPF, modusbits, PRE
  (bit 18–20) en ATT (bit 21–22);
- de ATU-latches: PD13 (stijl, in-line, antenne), PG2 (L) en PG5 (C,
  gespiegeld).

Elke latchwaarde wordt met VT-stempel gelogd en aan het plant-model
gegeven.

#### 3.5.8 SPI2-DAC (BU2506FV-type, Main)

Het 16-bit frame wordt gedecodeerd: twee voorloopbits weg, 4-bit adres
LSB-first, 10-bit waarde (HIGH). LD (PB12) laat de waarde toe; RESET
(PB14, actief laag) zet alles op VrefL. De kanalen volgens
`analysis/peripherals/spi2_dac.csv` gaan naar het plant-model: 1 drive,
2/8/7 bias, 3 ventilator, 6 vermogensreferentie.

#### 3.5.9 ADC-ingangen en het plant-model (Main)

Het plant-model levert de 7 ADC-ranks (VERIFIED voor de toewijzing,
`main_unit/docs/peripherals.md` ADC1, `analysis/memory/meter_fields.csv`):

| Rank | Grootheid | Plant-gedrag (standaard) |
| --- | --- | --- |
| 1 | Vext | 13,8 V; omgezet met de documentconstante 0,004835 V/LSB (de deler is een HYPOTHESIS). Scenario's: 10,5 / 11,5 / 15,5 V |
| 2/3 | Forward- en reflectiedetector | Uit P_fwd en Γ van de belasting; inverse van de gedocumenteerde wet P = 0,003405·x + 5,557·10⁻⁶·x² (x = 2·raw), plus richtingslek en reflectieversterking |
| 4 | Idd | I_static + Σ k_i · bias_i (ruststroom per trap) + I_rf(P). Parameters zo gekozen dat de **bias-trim bij de boot convergeert** (doelen +0,5 A en +0,9 A, ±0,1 A; VERIFIED). Een scenario "niet-convergerend" test het faalpad |
| 5 | PA-temperatuur | NTC-model, B ≈ 3950, raw 2047 = 25 °C (VERIFIED), met een thermische tijdconstante |
| 6/7 | EALC/ALC | Configureerbaar, standaard laag |

**P_fwd** volgt uit: T/R in TX (keten A bit 7 plus de T/R-lijnen), bias
aan, een LPF die de frequentie dekt, de TX-I/Q-omhullende, de
vermogensreferentie (P_ref = (ch6/75)²) en de drive (kanaal 1). Het
model is eenvoudig en monotoon; het claimt geen RF-getrouwheid, alleen
consistentie voor regelkringen en orakels.

**Belastingsmodel.** De antenne-impedantie per poort (ANT1/ANT2) als
functie van de frequentie; de ATU-latches transformeren die volgens een
eenvoudig L-netwerkmodel, zodat de ATU van stock (`docs/atu.md`) kan
convergeren of gericht falen. Standaard is de belasting een **50 Ω
dummy load**.

**Veiligheidsorakels.** Het plant-model meldt: RF-drive zonder T/R in
TX; een LPF die de TX-frequentie niet dekt; T/R- of ATU-relais schakelen
met drive aanwezig ("hot switching"); vermogen boven de cap; TX buiten
de toegestane lijst; TX in de slaapmodus (§3.8.4). Voor stock zijn dit
**rapportages** van bekend gedrag (stock heeft bijvoorbeeld geen
expliciete vertraging in de T/R-sequentie, VERIFIED,
`main_unit/docs/flow.md`). Voor de NF zijn het **harde fouten** (§10.4).

#### 3.5.10 W25Qxx-NOR (Control, SPI1)

JEDEC-ID configureerbaar: 0xEF4014/15/17/18 = 1/2/8/16 MiB; 0xEF4016 is
een fout-pad van stock (VERIFIED, `control_unit/docs/peripherals.md`).
Commando's 0x9F, 0x03, 0x06, 0x02, 0x20 en 0x05; WIP-duur in VT. Het
image is een FAT-volume (`1:`) met `config.ini`, de bandstack-bestanden,
`cwcall.ini` en de geheugenkanalen (`control_unit/docs/storage.md`).
Fault-injectie: stroomverlies tijdens het herschrijven van een sector.

#### 3.5.11 GT911-touch (Control, I2C1)

- **Adres:** het model bemonstert INT (PE2) op het moment dat RST
  (PG14) loslaat: hoog geeft 0x14, laag 0x5D (datasheet; de firmware
  drijft INT hoog, VERIFIED).
- **Registers:** product-ID, firmwareversie, resolutie (1024×600) en een
  configuratieblok van 186 bytes met een **geldige checksum**; bij een
  fout blijft TIM3 uit (VERIFIED).
- **Commando's 3 en 4** worden aanvaard.
- **Injectie-API:** `touch(x, y, duur)` en `swipe(...)`: het ready-bit en
  de punten in het 42-byte statusblok, plus een rising flank op INT.
- **Fault-injectie:** 10 I2C-fouten op rij; de firmware schakelt dan de
  touch-IRQ uit (VERIFIED).

#### 3.5.12 Display en framebuffer-capture

Het LTDC-model leest het laagadres op het moment van de VSYNC en levert
een frame van 1024×600 RGB565. Capture op verzoek, bij elke VSYNC na een
wijziging, of periodiek; uitvoer PNG plus de SHA-256 van de ruwe
pixels; de backlight-duty en de paneelvoedingssequentie in de metadata.
Zelfde invoer en VT geeft hetzelfde frame (vast RTC-epoch).

#### 3.5.13 Invoer-injectie (Control)

| Invoer | Model | Bron |
| --- | --- | --- |
| Toetsmatrix 5×5 plus de directe toets PA0 | Een elektrisch matrixmodel: drijft de firmware groep B laag en leest ze A, dan geeft het model laag op A[i] voor elke ingedrukte toets op (i, j), en omgekeerd | `control_unit/docs/peripherals.md`, `analysis/peripherals/button_map.csv` |
| Korte druk, hold, repeat | `press(code, ms)`; debounce vraagt 4 gelijke scans (~20–25 ms); hold ~0,84 s (docs: MEDIUM) | `control_unit/docs/gui.md` |
| 8 GPIO-encoders | Kwadratuurgenerator, minstens 2 samples (≥ 2 ms) per fase | `analysis/peripherals/encoder_map.csv` |
| Hoofdknop | TIM2-encodermodus, telwaarde-injectie | idem |
| Touch | GT911-model (§3.5.11) | — |
| H-22-micro-toetsenbord | Symboolgenerator op PI5: preambule ≥ 7 nul-symbolen, sync (verhouding ~4), 39 databits LSB-first (A = bits 0–19, B = bits 20–38, bits 12–19 gelijk). Toetscode = ((A>>15)&0x0F) \| ((A>>6)&0xF0). Hoog-tijd standaard 200 µs (< ~437 µs); loslaten = 50 ms zonder flank | `control_unit/docs/peripherals.md` H-22, `analysis/peripherals/h22_keycodes.csv`, `h22_timing.csv` |
| SD card detect | PA15 laag ≥ 320 ms = kaart aanwezig | `control_unit/docs/peripherals.md` |

#### 3.5.14 Bluetooth-module en de gedeelde USART1 (Control)

- **AT-model** (BT401-dialect, docs: MEDIUM): elke `AT…`-regel krijgt een
  `OK`-regel; de time-out is 3 s met 5 herhalingen; in een
  fault-scenario MAG het model zwijgen.
- **Voeding** via PCA9557-bit 4. Met de module "uit" geeft het model geen
  OK. De CI-V-parser ziet toch elke byte (VERIFIED, `docs/civ.md`).
- **TX-demultiplexer van het harnas:** CI-V-frames (`FE FE … FD`),
  AT-regels en consoleregels krijgen elk een eigen kanaal in de trace.
- **De CI-V-stroom van stock in de tests** loopt via deze USART1, de
  enige CI-V-ingang van Control in de code (VERIFIED). Op de echte radio
  loopt de USB-CAT via de CH342; die route is onbekend (HYPOTHESIS,
  `docs/hardware.md`, T0.8/T0.9). Het logische eindpunt **"USB-CAT"** is
  daarom standaard aan Control USART1 gekoppeld, met een
  bedradingsoptie.

#### 3.5.15 PCA9557 (Control, I2C2 0x19, reset PG3)

Registermodel (input, output, polariteit, configuratie) met een
bit-tap: bit 4 BT-voeding, bit 5 shutdown-puls, bits 6/7 TX/RX-audio
(rollen HYPOTHESIS, gedrag VERIFIED, `analysis/peripherals/pca9557_bits.csv`).
De eerste flush ~3 s na de reset is een boot-mijlpaal (§6.2).

#### 3.5.16 SD-kaart (Control)

Een SDHC-model met een FAT32-image (volume `0:`) voor de
spraakgeheugens. Profielen: geen kaart, lege kaart (de firmware
formatteert automatisch), gevulde kaart.

#### 3.5.17 CTRL-kabelmodel (systeemniveau)

De CTRL-kabel is een 15-polige HD-D-sub (VERIFIED, `docs/hardware.md`
§7). De bedrading is grotendeels onbekend; het model leest
`wiring.yaml` met een betrouwbaarheid per verbinding:

| Verbinding | Standaard | Betrouwbaarheid |
| --- | --- | --- |
| 13,8 V-afgeleide voeding van Main naar Control (nooit omgekeerd) | verbonden | HIGH (eigenaar, `docs/hardware.md` §1) |
| Main USART2 ↔ Control USART2 | verbonden (gekruist TX/RX) | HIGH (`docs/architecture.md`) |
| Main codec-DAC → Control IN1L (RX-audio) | analoog, gain 0 dB | HYPOTHESIS (docs: MEDIUM) |
| Control codec-uitgang slot 1 → Main mic-ingang | analoog | HYPOTHESIS |
| Control PE3/PE4 → Main PH3/PH4 (CW-key) | verbonden | HYPOTHESIS (`docs/cw.md`) |
| Control PI6 → Main PH6 (PTT bij spraakweergave) | verbonden | HYPOTHESIS (`control_unit/docs/voice_cw_memories.md`) |
| Power-toets → Main PH5 | harnas-gestuurd (PowerModel) | HYPOTHESIS (`TODO.md`) |
| Main PH9 (power hold) | naar het PowerModel | HYPOTHESIS |

Tests die van een HYPOTHESIS-verbinding afhangen, krijgen de tag
`wiring:hypothesis`. Een HIL-uitkomst mag zo'n verbinding bevestigen of
weerleggen (alleen black-box, §11).

### 3.6 Systeemniveau: bediening

| Handeling | Emulatie |
| --- | --- |
| Inschakelen | Via het PowerModel (§3.8.6): DC aan, dan een toets of auto-start afhankelijk van H1/H2. Beide machines starten met een configureerbare onderlinge vertraging. Main zendt `0x03` vanaf de boot zonder op Control te wachten (VERIFIED, `docs/protocol.md`) |
| Ordelijk uitschakelen | PH5 > 1 s laag. Main zet `0x03`-vlag bit 2, wacht 100 ms en sluit af. Control slaat `config.ini` en de stores op en wist daarna PCA9557-bit 5. Main wacht tot PH5 hoog is en reset dan (VERIFIED, `main_unit/docs/flow.md`) |
| Stroomuitval | DC weg op een gekozen VT-moment. Persistente media (EEPROM, NOR, SD, backupdomein) behouden de toestand van dat moment, met een gedeeltelijke schrijfactie waar gepast |
| Kabel los | De LinkCable onderbreekt TX/RX gedurende T. Main laat na ~1000 passages (2–3 s) de PTT vallen; Control bevriest (VERIFIED/docs: MEDIUM) |

### 3.7 Systeemconfiguraties

| Config | Main | Control | Link | Doel | Plaats |
| --- | --- | --- | --- | --- | --- |
| **SS** stock+stock | stock | stock | stock-SLIP | Baseline: valideert de hardwaremodellen (§6) | **kritiek pad, stap 1** |
| **EH** eigen Main headless | NF-Main | — (geen machine; CTRL-kabel los) | niet verbonden | **Primaire doelconfig.** Bediening uitsluitend via P1 en TCI op het netwerk, met AetherSDR of andere SDR-software als host | **kritiek pad, stap 2** |
| **ES** eigen Main + stock Control aangesloten | NF-Main | stock (ongewijzigd image) | fysiek verbonden; voor de NF-Main is het linkverkeer van het stock-paneel alleen onbekende bytes | **Alleen een robuustheids- en veiligheidstest**, geen doelconfiguratie en geen compatibiliteitstest (§8.3.6) | lage prioriteit |
| **EE** eigen+eigen | NF-Main | NF-Control | NF-link (eigen ontwerp, met versie-onderhandeling) | Latere, optionele track: een eigen frontpaneel | optioneel, later |

**Niet ondersteund als functionele configuratie:** een NF-Control met
een stock Main, en elke vorm van samenwerking tussen NF-Main en stock
Control. De interface van de NF-Main wijkt zo sterk af dat het
stock-paneel er helemaal niet mee kan praten. ES bestaat alleen om te
bewijzen dat een aangesloten stock-paneel de NF-Main niet verstoort en
geen schade oploopt.

**Eisen aan de NF-Main in EH:**
- De NF-Main MOET zonder Control-peer draaien: geen wachten op de link,
  geen fout bij link-stilte, alle bediening via P1, TCI en (optioneel)
  CI-V over het netwerk.
- De voedingseisen van §3.8.4 gelden (PH5 standaard genegeerd,
  always-on, slaap en wake).
- De hardware-PTT (PH6) en de key-ingangen (PH3/PH4) zijn volgens de
  NF-spec bruikbaar of uitgeschakeld; dat is een keuze van de NF-spec,
  met een test.
- De CTRL-kabel staat in EH op "los". De wiring-tests met
  `wiring:hypothesis` zijn n.v.t.

**Eisen aan de NF-Main in ES (robuustheid en veiligheid; lage
prioriteit):**
- **S-ES1 — Linkverkeer van het paneel = onbekende bytes.** Alles wat
  op USART2 binnenkomt van het stock-paneel (de `0x01`-images van elke
  20 ms, `0x06`-verzoeken, ruis) is voor de NF-Main een stroom onbekende
  bytes. Ze MOET die robuust negeren, zoals bij een fuzz-test: geen
  crash, geen hang, geen geheugenlek, geen toestandswijziging, geen TX.
  Het stock-verkeer dient in de emulator als fuzz-corpus (§8.4).
- **S-ES2 — Hardwarelijnen van het paneel standaard genegeerd.** Alle
  lijnen die via de CTRL-kabel van het paneel kunnen komen (PTT,
  CW-key, power-toets, audio; deels hypothesen, §3.5.17) MOET de
  NF-Main negeren, tenzij een lijn **expliciet in haar eigen
  configuratie** is ingeschakeld. Standaard veroorzaakt geen enkele
  paneellijn TX, keying, uitschakelen of een audio-pad naar de
  modulator.
- **S-ES3 — Niets naar het paneel dat zijn persistente staat kan
  wijzigen.** De NF-Main MOET NOOIT iets naar het paneel schrijven dat
  de persistente staat van het paneel kan veranderen:
  - geen frame dat de stock-decoder als geldig `0x03` met
    power-off-bit 2 kan lezen: stock Control schrijft `config.ini`
    alleen bij dat signaal (VERIFIED, `control_unit/docs/storage.md`);
  - aanbevolen: op de link naar het paneel helemaal niets zenden zolang
    er geen eigen paneel met een geldige onderhandeling is. Zendt de
    NF-Main toch (bijv. een onderhandelingsbeacon van de NF-link), dan
    MOET die framing bij de stock-decoder op CRC of lengte falen (te
    testen met de stock Control in de emulator);
  - geen spanning of signaal op paneellijnen buiten de HIS-specificatie.

  Orakel: na een ES-run zijn de NOR, de SD en het backupdomein van de
  stock Control **bytegelijk** aan vóór de run.
- Een "niet ondersteund"-toestand op het stock-paneel wordt **niet**
  nagestreefd: het paneel kan niet met de NF-Main praten.

### 3.8 Topprioriteit R0: kan de Main zonder Control inschakelen en werken?

Dit is **R0**, het grootste risico op het kritieke pad (§14.2). Als de
Main alleen inschakelt via de power-toets op het paneel, en die toets
via de CTRL-kabel loopt, dan is EH op de echte radio zonder aangesloten
paneel onmogelijk. Het stock-paneel moet dan fysiek aangesloten
blijven, enkel als inschakelpad, onder de ES-regels; de power-toetslijn
mag dan alleen gebruikt worden als die expliciet in de eigen
configuratie is ingeschakeld (S-ES2).

#### 3.8.1 Feiten uit de docs, de eigenaar en publieke meldingen

| Feit | Bron | Label |
| --- | --- | --- |
| De 13,8 V komt binnen op de Main. De Main voedt het paneel via de CTRL-kabel, nooit omgekeerd | eigenaar; `docs/hardware.md` §1 | HIGH |
| De Main schakelt in door PH9 hoog te zetten, 1 s te wachten en dan de AXP223-rails te programmeren en in te schakelen (eerst een veilige toestand met alleen DCDC1, dan alle rails samen) | `docs/hardware_init.md`, `main_unit/docs/flow.md` (power-on 1–3), `main_unit/docs/peripherals.md` (AXP223) | VERIFIED |
| PH5 is een ingang met interne pull-up (de power-toets-sense) | `main_unit/analysis/peripherals/gpio_map.csv` | HIGH |
| De power-toetslogica (TIM6, 100 Hz) wapent pas als PH5 één keer hoog gezien is. PH5 > 1 s laag geeft een power-off-verzoek | `main_unit/docs/flow.md` | VERIFIED |
| Uitschakelen: vlag in `0x03`, 100 ms wachten, alles veilig zetten (T/R-lijnen laag, DAC-kanalen 0, latch-uitgangen uit, CH394 in reset), kalibratie en ATU opslaan indien dirty, AXP223 naar de veilige toestand, interrupts uit, **wachten tot PH5 weer hoog is**, dan een systeemreset | `main_unit/docs/flow.md` (shutdown 1–11) | VERIFIED |
| PH9 wordt nooit expliciet laag gezet; een power-hold-lijn die de reset loslaat is een hypothese | `main_unit/docs/flow.md`, `gpio_map.csv` | VERIFIED (code) / HYPOTHESIS (rol) |
| Wat PH5 fysiek drijft (een paneeltoets via de CTRL-kabel?) is onbekend | `TODO.md` | HYPOTHESIS |
| Stock Main laadt bij elke start geforceerde defaults, ook voor het netwerk, en wacht op `0x01` van het paneel | `main_unit/docs/memory_map.md`, `docs/protocol.md` | VERIFIED |
| **De geforceerde netwerkdefaults zijn IP 192.168.3.199, gateway 192.168.3.1, netmask 255.255.255.0, basispoort 50001** | publiek upstream-issue #1 op `fventuri/g7250-base` | **HYPOTHESIS/MEDIUM (upstream-melding, niet door ons geverifieerd)** |
| **Netwerk-PTT wordt niet vrijgegeven bij verlies van de sessie** | publiek upstream-issue #2 op `fventuri/g7250-base` | **HYPOTHESIS/MEDIUM (upstream-melding, niet door ons geverifieerd)**. Past bij de docs: bij verlies van de wfview-stroom houdt Main de netwerkcontrole tot 60 s of drie pogingen (VERIFIED, `docs/protocol.md`, `main_unit/docs/network.md`) |
| De Control-shutdown pulst PCA9557-bit 5 (rol onbekend) | `control_unit/docs/peripherals.md` | VERIFIED (gedrag) / HYPOTHESIS (rol) |

**Wat de firmware niet zegt.** Of de Main-MCU al spanning heeft vóór
iemand een toets indrukt, en hoe de toets de voeding vrijgeeft. Dat zit
in hardware of in de bootloader, die beide buiten de images vallen.

#### 3.8.2 Twee hypothesen

| | **H1 — hardwarelatch op de Main** | **H2 — MCU altijd gevoed op een standby-rail** |
| --- | --- | --- |
| Werking | De toets schakelt via hardware de regelaar in; de MCU start en houdt de voeding vast met PH9. Bij de systeemreset aan het einde van de shutdown laat PH9 los en valt de voeding weg | De MCU (of een standby-deel) is gevoed zolang de 13,8 V er is. De firmware (waarschijnlijk de bootloader) wacht op PH5; PH9 schakelt de rails voor de rest van de radio |
| Past bij de docs | PH9 hoog als eerste stap, 1 s wachten, PH9 nooit laag, de reset als einde van de shutdown | De shutdown wacht op het loslaten van de toets vóór de reset; anders zou een bootloader die op PH5 wacht, meteen weer opstarten. Het reset-einde is dan "terug naar standby" |
| Zonder toets (paneel weg) | Er gebeurt niets bij DC-aan, tenzij (a) een **auto-start bij DC-aan** in hardware bestaat, of (b) als laatste redmiddel een **toets-emulatiecontact op de CTRL-connector** (hardware-aanpassing aan de buitenkant; beslissing van de eigenaar) | Alles is firmware: de NF kan zelf beslissen (§3.8.4) |
| Harde aan/uit voor EH | De 13,8 V schakelen door de stationsautomatisering, plus een auto-start (indien die bestaat) | Een schakelbare 13,8 V-voeding in de stationsautomatisering van de eigenaar, plus de firmwaremodi |

Beide zijn HYPOTHESIS en sluiten elkaar niet volledig uit.

**Valkuil van stock.** PH5 heeft een interne pull-up (HIGH); zonder
paneel leest de lijn eerst hoog en wapent de power-toetslogica. Trekt
iets aan de Main-kant van de CTRL-connector de lijn laag zodra het
paneel ontbreekt, dan ziet stock na ongeveer 1 s een power-off-verzoek
(HYPOTHESIS). Stock zet dan alles veilig, zet de CH394 in reset en
**blijft hangen tot PH5 hoog wordt**, wat zonder paneel nooit gebeurt.
Een link die opkomt en na enkele seconden wegvalt (en wegblijft tot DC
uit en weer aan), is dus een **verwacht** patroon. Volgens de
bootvolgorde komt de link pas op na de CH394-init, enkele seconden na
DC-aan (PH9 + 1 s, AXP + 1 s, EEPROM, VC6, CH394; VERIFIED volgorde,
`main_unit/docs/flow.md`).

#### 3.8.3 Beslissende tier-0-koudestartobservaties (zonder de radio te openen)

Een voorstel voor `docs/hardware_test_plan.md`. De eigenaar beslist of
hij elke stap als tier 0 aanvaardt.

**Vaste procedureregels voor elke headless stocktest** (normatief):
1. **Dummy load op de antenne-uitgang** (50 Ω, ≥ 100 W), op elke
   antennepoort die de radio kan kiezen, vóór DC-aan.
2. **Geen wfview en geen andere CI-V- of LAN-client die PTT kan zetten**
   is verbonden of actief, zolang de test loopt. Reden: de upstream-
   melding #2 (HYPOTHESIS/MEDIUM) dat netwerk-PTT bij sessieverlies niet
   vrijkomt, en de gedocumenteerde netwerkcontrole tot 60 s (VERIFIED).
   Alleen passieve captures, ping en ARP zijn toegestaan.
3. **De CTRL-kabel nooit met DC aan losmaken of aansluiten.**
4. **Nooit Enter op een Main-console** (servicemenu, VERIFIED,
   `main_unit/docs/peripherals.md`).
5. **Logboek** met datum, versies, de opstelling en elke waarneming.

**Wat een waarneming bewijst:**
- **"De LAN-link komt op"** bewijst alleen dat de CH394 uit reset is.
- **Een antwoord op een ping naar 192.168.3.199** vanaf een host in
  192.168.3.x/24 bewijst dat de applicatie draait: de CH394 beantwoordt
  ping zelf, maar pas nadat de app hem het IP-adres heeft gegeven. Na
  een stock-power-off staat de CH394 in reset, dus geen ping meer. De
  defaults komen uit de upstream-melding #1 (HYPOTHESIS/MEDIUM); een
  ARP-capture op het segment bevestigt ze.

| # | Observatie | Uitkomst → hypothese |
| --- | --- | --- |
| T0-P1 | **Stroomindicatie van de voeding** met DC aan en de radio "uit" (normaal uitgeschakeld via de paneeltoets, paneel aangesloten). Alleen de display van de eigen bankvoeding aflezen | ≈ 0 mA → **H1**. Tientallen mA → **H2**. De display moet tientallen mA kunnen tonen |
| T0-P2 | **CTRL los, DC aan:** komt de Ethernet-link van de Main op de switch op (LED of poortstatus)? | Geen link → H1 zonder auto-start, of H2 met wachten op PH5. Link op → de CH394 is uit reset (de Main is gestart). Link op en na enkele seconden weg → de stock-valkuil (§3.8.2) |
| T0-P3 | Bij T0-P2 met link: een host in 192.168.3.x/24 pingt 192.168.3.199; een passieve capture (ARP, broadcasts) | Ping-antwoord → de applicatie draait. Geen antwoord met link op → de app is nog niet zo ver, of al uitgezet (valkuil); herhalen met de tijdas vanaf DC-aan |
| T0-P4 | T0-P1 herhalen met CTRL los | Vergelijking: verbruik van het paneel tegenover standby van de Main |

T0-P1 scheidt H1 van H2; T0-P2/T0-P3 zeggen of een (auto-)start zonder
paneel mogelijk is en of de app blijft draaien. De resultaten gaan als
HIL-feit in de HIS en bepalen F0 (§10.3).

#### 3.8.4 Eisen aan de NF-Main voor het voedingsbeheer

| ID | Eis |
| --- | --- |
| P-1 | **PH5 standaard genegeerd.** Geen uitschakeltrigger tenzij expliciet in de configuratie ingeschakeld (S-ES2). Een zwevende of laag getrokken PH5 zonder paneel mag nooit tot uitschakelen leiden |
| P-2 | **PH9 vasthouden.** PH9 hoog als eerste stap bij de boot (zoals stock, VERIFIED) en hoog in elke modus behalve een bewuste uitschakeling |
| P-3 | **Always-on-modus.** Configureerbaar: na DC-aan volledig operationeel, zonder op een toets te wachten. Harde aan/uit komt van de schakelbare 13,8 V-voeding in de stationsautomatisering |
| P-4 | **Slaapmodus.** PA-bias 0, drive 0, T/R op RX, latch-uitgangen veilig, FPGA en audio (codec) uit of in reset, AXP-rails voor die delen uit waar de HIS dat toelaat; **de CH394 blijft wakker** met de link op |
| P-5 | **Veilige toestand bij het ingaan van de slaap.** Eerst de volledige RX-entry en de veilige-toestandsstappen (bias weg vóór de relais, §10.4 S7); geen relaisschakeling onder drive |
| P-6 | **Geen TX in slaap.** Elke TX-bron (P1-MOX, TCI, CI-V, hardware-PTT, VOX, key, ATU-tune) wordt geweigerd; TX vraagt eerst een volledige wake en een geslaagde zelftest |
| P-7 | **Wake over het netwerk.** Een op het lokale netwerk beperkt (en bij voorkeur geauthenticeerd) UDP-wake-commando, en/of **Wake-on-LAN** via de magic-packet-functie van de CH394 (§3.8.5) |
| P-8 | **Sleep-commando** via P1, TCI of eigen UDP-beheer; optioneel een time-out naar slaap zonder host |
| P-9 | **Ordelijk uitschakelen** (indien gevraagd): dezelfde veilige stappen als stock, EEPROM opslaan, AXP naar de veilige toestand; bij H1 PH9 loslaten als laatste stap |
| P-10 | **Status** van de voedingsmodus zichtbaar via P1, TCI en het beheerprotocol |
| P-11 | **Netwerk-PTT valt bij sessieverlies.** Als tegenhanger van upstream-melding #2: elke netwerk-TX valt binnen T_wd na verlies van de sessie (§10.4 S3) |

#### 3.8.5 CH394: Wake-on-LAN en power-down (publieke bron)

Uit de publieke CH394-handleiding van WCH (handleiding 1, versie 1.2,
wch.cn) (HIGH):
- **MODE (`0x0000`) bit 5 = WOL**: met WOL aan geeft de chip een
  interrupt als hij via **UDP** een magic packet met zijn eigen MAC
  ontvangt (6 × `0xFF` gevolgd door 16 × de MAC). Dezelfde bitpositie
  als bij de W5500 (MR bit 5).
- **GINT (`0x0015`) bit 4 = MP** (wissen door een 1 te schrijven) en
  **GINTE (`0x0016`) bit 4** als enable; de interrupt komt op INT, bij
  de G7250 PC13 (VERIFIED, `main_unit/docs/peripherals.md`).
- **PHY_CFG (`0x002E`)**: OPWD (bit 6) plus OPMDC (bits 5:3) = `110` is
  PHY-power-down; niet bruikbaar in slaap, want de link moet blijven.
- **Open (HYPOTHESIS):** of voor de magic-packet-detectie een
  UDP-socket open moet zijn (en op welke poort), en het
  standby-verbruik van de chip.

Stock zet WOL nooit aan: de driver schrijft MODE niet (VERIFIED,
`main_unit/docs/peripherals.md`).

#### 3.8.6 Emulatormodel van de voedingstoestand

Een **PowerModel**-component met de parameter `hypothese = H1 | H2`:

| Element | H1 | H2 |
| --- | --- | --- |
| DC-ingang (harnas) | aan of uit | aan of uit |
| Regelaar en latch | Toets (PH5-lijn) of de auto-start-optie zet de voeding aan; PH9 hoog houdt ze vast; PH9 laag of een reset met PH9 los → voeding uit, MCU stopt | De MCU draait zodra DC aan is (via de B2-shim, §4.3, met een optionele "wacht op PH5"-stap als model van een bootloader); PH9 schakelt een rail-domein voor de rest |
| Rails voor FPGA, codec, PA-deel | Volgen de AXP223-registers (§3.5.5) | idem, plus het PH9-domein |
| Verbruik (indicatief) | 0 mA uit | standby-waarde configureerbaar |
| PH5 zonder paneel | Configureerbaar: pull-up hoog, zwevend, of laag getrokken na x ms (de stock-valkuil) | idem |

**Tests:**

| ID | Scenario | Verwacht |
| --- | --- | --- |
| PW-1 | Stock Main, H1 en H2, paneel weg, PH5-varianten | Met PH5 hoog via de pull-up: stock draait door en beantwoordt ping op het default-IP (VLAN). Met PH5 laag na de boot: power-off-verzoek na ~1 s, veilige toestand, CH394 in reset (geen link, geen ping), en wachten op PH5. Voorspelling voor T0-P2/T0-P3 |
| PW-2 | NF-Main, always-on, H1 (met auto-start) en H2 | Boot naar operationeel zonder toets; PH5-varianten hebben geen effect (P-1) |
| PW-3 | NF-Main, slaap en wake via een UDP-commando | In slaap: geen bias en drive, FPGA- en codecdomein uit, CH394-link op; wake binnen de afgesproken tijd; zelftest vóór TX |
| PW-4 | NF-Main, slaap en Wake-on-LAN via een magic packet | MP-interrupt op PC13, wake |
| PW-5 | NF-Main in slaap, alle TX-bronnen geprobeerd | Geen enkele TX; nette weigering (P-6) |
| PW-6 | Overgang naar slaap tijdens TX | Eerst een volledige RX-entry in de juiste volgorde (P-5); geen hot switching |
| PW-7 | DC weg tijdens slaap of tijdens EEPROM-schrijven, daarna DC terug | Correcte boot in de geconfigureerde modus; vendor-records ongeschonden (E-B4) |
| PW-8 | NF-Main met aangesloten stock-paneel (ES), het paneel stuurt een toets of ruis op PH5 | Geen uitschakeling tenzij expliciet ingeschakeld (P-1, S-ES2) |

#### 3.8.7 Oplosplan, in volgorde

1. **Boot-toestand in de emulator** (RE-kant): stock Main met het
   PowerModel onder H1 en H2, met de PH5-varianten en zonder
   Control-machine (PW-1); vastleggen of stock volledig boot (A1), welk
   netwerkgedrag hij met de defaults heeft, en of er een spontane
   power-off volgt. De uitkomst gaat als hardwarefeit-hypothese de HIS
   in.
2. **De docs:** `docs/hardware.md` nalezen op het aan- en uitzetten;
   de PCA9557-bit-5-rol en de PH9-rol in `TODO.md` als gekoppelde vraag
   houden; de upstream-meldingen #1 en #2 volgen.
3. **Tier-0-observaties** T0-P1–T0-P4 van §3.8.3, onder de vaste
   procedureregels. Afronding: DC uit, de CTRL-kabel terug, DC aan, en
   de normale werking controleren.
   - H2, of H1 met auto-start: EH is haalbaar op hardware; de NF-Main
     implementeert always-on en slaap/wake (§3.8.4).
   - H1 zonder auto-start: het stock-paneel blijft tijdens HIL fysiek
     aangesloten, enkel om in te schakelen, onder de ES-regels. Een
     toets-emulatiecontact op de CTRL-connector is het laatste
     redmiddel (beslissing van de eigenaar).
4. **Firmwareproject:** het eindantwoord en de gevolgen voor de NF-Main
   staan in §15 (O7).

---

## 4. Image-aanlevering en boot-toestandsmodellering

### 4.1 Uitgangspunt: de emulator ontsleutelt niets

De emulator bevat **geen ontsleutelingscode, geen
sleutelconfiguratie en geen sleutelopslag** (geen sleutelbestand, geen
Keychain). Hij leest uitsluitend **reeds ontsleutelde
applicatie-images** die de gebruiker zelf aanlevert. Hoe de gebruiker
die images verkrijgt, valt buiten de emulator en buiten deze
specificatie (zie §12.4 voor het juridische advies).

| Feit | Bron | Label |
| --- | --- | --- |
| De vendor levert versleutelde updatebestanden (`.bbf` voor Main, `.ctl` voor Control) | `README.md`; het vendorpakket (§4.4) | VERIFIED |
| De applicatie-images van V1.0.1 zijn 453 152 B (Main) en 781 328 B (Control) | `README.md` | VERIFIED |
| Laadbasis `0x08020000`; vectoren in het image; VTOR wordt door SystemInit gezet | `main_unit/docs/startup.md`, `control_unit/docs/startup.md` | VERIFIED |
| Sector 0 (`0x08000000`, 128 KiB) bevat een bootloader die niet in de images zit | `main_unit/docs/memory_map.md` | HIGH |
| Geen van beide applicaties bevat update-, flash-unlock- of option-byte-code | `main_unit/docs/peripherals.md`, `control_unit/docs/peripherals.md` | HIGH |
| De bootloader-sprong in Main (via RTC wake-up) is dode code in V1.0.1 | `main_unit/docs/peripherals.md` | HIGH |
| Option bytes worden in productie of door de bootloader gezet | `main_unit/docs/flow.md` | VERIFIED (afwezigheid in de app) |

### 4.2 Aanlevering en controle van de images

**Configuratie.** Eén instelling wijst naar de imagemap, bijvoorbeeld
`images_dir` in een lokale configuratie van de gebruiker, of de
omgevingsvariabele `G7250_EMU_IMAGES`. De map:
- MOET **buiten elke git-werkboom** liggen; de emulator weigert te
  starten als de map binnen een git-repo ligt (controle op een
  bovenliggende `.git`);
- bevat per release de ontsleutelde applicatie-images, met een vrije
  bestandsnaam;
- MAG daarnaast de originele vendorbestanden bevatten, **alleen** als
  herkomst (§4.4).

**Manifest** (`images/manifest.yaml` in de repo, publiek): **alleen
hashes en versies**, nooit inhoud.

| Veld | Inhoud |
| --- | --- |
| `release` | bijv. `M1.0.1/C1.0.1` |
| `unit` | `main` of `control` |
| `image_sha256` | SHA-256 van het ontsleutelde applicatie-image — **door de gebruiker aan te leveren** bij de eerste ingest (§7) |
| `image_size` | grootte in bytes (V1.0.1: 453 152 / 781 328) |
| `load_base` | `0x08020000` |
| `vector_check` | verwachte MSP en reset-vector (V1.0.1: `0x24050000`/`0x08024554` Main, `0x24080000`/`0x080235AC` Control; VERIFIED) |
| `provenance` | het vendorpakket en de vendorbestanden met hun SHA-256 (§4.4) |

De `g7250-base`-README vermeldt de SHA-256 van de images die daar
geanalyseerd zijn. De gebruiker MAG die als controlewaarde gebruiken,
maar het manifest neemt alleen waarden op die de gebruiker zelf
aanlevert en bevestigt.

**Controle bij elke run** (normatief):
1. Het image bestaat en heeft de verwachte grootte.
2. De SHA-256 komt overeen met een manifestregel. Bij een mismatch
   **weigert** de emulator met een duidelijke melding, bijvoorbeeld:
   "Image voor main komt niet overeen met het manifest (verwacht
   release M1.0.1, sha256 …; gevonden sha256 …). Lever het juiste
   ontsleutelde image aan, of start de ingest voor een nieuwe release."
3. Structurele controle: vector[0] in het AXI-bereik van de unit,
   vector[1] Thumb en binnen het image, het `.data`-bereik binnen het
   image, grootte ≤ appslot.
4. Het run-manifest vermeldt de image-hashes (geen inhoud).

**Bescherming tegen lekken:** pre-commit- en CI-controles in elke repo
van het project weigeren bestanden waarvan de hash in het manifest
staat, binaire bestanden boven een drempel, en de bestandsextensies van
vendorupdates.

### 4.3 Boot-toestandsmodellering

De emulator **boot het applicatie-image rechtstreeks**. Hij emuleert
geen bootloader en geen updatepad (die horen bij het firmwareproject,
§15). Wel modelleert hij de reset- en overdrachtstoestand die een
bootloader achterlaat, zodat de stock-app correct boot:
- **klokken:** RCC na de reset op HSI, of een PLL die nog actief is;
- **VTOR, MSP en PC:** uit de vectortabel op `0x08020000`;
- **option bytes:** een profiel met plausibele, leesbare waarden (RDP,
  BOOT_ADD, CPUFREQ_BOOST voor 550 MHz op Main, IWDG_SW);
- **IWDG:** uit, of hardware-gestart met time-out T;
- **NVIC- en IRQ-staat**, eventueel een gewapende RTC-wake-up;
- **voeding:** via het PowerModel (§3.8.6).

| Strategie | Werking | Gebruik |
| --- | --- | --- |
| **B1 — directe boot** (standaard) | Renode zet PC en SP uit de vectoren op `0x08020000`, met VTOR = `0x08020000` (SystemInit zet het opnieuw). De kern- en peripheral-staat komt uit het boot-toestandsprofiel | Baseline, de meeste tests |
| **B2 — reset-vector-shim** | Een kleine clean-room stub (eigen code, enkele instructies) op `0x08000000`: VTOR zetten, MSP laden, naar de reset-vector van de app springen; optioneel "wacht op PH5" voor PowerModel-H2. Uitdrukkelijk **geen bootloadermodel** | Tests die door een reset heen lopen, de dode RTC-wake-sprong van Main, PowerModel-H2 |

De NF-images worden op dezelfde manier geboot en MOETEN in elk profiel
correct booten; ze mogen niet afhangen van een klok- of IWDG-staat die
een bootloader zou achterlaten.

**Boot-toestandsprofielen:**

| Profiel | IWDG | Klokken | NVIC en IRQ | Opmerking |
| --- | --- | --- | --- | --- |
| `clean` | uit | reset (HSI) | alles uit | standaard |
| `iwdg-hw` | gestart, time-out T in {4, 8, 16, 32} s | reset | uit | test de aanname "uit of meerdere seconden" (docs: MEDIUM) |
| `pll-left-on` | uit | PLL actief, SYSCLK op PLL | uit | SystemInit en HAL moeten dat correct terugzetten |
| `rtc-wkup-armed` | uit | reset | RTC-WKUP-IRQ aan | Toont dat de dode sprong pas vuurt als de bootloader hem gewapend laat (HIGH) |

Een baseline-run is pas "groen" als stock in **alle** profielen voldoet
aan §6, of als een afwijking uitdrukkelijk als profielafhankelijk
gedocumenteerd is.

### 4.4 Herkomst: het officiële vendorpakket

Het officiële vendorpakket wordt **alleen bewaard en gehasht** als
herkomst in het manifest. De emulator parseert, ontsleutelt of gebruikt
het nooit.

| Item | Waarde |
| --- | --- |
| Pakket | `2026-11-09_Xiegu_G7250_V1.0.1.zip`, van radioddity.com/pages/xiegu-download |
| SHA-256 pakket | `70d250a1d90a0e98da35e2845eea45288b9d1dc73552293287c882fd95372af8` |
| Main-updatebestand (versleuteld) | `G7250_MainUnit_Fw_V1.0.1.bbf`, 453 152 B, SHA-256 `66b97ad90de2711fcc88d8fb8c034fde57fa5cf1b483bfd75041b35edebb09d0` |
| Control-updatebestand (versleuteld) | `G7250_ControlUnit_Fw_V1.0.1.ctl`, 781 328 B, SHA-256 `78b61101a968dc9d786e75adb11552a4cdabc6944a50aed7492e095df286ee2e` |
| Ontsleutelde images | SHA-256 **door de gebruiker aan te leveren** |

**Publieke vendordocumentatie in het pakket** (bruikbaar als
clean-room bron, want publiek en bedoeld voor gebruikers):
- een **CI-V-referentie, revisie 1.2** (PDF): de publieke CI-V-
  commandoset; bron voor de CI-V-conformance van de NF (§8.3.4) en een
  cross-check op de black-box-baseline A4/A5;
- een **wfview-rigbestand `G7250.rig`** met CI-V-adres 0xA0: bevestigt
  de vendorkeuze voor het adres dat stock over LAN gebruikt (VERIFIED,
  `docs/civ.md`) en beantwoordt de open vraag in `TODO.md` of Xiegu een
  rigbestand levert. Het is documentatie; wfview zelf blijft geen
  testclient;
- een **HDSDR-ExtIO-DLL**: alleen als black-box-client bruikbaar voor
  HIL-tests in HDSDR-modus; deze vendorsoftware wordt niet
  geanalyseerd;
- **release notes**: bron voor de versiematrix (§7.2).

---

## 5. Gap-analyse

### 5.1 Ontbrekende kennis voor perfecte emulatie

Prioriteit: **K** = kritiek (boot of hoofdfunctie hangt ervan af),
**M** = middel, **L** = laag.

| # | Gat | Prio | Bron van het gat | Sluiten met dynamische analyse in de emulator | Kan HIL (tier 0) helpen? |
| --- | --- | --- | --- | --- | --- |
| G1 | Staat die de bootloader bij overdracht achterlaat | M | `main_unit/docs/peripherals.md` | Profielmatrix §4.3; de read-before-write-detector | Nee |
| G2 | Option bytes en IWDG-time-out | M | `TODO.md` | IWDG-profielsweep; boot-kickinterval meten (Main boot > 2 s zonder kick) | Nee (SWD nodig) |
| G3 | FPGA: echte sample rates, TX-rate, statuswaarden, kalibratiebytes, pulscommando's | **K** voor de NF, M voor stock | `docs/hpsdr_gap_analysis.md` Q1–Q3, Q9 | Alle FPGA-transacties loggen; per rate-index het aantal gelezen samples per DRDY tellen; afleiden wat de firmware *verwacht* | Deels: T0.3, T0.4, T0.5 |
| G4 | DRDY-rate en jitter | M | `main_unit/docs/peripherals.md` | Parametriseren; de gevoeligheid meten (underrun, health-check) bij 40–56 kHz | Indirect, via T0.3 |
| G5 | Rate van `0x03`-frames (volgt de FFT) | M | `docs/protocol.md` | **Volledig te sluiten in de emulator**: meten en als baselinewaarde bevriezen | Nee |
| G6 | CH394: CHIPV-waarde, PHY-details, SEND-latentie, maximale SPI-klok, WOL-voorwaarden | L/M | `main_unit/docs/peripherals.md`, Q4; §3.8.5 | Leesvolgorde en pollinglussen loggen; de SEND-latentie variëren | T0.3/T0.6; T0-P3 |
| G7 | VC6- en AXP223-teruglees-inhoud | L | `main_unit/docs/peripherals.md` | Nagaan of de firmware op de inhoud beslist | Nee |
| G8 | GT911-configuratieblok, product-ID, coördinatenoriëntatie | M | `control_unit/docs/peripherals.md` | Synthetisch blok; oriëntatie fitten met aanrakingen op bekende knopposities | T0.1 |
| G9 | Paneellegenda's, knop- en drukparen | L | `control_unit/docs/gui.md` | Niet nodig; de codes zijn bekend | T0.1 |
| G10 | Bedrading van de CTRL-kabel (audio, PE3/PE4, PI6, PH5, PH9) | M | `TODO.md`, `docs/cw.md` | `wiring.yaml` plus getagde tests | T0.11, T0.9, T0-P2 |
| G11 | Inhoud van een echte EEPROM | L voor de emulatie, M voor de twin | `TODO.md` | Defaults volstaan; de firmware schrijft ze zelf (VERIFIED) | Nee |
| G12 | Plant-parameters: Idd per biascode, detectorwet, NTC, belasting | M | — | Parameters kiezen zodat de regelkringen convergeren; gevoeligheidsanalyse | Ja: Po en SWR via CI-V (`15 11`, `15 12`) bij ≤ 5 W op de dummy load |
| G13 | Error_Handler-adres en het gedrag bij een HAL-init-fout | M | `docs/hardware_init.md` | De hangdetector vindt het; daarna een breakpoint als "fatal"-orakel | Nee |
| G14 | Gebruik van CRC- en IDCODE-controles door de GUI-bibliotheek | M | `docs/mcu_identification.md` | Toegang loggen tijdens de GUI-init | Nee |
| G15 | USB OTG-registergedrag voor HAL_PCD_Init en MSC | M | `control_unit/docs/peripherals.md` | Pollinglussen detecteren; registers stap voor stap toevoegen | T0.7 |
| G16 | SDMMC: IDMA-coherentie, kaartvarianten | L | `control_unit/docs/memory_map.md` | Zonder cachemodel niet te simuleren; als niet-emuleerbaar risico documenteren | Nee |
| G17 | AT-antwoorden van de BT-module | L | `control_unit/docs/peripherals.md` | De firmware negeert de antwoorden (VERIFIED) | T0.10 |
| G18 | Timing op cycli | M | — | Niet te emuleren; alleen indicatief (§8.7) | Indirect |
| G19 | Gedrag van nieuwe vendor-releases | doorlopend | — | Ingest-workflow §7 | — |
| G20 | Interacties die de docs nog niet noemen | onbekend | — | Strikte modus plus de toegangsheatmap per release | — |
| G21 | De concrete waarden van de netwerkdefaults van stock Main | L | upstream-issue #1 (HYPOTHESIS/MEDIUM) | In de emulator meten welk IP stock in de CH394 schrijft | T0-P3 (ping/ARP) |
| G22 | Hoe de Main inschakelt (H1/H2) | **K** (R0) | §3.8 | PowerModel-varianten | T0-P1–T0-P4 |

### 5.2 Dynamische-analysemethoden (RE-kant)

1. **Logging van niet-gemodelleerde toegang** {VT, machine, PC, adres,
   breedte, waarde, R/W}, geaggregeerd tot een **toegangsheatmap** per
   release.
2. **Tags met bewuste resetwaarden**, elk met een reden en een bron.
3. **Read-before-write-detector** voor registers die gevoelig zijn voor
   de overdrachtstoestand (G1).
4. **Hang- en polldetector** (§5.3).
5. **Functiecoverage van stock**: een execution trace gemapt op de
   functiebereiken uit `*/analysis/memory/function_ranges.csv` en de
   indeling uit `*/analysis/libs/lib_regions.csv`; het percentage
   applicatiefuncties (Main 305, Control 850; `docs/libraries.md`) dat de
   baseline uitvoert.
6. **Differentiële heatmap tussen releases** (§7).
7. **Bevriezen en muteren** van één modelparameter om de gevoeligheid
   van de firmware te vinden.

Alle uitvoer van §5.2 is **materiaal van de RE-kant** en gaat nooit
naar de NF-ontwikkeling (§12).

### 5.3 Hang- en polldetector

**Criterium.** Een machine is "hangend" als (a) de PC ≥ 50 ms VT in een
venster van ≤ 64 bytes blijft, of (b) de superloop-IWDG-kick (Main
`0x08022A80`, Control `0x080220DE`, VERIFIED,
`analysis/peripherals/iwdg_kicks.csv`) langer dan T_kick (standaard
500 ms VT) na de boot-mijlpaal uitblijft.

**Rapport:** de PC-lus en de laatste 16 MMIO-reads in die lus; de call
stack (frame-pointer-heuristiek plus de functiebereiken); de suggestie
"statusbit X van register Y ontbreekt".

**Bekende eindlussen** zijn orakels, geen gaten: Default_Handler, de
HardFault-stop, Error_Handler (G13) en de shutdown-wacht op PH5.

---

## 6. Acceptatiecriteria: "de fabrieksfirmware draait perfect"

### 6.1 Algemeen

Een release-combinatie (Main vX + Control vY) voldoet als **alle**
criteria A1–A12 groen zijn in de deterministische rijstrook, met
profiel `clean` en B1-boot. A1 en A2 MOETEN daarnaast groen zijn in alle
boot-toestandsprofielen (§4.3). Tijden zijn in VT. "Baselinewaarde"
betekent: gemeten bij de eerste groene run van V1.0.1, daarna bevroren
met de genoemde tolerantie.

### 6.2 A1 — Boot tot de hoofdlus, zonder faults

| ID | Criterium | Meting | Drempel |
| --- | --- | --- | --- |
| A1.1 | Main bereikt de superloop | Eerste uitvoering van de kick op `0x08022A80`; daarna periodiek | Baselinewaarde + 10 %. Verwacht 3–8 s VT (HYPOTHESIS) |
| A1.2 | Ready-vlag van Main | Watch op TRX+0x22D (`main_unit/analysis/memory/trx_runtime_fields.csv`); alleen RE-kant | Gezet, binnen A1.1 + 1 s |
| A1.3 | Alle boot-stappen van Main gelogd in de gedocumenteerde volgorde | Een consoleparser (USART1) vergelijkt met `main_unit/docs/flow.md` stap 5b, op een geparafraseerde sleutellijst, niet op letterlijke strings | Volledig, in de juiste volgorde |
| A1.4 | Control bereikt de superloop | Kick op `0x080220DE` | Baselinewaarde + 10 % |
| A1.5 | Control: GT911-init geslaagd (TIM3 actief), FatFS gemount, eerste PCA9557-flush | Timerstart TIM3; I2C2-schrijfactie naar 0x19 | Alle drie; de flush ~3 s na de reset (VERIFIED) ± 0,5 s |
| A1.6 | Hoofdscherm zichtbaar | Framebuffer-hash na het stabiliseren | Gelijk aan de golden (§6.10) |
| A1.7 | Geen fault | Geen uitvoering van Default_Handler (Main `0x080245A4`, Control `0x08023600`), HardFault, NMI of Error_Handler | 0 |
| A1.8 | Geen hang | Hangdetector §5.3 | 0 meldingen |
| A1.9 | Strikte modus | Niet-gemodelleerde toegang | 0 buiten de bevroren allowlist |
| A1.10 | Gezondheid van FPGA en codec | Boot-bustest zonder mismatch-log; geen FPGA- of codec-underrun in 60 s | 0 |
| A1.11 | IWDG | In profiel `iwdg-hw` met T ≥ de baselinedrempel: geen reset | 0 resets |
| A1.12 | Netwerkdefaults | Het IP dat stock Main zonder `0x01` in de CH394 schrijft; ping-antwoord in het VLAN | Gelijk aan de bevroren baselinewaarde; vergelijken met upstream-melding #1 |

### 6.3 A2 — Linktiming en -integriteit

Meting: de LinkCable-tap plus een SLIP-decoder, met
`g7250-base/tools/g7250/slip.py` als referentieparser.

| ID | Criterium | Drempel |
| --- | --- | --- |
| A2.1 | `0x01`-periode over 120 s | Gemiddelde 20,0 ms ± 0,2 ms; p99 ≤ 21 ms, behalve bij de gedocumenteerde skips door het TX-lock (VERIFIED, `docs/protocol.md`) |
| A2.2 | `0x01`-inhoud tijdens het opstarten: nul-images, compiled defaults, dan de waarden uit `config.ini` | Volgorde aanwezig; de config-waarden binnen de baselinetijd |
| A2.3 | `0x03`-frames: rate, jitter, payload van 552 B | Rate = baselinewaarde ± 5 % (G5); 0 CRC-fouten; vlaggenwoord consistent met de plant |
| A2.4 | `0x06`-verzoek en -antwoord | ≤ 100 ms; 104 B; inhoud zichtbaar op de systeeminfopagina |
| A2.5 | `0x08` met een actieve Icom-LAN-client (eigen testscript) | Binnen 300 ms; resends ≤ 300 ms tot de ack in `0x01` byte `0x158`; seq 1–255, nooit 0 (VERIFIED) |
| A2.6 | Linkverlies: LinkCable 5 s onderbroken tijdens CI-V-PTT op Control | Main laat de PTT binnen 2–3 s vallen; herstel zonder handshake |
| A2.7 | Foutvrijheid over 1 h VT | 0 CRC-, lengte- of overrunfouten zonder injectie |
| A2.8 | Bezetting: byteduur 21,7 µs | `0x01` ≈ 9,3 ms per frame (430 B), dus C→M ≈ 47 % (afleiding, HIGH) |

### 6.4 A3 — Elke GUI-pagina bereikbaar

Met invoer-injectie **en** een screenshot-match; als RE-orakel MAG de
`selectUi`-byte gelezen worden (UI +0x920, `control_unit/docs/gui.md`).

| Scherm | Pad (`control_unit/docs/gui.md`, `analysis/peripherals/button_map.csv`) |
| --- | --- |
| 0 hoofdscherm | elk exitpad |
| 4 Menu 1 (2 pagina's × 15 items) | A0×B3; pagina 2 via een encoder |
| 5 Menu 2 (2 pagina's) | A1×B3 |
| 6 Menu 3 CW | A0×B4 op het hoofdscherm in CW-modus |
| 7 Systeem, subpagina's 1–7 | A2×B3; subpagina 7 (fabrieksreset): **openen, niet bevestigen** |
| 8 Geheugenkanalen plus het naamtoetsenbord | A0×B0 of touch |
| 9 Applicaties: lijst 0 en SWR-scanner 2 | A3×B1 |
| 10 Keyergeheugen | A3×B0 in CW/CWR |
| 11 Spraakgeheugen | A3×B0 in een spraakmodus |
| 12 Snelle instelling | hold A3×B2 |
| Overlays `windows` 1–3 | modusselectie, bandselectie, frequentie direct invoeren (ook H-22 0x28) |
| Pop-ups | NF/NR/NB-niveau, RIT/XIT, niveaubalk 3 s |

| ID | Criterium | Drempel |
| --- | --- | --- |
| A3.1 | Elke rij bereikt, daarna terug naar 0 | 100 % |
| A3.2 | Screenshot per pagina = golden | Pixel-exact in de deterministische rijstrook |
| A3.3 | Elke matrixcode (22) en elke encoder (8 plus de hoofdknop) heeft het gedocumenteerde effect | 100 % van `button_map.csv` en `encoder_map.csv` |
| A3.4 | Elke H-22-code uit `h22_keycodes.csv` geeft de gedocumenteerde actie | 100 % |

### 6.5 A4 — CI-V-dekking (Control, USART1)

| ID | Criterium | Drempel |
| --- | --- | --- |
| A4.1 | Elk commando uit `control_unit/analysis/protocol/civ_control.csv` (17 families) in lees- en, waar het kan, schrijfvorm | 100 %; het antwoord heeft de verwachte klasse (data, FB, FA, echo) |
| A4.2 | Schrijven en teruglezen consistent; de waarde verschijnt in het volgende `0x01`-image en op het scherm | 100 % van de schrijfbare velden |
| A4.3 | Elk adres wordt beantwoord; `19` echoot het aangeroepen adres | conform (VERIFIED, `docs/civ.md`) |
| A4.4 | Transceive: na een draai aan de hoofdknop een ongevraagd `00`-frame | ≤ 1 frame per wijziging |
| A4.5 | CI-V-PTT valt na 10 s zonder CI-V-verkeer | 10 s ± 0,1 s (VERIFIED) |
| A4.6 | BT-AT-verkeer en console op dezelfde lijn storen de CI-V-parse niet | 0 fouten over 10 000 commando's |
| A4.7 | Cross-check met de publieke CI-V-referentie rev. 1.2 uit het vendorpakket (§4.4) | Afwijkingen tussen gedocumenteerd en geobserveerd gedrag gerapporteerd (informatief, geen fail) |

### 6.6 A5 — Icom-LAN-sessies (wfview-compatibele modus van Main) en HDSDR-modus

Alle sessies worden door **eigen testscripts** gedreven, niet door
wfview.

| ID | Criterium | Drempel |
| --- | --- | --- |
| A5.1 | Handshake: are-you-there, I-am-here, ready, login, token, capabilities en conninfo, status, streaming | Volledig, elke stap ≤ 5 s VT |
| A5.2 | Login met foute credentials | Geweigerd |
| A5.3 | Keep-alive: pings op control en CI-V elke 100 ms, op audio elke 500 ms; idle om de 100 ms (VERIFIED, `main_unit/docs/network.md`) | ± 5 % |
| A5.4 | Audio radio → PC: 20 ms-ritme, chunks ≤ 1364 B, header volgens `wfview_packets.csv`, LPCM 16/8-bit, 48/16 kHz | conform |
| A5.5 | Audio PC → radio met PTT (`1C 00`) | TX-pad actief in de plant (dummy-belasting); TX-I/Q in de FPGA-sink |
| A5.6 | CI-V over LAN: alle 68 rijen van `main_unit/analysis/protocol/civ_main.csv`, inclusief de quirks | 100 % |
| A5.7 | Scope: `27 10/11/14/15/16/19` volgens `civ_scope.csv`; golfvormframes ≤ 20/s, 518 B, 475 punten | conform |
| A5.8 | Netwerkcontrole: `0x03`-vlag bit 7, het VFO-blok van `0x01` genegeerd, `0x08`-push | conform |
| A5.9 | Time-outs en herstel: 15 s stilte, de herstelladder (`main_unit/docs/network.md`) | conform |
| A5.10 | **Sessieverlies tijdens netwerk-PTT** (scenario van upstream-melding #2) | Het geobserveerde stockgedrag vastgelegd als baseline; een PTT die blijft hangen wordt als **bekende stockafwijking** geregistreerd (veiligheidsrelevant, §10.4 S3 voor de NF) |
| A5.11 | HDSDR-modus: discover, heartbeat, LO-set 0,5–108 MHz, I/Q-pakketten van 774 B, de pakketrate per span, drop na 10 s | Baselinewaarden (verwacht 250/s, HYPOTHESIS) |
| A5.12 | Live van modus wisselen: alle sockets dicht, netwerklaag herstart (VERIFIED) | conform |
| A5.13 | Zelfherstel van de link: PHY > 10 s weg geeft een cyclus (max. elke 30 s), na 2 mislukte cycli één harde reset (VERIFIED) | conform |

### 6.7 A6 — Persistentie van instellingen

| ID | Criterium | Drempel |
| --- | --- | --- |
| A6.1 | `config.ini` alleen bij een ordelijke shutdown geschreven (VERIFIED, `control_unit/docs/storage.md`) | 0 schrijfacties daarbuiten |
| A6.2 | Rondreis: wijzigingen via CI-V en GUI, shutdown, koude start, dezelfde waarden | 100 % van ≥ 40 velden |
| A6.3 | Stroomuitval zonder shutdown | Wijzigingen weg (stockgedrag, VERIFIED); geen crash |
| A6.4 | Bandstack, CW-berichten, geheugenkanalen | Opslaan, herladen, gelijk |
| A6.5 | Spraakgeheugen op SD (16-bit, 48 kHz, mono, ≤ 30 s) | Opnemen en afspelen, gelijk binnen marge |
| A6.6 | Fabrieksreset: volume 1 geformatteerd, de MCU gereset, de EEPROM van Main ongewijzigd (VERIFIED) | conform |
| A6.7 | Leeg NOR-image | Auto-format, defaults, geen crash |

### 6.8 A7/A8 — Bandwissels en kalibratieblok

| ID | Criterium | Drempel |
| --- | --- | --- |
| A7.1 | Het bitpatroon van keten A en B voor een frequentieraster (alle randen ± 1 kHz) = de documenttabel | 100 %; afwijkingen alleen bij MEDIUM-randen, gedocumenteerd |
| A7.2 | De PRE/ATT-selectoren volgen de VFO-bytes (VERIFIED) | 100 % |
| A7.3 | De TX- en RX-volgorde = `main_unit/docs/flow.md` | conform |
| A7.4 | TX-bandhandhaving (veiligheidsorakel; alleen beperkend): buiten de ingeschakelde banden geen bias en geen T/R-lijnen (VERIFIED) | conform |
| A7.5 | ATU-tune met de belastingmodellen "afstembaar" en "onmogelijk" (`docs/atu.md`) | conform |
| A8.1 | Geldig kalibratieblok: geladen, de trim convergeert | conform |
| A8.2 | Ongeldige CRC of layout-id: defaults meteen teruggeschreven (VERIFIED) | conform |
| A8.3 | Bias buiten bereik: trim, dirty, opgeslagen bij de shutdown (VERIFIED) | conform |
| A8.4 | `0x02`-verzoek uit een "fabriekstool" in de emulator (RE-kant): antwoord 358 B | conform |
| A8.5 | `0x02`-set: alleen de RAM-kopie (VERIFIED) | conform |
| A8.6 | NVPARAM-marker bij elke geldige boot herschreven (VERIFIED) | conform |

### 6.9 A9–A11 — Overige functies

| ID | Criterium |
| --- | --- |
| A9.1 | Uitschakelsequentie volgens §3.6 |
| A9.2 | SWR-scanner: 51 punten, dwell 500 en 100 ms, 5 W NFM, sleutel via `0x15E` bit 6 (VERIFIED, `control_unit/docs/flow.md`); alleen op de dummy-belasting |
| A9.3 | CW: dot = 1200/WPM ms; trainermodus zonder bias en T/R; zijtoon op de codec |
| A9.4 | CW-geheugen vanuit Control (PE3/PE4) geeft CW aan de Main-zijde (`wiring:hypothesis`) |
| A9.5 | RX-audio end-to-end: een draaggolf op f_VFO + 700 Hz in USB geeft 700 Hz ± 2 Hz aan de Main-codecuitgang; de S-meter monotoon met het niveau |
| A10.1 | Bluetooth aan en uit: de AT-sequentie met 3 s time-out en 5 herhalingen; PCA9557-bit 4 |
| A11.1 | Soak 1 h VT (nightly) en 24 h VT (wekelijks); 0 faults, 0 hangs, geen heapgroei |

### 6.10 A12 — Golden traces en screenshots

Een golden trace is een gecanonicaliseerde JSONL-gebeurtenisstroom per
scenario (`t_vt_ns`, `machine`, `bron`, `soort`, `data`), met
link-frames, UART-tekst, datagrammen, GPIO-flanken, latchwaarden,
DAC-schrijfacties, I2C-transacties, framebuffer-hashes en
plant-gebeurtenissen.

| ID | Criterium | Drempel |
| --- | --- | --- |
| A12.1 | Determinisme: drie runs met hetzelfde manifest | Identieke trace- en screenshot-hashes |
| A12.2 | Replay van een opgenomen live-sessie | Dezelfde uitvoer voor de door de firmware bepaalde delen |
| A12.3 | Golden-vergelijking | Trace = golden, met tolerantievensters |
| A12.4 | Screenshotset: ≥ 1 per pagina uit A3 plus de kernscenario's | Pixel-exact |

Golden traces en screenshots zijn **afgeleid van stock** en dus privé
(§12); de publieke repo bevat alleen de scenariodefinities en de hashes.

---

## 7. Het vendor-releaseproces

### 7.1 Workflow

| Stap | Actie | Uitvoer | Wie of wat |
| --- | --- | --- | --- |
| R0 Herkomst | De gebruiker bewaart het officiële vendorpakket in de lokale imagemap. De emulatortooling hasht het pakket en de bestanden erin (zonder ze te openen of te parseren) en noteert ze als `provenance` | Manifestregel herkomst: bron-URL, datum, bestandsnamen, groottes, SHA-256 | tooling (automatisch) |
| R1 Aanlevering | De gebruiker levert de **ontsleutelde** applicatie-images van de nieuwe release aan in de imagemap en bevestigt hun SHA-256 | Manifestregel: release, unit, `image_sha256`, grootte, vectoren | gebruiker + tooling |
| R2 Controle | Hashcontrole tegen het manifest en de structurele controle (§4.2); bij een mismatch stopt de ingest met een duidelijke melding | OK of weigering | emulator |
| R3 Rooktest | Boot per unit in de strikte modus, profiel `clean`, solo en gekoppeld met de vorige release van de andere unit | Boot-OK of hangrapport; nieuwe heatmap | CI (privé-runner) |
| R4 Baseline-suite | A1–A12 volledig | Resultaat per criterium | CI |
| R5 Gedragsdiff | Diff tegen de vorige release: heatmap, link-frames, CI-V- en LAN-antwoorden, screenshots, consolesleutellijst, en (RE-kant) functiebereiken via de `g7250-base`-tooling; de release notes uit het vendorpakket als context | Diff-rapport (privé) | CI + RE |
| R6 Triage | Elke afwijking: **E** emulatorgat, **G** echte gedragswijziging, **R** regressie in de vendor-firmware | Triage-tabel | RE |
| R7 Modellen evolueren | Klasse E: model aanpassen; **alle releases in de matrix moeten blijven slagen**; release-afhankelijk gedrag alleen via een hardwareprofiel | Modelcommit plus regressierun | ontwikkelaar |
| R8 Golden bijwerken | Klasse G: golden vastleggen met review en motivatie | Nieuwe golden-set (privé) | review |
| R9 Docs terugkoppelen | Bevindingen naar `g7250-base`, volgens het eigen proces van die repo | Issue of PR, pas na een expliciete go van de eigenaar | RE |
| R10 Taggen | Emulatorrelease `emu-<semver>`; matrixregel "perfect" | Tag, matrix | release |

De emulator ontsleutelt in geen enkele stap iets. Levert de gebruiker
geen ontsleutelde images aan, dan blijft de release in de matrix op
"herkomst bekend, niet getest".

### 7.2 Versiematrix

`matrix/version_matrix.yaml` (publiek, alleen hashes en status):

| Kolom | Inhoud |
| --- | --- |
| `vendor_release` | bijv. `M1.0.1/C1.0.1` |
| `provenance` | pakketnaam, bron, datum, SHA-256 van pakket en vendorbestanden (§4.4) |
| `image_sha256` | per unit, door de gebruiker aangeleverd |
| `fpga_version_reported` | uit de `0x06`-slave-info (in V1.0.1 een gecompileerde string, VERIFIED) |
| `emu_version_min` | de eerste emulatorrelease waarop dit "perfect" is |
| `models` | modelversies |
| `profiles_green` | de boot-toestandsprofielen die groen zijn |
| `criteria` | A1…A12: groen, rood of n.v.t. |
| `cross_pairs` | combinaties met andere releases van de andere unit, met hun status |
| `known_deviations` | gedocumenteerde stockquirks, inclusief de upstream-meldingen #1/#2 zodra bevestigd of weerlegd |
| `golden_set_id` | verwijzing naar de privé golden-set |

**Versiebeleid van de emulator:** *major* bij een incompatibele
harnas-wijziging, *minor* bij een nieuwe vendor-release of een nieuw
model, *patch* bij modelcorrecties zonder golden-wijziging.

---

## 8. Testinfrastructuur

### 8.1 Lagen

| Laag | Doel | Doelwit | Typische duur | Rijstrook |
| --- | --- | --- | --- | --- |
| L0 Statisch | lint, typecheck, CSV-schema, image- en geheimscan, clean-room-scan (§12.2) | repo | < 2 min | — |
| L1 Unittests van de modellen | Elk C#- en Python-model los, tegen de datasheet- en docs-semantiek | modellen | < 5 min | host |
| L2 Emulator-integratie | Kleine **eigen** testfirmwares (clean-room) die één peripheral oefenen: UART-echo, SPI-latch-patroon, I2C-scan, FPGA-busprotocol, LTDC-testbeeld, PowerModel | emulator | < 15 min | det. |
| L3 Baseline-regressie | A1–A12 op stock (alle releases in de matrix) | stock (SS) | 30 min tot 6 h | det. |
| L4a Conformance NF-Main (kritiek pad) | P1, TCI, optioneel CI-V over het netwerk, headless werking, voedingsmodi (PW-2–PW-8) | NF-Main (EH) | 30–60 min | det. |
| L4b Robuustheid ES (lage prioriteit) | S-ES1–S-ES3 (§8.3.6) | NF-Main + stock Control | 15–30 min | det. |
| L4c Conformance eigen paneel (optionele track) | De NF-link met versie-onderhandeling, de NF-Control | NF-Main + NF-Control (EE) | 30–90 min | det. |
| L5 Property, fuzz en fault | Invarianten, fuzzing van parsers, fault-injectie | NF (stock alleen als referentie) | nightly en wekelijks | det. |
| L6 Prestaties en timing | Budgetten (§8.7) | NF (+ stock als referentie) | nightly | det. |
| L7 HIL | §11 | echte radio | op aanvraag, met gates | bank |

### 8.2 L1 — Unittests van de modellen (voorbeelden)

- **CH394:** de registersemantiek (RO, W1C, auto-clear van Sn_CTRL), de
  pool-indeling, de RX-header van 8 B, het negeren van toegang in het
  resetvenster, de TCP-toestandsmachine, WOL en het MP-bit,
  PHY-power-down.
- **FPGA:** de busdecodering bij willekeurige MODER-wisselingen; de
  NCO-vouwing en inversie (eigenschapstest woord → frequentie → woord);
  samples per DRDY per rate.
- **BU2506FV:** de bitvolgorde volgens de datasheet.
- **GT911:** de adreskeuze per INT-niveau; de checksum.
- **H-22-generator:** de inverse van de gedocumenteerde decoder.
- **SLIP/CRC:** kruistest met `g7250-base/tools/g7250/slip.py` en de
  bestaande tests in `tools/g7250/tests` (alleen voor de baseline).
- **PowerModel:** H1- en H2-toestandsdiagram, de PH5-varianten.
- **Plant:** monotonie, convergentie van de bias-trim, en de orakels (een
  opzettelijk foute T/R-volgorde moet een melding geven).
- **Image-controle:** weigering bij een hashmismatch, bij een map binnen
  een git-repo, bij een ongeldige vectortabel.

### 8.3 L4 — Conformance van de nieuwe firmware

**Volgorde.** Op het kritieke pad liggen §8.3.2 (P1), §8.3.3 (TCI),
§8.3.4 (CI-V over het netwerk, optioneel) en de voedingsmodi (§3.8.6),
in config EH. §8.3.6 (ES) heeft een lage prioriteit. §8.3.1 en §8.3.5
horen bij de optionele, latere track van een eigen paneel (EE).

#### 8.3.1 Eigen inter-unit-link (NF-link, config EE — optionele track)

De NF-link is een **eigen ontwerp** tussen NF-Main en NF-Control; geen
stock-SLIP en geen compatibiliteitseis met stock. De specificatie hoort
bij het firmwareproject. Het fysieke kanaal ligt vast door de hardware
(USART2 op PD5/PD6, HIS); baudrate en framing kiest het
firmwareproject.

| ID | Eis aan de NF-link (generiek, te verfijnen met de NF-linkspec) | Orakel |
| --- | --- | --- |
| C-L1 | Framing met integriteitscontrole en een expliciete lengte; een **protocolversie** en een **capability-onderhandeling** bij de start en na elk linkherstel | LinkCable-tap plus een referentiedecoder uit de NF-linkspec |
| C-L2 | Toestandssynchronisatie binnen T_sync (doel ≤ 500 ms) na de start en na elk herstel | Vergelijking via de externe interfaces en het NF-scherm |
| C-L3 | Gedefinieerde eigenaar per parameter (paneel, netwerkhost); geen tegenstrijdige toestand | Concurrency-scenario's (paneel en P1 of TCI tegelijk) |
| C-L4 | Meter- en spectrumstroom Main → Control met minimumrate en begrensde latentie | Tap; het NF-scherm |
| C-L5 | Linkverlies: de lokale PTT- en key-bronnen vallen binnen ≤ 3 s | LinkCable-onderbreking |
| C-L6 | Herstel zonder handmatige actie, ≤ 1 s na het herstel van de link | Fault-matrix §8.5 |
| C-L7 | Ordelijk uitschakelen: Control slaat zijn staat op vóór de Main de voeding vrijgeeft | NOR-trace en volgorde |
| C-L8 | Bezetting ≤ 70 % van de byte-tijd in elke richting | Tap-statistiek |
| C-L9 | Robuust tegen alle link-faults en fuzzing | Geen crash of hang |
| C-L10 | **Gracieuze degradatie tussen verschillende versies.** De versies van NF-Main en NF-Control hoeven niet gelijk te zijn; na de onderhandeling alleen de gemeenschappelijke capabilities; onbekende capabilities of berichtsoorten genegeerd; ontbrekende functies op het paneel als niet beschikbaar getoond; de TX-veiligheid hangt nooit af van een capability van het paneel | Een versiematrix N−2…N+1 tegen N−2…N+1 met in- en uitgeschakelde capabilities |
| C-L11 | Onderhandeling mislukt | Beide units werken zelfstandig verder (NF-Main zoals in EH); geen TX op basis van paneelbronnen |

#### 8.3.2 OpenHPSDR Protocol 1, "G7250-P1"-profiel

Bron: de publieke P1-documentatie (Metis "How it works", USB protocol
V1.58, de Hermes-Lite 2-wiki; verwijzingen in
`docs/hpsdr_gap_analysis.md`).

**Board-id.** Een nieuw, eigen board-id; een waarde die in de bekende
host-apps niet in gebruik is, gecoördineerd met hun maintainers
(HYPOTHESIS dat er een vrije waarde is). Het profiel definieert de
vermogens-, SWR-, spannings-, stroom- en temperatuurtelemetrie, de
bediening van ATU en antennepoorten (C&C-adressen buiten het
HL2-bereik of een gedocumenteerde extensie), de PA-informatie (100 W,
cap) en de voedingsmodus (P-10).

| ID | Eis | Test |
| --- | --- | --- |
| C-P1 | Discovery op UDP 1024 (`EF FE 02`); antwoord met status, MAC, codeversie, board-id | Referentie-host plus negatieve gevallen |
| C-P2 | Start/stop (`EF FE 04`) | Toestandsdiagram |
| C-P3 | EP6: 1032-B datagrammen, 2 × 512-B frames, sync `7F7F7F`, C0–C4, 63 × (I24, Q24, mic16) per frame; sequentienummers zonder gaten | Pakketvalidator; geen gaten over 10 min VT bij 48 en 96 kHz |
| C-P4 | Sample rates 48 en 96 kHz verplicht; 192 kHz optioneel (SPI-budget, `docs/hpsdr_gap_analysis.md` §2.4); 384 kHz netjes geweigerd | Rate in VT ± 0,01 % |
| C-P5 | EP2: L/R-audio naar de codec, TX-I/Q, MOX | TX-I/Q in de FPGA-sink; L/R in de codec-sink |
| C-P6 | RX-frequentie, TX-frequentie, preamp, attenuator, antenne | NCO-woord, latchtoestand; in EE ook het NF-paneel |
| C-P7 | Drive en vermogen | Vermogen ≤ min(drive-mapping, cap) (plant) |
| C-P8 | **Host-watchdog**: TX uit als er geen C&C of EP2 meer komt | TX uit binnen T_wd (eis ≤ 1 s, doel ≤ 250 ms) |
| C-P9 | Status: PTT, dot/dash, ADC-overload, fwd/rev, Vext, Idd, temp | Consistent met de plant |
| C-P10 | Headless werking (EH, primair); in de track EE samenleving met het NF-paneel | EH: alle C-P-tests zonder Control-machine |
| C-P11 | Interoperabiliteit met echte host-software | Opgenomen sessies van AetherSDR en andere SDR-hosts slagen als replay in de deterministische rijstrook |

#### 8.3.3 TCI

Bron: de publieke TCI-specificatie van ExpertSDR (WebSocket,
tekstcommando's en binaire I/Q- en audiostreams). TCI loopt over
**TCP**, dus het CH394-model MOET TCP ondersteunen (HIGH); stock
gebruikt geen TCP.

| ID | Eis | Test |
| --- | --- | --- |
| C-T1 | WebSocket-handshake; het device- en protocolbericht bij het verbinden | Referentieclient |
| C-T2 | Kerncommando's: VFO, modus, TX-enable en TRX, drive, tune, split, RIT/XIT, filterbanden | 100 % van het G7250-TCI-profiel; niet-ondersteunde commando's netjes geweigerd |
| C-T3 | Binaire streams op de afgesproken rate | Rate- en framevalidator |
| C-T4 | Watchdog: verbinding weg of geen ping, dan TX uit ≤ T_wd | Fault |
| C-T5 | Gelijktijdigheid met P1 (indien toegestaan) | Geen dubbele eigenaar van TX |
| C-T6 | Doorvoerbudget over SPI6 en CH394 met TCP-overhead | §8.7 |

#### 8.3.4 CI-V (NF)

Op het kritieke pad (EH) is er geen seriële CI-V; de NF-Main MAG CI-V
over het netwerk aanbieden. In de track EE MAG de NF-Control de seriële
route implementeren (in de code van stock is dat Control USART1; de
echte USB-CAT-route bevestigt HIL, H0). Conformance: een
commandoprofiel als tabel, antwoordklassen volgens de Icom-conventie,
adressering, transceive, een PTT-time-out, robuustheid tegen gemengd
verkeer.

**Bronnen:** de **publieke CI-V-referentie rev. 1.2** uit het
vendorpakket (§4.4) is een legitieme clean-room bron voor het
commandoprofiel. Waar de NF voor externe clients hetzelfde gedrag als
stock wil bieden, MAG ze de black-box-resultaten van A4/A5 gebruiken
(antwoorden zoals een client ze ziet, geen interne staat).

#### 8.3.5 NF-Control (frontpaneel, config EE — optionele track)

Een eigen frontpaneel-firmware op de Control-hardware, met een eigen
GUI-bibliotheek (STemWin valt onder de ST-licentie,
`control_unit/docs/gui.md`).

| ID | Eis | Orakel |
| --- | --- | --- |
| C-C1 | Boot tot een werkend hoofdscherm zonder fault of hang, in elk boot-toestandsprofiel | A1-achtige criteria |
| C-C2 | Elke invoer heeft een gedocumenteerd effect volgens de NF-paneelspec | Invoer-injectie plus screenshots (golden per NF-build) |
| C-C3 | Elke NF-pagina bereikbaar en terug | Paginalijst uit de NF-spec |
| C-C4 | Persistentie; ordelijk uitschakelen; stroomuitval zonder blokkerende corruptie | NOR- en SD-traces |
| C-C5 | Audio-routing via de codec en de CTRL-kabel volgens de HIS | Codec-sinks en -bronnen |
| C-C6 | Invoer tot schermupdate ≤ 100 ms (doel) | Trace |
| C-C7 | VSYNC-gesynchroniseerde bufferwissel | Framebuffer-capture |

#### 8.3.6 Robuustheid en veiligheid met een aangesloten stock-paneel (ES, lage prioriteit)

Geen compatibiliteitstest en geen doelconfiguratie.

| ID | Eis aan de NF-Main | Orakel |
| --- | --- | --- |
| C-S1 | Het linkverkeer van het stock-paneel is onbekende bytes en wordt robuust genegeerd (S-ES1) | 1 h VT met een draaiend stock-paneel plus gemuteerde frames: geen crash, hang of fault, geen toestandswijziging, geen TX |
| C-S2 | Paneellijnen genegeerd tenzij expliciet ingeschakeld (S-ES2) | Elke lijn activeren via het CTRL-kabelmodel: standaard geen TX, keying, uitschakeling of audio naar de modulator |
| C-S3 | Niets naar het paneel dat zijn persistente staat kan wijzigen (S-ES3) | NOR, SD en backupdomein bytegelijk; de stock-decoder ziet 0 geldige frames van de NF-Main |
| C-S4 | In- en uitschakelen met een aangesloten paneel | Geen ongedefinieerde toestand; het paneel krijgt geen shutdown-signaal |

### 8.4 L5 — Property-tests en fuzzing

| Doel | Methode | Orakel |
| --- | --- | --- |
| Onbekende bytes op de link-UART (ES) | Het verkeer van een draaiend stock-paneel als corpus, plus willekeurige bytes en bursts | Geen crash, hang of toestandswijziging; geen TX |
| Framedecoder van de NF-link (track EE) | Grammatica-gebaseerde fuzzing; ook als host-fuzzer | Geen crash, hang of out-of-bounds (sanitizers op de host-build) |
| CI-V-parser | Willekeurige adressen, ontbrekende FD, ingebedde FE FE, overlange payloads | idem, plus "geen ongewenste TX" |
| P1-pakketten | Mutaties van C&C, verkeerde sequenties, gemengde lengtes | idem, plus de C-P8-watchdog blijft werken |
| TCI-tekst en WebSocket-frames | Fuzzing van de framing en de syntaxis | idem |
| Wake- en beheerpakketten | Gemuteerde wake-commando's en magic packets | Geen onbedoelde wake buiten de regels; nooit TX |
| Eigenschappen | "Nooit RF-drive als T/R in RX staat"; "TX-frequentie ∈ allowlist"; "vermogen ≤ cap"; "geen TX in slaap"; "netwerk-TX valt binnen T_wd na sessieverlies" | Plant-orakels; temporele eigenschappen op de trace |

### 8.5 L5 — Fault-injectie

| Categorie | Injecties | Verwacht gedrag (NF: eis; stock: baseline-documentatie) |
| --- | --- | --- |
| Link | bitfouten (BER 10⁻⁶ tot 10⁻³), byteverlies, burstruis, afgekapte frames, CRC-fouten, verkeerde baudrate, kabel los 0,1–30 s, een stilgevallen peer | NF: geen crash, PTT-bronnen ≤ 3 s weg. Stock: CRC-logs, re-arm na ~200 ms (Main) of ~2 s (Control) (HIGH) |
| Stroom | DC weg op een willekeurig VT-moment, met nadruk op EEPROM-paginaschrijfacties, het herschrijven van `config.ini`, SD-schrijven, (NF) eigen schrijfacties, slaap- en wake-overgangen | Geen corrupte persistente staat die de boot blokkeert. Stock: een NOR zonder geldig bestandssysteem wordt automatisch geformatteerd (VERIFIED) |
| Netwerk | Pakketverlies, herordening, duplicatie, jitter, PHY-link weg en terug, CH394 SEND hangt, INT# blijft hangen, de harde reset faalt, **sessieverlies tijdens netwerk-PTT** | NF: sessies hervatten, TX-watchdog grijpt in. Stock: de herstelladder (A5.9, A5.13); het PTT-gedrag bij sessieverlies vastgelegd (A5.10) |
| Stille host | P1-host, TCI-client of CI-V-host valt stil tijdens MOX | TX uit binnen T_wd (C-P8, C-T4) |
| Plant | hoge SWR, overtemperatuur, Vext 10,5 en 15,5 V, Idd-runaway, FPGA stuck sample, underrun, ADC-overload | NF: de veiligheidsgates (§10.4). Stock: alleen logs en fan, geen TX-inhibit (VERIFIED, `main_unit/docs/flow.md`) |
| Peripherals | I2C-NACK of -hang, SPI-flash WIP blijft hangen, SD verwijderd tijdens schrijven, BT-module zwijgt | Geen hang van de superloop |
| Klok en tijd | DRDY-rate ± 10 %, DRDY valt weg, I2S-klok valt weg | Underrun-detectie, geen crash |
| Voeding | PH5 laag getrokken zonder paneel, PH9-verlies (H1), DC-dips | Stock: de valkuil reproduceerbaar (PW-1). NF: P-1, P-2 |

### 8.6 Determinisme, record en replay

- **De invoerwachtrij** bevat elke externe stimulus als {VT, doel, data}
  (UART-RX, UDP of TCP in, invoerevents, plant- en PowerModel-parameters,
  fault-acties). In de deterministische rijstrook komt ze uit het
  testscript, in de live rijstrook uit de host met een VT-stempel.
- **Een recording** = het run-manifest plus de invoerwachtrij. Replay
  onder hetzelfde manifest MOET bit-identieke traces opleveren.
- **Snapshots** per release ("geboot en idle"), alleen geldig onder
  hetzelfde manifest (gecontroleerd met een hash).
- **Seeds:** één globale seed; elke model-RNG een afgeleide seed per
  naam.
- **Verboden in de deterministische rijstrook:** wandkloktijd,
  host-sockets en ongeseede randomness (gedetecteerd via
  harnas-wrappers).

### 8.7 L6 — Prestaties en timingbudgetten

De emulator meet *functionele* timing; budgetten zijn marges in VT, op
HIL bevestigd waar dat kan.

| Budget | Definitie | Doel voor de NF | Opmerking |
| --- | --- | --- | --- |
| CH394-doorvoer | Netto payload per s, gemodelleerd met de SPI6-bytetiming (17,19 Mbit/s raw) en de toegangsoverhead | P1 48 kHz: ≥ 6,3 Mbit/s EP6+EP2 met ≥ 30 % marge; 96 kHz: 9,4 Mbit/s met ≥ 15 % marge | `docs/hpsdr_gap_analysis.md` §2.4 (afleiding, HIGH). De echte CH394-limiet is onbekend (Q4); de publieke handleiding noemt tot 62 MHz SPI (HIGH) |
| Bezetting van de SPI6-bus | Fractie van de VT dat CS actief is | ≤ 80 % | — |
| IRQ-rates | Per bron | Gedocumenteerd en stabiel | Stock-referentie: TIM5 en TIM17 20 kHz, TIM7 1 kHz, TIM6 100 Hz, SysTick 1 kHz, EXTI10 ~48 kHz (HYPOTHESIS), I²S-DMA 250 Hz |
| ISR-latentie en deadline | In VT-instructies | Elke ISR met een deadline (FPGA-DRDY 20,8 µs) ≤ 50 % | Alleen indicatief |
| CPU-load | Fractie niet-idle instructies | ≤ 70 % gemiddeld, ≤ 85 % piek, bij P1 96 kHz plus TX | MIPS-factor per core; stock-loadmeter als referentie |
| Linkbezetting | Fractie van de byte-tijd op USART2 | ≤ 70 % (track EE) | `0x03` ≈ 12,1 ms per frame bij 557 B (afleiding) |
| Bootduur | Van DC-aan tot operationeel | ≤ stock-baseline + 20 % | — |
| Wake-latentie | Van wake-pakket tot operationeel | Doel ≤ 3 s | Nieuw in v0.4 |
| PTT-latentie | Van MOX tot RF in de plant | ≤ 20 ms (doel), ≤ 50 ms (eis) | Stock: arbiter op 10 ms plus 200 nul-samples (VERIFIED) |

**Snelheid van de emulator** (CI-budget): doel ≥ 0,25× realtime voor de
gekoppelde emulatie bij rate-index 3 zonder netwerkstreams, ≥ 0,1× bij
P1 96 kHz (HYPOTHESIS, te meten in M1).

### 8.8 CI-orkestratie

| Pijplijn | Trigger | Inhoud | Runner |
| --- | --- | --- | --- |
| `fast` | elke push | L0, L1, L2 | publiek mag (geen stock nodig) |
| `pr` | PR | `fast` + L3-subset + L4a-kern | **privé** (de lokale imagemap is nodig) |
| `nightly` | dagelijks | Volledige L3, L4a, L4b, L5 (1 h fuzz, fault-matrix), L6, soak 1 h VT | privé |
| `weekly` | wekelijks | L3 over de hele versiematrix, soak 24 h VT, uitgebreide fuzzcampagnes, alle boot-toestandsprofielen, L4c (track EE) | privé |
| `release-gate` | handmatig | Alles plus de gate-evaluatie (§9, §10) | privé |
| `vendor-ingest` | nieuwe bestanden in de imagemap | R0–R5 (§7) | privé |

Een privé-runner leest de images uitsluitend uit zijn eigen lokale
imagemap (configuratie-instelling), heeft geen uitgaand netwerk tijdens
tests, en bevat geen sleutel of ontsleutelingstool. NF-tests die geen
stock-image nodig hebben (L4a, EH) MOGEN op publieke runners draaien.

### 8.9 Artefacten

| Artefact | Formaat | Zichtbaarheid |
| --- | --- | --- |
| Run-manifest | JSON | publiek (alleen hashes) |
| Testresultaten | JUnit-XML plus JSON | publiek voor de NF; privé voor stock |
| Traces | JSONL.zst plus hash | privé (stock), publiek mag (NF) |
| Link-captures | binair plus gedecodeerd | idem |
| Netwerkcaptures | pcapng, met de dissectors uit `g7250-base/tools/wireshark` | idem |
| Screenshots | PNG plus hash | privé (stock), publiek mag (NF-GUI) |
| Audio | WAV (codec- en FPGA-sinks) | idem |
| Coverage | lcov/HTML (NF via DWARF); functiecoverage van stock (privé) | — |
| Kwaliteitsrapport | JSON plus HTML/Markdown | publiek voor de NF |
| Recordings en snapshots | binair plus manifest | privé |
| Heatmaps en diff-rapporten | JSON/HTML | privé (RE-kant) |

---

## 9. Kwaliteitsmetrieken en score

### 9.1 Metrieken

| Code | Metriek | Berekening | Bron |
| --- | --- | --- | --- |
| Q-CONF | Conformance | Per suite. Kritiek pad: P1, TCI, EH (inclusief de voedingsmodi) en optioneel CI-V over het netwerk; lage prioriteit: ES; optionele track: NF-link en NF-Control. Σ(gewicht × geslaagd) / Σ gewicht, gewichten kritiek 5, belangrijk 3, normaal 1 | L4 |
| Q-SAFE | Veiligheidsinvarianten | Aantal overtredingen (plant-orakels, watchdogs, caps, geen TX in slaap) | L4–L6, fault |
| Q-COV | Codecoverage van de NF | Lijn- en branchcoverage uit de execution trace plus DWARF | alle lagen |
| Q-REQ | Requirement-dekking | Fractie NF-requirements met ≥ 1 geslaagde test | traceerbaarheidsmatrix |
| Q-TIME | Timingmarge | min over de budgetten van (1 − gemeten/limiet) | L6 |
| Q-FAULT | Fault-herstel | Fractie fault-scenario's met het verwachte herstel | L5 |
| Q-FUZZ | Fuzzrobuustheid | Unieke crashes of hangs (moet 0 zijn) | L5 |
| Q-STAB | Stabiliteit | Soak-uren zonder fault, inclusief slaap- en wakecycli | L3/L6 |
| Q-RES | Resources | Flash, RAM, stackdiepte, heap-watermerk | build + L6 |
| Q-STAT | Statische kwaliteit | Compilerwaarschuwingen (= 0), nieuwe bevindingen van statische analyse | L0 |
| Q-DET | Determinisme | Identieke hashes over 3 runs | L3/L4 |
| Q-TWIN | Twin-getrouwheid (HIL) | Overeenkomst tussen emulator- en HIL-uitkomsten op black-box-observabelen | L7 |

### 9.2 Score en oordeel

**Harde poorten** (elk blokkerend): Q-SAFE = 0; Q-FUZZ = 0; Q-DET =
identiek; alle kritieke conformance-items geslaagd; de statische
brick-controles (§10.1) geslaagd.

**Gewogen score** (0–100), alleen als alle harde poorten groen zijn:

```
score = 30·Q-CONF + 15·Q-REQ + 15·min(Q-COV_branch/0,80, 1) + 15·Q-FAULT
      + 10·clamp(Q-TIME/0,30, 0, 1) + 5·Q-STAB_norm + 5·Q-RES_norm + 5·Q-STAT_norm
```

`Q-STAB_norm` = min(soakuren / 24, 1); `Q-RES_norm` = 1 bij flash ≤ 85 %,
RAM ≤ 80 % en stack-marge ≥ 25 %, anders lineair naar 0;
`Q-STAT_norm` = 1 − min(nieuwe bevindingen / 20, 1).

| Oordeel | Voorwaarde | Wat het toestaat |
| --- | --- | --- |
| **ROOD** | Een harde poort gefaald | niets |
| **ORANJE** | Harde poorten groen, score < 75 | verder ontwikkelen in de emulator |
| **GROEN-EMU** | score ≥ 75; Q-CONF(P1) = 100 % kritieke items; Q-CONF(TCI) ≥ 95 %; Q-CONF(EH) = 100 % inclusief PW-5/PW-6; ES-items C-S2/C-S3 = 100 %; Q-FAULT ≥ 90 %; Q-TIME ≥ 0,2; terugrol-compatibiliteit van Main = 100 %. Track EE daarnaast: Q-CONF(NF-link) = 100 %, Q-CONF(NF-Control) ≥ 95 % | overdracht aan het firmwareproject (gate E4) |
| **GROEN-HIL** | GROEN-EMU + score ≥ 85 + twin-validatie van stock geslaagd + F0–F2 vervuld (F3 alleen voor de track EE) | eerste flash van de NF-Main op de echte radio (RX-only build) |
| **RELEASE** | GROEN-HIL + de HIL-suite op de echte radio geslaagd in alle TX-stappen + 24 h soak (emulator) + review | publiceren van de NF |

### 9.3 Rapport

Per build één rapport (JSON plus HTML): samenvatting en oordeel, harde
poorten, de score met bijdragen, de trend, gefaalde tests met links naar
de artefacten, de traceerbaarheidsmatrix, de timingbudgetten, de
veiligheidsorakels per invariant, en het bekende-afwijkingsregister.
Het rapport is de enige vorm waarin resultaten naar het NF-team gaan
(§12.2).

---

## 10. Brick-risico minimaliseren

De emulator kan het brick-risico niet wegnemen, wel verkleinen. Hij
dwingt af wat aan de firmwarekant toetsbaar is: geen schrijfacties naar
sector 0 of de option bytes, een terugrol-compatibele persistente staat,
veilige defaults en TX-veiligheid. Hoe een image op de radio komt, en
het herstel via de vendorprocedure, zijn afhankelijkheden van het
firmwareproject (§10.3, §15).

**Risicoprofiel per track.**
- **Kritiek pad (alleen NF-Main):** alleen de Main krijgt een NF-image;
  de Control blijft stock. Het herstelpad moet bewezen zijn voor de
  Main. De stock Control mag door de NF-Main niet beschadigd worden
  (S-ES3, E-B2).
- **Optionele track EE:** twee units geflasht, met een hoger
  brick-risico; het herstelpad moet dan voor beide units bewezen zijn.
  Verschillende NF-versies op Main en Control zijn toegestaan; de
  NF-link onderhandelt (C-L10).

### 10.1 Grondregels (normatief voor de NF en haar tooling)

1. **Sector 0 en de option bytes zijn heilig, op elke MCU met een
   NF-image.** De NF MOET NIET in sector 0 (`0x08000000`–`0x0801FFFF`)
   schrijven of wissen, en MOET NIET option bytes wijzigen (RDP,
   BOOT_ADD, WRP, BOR, IWDG-bits, CPUFREQ_BOOST). Reden: de
   vendor-bootloaders zijn naar huidige kennis het herstelpad; de
   eigenaar opent de radio niet, dus SWD-herstel bestaat niet; de
   updatelogica zit volgens de docs volledig in de bootloaders (HIGH,
   `main_unit/docs/peripherals.md`).
   - **Dynamische check in de emulator:** het FLASH-model meldt elke
     unlock-poging en elke schrijf- of wisactie op sector 0 of de
     option bytes als een harde fout.
2. **Geen flashprogrammering in de app.** Stock bevat geen flash- of
   option-byte-unlock-sleutel (VERIFIED, `main_unit/docs/flow.md`). De
   NF volgt dat: persistente data naar de EEPROM (Main) of naar NOR en
   SD (Control), nooit naar de interne flash. Een eigen updater is een
   eigen, gereviewd ontwerp buiten deze specificatie (§15).
   - **Statische check:** de NF-images bevatten geen FLASH_KEYR- of
     OPTKEYR-sleutelpatronen (literals of MOVW/MOVT-paren) en geen
     schrijfacties naar FLASH_CR, OPTCR of OPTSR_PRG (gate E0).
3. **De persistente staat blijft bruikbaar voor stock.**
   - **Main (EEPROM):** de NF MOET de vendor-records lezen maar NIET
     wijzigen: instellingen `0x0000`, kalibratie `0x0800`, NVPARAM
     `0x1000`, ATU `0x1800`–`0x24A7` (VERIFIED-layout,
     `main_unit/docs/memory_map.md`). Eigen data alleen in een eigen,
     versie-gemarkeerd gebied boven `0x24A7`, binnen de minimale
     EEPROM-grootte (24C128: tot `0x3FFF`, HIGH); meer ruimte moet de
     NF zelf veilig detecteren (HYPOTHESIS over de werkelijke grootte).
   - **Control (NOR en SD; track EE en ES):** het FAT-volume `1:` en de
     stockbestanden (`config.ini`, bandstack-bestanden, `cwcall.ini`,
     geheugenkanalen; `control_unit/docs/storage.md`) blijven
     ongewijzigd; eigen data in eigen bestanden of mappen; nooit
     herformatteren (stock zou een volume zonder geldig bestandssysteem
     automatisch formatteren, VERIFIED). Het backupdomein (marker
     0xA5A5) blijft compatibel (VERIFIED).
4. **Veilige defaults bij elke boot:** bias 0, T/R op RX, drive 0, de
   latch-uitgangen pas actief na het eerste geldige frame (zoals stock
   het OE-patroon gebruikt, HIGH); TX pas na een geslaagde zelftest
   (I2C-apparaten, FPGA-bustest, Vext in het venster, Idd in rust).
5. **Zelfbescherming van het image.** Een eigen integriteitsveld (CRC of
   hash in een trailer binnen het appslot), gecontroleerd bij de boot.
   Bij een mismatch een **veilige modus**: geen TX, PA onbekrachtigd,
   netwerk functioneel, een duidelijke melding via P1, TCI en het
   beheerprotocol.
6. **Bootlus-bescherming.** Een teller voor opeenvolgende
   watchdog-resets in het eigen persistente gebied; na N = 3 resets
   binnen T de veilige modus.
7. **TX-veiligheid is onafhankelijk van het paneel.** Alle
   TX-veiligheidsgates (§10.4) zitten in de NF-Main en hangen niet af
   van de aanwezigheid, de versie of de capabilities van een paneel.

### 10.2 Emulatortests voor brick-preventie

| Test | Inhoud | Eis |
| --- | --- | --- |
| **E-B1 — Terugrol-compatibiliteit Main** (kritiek pad) | NF-Main draaien (EH en ES), met EEPROM-gebruik, fault-injectie en stroomverlies tijdens het eigen schrijven; daarna **stock Main** in SS op dezelfde EEPROM en hetzelfde backup-SRAM | Stock haalt A1 en A8; de vendor-records zijn bytegelijk |
| **E-B2 — Stock Control ongeschonden** (kritiek pad, uit ES) | Na een ES-run (inclusief in- en uitschakelen en stroomverlies) de stock Control in SS herstarten | Stock haalt A1.4–A1.6 en A6.2 met de vooraf bestaande `config.ini`; NOR, SD en backupdomein bytegelijk (C-S3) |
| **E-B3 — Terugrol van het systeem** (kritiek pad) | Een SS-run direct na een EH- of ES-run op dezelfde media | De persistentie-subset van A1–A12 is groen |
| **E-B2c — Terugrol-compatibiliteit NF-Control** (track EE) | NF-Control draaien, daarna stock Control op dezelfde media | Geen auto-format; stockbestanden bytegelijk |
| **E-B4 — Stroomverlies tijdens de eigen persistente schrijfacties** | Een gestratificeerde steekproef over pagina-, sector- en bestandsgrenzen | De NF boot, eventueel in de veilige modus; de vendor-records ongeschonden |
| **E-B5 — Zelftest faalt bij de eerste boot** | Ontbrekende I2C-apparaten, kapotte FPGA-bus, Vext buiten het venster | Veilige modus, TX geblokkeerd |
| **E-B6 — Verschillende NF-versies** (track EE) | Versiematrix NF-Main tegen NF-Control (C-L10) | Gracieuze degradatie; TX-veiligheid volledig in de NF-Main |
| **E-B7 — Flash- en option-byte-bewaking** | Elke machine met een NF-image, de hele L3- tot L6-suite lang | 0 unlock-pogingen, 0 schrijfacties naar sector 0 of de option bytes |
| **E-B8 — Boot-toestandsprofielen** | De NF in alle profielen van §4.3, en voor de Main met de PowerModel-varianten (§3.8.6) | Correcte boot in elk profiel en elke variant |

**Beperking (expliciet).** Deze tests bewijzen alleen dat de NF de
hardware en de persistente staat niet beschadigt, en dat stock na een
terugrol werkt. Ze bewijzen niets over de bootloaders of het updatepad
op de echte radio. Dat is aan het firmwareproject (§15).

### 10.3 Gefaseerd gatebeleid

**Gates aan emulatorzijde** (de verantwoordelijkheid van dit project):

| Gate | Naam | Inhoud | Exit-criterium |
| --- | --- | --- | --- |
| E0 | Statisch | Reproduceerbare build van de NF-Main (en later de NF-Control), bit-identiek in twee omgevingen; de imagelay-out (vectortabel op `0x08020000`, grootte ≤ appslot, entry binnen het image); de brick-scan (§10.1.2); een image- en geheimscan | alles groen |
| E1 | Emulator: functioneel | L2, L4a volledig in EH (inclusief PW-2–PW-6 en PW-8 onder H1 en H2); L4b-veiligheidsitems C-S2/C-S3; oordeel ≥ GROEN-EMU. Track EE: daarnaast L4c | §9.2; PW-5 en PW-6 = 100 % |
| E2 | Emulator: robuustheid | L5 (fuzz ≥ 24 h cumulatief zonder bevindingen, inclusief het ES-corpus; fault-matrix ≥ 90 %); E-B4, E-B5, E-B7, E-B8; PW-7; 24 h soak in EH met slaap- en wakecycli. Track EE: daarnaast E-B6 | 100 % voor de genoemde E-B- en PW-tests |
| E3 | Terugrol-compatibiliteit | E-B1–E-B3. Track EE: daarnaast E-B2c | 100 % |
| E4 | Overdracht | Een rapportpakket per build voor het firmwareproject: het kwaliteitsrapport, de gate-resultaten E0–E3 en de image-hashes | volledig |

**Gates op de bank met stock** (HIL, black-box):

| Gate | Naam | Inhoud | Exit-criterium |
| --- | --- | --- | --- |
| H-G1 | Twin-validatie | §11.3 fase H1–H2: de black-box-observabelen van de emulator komen overeen met de echte radio, die stock draait | Q-TWIN ≥ de drempel per observabele |

**Afhankelijkheden van het firmwareproject** (geen gates van dit
project; ze MOETEN vervuld zijn vóór een NF-image op de echte radio
komt, §15):

| ID | Afhankelijkheid | Wat dit project verwacht |
| --- | --- | --- |
| F0 | **R0 beantwoord** (§3.8) | Bepaalt of de HIL-opstelling EH is, of de Main met een stock-paneel enkel om in te schakelen (ES-regels) |
| F1 | **Terugrol-oefening naar stock voor de Main** (kritiek pad) | Op de echte radio de officiële vendor-update voor de Main toepassen volgens de vendorprocedure, daarna de stock-HIL-smoke halen. Bewezen vóór de eerste NF-Main-flash. Track EE: dezelfde oefening voor de Control vóór de eerste NF-Control-flash |
| F2 | Installatiepad van de NF opgehelderd en juridisch in orde | Een schriftelijk besluit van de eigenaar, na juridisch advies (§12.4) |
| F3 | **Alleen track EE:** een flashprocedure voor twee units | Volgorde, gedrag bij verschillende versies, herstel van elke tussentoestand naar stock |

**HIL met de NF-Main** (pas na E0–E4, H-G1, F0, F1 en F2):

| Gate | Naam | Inhoud | Exit-criterium |
| --- | --- | --- | --- |
| H-G2 | HIL dry-run NF-Main, **RX-only build** | TX compile-time uitgeschakeld; bediening via P1 en TCI (AetherSDR of andere host, en de referentie-host); de Control blijft stock, losgekoppeld (EH) of aangesloten onder de ES-regels (volgens F0); RX-tests en voedingsmodi; daarna terug naar stock-Main (F1-procedure) | alles groen + terugrol geslaagd + stock Control ongeschonden |
| H-G3 | HIL NF-Main, **laagvermogen-TX** | Cap ≤ 5 W, uitsluitend in de dummy load via de bankschakelaar (§11.4); stapsgewijze TX-tests via P1 en TCI; daarna terug naar stock | alles groen, 0 veiligheidsincidenten |
| H-G4 | NF-Main normaal gebruik | De limieten van de gebruikersconfiguratie, nooit ruimer dan de band- en vermogenslimieten van de radio | release-oordeel |
| H-G5 | **Track EE:** HIL met NF-Control | Zoals H-G2/H-G3, met F1 (ook voor de Control) en F3 vervuld | idem |

**Regels:** een gate wordt alleen gepasseerd met een vastgelegd rapport
en een expliciete go van de eigenaar; elke code- of modelwijziging die
de NF raakt, valt terug naar E0; na H-G2 en H-G3 staat de radio **altijd
terug op stock** tot een volgende geplande sessie, tenzij de eigenaar
anders beslist.

### 10.4 TX-veiligheidsgates (alleen limieten)

Deze eisen gelden voor de NF. Ze worden in de emulator afgedwongen door
de plant-orakels en in HIL door de bankmetingen. Ze beperken alleen;
deze specificatie beschrijft geen manier om band- of vermogenslimieten
te verruimen of te omzeilen.

| # | Gate | Eis |
| --- | --- | --- |
| S1 | Vermogenscap | Een compile-time build-cap (RX-only = geen TX; test = ≤ 5 W; normaal = ≤ de nominale 100 W) plus een runtime-cap ≤ de build-cap; de drive wordt geklemd |
| S2 | Toegestane frequenties | TX alleen binnen de doorsnede van (a) de bandtabel van de radio zelf (kalibratieblok, `main_unit/docs/flow.md`), (b) de geconfigureerde banden en (c) het harde venster van de radio. Nooit ruimer dan (a) |
| S3 | Host- en sessie-watchdog | P1 en TCI: geen geldig verkeer binnen T_wd (≤ 1 s, doel ≤ 250 ms) en dus TX uit. **Netwerk-PTT valt bij elk sessieverlies** (de tegenhanger van upstream-melding #2). CI-V: een PTT-time-out, niet ruimer dan stock (10 s, VERIFIED) |
| S4 | Time-out-timer | Maximale ononderbroken TX-duur (standaard 180 s; test-build 30 s) |
| S5 | SWR-bescherming | Terugregelen boven een drempel (bijv. 2,5:1), TX uit boven een hogere (bijv. 4:1). Stock heeft dit niet (VERIFIED) |
| S6 | Temperatuur, Vext en Idd | TX uit buiten de vensters, met hysterese |
| S7 | Sequentie-interlock | Relais (T/R, LPF, ATU) alleen zonder drive; een minimale settle-tijd vóór de drive. Stock heeft geen expliciete vertraging (VERIFIED) |
| S8 | LPF-verificatie | De gekozen LPF dekt de TX-frequentie, anders geen TX |
| S9 | ATU | Afstemmen alleen met ≤ 10 W draaggolf (zoals stock, VERIFIED) en niet boven 54 MHz |
| S10 | Veilige boot | §10.1.4–6 |
| S11 | Voedingsmodi | Geen TX in slaap; een veilige toestand bij het ingaan van de slaap; TX pas na een volledige wake en een zelftest; PH5 standaard genegeerd (§3.8.4) |

### 10.5 Terugrolprocedure (rollback)

De procedure hoort bij het firmwareproject (F1, §15). Dit project eist:
1. **Voorwaarde:** de terugrol-oefening is ooit geslaagd voor elke unit
   die een NF-image heeft gekregen (op het kritieke pad alleen de Main),
   en het officiële vendorpakket van de laatst bekende goede release
   ligt lokaal klaar, met een hash die overeenkomt met de
   `provenance`-regel van het manifest (§4.4).
2. **Uitvoering:** uitsluitend de officiële vendorprocedure met het
   officiële vendorbestand.
3. **Verificatie:** de HIL-smoke (boot, versie via CI-V, CI-V-basis,
   RX-audio, ping naar het default- of geconfigureerde IP).
4. **Vastleggen** in het HIL-logboek: datum, versies, resultaat.

---

## 11. HIL-integratie (eindfase)

### 11.1 Uitgangspunten

- De **bestaande testbank van de eigenaar** wordt hergebruikt: meerdere
  radio's en antennes, een microHAM-antenneschakelaar met
  SharkRF-integratie, aangestuurd door een Claude-gebaseerde agent, en
  dagelijks in gebruik voor Hermes-Lite 2, AetherSDR en AnySDR.
- **Alleen tier-0-observaties** (`docs/hardware_test_plan.md`): de radio
  blijft dicht, er wordt niets gemeten aan de print, geen SWD.
  Observabelen zijn de externe interfaces: CI-V over USB, LAN
  (Icom-LAN, HDSDR, later P1 en TCI), USB-audio, RF via bankontvangers,
  en de display van de bankvoeding (T0-P1).
- **Laag vermogen en achter gates:** TX uitsluitend ≤ 5 W in een 50 Ω
  dummy load van ≥ 100 W, op een amateurband binnen de vergunning.

### 11.2 Architectuur: één test-API, twee doelwitten

```
        testcase (pytest, getagd @emu / @hil / @both)
                    |
            Target-interface
      +-------------+--------------+
  EmuTarget                     HilTarget (adapter naar de bank-agent)
  - Renode (Main, Control)      - lease van de G7250-lane via het bestaande lease-mechanisme van de bank
  - VLAN, PTY's, plant          - CI-V: USB-serieel (CH342-poort)
  - PowerModel                  - LAN: een geïsoleerd testsubnet (192.168.3.x/24 voor koude starts van stock)
  - invoerinjectie              - audio: USB-geluidskaart van de radio
  - framebuffer                 - RF: bankontvanger (bijv. een HL2 via een verzwakker/sampler)
                                - schakelaar: microHAM (dummy load of antenne), SharkRF-integratie
                                - voeding: schakelbare 13,8 V in de stationsautomatisering
```

**Wat HIL niet kan** (blijft `@emu`-only): invoerinjectie op toetsen,
touch en encoders; screenshots (een vaste camera MAG ter vergelijking);
linktaps, plant-orakels en interne staat.

**HIL-observabelen met een emulator-equivalent:** CI-V-antwoorden en
latenties; het LAN-gedrag (handshake, timing, pakketrates, ping); RX-audio;
de S-meter tegenover een gekalibreerd signaal; TX-vermogen, frequentie,
spectrumzuiverheid en sleutelgedrag (bankontvanger); CI-V-meters (Po,
SWR, Vd, Id); de voedingsstroom (indien de bankvoeding die toont).

In HDSDR-modus MAG de HDSDR-ExtIO-DLL uit het vendorpakket (§4.4) als
black-box-client dienen; ze wordt niet geanalyseerd.

### 11.3 HIL-fases

| Fase | Firmware | Inhoud | Gate |
| --- | --- | --- | --- |
| H0 | stock | Inventaris (T0.1, T0.2, T0.7–T0.10): poorten, VID/PID, de CI-V-route; `wiring.yaml` en de "USB-CAT"-mapping bijwerken. **Plus de koudestartobservaties T0-P1–T0-P4 voor R0** (§3.8.3) | levert F0 |
| H1 | stock, RX-only | Twin-validatie RX: CI-V-dekking (A4, black-box), Icom-LAN (A5, eigen scripts), HDSDR-rate per span (T0.3), I/Q-oriëntatie (T0.4) | — |
| H2 | stock, TX ≤ 5 W dummy | TX-twin: vermogen tegenover de instelling, PTT-latentie, CW-keying, frequentie gezet via LAN en uitgelezen via USB-CI-V, RX tijdens TX (T0.5) | H-G1 |
| — | stock (Main) | **Afhankelijkheid van het firmwareproject:** terugrol-oefening F1, installatiepad F2; de bank verifieert alleen (stock-HIL-smoke) | F1, F2 |
| H3 | NF-Main, RX-only (kritiek pad) | Opstelling volgens F0; bediening via P1 en TCI vanuit AetherSDR of andere SDR-software; voedingsmodi | H-G2 |
| H4 | NF-Main, TX ≤ 5 W (kritiek pad) | | H-G3 |
| H5 (track EE) | NF-Main + NF-Control | Pas na F1 voor de Control en F3 | H-G5 |

### 11.4 HIL-veiligheidsprotocol (bank)

**Vaste regels voor elke sessie** (aanvulling op §3.8.3):
- **Dummy load op elke antenne-uitgang** die de radio kan kiezen, tenzij
  een gate uitdrukkelijk een antenne toestaat (niet in deze
  specificatie).
- **Geen wfview en geen andere CI-V- of LAN-client die PTT kan zetten**,
  behalve het eigen, door de bank-agent gecontroleerde testscript
  tijdens een geplande TX-stap. Bij stock geldt daarbij de
  upstream-melding #2 (HYPOTHESIS/MEDIUM): een sessieverlies kan PTT
  laten hangen; het testscript MOET PTT daarom altijd expliciet via een
  tweede route (USB-CI-V) en door de voeding te schakelen kunnen
  beëindigen.
- **De CTRL-kabel nooit met DC aan losmaken of aansluiten.**
- **Nooit Enter op een Main-console.**

**Procedure:**
1. **Preflight door de bank-agent:** de schakelaar op de dummy load; de
   dummy load aanwezig (SWR-controle op laag vermogen); het vermogen van
   de radio op het minimum (stock: 5 W via CI-V `14 0A`,
   `main_unit/analysis/protocol/civ_main.csv`); de frequentie binnen de
   vergunning en de allowlist; geen ongeautoriseerde client op het
   testsubnet (een netwerkscan op open sessies).
2. **Interlock:** de antenne niet schakelen tijdens TX; eerst RX
   bevestigen via CI-V en de bankontvanger.
3. **Abort-voorwaarden:** gemeten vermogen > 1,2 × cap; SWR > 2:1 op de
   dummy; onverwachte TX zonder bevel; verlies van de controle-interface;
   temperatuurstijging. Bij een abort: PTT uit via elke beschikbare
   route, anders de 13,8 V uit.
4. **Maximale TX-duur per stap** ≤ 10 s, met een pauze tussen de
   stappen.
5. **Logboek:** firmwareversies, instellingen, meetwaarden; geen ruwe
   captures met wachtwoorden in een repo (wegwerp-credentials,
   `docs/hardware_test_plan.md`).

### 11.5 Terugkoppeling naar de modellen (alleen black-box)

Een HIL-afwijking leidt tot een hypothese over het model (de
SEND-latentie van de CH394, de plantkromme, de DRDY-rate, het
PowerModel). De aanpassing gebeurt in de emulator; daarna moet de
stock-baseline opnieuw groen zijn. De golden-sets veranderen alleen via
R8 (§7).

---

## 12. Clean-room en juridische scheiding

### 12.1 Twee kanten

| | RE-kant | Specificatie- en NF-kant |
| --- | --- | --- |
| Repo's | `g7250-base` (privé werkboom plus publieke docs), `g7250-emu` (inclusief de privé golden-sets, buiten git) | `g7250-his` (hardware-interfacespec), `g7250-fw` (clean-room NF) |
| Mag gebruiken | De door de gebruiker aangeleverde images (lokaal, eigen exemplaar), Ghidra-uitvoer, de volledige `g7250-base`-docs, heatmaps, interne traces, RAM-watches, golden-sets | De **HIS** (§12.2), publieke datasheets en protocolspecs (P1, TCI, CI-V), de **publieke vendordocumentatie** (CI-V-referentie rev. 1.2, het rigbestand, de release notes; §4.4), **black-box-testresultaten**, de emulator als **gereedschap** met de hardwaremodellen |
| Mag niet | — | Gedecompileerde of gedisassembleerde code, firmwarebytes, letterlijke firmwarestrings, interne traces van stock (PC, RAM, adressen), heatmaps, golden screenshots en traces, en beschrijvingen van stock-softwaregedrag (de stock-SLIP-link, de stock-GUI, de DSP-ketens) als bron voor implementatiekeuzes; analyse van vendorsoftware (bijv. de ExtIO-DLL) |

**Over het vervallen interoperabiliteitsargument.** De NF hoeft niet met
stock samen te werken; de NF-link is een eigen ontwerp, en
`docs/protocol.md` is voor het NF-team geen bron. Wat de NF nodig heeft,
is **hardwarekennis** (FPGA, CH394, PA, RF-schakelingen, DAC's, codecs,
display, invoer). Die bereikt de clean-room-kant uitsluitend via de HIS.

**Over de modellen.** Ze beschrijven **hardware**: pinnen, chips,
registers, de gedocumenteerde wiring. Elk model MOET per eigenschap de
bron vermelden: datasheet, HIS-paragraaf, `g7250-base`-doc (alleen
RE-kant) of HIL-meting. Gedrag dat alleen dient om stock te laten
slagen (quirk-compatibiliteit), MOET als zodanig gemarkeerd zijn en mag
de NF niet sturen.

### 12.2 Processen

1. **Informatiepoort: de HIS.** Kennis gaat van RE naar NF alleen via de
   HIS, een gereviewd, apart geversioneerd document (repo `g7250-his`).
   - **Inhoud:** per hardwareblok het *wat* en het *hoe aan te sturen*,
     als hardwarefeit: MCU's, klokken, geheugen, pinnen; FPGA-bus en
     commandoset, NCO-woordformaat, I/Q-formaat; CH394 op SPI6
     (W5500-compatibel, inclusief WOL); SPI1-latches en hun bits;
     SPI2-DAC-kanalen; ADC-kanalen en schaal; AXP223-rails, VC6,
     codecs; het voedingspad (PH9/PH5, H1/H2 zodra beslist); de
     EEPROM-layout van de vendor-records (alleen om ze te beschermen);
     display, touch, toetsmatrix, encoders, H-22, NOR, SD, BT; de
     CTRL-kabelbedrading met betrouwbaarheid; de veiligheidsrelevante
     hardwarelimieten.
   - **Uitgesloten:** stock-softwaregedrag dat geen hardwarefeit is.
   - **Elke HIS-regel** heeft een betrouwbaarheidslabel en een herkomst
     (datasheet, publieke bron, HIL-meting, of "RE-afgeleid
     hardwarefeit", zonder adressen of code).
   - **Review** door een tweede persoon of agent op het weglaten van
     softwaredetails; `tools/check_docs.py` van `g7250-base` (weigert
     letterlijke firmwaretekst) draait ook op de HIS en de NF-repo.
2. **Agentinstructies.** Agents die aan de NF werken, lezen geen
   RE-artefacten (de privé analysis-uitvoer, golden-sets, heatmaps).
3. **Black-box-resultaten.** Het NF-team ziet alleen het
   kwaliteitsrapport (§9.3).
4. **Herkomstlog.** Elke NF-requirement verwijst naar zijn bron.

### 12.3 Distributie

- **Nooit verspreid:** vendor-images in welke vorm ook (ontsleuteld of
  versleuteld), vendorpakketten, golden screenshots en traces van stock,
  recordings met stockgedrag, heatmaps.
- **Elke gebruiker levert zijn eigen** ontsleutelde images aan. De
  emulator bevat geen sleutel, geen ontsleutelingscode en geen
  aanwijzing om er een te verkrijgen; de repo bevat alleen hashes.
- **De publieke `g7250-emu`** bevat: de modellen, het harnas, de
  testdefinities, het hash-manifest, de documentatie, de eigen
  testfirmwares en de NF-resultaten.

### 12.4 Juridische aandachtspunten (geen juridisch advies)

| Onderwerp | Kern | Relevantie |
| --- | --- | --- |
| Richtlijn 2009/24/EG (softwarerichtlijn), art. 5 lid 3 | De rechtmatige gebruiker mag de werking van een programma observeren, bestuderen en testen tijdens het laden of uitvoeren | De kern van de emulatorbaseline: de eigen, rechtmatig verkregen firmware draaien om ze te bestuderen |
| Idem, art. 6 (decompilatie voor interoperabiliteit) | Toegestaan onder voorwaarden | De NF werkt niet samen met stock; de externe protocollen van de NF (P1, TCI, CI-V) zijn publiek. Wat overblijft, is het gebruik van RE-afgeleide **hardwarekennis** via de HIS. Of dat onder art. 6 (interoperabiliteit met de hardware), onder art. 5 lid 3 valt, of dat hardwarefeiten als zodanig niet beschermd zijn, is een **vraag voor de advocaat** |
| Idem, art. 7 lid 1 onder c | Verbod op het in het verkeer brengen of het commercieel bezit van middelen die uitsluitend bedoeld zijn om technische beschermingen te omzeilen | **Vervalt voor onze eigen tooling:** de emulator bevat geen ontsleutelingscode, geen sleutelafhandeling en geen manier om images te ontsleutelen; hij leest alleen door de gebruiker aangeleverde images en hasht het vendorpakket als herkomst |
| Verkrijgen en gebruiken van de images | Hoe de gebruiker de ontsleutelde images verkrijgt en gebruikt, valt buiten de emulator | **Blijft een vraag voor de advocaat** (ook in het licht van art. 7 en van richtlijn 2001/29/EG, art. 6) |
| Richtlijn 2001/29/EG, art. 6 | Bescherming van technische voorzieningen; voor software geldt in de eerste plaats de softwarerichtlijn (art. 1 lid 2 onder a) | idem |
| Belgisch recht | De omzetting zit in het Wetboek van economisch recht, boek XI (de titel over computerprogramma's, vroeger de wet van 30 juni 1994) (HIGH) | De concrete toepassing in België |
| Richtlijn 2014/53/EU (radioapparatuur) | Amateurapparatuur die niet op de markt wordt gebracht, en commerciële apparatuur die door en voor radioamateurs is aangepast, vallen buiten de richtlijn (bijlage I) (HIGH) | Eigen gebruik van de NF op de eigen radio; bij **publicatie** van de NF juridisch laten bekijken |
| Vergunning (BIPT) | TX-tests binnen de amateurvergunning | De HIL-gates (§11.4) |
| Bibliotheeklicenties | STemWin alleen op STM32 onder de ST-licentie; HAL BSD-3; CMSIS Apache-2.0 (`docs/libraries.md`, `control_unit/docs/gui.md`) | De NF-Control (track EE) MOET een eigen GUI-bibliotheek gebruiken of een met een passende licentie |
| Vendordocumentatie | De CI-V-referentie, het rigbestand en de release notes zijn publiek gepubliceerd door de vendor | Mogen als bron dienen; niet herverspreiden zonder toestemming; de ExtIO-DLL alleen gebruiken, niet analyseren |
| Merknamen | "Icom", "wfview", "Xiegu" alleen beschrijvend | Geen nabootsing van branding |

**Aanbeveling.** Leg vóór elke publicatie van de emulator, de HIS of de
NF, en vóór F2 van het firmwareproject, een **Belgische IE-advocaat**
voor: (a) het verkrijgen en gebruiken van de ontsleutelde images door de
gebruiker; (b) publicatie en licentie van de emulator, de HIS en de NF;
(c) het gebruik van RE-afgeleide hardwarekennis via de HIS; (d) RED en
de vergunning. Het verpakken van de NF in het vendor-updateformaat is een
vraag van het firmwareproject (§15).

---

## 13. Repository-indeling `g7250-emu`

### 13.1 Structuur

```
g7250-emu/
├── README.md                  doel, quickstart (zonder images), status per vendor-release
├── CLEANROOM.md               de regels van par. 12, voor mensen en agents
├── SECURITY.md                imagebeleid (alleen lokaal, alleen hashes in git), melden van lekken
├── LICENSE                    MIT of Apache-2.0 (eigen code)
├── AGENTS.md                  agentinstructies (RE-kant; NF-agents werken niet in deze repo)
├── pyproject.toml / Makefile
├── deps/
│   └── g7250-base.lock        vastgepinde commit van g7250-base (docs en CSV's als data)
├── images/
│   ├── manifest.yaml          releases: image-hashes (door de gebruiker), groottes, vectoren, herkomst (vendorpakket-hashes)
│   └── verify.py              controle van images uit de lokale imagemap; weigert bij mismatch
├── platforms/
│   ├── g7250_system.resc      twee machines, LinkCable, CTRL-kabel, VLAN (SS, ES, EE)
│   ├── g7250_main_headless.resc   alleen Main, CTRL-kabel los, VLAN (EH, primair)
│   ├── g7250_main.repl        H72x-afgeleid
│   ├── g7250_control.repl     H743-gebaseerd
│   └── profiles/              boot-toestandsprofielen (clean, iwdg-hw, …), PowerModel H1/H2, hardwareprofielen
├── models/
│   ├── stm32h7/               RCC, PWR, FLASH, SYSCFG/EXTI, GPIO, DMA/DMAMUX/BDMA/MDMA, USART, I2C,
│   │                          SPI/I2S, ADC, DAC, TIM, RTC, IWDG, CRC, LTDC, DMA2D, FMC, SDMMC, OTG-stub, DBGMCU
│   ├── devices/               CH394, FPGA (gefuseerd met GPIOE), AIC3204, EEPROM24C, AXP223, VC6, BU2506,
│   │                          ShiftLatch, GT911, PCA9557, W25Q, SDCard, BT401, KeyMatrix, QuadEncoder, H22Mic
│   ├── system/                LinkCable, CtrlCable (wiring.yaml), PowerModel, Plant (PA, detectoren, NTC,
│   │                          belasting, ATU-netwerk), orakels
│   └── python/                prototypes
├── harness/                   Python-pakket `g7250emu`
│   ├── core/                  run, manifest, VT-klok, snapshots, recording en replay, imagemap-configuratie
│   ├── io/                    UART-demux, VLAN, UDP-offload, TAP, pcapng
│   ├── inject/                toetsen, encoders, touch, H-22, plant, voeding, faults
│   ├── observe/               traces, screenshots, audio, orakels, hangdetector
│   ├── protocols/             slip (wrapper rond g7250-base/tools/g7250; alleen baseline), civ, icomlan,
│   │                          hdsdr, p1host, tciclient, nflink, wake (UDP-wake, magic packet)
│   ├── targets/               emu, hil (adapter naar de bank-agent)
│   └── report/                score, rapport, traceerbaarheid
├── firmware-tests/            eigen kleine testfirmwares (L2), clean-room
├── tests/
│   ├── unit/                  L1
│   ├── integration/           L2
│   ├── baseline/              L3 (scenario's A1–A12; vereisen de lokale imagemap)
│   ├── conformance/           L4a (p1, tci, civ-net, headless, power), L4b (es-robustness), L4c (nflink, nfcontrol)
│   ├── brick/                 E-B1–E-B8
│   ├── fault/ fuzz/ perf/     L5, L6
│   └── hil/                   L7 (gegated)
├── matrix/version_matrix.yaml
├── ci/                        pijplijndefinities
├── docs/                      ontwerpdocs, deze specificatie, modeldocs met bronvermelding
└── .private/  (gitignored)    golden-sets, recordings, heatmaps, runs; alternatief: een aparte privé artefactopslag
```

De imagemap zelf staat **niet** in deze structuur: ze ligt buiten elke
repo, op een pad uit de lokale configuratie.

### 13.2 Relaties

```
            g7250-base  (RE-kennis: docs + CSV, publiek; privé werkboom met evidence)
             |      |  vastgepinde commit (data: CSV-velden, knoppen, CI-V-tabellen ...)
             |      v
             |   g7250-emu   (RE-kant tooling; publiek: modellen/harnas/tests/hash-manifest; privé: golden/heatmaps)
             |      |  levert: emulator-releases + testsuites + kwaliteitsrapporten
             v      |
         g7250-his  |  (clean-room hardware-interfacespec; gereviewd; alleen hardwarefeiten)
             |      |
             v      v
            g7250-fw    (clean-room NF: eerst NF-Main; later optioneel NF-Control met de NF-link;
                         leest alleen de HIS, publieke specs, publieke vendordocs en rapporten)
                +-- CI van g7250-fw roept g7250-emu (versie-gepind) aan als testgereedschap
```

- `g7250-emu` hangt af van `g7250-base` als **data**; een update is een
  bewuste lock-bump met een regressierun.
- `g7250-his` wordt door de RE-kant geschreven en is de enige
  hardwarebron van `g7250-fw`; de modellen verwijzen per eigenschap naar
  de HIS-paragraaf.
- De NF-linkspecificatie hoort bij `g7250-fw`; `g7250-emu` neemt er
  alleen de referentiedecoder en de conformance-tests uit over.
- Bevindingen over stock gaan als RE-docs naar `g7250-base`; een push of
  PR gebeurt alleen na een expliciete go van de eigenaar.
- Commits volgen de identiteits- en trailerregels van de eigenaar:
  lokale commits op branches, geen push zonder een go.

---

## 14. Gefaseerde roadmap

Inspanning in persoonsweken (pw) voor één ervaren ontwikkelaar met
agent-ondersteuning; ruwe schattingen (HYPOTHESIS). M0 tot en met M6
vormen fase 1 (de baseline).

| Mijlpaal | Inhoud | Inspanning | Exit-criteria |
| --- | --- | --- | --- |
| **M0** Platformspike | Renode vastpinnen; de H743-platformbeschrijving evalueren; dp-FPU, MPU, DWT; MMIO-snelheid meten; het beslispunt van §2.3 | 1–2 pw | Go/no-go Renode; meetrapport |
| **M1** Stock Main boot tot de hoofdlus | `g7250_main.repl`; RCC, PWR, FLASH, GPIO, EXTI; DMA1, BDMA, MDMA; USART1, USART2-stub; I2C1 met EEPROM, AXP223, VC6, codec; SPI1- en SPI2-sinks; SPI6 plus een minimale CH394; TIM5/6/7/17; ADC1 plus de plant voor de bias-trim; DAC1; I²S3; een minimale FPGA; IWDG; PowerModel (eenvoudig); de hangdetector, strikte modus en heatmap; de image-controle uit de lokale imagemap | 4–6 pw | A1.1–A1.3, A1.7–A1.10, A1.12 voor Main solo; 60 s VT zonder hang |
| **M2** Stock Control boot tot het hoofdscherm | `g7250_control.repl`; FMC, SDRAM, LTDC, DMA2D, framebuffer-capture; GT911, PCA9557, codec-master, I²S2; W25Q met FatFS-image; SDMMC; TIM2/3/4/5/7/8/13/14; USART1 plus BT401; USB-stub; RTC plus backupdomein; DBGMCU, CRC | 5–7 pw | A1.4–A1.9 voor Control solo; stabiele screenshot van het hoofdscherm |
| **M3** Gekoppeld systeem | LinkCable met byte-timing; CTRL-kabelmodel; SLIP-tap; power-off | 2–3 pw | A2.1–A2.4, A2.6–A2.8; A9.1 |
| **M4** Invoer en GUI | Toetsmatrix, encoders, hoofdknop, touch, H-22; screenshot-pijplijn | 3–4 pw | A3 volledig; eerste golden screenshotset |
| **M5** CI-V, Icom-LAN, HDSDR, RF/audio | Volledige CH394 (UDP), VLAN plus UDP-offload; eigen clients (CI-V, Icom-LAN, HDSDR); RX-signaalgenerator, TX-sink; codec-WAV-I/O | 4–6 pw | A4, A5, A2.5, A9.5 |
| **M6** Baseline V1.0.1 bevroren | Persistentie, kalibratievarianten, ATU, SWR-scanner, CW; golden traces; determinisme; nightly CI; versiematrix met herkomst | 3–4 pw | **Fase 1 compleet:** A1–A12 groen; 3 identieke runs; soak 24 h VT |
| **M7** Fault-injectie, record en replay | §8.5, §8.6; live rijstrook | 3 pw | Fault-matrix op stock gedocumenteerd; A12.2 |
| **M8** Boot-toestandsprofielen en brick-tests | Profielen van §4.3, B2-shim; FLASH-bewaking; E0-scanner; E-B1–E-B8 met NF-stand-ins | 2–3 pw | E-B1–E-B8 uitvoerbaar; stock groen in alle profielen |
| **M8b** HIS v1 | De HIS opstellen uit de `g7250-base`-docs, met review (§12.2) | 2–3 pw (RE-kant, parallel) | Gereviewde HIS v1 |
| **M8c** R0-onderzoek (kritiek pad, vroeg) | §3.8.7 stap 1–2: PowerModel H1/H2, stock Main zonder Control (PW-1); de docs; het observatieprotocol T0-P1–T0-P4 klaarzetten | 1–2 pw (kan zodra M1 klaar is) | Rapport met de emulatoruitkomst en een gereed protocol voor de eigenaar |
| **M9** Conformance-framework NF-Main (kritiek pad) | Referentie-P1-host, TCI-client, optioneel CI-V over het netwerk; EH; voedingsmodi (PW-2–PW-8); replay van AetherSDR- en andere host-sessies (C-P11); TCP en WOL in het CH394-model; veiligheidsorakels als harde fouten | 5–6 pw (parallel aan de NF-Main-ontwikkeling) | De suites draaien in EH tegen een NF-Main-stand-in |
| **M9b** ES-robuustheid (lage prioriteit) | C-S1–C-S4; stock-paneelverkeer als fuzz-corpus; E-B2 | 1 pw | C-S2/C-S3 groen tegen de stand-in |
| **M10** Kwaliteitsscore en rapport | §9; traceerbaarheid; overdrachtspakket E4 | 2 pw | Een rapport per build; gates E0–E4 automatisch |
| **M11** HIL met stock | H0–H2; twin-validatie; de koudestartobservaties voor R0 | 3–4 pw (afhankelijk van de bank) | H-G1, F0 |
| — | **Afhankelijkheid van het firmwareproject:** F1, F2 | buiten dit project | vervuld |
| **M12** HIL met de NF-Main (kritiek pad) | H3–H4 | open | H-G2, H-G3 |
| **M13** Optionele track eigen paneel (EE) | C-L1…C-L11, C-C1…C-C7; E-B2c, E-B6; daarna H5 na F1 (Control) en F3 | 5–7 pw (emulatorzijde) | L4c groen; H-G5 |

**Kritiek pad:** M0 → M1 → M2 → M3 → M6 (stock+stock-baseline) → M8,
M8c → M9 (NF-Main headless in de emulator) → M10 → M11 → F0–F2 → M12
(HIL met de NF-Main). M4, M5 en M7 versterken de baseline en lopen
deels parallel; M9b en M13 liggen niet op het kritieke pad.

**Totaal tot en met M10** (zonder M13): ruwweg 38–54 pw. Fase 1 (M0–M6)
alleen: 22–32 pw.

### 14.1 Eerste drie concrete stappen

1. **M0-spike.** Een vastgepinde Renode-versie met een eigen minimale
   testfirmware (clean-room) die dp-FPU-instructies, MPU-regio's, DWT
   CYCCNT, cache-onderhoudsinstructies en een GPIO-bit-bang-lus oefent;
   MIPS en MMIO/s meten. Uitkomst: go/no-go plus de cijfers voor §8.7.
2. **Repo-skelet plus de image-controle.** In `g7250-emu` de structuur
   van §13 met `CLEANROOM.md`, `SECURITY.md`, pre-commit-scans
   (image-hashes, binaire bestanden, vendorextensies), de
   configuratie-instelling voor de lokale imagemap (met de weigering
   binnen een git-werkboom), en `images/manifest.yaml` met de herkomst
   van het V1.0.1-vendorpakket (§4.4) en lege `image_sha256`-velden die
   de gebruiker invult.
3. **`g7250_main.repl` plus de hangdetector en de heatmap.** Stock Main
   in de strikte modus starten en de eerste pollinglussen (RCC, PWR,
   BRRDY, I2C) wegwerken tot de console de boot-statusregels toont en
   het default-IP in de CH394 staat (A1.12). Dat is het begin van M1 en
   meteen de input voor M8c.

### 14.2 Risico's

| # | Risico | Kans | Impact | Mitigatie |
| --- | --- | --- | --- | --- |
| **R0** | **De Main kan niet inschakelen of werken zonder Control** (PH5/PH9; HYPOTHESIS) — **topprioriteit, op het kritieke pad** | middel (onbekend) | hoog: EH op hardware dan niet bruikbaar zonder aangesloten paneel | §3.8.7: (1) PowerModel H1/H2 met PW-1; (2) de docs; (3) de koudestartobservaties zonder de radio te openen: voedingsstroom met de radio "uit" (≈ 0 mA → H1, tientallen mA → H2), CTRL los met DC aan (link op = CH394 uit reset; ping op 192.168.3.199 = de app draait; link die na enkele seconden wegvalt = de stock-valkuil), onder de vaste regels (dummy load, geen PTT-client). Uitwijkpaden: bij H2 alles in firmware (always-on, slaap/wake, WoL); bij H1 zonder auto-start het stock-paneel enkel voor het inschakelen (ES-regels), of als laatste redmiddel een toets-emulatiecontact op de CTRL-connector |
| R1 | De boot-toestandsprofielen dekken de echte overdrachtstoestand niet | middel | middel | Profielmatrix; read-before-write-detector; E-B8; HIL H1 |
| R2 | De H7-dekking van Renode valt tegen (H72x, SPI/I2S v2, DMAMUX, MDMA, OTG) | middel | hoog | M0; eigen C#-modellen |
| R3 | De emulatie is te traag (FPGA-bit-bang, float-DSP bij 550 MHz) | middel tot hoog | middel | Gefuseerd FPGA-model; rate-index 3 als standaard; snapshots; parallel forken |
| R4 | Het determinisme lekt | middel | hoog voor de golden-aanpak | Strikte scheiding van de rijstroken; CI-detectie; drie-run-checks |
| R5 | De twin wijkt af van de hardware | hoog | middel | HIL H1/H2; parametrische modellen; Q-TWIN |
| R6 | De gebruiker kan voor een nieuwe release geen ontsleutelde images aanleveren (formaatwijziging of anti-tamper bij de vendor) | middel | middel | De emulator hangt niet van het formaat af; de release blijft "herkomst bekend, niet getest"; oudere releases blijven de baseline |
| R7 | Een image- of pakketlek in git of artefacten | laag tot middel | hoog (juridisch, vertrouwen) | Pre-commit- en CI-scans op hashes, binaire bestanden en extensies; de imagemap buiten elke werkboom (afgedwongen); privé-runners |
| R8 | Clean-room-besmetting (via de HIS of artefacten) | middel | hoog | §12-processen, HIS-review, agentinstructies, herkomstlog, check op de NF-repo |
| R9 | Juridische onzekerheid rond het verkrijgen en gebruiken van de images, de HIS en publicatie | middel | hoog | Belgische IE-advocaat vóór publicatie en vóór F2; niets verspreiden |
| R10 | De NF beschadigt de persistente staat, zodat stock na een terugrol niet goed werkt | laag (met E-B1–E-B3) | hoog | §10.1.3; gate E3 |
| R11 | FPGA-TX-gedrag onbekend, dus P1-TX niet goed te modelleren | hoog | middel | TX-sink met parameters; HIL H2 met stock; TX in de NF pas na H-G3 |
| R12 | Het TCP- of WOL-gedrag van de CH394 wijkt af van de W5500 | middel | middel | P1-first; conservatieve socketinstellingen; HIL-verificatie |
| R13 | GUI-screenshots niet stabiel | middel | laag tot middel | Vast RTC-epoch; capture bij "stil"; maskers |
| R14 | Een HYPOTHESIS-bedrading van de CTRL-kabel blijkt fout | middel | laag tot middel | `wiring:hypothesis`-tags; HIL-terugkoppeling |
| R15 | Een onderschatte inspanning | hoog | middel | Gefaseerde exits; prioriteit op het kritieke pad; Python-prototypes eerst |
| R16 | De NF-Control verdubbelt het testoppervlak | middel (optionele track) | middel | M13 apart van het kritieke pad |
| R17 | Een aangesloten stock-paneel veroorzaakt TX of verliest zijn instellingen door de NF-Main | laag | hoog | S-ES1–S-ES3; C-S1–C-S3 |
| R18 | Het gedrag tegenover echte SDR-hosts wijkt af van de referentie-host | middel | middel | Opname en replay (C-P11); HIL H3 |
| R19 | Een hangende netwerk-PTT van stock tijdens bank- of koudestarttests (upstream-melding #2) | middel | hoog | Vaste regels: dummy load, geen PTT-client, een tweede route en de voeding als noodstop (§3.8.3, §11.4) |

---

## 15. Buiten scope: open punten voor het firmwareproject

Deze punten horen bij het firmwareproject (`g7250-fw`), niet bij de
emulator. De emulator boot het applicatie-image rechtstreeks (§4.3),
ontsleutelt niets (§4.1) en levert de gates E0–E4 (§10.3).

| # | Open punt | Waarom het telt | Wat de emulator levert of verwacht |
| --- | --- | --- | --- |
| O1 | **Aanvaardt de vendor-bootloader een eigen image** (Q6, `docs/hpsdr_gap_analysis.md`)? Checksum of handtekening? | Zonder aanvaard image geen installatie | Een structureel geldig image (E0) |
| O2 | **Hoe komt het image op de radio?** Hypothesen: een seriële bootloader op de Main-console (G90-precedent) of een bestand op de MSC-schijf van Control (`main_unit/docs/peripherals.md`, `docs/related_radios.md`) | Installatie- en terugrolprocedure | Niets |
| O3 | **Het updatepad van de NF** (vendor-bootloader of een eigen updater) | Onderhoud en herstel | De regel "geen flashprogrammering in de app" (§10.1.2) geldt tot het firmwareproject anders beslist |
| O4 | **Terugrol-oefening** (F1) voor de Main, en voor de Control in de track EE | Het enige bekende herstelpad zonder SWD | De stock-HIL-smoke; de hash-gecontroleerde herkomst van het vendorpakket (§4.4) |
| O5 | **Alleen track EE:** flashprocedure voor twee units (F3) | Hoger brick-risico | E-B6 en §10.1.7 |
| O6 | **Verpakking in het vendor-updateformaat** en de juridische toets (F2) | Juridisch gevoelig (§12.4) | Niets: de emulator ontsleutelt, versleutelt of verpakt niets |
| O7 | **Topprioriteit (R0, F0): kan de Main inschakelen en werken zonder Control?** | Voorwaarde voor EH op de echte radio | §3.8: feiten, H1/H2, PowerModel met PW-1–PW-8, koudestartobservaties T0-P1–T0-P4. Het firmwareproject implementeert P-1–P-11 en beslist over de CH394-WOL-functie |
| O8 | **Alleen track EE:** de NF-linkspecificatie (framing, baudrate, synchronisatie, eigenaarschap, protocolversie en capability-onderhandeling) | Basis voor C-L1…C-L11 | De generieke eisen van §8.3.1 en de LinkCable-faultinjectie |
| O9 | **Het G7250-P1-profiel en het board-id**, de TCI-commandoset, het CI-V-commandoprofiel (met de publieke CI-V-referentie rev. 1.2 als bron) | Basis voor C-P, C-T en de CI-V-conformance | De referentieclients in het harnas |
| O10 | **Gedrag tegenover een aangesloten stock-paneel**: welke paneellijnen expliciet in te schakelen zijn, en of de NF-Main op de link volledig zwijgt | S-ES1–S-ES3 | C-S1–C-S4 |

---

## Bijlage A — Bronnen

**G7250 (repo `g7250-base`):**
- `README.md`, `AGENTS.md`, `TODO.md`
- `docs/architecture.md`, `docs/mcu_identification.md`,
  `docs/hardware_init.md`, `docs/protocol.md`, `docs/civ.md`,
  `docs/dma.md`, `docs/atu.md`, `docs/cw.md`, `docs/libraries.md`,
  `docs/hardware.md`, `docs/hardware_test_plan.md`,
  `docs/hpsdr_gap_analysis.md`, `docs/related_radios.md`,
  `docs/x6100_comparison.md` (gedeeltelijk)
- `main_unit/docs/startup.md`, `memory_map.md`, `peripherals.md`,
  `flow.md`, `network.md`, `dsp.md`
- `control_unit/docs/startup.md`, `memory_map.md`, `peripherals.md`,
  `flow.md`, `gui.md`, `storage.md`, `voice_cw_memories.md`
- CSV's onder `*/analysis/` (flow, peripherals, memory, protocol,
  storage), waaronder `hw_init_table.csv`, `i2c_devices.csv`,
  `ram_objects.csv`, `cmd01_fields.csv`, `cal02_fields.csv`,
  `band_table.csv`, `wfview_packets.csv`, `civ_scope.csv`,
  `civ_main.csv`, `civ_control.csv`, `gpio_map.csv`, `iwdg_kicks.csv`
- `tools/g7250/README.md` (de clean-room SLIP- en HDSDR-tools)

**Publieke upstream-meldingen** (niet door ons geverifieerd;
HYPOTHESIS/MEDIUM):
- `fventuri/g7250-base` issue #1: de geforceerde netwerkdefaults van
  stock Main (192.168.3.199, gateway 192.168.3.1, netmask
  255.255.255.0, basispoort 50001).
- `fventuri/g7250-base` issue #2: netwerk-PTT wordt niet vrijgegeven
  bij sessieverlies.

**Publieke vendordocumentatie** (uit het officiële pakket
`2026-11-09_Xiegu_G7250_V1.0.1.zip`, radioddity.com/pages/xiegu-download;
alleen als publieke bron, niet herverspreid): CI-V-referentie rev. 1.2
(PDF), wfview-rigbestand `G7250.rig` (CI-V 0xA0), release notes. De
HDSDR-ExtIO-DLL alleen als black-box-client.

**Publiek (platform, chips, protocollen; geen inhoud overgenomen):**
- de Renode-documentatie (Antmicro): multi-machine, UART-hub, netwerk en
  TAP, Python- en C#-peripherals, GDB, Robot, state save/load, execution
  tracing;
- de QEMU-documentatie (Arm-machines, STM32-boards, record/replay met
  `icount`);
- de ST-referentiehandleidingen RM0433 (H743) en RM0468 (H72x/H73x) en de
  datasheets;
- WCH, CH394-handleiding 1, versie 1.2 (wch.cn): MODE-bit WOL,
  GINT/GINTE-bit MP, PHY_CFG-power-down, SPI tot 62 MHz;
- de WIZnet W5500-datasheet; WCH CH394DS1 (zoals geciteerd in de
  `g7250-base`-docs);
- de AIC3204-, AXP22x-, 5P49V6965-, BU2505/2506FV-, GT911-, PCA9557-,
  W25Qxx- en 24Cxx-datasheets;
- OpenHPSDR Protocol 1 (Metis "How it works", USB protocol V1.58) en de
  Hermes-Lite 2-protocolwiki;
- de ExpertSDR TCI-protocolspecificatie;
- de richtlijnen 2009/24/EG, 2001/29/EG en 2014/53/EU, en het Belgische
  Wetboek van economisch recht, boek XI.

*Einde van v0.5.*
