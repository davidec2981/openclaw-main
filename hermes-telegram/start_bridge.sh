#!/bin/bash
cd /root/.openclaw/workspace/hermes-telegram
exec python3 bridge.py > /opt/hermes-telegram/bridge.log 2>&1
