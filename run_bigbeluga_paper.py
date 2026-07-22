#!/usr/bin/env python3
import subprocess, sys
r = subprocess.run(
    ["python3", "live/bigbeluga_paper.py"],
    cwd="/root/.openclaw/workspace-trading/opentrade",
    capture_output=True, text=True, timeout=120
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr, file=sys.stderr)
sys.exit(r.returncode)
