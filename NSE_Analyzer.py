"""
NSE Stock Analyzer - NIFTY 50 Top 10 (Light Theme)
===================================================
• Live data via yfinance ONLY
• 3 Timeframes: 1H, 4H, 1D
• Heikin Ashi candles
• Custom Signal: BUY (RSI>40 & Stoch>20) | SELL (RSI<70 & Stoch<80)
• Top 10 from NIFTY 50 stocks
• Light & Clean Design
• Mobile + Laptop Responsive
• Created by Supriya Jaiswal
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime
import time
import warnings
warnings.filterwarnings("ignore")

# ── CONFIG ─────────────────────────────────────────────────────────
TIMEFRAMES = ["1h", "4h", "1d"]
LOOKBACK_DAYS = 30
BUY_RSI, BUY_STOCH = 40, 20
SELL_RSI, SELL_STOCH = 70, 80
RSI_PERIOD = 14
STOCH_K, STOCH_D = 14, 3

# ── NIFTY 50 STOCKS ────────────────────────────────────────────────
NIFTY_50 = {
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "INFY": "INFY.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "HINDUNILVR": "HINDUNILVR.NS",
    "ITC": "ITC.NS",
    "SBIN": "SBIN.NS",
    "BHARTIARTL": "BHARTIARTL.NS",
    "KOTAKBANK": "KOTAKBANK.NS",
    "LT": "LT.NS",
    "AXISBANK": "AXISBANK.NS",
    "WIPRO": "WIPRO.NS",
    "TITAN": "TITAN.NS",
    "HCLTECH": "HCLTECH.NS",
    "ASIANPAINT": "ASIANPAINT.NS",
    "ADANIPORTS": "ADANIPORTS.NS",
    "SUNPHARMA": "SUNPHARMA.NS",
    "BAJFINANCE": "BAJFINANCE.NS",
    "NTPC": "NTPC.NS",
    "POWERGRID": "POWERGRID.NS",
    "M&M": "M&M.NS",
    "MARUTI": "MARUTI.NS",
    "TATAMOTORS": "TATAMOTORS.NS",
    "ULTRACEMCO": "ULTRACEMCO.NS",
    "ADANIENT": "ADANIENT.NS",
    "HDFCLIFE": "HDFCLIFE.NS",
    "SBILIFE": "SBILIFE.NS",
    "TATASTEEL": "TATASTEEL.NS",
    "JSWSTEEL": "JSWSTEEL.NS",
    "TECHM": "TECHM.NS",
    "INDUSINDBK": "INDUSINDBK.NS",
    "BAJAJFINSV": "BAJAJFINSV.NS",
    "NESTLEIND": "NESTLEIND.NS",
    "DIVISLAB": "DIVISLAB.NS",
    "ONGC": "ONGC.NS",
    "COALINDIA": "COALINDIA.NS",
    "HINDALCO": "HINDALCO.NS",
    "GRASIM": "GRASIM.NS",
    "DRREDDY": "DRREDDY.NS",
    "BRITANNIA": "BRITANNIA.NS",
    "EICHERMOT": "EICHERMOT.NS",
    "APOLLOHOSP": "APOLLOHOSP.NS",
    "HEROMOTOCO": "HEROMOTOCO.NS",
    "SHREECEM": "SHREECEM.NS",
    "CIPLA": "CIPLA.NS",
    "TATACONSUM": "TATACONSUM.NS",
    "UPL": "UPL.NS",
    "BAJAJ-AUTO": "BAJAJ-AUTO.NS",
    "BPCL": "BPCL.NS",
}

# ── PAGE CONFIG ────────────────────────────────────────────────────
st.set_page_config(
    page_title="NIFTY 50 Top 10",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── LIGHT THEME CSS ────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base ── */
* { box-sizing: border-box; }
.stApp { background: #f5f7fa; color: #1a2332; }
.block-container { padding: 1rem 1rem 2rem !important; max-width: 1200px !important; }

/* ── Header ── */
.app-header {
    text-align: center;
    padding: 0.75rem 0 0.5rem;
    border-bottom: 2px solid #e8ecf1;
    margin-bottom: 1rem;
    background: white;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.app-header h1 {
    font-size: clamp(1.2rem, 4vw, 1.8rem);
    font-weight: 700;
    color: #1a2332;
    margin: 0;
}
.app-header .subtitle {
    font-size: 0.75rem;
    color: #6b7a8f;
    margin-top: 2px;
}

/* ── Rules Bar ── */
.rules-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1rem;
    justify-content: center;
}
.rule-pill {
    padding: 4px 14px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.3px;
}
.rule-buy  { background: #e6f7e6; color: #1a7a3a; border: 1px solid #b8e0b8; }
.rule-sell { background: #fde8e8; color: #b91c1c; border: 1px solid #f5c6c6; }
.rule-hold { background: #fef7e0; color: #9c7c1a; border: 1px solid #f5e6b8; }
.rule-ha   { background: #e8f0fe; color: #1a4a7a; border: 1px solid #c6d8f5; }

/* ── Card Grid ── */
.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 0.75rem;
    margin-top: 0.5rem;
}

/* ── Stock Card ── */
.stock-card {
    background: white;
    border: 1px solid #e8ecf1;
    border-radius: 12px;
    padding: 0.85rem 1rem;
    transition: all 0.2s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.stock-card:hover {
    border-color: #c8d0db;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    transform: translateY(-1px);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.6rem;
}
.stock-name {
    font-size: 0.95rem;
    font-weight: 700;
    color: #1a2332;
}
.ltp-block { text-align: right; }
.ltp-price {
    font-size: 0.9rem;
    font-weight: 600;
    color: #1a2332;
}
.ltp-change {
    font-size: 0.72rem;
    font-weight: 600;
}
.pos { color: #1a8a3a; }
.neg { color: #c92a2a; }

/* ── Signal Badges ── */
.sig-row {
    display: flex;
    gap: 0.4rem;
    margin-bottom: 0.6rem;
    flex-wrap: wrap;
}
.tf-badge {
    flex: 1;
    min-width: 72px;
    text-align: center;
    padding: 5px 4px;
    border-radius: 8px;
    font-size: 0.68rem;
    font-weight: 700;
}
.tf-label {
    font-size: 0.6rem;
    opacity: 0.7;
    margin-bottom: 2px;
    display: block;
}
.sig-buy  { background: #d4edda; color: #155724; border: 1px solid #b8e0b8; }
.sig-sell { background: #f8d7da; color: #721c24; border: 1px solid #f5c6c6; }
.sig-hold { background: #fff3cd; color: #856404; border: 1px solid #f5e6b8; }
.sig-wait { background: #e9ecef; color: #6c757d; border: 1px solid #d5d8dc; }

/* ── Metrics ── */
.metrics-row {
    display: flex;
    gap: 0.4rem;
}
.metric-chip {
    flex: 1;
    background: #f8f9fa;
    border: 1px solid #e8ecf1;
    border-radius: 6px;
    padding: 4px 6px;
    text-align: center;
}
.metric-chip .m-label {
    font-size: 0.58rem;
    color: #6b7a8f;
    display: block;
}
.metric-chip .m-val {
    font-size: 0.8rem;
    font-weight: 600;
    color: #1a2332;
}

/* ── Strength Bar ── */
.strength-wrap {
    margin-top: 0.55rem;
}
.strength-label {
    display: flex;
    justify-content: space-between;
    font-size: 0.6rem;
    color: #6b7a8f;
    margin-bottom: 3px;
}
.strength-bar {
    height: 4px;
    border-radius: 2px;
    background: #e8ecf1;
    overflow: hidden;
}
.strength-fill {
    height: 100%;
    border-radius: 2px;
    transition: width 0.4s ease;
}
.s-high { background: linear-gradient(90deg, #28a745, #5dd87a); }
.s-mid  { background: linear-gradient(90deg, #d4a017, #f5c842); }
.s-low  { background: linear-gradient(90deg, #c92a2a, #f06060); }

/* ── Summary Table ── */
.summary-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.78rem;
    margin-top: 0.5rem;
    background: white;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.summary-table th {
    background: #f0f2f5;
    color: #4a5a6f;
    font-weight: 600;
    padding: 10px 12px;
    text-align: left;
    border-bottom: 2px solid #e8ecf1;
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}
.summary-table td {
    padding: 8px 12px;
    border-bottom: 1px solid #e8ecf1;
    color: #1a2332;
    vertical-align: middle;
}
.summary-table tr:hover td { background: #f8f9fa; }
.summary-table tr:last-child td { border-bottom: none; }

.td-sig {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 6px;
    font-size: 0.67rem;
    font-weight: 700;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: white;
    border-radius: 10px;
    padding: 4px;
    border: 1px solid #e8ecf1;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px;
    color: #6b7a8f;
    font-size: 0.8rem;
    padding: 6px 16px;
}
.stTabs [aria-selected="true"] {
    background: #1a2332 !important;
    color: white !important;
}

/* ── Refresh Button ── */
.stButton > button {
    background: #1a2332;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 600;
    padding: 6px 20px;
    width: 100%;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: #2a3a5a;
    color: white;
    transform: scale(1.02);
}

/* ── Mobile ── */
@media (max-width: 600px) {
    .block-container { padding: 0.5rem 0.5rem 2rem !important; }
    .card-grid { grid-template-columns: 1fr; gap: 0.5rem; }
    .summary-table { font-size: 0.68rem; }
    .summary-table th, .summary-table td { padding: 5px 6px; }
}
</style>
""", unsafe_allow_html=True)

# ── HELPERS ────────────────────────────────────────────────────────
def to_heikin_ashi(df):
    ha = df.copy()
    ha["HA_Close"] = (df["Open"] + df["High"] + df["Low"] + df["Close"]) / 4
    ha["HA_Open"] = ha["HA_Close"].copy()
    ha.iloc[0, ha.columns.get_loc("HA_Open")] = (df["Open"].iloc[0] + df["Close"].iloc[0]) / 2
    for i in range(1, len(ha)):
        ha.iloc[i, ha.columns.get_loc("HA_Open")] = (
            ha.iloc[i-1]["HA_Open"] + ha.iloc[i-1]["HA_Close"]) / 2
    ha["HA_High"] = ha[["HA_Open", "HA_Close", "High"]].max(axis=1)
    ha["HA_Low"]  = ha[["HA_Open", "HA_Close", "Low"]].min(axis=1)
    return ha

def calc_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(com=period-1, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(com=period-1, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def calc_stoch(high, low, close, k=14, d=3):
    ll = low.rolling(k).min()
    hh = high.rolling(k).max()
    pk = 100 * (close - ll) / (hh - ll).replace(0, np.nan)
    return pk, pk.rolling(d).mean()

def calc_macd(close, fast=12, slow=26, sig=9):
    ml = close.ewm(span=fast, adjust=False).mean() - close.ewm(span=slow, adjust=False).mean()
    sl = ml.ewm(span=sig, adjust=False).mean()
    return ml, sl, ml - sl

def get_signal(rsi, stk):
    if pd.isna(rsi) or pd.isna(stk):
        return "WAIT"
    if rsi > BUY_RSI and stk > BUY_STOCH:
        return "BUY"
    if rsi < SELL_RSI and stk < SELL_STOCH:
        return "SELL"
    return "HOLD"

def signal_strength(rsi, stk, macd_h, vol, avg_vol):
    if pd.isna(rsi) or pd.isna(stk):
        return 0
    score = 0
    if rsi > 40:   score += min(35, int((rsi - 40) / 30 * 70))
    if rsi < 70:   score += min(35, int((70 - rsi) / 30 * 70))
    if stk > 20:   score += min(35, int((stk - 20) / 60 * 70))
    if stk < 80:   score += min(35, int((80 - stk) / 60 * 70))
    if not pd.isna(macd_h):
        score += 20 if (macd_h > 0 and rsi > 40) or (macd_h < 0 and rsi < 70) else 5
    if not pd.isna(avg_vol) and avg_vol > 0 and vol / avg_vol > 1.5:
        score += 10
    return min(100, score)

def fetch_live_data(ticker, interval):
    try:
        df = yf.download(ticker, period=f"{LOOKBACK_DAYS}d",
                         interval=interval, progress=False, auto_adjust=True, timeout=15)
        if df is not None and len(df) > RSI_PERIOD + 5:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            return df[~df.index.duplicated(keep="last")].sort_index(), True
        return None, False
    except:
        return None, False

def analyse_stock(name, ticker, interval):
    df, ok = fetch_live_data(ticker, interval)
    if not ok or df is None:
        return None
    ha = to_heikin_ashi(df)
    ha["RSI"] = calc_rsi(ha["HA_Close"], RSI_PERIOD)
    ha["SK"], ha["SD"] = calc_stoch(ha["HA_High"], ha["HA_Low"], ha["HA_Close"], STOCH_K, STOCH_D)
    ha["MACD"], ha["MSIG"], ha["MHIST"] = calc_macd(ha["HA_Close"])
    ha["VOLAVG"] = ha["Volume"].rolling(20).mean()
    ha["SUPP"] = ha["HA_Low"].rolling(20).min()
    ha["RES"]  = ha["HA_High"].rolling(20).max()

    lat  = ha.iloc[-1]
    prev = ha.iloc[-2] if len(ha) > 1 else lat

    rsi  = round(float(lat["RSI"]), 1) if pd.notna(lat["RSI"]) else 50.0
    sk   = round(float(lat["SK"]),  1) if pd.notna(lat["SK"])  else 50.0
    sd   = round(float(lat["SD"]),  1) if pd.notna(lat["SD"])  else 50.0
    ltp  = round(float(lat["HA_Close"]), 2)
    chg  = round((ltp - float(prev["HA_Close"])) / float(prev["HA_Close"]) * 100, 2) if prev["HA_Close"] != 0 else 0
    mh   = float(lat["MHIST"]) if pd.notna(lat["MHIST"]) else 0
    va   = float(lat["VOLAVG"]) if pd.notna(lat["VOLAVG"]) else float("nan")
    sig  = get_signal(rsi, sk)
    str_ = signal_strength(rsi, sk, mh, float(lat["Volume"]) if pd.notna(lat["Volume"]) else 0, va)

    return {
        "Stock": name, "Ticker": ticker, "Timeframe": interval,
        "LTP": ltp, "Change": chg,
        "RSI": rsi, "SK": sk, "SD": sd,
        "Signal": sig, "Strength": str_,
        "MACD_H": round(mh, 4),
        "Support": round(float(lat["SUPP"]), 2) if pd.notna(lat["SUPP"]) else None,
        "Resistance": round(float(lat["RES"]), 2) if pd.notna(lat["RES"]) else None,
        "As_of": ha.index[-1].strftime("%d-%b %H:%M"),
    }

@st.cache_data(ttl=300)
def get_all_data():
    results_by_tf = {}
    
    progress_text = st.empty()
    progress_bar = st.progress(0)
    
    total = len(NIFTY_50) * len(TIMEFRAMES)
    current = 0
    
    for tf in TIMEFRAMES:
        tf_res = []
        for name, ticker in NIFTY_50.items():
            current += 1
            progress_text.text(f"📈 Analysing {name} ({tf})...")
            progress_bar.progress(current / total)
            
            try:
                r = analyse_stock(name, ticker, tf)
                if r: 
                    tf_res.append(r)
                time.sleep(0.1)
            except:
                continue
        results_by_tf[tf] = tf_res
    
    progress_text.text("✅ Analysis complete!")
    progress_bar.empty()
    
    # Top 10 based on 1H Change
    top_10 = list(NIFTY_50.keys())[:10]
    if results_by_tf.get("1h"):
        valid = [r for r in results_by_tf["1h"] if r is not None]
        if valid:
            top_10 = [r["Stock"] for r in sorted(valid, key=lambda x: x["Change"], reverse=True)[:10]]
    
    return results_by_tf, top_10

# ── HTML BUILDERS ──────────────────────────────────────────────────
SIG_CLASS = {"BUY": "sig-buy", "SELL": "sig-sell", "HOLD": "sig-hold", "WAIT": "sig-wait"}
SIG_ICON  = {"BUY": "▲ BUY", "SELL": "▼ SELL", "HOLD": "● HOLD", "WAIT": "… WAIT"}
TD_CLASS  = {"BUY": "sig-buy", "SELL": "sig-sell", "HOLD": "sig-hold", "WAIT": "sig-wait"}

def strength_bar_html(val):
    cls = "s-high" if val >= 65 else ("s-mid" if val >= 35 else "s-low")
    return f"""
    <div class="strength-wrap">
        <div class="strength-label"><span>Signal Strength</span><span>{val}%</span></div>
        <div class="strength-bar"><div class="strength-fill {cls}" style="width:{val}%"></div></div>
    </div>"""

def stock_card_html(name, r1h, r4h, r1d, rank):
    # Safe value extraction with fallbacks
    if r1h:
        ltp = r1h["LTP"]
        chg = r1h["Change"]
        rsi_1h = r1h["RSI"]
        sk_1h = r1h["SK"]
    elif r1d:
        ltp = r1d["LTP"]
        chg = r1d["Change"]
        rsi_1h = "–"
        sk_1h = "–"
    else:
        ltp = 0
        chg = 0
        rsi_1h = "–"
        sk_1h = "–"
    
    # Average strength - handle empty list case
    strengths = []
    if r1h and "Strength" in r1h:
        strengths.append(r1h["Strength"])
    if r4h and "Strength" in r4h:
        strengths.append(r4h["Strength"])
    if r1d and "Strength" in r1d:
        strengths.append(r1d["Strength"])
    
    avg_str = int(np.mean(strengths)) if strengths else 0
    
    chg_cls = "pos" if chg >= 0 else "neg"
    chg_sym = "▲" if chg >= 0 else "▼"

    def tf_badge(r, label):
        if not r:
            return f'<div class="tf-badge sig-wait"><span class="tf-label">{label}</span>–</div>'
        sc = SIG_CLASS.get(r.get("Signal", "WAIT"), "sig-wait")
        ic = SIG_ICON.get(r.get("Signal", "WAIT"), "WAIT")
        return f'<div class="tf-badge {sc}"><span class="tf-label">{label}</span>{ic}</div>'

    sig_row = f"""
    <div class="sig-row">
        {tf_badge(r1h, "1H")}
        {tf_badge(r4h, "4H")}
        {tf_badge(r1d, "1D")}
    </div>"""

    def metric_chip(label, val):
        return f'<div class="metric-chip"><span class="m-label">{label}</span><span class="m-val">{val}</span></div>'

    metrics = f"""
    <div class="metrics-row">
        {metric_chip("RSI 1H", rsi_1h)}
        {metric_chip("SK 1H", sk_1h)}
        {metric_chip("RSI 1D", r1d["RSI"] if r1d else '–')}
        {metric_chip("SK 1D", r1d["SK"] if r1d else '–')}
    </div>"""
    
    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"

    return f"""
    <div class="stock-card">
        <div class="card-header">
            <span class="stock-name">{medal} {name}</span>
            <div class="ltp-block">
                <div class="ltp-price">₹{ltp:,.2f}</div>
                <div class="ltp-change {chg_cls}">{chg_sym} {abs(chg):.2f}%</div>
            </div>
        </div>
        {sig_row}
        {metrics}
        {strength_bar_html(avg_str)}
    </div>"""

def summary_table_html(top_10, all_res):
    rows = ""
    for rank, stock in enumerate(top_10, 1):
        r1h = all_res.get((stock, "1h"))
        r4h = all_res.get((stock, "4h"))
        r1d = all_res.get((stock, "1d"))
        
        if r1h:
            ltp = r1h["LTP"]
            chg = r1h["Change"]
            as_of = r1h["As_of"]
        else:
            ltp = "–"
            chg = 0
            as_of = "–"
            
        chg_cls = "pos" if chg >= 0 else "neg"
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}"

        def td_sig(r):
            if not r:
                return '<span class="td-sig sig-wait">–</span>'
            sc = TD_CLASS.get(r.get("Signal", "WAIT"), "sig-wait")
            return f'<span class="td-sig {sc}">{SIG_ICON.get(r.get("Signal", "WAIT"), "–")}</span>'

        rows += f"""<tr>
            <td style="color:#6b7a8f;font-size:0.7rem">{medal}</td>
            <td><strong style="color:#1a2332">{stock}</strong></td>
            <td class="{chg_cls}">₹{ltp:,.0f}</td>
            <td class="{chg_cls}">{"▲" if chg>=0 else "▼"}{abs(chg):.1f}%</td>
            <td>{td_sig(r1h)}</td>
            <td>{td_sig(r4h)}</td>
            <td>{td_sig(r1d)}</td>
            <td style="color:#6b7a8f;font-size:0.65rem">{as_of}</td>
        </tr>"""

    return f"""
    <table class="summary-table">
        <thead><tr>
            <th>#</th><th>Stock</th><th>LTP</th><th>Chg</th>
            <th>1H</th><th>4H</th><th>1D</th><th>Updated</th>
        </tr></thead>
        <tbody>{rows}</tbody>
    </table>"""

# ── MAIN UI ────────────────────────────────────────────────────────
st.markdown(f"""
<div class="app-header">
    <h1>📊 NIFTY 50 — Top 10 Performers</h1>
    <div class="subtitle">🕐 {datetime.now().strftime('%d %b %Y, %H:%M')} IST &nbsp;|&nbsp; Heikin Ashi &nbsp;|&nbsp; Live via Yahoo Finance &nbsp;|&nbsp; {len(NIFTY_50)} NIFTY 50 stocks tracked</div>
</div>""", unsafe_allow_html=True)

st.markdown(f"""
<div class="rules-bar">
    <span class="rule-pill rule-buy">▲ BUY: RSI &gt; {BUY_RSI} &amp; Stoch &gt; {BUY_STOCH}</span>
    <span class="rule-pill rule-sell">▼ SELL: RSI &lt; {SELL_RSI} &amp; Stoch &lt; {SELL_STOCH}</span>
    <span class="rule-pill rule-hold">● HOLD: No clear signal</span>
    <span class="rule-pill rule-ha">📊 Heikin Ashi Candles</span>
</div>""", unsafe_allow_html=True)

col_r1, col_r2, col_r3 = st.columns([3, 1, 3])
with col_r2:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

with st.spinner("📈 Fetching live data from NIFTY 50..."):
    results_by_tf, top_10_names = get_all_data()

all_res = {}
for tf, res_list in results_by_tf.items():
    for r in res_list:
        if r: 
            all_res[(r["Stock"], tf)] = r

COMPONENT_CSS = """
<style>
* { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
body { background: transparent; color: #1a2332; }

.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 0.7rem;
    padding: 4px 2px 8px;
}
.stock-card {
    background: white;
    border: 1px solid #e8ecf1;
    border-radius: 12px;
    padding: 0.85rem 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.stock-card:hover {
    border-color: #c8d0db;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.6rem;
}
.stock-name { font-size: 0.92rem; font-weight: 700; color: #1a2332; }
.ltp-block { text-align: right; }
.ltp-price { font-size: 0.88rem; font-weight: 600; color: #1a2332; }
.ltp-change { font-size: 0.7rem; font-weight: 600; margin-top: 1px; }
.pos { color: #1a8a3a; }
.neg { color: #c92a2a; }

.sig-row { display: flex; gap: 0.4rem; margin-bottom: 0.6rem; }
.tf-badge {
    flex: 1;
    text-align: center;
    padding: 5px 3px;
    border-radius: 8px;
    font-size: 0.67rem;
    font-weight: 700;
    line-height: 1.3;
}
.tf-label { font-size: 0.58rem; opacity: 0.65; display: block; margin-bottom: 2px; }
.sig-buy  { background: #d4edda; color: #155724; border: 1px solid #b8e0b8; }
.sig-sell { background: #f8d7da; color: #721c24; border: 1px solid #f5c6c6; }
.sig-hold { background: #fff3cd; color: #856404; border: 1px solid #f5e6b8; }
.sig-wait { background: #e9ecef; color: #6c757d; border: 1px solid #d5d8dc; }

.metrics-row { display: flex; gap: 0.4rem; margin-bottom: 0.55rem; }
.metric-chip {
    flex: 1;
    background: #f8f9fa;
    border: 1px solid #e8ecf1;
    border-radius: 6px;
    padding: 4px 5px;
    text-align: center;
}
.m-label { font-size: 0.56rem; color: #6b7a8f; display: block; }
.m-val   { font-size: 0.78rem; font-weight: 600; color: #1a2332; }

.strength-wrap { margin-top: 0.1rem; }
.strength-label { display: flex; justify-content: space-between; font-size: 0.58rem; color: #6b7a8f; margin-bottom: 3px; }
.strength-bar { height: 4px; border-radius: 2px; background: #e8ecf1; overflow: hidden; }
.strength-fill { height: 100%; border-radius: 2px; }
.s-high { background: linear-gradient(90deg, #28a745, #5dd87a); }
.s-mid  { background: linear-gradient(90deg, #d4a017, #f5c842); }
.s-low  { background: linear-gradient(90deg, #c92a2a, #f06060); }

.summary-table { width: 100%; border-collapse: collapse; font-size: 0.78rem; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.summary-table th {
    background: #f0f2f5; color: #4a5a6f; font-weight: 600;
    padding: 8px 12px; text-align: left; border-bottom: 2px solid #e8ecf1;
    font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.4px;
}
.summary-table td { padding: 7px 12px; border-bottom: 1px solid #e8ecf1; color: #1a2332; vertical-align: middle; }
.summary-table tr:hover td { background: #f8f9fa; }
.summary-table tr:last-child td { border-bottom: none; }
.td-sig { display: inline-block; padding: 2px 10px; border-radius: 6px; font-size: 0.67rem; font-weight: 700; }

@media (max-width: 500px) {
    .card-grid { grid-template-columns: 1fr; }
    .summary-table { font-size: 0.68rem; }
    .summary-table th, .summary-table td { padding: 5px 6px; }
}
</style>
"""

if top_10_names and len(top_10_names) > 0:
    tab1, tab2 = st.tabs(["🃏 Signal Cards", "📋 Summary Table"])

    with tab1:
        cards_html = '<div class="card-grid">'
        for idx, stock in enumerate(top_10_names, 1):
            r1h = all_res.get((stock, "1h"))
            r4h = all_res.get((stock, "4h"))
            r1d = all_res.get((stock, "1d"))
            cards_html += stock_card_html(stock, r1h, r4h, r1d, idx)
        cards_html += '</div>'
        n_rows = max(1, -(-len(top_10_names) // 3))
        card_height = n_rows * 240 + 40
        components.html(COMPONENT_CSS + cards_html, height=card_height, scrolling=False)

    with tab2:
        tbl_html = summary_table_html(top_10_names, all_res)
        components.html(COMPONENT_CSS + tbl_html, height=len(top_10_names) * 42 + 80, scrolling=False)
else:
    st.error("❌ No data available. Please try again later.")
    st.info("💡 Tips:\n- Check internet connection\n- Yahoo Finance might be temporarily unavailable\n- Try refreshing after 1-2 minutes")

# ── FOOTER ─────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; margin-top:2rem; font-size:0.7rem; color:#6b7a8f; border-top:2px solid #e8ecf1; padding-top:0.75rem; background:white; border-radius:10px; padding:0.75rem;">
    Created with ❤️ by <strong style="color:#1a2332;">Supriya Jaiswal</strong> &nbsp;|&nbsp; 
    📧 <a href="mailto:supriyajswl43@gmail.com" style="color:#4a6a8a;text-decoration:none;">supriyajswl43@gmail.com</a> &nbsp;|&nbsp;
    ⚠️ Educational purposes only. Not financial advice. &nbsp;|&nbsp; 
    📊 NIFTY 50 stocks tracked
</div>
""", unsafe_allow_html=True)
