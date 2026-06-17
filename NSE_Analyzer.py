import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime, timedelta
import json
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

# Alpha Vantage API Key (Free - signup at alphavantage.co)
# You can get your own free key from: https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_KEY = "5C75RZIQ6LMJDQRN"  # Replace with your key for more requests

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

def get_signal(rsi, stk):
    if pd.isna(rsi) or pd.isna(stk):
        return "WAIT"
    if rsi > BUY_RSI and stk > BUY_STOCH:
        return "BUY"
    if rsi < SELL_RSI and stk < SELL_STOCH:
        return "SELL"
    return "HOLD"

# ── FETCH DATA FROM MULTIPLE SOURCES ─────────────────────────────
def fetch_from_yfinance(ticker):
    """Try to fetch from Yahoo Finance"""
    try:
        import yfinance as yf
        df = yf.download(ticker, period="60d", interval="1h", progress=False, auto_adjust=True, timeout=15)
        if df is not None and len(df) > 20:
            return df
    except:
        pass
    return None

def fetch_from_alphavantage(ticker):
    """Try to fetch from Alpha Vantage"""
    try:
        # Remove .NS for Alpha Vantage
        symbol = ticker.replace(".NS", "")
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}&outputsize=compact"
        
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if "Time Series (Daily)" in data:
            ts = data["Time Series (Daily)"]
            df_data = []
            for date, values in list(ts.items())[:60]:
                df_data.append({
                    "Date": date,
                    "Open": float(values["1. open"]),
                    "High": float(values["2. high"]),
                    "Low": float(values["3. low"]),
                    "Close": float(values["4. close"]),
                    "Volume": float(values["5. volume"])
                })
            
            df = pd.DataFrame(df_data)
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.set_index("Date")
            df = df.sort_index()
            return df
    except:
        pass
    return None

def fetch_stock_data(ticker):
    """Fetch data from multiple sources"""
    # Try Yahoo Finance first
    df = fetch_from_yfinance(ticker)
    if df is not None:
        return df, "Yahoo Finance"
    
    # Try Alpha Vantage
    df = fetch_from_alphavantage(ticker)
    if df is not None:
        return df, "Alpha Vantage"
    
    return None, None

# ── ANALYSE STOCK ──────────────────────────────────────────────────
def analyse_stock(name, ticker):
    try:
        df, source = fetch_stock_data(ticker)
        
        if df is None or len(df) < 20:
            return None
        
        # Heikin Ashi
        ha = to_heikin_ashi(df)
        
        # Indicators
        ha["RSI"] = calc_rsi(ha["HA_Close"], RSI_PERIOD)
        ha["SK"], ha["SD"] = calc_stoch(ha["HA_High"], ha["HA_Low"], ha["HA_Close"], STOCH_K, STOCH_D)
        
        # Latest values
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
        
        # Signal with emoji
        if signal == "BUY":
            signal_display = "🟢 BUY"
        elif signal == "SELL":
            signal_display = "🔴 SELL"
        else:
            signal_display = "🟡 HOLD"
        
        return {
            "Stock": name,
            "LTP (₹)": ltp,
            "Change %": chg,
            "RSI": rsi,
            "Stoch %K": stk,
            "Signal": signal_display,
            "Signal Text": signal,
            "Data Source": source,
            "Data Points": len(df)
        }
        
    except Exception as e:
        print(f"Error with {name}: {e}")
        return None

# ── FALLBACK DATA (When no API works) ────────────────────────────
def get_fallback_data():
    """Return sample data when APIs fail"""
    fallback_data = [
        {"Stock": "RELIANCE", "LTP (₹)": 2850.50, "Change %": 2.5, "RSI": 65.4, "Stoch %K": 72.3, "Signal": "🟢 BUY", "Signal Text": "BUY"},
        {"Stock": "TCS", "LTP (₹)": 3900.00, "Change %": 1.8, "RSI": 58.2, "Stoch %K": 45.6, "Signal": "🟡 HOLD", "Signal Text": "HOLD"},
        {"Stock": "INFY", "LTP (₹)": 1700.00, "Change %": -1.2, "RSI": 35.8, "Stoch %K": 18.4, "Signal": "🔴 SELL", "Signal Text": "SELL"},
        {"Stock": "HDFCBANK", "LTP (₹)": 1680.00, "Change %": 0.8, "RSI": 52.3, "Stoch %K": 38.7, "Signal": "🟡 HOLD", "Signal Text": "HOLD"},
        {"Stock": "ICICIBANK", "LTP (₹)": 1200.00, "Change %": 3.2, "RSI": 72.1, "Stoch %K": 85.6, "Signal": "🟢 BUY", "Signal Text": "BUY"},
        {"Stock": "WIPRO", "LTP (₹)": 570.00, "Change %": -0.5, "RSI": 42.8, "Stoch %K": 28.9, "Signal": "🟡 HOLD", "Signal Text": "HOLD"},
        {"Stock": "AXISBANK", "LTP (₹)": 1150.00, "Change %": 1.5, "RSI": 48.3, "Stoch %K": 32.1, "Signal": "🟡 HOLD", "Signal Text": "HOLD"},
        {"Stock": "TATAMOTORS", "LTP (₹)": 1050.00, "Change %": 4.2, "RSI": 78.5, "Stoch %K": 92.4, "Signal": "🔴 SELL", "Signal Text": "SELL"},
    ]
    return fallback_data

# ── MAIN ANALYSIS ──────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_all_stocks():
    results = []
    failed = []
    used_fallback = False
    
    # Try to fetch real data
    for name, ticker in NSE_STOCKS.items():
        result = analyse_stock(name, ticker)
        if result:
            results.append(result)
        else:
            failed.append(name)
        time.sleep(0.3)  # Small delay
    
    # If no data fetched, use fallback
    if len(results) == 0:
        used_fallback = True
        fallback_data = get_fallback_data()
        results = fallback_data
    
    # Sort by absolute change
    results.sort(key=lambda x: abs(x["Change %"]), reverse=True)
    
    return results[:10], failed, used_fallback

# ── STREAMLIT UI ──────────────────────────────────────────────────
st.set_page_config(
    page_title="NSE Stock Signals",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .buy { background-color: #C6EFCE; color: #276221; padding: 2px 10px; border-radius: 10px; font-weight: bold; }
    .sell { background-color: #FFC7CE; color: #9C0006; padding: 2px 10px; border-radius: 10px; font-weight: bold; }
    .hold { background-color: #FFEB9C; color: #9C5700; padding: 2px 10px; border-radius: 10px; font-weight: bold; }
    .title { font-size: 28px; font-weight: bold; text-align: center; color: #1F3864; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="title">📊 NSE Stock Signals</p>', unsafe_allow_html=True)
st.caption(f"🕐 {datetime.now().strftime('%d-%b-%Y %H:%M:%S')} IST")

# Rules
col1, col2, col3 = st.columns(3)
col1.info(f"🟢 **BUY:** RSI > {BUY_RSI} & Stoch > {BUY_STOCH}")
col2.warning("🟡 **HOLD:** No clear signal")
col3.error(f"🔴 **SELL:** RSI < {SELL_RSI} & Stoch < {SELL_STOCH}")

if st.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Fetch and display
with st.spinner("📈 Fetching data..."):
    data, failed, used_fallback = fetch_all_stocks()

if data:
    df = pd.DataFrame(data)
    
    # Display
    def highlight_signal(val):
        if "BUY" in str(val):
            return 'background-color: #C6EFCE; color: #276221; font-weight: bold'
        elif "SELL" in str(val):
            return 'background-color: #FFC7CE; color: #9C0006; font-weight: bold'
        elif "HOLD" in str(val):
            return 'background-color: #FFEB9C; color: #9C5700; font-weight: bold'
        return ''
    
    # Show data
    display_df = df[['Stock', 'LTP (₹)', 'Change %', 'RSI', 'Stoch %K', 'Signal']]
    st.dataframe(
        display_df.style.applymap(highlight_signal, subset=['Signal']),
        use_container_width=True,
        height=400
    )
    
    # Summary
    col1, col2, col3, col4 = st.columns(4)
    buys = len(df[df['Signal'] == '🟢 BUY'])
    sells = len(df[df['Signal'] == '🔴 SELL'])
    
    col1.metric("🟢 BUY", buys)
    col2.metric("🔴 SELL", sells)
    col3.metric("📈 Avg RSI", round(df['RSI'].mean(), 1))
    col4.metric("📊 Total", len(df))
    
    # Show warning if using fallback
    if used_fallback:
        st.warning("⚠️ Using demo data (APIs temporarily unavailable)")
    
    # Download
    csv = df.to_csv(index=False)
    st.download_button(
        "📥 Download CSV",
        csv,
        f"NSE_Signals_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        "text/csv",
        use_container_width=True
    )
    
    # Detail view
    with st.expander("📋 Detailed View", expanded=False):
        for _, row in df.iterrows():
            sig = row['Signal']
            cls = "buy" if "BUY" in sig else ("sell" if "SELL" in sig else "hold")
            col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 2, 2])
            col1.write(f"**{row['Stock']}**")
            col2.write(f"₹{row['LTP (₹)']:.2f}")
            col3.write(f"{row['Change %']:.1f}%")
            col4.write(f"{row['RSI']:.1f}")
            col5.write(f"{row['Stoch %K']:.1f}")
            col6.markdown(f'<span class="{cls}">{sig}</span>', unsafe_allow_html=True)
            st.divider()

else:
    st.error("❌ No data available")
    st.info("💡 Try:\n- Refresh after 1 minute\n- Check internet connection\n- Use demo data below")

    # Demo data button
    if st.button("📊 Show Demo Data"):
        demo = get_fallback_data()
        df_demo = pd.DataFrame(demo)
        st.dataframe(df_demo, use_container_width=True)

st.markdown("---")
st.caption("⚠️ **Disclaimer:** Educational only. Not financial advice.")
st.caption(f"📊 Watchlist: {len(NSE_STOCKS)} stocks")
