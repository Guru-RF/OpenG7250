# Comparison with xiegu-g7250-open-control

Reviewed on 2026-11-13 at commit
[`17648f19254fa4556fe06339bfdbf0cff8916d51`](https://github.com/nathan86daniels-commits/xiegu-g7250-open-control/tree/17648f19254fa4556fe06339bfdbf0cff8916d51).
The reference was downloaded into `/tmp/g7250-open-control-reference` for reading;
its application was not run and no dependencies were installed.

The project provides useful browser UI, receiver DSP, CAT scheduling and simulated
radio examples. Its README explicitly distinguishes simulator testing from
unperformed testing of the complete application on a real G7250. The LAN protocol
notes also credit earlier hardware observations and DLL analysis. Those claims
should be compared with the exact firmware version rather than treated as proof
of complete headless operation.

## Power and head dependency

No bootloader image, firmware patch, cold-start test, standby implementation or
power-on mechanism was found. The project therefore does not settle whether DC
alone starts the main unit. Our [startup conclusions](headless-startup-analysis.md)
remain unchanged.

Its real control transport is USB serial CI-V (`g7250/cat.py`, `SerialTransport`;
selected in `g7250/station.py`). Transmit audio uses the USB audio device
(`web/js/audio.js`). The production G7250's USB connection is on the head, so this
architecture still depends on the head for these functions. See the port evidence
in [radio-overview.md](radio-overview.md).

With CAT absent, `station.py` can tune over LAN and change its PC-side demodulator.
Changing that local mode or passband is not the same as changing the main radio's
operating mode, DSP filter, transmit settings or hardware controls.

## Legacy LAN differences requiring verification

These are comparisons with our supplied **2026-11-09 V1.0.1** main firmware and
bundled ExtIO DLL. The reference commit is older. An earlier protocol revision
could explain differences; its original hardware captures/version were not supplied.

| Item | Reference implementation | Our firmware / DLL evidence |
|---|---|---|
| UDP ports and sample rate | Radio 50002, PC 50001, 48 ksample/s | Consistent with the legacy route. |
| Tune command | `protocol.py` sends wire `00 01` | DLL setter `0x100018fd` passes `0x0103` to its network-order builder. Main parser `0x0804af68` accepts wire `01 03`. |
| IQ datagram | `radio.py` accepts exactly 768 bytes | Firmware sends 774: header `AA 55 55 AA 02 02` followed by 768 sample bytes. |
| Session startup | No discovery or heartbeat in `RadioLink` | Firmware accepts discovery `01 01` and heartbeat `01 02`, learns the destination and expires the session after about 10 seconds. |
| IQ-centre relationship | Scope panning assumes it can retune IQ without changing radio VFO | Legacy tune applies through `0x0804b184` → `0x0803ebb0` to the current VFO. Independent LO/VFO behavior is not established. |

The simulator imports the same protocol constants and encoding as the client, so
an end-to-end simulator pass cannot resolve these disagreements with the firmware.
Our [receive-only probe](../scripts/probe_radio.py) follows the recovered V1.0.1
discovery framing. Packet captures on the user's radio remain the next check.

## Adapting its UI to main-unit-only operation

The project's statement that LAN carries no CAT/PTT describes its legacy-LAN plus
USB implementation. V1.0.1 also contains a separate **wfview/Icom-style network
service**, with real control and bidirectional audio paths; see the
[IP coverage inventory](ip-protocol-coverage.md).

A practical adaptation would require:

1. A wfview-compatible session transport handling login, negotiation, heartbeat,
   CI-V, audio and scope. Raw serial CI-V bytes cannot simply be sent to UDP.
2. A G7250 network command profile. The network destination is `A0`, absent from
   this project's USB auto-detection list. Its standard `05` frequency setter
   does not match this firmware's network handler, which treats `05` as VFO
   selection; use the verified `25` A/B-frequency handler instead. AGC, filter,
   VFO mode and unsupported settings also require explicit mappings.
3. A verified capability list. The project's unsupported-command detection relies
   on CI-V `FA`; the network firmware can echo a command even when it only caches
   or ignores the requested setting. Echoes cannot establish support.
4. A decision about the receive display/audio source. This firmware selects either
   legacy IQ or wfview service. The existing legacy IQ decoder cannot be combined
   unchanged with wfview control; the latter provides PCM audio and scope frames.
5. Both client and firmware handling of lost PTT control. `PttGuard` in `cat.py`
   supplies useful heartbeat, ownership and maximum-duration patterns. Its release
   is still a command sent over a working transport: it cannot guarantee unkeying
   after that transport fails. Our firmware analysis found retained network PTT on
   session loss, so a firmware-side release remains necessary for a headless TX
   experiment.

The UI and client-side processing are useful reference material. They do not
remove the cold-start unknown, provide a drop-in V1.0.1 network client, or prove
that every displayed control has a working main-unit IP equivalent.

## Reference files

- [README and stated test status](https://github.com/nathan86daniels-commits/xiegu-g7250-open-control/blob/17648f19254fa4556fe06339bfdbf0cff8916d51/README.md)
- [Legacy framing](https://github.com/nathan86daniels-commits/xiegu-g7250-open-control/blob/17648f19254fa4556fe06339bfdbf0cff8916d51/g7250/protocol.py)
- [LAN client](https://github.com/nathan86daniels-commits/xiegu-g7250-open-control/blob/17648f19254fa4556fe06339bfdbf0cff8916d51/g7250/radio.py)
- [Serial CAT and PTT guard](https://github.com/nathan86daniels-commits/xiegu-g7250-open-control/blob/17648f19254fa4556fe06339bfdbf0cff8916d51/g7250/cat.py)
- [CI-V command definitions](https://github.com/nathan86daniels-commits/xiegu-g7250-open-control/blob/17648f19254fa4556fe06339bfdbf0cff8916d51/g7250/civ.py)
- [Station routing and local demodulation](https://github.com/nathan86daniels-commits/xiegu-g7250-open-control/blob/17648f19254fa4556fe06339bfdbf0cff8916d51/g7250/station.py)
