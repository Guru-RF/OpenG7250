# Xiegu G7250: hardware and remote operation

Research date: **2026-11-13**. Published specifications and demonstrations refer to different firmware and production stages; the distinctions below matter when reproducing a setup.

## Radio and connections

The G7250 is a direct RF sampling SDR with a separate RF main unit and 7-inch touchscreen controller. Radioddity currently specifies up to **100 W on HF and 90 W on 6 m**, an internal automatic antenna tuner with a **20–150 Ω** matching range, and two selectable SO-239 antenna connectors. It has **one receiver**, so those antenna connectors do not provide simultaneous reception on two frequencies. The advertised supply is **13.8 V DC ±15%**, with maximum transmit current of **25 A**. These are vendor specifications, not measurements made for this project. [Radioddity product page](https://www.radioddity.com/products/xiegu-g7250)

The head connects to the main unit through the dedicated **15-pin L2001 CTRL cable**. The main unit has a separate **RJ45 LAN port**. The controller carries the power button, microphone and key connections, speaker output, and USB interfaces used for computer audio/CAT. The manual requires a supply capable of at least 25 A and describes HDSDR network reception. A detached head positioned elsewhere is therefore different from a radio operating with the head completely unplugged. Earlier descriptions implying an Ethernet connection between the two boxes should not override the documented production connections. [Official operation manual, pp. 7–9, 13–14, 17, 42, 44, 48](https://radioddity.s3.amazonaws.com/Xiegu_G7250_Operation_Manual_EN_rev0.1_20261008.pdf)

## What works without the head?

**Receive and PC tuning after startup have been demonstrated with the head disconnected.** In Temporarily Offline's 20 October 2026 video, the presenter starts with the radio running, disconnects the cable behind the controller, and its display goes dark. HDSDR continues receiving; changing the PC tuning moves the displayed LO from 14.074 to 13.074 MHz. The sequence was checked in both the video frames and captions. It uses **HDSDR with ExtIO_G7250.dll**, running under Wine on Linux. [Demonstration from approximately 12:27](https://www.youtube.com/watch?v=BKcAIiPExZY&t=747)

That demonstration uses a preproduction setup. It does **not** establish cold startup with no head attached, recovery after a power failure, or transmission over Ethernet. The presenter specifically notes that unplugging the head also removes access to the power button. Consequently, an unattended, fully headless transmit station remains unverified; a screen blanking feature would not establish the same thing either.

## Firmware and software status

The bundled **V1.0.1** release notes add a network control protocol module to the main unit and network remote-control content to the controller. They also explicitly say the **TCI module is disabled**. Those statements do not document a complete remote operating interface or prove headless startup. [Bundled release notes](../firmware/2026-11-09_Xiegu_G7250_V1.0.1/G7250_V1.0.1_ReleaseNote-261109_%28EN_CHS%29.txt)

A separate November 1 Station Master Pro setup guide uses **serial CAT/PTT plus Ethernet for the waterfall scope**, illustrating that working PC control can still depend on the head's USB connection. [Station Master setup guide](https://stationmastercloud.com/post/816/Xiegu-G7250-how-to-set-it-up-in-Station-Master-Pro)

No authoritative G7250-specific confirmation of full **wfview** compatibility was found in this research. X6100/X6200 instructions, generic CI-V compatibility, and shared UDP port numbers are insufficient evidence. Cold startup, transmit audio/PTT, and operation after network loss need separate verification on the exact G7250 firmware being used.
