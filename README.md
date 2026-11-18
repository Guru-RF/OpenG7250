# g7250-emu

Emulator and automated test environment for the Xiegu G7250, part of the
OpenG7250 effort. Clean-room: built from the public RE documentation in
g7250-base and from public sources.

The emulator does **no** decryption. You supply already-decrypted
application images in a local folder outside any repository; the emulator
reads that folder through a config setting and checks each image against a
hash-only manifest. Firmware images and key material are never committed
or distributed.

See `docs/` for the specification.
