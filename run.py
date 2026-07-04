#!/usr/bin/env python3
"""PolyHedge — Main Entry Point

Strategie ATTIVE:
  1. CopyTrader (★ principale) — copia top trader Polymarket, crypto 15m e sports
  2. Arbitrage/Hedge — mutual-exclusion arb su tornei (NHL, NBA)

Strategie DISATTIVATE (troppo conservative o senza edge):
  - Directional (AI) — non trova edge da settimane
  - Tail-end (longshots) — conviction mai sufficiente
  - Gabagool (complete-set arb) — 0 edges trovati
  - Cross-exchange arb — 0 opportunità trovate
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

from polyhedge.config import CONFIG
from polyhedge.core.scanner import scan, scan_fast_markets, scan_crypto_updown
from polyhedge.core.risk_manager import Portfolio
from polyhedge.core.executor import Executor
from polyhedge.core.logger import TradeLogger
from polyhedge.strategies.arbitrage import run as run_arbitrage
from polyhedge.core.bayesian import BayesianEngine
from polyhedge.core.forward_test import ForwardTester
from polyhedge.core.executor import set_forward_tester
from polyhedge.copytrader.scanner import CopytradeScanner
from polyhedge.copytrader.analyzer import TraderAnalyzer


# ── Known profitable Polymarket wallets to copy ─────────────────────────
SEED_WALLETS = {
    "gabagool22": "0x6031b6eed1c97e853c6e0f03ad3ce3529351f96d",
    "gabagool-inv": "0xf444220e8d32f456c39b6b727e7bb5bc41d8c970",
    "sherlockhomie": "0xd44e29936409019f93993de8bd603ef6cb1bb15e",
    "BoshBashBish": "0x29bc82f761749e67fa00d62896bc6855097b683c",
    "distinct-baguette": "0xe00740bce98a594e26861838885ab310ec3b548c",
    "Account88888": "0x7f69983eb28245bba0d5083502a78744a8f66162",
}

# CopyTrader thresholds
COPYTRADER_MIN_SCORE = 50
COPYTRADER_CRYPTO_MAX_AGE = 60
COPYTRADER_SLOW_MAX_AGE = 360
COPYTRADER_DISCOVER_NEW = True
COPYTRADER_DISCOVER_COUNT = 10  # discover up to 10 new traders per cycle


def auto_tune_size(score, win_rate=None):
    """Dynamic sizing: more confidence → more exposure."""
    if score < 50:
        return 0.0
    elif score < 60:
        mult = 0.3
    elif score < 70:
        mult = 0.4
    elif score < 80:
        mult = 0.5
    else:
        mult = 0.6
    if win_rate:
        if win_rate > 0.6:
            mult += 0.1
        if win_rate > 0.8:
            mult += 0.1
    return min(mult, 0.7)


def print_banner():
    print(r"""
 ╔══════════════════════════════════════════╗
 ║       PolyHedge — AI Polymarket Bot      ║
 ║                                          ║
 ║   ★ CopyTrader        (crypto 15m)      ║
 ║   🛡️ Arbitrage/Hedge  (sports)          ║
 ║   ❌ Directional/Tail/Gabagool (off)    ║
 ╚══════════════════════════════════════════╝
    """)


def discover_new_traders(cs, ca):
    """Discover new profitable wallets and add them to the tracking pool."""
    print(f"\n  🔎 Discovering new traders (up to {COPYTRADER_DISCOVER_COUNT})...")
    try:
        # Method 1: scan top markets for active wallets
        new_traders = cs.discover_new_traders(min_trades=15, max_results=COPYTRADER_DISCOVER_COUNT)
        
        if new_traders:
            rankings = ca.score_and_rank({t.name or t.address[:12]: t for t in new_traders})
            ca.save_scores(rankings)
            for name, info, score in rankings:
                if score >= COPYTRADER_MIN_SCORE:
                    print(f"     🆕 {info.pseudonym or name}: score={score:.1f}, "
                          f"{info.total_trades} trades, ${info.total_volume:.0f} vol")
                    
                    # Auto-add high-scoring new traders to seed list
                    if score >= 70 and info.address not in SEED_WALLETS.values():
                        key = (info.pseudonym or info.name or f"auto_{info.address[:8]}")
                        if key not in SEED_WALLETS:
                            SEED_WALLETS[key] = info.address
                            print(f"        → Added to tracked wallets!")
        else:
            # Method 2: refresh cached scores to find any that improved
            cached = ca.load_scores()
            if cached:
                for s in cached[:5]:
                    try:
                        name = s.get("name", "")
                        addr = s.get("address", "")
                        if name and addr and addr not in SEED_WALLETS.values() and s.get("score", 0) >= 60:
                            SEED_WALLETS[f"auto_{name[:16]}"] = addr
                            print(f"     🆕 Auto-added {name} (score={s['score']:.1f}) from cache")
                    except:
                        pass
            if not new_traders:
                print("     ℹ️  No new traders found this cycle")
    except Exception as e:
        print(f"     ⚠ Discovery error: {e}")


def run_copytrader_cycle(portfolio, executor, logger):
    """Core CopyTrader cycle — scan, score, and copy."""
    print(f"\n{'='*60}")
    print(f"📋 COPYTRADER — Copying top Polymarket traders")
    print(f"{'='*60}")

    cs = CopytradeScanner(data_dir=CONFIG.data_dir)
    ca = TraderAnalyzer(data_dir=CONFIG.data_dir)

    copy_trades = 0

    # Discover new traders
    if COPYTRADER_DISCOVER_NEW:
        discover_new_traders(cs, ca)

    # Check all tracked wallets (seed + auto-discovered)
    wallets = dict(SEED_WALLETS)
    print(f"\n  📡 Checking {len(wallets)} tracked wallets...")
    
    for name, addr in wallets.items():
        try:
            info = cs.refresh_trader(name, addr, limit=30)
            score = ca.score_trader(info)
            
            # Fallback rescore on buys only if borderline
            if score < COPYTRADER_MIN_SCORE:
                buys_only = cs.refresh_trader(name, addr, limit=20)
                buys_only.recent_trades = [t for t in buys_only.recent_trades if t.is_buy]
                if buys_only.recent_trades:
                    buy_score = ca.score_trader(buys_only)
                    if buy_score > score:
                        score = buy_score
                        info.win_rate = buys_only.win_rate
            
            win_rate = info.win_rate
            size_mult = auto_tune_size(score, win_rate)

            # Show pseudonym if available
            display = info.pseudonym or name
            score_color = "🟢" if score >= 70 else ("🟡" if score >= 50 else "🔴")
            print(f"     {score_color} {display:20s} score={score:.1f} win={win_rate*100:.0f}% "
                  f"mult={size_mult:.1f}x trades={info.total_trades} vol=${info.total_volume:.0f}")

            if score < COPYTRADER_MIN_SCORE or size_mult <= 0:
                continue

            # Detect trader style
            buys = [t for t in info.recent_trades if t.is_buy]
            crypto_ratio = sum(1 for t in buys if "Up or Down" in t.title) / max(len(buys), 1)

            if crypto_ratio > 0.2:
                max_age = COPYTRADER_CRYPTO_MAX_AGE
                label = "⚡ crypto 15m"
            else:
                max_age = COPYTRADER_SLOW_MAX_AGE
                label = "🐢 sports/events"

            tradable = ca.get_tradable_trades(info, min_size=0.5, max_age_minutes=max_age)
            if not tradable:
                if buys:
                    print(f"         ⏳ No recent trades ({label}, {max_age}m window)")
                continue

            print(f"         📋 {len(tradable)} trades to copy ({label}, mult={size_mult:.1f}x)")

            from polyhedge.copytrader.executor import CopytradeExecutor
            ce = CopytradeExecutor(executor=executor, portfolio=portfolio)
            results = ce.match_and_copy(tradable, name, size_multiplier=size_mult)

            for r in results:
                if r.success:
                    try:
                        logger.log_trade(r, question=getattr(r, 'question', ''),
                                        outcome=getattr(r, 'outcome', ''),
                                        strategy="copytrade")
                    except TypeError:
                        pass
                    copy_trades += 1

            time.sleep(0.3)

        except Exception as e:
            print(f"     ⚠ {name}: {e}")

    if copy_trades > 0:
        portfolio.save(f"{CONFIG.data_dir}/portfolio.json")
    
    print(f"\n  📊 Copy trades placed: {copy_trades}")
    return copy_trades


def run_once():
    """Execute one scan → arbitrage → copytrade cycle."""
    portfolio = Portfolio()
    portfolio.load(f"{CONFIG.data_dir}/portfolio.json")
    executor = Executor()
    logger = TradeLogger()

    # Forward tester
    ft = ForwardTester()
    set_forward_tester(ft)
    ft_metrics = ft.metrics()
    print(f"  📊 Forward: {ft_metrics.resolved_trades} resolved, "
          f"{ft_metrics.active_markets} pending, {ft_metrics.total_trades} total")

    # Bayesian engine (lightweight, just for priors)
    bayes = BayesianEngine(f"{CONFIG.data_dir}/bayesian_priors.json")
    bayes_stats = bayes.stats()
    if bayes_stats["markets"] > 0:
        print(f"  🧠 Bayesian: {bayes_stats['markets']} markets, {bayes_stats['total_ai_calls']} AI calls")

    # Phase 1: Scan markets
    print(f"\n📡 Scanning markets...")
    t0 = time.time()
    markets = []
    
    # Main scan
    try:
        markets = scan(limit=100, min_volume=CONFIG.min_volume)
    except:
        pass
    
    # Fast markets (up to 45d)
    try:
        fast = scan_fast_markets(min_volume=1000, max_days_to_resolve=45)
        existing_ids = {m.id for m in markets}
        markets.extend([m for m in fast if m.id not in existing_ids])
    except:
        pass
    
    # Crypto up/down
    try:
        crypto = scan_crypto_updown(min_volume=500)
        existing_ids = {m.id for m in markets}
        markets.extend([m for m in crypto if m.id not in existing_ids])
    except:
        pass
    
    print(f"   → {len(markets)} markets in {time.time()-t0:.1f}s")

    # Phase 2: Arbitrage / Hedge (fast, no AI)
    order_results = []
    try:
        results = run_arbitrage(markets, portfolio, executor, logger)
        order_results.extend(results)
    except Exception as e:
        print(f"  ❌ Arbitrage: {e}")

    # Phase 3: CopyTrader (★)
    try:
        copy_trades = run_copytrader_cycle(portfolio, executor, logger)
    except Exception as e:
        print(f"  ❌ CopyTrader: {e}")
        import traceback; traceback.print_exc()
        copy_trades = 0

    # Summary
    successful = sum(1 for r in order_results if r.success)
    total_size = sum(r.size for r in order_results if r.success)
    print(f"\n{'='*60}")
    print(f"📊 CYCLE SUMMARY ({datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC)")
    print(f"   Markets scanned:    {len(markets)}")
    print(f"   Arbitrage trades:   {successful}")
    print(f"   Copy trades:        {copy_trades}")
    print(f"   Portfolio:          ${portfolio.bankroll:.2f}")
    print(f"   Open positions:     {len(portfolio.positions)}")
    print(f"{'='*60}")

    portfolio.save(f"{CONFIG.data_dir}/portfolio.json")

    # Check resolutions
    newly_resolved = ft.poll_resolutions()
    ft_metrics = ft.metrics()
    if newly_resolved > 0:
        print(f"  ✅ {newly_resolved} resolved!")
        print(ft.report())
    print(f"📊 Forward: {ft_metrics.wins}W/{ft_metrics.losses}L "
          f"({ft_metrics.win_rate*100:.0f}%) P&L=${ft_metrics.total_pnl:.2f} "
          f"| {ft_metrics.active_markets} pending")


def main():
    parser = argparse.ArgumentParser(description="PolyHedge — Polymarket CopyTrader")
    parser.add_argument("--once", action="store_true", help="Single cycle (default)")
    parser.add_argument("--loop", action="store_true", help="Continuous loop")
    parser.add_argument("--paper", action="store_true", help="Paper mode")
    parser.add_argument("--live", action="store_true", help="Live mode")
    parser.add_argument("--limits", action="store_true", help="Show portfolio")
    parser.add_argument("--copytrader-only", action="store_true", help="Only copytrader")
    args = parser.parse_args()

    if args.paper:
        CONFIG.mode = "paper"
    if args.live:
        CONFIG.mode = "live"

    print_banner()
    print(f"Mode: {CONFIG.mode.upper()} | Max pos: ${CONFIG.max_position_size:.2f}")
    print(f"Scan: every {CONFIG.scan_interval_minutes}m\n")

    if args.limits:
        portfolio = Portfolio()
        portfolio.load(f"{CONFIG.data_dir}/portfolio.json")
        print(f"📊 Portfolio: ${portfolio.bankroll:.2f}, {len(portfolio.positions)} positions")
        return

    def single_cycle():
        if args.copytrader_only:
            p = Portfolio()
            p.load(f"{CONFIG.data_dir}/portfolio.json")
            e = Executor()
            l = TradeLogger()
            return run_copytrader_cycle(p, e, l)
        return run_once()

    if args.loop:
        print(f"🔄 Loop every {CONFIG.scan_interval_minutes}min")
        while True:
            single_cycle()
            try:
                from polyhedge.core.dashboard import generate
                generate()
            except:
                pass
            time.sleep(CONFIG.scan_interval_minutes * 60)
    else:
        single_cycle()
        try:
            from polyhedge.core.dashboard import generate
            generate()
        except:
            pass


if __name__ == "__main__":
    main()
