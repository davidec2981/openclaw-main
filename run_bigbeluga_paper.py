#!/usr/bin/env python3
import sys, os
sys.path.insert(0, '/root/.openclaw/workspace-trading/opentrade/live')
os.chdir('/root/.openclaw/workspace-trading/opentrade')
# Set __file__ so the script can compute BASE
script_path = '/root/.openclaw/workspace-trading/opentrade/live/bigbeluga_paper.py'
exec(compile(open(script_path).read(), script_path, 'exec'), {'__file__': script_path, '__name__': '__main__'})
