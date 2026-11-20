// PA bias plant and ADC1 metering feed for the Main (clean-room; see
// docs/PA-plant-model.md).
//
// Two parts:
// 1. An SPI2 slave that decodes the bias DAC words (BU2505FV/BU2506FV format) and
//    computes the PA drain current Idd from the bias codes (monotonic, safe at
//    zero; shape as in models/devices/bias_trim_plant.py).
// 2. A metering feed that stands in for ADC1 + circular DMA1 Stream 7: Renode
//    1.17's DMA model does not keep the CIRC bit (one transfer, then NDTR = 0)
//    and its ADC returns wrong raw values, so the firmware's meters stay 0. The
//    feed writes the seven 16-bit scan results into the DMA buffer at
//    0x30003740 in rank order and pulses IRQ 47 (DMA1_Stream7), as a circular
//    DMA does after each scan. The firmware's Stream 7 vector filters the buffer
//    itself before the HAL handler (g7250-base docs/dma.md).
//
// From the analysis (g7250-base, used as data, VERIFIED unless noted): DAC word =
// 4-bit address (bit-reversed channel) << 2 | value bits 9..8, then bits 7..0;
// LD high on PB12 latches; RESET low on PB14 forces all outputs to 0; bias
// channels 2 (driver), 8 (final 1), 7 (final 2); ADC1 rank order INP1 Vext,
// INP2 forward, INP3 reflected, INP4 Idd, INP5 PA NTC, INP8 EALC, INP14 ALC;
// 12-bit; Idd 0.008059 A/LSB; Vext 0.004835 V/LSB (steady state); NTC raw 2047 =
// 25 degC; buffer 0x30003740, 16-bit, IRQ 47.
// Assumed (HYPOTHESIS, placeholders, not measured): static Idd, dead zones and
// gains per stage, Vext 13.8 V, 25 degC, no RF (forward/reflected/ALC 0), and the
// feed rate (1 kHz virtual time).
using Antmicro.Renode.Core;
using Antmicro.Renode.Logging;

namespace Antmicro.Renode.Peripherals.SPI
{
    public class G7250PaPlant : ISPIPeripheral, Antmicro.Renode.Core.IGPIOReceiver
    {
        // HYPOTHESIS: placeholder plant parameters
        private const double StaticIdd = 0.05;                      // A, must stay <= 0.1 A
        private static readonly int[] BiasCh = { 2, 8, 7 };          // driver, final 1, final 2
        private static readonly int[] DeadZone = { 450, 800, 800 };  // DAC codes; targets must lie below the 10-bit clamp (1023)
        private static readonly double[] Gain = { 0.5 / 150, 0.9 / 150, 0.9 / 150 }; // A per code
        private const double VextVolts = 13.8;
        private const uint FeedHz = 1000;
        // from the analysis
        private const double IddPerLsb = 0.008059, VextPerLsb = 0.004835;
        private const int NtcRaw25 = 2047;
        private const ulong Buffer = 0x30003740;

        private readonly IMachine machine;
        private readonly int[] dac = new int[9];
        private readonly byte[] word = new byte[2];
        private int nbytes;
        private bool ldPrev, rstPrev = true;
        private ulong scans;

        public GPIO IRQ { get; private set; }

        public G7250PaPlant(IMachine machine)
        {
            this.machine = machine;
            IRQ = new GPIO();
            var feed = machine.ObtainManagedThread(Scan, FeedHz);
            feed.Start();
            Reset();
        }

        public void Reset()
        {
            for(int i = 0; i < dac.Length; i++) dac[i] = 0;
            nbytes = 0;
        }

        public byte Transmit(byte data)
        {
            word[nbytes & 1] = data;   // keep the last two bytes of the word
            nbytes++;
            return 0;
        }

        public void FinishTransmission() { }

        private static int Reverse4(int v)
        {
            return ((v & 1) << 3) | ((v & 2) << 1) | ((v & 4) >> 1) | ((v & 8) >> 3);
        }

        // GPIO 0 = LD (PB12, rising edge latches), GPIO 1 = RESET (PB14, low clears)
        public void OnGPIO(int number, bool value)
        {
            if(number == 0)
            {
                if(value && !ldPrev && nbytes >= 2)
                {
                    byte hi = word[(nbytes - 2) & 1], lo = word[(nbytes - 1) & 1];
                    int ch = Reverse4((hi >> 2) & 0xF);
                    int val = ((hi & 3) << 8) | lo;
                    if(ch >= 1 && ch <= 8) dac[ch] = val;
                    this.Log(LogLevel.Debug, "DAC ch {0} = {1}, Idd {2:F3} A", ch, val, Idd());
                    nbytes = 0;
                }
                ldPrev = value;
            }
            else if(number == 1)
            {
                if(!value && rstPrev) for(int i = 0; i < dac.Length; i++) dac[i] = 0;
                rstPrev = value;
            }
        }

        private double Idd()
        {
            double i = StaticIdd;
            for(int k = 0; k < BiasCh.Length; k++)
            {
                int above = dac[BiasCh[k]] - DeadZone[k];
                if(above > 0) i += Gain[k] * above;
            }
            return i;
        }

        private static ushort Raw(double raw)
        {
            if(raw < 0) raw = 0;
            if(raw > 4095) raw = 4095;
            return (ushort)(raw + 0.5);
        }

        private void Scan()
        {
            var bus = machine.SystemBus;
            ushort[] rank = {
                Raw(VextVolts / VextPerLsb), // 1 INP1  PA1_C  Vext
                0,                           // 2 INP2  PF11   forward (no RF)
                0,                           // 3 INP3  PA6    reflected
                Raw(Idd() / IddPerLsb),      // 4 INP4  PC4    Idd
                (ushort)NtcRaw25,            // 5 INP5  PB1    PA NTC, 25 degC
                0,                           // 6 INP8  PC5    EALC
                0,                           // 7 INP14 PA2    ALC
            };
            for(int r = 0; r < rank.Length; r++) bus.WriteWord(Buffer + (ulong)(2 * r), rank[r]);
            IRQ.Set(true);
            IRQ.Set(false);
            if((++scans & (scans - 1)) == 0)
                this.Log(LogLevel.Debug, "metering scan #{0}: Idd raw {1}", scans, rank[3]);
        }
    }
}
