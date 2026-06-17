"""
NSE Stock Analyzer - Web Version (Same Logic as Excel)
==================================================
• Live data via yfinance ONLY
• 3 Timeframes: 1H, 4H, 1D
• Heikin Ashi candles for all timeframes
• Custom Signal: BUY (RSI>40 & Stoch>20) | SELL (RSI<70 & Stoch<80)
• Top 10 stocks by performance
• URL Access - Streamlit Web App
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

# SIGNAL RULES (Same as Excel version)
BUY_RSI = 40
BUY_STOCH = 20
SELL_RSI = 70
SELL_STOCH = 80

RSI_PERIOD = 14
STOCH_K = 14
STOCH_D = 3
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIG = 9
BB_PERIOD = 20
BB_STD = 2

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

# ── HEIKIN ASHI ────────────────────────────────────────────────────
def to_heikin_ashi(df):
    ha = df.copy()
    ha["HA_Close"] = (df["Open"] + df["High"] + df["Low"] + df["Close"]) / 4
    ha["HA_Open"] = ha["HA_Close"].copy()
    ha.iloc[0, ha.columns.get_loc("HA_Open")] = (df["Open"].iloc[0] + df["Close"].iloc[0]) / 2
    for i in range(1, len(ha)):
        ha.iloc[i, ha.columns.get_loc("HA_Open")] = (ha.iloc[i-1]["HA_Open"] + ha.iloc[i-1]["HA_Close"]) / 2
    ha["HA_High"] = ha[["HA_Open", "HA_Close", "High"]].max(axis=1)
    ha["HA_Low"] = ha[["HA_Open", "HA_Close", "Low"]].min(axis=1)
    return ha

# ── INDICATORS ─────────────────────────────────────────────────────
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
    ef = close.ewm(span=fast, adjust=False).mean()
    es = close.ewm(span=slow, adjust=False).mean()
    ml = ef - es
    sl = ml.ewm(span=sig, adjust=False).mean()
    return ml, sl, ml - sl

def calc_bb(close, p=20, s=2):
    sma = close.rolling(p).mean()
    std = close.rolling(p).std()
    return sma, sma + s * std, sma - s * std

def calc_ema(close, p=21):
    return close.ewm(span=p, adjust=False).mean()

# ── SIGNAL FUNCTIONS (Same as Excel) ─────────────────────────────
def get_signal(rsi, stk):
    if pd.isna(rsi) or pd.isna(stk):
        return "⏳ WAIT"
    if rsi > BUY_RSI and stk > BUY_STOCH:
        return "🟢 BUY"
    if rsi < SELL_RSI and stk < SELL_STOCH:
        return "🔴 SELL"
    return "🟡 HOLD"

def signal_strength(rsi, stk, macd_h, vol, avg_vol):
    score = 0
    if pd.isna(rsi) or pd.isna(stk):
        return 0
    if rsi > 40:
        score += min(35, int((rsi - 40) / 30 * 70))
    if rsi < 70:
        score += min(35, int((70 - rsi) / 30 * 70))
    if stk > 20:
        score += min(35, int((stk - 20) / 60 * 70))
    if stk < 80:
        score += min(35, int((80 - stk) / 60 * 70))
    if not pd.isna(macd_h):
        score += 20 if (macd_h > 0 and rsi > 40) or (macd_h < 0 and rsi < 70) else 5
    if not pd.isna(avg_vol) and avg_vol > 0 and vol / avg_vol > 1.5:
        score += 10
    return min(100, score)

def sig_short(sig):
    if not isinstance(sig, str):
        return "WAIT"
    if "BUY" in sig:
        return "BUY"
    if "SELL" in sig:
        return "SELL"
    if "HOLD" in sig:
        return "HOLD"
    return "WAIT"

# ── FETCH LIVE DATA ──────────────────────────────────────────────
def fetch_live_data(ticker, interval):
    """Fetch live data from yfinance"""
    try:
        df = yf.download(ticker, period=f"{LOOKBACK_DAYS}d",
                         interval=interval, progress=False, auto_adjust=True, timeout=20)
        if df is not None and len(df) > RSI_PERIOD + 5:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df[~df.index.duplicated(keep="last")].sort_index()
            return df, True
        return None, False
    except Exception as e:
        return None, False

# ── ANALYSE ────────────────────────────────────────────────────────
def analyse_stock(name, ticker, interval):
    """Analyse single stock for given timeframe"""
    df, is_live = fetch_live_data(ticker, interval)
    
    if not is_live or df is None:
        return None
    
    ha = to_heikin_ashi(df.copy())
    ha["RSI"] = calc_rsi(ha["HA_Close"], RSI_PERIOD)
    ha["SK"], ha["SD"] = calc_stoch(ha["HA_High"], ha["HA_Low"], ha["HA_Close"], STOCH_K, STOCH_D)
    ha["MACD"], ha["MSIG"], ha["MHIST"] = calc_macd(ha["HA_Close"])
    ha["BB_MID"], ha["BB_UP"], ha["BB_LO"] = calc_bb(ha["HA_Close"])
    ha["EMA21"] = calc_ema(ha["HA_Close"], 21)
    ha["EMA9"] = calc_ema(ha["HA_Close"], 9)
    ha["SUPP"] = ha["HA_Low"].rolling(20).min()
    ha["RES"] = ha["HA_High"].rolling(20).max()
    ha["VOLAVG"] = ha["Volume"].rolling(20).mean()

    lat = ha.iloc[-1]
    prev = ha.iloc[-2] if len(ha) > 1 else ha.iloc[-1]
    
    rsi = round(float(lat["RSI"]), 2) if pd.notna(lat["RSI"]) else 50
    sk = round(float(lat["SK"]), 2) if pd.notna(lat["SK"]) else 50
    sd = round(float(lat["SD"]), 2) if pd.notna(lat["SD"]) else 50
    ltp = round(float(lat["HA_Close"]), 2)
    chg = round((float(lat["HA_Close"]) - float(prev["HA_Close"])) / float(prev["HA_Close"]) * 100, 2) if prev["HA_Close"] != 0 else 0
    sig = get_signal(rsi, sk)
    mh = float(lat["MHIST"]) if pd.notna(lat["MHIST"]) else 0
    va = float(lat["VOLAVG"]) if pd.notna(lat["VOLAVG"]) else float("nan")
    str_ = signal_strength(rsi, sk, mh, float(lat["Volume"]) if pd.notna(lat["Volume"]) else 0, va)
    sup = round(float(lat["SUPP"]), 2) if pd.notna(lat["SUPP"]) else None
    res = round(float(lat["RES"]), 2) if pd.notna(lat["RES"]) else None

    # Count signals in history
    signals = ha.apply(lambda r: get_signal(r["RSI"] if pd.notna(r["RSI"]) else 50,
                                            r["SK"] if pd.notna(r["SK"]) else 50), axis=1)
    buy_candles = int((signals == "🟢 BUY").sum())
    sell_candles = int((signals == "🔴 SELL").sum())

    return {
        "Stock": name,
        "Ticker": ticker,
        "Timeframe": interval,
        "LTP (₹)": ltp,
        "Change (%)": chg,
        "RSI": rsi,
        "Stoch %K": sk,
        "Stoch %D": sd,
        "Signal": sig,
        "Strength": str_,
        "MACD Hist": round(mh, 4) if not np.isnan(mh) else 0,
        "BB Upper": round(float(lat["BB_UP"]), 2) if pd.notna(lat["BB_UP"]) else None,
        "BB Lower": round(float(lat["BB_LO"]), 2) if pd.notna(lat["BB_LO"]) else None,
        "Support": sup,
        "Resistance": res,
        "Buy Candles": buy_candles,
        "Sell Candles": sell_candles,
        "As of": ha.index[-1].strftime("%d-%b-%Y %H:%M"),
    }

# ── GET TOP 10 ─────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_top_10_stocks():
    """Get top 10 stocks based on 1H performance"""
    results_by_tf = {}
    
    for tf in TIMEFRAMES:
        tf_results = []
        for name, ticker in NSE_STOCKS.items():
            try:
                r = analyse_stock(name, ticker, tf)
                if r is not None:
                    tf_results.append(r)
                time.sleep(0.2)
            except Exception as e:
                continue
        results_by_tf[tf] = tf_results
    
    # Get top 10 based on 1H Change
    if "1h" in results_by_tf and results_by_tf["1h"]:
        sorted_stocks = sorted(results_by_tf["1h"], key=lambda x: x["Change (%)"], reverse=True)
        top_10_names = [r["Stock"] for r in sorted_stocks[:10]]
    else:
        top_10_names = list(NSE_STOCKS.keys())[:10]
    
    return results_by_tf, top_10_names

# ── STREAMLIT UI ──────────────────────────────────────────────────
st.set_page_config(
    page_title="NSE Top 10 Signals",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .title { font-size: 32px; font-weight: bold; text-align: center; color: #1F3864; }
    .buy { background-color: #C6EFCE; color: #276221; padding: 4px 12px; border-radius: 12px; font-weight: bold; }
    .sell { background-color: #FFC7CE; color: #9C0006; padding: 4px 12px; border-radius: 12px; font-weight: bold; }
    .hold { background-color: #FFEB9C; color: #9C5700; padding: 4px 12px; border-radius: 12px; font-weight: bold; }
    .wait { background-color: #D9D9D9; color: #666666; padding: 4px 12px; border-radius: 12px; font-weight: bold; }
    .strength-high { background-color: #C6EFCE; color: #276221; }
    .strength-mid { background-color: #FFEB9C; color: #9C5700; }
    .strength-low { background-color: #FFC7CE; color: #9C0006; }
</style>
""", unsafe_allow_html=True)

# ── HEADER ─────────────────────────────────────────────────────────
st.markdown('<p class="title">📊 NSE Top 10 - Multi-Timeframe Signals</p>', unsafe_allow_html=True)
st.caption(f"🕐 {datetime.now().strftime('%d-%b-%Y %H:%M:%S')} IST")

# ── RULES ──────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.info(f"🟢 **BUY:** RSI > {BUY_RSI} & Stoch > {BUY_STOCH}")
with col2:
    st.error(f"🔴 **SELL:** RSI < {SELL_RSI} & Stoch < {SELL_STOCH}")
with col3:
    st.warning("🟡 **HOLD:** No clear signal")
with col4:
    st.caption("📊 **Heikin Ashi** candles")

# ── REFRESH ────────────────────────────────────────────────────────
if st.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# ── FETCH DATA ─────────────────────────────────────────────────────
with st.spinner("📈 Fetching live data from Yahoo Finance..."):
    results_by_tf, top_10_names = get_top_10_stocks()

# ── PREPARE DATA FOR DISPLAY ─────────────────────────────────────
all_results = {}
for tf, res_list in results_by_tf.items():
    for r in res_list:
        if r is not None:
            all_results[(r["Stock"], tf)] = r

if top_10_names:
    # ── DASHBOARD ────────────────────────────────────────────────────
    st.markdown("### 📊 Multi-Timeframe Dashboard")
    
    # Prepare data for display
    dash_data = []
    for stock in top_10_names:
        row = {"Stock": stock}
        for tf in TIMEFRAMES:
            r = all_results.get((stock, tf))
            if r:
                row[f"{tf}_RSI"] = r["RSI"]
                row[f"{tf}_SK"] = r["Stoch %K"]
                row[f"{tf}_Signal"] = r["Signal"]
                row[f"{tf}_Strength"] = r["Strength"]
                row[f"{tf}_LTP"] = r["LTP (₹)"]
                row[f"{tf}_Change"] = r["Change (%)"]
            else:
                row[f"{tf}_RSI"] = "-"
                row[f"{tf}_SK"] = "-"
                row[f"{tf}_Signal"] = "⏳ WAIT"
                row[f"{tf}_Strength"] = 0
                row[f"{tf}_LTP"] = "-"
                row[f"{tf}_Change"] = 0
        dash_data.append(row)
    
    df_dash = pd.DataFrame(dash_data)
    
    # Display as columns
    for idx, row in df_dash.iterrows():
        st.divider()
        cols = st.columns([1.5, 1, 1, 1, 1, 1, 1, 1, 1])
        
        # Stock name
        cols[0].markdown(f"**{row['Stock']}**")
        
        # 1H data
        sig1 = row['1h_Signal']
        bg1 = "buy" if "BUY" in sig1 else ("sell" if "SELL" in sig1 else ("hold" if "HOLD" in sig1 else "wait"))
        cols[1].metric("1H RSI", row['1h_RSI'])
        cols[2].metric("1H SK", row['1h_SK'])
        cols[3].markdown(f'<span class="{bg1}">{sig1}</span>', unsafe_allow_html=True)
        
        # 4H data
        sig4 = row['4h_Signal']
        bg4 = "buy" if "BUY" in sig4 else ("sell" if "SELL" in sig4 else ("hold" if "HOLD" in sig4 else "wait"))
        cols[4].metric("4H RSI", row['4h_RSI'])
        cols[5].metric("4H SK", row['4h_SK'])
        cols[6].markdown(f'<span class="{bg4}">{sig4}</span>', unsafe_allow_html=True)
        
        # 1D data
        sigD = row['1d_Signal']
        bgD = "buy" if "BUY" in sigD else ("sell" if "SELL" in sigD else ("hold" if "HOLD" in sigD else "wait"))
        cols[7].metric("1D RSI", row['1d_RSI'])
        cols[8].metric("1D SK", row['1d_SK'])
        
        # Extra row for signals
        st.divider()
        cols2 = st.columns([1.5, 1, 1, 1, 1, 1, 1, 1, 1])
        cols2[0].write("")
        cols2[1].write("")
        cols2[2].write("")
        cols2[3].markdown(f'<span class="{bg1}">{sig1}</span>', unsafe_allow_html=True)
        cols2[4].write("")
        cols2[5].write("")
        cols2[6].markdown(f'<span class="{bg4}">{sig4}</span>', unsafe_allow_html=True)
        cols2[7].write("")
        cols2[8].markdown(f'<span class="{bgD}">{sigD}</span>', unsafe_allow_html=True)

    # ── SUMMARY ─────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📈 Summary")
    
    # Count signals across timeframes
    summary_data = []
    for stock in top_10_names:
        row = {"Stock": stock}
        for tf in TIMEFRAMES:
            r = all_results.get((stock, tf))
            if r:
                row[f"{tf}_Signal"] = r["Signal"]
                row[f"{tf}_LTP"] = r["LTP (₹)"]
                row[f"{tf}_Change"] = r["Change (%)"]
            else:
                row[f"{tf}_Signal"] = "⏳ WAIT"
                row[f"{tf}_LTP"] = "-"
                row[f"{tf}_Change"] = 0
        summary_data.append(row)
    
    df_summary = pd.DataFrame(summary_data)
    
    # Display summary table
    cols = st.columns([2, 2, 2, 2, 2])
    cols[0].write("**Stock**")
    cols[1].write("**1H**")
    cols[2].write("**4H**")
    cols[3].write("**1D**")
    cols[4].write("**LTP**")
    
    for _, row in df_summary.iterrows():
        cols = st.columns([2, 2, 2, 2, 2])
        cols[0].write(row['Stock'])
        
        sig1 = row['1h_Signal']
        bg1 = "buy" if "BUY" in sig1 else ("sell" if "SELL" in sig1 else ("hold" if "HOLD" in sig1 else "wait"))
        cols[1].markdown(f'<span class="{bg1}">{sig1}</span>', unsafe_allow_html=True)
        
        sig4 = row['4h_Signal']
        bg4 = "buy" if "BUY" in sig4 else ("sell" if "SELL" in sig4 else ("hold" if "HOLD" in sig4 else "wait"))
        cols[2].markdown(f'<span class="{bg4}">{sig4}</span>', unsafe_allow_html=True)
        
        sigD = row['1d_Signal']
        bgD = "buy" if "BUY" in sigD else ("sell" if "SELL" in sigD else ("hold" if "HOLD" in sigD else "wait"))
        cols[3].markdown(f'<span class="{bgD}">{sigD}</span>', unsafe_allow_html=True)
        
        # Get LTP from 1H
        r1h = all_results.get((row['Stock'], "1h"))
        cols[4].write(f"₹{r1h['LTP (₹)']:.2f}" if r1h else "-")

    # ── DETAILED VIEW ──────────────────────────────────────────────
    with st.expander("📋 Detailed View (All Metrics)", expanded=False):
        for stock in top_10_names:
            st.markdown(f"**{stock}**")
            tf_data = {}
            for tf in TIMEFRAMES:
                r = all_results.get((stock, tf))
                if r:
                    tf_data[tf] = r
            
            if tf_data:
                detail_cols = st.columns(len(tf_data) + 1)
                detail_cols[0].write("**Metric**")
                for i, tf in enumerate(TIMEFRAMES, 1):
                    detail_cols[i].write(f"**{tf}**")
                
                metrics = ["LTP (₹)", "Change (%)", "RSI", "Stoch %K", "Signal", "Strength", "MACD Hist"]
                for metric in metrics:
                    detail_cols = st.columns(len(tf_data) + 1)
                    detail_cols[0].write(metric)
                    for i, tf in enumerate(TIMEFRAMES, 1):
                        r = tf_data.get(tf)
                        if r:
                            val = r.get(metric, "-")
                            if metric == "Signal":
                                sig = val
                                bg = "buy" if "BUY" in sig else ("sell" if "SELL" in sig else ("hold" if "HOLD" in sig else "wait"))
                                detail_cols[i].markdown(f'<span class="{bg}">{sig}</span>', unsafe_allow_html=True)
                            else:
                                detail_cols[i].write(val)
                        else:
                            detail_cols[i].write("-")
            st.divider()

else:
    st.error("❌ No data available. Please try again later.")

# ── FOOTER ─────────────────────────────────────────────────────────
st.markdown("---")
st.caption("⚠️ **Disclaimer:** Educational purposes only. Not financial advice.")
st.caption(f"📊 Watchlist: {len(NSE_STOCKS)} stocks | Timeframes: 1H, 4H, 1D | Heikin Ashi")
