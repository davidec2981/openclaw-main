#!/usr/bin/env python3
"""
Hermes Agent ↔ Telegram Bridge
Relays Telegram messages to Hermes Agent and sends responses back.
"""
import json
import logging
import os
import re
import subprocess
import sys
import time

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("hermes-bridge")

# === Config ===
TELEGRAM_TOKEN = "8910858419:AAHtCTeJdgRU5vPjgNr_CWplkkvN9QC-Nps"
HERMES_API = "http://localhost:8081"
ALLOWED_USER_IDS = [951887934]
DEEPSEEK_KEY = "sk-567…70da"

TG_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
last_update_id = 0


def tg_send(chat_id, text, reply_to=None):
    url = f"{TG_API}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            log.warning(f"send error: {r.status_code} {r.text[:200]}")
    except Exception as e:
        log.error(f"send failed: {e}")


def clean_ansi(text):
    text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
    text = re.sub(r'\x1b\][0-9;]*[^\x1b]*\x1b\\', '', text)
    return text


def run_hermes(prompt):
    """Send a prompt to Hermes Agent via CLI."""
    try:
        env = os.environ.copy()
        env["DEEPSEEK_API_KEY"] = DEEPSEEK_KEY
        env["HERMES_DEFAULT_PROVIDER"] = "custom"
        env["HERMES_DEFAULT_MODEL"] = "deepseek/deepseek-v4-pro"
        env["PYTHONUNBUFFERED"] = "1"

        result = subprocess.run(
            [
                "docker", "exec", "-i", "hermes-agent",
                "/opt/hermes/.venv/bin/python3", "/opt/hermes/cli.py",
                "--non-interactive",
            ],
            input=prompt.encode("utf-8"),
            capture_output=True,
            timeout=120,
            env=env,
        )
        stdout = result.stdout.decode("utf-8", errors="replace")
        stderr = result.stderr.decode("utf-8", errors="replace")

        stdout = clean_ansi(stdout)
        stderr = clean_ansi(stderr)

        # Extract response - skip hermes UI boilerplate
        lines = stdout.split('\n')
        clean = []
        skip_patterns = [
            '❯', '─', 'ctx', 'Welcome to Hermes', 'Tip:', '⚠', '⚕',
            'tools', 'skills', '/help', 'Quick commands',
        ]
        for l in lines:
            stripped = l.strip()
            if not stripped:
                continue
            if any(p in stripped for p in skip_patterns):
                continue
            if stripped == prompt.strip():
                continue
            clean.append(stripped)

        if not clean:
            return "✅ Eseguito (nessun output testuale)."

        response = "\n".join(clean[-30:])
        if len(response) > 4000:
            response = response[:3997] + "..."

        return response

    except subprocess.TimeoutExpired:
        return "⏱️ Timeout (120s). Hermes ci sta ancora lavorando."
    except Exception as e:
        log.error(f"Hermes error: {e}")
        return f"❌ Errore: {str(e)[:200]}"


def process_update(update):
    global last_update_id
    if "message" not in update:
        return

    msg = update["message"]
    chat_id = msg["chat"]["id"]
    user_id = msg.get("from", {}).get("id", 0)
    text = msg.get("text", "")
    msg_id = msg["message_id"]
    last_update_id = update["update_id"]

    if user_id not in ALLOWED_USER_IDS:
        return
    if not text:
        return

    cmd = text.split()[0].lower()

    if cmd == "/start":
        tg_send(chat_id,
                "👋 *Hermes Bridge*\n\n"
                "Invia un messaggio → Hermes Agent.\n"
                "`/status` — Stato\n"
                "`/restart` — Riavvio",
                reply_to=msg_id)
        return

    if cmd == "/status":
        try:
            r = requests.get(f"{HERMES_API}/health", timeout=5)
            st = "✅ Online" if r.status_code == 200 else f"⚠️ {r.status_code}"
        except:
            st = "❌ Offline"
        tg_send(chat_id, f"*Hermes:* {st}\n*Model:* deepseek-v4-pro", reply_to=msg_id)
        return

    if cmd == "/restart":
        tg_send(chat_id, "🔄 Riavvio...", reply_to=msg_id)
        subprocess.run(["docker", "restart", "hermes-agent"], timeout=30)
        time.sleep(3)
        tg_send(chat_id, "✅ Riavviato.", reply_to=msg_id)
        return

    log.info(f"→ Hermes: {text[:80]}...")
    tg_send(chat_id, "⏳ Hermes sta pensando...", reply_to=msg_id)

    response = run_hermes(text)
    tg_send(chat_id, response, reply_to=msg_id)


def main():
    log.info("Starting Hermes ↔ Telegram bridge...")

    r = requests.get(f"{TG_API}/getMe", timeout=10)
    if r.status_code == 200:
        bot = r.json().get("result", {})
        log.info(f"Bot: @{bot.get('username')}")
    else:
        log.error(f"Token fail: {r.text}")
        sys.exit(1)

    global last_update_id
    while True:
        try:
            url = f"{TG_API}/getUpdates"
            params = {"offset": last_update_id + 1, "timeout": 30,
                       "allowed_updates": json.dumps(["message"])}
            r = requests.get(url, params=params, timeout=35)
            if r.status_code != 200:
                time.sleep(5)
                continue
            data = r.json()
            if not data.get("ok"):
                time.sleep(5)
                continue
            for update in data.get("result", []):
                process_update(update)
        except requests.exceptions.Timeout:
            pass
        except Exception as e:
            log.error(f"Poll error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
