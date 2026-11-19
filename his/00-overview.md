# HIS 00 — Overview (outline)

**Scope.** The behavioural interface of the G7250 hardware as the native-SDR
firmware must drive it. Two MCUs: Main (STM32H72x class) and Control (STM32H743
class), linked by a serial inter-MCU protocol.

**Conventions.** Confidence tags (VERIFIED/HIGH/HYPOTHESIS) mirror the source
observation. Every entry cites its evidence (an emulator run or a public
datasheet), never stock firmware source.

**Process.** Candidate facts are proposed from `g7250-emu` observations, pass a
clean-room review (behaviour, not implementation), then land here. The firmware
repo consumes this spec only.

*(Sections 10–80 are to be populated under that process.)*
