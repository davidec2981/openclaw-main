#!/usr/bin/env python3
"""
BigBeluga — Forward Test
Two-Pole Oscillator + Volumatic VIDYA su BTC 1h
Esegue: segnale → paper trade → journal
"""
import json, csv, math, os, sys
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = '/root/.openclaw/workspace/BTC_1h_full.csv'
JOURNAL_FILE = '/root/.openclaw/workspace/paper_journal_bigbeluga.json'

# Config finale
TPL, VL, DVT, BD, RR = 15, 30, 10, 2.0, 1.7
RISK_PCT = 2.7
ENTRY_DELAY = 2

def two_pole_oscillator(close, length):
    sma1 = [sum(close[max(0,i-24):i+1]) / min(25,i+1) for i in range(len(close))]
    sma_n1 = []
    for i in range(len(close)):
        if i < 25: sma_n1.append(0.0); continue
        vals = [close[j] - sma1[j] for j in range(i-24, i+1)]
        mean = sum(vals)/25; variance = sum((v-mean)**2 for v in vals)/25
        stdev = math.sqrt(variance + 1e-10)
        sma_n1.append((close[i] - sma1[i]) / stdev)
    two_p = []; s1 = 0.0; s2 = 0.0; alpha = 2.0/(length+1)
    for i in range(len(sma_n1)):
        s1 = sma_n1[i] if i==0 else (1-alpha)*s1 + alpha*sma_n1[i]
        s2 = s1 if i==0 else (1-alpha)*s2 + alpha*s1
        two_p.append(s2)
    return two_p

def calc_area(high, low, period=100):
    return [(high[i]-low[i]) if i < period else (sum(high[i-period+1:i+1])-sum(low[i-period+1:i+1]))/period for i in range(len(high))]

def vidya_calc(src, vl, vm):
    mom = [0.0] + [src[i]-src[i-1] for i in range(1,len(src))]
    vv = 0.0; vals = []
    for i in range(len(src)):
        if i < vm: vals.append(0.0); continue
        sp = sum(max(0,mom[j]) for j in range(i-vm+1,i+1))
        sn = sum(max(0,-mom[j]) for j in range(i-vm+1,i+1))
        d = sp+sn; acmo = 0.0 if d==0 else abs(100*(sp-sn)/d)
        a = 2.0/(vl+1)
        vv = src[i] if i==0 else a*acmo/100*src[i] + (1-a*acmo/100)*vv
        vals.append(vv)
    return vals

def vidya_system(close, high, low, volume, vidya_length, band_distance):
    src = close; vraw = vidya_calc(src, vidya_length, 20)
    vsm = [sum(vraw[max(0,i-14):i+1])/min(15,i+1) for i in range(len(vraw))]
    atr = []
    for i in range(len(high)):
        if i < 200: atr.append(high[i]-low[i])
        else:
            tr = [max(high[j]-low[j], abs(high[j]-close[j-1]), abs(low[j]-close[j-1])) for j in range(i-199,i+1)]
            atr.append(sum(tr)/200)
    ub = [v+a*bd for v,a,bd in zip(vsm,atr,[band_distance]*len(vsm))]
    lb = [v-a*bd for v,a,bd in zip(vsm,atr,[band_distance]*len(vsm))]
    itu = [False]*len(close)
    for i in range(1,len(close)):
        itu[i] = itu[i-1]
        if src[i] > ub[i] and src[i-1] <= ub[i-1]: itu[i] = True
        if src[i] < lb[i] and src[i-1] >= lb[i-1]: itu[i] = False
    uv = [0.0]; dv = [0.0]; dvp = [0.0]
    for i in range(1,len(close)):
        tc = (itu[i-1] != itu[i])
        u = 0.0 if tc else uv[-1] + (volume[i] if close[i] > open_[i] else 0)
        d = 0.0 if tc else dv[-1] + (volume[i] if close[i] < open_[i] else 0)
        avg = (u+d)/2
        dvp.append((u-d)/avg*100 if avg > 0 else 0)
        uv.append(u); dv.append(d)
    return {'itu':itu,'dvp':dvp}

def cross_over(s1,s2,i): return i>=1 and s1[i]>s2[i] and s1[i-1]<=s2[i-1]
def cross_under(s1,s2,i): return i>=1 and s1[i]<s2[i] and s1[i-1]>=s2[i-1]

def load_data():
    dates, opens, highs, lows, closes, volumes = [], [], [], [], [], []
    with open(DATA_FILE) as f:
        for row in csv.DictReader(f):
            dates.append(row['datetime'])
            opens.append(float(row['open']))
            highs.append(float(row['high']))
            lows.append(float(row['low']))
            closes.append(float(row['close']))
            volumes.append(float(row['volume']))
    return dates, opens, highs, lows, closes, volumes

def load_journal():
    try:
        with open(JOURNAL_FILE) as f:
            return json.load(f)
    except:
        return {
            'initial_capital': 10000, 'capital': 10000,
            'trade_list': [], 'equity_history': [],
            'open_position': None, 'last_signal_time': None,
        }

def save_journal(j):
    with open(JOURNAL_FILE, 'w') as f:
        json.dump(j, f, indent=2)

def run():
    main()

def main():
    print(f"🔬 BigBeluga Forward Test — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    dates, opens, highs, lows, closes, volumes = load_data()
    global open_
    open_ = opens
    
    n = len(closes)
    last_time = dates[-1]
    
    # Check we have enough data
    if n < 300:
        print("❌ Dati insufficienti")
        return
    
    # Calculate indicators on full data
    two_p = two_pole_oscillator(closes, TPL)
    two_pp = [0.0]*4 + two_p[:-4]
    area = calc_area(highs, lows)
    vid = vidya_system(closes, highs, lows, volumes, VL, BD)
    
    # Find signal on last completed candle (index n-1-2 because signal needs 2 candles delay)
    # Signal must be at index n-3 (3 candles ago) so entry is at n-1 (last completed candle)
    # Actually: signal at i → entry at i+2 → we check if the last completed candle is the entry
    sig_idx = n - 1 - ENTRY_DELAY  # signal at this candle
    
    if sig_idx < 200:
        print("❌ Non abbastanza dati per il segnale")
        return
    
    signal = None
    if cross_over(two_p, two_pp, sig_idx) and two_p[sig_idx] < 0.5 and vid['itu'][sig_idx] and vid['dvp'][sig_idx] > DVT:
        signal = {
            'type': 'LONG',
            'direction': 1,
            'signal_time': dates[sig_idx],
            'entry_idx': sig_idx + ENTRY_DELAY,
            'sl_price': lows[sig_idx] - area[sig_idx],
            'two_p': two_p[sig_idx],
            'dvp': vid['dvp'][sig_idx],
        }
    elif cross_under(two_p, two_pp, sig_idx) and two_p[sig_idx] > -0.5 and not vid['itu'][sig_idx] and vid['dvp'][sig_idx] < -DVT:
        signal = {
            'type': 'SHORT',
            'direction': -1,
            'signal_time': dates[sig_idx],
            'entry_idx': sig_idx + ENTRY_DELAY,
            'sl_price': highs[sig_idx] + area[sig_idx],
            'two_p': two_p[sig_idx],
            'dvp': vid['dvp'][sig_idx],
        }
    
    # Load journal
    journal = load_journal()
    
    # Check open position for SL/TP
    open_pos = journal.get('open_position')
    new_trade = None
    
    if open_pos:
        entry_time = open_pos.get('entry_time')
        entry_price = open_pos['entry_price']
        sl = open_pos['sl_price']
        tp = open_pos['tp_price']
        side = open_pos['side']
        direction = 1 if side == 'LONG' else -1
        
        # Check if SL or TP hit on last candle
        last_candle = n - 1
        hit_sl = (direction == 1 and lows[last_candle] <= sl) or (direction == -1 and highs[last_candle] >= sl)
        hit_tp = (direction == 1 and highs[last_candle] >= tp) or (direction == -1 and lows[last_candle] <= tp)
        
        if hit_sl or hit_tp:
            exit_price = sl if hit_sl else tp
            rpt = abs(entry_price - sl) / entry_price if direction == 1 else abs(sl - entry_price) / entry_price
            pnl = -rpt if hit_sl else rpt * RR
            position = journal['capital'] * (RISK_PCT/100) / max(rpt, 0.0001)
            actual_pnl = position * pnl
            
            journal['capital'] += actual_pnl
            journal['trade_list'].append({
                'entry_time': entry_time,
                'exit_time': dates[last_candle],
                'side': side,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pnl_pct': round(pnl * 100, 2),
                'pnl': round(actual_pnl, 2),
            })
            # Equity history
            ts = int(datetime.strptime(dates[last_candle], '%Y-%m-%d %H:%M:%S').timestamp() * 1000)
            journal.setdefault('equity_history', []).append({'ts': ts, 'equity': round(journal['capital'], 2)})
            journal['open_position'] = None
            
            result = "✅ WIN" if pnl > 0 else "❌ LOSS"
            print(f"{result} | {side} | Entry: ${entry_price:.0f} | Exit: ${exit_price:.0f} | PnL: {pnl*100:+.2f}% | Capital: ${journal['capital']:.0f}")
            save_journal(journal)
            return  # Exit and let next cron check for new signals
    
    # Check if we have a new signal and no open position
    if signal and not open_pos:
        # Check we haven't already used this signal
        last_sig_time = journal.get('last_signal_time')
        if last_sig_time == signal['signal_time']:
            print(f"⏭️ Segnale già processato: {signal['signal_time']}")
            new_trade = None
        else:
            new_trade = signal
    
    if new_trade:
        sl_price = new_trade['sl_price']
        entry_price = closes[new_trade['entry_idx']]
        
        if sl_price <= 0:
            print(f"⏭️ SL invalido: {sl_price}")
            save_journal(journal)
            return
        
        direction = new_trade['direction']
        if direction == 1:
            risk_amt = entry_price - sl_price
            tp_price = entry_price + risk_amt * RR
        else:
            risk_amt = sl_price - entry_price
            tp_price = entry_price - risk_amt * RR
        
        if risk_amt <= 0:
            print(f"⏭️ Rischio zero")
            save_journal(journal)
            return
        
        rpt = risk_amt / entry_price
        position = journal['capital'] * (RISK_PCT/100) / max(rpt, 0.0001)
        
        journal['open_position'] = {
            'side': new_trade['type'],
            'entry_time': dates[new_trade['entry_idx']],
            'entry_price': entry_price,
            'sl_price': sl_price,
            'tp_price': tp_price,
            'risk_pct': round(rpt * 100, 2),
            'position_size': round(position, 2),
        }
        journal['last_signal_time'] = new_trade['signal_time']
        
        # Equity history for entry
        ts = int(datetime.strptime(dates[new_trade['entry_idx']], '%Y-%m-%d %H:%M:%S').timestamp() * 1000)
        journal.setdefault('equity_history', []).append({'ts': ts, 'equity': round(journal['capital'], 2)})
        
        print(f"🟢 NEW {new_trade['type']} | Entry: ${entry_price:.0f} | SL: ${sl_price:.0f} | TP: ${tp_price:.0f} | Risk: {rpt*100:.2f}% | DVP: {new_trade['dvp']:.1f}")
        save_journal(journal)
    else:
        if open_pos:
            op = open_pos
            print(f"📌 Posizione aperta: {op['side']} @ ${op['entry_price']:.0f} | SL: ${op['sl_price']:.0f} | TP: ${op['tp_price']:.0f}")
        else:
            print(f"📭 Nessun segnale | ultima candela: {dates[-1]}")
    
    save_journal(journal)

if __name__ == '__main__':
    main()
