import sys, os
os.chdir('/root/.openclaw/workspace-trading/opentrade')
sys.path.insert(0, '/root/.openclaw/workspace-trading/opentrade')
import runpy
result = runpy.run_path('/root/.openclaw/workspace-trading/opentrade/live/bigbeluga_paper.py', run_name='__main__')
# Print any signals/orders that resulted
for k in ('signals', 'orders', 'entry', 'exit'):
    if k in result:
        print(f"{k}: {result[k]}")
