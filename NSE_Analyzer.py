import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime
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
        return "⏳ WAIT"
    # BUY: RSI > 40 AND Stoch > 20
    if rsi > BUY_RSI and stk > BUY_STOCH:
        return "🟢 BUY"
    # SELL: RSI < 70 AND Stoch < 80
    if rsi < SELL_RSI and stk < SELL_STOCH:
        return "🔴 SELL"
    return "🟡 HOLD"

def get_signal_text(signal):
    if "BUY" in signal:
        return "BUY"
    elif "SELL" in signal:
        return "SELL"
    return "HOLD"

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_and_analyse():
    results = []
    
    for name, ticker in NSE_STOCKS.items():
        try:
            df = yf.download(ticker, period="60d", interval="1h", progress=False, auto_adjust=True)
            
            if df is None or len(df) < 20:
                continue
            
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
            
            # Change %
            if prev["HA_Close"] != 0:
                chg = round((float(lat["HA_Close"]) - float(prev["HA_Close"])) / float(prev["HA_Close"]) * 100, 2)
            else:
                chg = 0
            
            signal = get_signal(rsi, stk)
            
            results.append({
                "Stock": name,
                "LTP (₹)": ltp,
                "Change %": chg,
                "RSI": rsi,
                "Stoch %K": stk,
                "Signal": signal,
                "Signal Text": get_signal_text(signal)
            })
            
        except Exception as e:
            print(f"Error with {name}: {e}")
            continue
    
    # Sort by Change % (Top performers)
    results.sort(key=lambda x: abs(x["Change %"]), reverse=True)
    
    return results[:10]  # Return Top 10

# ── STREAMLIT UI ──────────────────────────────────────────────────
st.set_page_config(
    page_title="NSE Top 10 Signals",
    page_icon="📊",
    layout="wide"
)

# Header
st.markdown("""
<style>
    .main-title {
        font-size: 32px;
        font-weight: bold;
        color: #1F3864;
        text-align: center;
    }
    .sub-title {
        text-align: center;
        color: #666;
        margin-bottom: 20px;
    }
    .buy-badge {
        background-color: #C6EFCE;
        color: #276221;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: bold;
    }
    .sell-badge {
        background-color: #FFC7CE;
        color: #9C0006;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: bold;
    }
    .hold-badge {
        background-color: #FFEB9C;
        color: #9C5700;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">📊 NSE Top 10 Live Signals</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-title">🕐 Updated: {datetime.now().strftime("%d-%b-%Y %H:%M:%S")} IST</p>', unsafe_allow_html=True)

# Rules
col1, col2, col3 = st.columns(3)
with col1:
    st.info(f"🟢 **BUY:** RSI > {BUY_RSI} & Stoch > {BUY_STOCH}")
with col2:
    st.warning("🟡 **HOLD:** No clear signal")
with col3:
    st.error(f"🔴 **SELL:** RSI < {SELL_RSI} & Stoch < {SELL_STOCH}")

# Refresh Button
if st.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Fetch Data
with st.spinner("📈 Fetching live data from Yahoo Finance..."):
    data = fetch_and_analyse()

if data:
    df = pd.DataFrame(data)
    
    # Color coding function
    def highlight_signal(val):
        if "BUY" in str(val):
            return 'background-color: #C6EFCE; color: #276221; font-weight: bold'
        elif "SELL" in str(val):
            return 'background-color: #FFC7CE; color: #9C0006; font-weight: bold'
        elif "HOLD" in str(val):
            return 'background-color: #FFEB9C; color: #9C5700; font-weight: bold'
        return ''
    
    # Display dataframe with styling
    styled_df = df.style.applymap(highlight_signal, subset=['Signal'])
    st.dataframe(styled_df, use_container_width=True, height=400)
    
    # Summary Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    buys = len(df[df['Signal'] == '🟢 BUY'])
    sells = len(df[df['Signal'] == '🔴 SELL'])
    holds = len(df[df['Signal'] == '🟡 HOLD'])
    
    with col1:
        st.metric("🟢 BUY", buys, delta=f"{buys} stocks")
    with col2:
        st.metric("🔴 SELL", sells, delta=f"{sells} stocks")
    with col3:
        st.metric("🟡 HOLD", holds, delta=f"{holds} stocks")
    with col4:
        st.metric("📈 Avg RSI", round(df['RSI'].mean(), 1))
    
    # CSV Download
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"NSE_Signals_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    # Show individual stock details
    st.subheader("📋 Individual Stock Details")
    for idx, row in df.iterrows():
        signal = row['Signal']
        if "BUY" in signal:
            badge = f'<span class="buy-badge">{signal}</span>'
        elif "SELL" in signal:
            badge = f'<span class="sell-badge">{signal}</span>'
        else:
            badge = f'<span class="hold-badge">{signal}</span>'
        
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 3])
        with col1:
            st.write(f"**{row['Stock']}**")
        with col2:
            st.write(f"₹{row['LTP (₹)']}")
        with col3:
            st.write(f"{row['Change %']}%")
        with col4:
            st.write(f"RSI: {row['RSI']}")
        with col5:
            st.markdown(badge, unsafe_allow_html=True)
        st.divider()

else:
    st.error("❌ No data available. Please try again later.")
    st.info("💡 Tips:\n- Check your internet connection\n- Make sure yfinance is working\n- Try refreshing after a few minutes")

# Footer
st.markdown("---")
st.caption("⚠️ **Disclaimer:** Educational purposes only. Not financial advice. Always verify with your broker.")
st.caption(f"📊 Data Source: Yahoo Finance | Total Stocks Analyzed: {len(NSE_STOCKS)}")
