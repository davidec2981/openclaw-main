# MEMORY.md — Durable Long-Term Memory

> Last promotion: 2026-07-03 07:42 UTC (High-signal cycle: Telegram restored, dist build fixed)

---

## User Profile (Dade)

- **Identity**: Italian-speaking crypto operator, entrepreneur, and freelancer
- **Communication**: Primarily Italian (native), mixed Italian/English for crypto operations
- **Style**: Direct, results-oriented, values system reliability and backtest-validated strategies
- **Time zone**: Europe/Rome (CEST, UTC+2)

## Active Projects

### 1. BigBeluga Trading Strategy (BTC 1h)
- **System**: Two-Pole Oscillator + Volumatic VIDYA on BTC 1h
- **Backtest results** (8.7 years, 2017→2026): 678 trades (342L/361S), Win Rate 44.5%, Return +3,147%, Drawdown 24.28%, Calmar Ratio 129.6, Profit Factor 1.36, CAGR 48.8%, 31× return
- **Dashboard**: Teal (#00bcd4) card on :8090, cron `05 * * * *`
- **Journal**: `live/paper_journal_bigbeluga.json`
- **Anomaly flagged**: PULSAR strategy showed 336,202× return (probably calculation error); SCALE DCA discrepancy: 22,176× in backtest vs 19× forward
- **Status**: Active paper-trading. No new positions opened week of June 29.

### 2. VOLCAN BTC 15m Signal Bot
- **Purpose**: Real-time BTC 15m trading signals
- **Status**: Quiet period — multiple checks (June 29-30) showed no signals. RSI ~52 neutral, trend -0.016 weak bearish, volume 0.80x avg
- **Positions**: 0 open, 0 closed. Equity flat.

### 3. Airdrop Farming Infrastructure
- **Workflow**: Scout → Analyst → Creator (daily pipeline)
- **Chains**: Base, Unichain, MegaETH (multi-wallet strategy)
- **Key metrics**: Gas costs on Base ~0.00000013 ETH per self-transfer, Unichain ~0.00000003 ETH
- **Recent**: Finestra Sera June 29: 3/3 successes. W4 MegaETH swap initially failed (gas error) but later resolved.
- **Cron farming**: 3 cron jobs rebuilt after outage. Watchdog active.
- **Airdrop scouting**: ~64 scanned daily, 22 zero-cost, 5 approved. Hoppr (70) and Aether (70) are new priority targets.
- **Long-term goal**: Qualify for airdrops over 6-month horizon, minimizing ETH consumption.
- **Farmer V4.4 bugs** (July 3): `_execute_action` missing (Wallet 13 operations fail) and `_send_window_summary` missing. System cron still fires (07:00, 13:00, 19:00 UTC) but operations may be partial.

### 4. Odoo Migration (Fattureincloud → Odoo)
- **Client**: Dott. Mazzoleny
- **Scope**: Full accounting platform migration
- **Key decisions**: Piano dei conti italiano (standard), bank sync via Ponto/Basiq, Italian tax localization
- **Active**: Q&A phase — managing import procedures for contacts and invoices, handling forfettario (flat-rate) tax regime

### 5. AureaMedia Blog Pipeline
- **Status**: **Stalled** — W26 had zero publications
- **Topic cluster**: SEO
- **Issue**: Weekly pipeline not executing; cron potentially missing or misconfigured
- **URL**: aureamedia.it

### 6. Tax Optimization Evaluation
- **Inquiry**: Evaluating Gegidze tax optimization (Georgia IE regime) for Italian freelancer with marginal foreign clients
- **Assessment**: Georgia IE registration without physical relocation is "fiscalmente inoperante" — Italy would still tax the income. Regime forfettario at 15% remains the baseline.

## Infrastructure

### OpenClaw Instance
- **Version**: 2026.6.11 (reinstalled by Dade ~July 2 after failed update caused 2-day Telegram outage)
- **Host**: ubuntu, Node.js v22.22.3
- **Model**: deepseek/deepseek-v4-pro (primary); deepseek/deepseek-v4-flash (fallback)
- **Active plugins**: browser, camofox, duckduckgo, active-memory

### Telegram Status ✅ (RESTORED July 3, 07:42 UTC)
- **Main bot**: `openclawrailwayvps_bot` — WORKING, delivering messages to Dade (951887934)
- **Restoration**: Dade manually reinstalled OpenClaw after ~2-day outage. Additional dist build fixes applied by assistant at 07:13–07:21 UTC.
- **6 sub-agent bots**: STILL DEAD (airdrops, trading, farmer, polyclaw, wp-claw, pfa) — tokens need replacement
- **Delivery confirmed**: `telegram-final` mirror shows successful outbound delivery as of 07:42:11 UTC

### Sub-Agents (8 total)
| Agent | Purpose | Telegram Bot |
|-------|---------|-------------|
| main | Primary assistant | @openclawrailwayvps_bot ✅ |
| airdrop | Airdrop scouting/posting | @OCAirdrops_bot ❌ |
| trading | Trading strategies | @opentradedvd_bot ❌ |
| farmer | Chain operations/farming | @Openfarmer_bot ❌ |
| polyclaw | Polyhedge paper trading | @polyclawdvd_bot ❌ |
| wp-claw | WordPress/blog management | @WPmanager_bot ❌ |
| pfa | Accounting/invoicing | @PFA_BPM_bot ❌ |
| robocop | Nightly audit | (cron-only) ❌ |

### Dist Build Fix (Critical — Applied July 3, 07:13–07:21 UTC)
- **Problem**: Inconsistent dist build — `/root/openclaw/dist/` had wrong hash references, `node_modules/openclaw/dist/` had correct files
- **Fixes applied**:
  1. Copied 3975 missing files from `node_modules/openclaw/dist/` → `/root/openclaw/dist/`
  2. Fixed hash references: all `number-coercion-CgoBR0cm` → `number-coercion-CJQ8TR--`
  3. Copied `plugin-sdk/number-runtime.js` and `plugin-sdk/channel-outbound.js`
  4. Verified `threadId.trim` hot-patch in `sent-message-cache-BNy8x8Gj.js` (lines 33-34)
  5. Verified `finiteSecondsToTimerSafeMilliseconds` exports
  6. Gateway restarted with fixed modules
- **⚠️ FRAGILITY WARNING**: Any future `npm run build` or OpenClaw update WILL overwrite these fixes. They must be re-applied after every build/update.

### ⚠️ Known Issues
1. **⚠️ OpenRouter credits EXHAUSTED** (July 3 00:04 UTC): `openai/deepseek/*` routing path dead (402). Only direct `deepseek/deepseek-v4-pro` path remains. Top up at https://openrouter.ai/settings/credits.
2. **Dist build fragility**: Hash mismatches between `node_modules` and `dist` recur after updates. Fix procedure documented above.
3. **6 of 7 Telegram bot tokens dead**: Only main bot works. Sub-agents unreachable via Telegram.
4. **Farmer V4.4 bugs**: `_execute_action` (Wallet 13) and `_send_window_summary` (completion) fail. Operations may be partial.
5. **Model override bug**: `deepseek/deepseek-v4-pro` is not in `agents.defaults.models` for the main agent. Heartbeat polls silently fall back to `deepseek/deepseek-v4-flash`.
6. **Memory dreaming fragility**: Three of the last five dreaming cycles crashed. Context window pressure from growing memory corpus.
7. **Robocop nightly audit**: Failed June 29 — all 3 fallback models returned errors. Now has fewer fallback paths due to OpenRouter outage.

### Recovery Reference
- **Backup location**: `~/.openclaw/backup/` — proven reliable; saved full config during July 1 outage
- **Reinstall recovery**: Dade's manual OpenClaw reinstall (July 2-3) successfully restored core Telegram functionality. This is a viable recovery path when updates corrupt the installation.
- **Dist fix procedure** (post-build/post-update):
  1. Copy missing files: `cp -n /root/openclaw/node_modules/openclaw/dist/*.js /root/openclaw/dist/`
  2. Fix hash refs: `sed -i 's/number-coercion-CgoBR0cm/number-coercion-CJQ8TR--/g'` in all dist files
  3. Copy plugin-sdk subdirectory files from node_modules
  4. Gateway restart
- **Critical recovery steps** (if update corrupts config):
  1. `npm run build` from OpenClaw repo directory
  2. Restore `config.yaml` from backup
  3. Verify Telegram channels section is populated
  4. Apply dist fix procedure (above)
  5. Gateway restart

## Recurring Patterns

- **Backups save us**: Multiple incidents across weeks prove the backup directory is the most reliable recovery mechanism
- **Telegram is the single point of failure**: When Telegram breaks, Dade can't reach us. The 2-day outage (July 1-3) is the most severe incident to date.
- **Dist build inconsistency is chronic**: Hash mismatches between `node_modules` and `dist` recur after updates. Same bug hit July 1 and July 3.
- **Backtest euphoria vs forward reality**: Backtest returns (3,147%, 336,202×, 22,176×) vastly exceed what forward testing produces. Ongoing skepticism needed.
- **Gas optimization is a core value**: Dade optimizes for cost-efficiency across all crypto operations.
- **"Turn failed" pattern**: ~30% of longer assistant turns crash mid-generation when using fallback/free model tiers.
- **Reinstall as recovery**: Dade manually reinstalled OpenClaw to fix Telegram. This is now a documented recovery path alongside the backup restore procedure.
- **Hot-patches survive reinstalls**: The `threadId.trim` fix persisted through the reinstall, suggesting it was bundled in source.

---

*This file is maintained by the memory dreaming system. Promotion cycles run periodically (target: daily at ~06:00 UTC; emergency cycles on high-signal events). See `memory/dreaming/` for per-cycle light/deep/REM stages.*
