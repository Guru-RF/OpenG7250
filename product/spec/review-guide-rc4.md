# Review guide — spec rc4 (for ON8ST)

- Date: 2026-11-20
- Purpose: let ON8ST review the proposed decisions 0020, 0021 and 0022 in one pass. It lists
  the choices that need the owner's judgement, with where to read them. The rest of the three
  decisions is detail that follows from accepted decisions or from [P2]/[TCI] and has been
  checked by six rounds of independent review (last verification: no open HIGH or MEDIUM).
- How to answer: per item "accept", "change to …", or "discuss". Anything not mentioned is
  taken as accepted with the decision it belongs to.

## A. Choices that need your judgement

| # | Choice in rc4 | Where | Alternative that was considered |
|---|---------------|-------|---------------------------------|
| A1 | Register-map port **7250**, management port **7251** (UDP) | 0020 §1–§2; spec B2.3, A1.3 | ports in the 1030–1034 range (collide with P2 wideband defaults) |
| A2 | TCI on TCP **50001** on both levels (AetherSDR's port) | 0021 §2; part C C2 | 40001 (no source), configurable only |
| A3 | TCI announces **`PROTOCOL:ExpertSDR3,2.1`** (compatibility), `DEVICE:G7250` | 0021 §4–§5; part C C3 | an own program name such as `G7250-FW` |
| A4 | Once armed, **any TCI client may key** (policy `any`; `holder` optional) | 0021 §1, §24, §46; part C C5.5.8 | only the client that armed |
| A5 | A generic TCI client's `TUNE`/CW key-down lasts **1 s** unless it restates the request | 0021 §18, §28; part C C8.2 | 2 s, or no limit below the 5 min maximum TX time |
| A6 | First management secret claimed **over the network** in a 300 s window after first start or factory reset | 0008 (accepted), 0020 §24; spec A1.10 | confirmation on the controller (needs HIS-17) |
| A7 | **P2 Set IP accepted** as in P2, but only from the own subnet (limited broadcast from anywhere) | 0008, 0022 §70; spec B3.9 | refuse Set IP; management only |
| A8 | **P2 control only from the own subnet** (C&C, DUC I&Q, register map) | 0022 §49; spec B11.15 | accept routed hosts too (reflection risk) |
| A9 | **Takeover always allowed**; it unkeys, disarms, and the old owner is told | 0007 (accepted), 0022 §3, §29, §48, §87; spec A2.4 | refuse takeover while armed |
| A10 | Safety timers: keyed timeout **500 ms**, max continuous TX **5 min** (unkey only), CW **hang ≤ 2 s**, CWX key-down cap **1 s** | 0007 (accepted), 0022 §25, §36, §83; spec A3.4d, B10.5, B10.5a | other values |
| A11 | Limit reaction times: SWR/voltage/current/RF-not-keyed **≤ 10 ms**, temperature ≤ 100 ms | 0022 §80; spec Table A3-2 | leave to HIS-11/HIS-12 |
| A12 | No PEP detector ⇒ PEP **estimated from the DUC samples**; AM limited on its **carrier** (25 W) | 0022 §43, §52, §62; spec A3.4c | mean-only limits (unsafe for high crest factor) |
| A13 | Restart by the run bit **keeps RX settings** for the same host; TX settings always reset | 0022 §76, §78; spec B5.4 | resend everything after every session end |
| A14 | Frequencies always as **phase word on a virtual 122.88 MHz clock** (discovery byte 21 = 1) | 0022 §81; spec B3.8 | follow the real hardware clock (HIS-04) |
| A15 | With **CW break-in clear**, KEY/CWX form RF only inside the owner's PTT transmission | 0022 §85, §87; spec B10.5b | KEY/CWX key on their own as with break-in |
| A16 | Wideband in M2: **4096 samples, 20 frames/s** (already accepted in 0004) | 0004 (accepted) | — |
| A17 | Firmware updates: integrity checks, **no signatures yet**; downgrade needs a flag | 0008 (accepted), 0020 §27 | signed images |
| A18 | Factory reset keeps the persistent limits, log and counters; resets network, level, secret, region, TCI allow-list | 0022 §60, §69; spec A1.6a | reset limits too |

## B. Detail you can take as a block

- 0020 §3–§31 except those above: address map, codes, enumerations, message formats, error
  handling (B11), timers, capability record v1.1.
- 0021 §6–§47 except those above: TCI command subset, extensions (`G7250_*`), liveness table,
  stream formats, level-2 sequences.
- 0022 §1–§88 except those above: the fixes from the reviews and the P2 byte check.

## C. Known limits stated in rc4 (accepting rc4 accepts these)

- A host that sends non-zero samples in CW gaps hides those gaps from the "RF while not keyed"
  check (spec A3.9a item 6; part C C8.2.5).
- A host whose I/O thread keeps sending a cached PTT/CWX bit while its TX logic hangs is
  bounded by the underrun check, the caps and the maximum TX time, not by the keyed timeout
  (spec B10.5; part C C8.2.3a).
- TCI clients answering TX_CHRONO with zero audio in AM/FM keep a carrier until the maximum TX
  time (part C C8.2.3a).
- Unnumbered P2 hosts: duplicated or reordered High Priority packets are filtered only by the
  10 ms edge rule (spec B11.6a).

## E. Your remarks on rc4 (2026-11-20) and how they are handled

| # | Remark | Where | Choice to confirm |
|---|--------|-------|-------------------|
| E1 | Nothing says what is done with the controller (head), although it is clearly out of scope | 0023; spec part A "Scope of the firmware", B1.9, A1.5 I-6; design note §7; HIS-17 | Scope statement taken as accepted (your remark). Proposed details: never write controller firmware; do no harm on CTRL, idle until HIS-17 says what is safe; network operation without a working controller; a controller in an unknown or error state is accepted (you get it back by returning to stock) |
| E2 | Switching back and forth between stock and new firmware; from our firmware it must be possible to upload the factory firmware again | 0024; spec A1.8a, Table A1-2 (`RETURN_TO_STOCK` 0x0050, `ENTER_VENDOR_RECOVERY` 0x0051), T-A1-52 to T-A1-57; design note §7, §8; HIS-18, HIS-19 | Layered: owner-supplied stock image through the update path MUST (your remark); vendor's own path MUST stay intact; retained stock image SHOULD if the flash has room; reboot into vendor recovery MAY. Switch is permanent (no trial boot), never while armed or keyed, erases our secret. Stock to new is the first-install path, documented outside the network spec. Alternative considered: vendor path or recovery mode as the only MUST |
| E3 | Your decisions of 2026-11-20: controller left alone (option A, not a front panel); installing the factory firmware from the main-unit side, in the same way as the new firmware, without the controller, in both directions | 0023 note of 2026-11-20; 0025 (proposed); spec part A "Scope of the firmware", A3.7, A1.8a "One installation path" and item 9, T-A1-58, T-A1-59; design note §7, §8; HIS-19 | One main-unit path for both image kinds (same transport, staging, checks, reset order); vendor path and vendor recovery count only without a controller step; first install on the same path, pending HIS-19. Open risk: if the only stock path needs the controller, it comes back to you (outcomes listed in 0025 R5, none chosen). Alternatives considered: keep 0024's layered set; a separate path per direction |

## D. After your answer

- Accepted items: the decision files get status "accepted (ON8ST, date)".
- Changed items: one more fix pass, the lint and traceability checks, a short verification
  review, and a new tag.
