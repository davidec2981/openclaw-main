# MEMORY.md — Durable Knowledge

_Last promoted: 2026-07-03 07:52 UTC_

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

### OpenClaw Infrastructure
- **Current version**: 2026.6.11 (updated July 1, 2026 from 2026.5.20)
- **Active model**: deepseek/deepseek-v4-pro (⚠️ not in allowed models list — silently falls back to flash on some paths)
- **⚠️ OpenRouter credits EXHAUSTED** (discovered July 3 00:04 UTC): The `openai/deepseek/deepseek-v4-pro` routing path returns 402. Only the direct `deepseek/deepseek-v4-pro` path remains operational. All agents depending on the openai→deepseek route will fail.
- **Gateway**: Running manually (pid varies after restarts), port 18789. Systemd service DISABLED after July 2 restart-loop incident (counter reached 487).

#### July 1 Update + Recovery
- Update corrupted config — `dist/` entry point mismatch, Telegram channels wiped. Full-day outage. Recovered via `npm run build` + `~/.openclaw/backup/` config restore.
- **Pre-update checklist**: Snapshot full config directory before any future `openclaw update`.

#### July 2 — Telegram Plugin Catastrophic Failure
- **All 7 Telegram bots non-functional** since ~08:50 UTC. Communication shifted to webchat.
- **Root cause: Two bugs in v2026.6.11 plugin compile**:
  - **Bug 1** — `threadId.trim is not a function`: `parseTelegramThreadId()` in compiled dist (`sent-message-cache-BNy8x8Gj.js`) calls `.trim()` on threadId without type guard. When threadId is not a string (undefined, object, from webchat context), it crashes all outbound delivery.
  - **Bug 2** — `finiteSecondsToTimerSafeMilliseconds is not a function`: The Telegram plugin source (`extensions/telegram/src/request-timeouts.ts:3`) imports this from `openclaw/plugin-sdk/number-runtime`, but the function was **never exported** from the runtime bundle (`number-runtime-C7CNv3wi.js`). This causes all 7 bot channels to fail at provider startup with `channel exited`. Both bugs must be present simultaneously for total Telegram outage.
- **Hot-patches applied to dist**:
  - Added `if (typeof threadId !== "string") return;` guard before `.trim()` in `sent-message-cache-BNy8x8Gj.js`
  - Manually appended `finiteSecondsToTimerSafeMilliseconds` + `MAX_TIMER_TIMEOUT_MS` functions to `number-runtime-C7CNv3wi.js`
- **⚠️ WARNING**: Hot-patches will be **wiped on next `openclaw update` or `npm run build`**. Need to re-apply or wait for upstream fix (2026.6.12+).
- **Bot tokens**: All 7 tokens invalidated simultaneously (July 2, ~15:30 UTC). User replaced default bot token (830138…jKwI). Other 6 bot tokens still dead. Token reset cause: unknown (possibly BotFather regeneration).
- **Gateway restart behavior**: `SIGUSR1` hot-reload does NOT reload secret-protected config paths (bot tokens, API keys). Full gateway kill + restart is needed for token changes.
- **Systemd restart loop**: After gateway restarts, systemd tried to launch new instances (counter 487) while port 18789 occupied. Service now `inactive (dead)`. Gateway started manually.

#### Known Issues
- **OpenRouter credits depleted** — top up at https://openrouter.ai/settings/credits. Affects all agents routing through `openai/deepseek/*`.
- **robocop-nightly-audit** cron failing (free-tier model timeouts, now with 1 fewer fallback)
- **Systemd** disabled — gateway runs manually, no auto-restart on crash
- **Config hot-reload** doesn't apply to secret paths (bot tokens, API keys)
- **6 of 7 Telegram bot tokens** are dead and need replacement from BotFather
- **Memory dreaming** cycles occasionally crash mid-generation (context window issues on fallback model; 00:04 July 3 cycle failed twice)
- **Dist hot-patches** are fragile — will be lost on update/build
- **Context window risk**: Memory corpus exceeding fallback model limits when primary path dead

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
- **2026-07-02 08:48–15:56 UTC** (session `21fa0d20`, 455 lines): Dade reconnected via webchat after connection loss. Diagnosed Telegram outage. Discovered two compiler bugs in plugin. Applied hot-patches. Replaced default bot token. Systemd restart loop stopped. Gateway stable with manual start.
- **2026-07-03 00:04 UTC** (session `36624075`): Memory dreaming cycle failed twice — OpenRouter 402 (credits exhausted) then deepseek-direct abort. No user activity in 12-hour window. System is running on a single model path.
