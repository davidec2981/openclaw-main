#!/usr/bin/env bash
set -e
cd /root/.openclaw/workspace-trading/opentrade
python3 live/update_btc_data.py
echo "=== BTC DATA UPDATE DONE ==="
python3 live/bigbeluga_paper.py
echo "=== BIGBELUGA PAPER DONE ==="
