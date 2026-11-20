// Prepare the two known G7250 v1.0.1 application images for static analysis.
// @category G7250
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.data.DWordDataType;
import ghidra.program.model.lang.Register;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.SourceType;
import java.io.ByteArrayInputStream;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.Set;

public class ConfigureFirmware extends GhidraScript {
    private static final long BASE = 0x08020000L;

    private void region(String name, long start, long size, boolean execute, boolean vol) throws Exception {
        MemoryBlock b = currentProgram.getMemory().createUninitializedBlock(name, toAddr(start), size, false);
        b.setRead(true);
        b.setWrite(true);
        b.setExecute(execute);
        b.setVolatile(vol);
    }

    private void function(long address, String name) throws Exception {
        Address a = toAddr(address & ~1L);
        disassemble(a);
        Function f = getFunctionAt(a);
        if (f == null) f = createFunction(a, name);
        if (f != null) f.setName(name, SourceType.USER_DEFINED);
        currentProgram.getSymbolTable().addExternalEntryPoint(a);
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1 || !(args[0].equals("control") || args[0].equals("main")))
            throw new IllegalArgumentException("Expected control or main");
        boolean control = args[0].equals("control");
        Memory mem = currentProgram.getMemory();
        Address base = toAddr(BASE);
        // Import at zero, then relocate before any RAM/peripheral blocks exist.
        // setImageBase moves existing blocks even when its commit argument is false.
        currentProgram.setImageBase(base, true);
        MemoryBlock flash = mem.getBlock(base);
        if (flash == null || !flash.getStart().equals(base))
            throw new IllegalArgumentException("Import raw binary at zero before running this script");
        long expectedSp = control ? 0x24080000L : 0x24050000L;
        long expectedReset = control ? 0x080235adL : 0x08024555L;
        if (Integer.toUnsignedLong(mem.getInt(base)) != expectedSp ||
            Integer.toUnsignedLong(mem.getInt(base.add(4))) != expectedReset)
            throw new IllegalArgumentException("Image does not match known v1.0.1 vectors");
        flash.setName("FLASH_APP");
        flash.setRead(true);
        flash.setWrite(false);
        flash.setExecute(true);
        Register thumb = currentProgram.getRegister("TMode");
        currentProgram.getProgramContext().setValue(thumb, flash.getStart(), flash.getEnd(), BigInteger.ONE);

        // Restore the startup .data copy into a writable RAM segment. These values
        // are taken from the reset-handler literal pools, not guessed from strings.
        int dataSize = control ? 0x1698 : 0x4c58;
        long dataSource = control ? 0x080dd568L : 0x0808486cL;
        byte[] data = new byte[dataSize];
        mem.getBytes(toAddr(dataSource), data);
        MemoryBlock ramData = mem.createInitializedBlock("AXI_DATA", toAddr(0x24000000L),
            new ByteArrayInputStream(data), data.length, monitor, false);
        ramData.setRead(true); ramData.setWrite(true); ramData.setExecute(false);
        region("AXI_RAM", 0x24000000L + dataSize, expectedSp - 0x24000000L - dataSize, false, false);
        region("ITCM", 0, 0x10000, true, false);
        region("DTCM", 0x20000000L, 0x20000, false, false);
        region("D2_SRAM", 0x30000000L, control ? 0x48000 : 0x8000, false, false);
        region("D3_SRAM", 0x38000000L, control ? 0x10000 : 0x4000, false, false);
        region("BACKUP_SRAM", 0x38800000L, 0x1000, false, false);
        region("PERIPHERAL_WINDOW", 0x40000000L, 0x20000000L, false, true);
        region("CORTEX_SYSTEM", 0xe0000000L, 0x100000L, false, true);
        // Control firmware configures an MPU region at 0xc0000000 of 32 MiB.
        // This is an address window, not a verified measurement of fitted RAM.
        if (control) region("EXTERNAL_RAM_WINDOW_INFERRED", 0xc0000000L, 0x2000000L, false, false);

        String[] core = {"Initial_SP", "Reset_Handler", "NMI_Handler", "HardFault_Handler",
            "MemManage_Handler", "BusFault_Handler", "UsageFault_Handler", "Reserved7",
            "Reserved8", "Reserved9", "Reserved10", "SVC_Handler", "DebugMon_Handler",
            "Reserved13", "PendSV_Handler", "SysTick_Handler"};
        int count = control ? 166 : 179;
        Set<Long> seen = new HashSet<>();
        createLabel(base, "application_vector_table", true);
        for (int i = 0; i < count; i++) {
            Address slot = base.add(i * 4L);
            createData(slot, DWordDataType.dataType);
            long target = Integer.toUnsignedLong(mem.getInt(slot));
            String name = i < 16 ? core[i] : "IRQ_" + (i - 16) + "_Handler";
            setEOLComment(slot, name + " = " + String.format("0x%08x", target));
            if (i > 0 && (target & 1) != 0 && target >= BASE && target <= flash.getEnd().getOffset()) {
                if (seen.add(target)) function(target, name);
            }
        }
        function(BASE + (control ? 0x1e74 : 0x239c), "app_main_inferred");
        if (!control) {
            // Six Thumb callback pointers at 0x08081924; automatic discovery
            // misses these because the caller invokes them indirectly.
            long[] callbacks = {0x080504e8L, 0x0804f094L, 0x0804edf0L,
                0x0804ed18L, 0x0804f604L, 0x0804ede0L};
            for (int i = 0; i < callbacks.length; i++)
                function(callbacks[i], i == 0 ? "wfv_civ_dispatch_inferred" : "wfv_callback_" + i + "_inferred");
            function(0x08041ef4L, "controller_link_service_inferred");
            // DSP audio callbacks registered by 0x08052930. These entry points
            // are also reached indirectly and need explicit function creation.
            function(0x0804eb84L, "wfv_rx_audio_capture_inferred");
            function(0x0804ec5cL, "wfv_tx_audio_consume_inferred");
        }
        setPlateComment(base, "G7250 v1.0.1 decrypted application. Raw load base 0x08020000.\n" +
            "RAM and peripheral mappings are analysis aids, not an emulated board.\n" +
            "User-assigned function names are inferred; no original debug symbols are present.");
        println("Configured " + args[0] + ": " + count + " vector entries, " + seen.size() + " unique handlers");
    }
}
