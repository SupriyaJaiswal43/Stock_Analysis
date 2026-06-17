"""
NSE Stock Analyzer - Responsive Web Version
============================================
• Live data via yfinance ONLY
• 3 Timeframes: 1H, 4H, 1D
• Heikin Ashi candles
• Compact Card UI — Mobile + Tablet + Desktop friendly
• Minimal scroll with tabbed timeframe view
"""

import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime
import time
import warnings
warnings.filterwarnings("ignore")

# ── CONFIG ─────────────────────────────────────────────────────────
TIMEFRAMES = ["1h", "4h", "1d"]
LOOKBACK_DAYS = 60
BUY_RSI, BUY_STOCH = 40, 20
SELL_RSI, SELL_STOCH = 70, 80
RSI_PERIOD = 14
STOCH_K, STOCH_D = 14, 3
MACD_FAST, MACD_SLOW, MACD_SIG = 12, 26, 9
BB_PERIOD, BB_STD = 20, 2

NSE_STOCKS = {
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "WIPRO": "WIPRO.NS",
    "AXISBANK": "AXISBANK.NS",
    "BAJFINANCE": "BAJFINANCE.NS",
    "MARUTI": "MARUTI.NS",
    "SUNPHARMA": "SUNPHARMA.NS",
    "TATAMOTORS": "TATAMOTORS.NS",
    "LTIM": "LTIM.NS",
    "HCLTECH": "HCLTECH.NS",
    "KOTAKBANK": "KOTAKBANK.NS",
    "SBIN": "SBIN.NS",
}

# ── PAGE CONFIG ────────────────────────────────────────────────────
st.set_page_config(
    page_title="NSE Signals",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── RESPONSIVE CSS ─────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base Reset ── */
* { box-sizing: border-box; }

/* ── App Background ── */
.stApp { background: #0f1117; color: #e8eaf0; }
.block-container { padding: 1rem 1rem 2rem !important; max-width: 1200px !important; }

/* ── Header ── */
.app-header {
    text-align: center;
    padding: 0.75rem 0 0.5rem;
    border-bottom: 1px solid #2a2d3a;
    margin-bottom: 1rem;
}
.app-header h1 {
    font-size: clamp(1.2rem, 4vw, 1.8rem);
    font-weight: 700;
    color: #ffffff;
    margin: 0;
    letter-spacing: -0.5px;
}
.app-header .subtitle {
    font-size: 0.75rem;
    color: #6b7280;
    margin-top: 2px;
}

/* ── Signal Rules Bar ── */
.rules-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1rem;
    justify-content: center;
}
.rule-pill {
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.3px;
}
.rule-buy  { background: #0d2b1a; color: #4ade80; border: 1px solid #1a5c38; }
.rule-sell { background: #2b0d0d; color: #f87171; border: 1px solid #5c1a1a; }
.rule-hold { background: #2b2200; color: #fbbf24; border: 1px solid #5c4a00; }
.rule-ha   { background: #1a1f2e; color: #93c5fd; border: 1px solid #2a3a5c; }

/* ── Stock Card Grid ── */
.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 0.75rem;
    margin-top: 0.5rem;
}

/* ── Individual Stock Card ── */
.stock-card {
    background: #1a1d27;
    border: 1px solid #2a2d3a;
    border-radius: 12px;
    padding: 0.85rem 1rem;
    transition: border-color 0.2s;
}
.stock-card:hover { border-color: #3a3f54; }

/* Card Header */
.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.6rem;
}
.stock-name {
    font-size: 0.95rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: 0.3px;
}
.ltp-block { text-align: right; }
.ltp-price {
    font-size: 0.9rem;
    font-weight: 600;
    color: #e8eaf0;
}
.ltp-change {
    font-size: 0.72rem;
    font-weight: 600;
}
.pos { color: #4ade80; }
.neg { color: #f87171; }

/* Signal Row */
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
.sig-buy  { background: #0d2b1a; color: #4ade80; border: 1px solid #1a5c38; }
.sig-sell { background: #2b0d0d; color: #f87171; border: 1px solid #5c1a1a; }
.sig-hold { background: #2b2200; color: #fbbf24; border: 1px solid #5c4a00; }
.sig-wait { background: #1a1f2e; color: #6b7280; border: 1px solid #2a3a5c; }

/* RSI / Stoch mini row */
.metrics-row {
    display: flex;
    gap: 0.4rem;
}
.metric-chip {
    flex: 1;
    background: #0f1117;
    border: 1px solid #2a2d3a;
    border-radius: 6px;
    padding: 4px 6px;
    text-align: center;
}
.metric-chip .m-label {
    font-size: 0.58rem;
    color: #6b7280;
    display: block;
}
.metric-chip .m-val {
    font-size: 0.8rem;
    font-weight: 600;
    color: #c8cfe0;
}

/* Strength bar */
.strength-wrap {
    margin-top: 0.55rem;
}
.strength-label {
    display: flex;
    justify-content: space-between;
    font-size: 0.6rem;
    color: #6b7280;
    margin-bottom: 3px;
}
.strength-bar {
    height: 4px;
    border-radius: 2px;
    background: #2a2d3a;
    overflow: hidden;
}
.strength-fill {
    height: 100%;
    border-radius: 2px;
    transition: width 0.4s ease;
}
.s-high { background: linear-gradient(90deg, #16a34a, #4ade80); }
.s-mid  { background: linear-gradient(90deg, #d97706, #fbbf24); }
.s-low  { background: linear-gradient(90deg, #b91c1c, #f87171); }

/* ── Summary Table ── */
.summary-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.78rem;
    margin-top: 0.5rem;
}
.summary-table th {
    background: #1a1d27;
    color: #6b7280;
    font-weight: 600;
    padding: 8px 10px;
    text-align: left;
    border-bottom: 1px solid #2a2d3a;
    font-size: 0.7rem;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.summary-table td {
    padding: 7px 10px;
    border-bottom: 1px solid #1a1d27;
    color: #c8cfe0;
    vertical-align: middle;
}
.summary-table tr:hover td { background: #1a1d27; }

.td-sig {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.68rem;
    font-weight: 700;
}

/* ── Tabs Override ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #1a1d27;
    border-radius: 8px;
    padding: 4px;
    border: 1px solid #2a2d3a;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px;
    color: #6b7280;
    font-size: 0.8rem;
    padding: 6px 16px;
}
.stTabs [aria-selected="true"] {
    background: #2a2d3a !important;
    color: #fff !important;
}

/* ── Refresh button ── */
.stButton > button {
    background: #1e3a5f;
    color: #93c5fd;
    border: 1px solid #2a4a7f;
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 600;
    padding: 6px 20px;
    width: 100%;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: #2a4a7f;
    color: #bfdbfe;
}

/* ── Spinner ── */
.stSpinner { color: #4ade80 !important; }

/* ── Mobile ── */
@media (max-width: 600px) {
    .block-container { padding: 0.5rem 0.5rem 2rem !important; }
    .card-grid { grid-template-columns: 1fr; gap: 0.5rem; }
    .summary-table { font-size: 0.7rem; }
    .summary-table th, .summary-table td { padding: 6px 6px; }
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
                         interval=interval, progress=False, auto_adjust=True, timeout=20)
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
    ha["BB_MID"], ha["BB_UP"], ha["BB_LO"] = (
        ha["HA_Close"].rolling(BB_PERIOD).mean(),
        ha["HA_Close"].rolling(BB_PERIOD).mean() + BB_STD * ha["HA_Close"].rolling(BB_PERIOD).std(),
        ha["HA_Close"].rolling(BB_PERIOD).mean() - BB_STD * ha["HA_Close"].rolling(BB_PERIOD).std(),
    )
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
    for tf in TIMEFRAMES:
        tf_res = []
        for name, ticker in NSE_STOCKS.items():
            try:
                r = analyse_stock(name, ticker, tf)
                if r: tf_res.append(r)
                time.sleep(0.15)
            except:
                continue
        results_by_tf[tf] = tf_res

    top_10 = list(NSE_STOCKS.keys())[:10]
    if results_by_tf.get("1h"):
        top_10 = [r["Stock"] for r in sorted(results_by_tf["1h"], key=lambda x: x["Change"], reverse=True)[:10]]
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

def stock_card_html(name, r1h, r4h, r1d):
    # Use 1H as primary for LTP / Change
    ltp = r1h["LTP"] if r1h else (r1d["LTP"] if r1d else 0)
    chg = r1h["Change"] if r1h else (r1d["Change"] if r1d else 0)
    chg_cls = "pos" if chg >= 0 else "neg"
    chg_sym = "▲" if chg >= 0 else "▼"
    avg_str = int(np.mean([r["Strength"] for r in [r1h, r4h, r1d] if r]))

    def tf_badge(r, label):
        if not r:
            return f'<div class="tf-badge sig-wait"><span class="tf-label">{label}</span>–</div>'
        sc = SIG_CLASS.get(r["Signal"], "sig-wait")
        ic = SIG_ICON.get(r["Signal"], "WAIT")
        return f'<div class="tf-badge {sc}"><span class="tf-label">{label}</span>{ic}</div>'

    sig_row = f"""
    <div class="sig-row">
        {tf_badge(r1h, "1H")}
        {tf_badge(r4h, "4H")}
        {tf_badge(r1d, "1D")}
    </div>"""

    def metric_chip(label, val):
        return f'<div class="metric-chip"><span class="m-label">{label}</span><span class="m-val">{val}</span></div>'

    metrics = ""
    if r1h:
        metrics = f"""
        <div class="metrics-row">
            {metric_chip("RSI 1H", r1h['RSI'])}
            {metric_chip("SK 1H", r1h['SK'])}
            {metric_chip("RSI 1D", r1d['RSI'] if r1d else '–')}
            {metric_chip("SK 1D", r1d['SK'] if r1d else '–')}
        </div>"""

    return f"""
    <div class="stock-card">
        <div class="card-header">
            <span class="stock-name">{name}</span>
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
    for stock in top_10:
        r1h = all_res.get((stock, "1h"))
        r4h = all_res.get((stock, "4h"))
        r1d = all_res.get((stock, "1d"))
        ltp = r1h["LTP"] if r1h else "–"
        chg = r1h["Change"] if r1h else 0
        chg_cls = "pos" if chg >= 0 else "neg"

        def td_sig(r):
            if not r: return '<span class="td-sig sig-wait">–</span>'
            sc = TD_CLASS.get(r["Signal"], "sig-wait")
            return f'<span class="td-sig {sc}">{SIG_ICON.get(r["Signal"], "–")}</span>'

        rows += f"""<tr>
            <td><strong style="color:#fff">{stock}</strong></td>
            <td class="{chg_cls}">₹{ltp:,.0f}</td>
            <td class="{chg_cls}">{"▲" if chg>=0 else "▼"}{abs(chg):.1f}%</td>
            <td>{td_sig(r1h)}</td>
            <td>{td_sig(r4h)}</td>
            <td>{td_sig(r1d)}</td>
            <td style="color:#6b7280;font-size:0.65rem">{r1h['As_of'] if r1h else '–'}</td>
        </tr>"""

    return f"""
    <table class="summary-table">
        <thead><tr>
            <th>Stock</th><th>LTP</th><th>Chg</th>
            <th>1H</th><th>4H</th><th>1D</th><th>Updated</th>
        </tr></thead>
        <tbody>{rows}</tbody>
    </table>"""

# ── MAIN UI ────────────────────────────────────────────────────────
# Header
st.markdown(f"""
<div class="app-header">
    <h1>📊 NSE Top 10 — Multi-Timeframe Signals</h1>
    <div class="subtitle">🕐 {datetime.now().strftime('%d %b %Y, %H:%M')} IST &nbsp;|&nbsp; Heikin Ashi &nbsp;|&nbsp; Live via Yahoo Finance</div>
</div>""", unsafe_allow_html=True)

# Rules bar
st.markdown(f"""
<div class="rules-bar">
    <span class="rule-pill rule-buy">▲ BUY: RSI &gt; {BUY_RSI} &amp; Stoch &gt; {BUY_STOCH}</span>
    <span class="rule-pill rule-sell">▼ SELL: RSI &lt; {SELL_RSI} &amp; Stoch &lt; {SELL_STOCH}</span>
    <span class="rule-pill rule-hold">● HOLD: No clear signal</span>
    <span class="rule-pill rule-ha">📊 Heikin Ashi Candles</span>
</div>""", unsafe_allow_html=True)

# Refresh
col_r1, col_r2, col_r3 = st.columns([3, 1, 3])
with col_r2:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

# Fetch
with st.spinner("📈 Fetching live data..."):
    results_by_tf, top_10_names = get_all_data()

all_res = {}
for tf, res_list in results_by_tf.items():
    for r in res_list:
        if r: all_res[(r["Stock"], tf)] = r

# Tabs: Cards View / Summary Table
tab1, tab2 = st.tabs(["🃏 Signal Cards", "📋 Summary Table"])

with tab1:
    cards_html = '<div class="card-grid">'
    for stock in top_10_names:
        r1h = all_res.get((stock, "1h"))
        r4h = all_res.get((stock, "4h"))
        r1d = all_res.get((stock, "1d"))
        cards_html += stock_card_html(stock, r1h, r4h, r1d)
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)

with tab2:
    st.markdown(summary_table_html(top_10_names, all_res), unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align:center; margin-top:2rem; font-size:0.65rem; color:#4b5563; border-top:1px solid #2a2d3a; padding-top:0.75rem;">
    ⚠️ Educational purposes only. Not financial advice. &nbsp;|&nbsp; Data: Yahoo Finance &nbsp;|&nbsp; 15 NSE stocks tracked
</div>""", unsafe_allow_html=True)
