#!/usr/bin/env python3
"""Run Ghidra headless on prepared G7250 images. Does not execute firmware."""
import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ghidra-dir", type=Path, required=True)
    parser.add_argument("--unit", choices=("main", "control", "both"), default="both")
    parser.add_argument("--output", type=Path, default=ROOT / "analysis/generated")
    parser.add_argument("--function-timeout", type=int, default=10)
    parser.add_argument("--export-only", action="store_true",
                        help="re-export a saved project without importing or analyzing again")
    args = parser.parse_args()
    ghidra = args.ghidra_dir.resolve()
    utility = ghidra / "Ghidra/Framework/Utility/lib/Utility.jar"
    if not utility.is_file():
        parser.error("--ghidra-dir must point to an extracted Ghidra distribution")
    if args.function_timeout < 1:
        parser.error("--function-timeout must be positive")
    output = args.output.resolve()
    project_dir = output / "projects"
    project_dir.mkdir(parents=True, exist_ok=True)
    for unit in ("main", "control") if args.unit == "both" else (args.unit,):
        binary = output / f"{unit}.bin"
        if not binary.is_file():
            parser.error(f"Missing {binary}; run scripts/prepare_firmware.py first")
        if args.export_only and not (project_dir / f"g7250_{unit}.gpr").is_file():
            parser.error(f"No saved Ghidra project for {unit}; run a normal analysis first")
        target = output / unit
        target.mkdir(exist_ok=True)
        summary = target / "export_summary.txt"
        summary.unlink(missing_ok=True)
        # Same Java entry point used by Ghidra's support/launch.sh. Explicit
        # settings/cache paths keep all generated application state under output.
        command = [
            "java", "-Xmx2G", "-XX:ParallelGCThreads=2", "-XX:CICompilerCount=2",
            "-Djava.awt.headless=true", "-Dfile.encoding=UTF8",
            "-Djava.system.class.loader=ghidra.GhidraClassLoader",
            f"-Dapplication.settingsdir={output / 'runtime' / unit / 'settings'}",
            f"-Dapplication.cachedir={output / 'runtime' / unit / 'cache'}",
            f"-Dapplication.tempdir={output / 'runtime' / unit / 'tmp'}",
            "--enable-native-access=ALL-UNNAMED",
            "-cp", str(utility), "ghidra.Ghidra",
            "ghidra.app.util.headless.AnalyzeHeadless", str(project_dir),
            f"g7250_{unit}",
        ]
        if args.export_only:
            command += ["-process", f"{unit}.bin", "-noanalysis"]
        else:
            command += [
                "-import", str(binary), "-overwrite",
                "-loader", "BinaryLoader", "-loader-baseAddr", "0",
                "-processor", "ARM:LE:32:Cortex", "-cspec", "default",
                "-preScript", "ConfigureFirmware.java", unit,
            ]
        command += [
            "-scriptPath", str(ROOT / "scripts/ghidra"),
            "-postScript", "ExportFirmware.java", str(target), str(args.function_timeout),
            "-analysisTimeoutPerFile", "600", "-max-cpu", "4",
            "-log", str(target / "analysis.log"),
            "-scriptlog", str(target / "scripts.log"),
        ]
        print(f"Analyzing {unit}; output: {target}", flush=True)
        subprocess.run(command, check=True)
        if not summary.is_file() or "export_complete\ttrue" not in summary.read_text():
            raise RuntimeError(f"Ghidra did not complete export; inspect {target / 'analysis.log'}")


if __name__ == "__main__":
    main()
