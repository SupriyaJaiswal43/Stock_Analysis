"""
NSE Stock Analyzer - Responsive Web App
=======================================
• Live data via yfinance ONLY
• 3 Timeframes: 1H, 4H, 1D
• Heikin Ashi candles
• Custom Signal: BUY (RSI>40 & Stoch>20) | SELL (RSI<70 & Stoch<80)
• Top 10 stocks by performance
• Mobile + Laptop Responsive
• Created by Supriya Jaiswal
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

# SIGNAL RULES
BUY_RSI = 40
BUY_STOCH = 20
SELL_RSI = 70
SELL_STOCH = 80

RSI_PERIOD = 14
STOCH_K = 14
STOCH_D = 3

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

# ── FUNCTIONS ──────────────────────────────────────────────────────
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

def get_signal(rsi, stk):
    if pd.isna(rsi) or pd.isna(stk):
        return "WAIT"
    if rsi > BUY_RSI and stk > BUY_STOCH:
        return "BUY"
    if rsi < SELL_RSI and stk < SELL_STOCH:
        return "SELL"
    return "HOLD"

def get_signal_display(signal):
    if signal == "BUY":
        return "🟢 BUY"
    elif signal == "SELL":
        return "🔴 SELL"
    else:
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

def fetch_live_data(ticker, interval):
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

def analyse_stock(name, ticker, interval):
    df, is_live = fetch_live_data(ticker, interval)
    
    if not is_live or df is None:
        return None
    
    ha = to_heikin_ashi(df.copy())
    ha["RSI"] = calc_rsi(ha["HA_Close"], RSI_PERIOD)
    ha["SK"], ha["SD"] = calc_stoch(ha["HA_High"], ha["HA_Low"], ha["HA_Close"], STOCH_K, STOCH_D)
    ha["MACD"], ha["MSIG"], ha["MHIST"] = calc_macd(ha["HA_Close"])
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

    return {
        "Stock": name,
        "Ticker": ticker,
        "Timeframe": interval,
        "LTP (₹)": ltp,
        "Change (%)": chg,
        "RSI": rsi,
        "Stoch %K": sk,
        "Stoch %D": sd,
        "Signal": get_signal_display(sig),
        "Signal_Text": sig,
        "Strength": str_,
        "MACD Hist": round(mh, 4) if not np.isnan(mh) else 0,
    }

@st.cache_data(ttl=300)
def get_top_10_stocks():
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
    
    if "1h" in results_by_tf and results_by_tf["1h"]:
        sorted_stocks = sorted(results_by_tf["1h"], key=lambda x: x["Change (%)"], reverse=True)
        top_10_names = [r["Stock"] for r in sorted_stocks[:10]]
    else:
        top_10_names = list(NSE_STOCKS.keys())[:10]
    
    return results_by_tf, top_10_names

# ── RESPONSIVE STREAMLIT UI ──────────────────────────────────────
st.set_page_config(
    page_title="NSE Stock Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CUSTOM CSS FOR RESPONSIVE DESIGN ─────────────────────────────
st.markdown("""
<style>
    /* Mobile First Design */
    .main-title {
        font-size: 24px !important;
        font-weight: bold !important;
        text-align: center !important;
        color: #1F3864 !important;
        padding: 10px 0 !important;
    }
    
    .sub-title {
        text-align: center !important;
        color: #666 !important;
        font-size: 14px !important;
        margin-bottom: 15px !important;
    }
    
    /* Signal Badges */
    .badge-buy {
        background-color: #C6EFCE !important;
        color: #276221 !important;
        padding: 4px 12px !important;
        border-radius: 20px !important;
        font-weight: bold !important;
        font-size: 13px !important;
        display: inline-block !important;
    }
    .badge-sell {
        background-color: #FFC7CE !important;
        color: #9C0006 !important;
        padding: 4px 12px !important;
        border-radius: 20px !important;
        font-weight: bold !important;
        font-size: 13px !important;
        display: inline-block !important;
    }
    .badge-hold {
        background-color: #FFEB9C !important;
        color: #9C5700 !important;
        padding: 4px 12px !important;
        border-radius: 20px !important;
        font-weight: bold !important;
        font-size: 13px !important;
        display: inline-block !important;
    }
    .badge-wait {
        background-color: #D9D9D9 !important;
        color: #666666 !important;
        padding: 4px 12px !important;
        border-radius: 20px !important;
        font-weight: bold !important;
        font-size: 13px !important;
        display: inline-block !important;
    }
    
    /* Metric Cards */
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 12px 10px;
        text-align: center;
        border: 1px solid #e9ecef;
        margin: 4px 0;
    }
    .metric-value {
        font-size: 20px !important;
        font-weight: bold !important;
    }
    .metric-label {
        font-size: 11px !important;
        color: #6c757d !important;
        margin-top: 2px !important;
    }
    
    /* Stock Row */
    .stock-row {
        background-color: white;
        border-radius: 8px;
        padding: 12px 10px;
        margin: 6px 0;
        border: 1px solid #e9ecef;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .stock-name {
        font-weight: bold !important;
        font-size: 16px !important;
    }
    .stock-ltp {
        font-size: 15px !important;
        font-weight: bold !important;
    }
    .stock-change-positive {
        color: #28a745 !important;
        font-weight: bold !important;
    }
    .stock-change-negative {
        color: #dc3545 !important;
        font-weight: bold !important;
    }
    
    /* Footer Styles */
    .footer {
        background: linear-gradient(135deg, #1F3864, #2E4D8A);
        padding: 20px 15px;
        border-radius: 12px;
        margin-top: 30px;
        text-align: center;
        border: 1px solid #4a6fa5;
    }
    .footer-text {
        color: #FFFFFF !important;
        font-size: 14px !important;
        margin: 2px 0 !important;
        font-family: 'Arial', sans-serif !important;
    }
    .footer-highlight {
        color: #FFD700 !important;
        font-weight: bold !important;
    }
    .footer-email {
        color: #87CEEB !important;
        font-weight: bold !important;
        text-decoration: none !important;
    }
    .footer-email:hover {
        color: #FFD700 !important;
        text-decoration: underline !important;
    }
    .footer-line {
        border: none;
        height: 1px;
        background: linear-gradient(to right, transparent, #4a6fa5, transparent);
        margin: 8px 0;
    }
    .footer-heart {
        color: #FF6B6B !important;
    }
    .footer-icon {
        font-size: 18px !important;
    }
    
    /* Responsive Footer */
    @media (max-width: 768px) {
        .footer-text {
            font-size: 12px !important;
        }
        .footer {
            padding: 15px 10px !important;
        }
        .footer-icon {
            font-size: 15px !important;
        }
    }
    
    @media (max-width: 480px) {
        .footer-text {
            font-size: 10px !important;
        }
        .footer {
            padding: 12px 8px !important;
        }
    }
    
    /* Responsive Grid */
    @media (max-width: 768px) {
        .main-title {
            font-size: 20px !important;
        }
        .stock-name {
            font-size: 14px !important;
        }
        .metric-value {
            font-size: 16px !important;
        }
        .badge-buy, .badge-sell, .badge-hold, .badge-wait {
            font-size: 11px !important;
            padding: 3px 8px !important;
        }
    }
    
    @media (max-width: 480px) {
        .main-title {
            font-size: 18px !important;
        }
        .stock-name {
            font-size: 13px !important;
        }
        .stock-ltp {
            font-size: 13px !important;
        }
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom scroll */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
    }
    
    /* Container padding */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ── HEADER ─────────────────────────────────────────────────────────
st.markdown('<p class="main-title">📊 NSE Top 10 Stock Signals</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-title">🕐 {datetime.now().strftime("%d-%b-%Y %H:%M:%S")} IST | Live Data</p>', unsafe_allow_html=True)

# ── RULES (Responsive Cards) ─────────────────────────────────────
st.markdown("""
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 8px; margin: 10px 0;">
    <div style="background-color: #C6EFCE; padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #a8d5b3;">
        <span style="font-weight: bold; color: #276221;">🟢 BUY</span><br>
        <span style="font-size: 12px; color: #276221;">RSI > 40 & Stoch > 20</span>
    </div>
    <div style="background-color: #FFC7CE; padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #f5a3a3;">
        <span style="font-weight: bold; color: #9C0006;">🔴 SELL</span><br>
        <span style="font-size: 12px; color: #9C0006;">RSI < 70 & Stoch < 80</span>
    </div>
    <div style="background-color: #FFEB9C; padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #e8d57a;">
        <span style="font-weight: bold; color: #9C5700;">🟡 HOLD</span><br>
        <span style="font-size: 12px; color: #9C5700;">No clear signal</span>
    </div>
    <div style="background-color: #E3F2FD; padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #BBDEFB;">
        <span style="font-weight: bold; color: #0D47A1;">📈 TOP 10</span><br>
        <span style="font-size: 12px; color: #0D47A1;">By 1H Performance</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── REFRESH ────────────────────────────────────────────────────────
col_refresh, col_empty = st.columns([1, 3])
with col_refresh:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── FETCH DATA ─────────────────────────────────────────────────────
with st.spinner("📈 Fetching live data..."):
    results_by_tf, top_10_names = get_top_10_stocks()

all_results = {}
for tf, res_list in results_by_tf.items():
    for r in res_list:
        if r is not None:
            all_results[(r["Stock"], tf)] = r

if top_10_names:
    
    # ── SUMMARY METRICS (Responsive) ──────────────────────────────
    st.markdown("### 📊 Summary")
    
    # Calculate metrics
    buy_count = 0
    sell_count = 0
    hold_count = 0
    
    for stock in top_10_names:
        r = all_results.get((stock, "1h"))
        if r:
            if r["Signal_Text"] == "BUY":
                buy_count += 1
            elif r["Signal_Text"] == "SELL":
                sell_count += 1
            else:
                hold_count += 1
    
    cols = st.columns(5)
    cols[0].metric("🟢 BUY", buy_count)
    cols[1].metric("🔴 SELL", sell_count)
    cols[2].metric("🟡 HOLD", hold_count)
    
    # Calculate average RSI from 1H
    rsi_values = []
    for stock in top_10_names:
        r = all_results.get((stock, "1h"))
        if r:
            rsi_values.append(r["RSI"])
    avg_rsi = round(sum(rsi_values) / len(rsi_values), 1) if rsi_values else 0
    cols[3].metric("📈 Avg RSI", avg_rsi)
    cols[4].metric("📊 Total", len(top_10_names))
    
    # ── TOP 10 STOCKS (Responsive Cards) ──────────────────────────
    st.markdown("---")
    st.markdown("### 🏆 Top 10 Stocks")
    
    for idx, stock in enumerate(top_10_names, 1):
        r1h = all_results.get((stock, "1h"))
        r4h = all_results.get((stock, "4h"))
        r1d = all_results.get((stock, "1d"))
        
        if r1h:
            # Get signal badge class
            sig = r1h["Signal_Text"]
            badge_class = "badge-buy" if sig == "BUY" else ("badge-sell" if sig == "SELL" else "badge-hold")
            
            # Change color
            change = r1h["Change (%)"]
            change_class = "stock-change-positive" if change >= 0 else "stock-change-negative"
            change_icon = "🟢" if change >= 0 else "🔴"
            
            # Card HTML
            st.markdown(f"""
            <div class="stock-row">
                <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 8px;">
                    <div style="min-width: 35px;">
                        <span style="font-weight: bold; color: #888;">#{idx}</span>
                    </div>
                    <div style="flex: 1; min-width: 70px;">
                        <span class="stock-name">{stock}</span>
                    </div>
                    <div style="min-width: 70px; text-align: right;">
                        <span class="stock-ltp">₹{r1h['LTP (₹)']:.2f}</span>
                    </div>
                    <div style="min-width: 60px; text-align: right;">
                        <span class="{change_class}">{change_icon} {change:.2f}%</span>
                    </div>
                    <div style="min-width: 50px; text-align: center;">
                        <span class="metric-label">RSI</span>
                        <div style="font-weight: bold;">{r1h['RSI']:.1f}</div>
                    </div>
                    <div style="min-width: 50px; text-align: center;">
                        <span class="metric-label">Stoch</span>
                        <div style="font-weight: bold;">{r1h['Stoch %K']:.1f}</div>
                    </div>
                    <div style="min-width: 80px; text-align: center;">
                        <span class="{badge_class}">{r1h['Signal']}</span>
                    </div>
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 6px; font-size: 12px; color: #888;">
                    <span>4H: {r4h['Signal'] if r4h else '⏳ WAIT'}</span>
                    <span>|</span>
                    <span>1D: {r1d['Signal'] if r1d else '⏳ WAIT'}</span>
                    <span>|</span>
                    <span>Strength: {r1h['Strength']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # ── DETAILED TABLE (Collapsible) ──────────────────────────────
    with st.expander("📋 View Detailed Table", expanded=False):
        table_data = []
        for stock in top_10_names:
            row = {"Stock": stock}
            for tf in TIMEFRAMES:
                r = all_results.get((stock, tf))
                if r:
                    row[f"{tf}_Signal"] = r["Signal"]
                    row[f"{tf}_RSI"] = r["RSI"]
                    row[f"{tf}_SK"] = r["Stoch %K"]
                    row[f"{tf}_LTP"] = r["LTP (₹)"]
                    row[f"{tf}_Change"] = r["Change (%)"]
                    row[f"{tf}_Strength"] = r["Strength"]
                else:
                    row[f"{tf}_Signal"] = "⏳ WAIT"
                    row[f"{tf}_RSI"] = "-"
                    row[f"{tf}_SK"] = "-"
                    row[f"{tf}_LTP"] = "-"
                    row[f"{tf}_Change"] = "-"
                    row[f"{tf}_Strength"] = "-"
            table_data.append(row)
        
        df_table = pd.DataFrame(table_data)
        
        # Show as dataframe
        display_cols = ['Stock', '1h_Signal', '1h_RSI', '1h_SK', 
                       '4h_Signal', '4h_RSI', '4h_SK',
                       '1d_Signal', '1d_RSI', '1d_SK']
        
        st.dataframe(
            df_table[display_cols],
            use_container_width=True,
            column_config={
                "Stock": "Stock",
                "1h_Signal": "1H Signal",
                "1h_RSI": "1H RSI",
                "1h_SK": "1H SK",
                "4h_Signal": "4H Signal",
                "4h_RSI": "4H RSI",
                "4h_SK": "4H SK",
                "1d_Signal": "1D Signal",
                "1d_RSI": "1D RSI",
                "1d_SK": "1D SK",
            }
        )
    
    # ── DOWNLOAD ────────────────────────────────────────────────────
    st.markdown("---")
    col_download1, col_download2 = st.columns([1, 3])
    with col_download1:
        # Prepare download data
        download_data = []
        for stock in top_10_names:
            row = {"Stock": stock}
            for tf in TIMEFRAMES:
                r = all_results.get((stock, tf))
                if r:
                    row[f"{tf}_Signal"] = r["Signal"]
                    row[f"{tf}_RSI"] = r["RSI"]
                    row[f"{tf}_Stoch"] = r["Stoch %K"]
                    row[f"{tf}_LTP"] = r["LTP (₹)"]
                    row[f"{tf}_Change"] = r["Change (%)"]
                    row[f"{tf}_Strength"] = r["Strength"]
                else:
                    row[f"{tf}_Signal"] = "WAIT"
                    row[f"{tf}_RSI"] = "-"
                    row[f"{tf}_Stoch"] = "-"
                    row[f"{tf}_LTP"] = "-"
                    row[f"{tf}_Change"] = "-"
                    row[f"{tf}_Strength"] = "-"
            download_data.append(row)
        
        df_download = pd.DataFrame(download_data)
        csv = df_download.to_csv(index=False)
        
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"NSE_Signals_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )

else:
    st.error("❌ No data available. Please try again later.")
    st.info("💡 Tips:\n- Check internet connection\n- Refresh after 1-2 minutes")

# ── FEATURES LIST (Collapsible) ──────────────────────────────────
with st.expander("ℹ️ Features & How to Use", expanded=False):
    st.markdown("""
    ### 📊 Features
    
    | Feature | Description |
    |---------|-------------|
    | **Live Data** | Real-time data from Yahoo Finance |
    | **Multi-Timeframe** | 1H, 4H, 1D analysis |
    | **Heikin Ashi** | Smoothed candles for clear trends |
    | **Signal Rules** | BUY: RSI>40 & Stoch>20 \| SELL: RSI<70 & Stoch<80 |
    | **Top 10** | Best performing stocks based on 1H change |
    | **Mobile Friendly** | Works on phone, tablet, laptop |
    
    ### 🎯 How to Use
    
    1. Open this URL on any device
    2. Click **Refresh** for latest data
    3. Check **BUY/SELL/HOLD** signals
    4. Use **Download CSV** for analysis
    
    ### ⚠️ Disclaimer
    
    Educational purposes only. Not financial advice.
    Always verify with your broker before trading.
    """)

# ── FOOTER ─────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    <p class="footer-text">
        <span class="footer-icon">📊</span> 
        <span class="footer-highlight">NSE Stock Analyzer</span> 
        — Real-time Market Signals
    </p>
    <hr class="footer-line">
    <p class="footer-text">
        Created with <span class="footer-heart">❤️</span> by 
        <span class="footer-highlight">Supriya Jaiswal</span>
    </p>
    <p class="footer-text">
        📧 <a href="mailto:supriyajswl43@gmail.com" class="footer-email">supriyajswl43@gmail.com</a>
    </p>
    <p class="footer-text" style="font-size: 11px; opacity: 0.7; margin-top: 5px;">
        ⚠️ Educational purposes only. Not financial advice.
    </p>
    <p class="footer-text" style="font-size: 10px; opacity: 0.5; margin-top: 3px;">
        © 2026 All Rights Reserved
    </p>
</div>
""", unsafe_allow_html=True)
