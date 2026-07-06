# MEMORY.md — Durable Knowledge

_Last promoted: 2026-07-06 00:06 UTC_

## Active Projects & Systems

### BigBeluga — BTC 1h Trading Strategy
- **Dashboard**: Port 8090, teal card (#00bcd4), "Two-Pole Oscillator + Volumatic VIDYA"
- **Backtest** (8.7yr, 2017→2026): 678 trades (342L/361S), WR 44.5%, Return +3,147%, DD 24.28%, Calmar 129.6, PF 1.36, CAGR 48.8%, ~2% risk/trade
- **Live**: Journal at `live/paper_journal_bigbeluga.json`, cron `05 * * * *` (hourly at :05)
- **Anomalies**: PULSAR shows 336,202× return (likely unnormalized calc); SCALE DCA shows 22,176× in backtest vs 19× forward (leverage/compound discrepancy)
- **Final classification**: BigBeluga — 31× return, 44.5% WR — top performer after normalization run

### Airdrop Farming (Multi-Wallet, Multi-Chain)
- **Wallets**: W04 (MegaETH), W12 (Unichain), W13 (Base), W05 (skip-pattern active)
- **Chains operated**: Base (gas ~0.00000013 ETH), Unichain (~0.00000003 ETH), MegaETH
- **Strategy**: Self-transfers (21k gas), WETH deposit/swap on Uniswap V3 (Unichain), swap on MegaETH
- **Schedule**: 3 daily windows (morning/afternoon/evening), automated via cron
- **Airdrop scouting pipeline**: scout → analyst → creator, posts to @onecrypto_airdrop
- **Known issue**: W4 swap failed on MegaETH — `out of gas: gas required exceeds 80000`. Evening window completed 3/3 on June 29-30. Later resolved.
- **Cron farming jobs had gone missing** — were detected and recreated around June 29-30.
- **Long-term goal**: Qualify for airdrops over 6-month horizon, minimizing ETH consumption.

### Odoo Migration — Dott. Mazzoleny
- **Context**: Migrating from Fattureincloud to Odoo, Italian freelance operations
- **Setup path**: Italian localization, piano dei conti standard, IBAN bank sync (Ponto/Basiq), tax configuration
- **Status**: Initial documentation study completed, user deferred further steps

### aureamedia.it — Blog Pipeline
- **Topic focus**: SEO
- **Status**: Pipeline NOT running for W26 — 0 articles published. Pipeline attempts failed or stalled.
- **Cron**: Weekly cycle not triggering. Blog monitor shows silence.

### VOLCAN BTC 15m — Signal Bot
- **Status**: No signals for multiple days (June 29-30). RSI ~52.0 (neutral), trend -1.6% (weak bearish), volume 0.80x avg
- **Equity**: $59,760.00, 0 open positions, 0 P&L
- **Behavior**: Properly reporting "nessun segnale" — bot is alive but market flat

### Hermes Agent (NousResearch) — Nuovo 🆕
- **Installato**: 2026-07-05, container Docker su Ubuntu server
- **Container**: `hermes-agent`, immagine buildata da GitHub, porta 8081
- **Telegram bot**: @Hermesdvdbot, connesso via gateway nativo Hermes (senza bridge Python)
- **Provider**: DeepSeek diretto via `DEEPSEEK_API_KEY` (stessa key usata da OpenClaw)
- **Modello**: deepseek-v4-pro (nativo, provider: `deepseek`)
- **Config**: gateway avviato con `gateway run --accept-hooks`, profilo default con provider deepseek
- **Model**: default `anthropic/claude-opus-4.6` sovrascritto con `deepseek/deepseek-v4-pro` tramite config YAML
- **Systemd**: gateway si auto-avvia dentro Docker con restart: unless-stopped
- **Note**: Il container non ha accesso TTY — la configurazione del modello va fatta via file YAML su /opt/hermes-data/, non via `hermes model` interattivo
- **Home channel**: /sethome inviato su @Hermesdvdbot

### OpenClaw Infrastructure
- **Current version**: 2026.6.11 (updated July 1, 2026 from 2026.5.20)
- **Active model**: deepseek/deepseek-v4-flash (⚠️ not in allowed models list — silently falls back to flash on some paths)
- **⚠️ OpenRouter credits EXHAUSTED** (discovered July 3 00:04 UTC): The `openai/deepseek/deepseek-v4-pro` routing path returns 402. Only the direct `deepseek/deepseek-v4-pro` path remains operational. All agents depending on the openai→deepseek route will fail.
- **Gateway**: Running manually (pid varies after restarts), port 18789. Systemd service DISABLED after July 2 restart-loop incident (counter reached 487).

#### Git Backup — 6 Repos (user: davidec2981)
- **Repos**: openclaw-main, openclaw-trading, openclaw-airdrop, openclaw-polyclaw, openclaw-robocop, openclaw-aihf
- **Cron backup**: `0 5 * * *` Europe/Rome, script `/root/.openclaw/workspace/scripts/backup-github.sh`
- **Last push**: 2026-07-05 — full backup + Hermes Telegram bridge (poi rimosso a favore del gateway nativo)

#### Known Issues
- **OpenRouter credits depleted** — top up at https://openrouter.ai/settings/credits. Affects all agents routing through `openai/deepseek/*`.
- **robocop-nightly-audit** cron failing (free-tier model timeouts, now with 1 fewer fallback)
- **Systemd** disabled — gateway runs manually, no auto-restart on crash
- **Config hot-reload** doesn't apply to secret paths (bot tokens, API keys)
- **6 of 7 Telegram bot tokens** are dead and need replacement from BotFather
- **Memory dreaming** cycles occasionally crash mid-generation (context window issues on fallback model; 00:04 July 3 cycle failed twice)
- **Dist hot-patches** are fragile — will be lost on update/build
- **Context window risk**: Memory corpus exceeding fallback model limits when primary path dead
- **Hermes Docker container**: no TTY — model config must be done via YAML files, not `hermes model` interactive

## User Preferences & Context
- **Name**: Dade (Telegram handle/display name)
- **Languages**: Italian primary, English operational
- **Trading style**: Systematic, backtest-validated, moderate risk (~2%/trade)
- **Crypto**: Airdrop farming focused, cost-conscious (gas optimization matters)
- **Business tools**: Odoo migration in progress, tax optimization evaluated (Gegidze Georgia IE — deemed not worthwhile for Italian resident freelancer on forfettario)
- **Timezone**: Rome (CET/CEST, UTC+1/+2)

## System Health Notes
- **Recurring**: `[assistant turn failed before producing content]` — appears in ~30% of dream-synthesis attempts. Likely related to model timeouts on free-tier fallbacks.
- **Session cleanup**: Many `.jsonl.deleted.*` files in session corpus — session deletion/cleanup is active and frequent.
- **Memory dreaming**: Running on schedule. Light sleep stages candidates; deep sleep promotes consolidated findings. Dreaming cycles occasionally crash after gateway restarts (context window exhaustion).
- **Telegram plugin**: Currently patched in dist — fragile. Both bugs (threadId.trim, finiteSecondsToTimerSafeMilliseconds) break ALL outbound messaging on v2026.6.11. Webchat is the reliable fallback.

## Recent Sessions
- **2026-07-05 15:04–23:58 UTC** (session `ff684424`): Installed Docker + Hermes Agent (NousResearch) in container. Configured DeepSeek provider directly. Created @Hermesdvdbot Telegram bot. Connected via native Hermes gateway (initially created Python bridge, later replaced with native gateway). Git pushed all 6 repos. Cron backup configured daily 05:00 IT. Model config fixed via YAML files.
