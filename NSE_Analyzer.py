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
        df = yf.download(ticker, period="30d",
                         interval=interval, progress=False, auto_adjust=True, timeout=15)
        if df is not None and len(df) > 10:
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
        "Data Points": len(df)
    }

@st.cache_data(ttl=300)
def get_top_10_stocks():
    results_by_tf = {}
    
    # Progress placeholder
    progress_text = st.empty()
    progress_bar = st.progress(0)
    
    total_stocks = len(NSE_STOCKS)
    current = 0
    
    for tf in TIMEFRAMES:
        tf_results = []
        for name, ticker in NSE_STOCKS.items():
            current += 1
            progress_text.text(f"📈 Analysing {name} ({tf})...")
            progress_bar.progress(current / (total_stocks * len(TIMEFRAMES)))
            
            try:
                r = analyse_stock(name, ticker, tf)
                if r is not None:
                    tf_results.append(r)
                time.sleep(0.1)
            except Exception as e:
                continue
        results_by_tf[tf] = tf_results
    
    progress_text.text("✅ Analysis complete!")
    progress_bar.empty()
    
    # Filter stocks that have 1H data
    valid_stocks = []
    if "1h" in results_by_tf:
        for r in results_by_tf["1h"]:
            if r is not None:
                valid_stocks.append(r)
    
    if valid_stocks:
        sorted_stocks = sorted(valid_stocks, key=lambda x: x["Change (%)"], reverse=True)
        top_10_names = [r["Stock"] for r in sorted_stocks[:10]]
    else:
        top_10_names = list(NSE_STOCKS.keys())[:10]
    
    return results_by_tf, top_10_names

# ── STREAMLIT UI ──────────────────────────────────────────────────
st.set_page_config(
    page_title="NSE Stock Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CUSTOM CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-title {
        font-size: 28px !important;
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
    .stock-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        margin: 8px 0;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stock-name {
        font-weight: bold !important;
        font-size: 18px !important;
    }
    .stock-ltp {
        font-size: 16px !important;
        font-weight: bold !important;
    }
    .change-positive {
        color: #28a745 !important;
        font-weight: bold !important;
    }
    .change-negative {
        color: #dc3545 !important;
        font-weight: bold !important;
    }
    .footer {
        background: #1F3864;
        padding: 20px;
        border-radius: 10px;
        margin-top: 30px;
        text-align: center;
    }
    .footer-text {
        color: white !important;
        font-size: 14px !important;
        margin: 2px 0 !important;
    }
    .footer-highlight {
        color: #FFD700 !important;
        font-weight: bold !important;
    }
    .footer-email {
        color: #87CEEB !important;
        font-weight: bold !important;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0.5rem !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ── HEADER ─────────────────────────────────────────────────────────
st.markdown('<p class="main-title">📊 NSE Top 10 Stock Signals</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-title">🕐 {datetime.now().strftime("%d-%b-%Y %H:%M:%S")} IST | Live Data</p>', unsafe_allow_html=True)

# ── RULES ─────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.info("🟢 **BUY**\nRSI > 40 & Stoch > 20")
with col2:
    st.error("🔴 **SELL**\nRSI < 70 & Stoch < 80")
with col3:
    st.warning("🟡 **HOLD**\nNo clear signal")
with col4:
    st.success("🏆 **TOP 10**\nBy 1H Performance")

# ── REFRESH ────────────────────────────────────────────────────────
if st.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# ── FETCH DATA ─────────────────────────────────────────────────────
try:
    with st.spinner("📈 Fetching live data from Yahoo Finance..."):
        results_by_tf, top_10_names = get_top_10_stocks()
    
    all_results = {}
    for tf, res_list in results_by_tf.items():
        for r in res_list:
            if r is not None:
                all_results[(r["Stock"], tf)] = r
    
    # ── CHECK IF WE HAVE DATA ──────────────────────────────────────
    if top_10_names and len(top_10_names) > 0:
        
        # ── SUMMARY METRICS ──────────────────────────────────────────
        st.markdown("### 📊 Summary")
        
        buy_count = 0
        sell_count = 0
        hold_count = 0
        rsi_values = []
        
        for stock in top_10_names:
            r = all_results.get((stock, "1h"))
            if r:
                if r["Signal_Text"] == "BUY":
                    buy_count += 1
                elif r["Signal_Text"] == "SELL":
                    sell_count += 1
                else:
                    hold_count += 1
                rsi_values.append(r["RSI"])
        
        avg_rsi = round(sum(rsi_values) / len(rsi_values), 1) if rsi_values else 0
        
        cols = st.columns(5)
        cols[0].metric("🟢 BUY", buy_count)
        cols[1].metric("🔴 SELL", sell_count)
        cols[2].metric("🟡 HOLD", hold_count)
        cols[3].metric("📈 Avg RSI", avg_rsi)
        cols[4].metric("📊 Total", len(top_10_names))
        
        # ── TOP 10 STOCKS ─────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 🏆 Top 10 Stocks")
        
        for idx, stock in enumerate(top_10_names, 1):
            r1h = all_results.get((stock, "1h"))
            r4h = all_results.get((stock, "4h"))
            r1d = all_results.get((stock, "1d"))
            
            if r1h:
                # Signal badge
                sig = r1h["Signal_Text"]
                badge_class = "badge-buy" if sig == "BUY" else ("badge-sell" if sig == "SELL" else "badge-hold")
                
                # Change
                change = r1h["Change (%)"]
                change_class = "change-positive" if change >= 0 else "change-negative"
                change_icon = "📈" if change >= 0 else "📉"
                
                # 4H and 1D signals
                sig4h = r4h["Signal"] if r4h else "⏳ WAIT"
                sig1d = r1d["Signal"] if r1d else "⏳ WAIT"
                
                st.markdown(f"""
                <div class="stock-card">
                    <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 10px;">
                        <div style="min-width: 40px;">
                            <span style="font-weight: bold; font-size: 18px; color: #1F3864;">#{idx}</span>
                        </div>
                        <div style="flex: 1; min-width: 100px;">
                            <span class="stock-name">{stock}</span>
                        </div>
                        <div style="min-width: 90px;">
                            <span class="stock-ltp">₹{r1h['LTP (₹)']:.2f}</span>
                        </div>
                        <div style="min-width: 80px;">
                            <span class="{change_class}">{change_icon} {change:.2f}%</span>
                        </div>
                        <div style="min-width: 70px; text-align: center;">
                            <span style="font-size: 11px; color: #888;">RSI</span><br>
                            <span style="font-weight: bold;">{r1h['RSI']:.1f}</span>
                        </div>
                        <div style="min-width: 70px; text-align: center;">
                            <span style="font-size: 11px; color: #888;">Stoch</span><br>
                            <span style="font-weight: bold;">{r1h['Stoch %K']:.1f}</span>
                        </div>
                        <div style="min-width: 100px; text-align: center;">
                            <span class="{badge_class}">{r1h['Signal']}</span>
                        </div>
                        <div style="min-width: 80px; text-align: center;">
                            <span style="font-size: 11px; color: #888;">Strength</span><br>
                            <span style="font-weight: bold; color: #1F3864;">{r1h['Strength']}</span>
                        </div>
                    </div>
                    <div style="display: flex; flex-wrap: wrap; gap: 15px; margin-top: 8px; font-size: 12px; color: #888; border-top: 1px solid #f0f0f0; padding-top: 8px;">
                        <span>🕐 1H: {r1h['Signal']}</span>
                        <span>🕓 4H: {sig4h}</span>
                        <span>📅 1D: {sig1d}</span>
                        <span>📊 MACD: {r1h['MACD Hist']:.4f}</span>
                        <span>📦 Data: {r1h['Data Points']} candles</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # ── DETAILED TABLE ───────────────────────────────────────────
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
            st.dataframe(df_table, use_container_width=True)
        
        # ── DOWNLOAD ─────────────────────────────────────────────────
        st.markdown("---")
        
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
        st.info("💡 Tips:\n- Check internet connection\n- Yahoo Finance might be temporarily unavailable\n- Try refreshing after 1-2 minutes")

except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    st.info("🔄 Please refresh the page")

# ── FEATURES ──────────────────────────────────────────────────────
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
        📊 <span class="footer-highlight">NSE Stock Analyzer</span> — Real-time Market Signals
    </p>
    <p class="footer-text" style="font-size: 12px; opacity: 0.7;">
        Created with ❤️ by <span class="footer-highlight">Supriya Jaiswal</span>
    </p>
    <p class="footer-text" style="font-size: 12px;">
        📧 <span class="footer-email">supriyajswl43@gmail.com</span>
    </p>
    <p class="footer-text" style="font-size: 11px; opacity: 0.6; margin-top: 5px;">
        ⚠️ Educational purposes only. Not financial advice.
    </p>
    <p class="footer-text" style="font-size: 10px; opacity: 0.4; margin-top: 3px;">
        © 2026 All Rights Reserved
    </p>
</div>
""", unsafe_allow_html=True)
