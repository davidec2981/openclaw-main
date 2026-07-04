# 🆘 Guida Recovery — Ripristino da GitHub

Se perdi contatto con me (gateway crash, server resettato, o altro), ecco come riprendere tutto.

## 1. Installare OpenClaw

```bash
npm install -g openclaw
```

## 2. Clonare TUTTI i workspace

```bash
# Crea la directory root
mkdir -p ~/.openclaw && cd ~/.openclaw

# Clona uno per uno
git clone https://github.com/davidec2981/openclaw-main.git workspace
git clone https://github.com/davidec2981/openclaw-trading.git workspace-trading
git clone https://github.com/davidec2981/openclaw-farmer.git workspace-farmer
git clone https://github.com/davidec2981/openclaw-airdrop.git workspace-airdrop
git clone https://github.com/davidec2981/openclaw-pfa.git workspace-pfa
git clone https://github.com/davidec2981/openclaw-polyclaw.git workspace-polyclaw
git clone https://github.com/davidec2981/openclaw-wpclaw.git workspace-wpclaw
git clone https://github.com/davidec2981/openclaw-aihf.git workspace-aihf
git clone https://github.com/davidec2981/openclaw-attestations.git workspace-attestations
git clone https://github.com/davidec2981/openclaw-robocop.git workspace-robocop
```

## 3. Avviare il Gateway

```bash
cd ~/.openclaw
openclaw gateway start
```

Il gateway cercherà i workspace nella directory `~/.openclaw/workspace-*` e rileverà la configurazione.

## 4. Cosa NON è su GitHub (e va ricreato)

- **Bot token Telegram** — da BotFather, va reinserito in config
- **OpenRouter API key** — da openrouter.ai/settings/keys
- **File `.env` o `openclaw.json`** con secrets vari
- **Wallet privati / chiavi** per airdrop farming

Tutto il resto (config, memoria, strategies, cron jobs) è nei repo.

## 5. Cron jobs da ricreare (se perduti)

Dopo il restore, ricontrolla i cron con: `"listami i cron jobs"`.  
Quelli importanti:

| Cron | Schedule | Cosa fa |
|------|----------|---------|
| BigBeluga | `:05 ogni ora` | Forward test BTC 1h |
| Git Backup | `08:00 ogni giorno` | Pusha tutti i workspace |
| Memory Dreaming | `ogni 6h` | Memory maintenance |
| Session Cleanup | `1x al giorno` | Pulisce sessioni vecchie |
| Robocop Audit | `1x al giorno` | Health check notturno |

## 6. Systemd (auto-restart)

Se vuoi che il gateway riparta da solo dopo reboot/crash:

```bash
# Crea il service
cat > /etc/systemd/system/openclaw-gateway.service << 'EOF'
[Unit]
Description=OpenClaw Gateway
After=network.target

[Service]
Type=simple
ExecStart=$(which openclaw) gateway start
ExecStop=$(which openclaw) gateway stop
Restart=on-failure
RestartSec=60
StartLimitBurst=3
StartLimitIntervalSec=300
User=root
WorkingDirectory=/root/.openclaw
Environment=PATH=$(which openclaw | xargs dirname):/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable openclaw-gateway
systemctl start openclaw-gateway
```

## 7. Contattarmi dopo il ripristino

Dopo aver avviato il gateway, mandami un messaggio su Telegram.  
Appena ricevo la connessione ricreo tutto ciò che serve.

---

**TL;DR:** `git clone` x10 → `openclaw gateway start` → scrivimi su Telegram. Il resto lo sistemo io.
