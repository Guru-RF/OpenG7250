// Minimal STM32H7 MDMA model for the Main (clean-room, from ST RM0468 public
// register map). The stock Main uses the MDMA only with software requests and
// polls for completion, without interrupts (g7250-base docs/dma.md, VERIFIED):
// channel 0-2 word copies in the RX/TX DSP, channel 4 a fill (fixed source,
// incrementing destination) for buffer clears. Without a model the tag returns
// 0, so every poll runs into its timeout and the Main crawls once RX blocks
// arrive (fused FPGA model). This model performs the whole transfer at once
// when CCR.SWRQ is written with CCR.EN set, then sets the completion flags and
// clears EN. Not modelled: hardware triggers, linked lists, repeated-block
// address updates (BRUR), packing between different element sizes beyond a
// byte-wise fallback, interrupts, bus errors.
using System;
using Antmicro.Renode.Core;
using Antmicro.Renode.Logging;
using Antmicro.Renode.Peripherals;
using Antmicro.Renode.Peripherals.Bus;

namespace Antmicro.Renode.Peripherals.DMA
{
    public class G7250Mdma : IDoubleWordPeripheral, IKnownSize
    {
        private const int Channels = 16;
        // per-channel registers at 0x40 + 0x40*x
        private const int ISR = 0x00, IFCR = 0x04, ESR = 0x08, CR = 0x0C, TCR = 0x10,
                          BNDTR = 0x14, SAR = 0x18, DAR = 0x1C, BRUR = 0x20, LAR = 0x24,
                          TBR = 0x28, MAR = 0x30, MDR = 0x34;
        private readonly uint[,] regs = new uint[Channels, 16];
        private readonly IMachine machine;
        private ulong transfers;

        public G7250Mdma(IMachine machine)
        {
            this.machine = machine;
            Reset();
        }

        public long Size { get { return 0x1000; } }

        public void Reset()
        {
            Array.Clear(regs, 0, regs.Length);
            transfers = 0;
        }

        private static bool Decode(long offset, out int ch, out int reg)
        {
            ch = reg = -1;
            if(offset < 0x40) return false;
            ch = (int)((offset - 0x40) / 0x40);
            reg = (int)((offset - 0x40) % 0x40);
            return ch < Channels;
        }

        public uint ReadDoubleWord(long offset)
        {
            if(offset == 0x00) // GISR0: channel x has a pending flag
            {
                uint g = 0;
                for(int c = 0; c < Channels; c++) if((regs[c, ISR / 4] & 0x1F) != 0) g |= 1u << c;
                return g;
            }
            int ch, reg;
            if(!Decode(offset, out ch, out reg)) return 0;
            if(reg == IFCR || reg == ESR) return 0;
            return regs[ch, reg / 4];
        }

        public void WriteDoubleWord(long offset, uint value)
        {
            int ch, reg;
            if(!Decode(offset, out ch, out reg)) return;
            switch(reg)
            {
                case ISR: case ESR: return;                           // read only
                case IFCR: regs[ch, ISR / 4] &= ~(value & 0x1F); return; // clear flags
                case CR:
                    regs[ch, CR / 4] = value & ~(1u << 16);             // SWRQ is write-only
                    if((value & 1u) != 0 && (value & (1u << 16)) != 0) Run(ch);
                    return;
                default:
                    regs[ch, reg / 4] = value; return;
            }
        }

        private void Run(int ch)
        {
            var bus = machine.GetSystemBus(this);
            uint tcr = regs[ch, TCR / 4], bndtr = regs[ch, BNDTR / 4];
            int sinc = (int)(tcr & 3), dinc = (int)((tcr >> 2) & 3);
            int ssize = 1 << (int)((tcr >> 4) & 3), dsize = 1 << (int)((tcr >> 6) & 3);
            int sincos = 1 << (int)((tcr >> 8) & 3), dincos = 1 << (int)((tcr >> 10) & 3);
            uint bndt = bndtr & 0x1FFFF;
            uint blocks = ((bndtr >> 20) & 0xFFF) + 1;
            ulong src = regs[ch, SAR / 4], dst = regs[ch, DAR / 4];
            long sstep = sinc == 2 ? sincos : sinc == 3 ? -sincos : 0;
            long dstep = dinc == 2 ? dincos : dinc == 3 ? -dincos : 0;
            for(uint b = 0; b < blocks; b++)
            {
                if(ssize == dsize)
                {
                    for(uint n = 0; n < bndt / (uint)ssize; n++)
                    {
                        if(ssize == 4) bus.WriteDoubleWord(dst, bus.ReadDoubleWord(src));
                        else if(ssize == 2) bus.WriteWord(dst, bus.ReadWord(src));
                        else if(ssize == 1) bus.WriteByte(dst, bus.ReadByte(src));
                        else { bus.WriteDoubleWord(dst, bus.ReadDoubleWord(src));
                               bus.WriteDoubleWord(dst + 4, bus.ReadDoubleWord(src + 4)); }
                        src = (ulong)((long)src + sstep); dst = (ulong)((long)dst + dstep);
                    }
                }
                else // byte-wise fallback for packing between sizes
                {
                    for(uint n = 0; n < bndt; n++)
                    {
                        bus.WriteByte(dst, bus.ReadByte(src));
                        if(sstep != 0) src = (ulong)((long)src + Math.Sign(sstep));
                        if(dstep != 0) dst = (ulong)((long)dst + Math.Sign(dstep));
                    }
                }
            }
            // completion: CTCIF(1) BRTIF(2) BTIF(3) TCIF(4); EN cleared by hardware
            regs[ch, ISR / 4] |= 0x1E;
            regs[ch, CR / 4] &= ~1u;
            regs[ch, BNDTR / 4] &= ~0x1FFFFu;
            transfers++;
            if((transfers & (transfers - 1)) == 0) // log at 1, 2, 4, 8, ... transfers
                this.Log(LogLevel.Info, "MDMA ch{0}: {1} B x {2} block(s) done (transfer #{3})", ch, bndt, blocks, transfers);
        }
    }
}
