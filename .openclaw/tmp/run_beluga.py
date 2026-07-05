#!/usr/bin/env python3
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "live/bigbeluga_paper.py"],
    cwd="/root/.openclaw/workspace-trading/opentrade/",
    capture_output=True,
    text=True,
    timeout=120,
)
out = result.stdout
if len(out) > 2000:
    out = out[-2000:]
print(out, end="")
if result.stderr:
    import os
    print("STDERR:", result.stderr[-1000:], file=sys.stderr, end="")
sys.exit(result.returncode)
