#!/usr/bin/env python3
"""Wrapper to run bigbeluga_paper.py safely."""
import subprocess, sys

result = subprocess.run(
    [sys.executable, "/root/.openclaw/workspace-trading/opentrade/live/bigbeluga_paper.py"],
    cwd="/root/.openclaw/workspace-trading/opentrade",
    capture_output=True, text=True, timeout=120
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr, file=sys.stderr)
sys.exit(result.returncode)
