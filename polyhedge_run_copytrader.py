#!/usr/bin/env python3
"""CopyTrader — Main Entry Point for scanning & copying top Polymarket traders.

Usage:
    python3 -m polyhedge.copytrader.run scan          # Scan known + discover new traders
    python3 -m polyhedge.copytrader.run rank           # Show current rankings
    python3 -m polyhedge.copytrader.run live           # Run a live copy cycle
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from .scanner import CopytradeScanner, SEED_WALLETS
from .analyzer import TraderAnalyzer, format_ranking, format_tradable_trades
from .executor import CopytradeExecutor
from polyhedge.config import CONFIG
from polyhedge.core.risk_manager import Portfolio
import time


def cmd_scan():
    """Scan all known wallets + discover new traders."""
    print("=" * 60)
    print("🔍 COPYTRADER — Scouting top Polymarket traders")
    print("=" * 60)
    
    scanner = CopytradeScanner()
    analyzer = TraderAnalyzer()
    
    print(f"\n📡 Refreshing {len(SEED_WALLETS)} seed wallets...")
    traders = scanner.refresh_all_seed_wallets(limit=30)
    
    print(f"\n🔎 Discovering new traders from top markets...")
    new_traders = scanner.discover_new_traders(min_trades=20, max_results=10)
    
    all_wallets = dict(traders)
    for t in new_traders:
        all_wallets[t.name or t.address] = t
    
    print(f"\n🏆 Ranking {len(all_wallets)} traders...")
    rankings = analyzer.score_and_rank(all_wallets)
    
    print()
    print(format_ranking(rankings))
    
    # Save scores
    analyzer.save_scores(rankings)
    
    print(f"\n✅ Scan complete — {len(all_wallets)} traders analyzed")


def cmd_rank():
    """Show current trader rankings from cache."""
    analyzer = TraderAnalyzer()
    scores = analyzer.load_scores()
    
    if not scores:
        print("⚠ No cached scores. Run 'scan' first.")
        return
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║       🏆  COPYTRADER — TRADER RANKINGS (cached)           ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    print(f"{'#':>3s} {'Trader':20s} {'Score':>6s} {'Trades':>7s} {'Volume':>10s} {'WinRate':>7s}")
    print("─" * 60)
    
    for i, s in enumerate(scores[:20], 1):
        display = s.get("pseudonym") or s.get("name", "?")
        print(f"{i:>3d} {display[:20]:20s} "
              f"{s['score']:>5.1f}  "
              f"{s['total_trades']:>6d}  "
              f"${s['total_volume']:>8,.0f} "
              f"{s.get('win_rate', 0)*100:>5.1f}%")


def cmd_live():
    """Run one copy cycle — find top traders and copy their trades."""
    print("=" * 60)
    print("🔁 COPYTRADER — Live copy cycle")
    print("=" * 60)
    
    scanner = CopytradeScanner()
    analyzer = TraderAnalyzer()
    portfolio = Portfolio()
    portfolio.load(f"{CONFIG.data_dir}/portfolio.json")
    executor = CopytradeExecutor(portfolio=portfolio)
    
    # Get traders quickly from cache
    cached = analyzer.load_scores()
    if not cached:
        print("⚠ No cached trader data. Run 'scan' first.")
        return
    
    # Refresh top traders
    print(f"\n📡 Refreshing top 5 traders...")
    top_traders = []
    for s in cached[:5]:
        name = s.get("name", "")
        addr = s.get("address", "")
        if name and addr:
            try:
                info = scanner.refresh_trader(name, addr, 20)
                score = analyzer.score_trader(info)
                top_traders.append((name, info, score))
                print(f"  ✅ {info.pseudonym or name}: score={score:.1f}, {len(info.recent_trades)} recent trades")
            except Exception as e:
                print(f"  ❌ {name}: {e}")
            time.sleep(0.3)
    
    print(f"\n📊 Analyzing trades to copy...")
    total_copies = 0
    for name, info, score in top_traders:
        if score < 50:
            continue
        
        trades = analyzer.get_tradable_trades(info)
        if trades:
            print(format_tradable_trades(info, trades))
            
            # If we have low conviction (<60), just report
            if score < 60:
                print("     ⚠ Score < 60 — reporting only")
                continue
            
            # Execute copies
            if CONFIG.mode == "paper" or score >= 70:
                print(f"     📝 Placing copy trades (paper mode)...")
                results = executor.match_and_copy(trades, name, size_multiplier=0.5)
                total_copies += sum(1 for r in results if r.success)
    
    print(f"\n📊 Cycle complete: {total_copies} copy trades placed")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    if cmd == "scan":
        cmd_scan()
    elif cmd == "rank":
        cmd_rank()
    elif cmd == "live":
        cmd_live()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
