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
• NEW: EMA 50 & 200 crossover with 2-minute timeframe
• NEW: Daily first-time high detection
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
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

# New EMA parameters
EMA_FAST = 50
EMA_SLOW = 200

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
    min-height: 100vh;
}

.block-container {
    padding: 0.75rem 0.75rem 1.5rem !important;
    max-width: 1280px !important;
    margin: 0 auto !important;
}

/* ── Premium Header ── */
.premium-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    padding: 1rem 1.2rem;
    border-radius: 16px;
    margin-bottom: 1rem;
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
    gap: 0.75rem;
}

.header-left {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.header-icon {
    font-size: 2rem;
    background: rgba(56, 189, 248, 0.15);
    padding: 0.4rem;
    border-radius: 14px;
    border: 1px solid rgba(56, 189, 248, 0.2);
}

.header-title h1 {
    font-size: clamp(1rem, 2.5vw, 1.8rem);
    font-weight: 800;
    color: #ffffff;
    margin: 0;
    letter-spacing: -0.5px;
}

.header-title .subtitle {
    font-size: 0.65rem;
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
    gap: 1rem;
    flex-wrap: wrap;
}

.live-badge {
    background: #dc2626;
    color: white;
    padding: 3px 12px;
    border-radius: 999px;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    animation: pulse 2s infinite;
    display: flex;
    align-items: center;
    gap: 6px;
}

.live-dot {
    width: 7px;
    height: 7px;
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
    gap: 1rem;
}

.header-stat {
    text-align: center;
}

.header-stat .num {
    font-size: 1rem;
    font-weight: 700;
    color: #ffffff;
    display: block;
}

.header-stat .label {
    font-size: 0.55rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ── Rules Bar ── */
.rules-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-bottom: 1rem;
    justify-content: center;
}

.rule-pill {
    padding: 4px 14px;
    border-radius: 999px;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.3px;
    transition: all 0.3s ease;
    cursor: default;
    white-space: nowrap;
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

.rule-ema {
    background: linear-gradient(135deg, #fefce8, #fef9c3);
    color: #854d0e;
    border: 1px solid #fde047;
    box-shadow: 0 2px 8px rgba(217, 119, 6, 0.15);
}

.rule-high {
    background: linear-gradient(135deg, #fce7f3, #fbcfe8);
    color: #9d174d;
    border: 1px solid #f9a8d4;
    box-shadow: 0 2px 8px rgba(157, 23, 77, 0.15);
}

/* ── Refresh Button ── */
.refresh-wrapper {
    display: flex;
    justify-content: center;
    margin-bottom: 1rem;
}

/* ── Stats Row ── */
.stats-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(90px, 1fr));
    gap: 0.6rem;
    margin-bottom: 1rem;
}

.stat-card {
    background: white;
    padding: 0.6rem 0.8rem;
    border-radius: 12px;
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
    font-size: 1.2rem;
    font-weight: 800;
    display: block;
}

.stat-card .stat-label {
    font-size: 0.55rem;
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
.stat-ema .stat-value { color: #eab308; }
.stat-high .stat-value { color: #ec4899; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: white;
    border-radius: 12px;
    padding: 4px;
    border: 1px solid #e8ecf1;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    flex-wrap: nowrap;
    overflow-x: auto;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #6b7a8f;
    font-size: 0.75rem;
    font-weight: 500;
    padding: 6px 16px;
    transition: all 0.3s ease;
    white-space: nowrap;
    flex: 1;
    text-align: center;
    min-width: 80px;
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
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 0.7rem;
    margin-top: 0.5rem;
}

/* ── Premium Stock Card ── */
.stock-card {
    background: white;
    border-radius: 14px;
    padding: 0.9rem 1rem;
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

.stock-card.ema-buy-border::before {
    background: linear-gradient(90deg, #fde047, #eab308);
}

.stock-card.high-breakout-border::before {
    background: linear-gradient(90deg, #f9a8d4, #ec4899);
}

/* Card Header */
.card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;
}

.stock-name-wrap {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
}

.stock-rank {
    font-size: 0.65rem;
    font-weight: 700;
    color: #6b7a8f;
    background: #f1f5f9;
    padding: 2px 8px;
    border-radius: 999px;
}

.stock-name {
    font-size: 0.85rem;
    font-weight: 700;
    color: #0f172a;
}

.ltp-block {
    text-align: right;
}

.ltp-price {
    font-size: 0.85rem;
    font-weight: 700;
    color: #0f172a;
}

.ltp-change {
    font-size: 0.65rem;
    font-weight: 600;
    padding: 2px 8px;
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
    gap: 0.3rem;
    margin-bottom: 0.5rem;
}

.tf-badge {
    flex: 1;
    text-align: center;
    padding: 4px 3px;
    border-radius: 8px;
    font-size: 0.6rem;
    font-weight: 700;
    transition: all 0.2s ease;
    min-width: 0;
}

.tf-badge:hover {
    transform: scale(1.05);
}

.tf-label {
    font-size: 0.5rem;
    opacity: 0.65;
    margin-bottom: 1px;
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

.tf-badge.sig-ema-buy {
    background: #fefce8;
    color: #854d0e;
    border: 1px solid #fde047;
}

.tf-badge.sig-high-breakout {
    background: #fce7f3;
    color: #9d174d;
    border: 1px solid #f9a8d4;
}

/* Metrics */
.metrics-row {
    display: flex;
    gap: 0.3rem;
    margin-bottom: 0.4rem;
    flex-wrap: wrap;
}

.metric-chip {
    flex: 1;
    background: #f8fafc;
    border: 1px solid #e8ecf1;
    border-radius: 6px;
    padding: 3px 5px;
    text-align: center;
    min-width: 40px;
}

.metric-chip .m-label {
    font-size: 0.45rem;
    color: #6b7a8f;
    display: block;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

.metric-chip .m-val {
    font-size: 0.7rem;
    font-weight: 600;
    color: #0f172a;
}

.metric-chip .ema-50 {
    color: #eab308;
}
.metric-chip .ema-200 {
    color: #22c55e;
}
.metric-chip .high-tag {
    color: #ec4899;
}

/* Strength */
.strength-wrap {
    margin-top: 0.3rem;
}

.strength-label {
    display: flex;
    justify-content: space-between;
    font-size: 0.5rem;
    color: #6b7a8f;
    margin-bottom: 3px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

.strength-bar {
    height: 4px;
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
    font-size: 0.7rem;
    background: white;
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.summary-table th {
    background: #f8fafc;
    color: #4a5a6f;
    font-weight: 600;
    padding: 10px 12px;
    text-align: left;
    border-bottom: 2px solid #e8ecf1;
    font-size: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.summary-table td {
    padding: 8px 12px;
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
    padding: 2px 10px;
    border-radius: 6px;
    font-size: 0.6rem;
    font-weight: 700;
}

/* ── Footer ── */
.premium-footer {
    text-align: center;
    margin-top: 1.5rem;
    padding: 1rem;
    background: white;
    border-radius: 14px;
    border: 1px solid #e8ecf1;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.premium-footer .footer-text {
    font-size: 0.65rem;
    color: #6b7a8f;
    line-height: 1.6;
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
    margin: 0 6px;
    color: #d1d5db;
}

/* ── Tablet & Desktop Responsive ── */

/* Tablet (768px - 1024px) */
@media (min-width: 768px) and (max-width: 1024px) {
    .card-grid {
        grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
        gap: 0.6rem;
    }
    
    .stats-row {
        grid-template-columns: repeat(5, 1fr);
        gap: 0.5rem;
    }
    
    .stock-card {
        padding: 0.8rem;
    }
    
    .block-container {
        padding: 0.6rem 0.6rem 1.2rem !important;
    }
}

/* Desktop (1025px+) */
@media (min-width: 1025px) {
    .card-grid {
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 0.8rem;
    }
    
    .stats-row {
        grid-template-columns: repeat(5, 1fr);
        gap: 0.8rem;
    }
    
    .stock-card {
        padding: 1rem 1.2rem;
    }
    
    .block-container {
        padding: 1rem 1.5rem 2rem !important;
    }
}

/* ── Mobile (up to 767px) ── */
@media (max-width: 767px) {
    .block-container {
        padding: 0.4rem 0.4rem 1rem !important;
    }
    
    .premium-header {
        padding: 0.7rem 0.8rem;
        border-radius: 12px;
    }
    
    .header-content {
        flex-direction: column;
        align-items: stretch;
        gap: 0.5rem;
    }
    
    .header-left {
        gap: 0.5rem;
    }
    
    .header-icon {
        font-size: 1.5rem;
        padding: 0.3rem;
        border-radius: 10px;
    }
    
    .header-title h1 {
        font-size: 1rem;
    }
    
    .header-title .subtitle {
        font-size: 0.55rem;
        gap: 0.3rem;
    }
    
    .header-right {
        justify-content: space-between;
        gap: 0.5rem;
    }
    
    .header-stats {
        gap: 0.6rem;
    }
    
    .header-stat .num {
        font-size: 0.85rem;
    }
    
    .header-stat .label {
        font-size: 0.5rem;
    }
    
    .live-badge {
        font-size: 0.55rem;
        padding: 2px 10px;
    }
    
    .live-dot {
        width: 6px;
        height: 6px;
    }
    
    .rules-bar {
        gap: 0.3rem;
        margin-bottom: 0.7rem;
    }
    
    .rule-pill {
        font-size: 0.55rem;
        padding: 3px 10px;
        white-space: normal;
        word-break: break-word;
    }
    
    .stats-row {
        grid-template-columns: repeat(3, 1fr);
        gap: 0.4rem;
        margin-bottom: 0.7rem;
    }
    
    .stat-card {
        padding: 0.4rem 0.3rem;
        border-radius: 10px;
    }
    
    .stat-card .stat-value {
        font-size: 1rem;
    }
    
    .stat-card .stat-label {
        font-size: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 3px;
        padding: 3px;
        border-radius: 10px;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 0.65rem;
        padding: 4px 12px;
        min-width: 60px;
        flex: 1;
    }
    
    .card-grid {
        grid-template-columns: 1fr;
        gap: 0.5rem;
    }
    
    .stock-card {
        padding: 0.7rem;
        border-radius: 12px;
    }
    
    .stock-name {
        font-size: 0.8rem;
    }
    
    .ltp-price {
        font-size: 0.8rem;
    }
    
    .ltp-change {
        font-size: 0.6rem;
        padding: 2px 6px;
    }
    
    .tf-badge {
        font-size: 0.55rem;
        padding: 3px 2px;
    }
    
    .tf-label {
        font-size: 0.45rem;
    }
    
    .metric-chip .m-val {
        font-size: 0.65rem;
    }
    
    .metric-chip .m-label {
        font-size: 0.4rem;
    }
    
    .summary-table {
        font-size: 0.6rem;
        display: block;
        overflow-x: auto;
        white-space: nowrap;
        -webkit-overflow-scrolling: touch;
    }
    
    .summary-table th,
    .summary-table td {
        padding: 5px 8px;
    }
    
    .summary-table th {
        font-size: 0.55rem;
    }
    
    .td-sig {
        font-size: 0.55rem;
        padding: 2px 6px;
    }
    
    .premium-footer {
        padding: 0.7rem;
        margin-top: 1rem;
        border-radius: 12px;
    }
    
    .premium-footer .footer-text {
        font-size: 0.55rem;
    }
    
    .premium-footer .divider {
        margin: 0 3px;
    }
}

/* ── Very Small Mobile (up to 400px) ── */
@media (max-width: 400px) {
    .block-container {
        padding: 0.2rem 0.2rem 0.8rem !important;
    }
    
    .premium-header {
        padding: 0.5rem 0.6rem;
        border-radius: 10px;
    }
    
    .header-icon {
        font-size: 1.2rem;
        padding: 0.2rem;
        border-radius: 8px;
    }
    
    .header-title h1 {
        font-size: 0.85rem;
    }
    
    .header-title .subtitle {
        font-size: 0.5rem;
    }
    
    .header-stat .num {
        font-size: 0.75rem;
    }
    
    .rule-pill {
        font-size: 0.5rem;
        padding: 2px 8px;
    }
    
    .stats-row {
        grid-template-columns: repeat(3, 1fr);
        gap: 0.3rem;
    }
    
    .stat-card .stat-value {
        font-size: 0.85rem;
    }
    
    .stock-card {
        padding: 0.6rem;
        border-radius: 10px;
    }
    
    .stock-name {
        font-size: 0.7rem;
    }
    
    .ltp-price {
        font-size: 0.7rem;
    }
    
    .tf-badge {
        font-size: 0.5rem;
        padding: 2px 1px;
    }
    
    .summary-table {
        font-size: 0.5rem;
    }
    
    .summary-table th,
    .summary-table td {
        padding: 4px 5px;
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

/* Fix for Streamlit elements */
.stButton button {
    width: 100%;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 600;
}

.stAlert {
    border-radius: 12px;
}

/* Scrollbar styling */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

::-webkit-scrollbar-track {
    background: #f1f5f9;
    border-radius: 3px;
}

::-webkit-scrollbar-thumb {
    background: #c8d0db;
    border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
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
    """Fetch data with fallback for 4h interval"""
    try:
        # For 4h, try with longer period to get enough data
        if interval == "4h":
            period = "60d"  # Need more data for 4h
        else:
            period = f"{LOOKBACK_DAYS}d"
            
        df = yf.download(ticker, period=period,
                         interval=interval, progress=False, auto_adjust=True, timeout=15)
        
        if df is not None and len(df) > RSI_PERIOD + 5:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            return df[~df.index.duplicated(keep="last")].sort_index(), True
        
        # If 4h fails, try with 1h data and resample
        if interval == "4h":
            df_hourly, ok = fetch_live_data(ticker, "1h")
            if ok and df_hourly is not None and len(df_hourly) > 20:
                # Resample to 4h
                df_4h = df_hourly.resample('4H').agg({
                    'Open': 'first',
                    'High': 'max',
                    'Low': 'min',
                    'Close': 'last',
                    'Volume': 'sum'
                }).dropna()
                if len(df_4h) > RSI_PERIOD + 5:
                    return df_4h, True
        
        return None, False
    except Exception as e:
        return None, False

def get_2min_data(ticker):
    """Fetch 2-minute data for EMA analysis"""
    try:
        # Get 5 days of 2-min data to ensure enough data points
        df = yf.download(ticker, period="5d", interval="2m", 
                         progress=False, auto_adjust=True, timeout=15)
        
        if df is not None and len(df) > 50:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Remove duplicate indices
            df = df[~df.index.duplicated(keep="last")].sort_index()
            
            # Calculate EMAs
            df['EMA_50'] = df['Close'].ewm(span=EMA_FAST, adjust=False).mean()
            df['EMA_200'] = df['Close'].ewm(span=EMA_SLOW, adjust=False).mean()
            
            # Calculate daily high and check for first-time high
            df['Date'] = df.index.date
            df['Daily_High'] = df.groupby('Date')['High'].transform('max')
            
            # Detect first-time high of the day
            df['Is_First_High'] = False
            for date in df['Date'].unique():
                day_data = df[df['Date'] == date]
                if len(day_data) > 0:
                    # Find first occurrence of daily high
                    max_high = day_data['High'].max()
                    first_high_idx = day_data[day_data['High'] == max_high].index[0]
                    df.loc[first_high_idx, 'Is_First_High'] = True
            
            # Check current conditions
            if len(df) > 0:
                latest = df.iloc[-1]
                current_price = latest['Close']
                ema_50 = latest['EMA_50'] if not pd.isna(latest['EMA_50']) else None
                ema_200 = latest['EMA_200'] if not pd.isna(latest['EMA_200']) else None
                
                # Condition 1: Price > EMA 50
                condition1 = current_price > ema_50 if ema_50 is not None else False
                
                # Condition 2: Price > EMA 200 and crossing above
                condition2 = False
                if ema_200 is not None and len(df) > 1:
                    prev = df.iloc[-2]
                    prev_ema_200 = prev['EMA_200'] if not pd.isna(prev['EMA_200']) else None
                    if prev_ema_200 is not None:
                        # Check if current price crossed above EMA 200
                        condition2 = (current_price > ema_200 and prev['Close'] <= prev_ema_200)
                
                # Check if it's first high of the day (only show when first time)
                is_first_high = latest['Is_First_High']
                
                return {
                    'Current_Price': current_price,
                    'EMA_50': ema_50,
                    'EMA_200': ema_200,
                    'Condition1': condition1,  # Price > EMA 50
                    'Condition2': condition2,  # Crossed above EMA 200
                    'Is_First_High': is_first_high,
                    'Daily_High': latest['Daily_High'] if 'Daily_High' in latest else None,
                    'DataPoints': len(df),
                    'Timestamp': df.index[-1]
                }
        
        return None
    except Exception as e:
        return None

def analyse_stock_with_ema(name, ticker, interval):
    """Analyse stock with additional EMA and 2-minute data"""
    # Get main timeframe data
    df, ok = fetch_live_data(ticker, interval)
    if not ok or df is None or len(df) < RSI_PERIOD + 5:
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

    # Get 2-minute data for EMA and high analysis
    ema_data = get_2min_data(ticker)
    
    ema_signal = "WAIT"
    high_signal = "WAIT"
    ema_text = ""
    high_text = ""
    ema_condition = False
    high_condition = False
    
    if ema_data:
        # Check EMA conditions
        if ema_data['Condition1'] and ema_data['Condition2']:
            ema_signal = "EMA-BUY"
            ema_text = "✓ Price > EMA50 & Crossed EMA200"
            ema_condition = True
        elif ema_data['Condition1']:
            ema_signal = "EMA-ONLY"
            ema_text = "✓ Price > EMA50"
        elif ema_data['Condition2']:
            ema_signal = "EMA-CROSS"
            ema_text = "✓ Crossed EMA200"
        
        # Check first-time high condition
        if ema_data['Is_First_High']:
            high_signal = "HIGH-BREAKOUT"
            high_text = f"🔥 First High @ ₹{ema_data['Daily_High']:.2f}"
            high_condition = True

    return {
        "Stock": name, "Ticker": ticker, "Timeframe": interval,
        "LTP": ltp, "Change": chg,
        "RSI": rsi, "SK": sk, "SD": sd,
        "Signal": sig, "Strength": str_,
        "MACD_H": round(mh, 4),
        "Support": round(float(lat["SUPP"]), 2) if pd.notna(lat["SUPP"]) else None,
        "Resistance": round(float(lat["RES"]), 2) if pd.notna(lat["RES"]) else None,
        "As_of": ha.index[-1].strftime("%d-%b %H:%M"),
        "DataPoints": len(ha),
        # EMA data
        "EMA_Signal": ema_signal,
        "EMA_Text": ema_text,
        "EMA_50_Value": round(ema_data['EMA_50'], 2) if ema_data and ema_data['EMA_50'] else None,
        "EMA_200_Value": round(ema_data['EMA_200'], 2) if ema_data and ema_data['EMA_200'] else None,
        "EMA_Condition": ema_condition,
        # High data
        "High_Signal": high_signal,
        "High_Text": high_text,
        "High_Condition": high_condition,
        "Daily_High": round(ema_data['Daily_High'], 2) if ema_data and ema_data['Daily_High'] else None,
    }

@st.cache_data(ttl=300)
def get_all_data():
    results_by_tf = {}
    ema_results = {}
    
    progress_text = st.empty()
    progress_bar = st.progress(0)
    
    total = len(NIFTY_50) * len(TIMEFRAMES)
    current = 0
    
    # First, get 2-minute EMA data for all stocks
    ema_progress = st.empty()
    ema_progress.text("📊 Analyzing 2-minute EMA data...")
    
    for name, ticker in NIFTY_50.items():
        ema_data = get_2min_data(ticker)
        if ema_data:
            ema_results[name] = ema_data
    
    ema_progress.text("✅ EMA analysis complete!")
    
    # Then get timeframe data
    for tf in TIMEFRAMES:
        tf_res = []
        for name, ticker in NIFTY_50.items():
            current += 1
            progress_text.text(f"📈 Analysing {name} ({tf})...")
            progress_bar.progress(current / total)
            
            try:
                r = analyse_stock_with_ema(name, ticker, tf)
                if r: 
                    # Add EMA data from pre-computed results
                    if name in ema_results:
                        ema = ema_results[name]
                        r["EMA_50_Value"] = round(ema['EMA_50'], 2) if ema['EMA_50'] else None
                        r["EMA_200_Value"] = round(ema['EMA_200'], 2) if ema['EMA_200'] else None
                        r["EMA_Condition"] = ema['Condition1'] and ema['Condition2']
                        r["High_Condition"] = ema['Is_First_High']
                        r["Daily_High"] = round(ema['Daily_High'], 2) if ema['Daily_High'] else None
                    tf_res.append(r)
                time.sleep(0.1)
            except Exception as e:
                continue
        results_by_tf[tf] = tf_res
    
    progress_text.text("✅ Analysis complete!")
    progress_bar.empty()
    
    # Top 10 based on 1H Change and EMA/High conditions
    top_10 = list(NIFTY_50.keys())[:10]
    if results_by_tf.get("1h"):
        valid = [r for r in results_by_tf["1h"] if r is not None]
        if valid:
            # Prioritize stocks with EMA and High conditions
            scored = []
            for r in valid:
                score = r["Change"]  # Base score from change
                if r.get("EMA_Condition", False):
                    score += 5  # Bonus for EMA condition
                if r.get("High_Condition", False):
                    score += 10  # Bonus for first-time high
                scored.append((r, score))
            scored.sort(key=lambda x: x[1], reverse=True)
            top_10 = [r[0]["Stock"] for r in scored[:10]]
    
    return results_by_tf, top_10

# ── HTML BUILDERS ──────────────────────────────────────────────────
SIG_CLASS = {"BUY": "sig-buy", "SELL": "sig-sell", "HOLD": "sig-hold", 
             "WAIT": "sig-wait", "EMA-BUY": "sig-ema-buy", 
             "EMA-ONLY": "sig-ema-buy", "EMA-CROSS": "sig-ema-buy",
             "HIGH-BREAKOUT": "sig-high-breakout"}
SIG_ICON = {"BUY": "▲ BUY", "SELL": "▼ SELL", "HOLD": "● HOLD", "WAIT": "… WAIT",
            "EMA-BUY": "📈 EMA BUY", "EMA-ONLY": "📊 EMA 50+", "EMA-CROSS": "🔄 EMA CROSS",
            "HIGH-BREAKOUT": "🚀 HIGH BREAKOUT"}

def strength_bar_html(val):
    cls = "s-high" if val >= 65 else ("s-mid" if val >= 35 else "s-low")
    return f"""
    <div class="strength-wrap">
        <div class="strength-label"><span>Signal Strength</span><span>{val}%</span></div>
        <div class="strength-bar"><div class="strength-fill {cls}" style="width:{val}%"></div></div>
    </div>"""

def stock_card_html(name, r1h, r4h, r1d, rank, ema_data=None):
    if r1h:
        ltp = r1h["LTP"]
        chg = r1h["Change"]
        rsi_1h = r1h["RSI"]
        sk_1h = r1h["SK"]
        sig_1h = r1h["Signal"]
        ema_condition = r1h.get("EMA_Condition", False)
        high_condition = r1h.get("High_Condition", False)
        ema_50 = r1h.get("EMA_50_Value")
        ema_200 = r1h.get("EMA_200_Value")
        daily_high = r1h.get("Daily_High")
    elif r1d:
        ltp = r1d["LTP"]
        chg = r1d["Change"]
        rsi_1h = "–"
        sk_1h = "–"
        sig_1h = "WAIT"
        ema_condition = False
        high_condition = False
        ema_50 = None
        ema_200 = None
        daily_high = None
    else:
        ltp = 0
        chg = 0
        rsi_1h = "–"
        sk_1h = "–"
        sig_1h = "WAIT"
        ema_condition = False
        high_condition = False
        ema_50 = None
        ema_200 = None
        daily_high = None
    
    # Get 4h data with fallback
    if r4h:
        rsi_4h = r4h["RSI"]
        sk_4h = r4h["SK"]
        sig_4h = r4h["Signal"]
    else:
        rsi_4h = "–"
        sk_4h = "–"
        sig_4h = "WAIT"
    
    if r1d:
        rsi_1d = r1d["RSI"]
        sk_1d = r1d["SK"]
        sig_1d = r1d["Signal"]
    else:
        rsi_1d = "–"
        sk_1d = "–"
        sig_1d = "WAIT"
    
    strengths = []
    if r1h and "Strength" in r1h:
        strengths.append(r1h["Strength"])
    if r4h and "Strength" in r4h:
        strengths.append(r4h["Strength"])
    if r1d and "Strength" in r1d:
        strengths.append(r1d["Strength"])
    
    avg_str = int(np.mean(strengths)) if strengths else 0
    
    # Border class based on conditions
    border_cls = ""
    if high_condition:
        border_cls = "high-breakout-border"
    elif ema_condition:
        border_cls = "ema-buy-border"
    elif sig_1h == "BUY":
        border_cls = "buy-border"
    elif sig_1h == "SELL":
        border_cls = "sell-border"
    elif sig_1h == "HOLD":
        border_cls = "hold-border"
    
    chg_cls = "pos" if chg >= 0 else "neg"
    chg_sym = "▲" if chg >= 0 else "▼"
    
    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"

    def tf_badge(sig, label, extra_cls=""):
        sc = SIG_CLASS.get(sig, "sig-wait")
        ic = SIG_ICON.get(sig, "WAIT")
        return f'<div class="tf-badge {sc} {extra_cls}"><span class="tf-label">{label}</span>{ic}</div>'

    sig_row = f"""
    <div class="sig-row">
        {tf_badge(sig_1h, "1H")}
        {tf_badge(sig_4h, "4H")}
        {tf_badge(sig_1d, "1D")}
    </div>"""

    # EMA and High indicators
    ema_high_row = ""
    if ema_50 is not None or ema_200 is not None or daily_high is not None:
        ema_high_row = '<div class="metrics-row">'
        if ema_50 is not None:
            ema_high_row += f'<div class="metric-chip"><span class="m-label">EMA 50</span><span class="m-val ema-50">₹{ema_50:.2f}</span></div>'
        if ema_200 is not None:
            ema_high_row += f'<div class="metric-chip"><span class="m-label">EMA 200</span><span class="m-val ema-200">₹{ema_200:.2f}</span></div>'
        if daily_high is not None:
            ema_high_row += f'<div class="metric-chip"><span class="m-label">📊 High</span><span class="m-val high-tag">₹{daily_high:.2f}</span></div>'
        ema_high_row += '</div>'
        
        # Add EMA and High status badges
        if ema_condition:
            ema_high_row += f'<div class="sig-row"><div class="tf-badge sig-ema-buy" style="flex:1;"><span class="tf-label">📈</span>✓ EMA Crossover</div></div>'
        if high_condition:
            ema_high_row += f'<div class="sig-row"><div class="tf-badge sig-high-breakout" style="flex:1;"><span class="tf-label">🚀</span>🔥 FIRST HIGH TODAY!</div></div>'

    def metric_chip(label, val):
        return f'<div class="metric-chip"><span class="m-label">{label}</span><span class="m-val">{val}</span></div>'

    metrics = f"""
    <div class="metrics-row">
        {metric_chip("RSI 1H", rsi_1h)}
        {metric_chip("SK 1H", sk_1h)}
        {metric_chip("RSI 4H", rsi_4h)}
        {metric_chip("SK 4H", sk_4h)}
    </div>"""

    return f"""
    <div class="stock-card {border_cls}">
        <div class="card-header">
            <div class="stock-name-wrap">
                <span class="stock-rank">{medal}</span>
                <span class="stock-name">{name}</span>
                {f'<span style="font-size:0.6rem;background:#fce7f3;color:#9d174d;padding:2px 6px;border-radius:4px;font-weight:700;">🔥 HIGH</span>' if high_condition else ''}
                {f'<span style="font-size:0.6rem;background:#fefce8;color:#854d0e;padding:2px 6px;border-radius:4px;font-weight:700;">📈 EMA</span>' if ema_condition else ''}
            </div>
            <div class="ltp-block">
                <div class="ltp-price">₹{ltp:,.2f}</div>
                <div class="ltp-change {chg_cls}">{chg_sym} {abs(chg):.2f}%</div>
            </div>
        </div>
        {sig_row}
        {ema_high_row}
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
            ema_condition = r1h.get("EMA_Condition", False)
            high_condition = r1h.get("High_Condition", False)
        else:
            ltp = "–"
            chg = 0
            as_of = "–"
            ema_condition = False
            high_condition = False
            
        chg_cls = "pos" if chg >= 0 else "neg"
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}"

        def td_sig(sig):
            sc = SIG_CLASS.get(sig, "sig-wait")
            return f'<span class="td-sig {sc}">{SIG_ICON.get(sig, "WAIT")}</span>'

        # Add EMA and High indicators in table
        extra_indicators = ""
        if high_condition:
            extra_indicators = '🔥'
        elif ema_condition:
            extra_indicators = '📈'

        rows += f"""<tr>
            <td style="color:#6b7a8f;font-size:0.65rem;font-weight:700;">{medal}</td>
            <td><strong style="color:#0f172a;font-size:0.75rem;">{stock} {extra_indicators}</strong></td>
            <td style="font-weight:600;font-size:0.75rem;">₹{ltp:,.0f}</td>
            <td class="{chg_cls}" style="font-weight:600;font-size:0.7rem;">{"▲" if chg>=0 else "▼"} {abs(chg):.1f}%</td>
            <td>{td_sig(r1h["Signal"] if r1h else "WAIT")}</td>
            <td>{td_sig(r4h["Signal"] if r4h else "WAIT")}</td>
            <td>{td_sig(r1d["Signal"] if r1d else "WAIT")}</td>
            <td style="color:#6b7a8f;font-size:0.55rem;">{as_of}</td>
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
                    <span>•</span>
                    <span>📊 2-Min EMA Analysis</span>
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
    <span class="rule-pill rule-ema">📈 EMA: Price &gt; EMA50 &amp; Crosses EMA200</span>
    <span class="rule-pill rule-high">🚀 HIGH: First Time High Today</span>
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
    ema_count = 0
    high_count = 0
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
            
            if r.get("EMA_Condition", False):
                ema_count += 1
            if r.get("High_Condition", False):
                high_count += 1
    
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
        <div class="stat-card stat-ema">
            <span class="stat-value">📈 {ema_count}</span>
            <span class="stat-label">EMA Breakout</span>
        </div>
        <div class="stat-card stat-high">
            <span class="stat-value">🚀 {high_count}</span>
            <span class="stat-label">First High</span>
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

# ── COMPONENT CSS ──
COMPONENT_CSS = """
<style>
* { 
    box-sizing: border-box; 
    margin: 0; 
    padding: 0; 
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; 
}
body { 
    background: transparent; 
    overflow-y: auto !important;
    height: auto !important;
    min-height: 100vh !important;
}

.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 0.7rem;
    padding: 4px 2px 20px 2px;
    overflow-y: visible !important;
}

.stock-card {
    background: white;
    border-radius: 14px;
    padding: 0.9rem 1rem;
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

.stock-card.ema-buy-border::before {
    background: linear-gradient(90deg, #fde047, #eab308);
}

.stock-card.high-breakout-border::before {
    background: linear-gradient(90deg, #f9a8d4, #ec4899);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;
}

.stock-name-wrap {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
}

.stock-rank {
    font-size: 0.65rem;
    font-weight: 700;
    color: #6b7a8f;
    background: #f1f5f9;
    padding: 2px 8px;
    border-radius: 999px;
}

.stock-name {
    font-size: 0.85rem;
    font-weight: 700;
    color: #0f172a;
}

.ltp-block { 
    text-align: right; 
}

.ltp-price { 
    font-size: 0.85rem; 
    font-weight: 700; 
    color: #0f172a; 
}

.ltp-change { 
    font-size: 0.65rem; 
    font-weight: 600; 
    padding: 2px 8px; 
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

.sig-row { 
    display: flex; 
    gap: 0.3rem; 
    margin-bottom: 0.5rem; 
}

.tf-badge {
    flex: 1;
    text-align: center;
    padding: 4px 3px;
    border-radius: 8px;
    font-size: 0.6rem;
    font-weight: 700;
    transition: all 0.2s ease;
    min-width: 0;
}

.tf-badge:hover { 
    transform: scale(1.05); 
}

.tf-label { 
    font-size: 0.5rem; 
    opacity: 0.65; 
    margin-bottom: 1px; 
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

.tf-badge.sig-ema-buy { 
    background: #fefce8; 
    color: #854d0e; 
    border: 1px solid #fde047; 
}

.tf-badge.sig-high-breakout { 
    background: #fce7f3; 
    color: #9d174d; 
    border: 1px solid #f9a8d4; 
}

.metrics-row { 
    display: flex; 
    gap: 0.3rem; 
    margin-bottom: 0.4rem; 
    flex-wrap: wrap; 
}

.metric-chip { 
    flex: 1; 
    background: #f8fafc; 
    border: 1px solid #e8ecf1; 
    border-radius: 6px; 
    padding: 3px 5px; 
    text-align: center; 
    min-width: 40px; 
}

.metric-chip .m-label { 
    font-size: 0.45rem; 
    color: #6b7a8f; 
    display: block; 
    text-transform: uppercase; 
    letter-spacing: 0.3px; 
}

.metric-chip .m-val { 
    font-size: 0.7rem; 
    font-weight: 600; 
    color: #0f172a; 
}

.metric-chip .ema-50 {
    color: #eab308;
}
.metric-chip .ema-200 {
    color: #22c55e;
}
.metric-chip .high-tag {
    color: #ec4899;
}

.strength-wrap { 
    margin-top: 0.3rem; 
}

.strength-label { 
    display: flex; 
    justify-content: space-between; 
    font-size: 0.5rem; 
    color: #6b7a8f; 
    margin-bottom: 3px; 
    text-transform: uppercase; 
    letter-spacing: 0.3px; 
}

.strength-bar { 
    height: 4px; 
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

.summary-table { 
    width: 100%; 
    border-collapse: collapse; 
    font-size: 0.7rem; 
    background: white; 
    border-radius: 14px; 
    overflow: hidden; 
    box-shadow: 0 2px 8px rgba(0,0,0,0.04); 
}

.summary-table th { 
    background: #f8fafc; 
    color: #4a5a6f; 
    font-weight: 600; 
    padding: 10px 12px; 
    text-align: left; 
    border-bottom: 2px solid #e8ecf1; 
    font-size: 0.6rem; 
    text-transform: uppercase; 
    letter-spacing: 0.5px; 
}

.summary-table td { 
    padding: 8px 12px; 
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
    padding: 2px 10px; 
    border-radius: 6px; 
    font-size: 0.6rem; 
    font-weight: 700; 
}

/* ── Mobile (up to 767px) ── */
@media (max-width: 767px) {
    .card-grid { 
        grid-template-columns: 1fr; 
        gap: 0.5rem; 
        padding: 4px 2px 40px 2px;
    }
    .stock-card { 
        padding: 0.7rem; 
        border-radius: 12px; 
    }
    .stock-name { 
        font-size: 0.8rem; 
    }
    .ltp-price { 
        font-size: 0.8rem; 
    }
    .ltp-change { 
        font-size: 0.6rem; 
        padding: 2px 6px; 
    }
    .tf-badge { 
        font-size: 0.55rem; 
        padding: 3px 2px; 
    }
    .tf-label { 
        font-size: 0.45rem; 
    }
    .metric-chip .m-val { 
        font-size: 0.65rem; 
    }
    .metric-chip .m-label { 
        font-size: 0.4rem; 
    }
    .summary-table { 
        font-size: 0.6rem; 
        display: block; 
        overflow-x: auto; 
        white-space: nowrap; 
        -webkit-overflow-scrolling: touch; 
    }
    .summary-table th, 
    .summary-table td { 
        padding: 5px 8px; 
    }
    .summary-table th { 
        font-size: 0.55rem; 
    }
    .td-sig { 
        font-size: 0.55rem; 
        padding: 2px 6px; 
    }
}

/* ── Very Small Mobile (up to 400px) ── */
@media (max-width: 400px) {
    .stock-card { 
        padding: 0.6rem; 
        border-radius: 10px; 
    }
    .stock-name { 
        font-size: 0.7rem; 
    }
    .ltp-price { 
        font-size: 0.7rem; 
    }
    .tf-badge { 
        font-size: 0.5rem; 
        padding: 2px 1px; 
    }
    .summary-table { 
        font-size: 0.5rem; 
    }
    .summary-table th, 
    .summary-table td { 
        padding: 4px 5px; 
    }
}

/* ── Tablet (768px - 1024px) ── */
@media (min-width: 768px) and (max-width: 1024px) {
    .card-grid { 
        grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); 
        gap: 0.6rem; 
    }
    .stock-card { 
        padding: 0.8rem; 
    }
}

/* ── Desktop (1025px+) ── */
@media (min-width: 1025px) {
    .card-grid { 
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); 
        gap: 0.8rem; 
        padding: 4px 2px 20px 2px;
    }
    .stock-card { 
        padding: 1rem 1.2rem; 
    }
}
</style>
"""

if top_10_names and len(top_10_names) > 0:
    tab1, tab2, tab3 = st.tabs(["🃏 Signal Cards", "📋 Summary Table", "📊 EMA & High Analysis"])

    with tab1:
        cards_html = f'{COMPONENT_CSS}<div class="card-grid">'
        for idx, stock in enumerate(top_10_names, 1):
            r1h = all_res.get((stock, "1h"))
            r4h = all_res.get((stock, "4h"))
            r1d = all_res.get((stock, "1d"))
            cards_html += stock_card_html(stock, r1h, r4h, r1d, idx)
        cards_html += '</div>'
        
        components.html(
            cards_html, 
            height=800,
            scrolling=True
        )

    with tab2:
        tbl_html = f'{COMPONENT_CSS}{summary_table_html(top_10_names, all_res)}'
        components.html(
            tbl_html, 
            height=600,
            scrolling=True
        )

    with tab3:
        # Create a detailed table showing EMA and High conditions
        st.markdown("### 📊 EMA & First High Analysis (2-Minute Timeframe)")
        
        ema_high_data = []
        for stock in top_10_names:
            r = all_res.get((stock, "1h"))
            if r:
                ema_high_data.append({
                    "Stock": stock,
                    "EMA 50": r.get("EMA_50_Value", "N/A"),
                    "EMA 200": r.get("EMA_200_Value", "N/A"),
                    "Price > EMA 50": "✓" if r.get("EMA_Condition", False) and r.get("EMA_50_Value") and r.get("LTP") > r.get("EMA_50_Value") else "✗",
                    "Crossed EMA 200": "✓" if r.get("EMA_Condition", False) else "✗",
                    "Daily High": r.get("Daily_High", "N/A"),
                    "First High Today": "🔥" if r.get("High_Condition", False) else "✗",
                    "Condition Met": "✅" if (r.get("EMA_Condition", False) or r.get("High_Condition", False)) else "❌"
                })
        
        if ema_high_data:
            df_ema_high = pd.DataFrame(ema_high_data)
            st.dataframe(
                df_ema_high,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Stock": st.column_config.TextColumn("Stock", width="small"),
                    "EMA 50": st.column_config.NumberColumn("EMA 50", format="₹%.2f", width="small"),
                    "EMA 200": st.column_config.NumberColumn("EMA 200", format="₹%.2f", width="small"),
                    "Price > EMA 50": st.column_config.TextColumn("Price > EMA 50", width="small"),
                    "Crossed EMA 200": st.column_config.TextColumn("Crossed EMA 200", width="small"),
                    "Daily High": st.column_config.NumberColumn("Daily High", format="₹%.2f", width="small"),
                    "First High Today": st.column_config.TextColumn("First High Today", width="small"),
                    "Condition Met": st.column_config.TextColumn("Condition Met", width="small")
                }
            )
            
            # Summary of conditions
            total_ema = sum(1 for d in ema_high_data if "✓" in d["Price > EMA 50"])
            total_high = sum(1 for d in ema_high_data if d["First High Today"] == "🔥")
            total_conditions = sum(1 for d in ema_high_data if d["Condition Met"] == "✅")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📈 EMA Breakout", total_ema, f"out of {len(ema_high_data)}")
            with col2:
                st.metric("🚀 First High Today", total_high, f"out of {len(ema_high_data)}")
            with col3:
                st.metric("✅ Total Conditions Met", total_conditions, f"out of {len(ema_high_data)}")
            
            st.info("📌 **How to read:**\n"
                   "- **Price > EMA 50**: Current price is above 50-period Exponential Moving Average\n"
                   "- **Crossed EMA 200**: Price has crossed above the 200-period EMA\n"
                   "- **First High Today**: Stock is trading at its highest point of the day (first time)\n"
                   "- **Condition Met**: Either EMA condition is met OR stock is at first high")
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
        <span class="divider">|</span>
        📈 2-Min EMA & First High Analysis
    </span>
</div>
""", unsafe_allow_html=True)
