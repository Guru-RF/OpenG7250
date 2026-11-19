// G7250 functional bus slaves (clean-room, compiled into Renode at runtime via
// the monitor `i @models/csharp/G7250Slaves.cs`). Semantics mirror the
// host-tested logic in models/devices/*.py and are traced to the public
// datasheets + g7250-base RE docs (used as data). No stock firmware code.
using System;
using Antmicro.Renode.Peripherals.I2C;
using Antmicro.Renode.Logging;

namespace Antmicro.Renode.Peripherals.I2C
{
    // 24Cxx I2C EEPROM with 16-bit (2-byte) memory addressing. The Main's
    // settings loader treats the 0x1A8-byte block at 0x0000 as valid iff bytes
    // 0x000, 0x1A3 and 0x1A4 are 'd' (0x64) (g7250-base main_unit/docs +
    // OpenG7250 RE). We seed those markers so the boot logs valid settings
    // instead of "[ERR] EEPROM Settings data incorrect". Erased bytes read 0xFF.
    public class G7250Eeprom24C : II2CPeripheral
    {
        private readonly byte[] mem;
        private int pointer;
        private int addrBytesSeen;
        private bool addrPhase;

        public G7250Eeprom24C()
        {
            mem = new byte[0x4000]; // >= 24C128 (highest ref 0x24A8)
            Reset();
        }

        public void Reset()
        {
            for(int i = 0; i < mem.Length; i++) mem[i] = 0xFF;
            // settings block validity markers ('d' = 0x64)
            mem[0x000] = 0x64; mem[0x1A3] = 0x64; mem[0x1A4] = 0x64;
            pointer = 0; addrPhase = true; addrBytesSeen = 0;
        }

        public void Write(byte[] data)
        {
            // Each write transaction begins with the 2-byte memory address,
            // then optional data bytes (auto-incrementing).
            int i = 0;
            if(addrPhase)
            {
                while(i < data.Length && addrBytesSeen < 2)
                {
                    pointer = ((pointer << 8) | data[i]) & (mem.Length - 1);
                    addrBytesSeen++; i++;
                }
                if(addrBytesSeen >= 2) addrPhase = false;
            }
            for(; i < data.Length; i++)
            {
                mem[pointer] = data[i];
                pointer = (pointer + 1) & (mem.Length - 1);
            }
        }

        public byte[] Read(int count)
        {
            var o = new byte[count];
            for(int i = 0; i < count; i++)
            {
                o[i] = mem[pointer];
                pointer = (pointer + 1) & (mem.Length - 1);
            }
            return o;
        }

        public void FinishTransmission()
        {
            // next transaction starts with a fresh address phase
            addrPhase = true; addrBytesSeen = 0;
        }
    }
}
