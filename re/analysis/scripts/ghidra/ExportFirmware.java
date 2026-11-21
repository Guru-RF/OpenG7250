// Export pseudocode, function inventory, and recognized string references.
// Run after analysis: -postScript ExportFirmware.java OUTPUT_DIR [TIMEOUT_SECONDS]
// This script only reads the Ghidra program; it does not rename or patch anything.
// @category OpenG7250

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.LinkedHashMap;
import java.util.Map;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileOptions;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.decompiler.DecompiledFunction;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressIterator;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.data.StringDataInstance;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.DataIterator;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.util.exception.CancelledException;

public class ExportFirmware extends GhidraScript {
    private final Map<String, Long> counts = new LinkedHashMap<>();
    private Path output;
    private int timeoutSeconds;

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (currentProgram == null || args.length < 1 || args.length > 2) {
            throw new IllegalArgumentException(
                "Usage: ExportFirmware.java OUTPUT_DIR [TIMEOUT_SECONDS]; requires an open program");
        }
        output = Paths.get(args[0]).toAbsolutePath().normalize();
        timeoutSeconds = args.length == 2 ? Integer.parseInt(args[1]) : 30;
        if (timeoutSeconds < 1) {
            throw new IllegalArgumentException("TIMEOUT_SECONDS must be positive");
        }
        Files.createDirectories(output);
        long started = System.nanoTime();
        boolean complete = false;
        String fatalError = "";
        try {
            exportFunctions();
            exportStrings();
            complete = true;
        }
        catch (Exception e) {
            fatalError = e.toString();
            throw e;
        }
        finally {
            writeSummary(complete, fatalError, (System.nanoTime() - started) / 1_000_000);
        }
        println("Firmware export: " + output + " " + counts);
    }

    private BufferedWriter writer(String filename) throws IOException {
        return Files.newBufferedWriter(output.resolve(filename), StandardCharsets.UTF_8);
    }

    // TSV fields escape control characters so each record stays on one physical line.
    private static String field(Object value) {
        return value == null ? "" : value.toString().replace("\\", "\\\\")
            .replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")
            .replace("\u0000", "\\0");
    }

    private static String comment(Object value) {
        return field(value).replace("*/", "* /");
    }

    private static void row(BufferedWriter out, Object... values) throws IOException {
        for (int i = 0; i < values.length; i++) {
            if (i != 0) out.write('\t');
            out.write(field(values[i]));
        }
        out.newLine();
    }

    private void increment(String key) {
        counts.put(key, counts.getOrDefault(key, 0L) + 1);
    }

    private void exportFunctions() throws Exception {
        DecompInterface decompiler = new DecompInterface();
        try (BufferedWriter code = writer("decompiled.c");
             BufferedWriter index = writer("functions.tsv");
             BufferedWriter errors = writer("decompile_errors.tsv")) {
            code.write("/* Ghidra reconstruction for static research, not original source.\n" +
                " * Types, names, boundaries, and control flow may be inferred incorrectly.\n" +
                " * This file is not expected to compile or produce flashable firmware.\n" +
                " * Program: " + comment(currentProgram.getName()) + "\n" +
                " * Language: " + comment(currentProgram.getLanguageID()) + "\n" +
                " * Image base: " + currentProgram.getImageBase() + "\n */\n\n");
            row(index, "entry", "name", "body_min", "body_max", "body_bytes",
                "thunk", "status", "elapsed_ms", "signature", "message");
            row(errors, "entry", "name", "status", "message");
            DecompileOptions options = new DecompileOptions();
            options.grabFromProgram(currentProgram);
            decompiler.setOptions(options);
            decompiler.toggleCCode(true);
            decompiler.toggleSyntaxTree(false);
            if (!decompiler.openProgram(currentProgram)) {
                throw new IOException("Cannot start decompiler: " + decompiler.getLastMessage());
            }
            FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
            while (functions.hasNext()) {
                monitor.checkCancelled();
                Function function = functions.next();
                increment("functions_seen");
                String status = "failed";
                String message = "";
                String signature = function.getPrototypeString(false, false);
                long started = System.nanoTime();
                String body = null;
                try {
                    DecompileResults result =
                        decompiler.decompileFunction(function, timeoutSeconds, monitor);
                    monitor.checkCancelled();
                    if (result == null) {
                        message = "Decompiler returned null: " + decompiler.getLastMessage();
                    }
                    else {
                        message = result.getErrorMessage();
                        DecompiledFunction compiled = result.getDecompiledFunction();
                        if (result.decompileCompleted() && compiled != null) {
                            status = "ok";
                            signature = compiled.getSignature();
                            body = compiled.getC();
                        }
                        else if (result.isTimedOut()) {
                            status = "timeout";
                        }
                    }
                }
                catch (CancelledException e) {
                    throw e;
                }
                catch (RuntimeException e) {
                    message = e.toString();
                }
                long elapsed = (System.nanoTime() - started) / 1_000_000;
                increment("functions_" + status);
                code.write("/* Function " + function.getEntryPoint() + ": " +
                    comment(function.getName()) + "; status=" + status + " */\n");
                if (message != null && !message.isEmpty()) {
                    code.write("/* Decompiler message: " + comment(message) + " */\n");
                    row(errors, function.getEntryPoint(), function.getName(), status, message);
                    increment("functions_with_messages");
                }
                else if (!"ok".equals(status)) {
                    row(errors, function.getEntryPoint(), function.getName(), status,
                        "No diagnostic from decompiler");
                }
                if (body != null) code.write(body);
                code.write("\n\n");
                row(index, function.getEntryPoint(), function.getName(),
                    function.getBody().getMinAddress(), function.getBody().getMaxAddress(),
                    function.getBody().getNumAddresses(), function.isThunk(), status,
                    elapsed, signature, message);
                if (counts.get("functions_seen") % 100 == 0) {
                    println("Exported " + counts.get("functions_seen") + " functions");
                    code.flush();
                    index.flush();
                    errors.flush();
                }
            }
        }
        finally {
            decompiler.dispose();
        }
    }

    private void exportStrings() throws Exception {
        try (BufferedWriter strings = writer("strings.tsv");
             BufferedWriter refs = writer("string_xrefs.tsv")) {
            row(strings, "address", "byte_length", "data_type", "value");
            row(refs, "string_address", "target_address", "from_address", "from_function_entry",
                "from_function", "reference_type", "operand_index", "value");
            DataIterator data = currentProgram.getListing().getDefinedData(true);
            while (data.hasNext()) {
                monitor.checkCancelled();
                Data item = data.next();
                if (!item.hasStringValue()) continue;
                String value = StringDataInstance.getStringDataInstance(item).getStringValue();
                row(strings, item.getAddress(), item.getLength(), item.getDataType().getName(), value);
                increment("strings");
                // Include references into the middle of a string, not only its first byte.
                AddressIterator targets = currentProgram.getReferenceManager()
                    .getReferenceDestinationIterator(
                        new AddressSet(item.getMinAddress(), item.getMaxAddress()), true);
                while (targets.hasNext()) {
                    Address target = targets.next();
                    ReferenceIterator references = currentProgram.getReferenceManager()
                        .getReferencesTo(target);
                    while (references.hasNext()) {
                        monitor.checkCancelled();
                        Reference reference = references.next();
                        Function owner = currentProgram.getFunctionManager()
                            .getFunctionContaining(reference.getFromAddress());
                        row(refs, item.getAddress(), target, reference.getFromAddress(),
                            owner == null ? "" : owner.getEntryPoint(),
                            owner == null ? "" : owner.getName(), reference.getReferenceType(),
                            reference.getOperandIndex(), value);
                        increment("string_xrefs");
                    }
                }
            }
        }
    }

    private void writeSummary(boolean complete, String error, long elapsedMs) throws IOException {
        try (BufferedWriter out = writer("export_summary.txt")) {
            row(out, "program", currentProgram.getName());
            row(out, "language", currentProgram.getLanguageID());
            row(out, "compiler_spec", currentProgram.getCompilerSpec().getCompilerSpecID());
            row(out, "image_base", currentProgram.getImageBase());
            row(out, "timeout_seconds_per_function", timeoutSeconds);
            row(out, "export_complete", complete);
            row(out, "fatal_error", error);
            row(out, "elapsed_ms", elapsedMs);
            for (Map.Entry<String, Long> entry : counts.entrySet()) {
                row(out, entry.getKey(), entry.getValue());
            }
            row(out, "scope", "Functions and top-level strings recognized in the analyzed program; " +
                "direct string references, including offcuts. Missing functions/strings and " +
                "indirect pointer chains are not recovered by this export.");
            row(out, "tsv_escaping", "Backslash, tab, CR, LF, and NUL are backslash-escaped.");
        }
    }
}
