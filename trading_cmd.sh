#!/bin/bash
cd /root/.openclaw/workspace-trading/opentrade/live
python3 update_btc_data.py 2>&1
echo "---EXIT CODE: $?---"
cd /root/.openclaw/workspace-trading/opentrade
python3 live/bigbeluga_paper.py 2>&1
echo "---EXIT CODE: $?---"
