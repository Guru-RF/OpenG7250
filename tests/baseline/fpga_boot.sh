#!/bin/bash
# D2 FPGA fused-model boot test (needs the local decrypted image-map).
#
# Boots the stock Main with the fused GPIOE+FPGA port (m1_run --fpga) and asserts
# the FPGA bus check passes and I/Q flows: no FPGA errors, version read, and the
# firmware's "Check complete!" line. The runtime-compiled port is slow, so this
# uses a long budget and is separate from the fast smoke gate. Skips with no image.
set -u
cd "$(dirname "$0")/../.." || exit 2
REPO="$PWD"; OUT="$REPO/.private/m1"; fail=0
ok(){ printf '  ok   %s\n' "$1"; }; bad(){ printf '  FAIL %s\n' "$1"; fail=1; }

if ! python3 harness/g7250emu/imagemap.py main >/dev/null 2>&1; then
  echo "fpga boot: SKIP (no image-map)"; exit 0
fi

echo "[boot --fpga] stock Main, 175 s budget"
python3 harness/g7250emu/m1_run.py --fpga --timeout 175 >/dev/null 2>&1
C="$OUT/main_console.txt"
grep -q "Init FPGA"            "$C" && ok "Init FPGA"                || bad "Init FPGA"
grep -q "FPGA FW Version"      "$C" && ok "FPGA version read"        || bad "FPGA version read"
grep -q "Check complete!"      "$C" && ok "FPGA bus check complete"  || bad "FPGA bus check"
if grep -qi "FPGA BUS Error\|FPGA bus error" "$C"; then bad "FPGA errors present"; else ok "no FPGA bus errors"; fi
grep -qi "Start RX mode"       "$C" && ok "TRX RX mode"              || bad "TRX RX mode"

echo
[ $fail -eq 0 ] && { echo "fpga boot: ALL PASS"; exit 0; } || { echo "fpga boot: FAILURES"; exit 1; }
