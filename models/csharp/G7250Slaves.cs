// G7250 functional bus slaves (clean-room, compiled into Renode at runtime via
// the monitor `i @models/csharp/G7250Slaves.cs`). Semantics mirror the
// host-tested logic in models/devices/*.py and are traced to the public
// datasheets + g7250-base RE docs (used as data). No stock firmware code.
using System;
using Antmicro.Renode.Peripherals.I2C;
using Antmicro.Renode.Peripherals.SPI;
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

namespace Antmicro.Renode.Peripherals.SPI
{
    // CH394 Ethernet controller (W5500-register-compatible) on SPI6. Clean-room,
    // mirrors models/devices/ch394.py. W5500 SPI frame: [addrHi][addrLo][control]
    // then data; control = (BSB<<3)|(RWB<<2)|OM, RWB bit2 = 1 write / 0 read.
    // We keep a flat per-(block,address) register file and auto-increment within
    // a frame. We log the source IP (SIPR, common block BSB=0, 0x0F..0x12) when
    // the firmware programs it — the A1.12 check that the forced default IP
    // 192.168.3.199 actually reaches the chip.
    public class G7250Ch394 : ISPIPeripheral
    {
        private readonly byte[,] regs = new byte[0x20, 0x200];
        private int phase, bsb, addr; private bool write;
        private const int SIPR = 0x0F;

        public void Reset() { phase = 0; }

        public byte Transmit(byte data)
        {
            byte outb = 0;
            if(phase == 0) { addr = data << 8; phase = 1; }
            else if(phase == 1) { addr |= data; phase = 2; }
            else if(phase == 2)
            {
                bsb = (data >> 3) & 0x1F;
                write = ((data >> 2) & 1) != 0;
                phase = 3;
            }
            else
            {
                int a = addr & 0x1FF;
                if(write) { regs[bsb, a] = data; }
                else { outb = regs[bsb, a]; }
                // log the source IP once the 4th SIPR byte is written
                if(write && bsb == 0 && addr >= SIPR && addr <= SIPR + 3 && addr == SIPR + 3)
                {
                    this.Log(LogLevel.Info, "[CH394 model] source IP set to {0}.{1}.{2}.{3}",
                             regs[0, SIPR], regs[0, SIPR + 1], regs[0, SIPR + 2], regs[0, SIPR + 3]);
                }
                addr++;
            }
            return outb;
        }

        public void FinishTransmission() { phase = 0; }
    }
}

namespace Antmicro.Renode.Peripherals.Miscellaneous
{
    // Headless LTDC stub for the Control: the real Video.STM32LTDC in this build
    // does not implement CDSR (offset 0x48) and never toggles VSYNC headless, so
    // the GUI framebuffer-swap spins forever (docs/M2-control-status.md). We
    // register this in its place (after sysbus UnregisterFromAddress 0x50001000)
    // purely so the boot gets past the VSYNC wait into the GUI service loop; we
    // do not render video. Writes are echoed; CDSR bit0 (VSYNCS) toggles each
    // read so both `while(!(CDSR&1))` and `while(CDSR&1)` complete.
    public class G7250LtdcStub : Antmicro.Renode.Peripherals.Bus.IDoubleWordPeripheral,
                                 Antmicro.Renode.Peripherals.IKnownSize
    {
        private readonly System.Collections.Generic.Dictionary<long, uint> regs =
            new System.Collections.Generic.Dictionary<long, uint>();
        private uint vtick;
        public long Size { get { return 0x1000; } }
        public void Reset() { regs.Clear(); vtick = 0; }
        public uint ReadDoubleWord(long offset)
        {
            if(offset == 0x48) { vtick++; return (vtick & 1u) != 0 ? 0x0Fu : 0x00u; } // CDSR status toggle (VSYNCS/HSYNCS/VDES/HDES)
            uint v; return regs.TryGetValue(offset, out v) ? v : 0u;
        }
        public void WriteDoubleWord(long offset, uint value) { regs[offset] = value; }
    }
}
