#!/usr/bin/env python3
"""Build the G7250 architecture PDF (A4 portrait).

Inlines the hand-authored SVGs from svg/ into the HTML template
(G7250-architecture.html), writes a self-contained build HTML under
.private/arch/, and renders it to PDF with headless Google Chrome.

Output: ../../.private/arch/G7250-architecture.pdf  (git-ignored)
Nothing is written to the session scratchpad.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SVG_DIR = os.path.join(HERE, "svg")
TEMPLATE = os.path.join(HERE, "G7250-architecture.html")
OUT_DIR = os.path.join(REPO, ".private", "arch")
BUILD_HTML = os.path.join(OUT_DIR, "G7250-architecture.build.html")
PDF = os.path.join(OUT_DIR, "G7250-architecture.pdf")

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def inline_svgs(html):
    def repl(m):
        name = m.group(1).strip()
        path = os.path.join(SVG_DIR, name)
        with open(path, encoding="utf-8") as f:
            svg = f.read()
        # strip the XML prolog if present; keep the <svg> element
        svg = re.sub(r"^<\?xml[^>]*\?>\s*", "", svg)
        return svg
    return re.sub(r"<!--INCLUDE:([^>]+?)-->", repl, html)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()
    html = inline_svgs(html)
    with open(BUILD_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    if not os.path.exists(CHROME):
        sys.exit("Google Chrome not found; install it or use weasyprint as a fallback.")

    cmd = [
        CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
        "--print-to-pdf=" + PDF,
        "--no-margins",
        "file://" + BUILD_HTML,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if not os.path.exists(PDF):
        print(r.stdout)
        print(r.stderr)
        sys.exit("PDF not produced")
    print("PDF:", PDF, os.path.getsize(PDF), "bytes")


if __name__ == "__main__":
    main()
