# M0 spike firmware build (clean-room). Output -> gitignored .private/m0/.

CROSS   ?= arm-none-eabi-
CC       = $(CROSS)gcc
OBJCOPY  = $(CROSS)objcopy
SIZE     = $(CROSS)size

OUT      = ../../.private/m0
TARGET   = $(OUT)/m0_test

# Cortex-M7 with the double-precision FPU (fpv5-d16): the dp-FPU is exactly
# what M0 must prove the Renode model supports.
ARCH     = -mcpu=cortex-m7 -mthumb -mfpu=fpv5-d16 -mfloat-abi=hard
CFLAGS   = $(ARCH) -O2 -g3 -ffreestanding -fno-common -Wall -Wextra \
           -ffunction-sections -fdata-sections
LDFLAGS  = $(ARCH) -T m0.ld -nostdlib -Wl,--gc-sections -Wl,-Map,$(TARGET).map

.PHONY: all clean
all: $(TARGET).elf

$(OUT):
	mkdir -p $(OUT)

$(TARGET).elf: m0_test.c m0.ld | $(OUT)
	$(CC) $(CFLAGS) $(LDFLAGS) m0_test.c -o $@
	$(OBJCOPY) -O binary $@ $(TARGET).bin
	$(SIZE) $@

clean:
	rm -f $(TARGET).elf $(TARGET).bin $(TARGET).map
