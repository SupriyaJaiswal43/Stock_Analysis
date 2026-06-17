import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import time
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

def get_signal_display(signal):
    if signal == "BUY":
        return "🟢 BUY"
    elif signal == "SELL":
        return "🔴 SELL"
    else:
        return "🟡 HOLD"

# ── FETCH DATA ─────────────────────────────────────────────────────
def fetch_stock_data(ticker):
    """Fetch data from Yahoo Finance with retry"""
    for attempt in range(3):
        try:
            df = yf.download(
                ticker,
                period="60d",
                interval="1h",
                progress=False,
                auto_adjust=True,
                timeout=20
            )
            if df is not None and len(df) > 20:
                # Handle multi-index columns
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                return df
        except Exception as e:
            if attempt < 2:
                time.sleep(1)
            continue
    return None

# ── ANALYSE STOCK ──────────────────────────────────────────────────
def analyse_stock(name, ticker):
    try:
        df = fetch_stock_data(ticker)
        
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
        signal_display = get_signal_display(signal)
        
        return {
            "Stock": name,
            "LTP (₹)": ltp,
            "Change %": chg,
            "RSI": rsi,
            "Stoch %K": stk,
            "Signal": signal_display,
            "Signal_Text": signal  # For sorting/filtering
        }
        
    except Exception as e:
        return None

# ── FALLBACK DATA ──────────────────────────────────────────────────
def get_fallback_data():
    return [
        {"Stock": "RELIANCE", "LTP (₹)": 2850.50, "Change %": 2.5, "RSI": 65.4, "Stoch %K": 72.3, "Signal": "🟢 BUY", "Signal_Text": "BUY"},
        {"Stock": "TCS", "LTP (₹)": 3900.00, "Change %": 1.8, "RSI": 58.2, "Stoch %K": 45.6, "Signal": "🟡 HOLD", "Signal_Text": "HOLD"},
        {"Stock": "INFY", "LTP (₹)": 1700.00, "Change %": -1.2, "RSI": 35.8, "Stoch %K": 18.4, "Signal": "🔴 SELL", "Signal_Text": "SELL"},
        {"Stock": "HDFCBANK", "LTP (₹)": 1680.00, "Change %": 0.8, "RSI": 52.3, "Stoch %K": 38.7, "Signal": "🟡 HOLD", "Signal_Text": "HOLD"},
        {"Stock": "ICICIBANK", "LTP (₹)": 1200.00, "Change %": 3.2, "RSI": 72.1, "Stoch %K": 85.6, "Signal": "🟢 BUY", "Signal_Text": "BUY"},
        {"Stock": "WIPRO", "LTP (₹)": 570.00, "Change %": -0.5, "RSI": 42.8, "Stoch %K": 28.9, "Signal": "🟡 HOLD", "Signal_Text": "HOLD"},
        {"Stock": "AXISBANK", "LTP (₹)": 1150.00, "Change %": 1.5, "RSI": 48.3, "Stoch %K": 32.1, "Signal": "🟡 HOLD", "Signal_Text": "HOLD"},
        {"Stock": "TATAMOTORS", "LTP (₹)": 1050.00, "Change %": 4.2, "RSI": 78.5, "Stoch %K": 92.4, "Signal": "🔴 SELL", "Signal_Text": "SELL"},
    ]

# ── MAIN FUNCTION ──────────────────────────────────────────────────
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
    
    if len(results) == 0:
        return get_fallback_data(), True, failed
    
    results.sort(key=lambda x: abs(x["Change %"]), reverse=True)
    return results[:10], False, failed

# ── STREAMLIT UI ──────────────────────────────────────────────────
st.set_page_config(
    page_title="NSE Stock Signals",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .title { font-size: 28px; font-weight: bold; text-align: center; color: #1F3864; }
    .buy-badge { background-color: #C6EFCE; color: #276221; padding: 2px 10px; border-radius: 10px; font-weight: bold; }
    .sell-badge { background-color: #FFC7CE; color: #9C0006; padding: 2px 10px; border-radius: 10px; font-weight: bold; }
    .hold-badge { background-color: #FFEB9C; color: #9C5700; padding: 2px 10px; border-radius: 10px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ── HEADER ─────────────────────────────────────────────────────────
st.markdown('<p class="title">📊 NSE Top Stock Signals</p>', unsafe_allow_html=True)
st.caption(f"🕐 {datetime.now().strftime('%d-%b-%Y %H:%M:%S')} IST")

# ── RULES ──────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    st.info(f"🟢 **BUY:** RSI > {BUY_RSI} & Stoch > {BUY_STOCH}")
with col2:
    st.warning("🟡 **HOLD:** No clear signal")
with col3:
    st.error(f"🔴 **SELL:** RSI < {SELL_RSI} & Stoch < {SELL_STOCH}")

# ── REFRESH ────────────────────────────────────────────────────────
if st.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# ── FETCH DATA ─────────────────────────────────────────────────────
with st.spinner("📈 Fetching live data..."):
    data, is_fallback, failed = get_top_stocks()

if data:
    df = pd.DataFrame(data)
    
    # ── COLOR FUNCTION (Fixed - using map instead of applymap) ──
    def highlight_signal(signal):
        if "BUY" in str(signal):
            return 'background-color: #C6EFCE; color: #276221; font-weight: bold'
        elif "SELL" in str(signal):
            return 'background-color: #FFC7CE; color: #9C0006; font-weight: bold'
        elif "HOLD" in str(signal):
            return 'background-color: #FFEB9C; color: #9C5700; font-weight: bold'
        return ''
    
    # Apply styling using map (new method)
    styled_df = df[['Stock', 'LTP (₹)', 'Change %', 'RSI', 'Stoch %K', 'Signal']].copy()
    
    # Apply color to Signal column
    styled_df['Signal'] = styled_df['Signal'].apply(lambda x: f'<span style="{highlight_signal(x)}">{x}</span>')
    
    # ── DISPLAY ─────────────────────────────────────────────────────
    st.markdown("### 📊 Top Stocks")
    
    # Display as HTML table with colors
    html_table = styled_df.to_html(escape=False, index=False)
    st.markdown(html_table, unsafe_allow_html=True)
    
    # Alternative: Use dataframe with column config
    col_config = {
        "Signal": st.column_config.TextColumn(
            "Signal",
            help="BUY/SELL/HOLD signal",
            width="medium"
        )
    }
    
    # Better display using st.dataframe with column config
    display_df = df[['Stock', 'LTP (₹)', 'Change %', 'RSI', 'Stoch %K', 'Signal']].copy()
    
    def color_signal(val):
        if "BUY" in str(val):
            return "🟢 BUY"
        elif "SELL" in str(val):
            return "🔴 SELL"
        return "🟡 HOLD"
    
    display_df['Signal'] = display_df['Signal'].apply(color_signal)
    
    # Use dataframe with conditional formatting
    st.dataframe(
        display_df,
        use_container_width=True,
        height=400,
        column_config={
            "Stock": "Stock",
            "LTP (₹)": st.column_config.NumberColumn("LTP (₹)", format="₹%.2f"),
            "Change %": st.column_config.NumberColumn("Change %", format="%.2f%%"),
            "RSI": st.column_config.NumberColumn("RSI", format="%.1f"),
            "Stoch %K": st.column_config.NumberColumn("Stoch %K", format="%.1f"),
            "Signal": st.column_config.TextColumn("Signal"),
        }
    )
    
    # ── SUMMARY ─────────────────────────────────────────────────────
    st.markdown("### 📈 Summary")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    buys = len(df[df['Signal_Text'] == 'BUY'])
    sells = len(df[df['Signal_Text'] == 'SELL'])
    holds = len(df[df['Signal_Text'] == 'HOLD'])
    
    with col1:
        st.metric("🟢 BUY", buys)
    with col2:
        st.metric("🔴 SELL", sells)
    with col3:
        st.metric("🟡 HOLD", holds)
    with col4:
        st.metric("📈 Avg RSI", f"{df['RSI'].mean():.1f}")
    with col5:
        st.metric("📊 Total", len(df))
    
    if is_fallback:
        st.warning("⚠️ Using demo data (live data temporarily unavailable)")
    
    # ── DETAILED VIEW ──────────────────────────────────────────────
    with st.expander("📋 Detailed View", expanded=False):
        for _, row in df.iterrows():
            sig = row['Signal']
            cls = "buy-badge" if "BUY" in sig else ("sell-badge" if "SELL" in sig else "hold-badge")
            
            cols = st.columns([2, 2, 2, 2, 2, 2])
            cols[0].write(f"**{row['Stock']}**")
            cols[1].write(f"₹{row['LTP (₹)']:.2f}")
            
            # Color for change %
            if row['Change %'] > 0:
                cols[2].write(f"🟢 {row['Change %']:.2f}%")
            elif row['Change %'] < 0:
                cols[2].write(f"🔴 {row['Change %']:.2f}%")
            else:
                cols[2].write(f"{row['Change %']:.2f}%")
            
            cols[3].write(f"{row['RSI']:.1f}")
            cols[4].write(f"{row['Stoch %K']:.1f}")
            cols[5].markdown(f'<span class="{cls}">{sig}</span>', unsafe_allow_html=True)
            st.divider()
    
    # ── DOWNLOAD ────────────────────────────────────────────────────
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"NSE_Signals_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True
    )

else:
    st.error("❌ No data available")
    st.info("💡 Try refreshing after 1 minute")

# ── FOOTER ─────────────────────────────────────────────────────────
st.markdown("---")
st.caption("⚠️ **Disclaimer:** Educational purposes only. Not financial advice.")
st.caption(f"📊 Watchlist: {len(NSE_STOCKS)} stocks")
