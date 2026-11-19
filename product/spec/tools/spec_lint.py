#!/usr/bin/env python3
"""Lint for the G7250-P2 spec (rc1 definition of done, checks 1, 2, 4, 5).

Checks over spec/*.md:
  L1  no "pending 0xxx" left
  L2  every "TBD" carries a HIS id (HIS-nn) or "G6" on the same line
  L3  every referenced decision number (0001..0099 in decision context) exists in decisions/
  L4  every referenced HIS-nn exists in open-questions-his.md
  L5  every paragraph or table row with MUST/SHOULD/MAY (upper case, RFC 2119) cites a source:
      [KEY], a decision number, or a section reference "Bn"/"An"/"Cn"
  L6  conformance test ids (T-...) are unique across the spec
  L7  register names used in the spec exist in spec/register-map.yaml (if that file exists)

Run from product/spec:  python3 tools/spec_lint.py    (exit 1 on any finding)
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = sorted((ROOT / "spec").glob("*.md"))
DECISIONS = {p.name[:4] for p in (ROOT / "decisions").glob("[0-9][0-9][0-9][0-9]-*.md")}
HIS_IDS = set(re.findall(r"### (HIS-\d\d)", (ROOT / "open-questions-his.md").read_text()))
REGMAP = ROOT / "spec" / "register-map.yaml"

RE_NORM = re.compile(r"\b(MUST|SHOULD|MAY|REQUIRED|SHALL)\b")
RE_CITE = re.compile(r"\[[A-Z][A-Za-z0-9.\-]+\]|\b00[0-9]{2}\b|\b[ABC]\d{1,2}(\.\d+)?\b|\bHIS-\d\d\b|RFC ?\d{3,4}")
RE_DEC = re.compile(r"(?<![\d.x])(00[0-9]{2})(?![\d.x])")
RE_HIS = re.compile(r"\bHIS-(\d\d)\b")
RE_TEST = re.compile(r"\b(T-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{2,3})\b")
RE_REG = re.compile(r"`([A-Z][A-Z0-9]*_[A-Z0-9_]+)`")


def blocks(text):
    """Paragraphs; table rows count as their own block."""
    out, cur = [], []
    for line in text.splitlines():
        if line.startswith("|"):
            if cur:
                out.append(" ".join(cur)); cur = []
            out.append(line)
        elif not line.strip():
            if cur:
                out.append(" ".join(cur)); cur = []
        else:
            cur.append(line)
    if cur:
        out.append(" ".join(cur))
    return out


def main():
    findings = []
    tests = {}
    regnames = None
    if REGMAP.exists():
        regnames = set(re.findall(r"^\s*-?\s*name:\s*([A-Z][A-Z0-9_]+)", REGMAP.read_text(), re.M))
    for path in SPEC:
        text = path.read_text()
        rel = path.relative_to(ROOT)
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(r"pending 00\d\d", line, re.I):
                findings.append(f"L1 {rel}:{i}: 'pending' left: {line.strip()[:90]}")
            if "TBD" in line and not re.search(r"HIS-\d\d|\bG6\b", line):
                findings.append(f"L2 {rel}:{i}: TBD without HIS id: {line.strip()[:90]}")
            for d in RE_DEC.findall(line):
                if d not in DECISIONS and not re.search(r"0x|port|byte|\d{4,}", line[:0]):
                    # ignore obvious non-decision numbers such as ports 0035 do not occur; keep strict
                    findings.append(f"L3 {rel}:{i}: decision {d} does not exist")
            for h in RE_HIS.findall(line):
                if f"HIS-{h}" not in HIS_IDS:
                    findings.append(f"L4 {rel}:{i}: HIS-{h} not in open-questions-his.md")
            for t in RE_TEST.findall(line):
                if line.lstrip().startswith("|") or line.lstrip().startswith("-"):
                    if t in tests and tests[t] != (rel, i):
                        findings.append(f"L6 {rel}:{i}: test id {t} also at {tests[t][0]}:{tests[t][1]}")
                    tests.setdefault(t, (rel, i))
            if regnames is not None:
                for r in RE_REG.findall(line):
                    if r not in regnames:
                        findings.append(f"L7 {rel}:{i}: register {r} not in register-map.yaml")
        for b in blocks(text):
            if RE_NORM.search(b) and not RE_CITE.search(b) and not b.lstrip().startswith("#"):
                if "RFC 2119" in b or "BCP 14" in b:
                    continue
                findings.append(f"L5 {rel}: normative text without a source: {b.strip()[:100]}")
    for f in findings:
        print(f)
    print(f"\n{len(findings)} finding(s) in {len(SPEC)} file(s); {len(tests)} test id(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
