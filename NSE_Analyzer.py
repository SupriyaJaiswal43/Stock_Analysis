import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime
import time
import warnings
warnings.filterwarnings("ignore")

# ── CONFIG ─────────────────────────────────────────────────────────
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
    return sma, sma+s*std, sma-s*std

def calc_ema(close, p=21):
    return close.ewm(span=p, adjust=False).mean()

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
    if not pd.isna(avg_vol) and avg_vol > 0 and vol/avg_vol > 1.5:
        score += 10
    return min(100, score)

# ── FETCH DATA ─────────────────────────────────────────────────────
def fetch_stock_data(ticker):
    try:
        df = yf.download(ticker, period="60d", interval="1h", progress=False, auto_adjust=True, timeout=20)
        if df is not None and len(df) > 20:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            return df
    except:
        pass
    return None

# ── ANALYSE ────────────────────────────────────────────────────────
def analyse_stock(name, ticker):
    try:
        df = fetch_stock_data(ticker)
        if df is None or len(df) < 20:
            return None
        
        ha = to_heikin_ashi(df)
        ha["RSI"] = calc_rsi(ha["HA_Close"], RSI_PERIOD)
        ha["SK"], ha["SD"] = calc_stoch(ha["HA_High"], ha["HA_Low"], ha["HA_Close"], STOCH_K, STOCH_D)
        ha["MACD"], _, ha["MHIST"] = calc_macd(ha["HA_Close"])
        ha["VOLAVG"] = ha["Volume"].rolling(20).mean()
        
        lat = ha.iloc[-1]
        prev = ha.iloc[-2] if len(ha) > 1 else ha.iloc[-1]
        
        rsi = round(float(lat["RSI"]), 2) if pd.notna(lat["RSI"]) else 50
        stk = round(float(lat["SK"]), 2) if pd.notna(lat["SK"]) else 50
        ltp = round(float(lat["HA_Close"]), 2)
        
        if prev["HA_Close"] != 0:
            chg = round((float(lat["HA_Close"]) - float(prev["HA_Close"])) / float(prev["HA_Close"]) * 100, 2)
        else:
            chg = 0
        
        signal = get_signal(rsi, stk)
        signal_display = get_signal_display(signal)
        
        mh = float(lat["MHIST"]) if pd.notna(lat["MHIST"]) else 0
        vol = float(lat["Volume"]) if pd.notna(lat["Volume"]) else 0
        avg_vol = float(lat["VOLAVG"]) if pd.notna(lat["VOLAVG"]) else 0
        strength = signal_strength(rsi, stk, mh, vol, avg_vol)
        
        return {
            "Stock": name,
            "Ticker": ticker,
            "LTP (₹)": ltp,
            "Change %": chg,
            "RSI": rsi,
            "Stoch %K": stk,
            "Stoch %D": round(float(lat["SD"]), 2) if pd.notna(lat["SD"]) else 0,
            "Signal": signal_display,
            "Signal_Text": signal,
            "Strength": strength,
            "MACD Hist": round(mh, 4),
            "Data Points": len(df)
        }
    except:
        return None

# ── GET TOP 10 ─────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_top_stocks():
    results = []
    failed = []
    
    for name, ticker in NSE_STOCKS.items():
        result = analyse_stock(name, ticker)
        if result:
            results.append(result)
        else:
            failed.append(name)
        time.sleep(0.3)
    
    results.sort(key=lambda x: abs(x["Change %"]), reverse=True)
    return results[:10], failed

# ── STREAMLIT UI ──────────────────────────────────────────────────
st.set_page_config(
    page_title="NSE Top 10 Signals",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .title { font-size: 30px; font-weight: bold; text-align: center; color: #1F3864; }
    .buy { background-color: #C6EFCE; color: #276221; padding: 2px 12px; border-radius: 12px; font-weight: bold; }
    .sell { background-color: #FFC7CE; color: #9C0006; padding: 2px 12px; border-radius: 12px; font-weight: bold; }
    .hold { background-color: #FFEB9C; color: #9C5700; padding: 2px 12px; border-radius: 12px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ── HEADER ─────────────────────────────────────────────────────────
st.markdown('<p class="title">📊 NSE Top 10 Stock Signals</p>', unsafe_allow_html=True)
st.caption(f"🕐 {datetime.now().strftime('%d-%b-%Y %H:%M:%S')} IST")

# ── RULES ──────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.info(f"🟢 **BUY:** RSI > {BUY_RSI} & Stoch > {BUY_STOCH}")
col2.warning("🟡 **HOLD:** No clear signal")
col3.error(f"🔴 **SELL:** RSI < {SELL_RSI} & Stoch < {SELL_STOCH}")

# ── REFRESH ────────────────────────────────────────────────────────
if st.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# ── FETCH DATA ─────────────────────────────────────────────────────
with st.spinner("📈 Fetching live data from Yahoo Finance..."):
    data, failed = get_top_stocks()

if data:
    df = pd.DataFrame(data)
    
    # Display columns
    display_cols = ['Stock', 'LTP (₹)', 'Change %', 'RSI', 'Stoch %K', 'Strength', 'Signal']
    display_df = df[display_cols].copy()
    
    # ── COLOR FUNCTION ──────────────────────────────────────────────
    def highlight_signal(signal):
        if "BUY" in str(signal):
            return 'background-color: #C6EFCE; color: #276221; font-weight: bold'
        elif "SELL" in str(signal):
            return 'background-color: #FFC7CE; color: #9C0006; font-weight: bold'
        elif "HOLD" in str(signal):
            return 'background-color: #FFEB9C; color: #9C5700; font-weight: bold'
        return ''
    
    # ── DISPLAY ─────────────────────────────────────────────────────
    st.subheader("📊 Top 10 Stocks by Performance")
    
    # Method 1: HTML Table with colors
    styled_html = display_df.copy()
    styled_html['Signal'] = styled_html['Signal'].apply(
        lambda x: f'<span style="{highlight_signal(x)}">{x}</span>'
    )
    
    # Display as HTML
    st.markdown(styled_html.to_html(escape=False, index=False), unsafe_allow_html=True)
    
    # ── SUMMARY ─────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📈 Summary")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    buys = len(df[df['Signal_Text'] == 'BUY'])
    sells = len(df[df['Signal_Text'] == 'SELL'])
    holds = len(df[df['Signal_Text'] == 'HOLD'])
    
    col1.metric("🟢 BUY", buys)
    col2.metric("🔴 SELL", sells)
    col3.metric("🟡 HOLD", holds)
    col4.metric("📈 Avg RSI", f"{df['RSI'].mean():.1f}")
    col5.metric("📊 Total", len(df))
    
    # ── DETAILED VIEW ──────────────────────────────────────────────
    with st.expander("📋 Detailed View (All Metrics)", expanded=False):
        st.dataframe(df, use_container_width=True)
    
    # ── DOWNLOAD ────────────────────────────────────────────────────
    st.markdown("---")
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"NSE_Signals_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    # Show failed stocks if any
    if failed:
        with st.expander(f"⚠️ {len(failed)} stocks failed to fetch"):
            st.warning(f"Could not fetch data for: {', '.join(failed)}")

else:
    st.error("❌ No data available. Please try again later.")
    st.info("💡 Try refreshing after 1-2 minutes")

# ── FOOTER ─────────────────────────────────────────────────────────
st.markdown("---")
st.caption("⚠️ **Disclaimer:** Educational purposes only. Not financial advice.")
st.caption(f"📊 Watchlist: {len(NSE_STOCKS)} stocks")
