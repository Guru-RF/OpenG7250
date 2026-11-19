#!/bin/bash
# M1 scaffolding smoke test (image-independent).
#
# Verifies the parts of M1 that do not need the decrypted image:
#   1. observe.py  — strict/hang/heatmap logic self-test
#   2. ch394.py    — A1.12 default-IP register logic self-test
#   3. the Main platform loads on the pinned Renode with the 320 KiB AXI SRAM
#      override (the Main-specific memory map, not the H743 base 512 KiB)
#   4. observe end-to-end: enable logging, poke RCC/PWR, parse the real log clean
#   5. m1_run.py   — refuses cleanly when no image-map is configured (exit 2)
#
# Run from anywhere:  bash tests/baseline/m1_smoke.sh
set -u
cd "$(dirname "$0")/../.." || exit 2
REPO="$PWD"
RN="$REPO/tools/renode-1.17.0/Renode.app/Contents/MacOS/renode"
OUT="$REPO/.private/m1"; mkdir -p "$OUT"
fail=0
ok()   { printf '  ok   %s\n' "$1"; }
bad()  { printf '  FAIL %s\n' "$1"; fail=1; }

echo "[1] observe.py self-test"
python3 harness/g7250emu/observe.py --selftest >/dev/null 2>&1 && ok observe || bad observe

echo "[2] ch394.py self-test"
python3 models/devices/ch394.py >/dev/null 2>&1 && ok ch394 || bad ch394

echo "[2b] i2c_devices.py self-test"
python3 models/devices/i2c_devices.py >/dev/null 2>&1 && ok i2c_devices || bad i2c_devices

echo "[2c] power_model.py self-test"
python3 models/system/power_model.py >/dev/null 2>&1 && ok power_model || bad power_model

echo "[2c2] r0_sim.py self-test (PW-1 predictions)"
python3 harness/g7250emu/r0_sim.py --selftest >/dev/null 2>&1 && ok r0_sim || bad r0_sim

echo "[2d] bias_trim_plant.py self-test"
python3 models/devices/bias_trim_plant.py >/dev/null 2>&1 && ok bias_trim_plant || bad bias_trim_plant

echo "[2e] spi_sink.py self-test"
python3 models/devices/spi_sink.py >/dev/null 2>&1 && ok spi_sink || bad spi_sink

if [ ! -x "$RN" ] && [ ! -f "$RN" ]; then
  echo "[3-4] SKIP (pinned Renode not found at tools/renode-1.17.0)"
else
  echo "[3] platform load: 320 KiB AXI SRAM + SPI1/2/3/6 controllers"
  cat > "$OUT/smoke_load.resc" <<EOF
mach create "main"
machine LoadPlatformDescription @platforms/g7250_main.repl
peripherals
quit
EOF
  LOAD_OUT="$(timeout 90 "$RN" --disable-xwt --console -e "path add @$REPO" \
        -e "include @$OUT/smoke_load.resc" </dev/null 2>&1)"
  if echo "$LOAD_OUT" | grep -q "<0x24000000, 0x2404FFFF>"; then
    ok "axiSram = 0x24000000..0x2404FFFF (320 KiB)"
  else
    bad "axiSram override not found (expected 320 KiB)"
  fi
  if [ "$(echo "$LOAD_OUT" | grep -cE 'spi[1236] \(STM32H7_SPI\)')" -eq 4 ]; then
    ok "spi1/spi2/spi3/spi6 registered"
  else
    bad "expected 4 added SPI controllers"
  fi

  echo "[3b] Tag regions apply (H72x-only + unmodelled DAC1/MDMA)"
  { echo 'mach create "main"'
    echo 'machine LoadPlatformDescription @platforms/g7250_main.repl'
    python3 harness/g7250emu/platform_extras.py
    echo 'echo TAGS_OK'; echo 'quit'; } > "$OUT/smoke_tags.resc"
  if timeout 90 "$RN" --disable-xwt --console -e "path add @$REPO" \
        -e "include @$OUT/smoke_tags.resc" </dev/null 2>&1 | grep -q "TAGS_OK"; then
    ok "TIM23/24, UART9, USART10, DAC1, MDMA tagged"
  else
    bad "Tag regions rejected"
  fi

  echo "[3c] Control platform load: 512 KiB AXI SRAM + 32 MiB SDRAM + SPI1/2"
  cat > "$OUT/smoke_ctrl.resc" <<EOF
mach create "control"
machine LoadPlatformDescription @platforms/g7250_control.repl
sysbus GetRegistrationPoints sdramBank1
peripherals
quit
EOF
  CTRL_OUT="$(timeout 90 "$RN" --disable-xwt --console -e "path add @$REPO" \
        -e "include @$OUT/smoke_ctrl.resc" </dev/null 2>&1)"
  if echo "$CTRL_OUT" | grep -q "<0xC0000000, 0xC1FFFFFF>"; then
    ok "control sdramBank1 = 32 MiB (framebuffer window)"
  else
    bad "control SDRAM not narrowed to 32 MiB"
  fi
  if [ "$(echo "$CTRL_OUT" | grep -cE 'spi[12] \(STM32H7_SPI\)')" -eq 2 ]; then
    ok "control spi1 (W25Qxx) + spi2 (I2S2) registered"
  else
    bad "control expected 2 added SPI controllers"
  fi

  echo "[4] observe end-to-end (log capture + parse)"
  LOG="$OUT/smoke_e2e.log"; : > "$LOG"
  cat > "$OUT/smoke_e2e.resc" <<EOF
mach create "main"
machine LoadPlatformDescription @platforms/g7250_main.repl
logLevel -1 sysbus
sysbus LogAllPeripheralsAccess true
logFile @$LOG
sysbus ReadDoubleWord 0x58024400
sysbus WriteDoubleWord 0x58024400 0x1
sysbus ReadDoubleWord 0x58024800
quit
EOF
  timeout 90 "$RN" --disable-xwt --console -e "path add @$REPO" \
        -e "include @$OUT/smoke_e2e.resc" </dev/null >/dev/null 2>&1
  if python3 harness/g7250emu/observe.py "$LOG" 2>/dev/null | grep -q "^| rcc |"; then
    ok "observe parsed rcc accesses from real log"
  else
    bad "observe did not parse the captured log"
  fi
fi

echo "[5] m1_run.py refuses with no image-map (exit 2)"
( unset G7250_IMAGE_MAP; python3 harness/g7250emu/m1_run.py >/dev/null 2>&1 )
[ $? -eq 2 ] && ok "clean refusal" || bad "expected exit 2"

echo
[ $fail -eq 0 ] && { echo "M1 smoke: ALL PASS"; exit 0; } || { echo "M1 smoke: FAILURES"; exit 1; }
