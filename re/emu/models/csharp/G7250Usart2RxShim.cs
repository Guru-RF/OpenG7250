// USART2 RX shim for the Main (clean-room; see docs/USART2-RX-shim.md).
//
// The Main receives the Control link on USART2 through circular DMA1 Stream 2
// into a 1 KiB ring and drains it using the DMA counter (position = size -
// NDTR) (g7250-base docs/protocol.md "Transport", docs/dma.md; VERIFIED).
// Renode 1.17's DMA keeps no circular mode and delivers no USART2 RX bytes to
// the stream (NDTR stays at 0x400). This shim is the UART endpoint for a
// terminal (connector Connect sysbus.u2rx <terminal>): each received byte is
// written into the ring at the current position (ring base from DMA1 S2 M0AR,
// size from the first NDTR value), and NDTR is updated the way a circular DMA
// does. The Main's own USART2 still does the transmit side. Not modelled:
// half/complete-transfer interrupts (the firmware does not use them for RX),
// overrun, line errors.
using System;
using Antmicro.Renode.Core;
using Antmicro.Renode.Logging;
using Antmicro.Renode.Peripherals.Bus;
using Antmicro.Renode.Peripherals.UART;

namespace Antmicro.Renode.Peripherals.UART
{
    public class G7250Usart2RxShim : IUART, IDoubleWordPeripheral, IKnownSize
    {
        private const ulong Dma1 = 0x40020000;
        private const ulong S2Ndtr = Dma1 + 0x10 + 0x18 * 2 + 0x04;
        private const ulong S2M0ar = Dma1 + 0x10 + 0x18 * 2 + 0x0C;
        private readonly IMachine machine;
        private ulong ring;
        private uint size, pos, received;

        public G7250Usart2RxShim(IMachine machine)
        {
            this.machine = machine;
            Reset();
        }

        public long Size { get { return 0x10; } }
        public uint BaudRate { get { return 460800; } }
        public Bits StopBits { get { return Bits.One; } }
        public Parity ParityBit { get { return Parity.None; } }
#pragma warning disable 67
        public event Action<byte> CharReceived;
#pragma warning restore 67

        public void Reset() { ring = 0; size = 0; pos = 0; received = 0; }

        // a few read-only status words for debugging: 0 position, 4 size, 8 bytes received
        public uint ReadDoubleWord(long offset)
        {
            switch(offset) { case 0: return pos; case 4: return size; case 8: return received; default: return 0; }
        }

        public void WriteDoubleWord(long offset, uint value) { }

        public void WriteChar(byte value)
        {
            var bus = machine.SystemBus;
            if(size == 0)
            {
                ring = bus.ReadDoubleWord(S2M0ar);
                size = bus.ReadDoubleWord(S2Ndtr) & 0xFFFF;
                if(ring == 0 || size == 0) { size = 0; return; }   // stream not set up yet: drop
                pos = 0;
                this.Log(LogLevel.Info, "USART2 RX ring at 0x{0:X8}, {1} B", ring, size);
            }
            bus.WriteByte(ring + pos, value);
            pos = (pos + 1) % size;
            bus.WriteDoubleWord(S2Ndtr, size - pos);   // circular: NDTR counts down and wraps to size
            received++;
            if((received & (received - 1)) == 0)
                this.Log(LogLevel.Info, "USART2 RX shim: {0} bytes delivered", received);
        }
    }
}
