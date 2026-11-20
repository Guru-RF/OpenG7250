// Fused GPIOE + RF-FPGA model for the Main (clean-room, M3). Replaces the stock
// GPIOE port with a port that ALSO answers the FPGA's 8-bit bit-banged bus
// internally (HIS 80): D0-7=PE0-7, CMD=PE8, STB=PE9, DRDY=PE10. Because the port
// computes IDR itself, it returns the FPGA's data on a read without the
// bidirectional-GPIO / spurious-EXTI problems of wiring a separate peripheral to
// the pins. MODER gives the data direction, so reads vs writes are unambiguous.
// Handles the boot loopback bus-test (cmd 0x00) and the 3-byte version (0x08);
// RX I/Q (0x04) returns a changing counter so the runtime health check is happy.
// Logs every 0x01 configuration frame (the bytes the MCU writes) and every latch of
// the pulse commands 0x05/0x06/0x09/0x0A at Info level, for the HIS-02 NCO probe.
using System.Collections.Generic;
using Antmicro.Renode.Core;
using Antmicro.Renode.Core.Structure;
using Antmicro.Renode.Peripherals;
using Antmicro.Renode.Peripherals.Bus;
using Antmicro.Renode.Logging;

namespace Antmicro.Renode.Peripherals.GPIOPort
{
    public class G7250GpioeFpga : IDoubleWordPeripheral, IKnownSize, INumberedGPIOOutput
    {
        private uint moder, otyper, ospeedr, pupdr, odr, lckr, afrl, afrh;
        private readonly GPIO[] pins;
        private int cmd, readIdx;
        private bool stbPrev, cmdPrev;
        private byte testReg, fpgaOut;
        private uint rx;
        private readonly List<byte> wr = new List<byte>();
        private Antmicro.Renode.Core.IManagedThread drdy;
        private readonly byte[] ver = { 1, 0, 0 };

        public G7250GpioeFpga(IMachine machine)
        {
            pins = new GPIO[16];
            for(int i = 0; i < 16; i++) pins[i] = new GPIO();
            drdy = machine.ObtainManagedThread(() => { pins[10].Set(true); pins[10].Set(false); }, 200);
            drdy.Start();
            Reset();
        }

        public long Size { get { return 0x400; } }

        public IReadOnlyDictionary<int, IGPIO> Connections
        {
            get
            {
                var d = new Dictionary<int, IGPIO>();
                for(int i = 0; i < 16; i++) d[i] = pins[i];
                return d;
            }
        }

        public void Reset()
        {
            moder = otyper = ospeedr = pupdr = odr = lckr = afrl = afrh = 0;
            cmd = readIdx = 0; stbPrev = cmdPrev = false; testReg = fpgaOut = 0; rx = 0;
            wr.Clear();
        }

        private bool IsOutput(int pin) { return ((moder >> (2 * pin)) & 3u) == 1u; }

        private uint PinLevel(int pin)
        {
            if(IsOutput(pin)) return (odr >> pin) & 1u;
            if(pin < 8) return (uint)((fpgaOut >> pin) & 1); // FPGA drives D0-7 on reads
            // other input pins read their pull resistor (PUPDR 01 = pull-up -> 1)
            return ((pupdr >> (2 * pin)) & 3u) == 1u ? 1u : 0u;
        }

        private uint Idr()
        {
            uint v = 0;
            for(int i = 0; i < 16; i++) v |= PinLevel(i) << i;
            return v;
        }

        private byte NextReadByte()
        {
            if(cmd == 0x00) return testReg;                 // loopback
            if(cmd == 0x08) return ver[(readIdx++) % 3];     // version
            if(cmd == 0x04) { rx++; return (byte)(rx & 0xFF); } // RX I/Q (changing)
            if(cmd == 0x02) return (byte)(readIdx++ == 0 ? 0 : 0); // status
            return 0;
        }

        private void ProcessBus()
        {
            bool stb = ((odr >> 9) & 1u) != 0;
            bool cmdPin = ((odr >> 8) & 1u) != 0;
            if(stb && !stbPrev) // STB rising edge
            {
                bool outp = IsOutput(0);
                if(cmdPin)                                                   // latch command
                {
                    FlushFrame();
                    cmd = (int)(odr & 0xFF); readIdx = 0;
                    if(cmd == 0x05 || cmd == 0x06 || cmd == 0x09 || cmd == 0x0A)
                        this.Log(LogLevel.Info, "FPGA pulse cmd 0x{0:X2}", cmd);
                }
                else if(outp)                                                // write
                {
                    if(cmd == 0x00) { testReg = (byte)(odr & 0xFF); fpgaOut = testReg; }
                    else if(cmd == 0x01 && wr.Count < 64) wr.Add((byte)(odr & 0xFF));
                }
                else { fpgaOut = NextReadByte(); }                           // read strobe
            }
            stbPrev = stb; cmdPrev = cmdPin;
        }

        private void FlushFrame()
        {
            if(cmd == 0x01 && wr.Count > 0)
                this.Log(LogLevel.Info, "FPGA cmd 0x01 frame {0} B: {1}", wr.Count,
                         System.BitConverter.ToString(wr.ToArray()).Replace("-", ""));
            wr.Clear();
        }

        private void DriveExti()
        {
            for(int i = 0; i < 16; i++) pins[i].Set(PinLevel(i) != 0);
        }

        public uint ReadDoubleWord(long offset)
        {
            switch(offset)
            {
                case 0x00: return moder;
                case 0x04: return otyper;
                case 0x08: return ospeedr;
                case 0x0C: return pupdr;
                case 0x10: return Idr();
                case 0x14: return odr;
                case 0x1C: return lckr;
                case 0x20: return afrl;
                case 0x24: return afrh;
                default: return 0;
            }
        }

        public void WriteDoubleWord(long offset, uint value)
        {
            switch(offset)
            {
                case 0x00: moder = value; break;
                case 0x04: otyper = value; break;
                case 0x08: ospeedr = value; break;
                case 0x0C: pupdr = value; break;
                case 0x14: odr = value; ProcessBus(); break;
                case 0x18: // BSRR: high 16 reset, low 16 set — SET wins on STM32
                    odr &= ~(value >> 16);
                    odr |= (value & 0xFFFF);
                    ProcessBus(); break;
                case 0x1C: lckr = value; break;
                case 0x20: afrl = value; break;
                case 0x24: afrh = value; break;
            }
        }
    }
}
