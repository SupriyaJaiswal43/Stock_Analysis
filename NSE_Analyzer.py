"""
NSE Stock Analyzer - Premium Design
====================================
• Live data via yfinance ONLY
• 3 Timeframes: 1H, 4H, 1D
• Heikin Ashi candles
• Custom Signal: BUY (RSI>40 & Stoch>20) | SELL (RSI<70 & Stoch<80)
• Top 10 from NIFTY 50 stocks
• Premium UI Design
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

# ── PREMIUM CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

* {
    box-sizing: border-box;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 100%);
}

.block-container {
    padding: 1rem 1rem 2rem !important;
    max-width: 1280px !important;
}

/* ── Premium Header ── */
.premium-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    padding: 1.5rem 2rem;
    border-radius: 20px;
    margin-bottom: 1.5rem;
    box-shadow: 0 20px 60px rgba(15, 23, 42, 0.3);
    position: relative;
    overflow: hidden;
}

.premium-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 60%;
    height: 200%;
    background: linear-gradient(135deg, transparent 40%, rgba(56, 189, 248, 0.05) 100%);
    transform: rotate(-15deg);
}

.header-content {
    position: relative;
    z-index: 1;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
}

.header-left {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.header-icon {
    font-size: 2.5rem;
    background: rgba(56, 189, 248, 0.15);
    padding: 0.5rem;
    border-radius: 16px;
    border: 1px solid rgba(56, 189, 248, 0.2);
}

.header-title h1 {
    font-size: clamp(1.3rem, 3vw, 2rem);
    font-weight: 800;
    color: #ffffff;
    margin: 0;
    letter-spacing: -0.5px;
}

.header-title .subtitle {
    font-size: 0.75rem;
    color: #94a3b8;
    margin-top: 2px;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.header-right {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    flex-wrap: wrap;
}

.live-badge {
    background: #dc2626;
    color: white;
    padding: 4px 14px;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    animation: pulse 2s infinite;
    display: flex;
    align-items: center;
    gap: 6px;
}

.live-dot {
    width: 8px;
    height: 8px;
    background: white;
    border-radius: 50%;
    animation: blink 1s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.85; }
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.2; }
}

.header-stats {
    display: flex;
    gap: 1.5rem;
}

.header-stat {
    text-align: center;
}

.header-stat .num {
    font-size: 1.1rem;
    font-weight: 700;
    color: #ffffff;
    display: block;
}

.header-stat .label {
    font-size: 0.6rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ── Rules Bar ── */
.rules-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    margin-bottom: 1.5rem;
    justify-content: center;
}

.rule-pill {
    padding: 6px 18px;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.3px;
    transition: all 0.3s ease;
    cursor: default;
}

.rule-pill:hover {
    transform: translateY(-2px);
}

.rule-buy {
    background: linear-gradient(135deg, #dcfce7, #bbf7d0);
    color: #15803d;
    border: 1px solid #86efac;
    box-shadow: 0 2px 8px rgba(22, 163, 74, 0.15);
}

.rule-sell {
    background: linear-gradient(135deg, #fee2e2, #fecaca);
    color: #b91c1c;
    border: 1px solid #fca5a5;
    box-shadow: 0 2px 8px rgba(220, 38, 38, 0.15);
}

.rule-hold {
    background: linear-gradient(135deg, #fef3c7, #fde68a);
    color: #92400e;
    border: 1px solid #fcd34d;
    box-shadow: 0 2px 8px rgba(217, 119, 6, 0.15);
}

.rule-ha {
    background: linear-gradient(135deg, #dbeafe, #bfdbfe);
    color: #1d4ed8;
    border: 1px solid #93c5fd;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.15);
}

.rule-stats {
    background: linear-gradient(135deg, #f3e8ff, #e9d5ff);
    color: #6d28d9;
    border: 1px solid #c4b5fd;
    box-shadow: 0 2px 8px rgba(109, 40, 217, 0.15);
}

/* ── Refresh Button ── */
.refresh-wrapper {
    display: flex;
    justify-content: center;
    margin-bottom: 1.5rem;
}

.refresh-btn {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: white;
    border: none;
    padding: 10px 40px;
    border-radius: 12px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.25);
    display: flex;
    align-items: center;
    gap: 8px;
}

.refresh-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(15, 23, 42, 0.35);
}

.refresh-btn:active {
    transform: translateY(0px);
}

/* ── Stats Row ── */
.stats-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
    gap: 0.75rem;
    margin-bottom: 1.5rem;
}

.stat-card {
    background: white;
    padding: 0.8rem 1rem;
    border-radius: 14px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    border: 1px solid #e8ecf1;
    transition: all 0.3s ease;
}

.stat-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.08);
}

.stat-card .stat-value {
    font-size: 1.4rem;
    font-weight: 800;
    display: block;
}

.stat-card .stat-label {
    font-size: 0.6rem;
    color: #6b7a8f;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 2px;
}

.stat-buy .stat-value { color: #16a34a; }
.stat-sell .stat-value { color: #dc2626; }
.stat-hold .stat-value { color: #d97706; }
.stat-rsi .stat-value { color: #2563eb; }
.stat-total .stat-value { color: #7c3aed; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: white;
    border-radius: 14px;
    padding: 6px;
    border: 1px solid #e8ecf1;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    color: #6b7a8f;
    font-size: 0.8rem;
    font-weight: 500;
    padding: 8px 20px;
    transition: all 0.3s ease;
}

.stTabs [data-baseweb="tab"]:hover {
    background: #f1f5f9;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #0f172a, #1e293b) !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.2);
}

/* ── Card Grid ── */
.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
    gap: 0.8rem;
    margin-top: 0.5rem;
}

/* ── Premium Stock Card ── */
.stock-card {
    background: white;
    border-radius: 16px;
    padding: 1rem 1.2rem;
    border: 1px solid #e8ecf1;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    position: relative;
    overflow: hidden;
}

.stock-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #e8ecf1, #e8ecf1);
}

.stock-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(0,0,0,0.1);
    border-color: #c8d0db;
}

.stock-card.buy-border::before {
    background: linear-gradient(90deg, #4ade80, #16a34a);
}

.stock-card.sell-border::before {
    background: linear-gradient(90deg, #f87171, #dc2626);
}

.stock-card.hold-border::before {
    background: linear-gradient(90deg, #fbbf24, #d97706);
}

/* Card Header */
.card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.6rem;
}

.stock-name-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
}

.stock-rank {
    font-size: 0.7rem;
    font-weight: 700;
    color: #6b7a8f;
    background: #f1f5f9;
    padding: 2px 10px;
    border-radius: 999px;
}

.stock-name {
    font-size: 0.95rem;
    font-weight: 700;
    color: #0f172a;
}

.ltp-block {
    text-align: right;
}

.ltp-price {
    font-size: 0.95rem;
    font-weight: 700;
    color: #0f172a;
}

.ltp-change {
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 999px;
}

.ltp-change.pos {
    background: #dcfce7;
    color: #15803d;
}

.ltp-change.neg {
    background: #fee2e2;
    color: #b91c1c;
}

/* Signal Row */
.sig-row {
    display: flex;
    gap: 0.4rem;
    margin-bottom: 0.6rem;
}

.tf-badge {
    flex: 1;
    text-align: center;
    padding: 6px 4px;
    border-radius: 10px;
    font-size: 0.65rem;
    font-weight: 700;
    transition: all 0.2s ease;
}

.tf-badge:hover {
    transform: scale(1.05);
}

.tf-label {
    font-size: 0.55rem;
    opacity: 0.65;
    margin-bottom: 2px;
    display: block;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

.tf-badge.sig-buy {
    background: #dcfce7;
    color: #15803d;
    border: 1px solid #86efac;
}

.tf-badge.sig-sell {
    background: #fee2e2;
    color: #b91c1c;
    border: 1px solid #fca5a5;
}

.tf-badge.sig-hold {
    background: #fef3c7;
    color: #92400e;
    border: 1px solid #fcd34d;
}

.tf-badge.sig-wait {
    background: #f1f5f9;
    color: #6b7a8f;
    border: 1px solid #e2e8f0;
}

/* Metrics */
.metrics-row {
    display: flex;
    gap: 0.4rem;
    margin-bottom: 0.5rem;
}

.metric-chip {
    flex: 1;
    background: #f8fafc;
    border: 1px solid #e8ecf1;
    border-radius: 8px;
    padding: 4px 6px;
    text-align: center;
}

.metric-chip .m-label {
    font-size: 0.5rem;
    color: #6b7a8f;
    display: block;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

.metric-chip .m-val {
    font-size: 0.78rem;
    font-weight: 600;
    color: #0f172a;
}

/* Strength */
.strength-wrap {
    margin-top: 0.4rem;
}

.strength-label {
    display: flex;
    justify-content: space-between;
    font-size: 0.55rem;
    color: #6b7a8f;
    margin-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

.strength-bar {
    height: 5px;
    border-radius: 4px;
    background: #e8ecf1;
    overflow: hidden;
}

.strength-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.8s ease;
}

.strength-fill.s-high {
    background: linear-gradient(90deg, #4ade80, #16a34a);
}

.strength-fill.s-mid {
    background: linear-gradient(90deg, #fbbf24, #d97706);
}

.strength-fill.s-low {
    background: linear-gradient(90deg, #f87171, #dc2626);
}

/* ── Summary Table ── */
.summary-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.78rem;
    background: white;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.summary-table th {
    background: #f8fafc;
    color: #4a5a6f;
    font-weight: 600;
    padding: 12px 14px;
    text-align: left;
    border-bottom: 2px solid #e8ecf1;
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.summary-table td {
    padding: 10px 14px;
    border-bottom: 1px solid #f1f5f9;
    color: #0f172a;
    vertical-align: middle;
}

.summary-table tr:hover td {
    background: #f8fafc;
}

.summary-table tr:last-child td {
    border-bottom: none;
}

.td-sig {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 8px;
    font-size: 0.65rem;
    font-weight: 700;
}

/* ── Footer ── */
.premium-footer {
    text-align: center;
    margin-top: 2rem;
    padding: 1.2rem;
    background: white;
    border-radius: 16px;
    border: 1px solid #e8ecf1;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.premium-footer .footer-text {
    font-size: 0.7rem;
    color: #6b7a8f;
}

.premium-footer .highlight {
    color: #0f172a;
    font-weight: 600;
}

.premium-footer .email-link {
    color: #2563eb;
    text-decoration: none;
    font-weight: 500;
}

.premium-footer .email-link:hover {
    text-decoration: underline;
}

.premium-footer .divider {
    display: inline-block;
    margin: 0 8px;
    color: #d1d5db;
}

/* ── Mobile ── */
@media (max-width: 640px) {
    .header-content {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .header-right {
        width: 100%;
        justify-content: space-between;
    }
    
    .header-stats {
        gap: 1rem;
    }
    
    .header-stat .num {
        font-size: 0.9rem;
    }
    
    .card-grid {
        grid-template-columns: 1fr;
    }
    
    .rules-bar {
        gap: 0.4rem;
    }
    
    .rule-pill {
        font-size: 0.6rem;
        padding: 4px 12px;
    }
    
    .stats-row {
        grid-template-columns: repeat(3, 1fr);
        gap: 0.5rem;
    }
    
    .stat-card .stat-value {
        font-size: 1.1rem;
    }
    
    .summary-table {
        font-size: 0.68rem;
    }
    
    .summary-table th,
    .summary-table td {
        padding: 6px 8px;
    }
}

/* ── Spinner ── */
.stSpinner {
    color: #2563eb !important;
}

/* Hide default elements */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
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
SIG_ICON = {"BUY": "▲ BUY", "SELL": "▼ SELL", "HOLD": "● HOLD", "WAIT": "… WAIT"}

def strength_bar_html(val):
    cls = "s-high" if val >= 65 else ("s-mid" if val >= 35 else "s-low")
    return f"""
    <div class="strength-wrap">
        <div class="strength-label"><span>Signal Strength</span><span>{val}%</span></div>
        <div class="strength-bar"><div class="strength-fill {cls}" style="width:{val}%"></div></div>
    </div>"""

def stock_card_html(name, r1h, r4h, r1d, rank):
    if r1h:
        ltp = r1h["LTP"]
        chg = r1h["Change"]
        rsi_1h = r1h["RSI"]
        sk_1h = r1h["SK"]
        sig_1h = r1h["Signal"]
    elif r1d:
        ltp = r1d["LTP"]
        chg = r1d["Change"]
        rsi_1h = "–"
        sk_1h = "–"
        sig_1h = "WAIT"
    else:
        ltp = 0
        chg = 0
        rsi_1h = "–"
        sk_1h = "–"
        sig_1h = "WAIT"
    
    strengths = []
    if r1h and "Strength" in r1h:
        strengths.append(r1h["Strength"])
    if r4h and "Strength" in r4h:
        strengths.append(r4h["Strength"])
    if r1d and "Strength" in r1d:
        strengths.append(r1d["Strength"])
    
    avg_str = int(np.mean(strengths)) if strengths else 0
    
    # Border class based on primary signal
    border_cls = "buy-border" if sig_1h == "BUY" else ("sell-border" if sig_1h == "SELL" else "hold-border" if sig_1h == "HOLD" else "")
    
    chg_cls = "pos" if chg >= 0 else "neg"
    chg_sym = "▲" if chg >= 0 else "▼"
    
    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"

    def tf_badge(r, label):
        if not r:
            return f'<div class="tf-badge sig-wait"><span class="tf-label">{label}</span>… WAIT</div>'
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

    return f"""
    <div class="stock-card {border_cls}">
        <div class="card-header">
            <div class="stock-name-wrap">
                <span class="stock-rank">{medal}</span>
                <span class="stock-name">{name}</span>
            </div>
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
                return '<span class="td-sig sig-wait">… WAIT</span>'
            sc = SIG_CLASS.get(r.get("Signal", "WAIT"), "sig-wait")
            return f'<span class="td-sig {sc}">{SIG_ICON.get(r.get("Signal", "WAIT"), "WAIT")}</span>'

        rows += f"""<tr>
            <td style="color:#6b7a8f;font-size:0.7rem;font-weight:700;">{medal}</td>
            <td><strong style="color:#0f172a;">{stock}</strong></td>
            <td style="font-weight:600;">₹{ltp:,.0f}</td>
            <td class="{chg_cls}" style="font-weight:600;">{"▲" if chg>=0 else "▼"} {abs(chg):.1f}%</td>
            <td>{td_sig(r1h)}</td>
            <td>{td_sig(r4h)}</td>
            <td>{td_sig(r1d)}</td>
            <td style="color:#6b7a8f;font-size:0.6rem;">{as_of}</td>
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

# ── Premium Header ──
st.markdown(f"""
<div class="premium-header">
    <div class="header-content">
        <div class="header-left">
            <div class="header-icon">📊</div>
            <div class="header-title">
                <h1>NIFTY 50 — Top Performers</h1>
                <div class="subtitle">
                    <span>🕐 {datetime.now().strftime('%d %b %Y, %H:%M')} IST</span>
                    <span>•</span>
                    <span>🕯️ Heikin Ashi</span>
                    <span>•</span>
                    <span>📈 Live Market Data</span>
                </div>
            </div>
        </div>
        <div class="header-right">
            <div class="live-badge">
                <span class="live-dot"></span>
                LIVE
            </div>
            <div class="header-stats">
                <div class="header-stat">
                    <span class="num">{len(NIFTY_50)}</span>
                    <span class="label">Tracked</span>
                </div>
                <div class="header-stat">
                    <span class="num">3</span>
                    <span class="label">Timeframes</span>
                </div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Rules Bar ──
st.markdown(f"""
<div class="rules-bar">
    <span class="rule-pill rule-buy">🟢 BUY: RSI &gt; {BUY_RSI} &amp; Stoch &gt; {BUY_STOCH}</span>
    <span class="rule-pill rule-sell">🔴 SELL: RSI &lt; {SELL_RSI} &amp; Stoch &lt; {SELL_STOCH}</span>
    <span class="rule-pill rule-hold">🟡 HOLD: No clear signal</span>
    <span class="rule-pill rule-ha">🕯️ Heikin Ashi</span>
    <span class="rule-pill rule-stats">📊 Signal Strength: 0-100%</span>
</div>
""", unsafe_allow_html=True)

# ── Refresh Button ──
col1, col2, col3 = st.columns([1, 1.5, 1])
with col2:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── Fetch Data ──
with st.spinner("📈 Fetching live data from NIFTY 50..."):
    results_by_tf, top_10_names = get_all_data()

all_res = {}
for tf, res_list in results_by_tf.items():
    for r in res_list:
        if r: 
            all_res[(r["Stock"], tf)] = r

# ── Stats Row ──
if top_10_names and len(top_10_names) > 0:
    buy_count = 0
    sell_count = 0
    hold_count = 0
    rsi_values = []
    
    for stock in top_10_names:
        r = all_res.get((stock, "1h"))
        if r:
            if r["Signal"] == "BUY":
                buy_count += 1
            elif r["Signal"] == "SELL":
                sell_count += 1
            else:
                hold_count += 1
            rsi_values.append(r["RSI"])
    
    avg_rsi = round(sum(rsi_values) / len(rsi_values), 1) if rsi_values else 0
    
    st.markdown(f"""
    <div class="stats-row">
        <div class="stat-card stat-buy">
            <span class="stat-value">🟢 {buy_count}</span>
            <span class="stat-label">BUY Signals</span>
        </div>
        <div class="stat-card stat-sell">
            <span class="stat-value">🔴 {sell_count}</span>
            <span class="stat-label">SELL Signals</span>
        </div>
        <div class="stat-card stat-hold">
            <span class="stat-value">🟡 {hold_count}</span>
            <span class="stat-label">HOLD Signals</span>
        </div>
        <div class="stat-card stat-rsi">
            <span class="stat-value">{avg_rsi}</span>
            <span class="stat-label">Avg RSI</span>
        </div>
        <div class="stat-card stat-total">
            <span class="stat-value">{len(top_10_names)}</span>
            <span class="stat-label">Top Stocks</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

COMPONENT_CSS = """
<style>
* { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
body { background: transparent; }

.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 0.7rem;
    padding: 4px 2px 8px;
}

.stock-card {
    background: white;
    border-radius: 16px;
    padding: 1rem 1.2rem;
    border: 1px solid #e8ecf1;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    position: relative;
    overflow: hidden;
}

.stock-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #e8ecf1, #e8ecf1);
}

.stock-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(0,0,0,0.1);
    border-color: #c8d0db;
}

.stock-card.buy-border::before {
    background: linear-gradient(90deg, #4ade80, #16a34a);
}

.stock-card.sell-border::before {
    background: linear-gradient(90deg, #f87171, #dc2626);
}

.stock-card.hold-border::before {
    background: linear-gradient(90deg, #fbbf24, #d97706);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.6rem;
}

.stock-name-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
}

.stock-rank {
    font-size: 0.7rem;
    font-weight: 700;
    color: #6b7a8f;
    background: #f1f5f9;
    padding: 2px 10px;
    border-radius: 999px;
}

.stock-name {
    font-size: 0.95rem;
    font-weight: 700;
    color: #0f172a;
}

.ltp-block { text-align: right; }
.ltp-price { font-size: 0.95rem; font-weight: 700; color: #0f172a; }
.ltp-change { font-size: 0.7rem; font-weight: 600; padding: 2px 10px; border-radius: 999px; }
.ltp-change.pos { background: #dcfce7; color: #15803d; }
.ltp-change.neg { background: #fee2e2; color: #b91c1c; }

.sig-row { display: flex; gap: 0.4rem; margin-bottom: 0.6rem; }
.tf-badge {
    flex: 1;
    text-align: center;
    padding: 6px 4px;
    border-radius: 10px;
    font-size: 0.65rem;
    font-weight: 700;
    transition: all 0.2s ease;
}
.tf-badge:hover { transform: scale(1.05); }
.tf-label { font-size: 0.55rem; opacity: 0.65; margin-bottom: 2px; display: block; text-transform: uppercase; letter-spacing: 0.3px; }
.tf-badge.sig-buy { background: #dcfce7; color: #15803d; border: 1px solid #86efac; }
.tf-badge.sig-sell { background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }
.tf-badge.sig-hold { background: #fef3c7; color: #92400e; border: 1px solid #fcd34d; }
.tf-badge.sig-wait { background: #f1f5f9; color: #6b7a8f; border: 1px solid #e2e8f0; }

.metrics-row { display: flex; gap: 0.4rem; margin-bottom: 0.5rem; }
.metric-chip { flex: 1; background: #f8fafc; border: 1px solid #e8ecf1; border-radius: 8px; padding: 4px 6px; text-align: center; }
.metric-chip .m-label { font-size: 0.5rem; color: #6b7a8f; display: block; text-transform: uppercase; letter-spacing: 0.3px; }
.metric-chip .m-val { font-size: 0.78rem; font-weight: 600; color: #0f172a; }

.strength-wrap { margin-top: 0.4rem; }
.strength-label { display: flex; justify-content: space-between; font-size: 0.55rem; color: #6b7a8f; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.3px; }
.strength-bar { height: 5px; border-radius: 4px; background: #e8ecf1; overflow: hidden; }
.strength-fill { height: 100%; border-radius: 4px; transition: width 0.8s ease; }
.strength-fill.s-high { background: linear-gradient(90deg, #4ade80, #16a34a); }
.strength-fill.s-mid { background: linear-gradient(90deg, #fbbf24, #d97706); }
.strength-fill.s-low { background: linear-gradient(90deg, #f87171, #dc2626); }

.summary-table { width: 100%; border-collapse: collapse; font-size: 0.78rem; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.summary-table th { background: #f8fafc; color: #4a5a6f; font-weight: 600; padding: 12px 14px; text-align: left; border-bottom: 2px solid #e8ecf1; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.5px; }
.summary-table td { padding: 10px 14px; border-bottom: 1px solid #f1f5f9; color: #0f172a; vertical-align: middle; }
.summary-table tr:hover td { background: #f8fafc; }
.summary-table tr:last-child td { border-bottom: none; }
.td-sig { display: inline-block; padding: 3px 12px; border-radius: 8px; font-size: 0.65rem; font-weight: 700; }

@media (max-width: 500px) {
    .card-grid { grid-template-columns: 1fr; }
    .summary-table { font-size: 0.68rem; }
    .summary-table th, .summary-table td { padding: 6px 8px; }
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
        card_height = n_rows * 230 + 40
        components.html(COMPONENT_CSS + cards_html, height=card_height, scrolling=False)

    with tab2:
        tbl_html = summary_table_html(top_10_names, all_res)
        components.html(COMPONENT_CSS + tbl_html, height=len(top_10_names) * 42 + 80, scrolling=False)
else:
    st.error("❌ No data available. Please try again later.")
    st.info("💡 Tips:\n- Check internet connection\n- Yahoo Finance might be temporarily unavailable\n- Try refreshing after 1-2 minutes")

# ── Premium Footer ──
st.markdown("""
<div class="premium-footer">
    <span class="footer-text">
        Created with ❤️ by <span class="highlight">Supriya Jaiswal</span>
        <span class="divider">|</span>
        📧 <a href="mailto:supriyajswl43@gmail.com" class="email-link">supriyajswl43@gmail.com</a>
        <span class="divider">|</span>
        ⚠️ Educational purposes only. Not financial advice.
        <span class="divider">|</span>
        📊 NIFTY 50 stocks tracked
    </span>
</div>
""", unsafe_allow_html=True)
