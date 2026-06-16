import math
import shutil
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh


import os

APP_DIR = Path(__file__).resolve().parent
SOURCE_DATA_FILE = Path(
    r"\\Hdfc1\d\HDFC\ALLOCATION FILE\TW FILES\JUNE 26\TW ALLOCATION JUNE 26.xlsx"
)
LOCAL_DATA_COPY = APP_DIR / "RCC_DATA.xlsx"
ONEDRIVE_DATA_COPY = Path(os.path.expanduser("~")) / "OneDrive" / "RCC" / "RCC_DATA.xlsx"
DEFAULT_DATA_FILE = LOCAL_DATA_COPY.name
DEFAULT_SHEET_NAME = "MAIN"
# Set RCC_CLOUD=1 in environment to skip network sync (for Render/cloud deployments)
# Set ONEDRIVE_SHARE_URL to the OneDrive share link for cloud data download
CLOUD_MODE = os.environ.get("RCC_CLOUD", "0") == "1"
ONEDRIVE_SHARE_URL = os.environ.get("ONEDRIVE_SHARE_URL", "")

CREDENTIALS = {
    "ADMIN": {"password": "Admin@123", "role": "admin"},
    "AKSHAY KARALE": {"password": "akshay@123", "role": "executive"},
    "AMIT GADE": {"password": "amit@123", "role": "executive"},
    "AMOL DHUMAL": {"password": "amol@123", "role": "executive"},
    "ANWAR SHAIKH": {"password": "anwar@123", "role": "executive"},
    "HARIDAS DIVATE": {"password": "haridas@123", "role": "executive"},
    "HEMANT WALUNJ": {"password": "hemant@123", "role": "executive"},
    "KIRAN KHAIRNAR": {"password": "kiran@123", "role": "executive"},
    "NITIN KADAM": {"password": "nitin@123", "role": "executive"},
    "PARMESHWAR KOTULE": {"password": "parmeshwar@123", "role": "executive"},
    "SACHIN INGALE": {"password": "sachini@123", "role": "executive"},
    "SACHIN KHAPRE": {"password": "sachink@123", "role": "executive"},
    "SAGAR DONGRE": {"password": "sagar@123", "role": "executive"},
    "SANDEEP KHAIRNAR": {"password": "sandeep@123", "role": "executive"},
    "SUNNY SHINDE": {"password": "sunny@123", "role": "executive"},
    "SWAPNIL JADHAV": {"password": "swapnil@123", "role": "executive"},
    "TANAJI SURVASE": {"password": "tanaji@123", "role": "executive"},
    "UDAY SOHANE": {"password": "uday@123", "role": "executive"},
    "VIKRAM GAIKWAD": {"password": "vikram@123", "role": "executive"},
}

REQUIRED_COLUMNS = [
    "LOAN NO", "CUSTOMER NAME", "TEAM", "BUCKET", "POS STATUS", "POS",
    "EMI", "TOTAL EMI DUE", "DPIC CHARGES", "STAB AMOUNTWITH DPIC",
    "RB AMOUNTWITH DPIC", "Paid Amount", "RECEIPT CUT", "TRAILS PENDING",
    "DRA CASE%", "AGENCY CASE%", "AREA", "MOBILE", "DPD",
]

st.set_page_config(
    page_title="Resolution Command Center",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state='expanded',
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap');

/* ── PREMIUM DARK THEME (default) ── */
:root {
    --bg:       #0b1120;
    --surface:  #131c2e;
    --surface2: #1a2540;
    --border:   #2d3b52;
    --ink:      #e8edf5;
    --muted:    #94a3b8;
    --accent:   #3b82f6;
    --green:    #10b981;
    --amber:    #f59e0b;
    --red:      #ef4444;
    --purple:   #8b5cf6;
    --font-main: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    --font-mono: 'JetBrains Mono', 'Roboto Mono', monospace;
    --shadow-sm: 0 1px 2px rgba(0,0,0,.3);
    --shadow-md: 0 4px 12px rgba(0,0,0,.3);
    --shadow-lg: 0 12px 40px rgba(0,0,0,.4);
    --transition: all .2s cubic-bezier(.4,0,.2,1);
    --card-bg: rgba(26,37,64,.9);
    --card-border: rgba(45,59,82,.5);
    --inner-bg: rgba(11,17,32,.6);
    --inner-bg2: #0d1e38;
    --track-bg: #0a1425;
    --glass: rgba(26,37,64,.8);
    --glass-border: rgba(59,130,246,.15);
}
""", unsafe_allow_html=True)

# ── Theme state ──
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

THEME = st.session_state.theme

# Theme-aware color palette for inline styles
# ─────────────────────────────────────────────────────────────────────
# IMPORTANT: Jab bhi naya inline HTML likho (st.markdown with style="..."),
# HAMESHA T[...] dictionary use karo — hardcoded colors mat likho!
#
# ✅ SAHI:  f'<div style="color:{T["ink"]};background:{T["surface"]}">'
# ❌ GALAT: f'<div style="color:#f1f5f9;background:#1a2540">'
#
# Available keys:
#   T["bg"]         → page background
#   T["surface"]    → card/container background
#   T["surface2"]   → alternate/inner background
#   T["border"]     → borders
#   T["ink"]        → primary text (headings, values)
#   T["muted"]      → secondary/label text
#   T["accent"]     → blue accent
#   T["green"]      → green (theme-adjusted)
#   T["amber"]      → amber/warning
#   T["red"]        → red/error
#   T["purple"]     → purple
#   T["card_bg"]    → card wrapper background
#   T["card_border"]→ card border
#   T["inner_bg"]   → inner section bg (inside cards)
#   T["inner_bg2"]  → alternate inner bg
#   T["track_bg"]   → progress bar track
#   T["glass"]      → glassmorphism bg
#   T["glass_border"]→ glass border
#   T["green_val"]  → green value text (numbers)
#   T["red_val"]    → red value text
#   T["blue_val"]   → blue value text
#   T["purple_val"] → purple value text
#   T["amber_val"]  → amber value text
#   T["card_shadow"]→ card box-shadow
#   T["flow_color"] → flow status color
#   T["stable_color"]→ stable status color
#   T["rb_color"]   → RB status color
# ─────────────────────────────────────────────────────────────────────
if THEME == "light":
    T = {
        "bg": "#f8fafc", "surface": "#ffffff", "surface2": "#f1f5f9",
        "border": "#e2e8f0", "ink": "#0f172a", "muted": "#475569",
        "accent": "#2563eb", "green": "#059669", "amber": "#d97706",
        "red": "#dc2626", "purple": "#7c3aed",
        "card_bg": "#ffffff", "card_border": "#e2e8f0",
        "inner_bg": "#f8fafc", "inner_bg2": "#f1f5f9",
        "track_bg": "#e2e8f0", "glass": "rgba(255,255,255,.9)",
        "glass_border": "rgba(37,99,235,.1)",
        "text_primary": "#0f172a", "text_secondary": "#475569",
        "green_val": "#059669", "red_val": "#dc2626", "blue_val": "#2563eb",
        "purple_val": "#7c3aed", "amber_val": "#d97706",
        "card_shadow": "0 4px 12px rgba(0,0,0,.05), 0 2px 4px rgba(0,0,0,.04)",
        "flow_color": "#0369a1", "stable_color": "#059669", "rb_color": "#be185d",
    }
else:
    T = {
        "bg": "#0b1120", "surface": "#131c2e", "surface2": "#1a2540",
        "border": "#2d3b52", "ink": "#e8edf5", "muted": "#7a8ba8",
        "accent": "#3b82f6", "green": "#10b981", "amber": "#f59e0b",
        "red": "#ef4444", "purple": "#8b5cf6",
        "card_bg": "rgba(26,37,64,.9)", "card_border": "rgba(45,59,82,.5)",
        "inner_bg": "rgba(11,17,32,.6)", "inner_bg2": "#0d1e38",
        "track_bg": "#0a1425", "glass": "rgba(26,37,64,.8)",
        "glass_border": "rgba(59,130,246,.15)",
        "text_primary": "#f1f5f9", "text_secondary": "#7a8ba8",
        "green_val": "#4ade80", "red_val": "#ef4444", "blue_val": "#7dd3fc",
        "purple_val": "#c4b5fd", "amber_val": "#fbbf24",
        "card_shadow": "0 8px 32px rgba(0,0,0,.2)",
        "flow_color": "#7dd3fc", "stable_color": "#4ade80", "rb_color": "#f472b6",
    }

# Inject theme-specific CSS overrides
if THEME == "light":
    st.markdown("""<style>
    :root {
        --bg:       #f8fafc;
        --surface:  #ffffff;
        --surface2: #f1f5f9;
        --border:   #e2e8f0;
        --ink:      #0f172a;
        --muted:    #475569;
        --accent:   #2563eb;
        --green:    #059669;
        --amber:    #d97706;
        --red:      #dc2626;
        --purple:   #7c3aed;
        --shadow-sm: 0 1px 3px rgba(0,0,0,.04), 0 1px 2px rgba(0,0,0,.06);
        --shadow-md: 0 4px 6px -1px rgba(0,0,0,.05), 0 2px 4px -2px rgba(0,0,0,.05);
        --shadow-lg: 0 10px 15px -3px rgba(0,0,0,.06), 0 4px 6px -4px rgba(0,0,0,.04);
        --card-bg: #ffffff;
        --card-border: #e2e8f0;
        --inner-bg: #f8fafc;
        --inner-bg2: #f1f5f9;
        --track-bg: #e2e8f0;
        --glass: rgba(255,255,255,.8);
        --glass-border: rgba(37,99,235,.08);
    }

    /* ─── PREMIUM LIGHT BASE ─── */
    .stApp, [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%)!important;
        color:var(--ink)!important;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)!important;
        border-right:1px solid #e2e8f0!important;
        box-shadow: 2px 0 8px rgba(0,0,0,.03)!important;
    }

    /* ─── INPUTS ─── */
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] > div {
        background:#ffffff!important;
        border:1.5px solid #e2e8f0!important;
        color:var(--ink)!important;
        box-shadow: 0 1px 2px rgba(0,0,0,.04)!important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color:var(--accent)!important;
        box-shadow: 0 0 0 3px rgba(37,99,235,.1)!important;
    }

    /* ─── BUTTONS ─── */
    .stButton button {
        background:#ffffff!important;
        border:1.5px solid #e2e8f0!important;
        color:var(--ink)!important;
        box-shadow: 0 1px 3px rgba(0,0,0,.04)!important;
        transition: all .2s!important;
    }
    .stButton button:hover {
        border-color:var(--accent)!important;
        background:#f8fafc!important;
        box-shadow: 0 4px 12px rgba(37,99,235,.1)!important;
        transform: translateY(-1px)!important;
    }

    /* ─── SIDEBAR NAV ─── */
    [data-testid="stSidebar"] .stButton button[kind="primary"],
    [data-testid="stSidebar"] div[data-testid="stVerticalBlock"] button[kind="primary"] {
        background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)!important;
        color:#ffffff!important;
        border:none!important;
        box-shadow: 0 4px 14px rgba(37,99,235,.3), 0 2px 4px rgba(37,99,235,.15)!important;
        font-weight:700!important;
    }
    [data-testid="stSidebar"] .stButton button[kind="secondary"],
    [data-testid="stSidebar"] div[data-testid="stVerticalBlock"] button[kind="secondary"] {
        background:#ffffff!important;
        color:#475569!important;
        border:1.5px solid #e2e8f0!important;
        box-shadow: 0 1px 2px rgba(0,0,0,.04)!important;
    }
    [data-testid="stSidebar"] .stButton button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #eff6ff, #f0f9ff)!important;
        border-color:#93c5fd!important;
        color:var(--accent)!important;
        box-shadow: 0 2px 8px rgba(37,99,235,.08)!important;
    }

    /* ─── TABS ─── */
    [data-testid="stTabs"] [role="tablist"] { border-bottom:2px solid #e2e8f0; }
    [data-testid="stTabs"] [role="tab"] { color:#64748b!important; font-weight:700!important; font-size:.82rem!important; padding:12px 20px!important; border-radius:8px 8px 0 0!important; }
    [data-testid="stTabs"] [role="tab"]:hover { color:#0f172a!important; background:#f1f5f9!important; }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        color:#2563eb!important;
        background:#eff6ff!important;
        border:1px solid #2563eb!important;
        border-bottom:none!important;
        font-weight:800!important;
        box-shadow:0 -2px 8px rgba(37,99,235,.1)!important;
    }
    div[data-testid="stCaptionContainer"] { color:#64748b!important; }

    /* ─── TABLES ─── */
    .rcc-table-wrap {
        border:1px solid #e2e8f0!important;
        background:#ffffff!important;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,.04), 0 2px 4px -2px rgba(0,0,0,.04)!important;
        border-radius:12px!important;
    }
    .rcc-table thead th {
        background: linear-gradient(180deg, #f8fafc, #f1f5f9)!important;
        color:#475569!important;
        border-bottom:2px solid #e2e8f0!important;
    }
    .rcc-table tbody td {
        background:#ffffff!important;
        color:#0f172a!important;
        border-bottom:1px solid #f1f5f9!important;
    }
    .rcc-table tbody tr:nth-child(even) td { background:#f8fafc!important; }
    .rcc-table tbody tr:hover td { background:#eff6ff!important; }
    .rcc-table tbody tr:last-child td {
        background: linear-gradient(180deg, #f1f5f9, #e8f0fe)!important;
        color:#0f172a!important;
        font-weight:800!important;
        border-top:2px solid var(--accent)!important;
    }

    /* ─── LOGIN ─── */
    div[data-testid="stForm"] {
        background:#ffffff!important;
        border:1px solid #e2e8f0!important;
        box-shadow: 0 20px 60px rgba(0,0,0,.08), 0 8px 20px rgba(0,0,0,.04)!important;
    }
    /* Sidebar collapse arrow - both open and closed states */
    [data-testid="collapsedControl"] button {
        background:#2563eb!important;
        box-shadow:0 4px 14px rgba(37,99,235,.3)!important;
        border:2px solid #60a5fa!important;
    }
    [data-testid="collapsedControl"] svg,
    [data-testid="collapsedControl"] button svg,
    [data-testid="collapsedControl"] span { color:#ffffff!important; stroke:#ffffff!important; fill:#ffffff!important; }
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stSidebar"] button[kind="header"],
    [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button {
        background:#2563eb!important;
        border:none!important;
        border-radius:8px!important;
        min-width:32px!important;
        min-height:32px!important;
        box-shadow:0 4px 12px rgba(37,99,235,.3)!important;
    }
    [data-testid="stSidebarCollapseButton"] svg,
    [data-testid="stSidebarCollapseButton"] span,
    [data-testid="stSidebarCollapseButton"] button *,
    [data-testid="stSidebar"] button[kind="header"] svg,
    [data-testid="stSidebar"] button[kind="header"] span,
    [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] svg,
    [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] span { color:#ffffff!important; fill:#ffffff!important; stroke:#ffffff!important; visibility:visible!important; }

    /* ─── METRIC / HERO CARDS ─── */
    .metric-card {
        background:#ffffff!important;
        border:1px solid #e2e8f0!important;
        box-shadow: 0 2px 4px rgba(0,0,0,.04)!important;
    }
    .metric-card:hover { box-shadow: 0 8px 20px rgba(37,99,235,.08)!important; border-color:#93c5fd!important; }
    .metric-label { background:#f8fafc!important; color:#475569!important; border-bottom:1px solid #e2e8f0!important; }
    .metric-value { color:#0f172a!important; }
    .metric-note { color:#64748b!important; }
    .progress-track { background:#e2e8f0!important; }
    .hero-card {
        background:#ffffff!important;
        border:1px solid #e2e8f0!important;
        box-shadow: 0 4px 12px rgba(0,0,0,.04)!important;
    }
    .hero-card:hover { box-shadow: 0 12px 28px rgba(37,99,235,.08)!important; border-color:#bfdbfe!important; }
    .hero-box { background:#f8fafc!important; border:1px solid #e2e8f0!important; }
    .hero-box:hover { border-color:#93c5fd!important; background:#eff6ff!important; }
    .hero-total { background: linear-gradient(135deg, #f8fafc, #eff6ff)!important; color:#0f172a!important; border:1px solid #e2e8f0!important; }
    .receipt-stat-box { background:#f8fafc!important; border:1px solid #e2e8f0!important; }
    .receipt-stat-box:hover { border-color:#93c5fd!important; }
    .hero-prog-track { background:#e2e8f0!important; }
    .bkt-card { background:#ffffff!important; border:1px solid #e2e8f0!important; box-shadow: 0 2px 8px rgba(0,0,0,.04)!important; }
    .bkt-card:hover { border-color:#6ee7b7!important; box-shadow: 0 8px 24px rgba(5,150,105,.06)!important; }
    .bkt-mini-item { background:#f8fafc!important; border:1px solid #e2e8f0!important; }
    .mini-stat { background:#f8fafc!important; border:1px solid #e2e8f0!important; }

    /* ─── SECTION HEADING ─── */
    .section-head { color:#0f172a!important; border-bottom:2px solid #e2e8f0!important; }

    /* ─── EXPANDER ─── */
    [data-testid="stExpander"] {
        background:#ffffff!important;
        border:1px solid #e2e8f0!important;
        border-radius:10px!important;
        box-shadow: 0 2px 4px rgba(0,0,0,.03)!important;
    }
    [data-testid="stExpander"] summary { color:#0f172a!important; }
    [data-testid="stExpander"]:hover { border-color:#93c5fd!important; }

    /* ─── TEXT VISIBILITY ─── */
    .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown div { color:#0f172a!important; }
    label, [data-testid="stWidgetLabel"] label, [data-testid="stWidgetLabel"] p { color:#0f172a!important; }
    [data-testid="stRadio"] label span, [data-testid="stSelectbox"] label { color:#0f172a!important; }
    h1, h2, h3, h4, h5, h6 { color:#0f172a!important; }

    /* ─── SCROLLBAR ─── */
    ::-webkit-scrollbar-thumb { background:#cbd5e1!important; }
    ::-webkit-scrollbar-thumb:hover { background:#94a3b8!important; }
    ::-webkit-scrollbar-track { background:#f1f5f9!important; }

    /* ─── RADIO BUTTONS ─── */
    [data-testid="stRadio"] > div { gap:8px; }
    [data-testid="stRadio"] label {
        background:#ffffff!important;
        border:1.5px solid #e2e8f0!important;
        border-radius:8px!important;
        padding:8px 16px!important;
        color:#0f172a!important;
        transition: all .2s!important;
    }
    [data-testid="stRadio"] label:hover {
        border-color:#93c5fd!important;
        background:#eff6ff!important;
    }
    [data-testid="stRadio"] label[data-checked="true"],
    [data-testid="stRadio"] label:has(input:checked) {
        background: linear-gradient(135deg,#eff6ff,#dbeafe)!important;
        border-color:#2563eb!important;
        color:#1d4ed8!important;
        box-shadow: 0 2px 8px rgba(37,99,235,.12)!important;
    }
    [data-testid="stRadio"] input[type="radio"] { accent-color:#2563eb!important; }
    [data-testid="stRadio"] label p,
    [data-testid="stRadio"] label span,
    [data-testid="stRadio"] label div { color:#0f172a!important; }

    /* ─── SELECTBOX dark override fix ─── */
    div[data-testid="stSelectbox"] > div,
    div[data-testid="stSelectbox"] > div > div {
        background:#ffffff!important;
        border:1.5px solid #e2e8f0!important;
        color:#0f172a!important;
    }
    div[data-testid="stSelectbox"] span { color:#0f172a!important; }
    [data-testid="stSelectbox"] svg { fill:#475569!important; }

    /* Dropdown/popover menu */
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    ul[role="listbox"],
    div[data-baseweb="popover"] > div,
    div[data-baseweb="menu"] {
        background:#ffffff!important;
        border:1px solid #e2e8f0!important;
        box-shadow: 0 10px 40px rgba(0,0,0,.1)!important;
    }
    ul[role="listbox"] li,
    [data-baseweb="menu"] li,
    [role="option"] {
        background:#ffffff!important;
        color:#0f172a!important;
    }
    ul[role="listbox"] li:hover,
    [data-baseweb="menu"] li:hover,
    [role="option"]:hover,
    li[aria-selected="true"] {
        background:#eff6ff!important;
        color:#1d4ed8!important;
    }

    /* ─── ALERTS ─── */
    .stAlert { border-radius:10px!important; }

    /* ─── SIDEBAR OPEN ARROW (collapsed state) ─── */
    [data-testid="collapsedControl"] { z-index:99999!important; }
    .stApp [data-testid="collapsedControl"] button,
    [data-testid="collapsedControl"] > button {
        background:#2563eb!important;
        border:none!important;
        border-radius:10px!important;
        width:44px!important;
        height:44px!important;
        box-shadow:0 4px 14px rgba(37,99,235,.4)!important;
        opacity:1!important;
        visibility:visible!important;
    }
    .stApp [data-testid="collapsedControl"] button *,
    [data-testid="collapsedControl"] svg,
    [data-testid="collapsedControl"] path,
    [data-testid="collapsedControl"] span {
        color:#ffffff!important;
        fill:#ffffff!important;
        stroke:#ffffff!important;
        visibility:visible!important;
        opacity:1!important;
    }

    /* ─── CHIPS ─── */
    .chip-high { background:rgba(5,150,105,.1)!important; color:#059669!important; border:1px solid rgba(5,150,105,.25)!important; }
    .chip-mid { background:rgba(217,119,6,.1)!important; color:#d97706!important; border:1px solid rgba(217,119,6,.25)!important; }
    .chip-low { background:rgba(220,38,38,.1)!important; color:#dc2626!important; border:1px solid rgba(220,38,38,.25)!important; }
    </style>""", unsafe_allow_html=True)

st.markdown("""<style>

@keyframes fadeInUp { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }
@keyframes fillBar { from { width:0; } }
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:.7; } }
@keyframes shimmer { 0% { background-position:-200% 0; } 100% { background-position:200% 0; } }
@keyframes glow { 0%,100% { box-shadow:0 0 8px rgba(59,130,246,.2); } 50% { box-shadow:0 0 20px rgba(59,130,246,.4); } }

/* Base */
.stApp, [data-testid="stAppViewContainer"] { background:var(--bg)!important; color:var(--ink)!important; font-family:var(--font-main)!important; }
[data-testid="stSidebar"] { background:var(--surface)!important; border-right:1px solid var(--border)!important; }
[data-testid="stHeader"] { background:transparent!important; }
[data-testid="stMainBlockContainer"], div.block-container { padding-top:.3rem!important; }

/* Sidebar collapse */
[data-testid="collapsedControl"] { top:10px!important; left:6px!important; z-index:9999!important; }
[data-testid="collapsedControl"] button { background:var(--accent)!important; border-radius:10px!important; width:44px!important; height:44px!important; box-shadow:0 0 14px rgba(59,130,246,.5)!important; border:2px solid #60a5fa!important; transition:var(--transition)!important; }
[data-testid="collapsedControl"] button:hover { background:#2563eb!important; box-shadow:0 0 24px rgba(59,130,246,.8)!important; transform:scale(1.05); }
[data-testid="collapsedControl"] svg { color:white!important; stroke:white!important; width:20px!important; height:20px!important; }

/* Scrollbar */
::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:var(--border); border-radius:99px; }
::-webkit-scrollbar-thumb:hover { background:var(--muted); }

/* Header */
.rcc-header { background:linear-gradient(135deg,var(--surface),var(--surface2)); border:1px solid var(--border); border-radius:12px; padding:18px 24px; margin-bottom:20px; display:flex; align-items:center; justify-content:space-between; animation:fadeInUp .4s ease-out; box-shadow:var(--shadow-md); }
.rcc-logo { font-size:1.5rem; font-weight:800; color:var(--ink); letter-spacing:-.5px; }
.rcc-logo span { color:var(--accent); }
.rcc-tagline { color:var(--muted); font-size:.78rem; margin-top:3px; }
.rcc-badge { background:rgba(59,130,246,.12); color:var(--accent); border:1px solid rgba(59,130,246,.3); font-size:.68rem; font-weight:700; padding:4px 12px; border-radius:20px; text-transform:uppercase; }

/* Metric Cards */
.metric-card { background:var(--surface); border:1px solid var(--border); border-radius:10px; overflow:hidden; margin-bottom:8px; transition:var(--transition); animation:fadeInUp .5s ease-out; box-shadow:var(--shadow-sm); }
.metric-card:hover { border-color:var(--accent); box-shadow:0 4px 20px rgba(59,130,246,.1); transform:translateY(-1px); }
.metric-label { background:var(--surface2); color:var(--muted); font-size:.65rem; font-weight:700; text-transform:uppercase; padding:6px 12px; border-bottom:1px solid var(--border); letter-spacing:.05em; }
.metric-value { font-size:1.4rem; font-weight:800; color:var(--ink); padding:12px 12px 4px; font-family:var(--font-mono); }
.metric-note { color:var(--muted); font-size:.7rem; padding:0 12px 12px; }

/* Progress bar */
.progress-track { height:6px; background:var(--track-bg); border-radius:99px; overflow:hidden; margin:4px 12px 12px; }
.progress-fill { height:100%; background:linear-gradient(90deg,var(--accent),var(--green)); border-radius:99px; animation:fillBar .8s ease-out; }

/* Mini stats */
.mini-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; padding:0 12px 12px; }
.mini-stat { background:var(--bg); border:1px solid var(--border); border-radius:6px; padding:8px; transition:var(--transition); }
.mini-stat:hover { border-color:var(--accent); }
.mini-label { color:var(--muted); font-size:.6rem; font-weight:700; text-transform:uppercase; }
.mini-value { color:var(--ink); font-size:.85rem; font-weight:700; font-family:var(--font-mono); }

/* Bucket board */
.bucket-board { display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:16px; margin-bottom:20px; animation:fadeInUp .5s ease-out; }
.bkt-card { background:var(--surface); border:1px solid var(--border); border-radius:10px; padding:16px; transition:var(--transition); box-shadow:var(--shadow-sm); }
.bkt-card:hover { border-color:var(--green); box-shadow:0 4px 20px rgba(16,185,129,.08); transform:translateY(-2px); }
.bkt-title { font-size:.7rem; font-weight:700; color:var(--muted); text-transform:uppercase; margin-bottom:8px; }
.bkt-value { font-size:1.8rem; font-weight:800; color:var(--green); font-family:var(--font-mono); }
.bkt-mini { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-top:12px; }
.bkt-mini-item { background:var(--bg); border:1px solid var(--border); border-radius:6px; padding:6px; }
.bkt-mini-label { color:var(--muted); font-size:.6rem; font-weight:700; text-transform:uppercase; }
.bkt-mini-value { color:var(--ink); font-size:.85rem; font-weight:700; font-family:var(--font-mono); }

/* Section heading */
.section-head { font-size:.85rem; font-weight:700; color:var(--ink); margin:24px 0 12px; padding-bottom:8px; border-bottom:1px solid var(--border); text-transform:uppercase; letter-spacing:.04em; }

/* Tables */
.rcc-table-wrap { border:1px solid var(--border); border-radius:10px; overflow:auto; background:var(--surface); box-shadow:var(--shadow-md); animation:fadeInUp .5s ease-out; }
.rcc-table { width:100%; border-collapse:collapse; color:var(--ink); font-size:.78rem; }
.rcc-table thead th { position:sticky; top:0; z-index:10; background:var(--surface2); color:var(--muted); font-weight:700; text-align:left; border-bottom:2px solid var(--border); padding:8px 12px; white-space:nowrap; font-size:.68rem; text-transform:uppercase; letter-spacing:.03em; }
.rcc-table tbody td { background:var(--surface); color:var(--ink); border-bottom:1px solid var(--border); padding:6px 12px; white-space:nowrap; transition:background .15s; }
.rcc-table tbody tr:nth-child(even) td { background:var(--surface2); }
.rcc-table tbody tr:hover td { background:rgba(59,130,246,.06); }
.rcc-table tbody tr:last-child td { background:var(--surface2)!important; color:var(--ink)!important; font-weight:800!important; border-top:2px solid var(--accent); padding:8px 12px; }
.text-right { text-align:right; }

/* Status Chips */
.chip { display:inline-flex; align-items:center; padding:2px 8px; border-radius:20px; font-size:.68rem; font-weight:700; font-family:var(--font-mono); }
.chip-high { background:rgba(16,185,129,.15); color:#4ade80; border:1px solid rgba(16,185,129,.3); }
.chip-mid { background:rgba(245,158,11,.15); color:#fbbf24; border:1px solid rgba(245,158,11,.3); }
.chip-low { background:rgba(239,68,68,.15); color:#f87171; border:1px solid rgba(239,68,68,.3); }
.col-mono { font-family:var(--font-mono)!important; }

/* Tabs */
[data-testid="stTabs"] [role="tablist"] { gap:4px; border-bottom:2px solid var(--border); padding-bottom:0; }
[data-testid="stTabs"] [role="tab"] { color:var(--muted)!important; font-weight:700; font-size:.82rem; padding:12px 20px; transition:var(--transition); border-radius:8px 8px 0 0; border:1px solid transparent; border-bottom:none; }
[data-testid="stTabs"] [role="tab"]:hover { color:var(--ink)!important; background:var(--surface2); }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { color:var(--accent)!important; background:rgba(59,130,246,.08)!important; border:1px solid var(--accent)!important; border-bottom:none!important; font-weight:800; box-shadow:0 -2px 8px rgba(59,130,246,.15); }

/* Inputs & Buttons */
div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] > div { background:var(--surface2)!important; border:1px solid var(--border)!important; color:var(--ink)!important; border-radius:6px; transition:var(--transition); }
div[data-testid="stTextInput"] input:focus { border-color:var(--accent)!important; box-shadow:0 0 0 2px rgba(59,130,246,.2)!important; }
.stButton button { background:var(--surface2)!important; border:1px solid var(--border)!important; color:var(--ink)!important; border-radius:6px; font-weight:600; transition:var(--transition)!important; }
.stButton button:hover { border-color:var(--accent)!important; background:rgba(59,130,246,.1)!important; transform:translateY(-1px); box-shadow:0 4px 12px rgba(59,130,246,.15)!important; }

/* Sidebar nav - active (primary) button */
[data-testid="stSidebar"] .stButton button[kind="primary"],
[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] button[kind="primary"] {
    background:linear-gradient(135deg,#2563eb,#3b82f6)!important;
    color:#ffffff!important;
    border:none!important;
    box-shadow:0 4px 16px rgba(59,130,246,.35)!important;
    font-weight:700!important;
    transform:none!important;
}
[data-testid="stSidebar"] .stButton button[kind="secondary"],
[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] button[kind="secondary"] {
    background:var(--surface2)!important;
    color:var(--muted)!important;
    border:1px solid var(--border)!important;
}
[data-testid="stSidebar"] .stButton button[kind="secondary"]:hover {
    background:rgba(59,130,246,.08)!important;
    border-color:var(--accent)!important;
    color:var(--ink)!important;
}

/* Login form */
div[data-testid="stForm"] { width:min(400px,100%); background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:36px; margin:10vh auto 0; box-shadow:var(--shadow-lg); animation:fadeInUp .5s ease-out; }
.login-logo { font-size:1.6rem; font-weight:900; color:var(--ink); margin-bottom:4px; }
.login-logo span { color:var(--accent); }
.login-sub { color:var(--muted); font-size:.82rem; margin-bottom:24px; }
div[data-testid="stForm"] .stButton button, div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button { background:var(--accent)!important; color:#fff!important; border:none!important; border-radius:6px; font-weight:700; min-height:44px; }
div[data-testid="stForm"] .stButton button:hover, div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button:hover { background:#2563eb!important; box-shadow:0 4px 16px rgba(59,130,246,.3)!important; }

/* Hero Cards */
.hero-desktop { display:block; animation:fadeInUp .5s ease-out; }
.hero-wrap { display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:16px; margin:16px 0 24px; }

/* Hide mobile tabs on desktop */
.hero-desktop + div [data-testid="stTabs"] { display:none; }
.hero-card { background:linear-gradient(145deg,var(--surface),var(--surface2)); border:1px solid var(--border); border-radius:12px; padding:18px; position:relative; transition:var(--transition); box-shadow:var(--shadow-sm); overflow:hidden; }
.hero-card::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:linear-gradient(90deg,var(--green),var(--accent)); opacity:.6; }
.hero-card:hover { border-color:rgba(59,130,246,.4); box-shadow:0 8px 32px rgba(59,130,246,.08); transform:translateY(-2px); }
.hero-badge { display:inline-flex; align-items:center; gap:6px; background:rgba(59,130,246,.08); border:1px solid rgba(59,130,246,.2); border-radius:20px; padding:4px 12px; font-size:.62rem; font-weight:700; color:var(--muted); text-transform:uppercase; margin-bottom:16px; }
.hero-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-top:12px; }
.hero-box { background:var(--surface2); border:1px solid var(--border); border-radius:6px; padding:10px 6px; text-align:center; transition:var(--transition); }
.hero-box:hover { border-color:var(--accent); }
.hero-box-label { color:var(--muted); font-size:.58rem; font-weight:700; text-transform:uppercase; margin-bottom:4px; letter-spacing:.03em; }
.hero-box-val { color:var(--ink); font-size:1rem; font-weight:700; font-family:var(--font-mono); }
.hero-total { margin-top:16px; padding:10px 14px; border-radius:6px; background:var(--surface2); border:1px solid var(--border); color:var(--ink); font-weight:700; display:flex; justify-content:space-between; align-items:center; }
.hero-total-label { color:var(--muted); font-size:.62rem; text-transform:uppercase; letter-spacing:.03em; }
.hero-total-val { font-size:1.2rem; font-weight:800; font-family:var(--font-mono); }
.hero-prog-track { height:8px; background:var(--track-bg); border-radius:99px; overflow:hidden; margin:12px 0; }
.hero-prog-fill { height:100%; border-radius:99px; background:linear-gradient(90deg,var(--purple),#ec4899); animation:fillBar .8s ease-out; }
.hero-pct-label { display:flex; justify-content:flex-end; color:var(--muted); font-size:.62rem; margin-top:4px; font-family:var(--font-mono); }
.receipt-stats { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-top:12px; }
.receipt-stat-box { background:var(--surface2); border:1px solid var(--border); border-radius:6px; padding:10px; text-align:center; transition:var(--transition); }
.receipt-stat-box:hover { border-color:var(--accent); }
.receipt-stat-label { color:var(--muted); font-size:.58rem; font-weight:700; text-transform:uppercase; margin-bottom:4px; }
.receipt-stat-val { font-size:1.2rem; font-weight:800; font-family:var(--font-mono); }
.receipt-stat-val.paid { color:var(--green); }
.receipt-stat-val.unpaid { color:var(--red); }
.receipt-stat-val.total { color:var(--accent); }

/* CSS-only tabs for mobile hero */
.hero-mobile { display:none; }
.hero-tab-input { display:none; }
.hero-tab-nav { display:flex; gap:4px; margin-bottom:12px; background:var(--surface2); border-radius:8px; padding:4px; }
.hero-tab-label { flex:1; text-align:center; padding:8px 6px; font-size:.7rem; font-weight:700; color:var(--muted); cursor:pointer; border-radius:6px; transition:var(--transition); }
.hero-tab-label:hover { color:var(--ink); }
#htab1:checked ~ .hero-tab-nav label[for="htab1"],
#htab2:checked ~ .hero-tab-nav label[for="htab2"],
#htab3:checked ~ .hero-tab-nav label[for="htab3"] { background:var(--accent); color:#fff; }
.hero-tab-panels { position:relative; }
.hero-tab-panel { display:none; }
#htab1:checked ~ .hero-tab-panels .hero-tab-panel:nth-child(1) { display:block; }
#htab2:checked ~ .hero-tab-panels .hero-tab-panel:nth-child(2) { display:block; }
#htab3:checked ~ .hero-tab-panels .hero-tab-panel:nth-child(3) { display:block; }

@media (max-width: 768px) {
    .hero-desktop { display:none!important; }
    .hero-desktop + div [data-testid="stTabs"] { display:block!important; }
    .rcc-header { flex-direction:column; align-items:flex-start; gap:12px; padding:14px 16px; }
    .bucket-board { grid-template-columns:1fr 1fr; }
    .hero-card { padding:12px; }
    .hero-card div[style*="width:75px"] { width:50px!important; height:50px!important; }
    .hero-card svg { width:50px!important; height:50px!important; }
    .hero-card div[style*="position:absolute;inset:0"] div:first-child { font-size:.4rem!important; }
    .hero-card div[style*="position:absolute;inset:0"] div:last-child { font-size:.6rem!important; }
    .hero-card div[style*="font-size:2.2rem"] { font-size:1.5rem!important; }
    .hero-grid { gap:4px; margin-top:8px; }
    .hero-box { padding:6px 3px; }
    .hero-box-label { font-size:.5rem; }
    .hero-box-val { font-size:.78rem; }
    .hero-total { margin-top:10px; padding:6px 10px; }
    .hero-total-label { font-size:.55rem; }
    .hero-total-val { font-size:.9rem; }
    [data-testid="stSidebar"] { width:180px!important; }
    /* Payout slab grid mobile */
    .payout-grid { grid-template-columns:1fr 1fr!important; gap:8px!important; }
}
@media (max-width: 480px) {
    .bucket-board { grid-template-columns:1fr; }
    .hero-card { padding:10px; }
    .hero-card div[style*="width:75px"], .hero-card svg { width:40px!important; height:40px!important; }
    .hero-card div[style*="font-size:2.2rem"] { font-size:1.2rem!important; }
    .hero-grid { gap:2px; }
    .hero-box { padding:4px 2px; }
    .hero-box-label { font-size:.45rem; }
    .hero-box-val { font-size:.65rem; }
    .hero-total { padding:4px 6px; margin-top:6px; }
    .hero-total-val { font-size:.75rem; }
    .receipt-stat-label { font-size:.5rem; }
    .receipt-stat-val { font-size:.9rem; }
    /* Payout slab grid mobile small */
    .payout-grid { grid-template-columns:1fr!important; gap:8px!important; }
}

/* Sidebar arrows */
[data-testid="stSidebar"] button[kind="header"] span,
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] span,
[data-testid="stSidebar"] header button span { font-size:1.8rem!important; visibility:visible!important; }
span[style*="Material Symbols Rounded"],
[data-testid="stSidebar"] span.st-emotion-cache-13qy8gz,
[data-testid="stSidebar"] span[data-testid="stIconMaterial"] { font-size:1.8rem!important; visibility:visible!important; }

div[data-testid="stCaptionContainer"] { color:var(--muted)!important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def normalize_columns(df):
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    return df

def require_columns(df):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        st.error("Missing columns: " + ", ".join(missing))
        st.stop()

def as_number(series):
    cleaned = series.astype(str).str.replace(",", "", regex=False).str.replace("₹", "", regex=False).str.strip()
    return pd.to_numeric(cleaned, errors="coerce").fillna(0)

def clean_bucket(series):
    return pd.to_numeric(series.astype(str).str.extract(r"(\d+)", expand=False), errors="coerce").fillna(0).astype(int)

def clean_status(series):
    return series.astype(str).str.strip().str.upper()

def clean_team(series):
    return series.astype(str).str.strip().str.upper()

def excel_files():
    return sorted(APP_DIR.glob("*.xlsx"))

def format_indian(value):
    if pd.isna(value): return "₹0"
    v = float(value)
    if abs(v) >= 1_00_00_000: return f"₹{v/1_00_00_000:.2f} Cr"
    if abs(v) >= 1_00_000:    return f"₹{v/1_00_000:.2f} L"
    if abs(v) >= 1_000:       return f"₹{v/1_000:.1f} K"
    return f"₹{v:,.0f}"

def format_percent(value):
    if value is None or (isinstance(value, float) and math.isnan(value)): return "0.00%"
    return f"{float(value):.2f}%"


# ─────────────────────────────────────────────
# DATA SYNC
# ─────────────────────────────────────────────

def sync_source_excel():
    # In cloud mode, download from OneDrive
    if CLOUD_MODE:
        return _sync_from_onedrive()
    if not SOURCE_DATA_FILE.exists():
        if LOCAL_DATA_COPY.exists():
            return LOCAL_DATA_COPY, "⚠️ Source not reachable. Using last local copy."
        return None, "❌ Source not reachable and no local copy found."
    try:
        should_copy = (
            not LOCAL_DATA_COPY.exists()
            or SOURCE_DATA_FILE.stat().st_mtime > LOCAL_DATA_COPY.stat().st_mtime
        )
        if should_copy:
            shutil.copy2(SOURCE_DATA_FILE, LOCAL_DATA_COPY)
            _sync_to_onedrive()
            return LOCAL_DATA_COPY, "✅ Fresh data loaded from network."
        return LOCAL_DATA_COPY, "✅ Data is up to date."
    except PermissionError:
        if LOCAL_DATA_COPY.exists():
            return LOCAL_DATA_COPY, "⚠️ File locked. Using last local copy."
        return None, "❌ File locked. Close Excel on network, then refresh."
    except OSError as e:
        if LOCAL_DATA_COPY.exists():
            return LOCAL_DATA_COPY, f"⚠️ Network error. Using last local copy."
        return None, f"❌ Cannot read source. ({e})"


def _onedrive_direct_url(share_url):
    """Convert OneDrive share link to direct download URL."""
    # Append download=1 to force file download
    separator = "&" if "?" in share_url else "?"
    return f"{share_url}{separator}download=1"


def _sync_from_onedrive():
    """Download RCC_DATA.xlsx from OneDrive share link (cloud mode)."""
    import requests
    if not ONEDRIVE_SHARE_URL:
        if LOCAL_DATA_COPY.exists():
            return LOCAL_DATA_COPY, "⚠️ No OneDrive URL configured. Using cached file."
        return None, "❌ No OneDrive URL configured and no cached file."
    try:
        download_url = _onedrive_direct_url(ONEDRIVE_SHARE_URL)
        resp = requests.get(download_url, timeout=30, allow_redirects=True)
        if resp.status_code == 200 and len(resp.content) > 1000:
            LOCAL_DATA_COPY.write_bytes(resp.content)
            return LOCAL_DATA_COPY, "☁️ Fresh data downloaded from OneDrive."
        else:
            if LOCAL_DATA_COPY.exists():
                return LOCAL_DATA_COPY, f"⚠️ OneDrive download failed (HTTP {resp.status_code}). Using cached file."
            return None, f"❌ OneDrive download failed (HTTP {resp.status_code})."
    except Exception as e:
        if LOCAL_DATA_COPY.exists():
            return LOCAL_DATA_COPY, f"⚠️ OneDrive error. Using cached file."
        return None, f"❌ OneDrive download failed: {e}"


def _sync_to_onedrive():
    """Copy RCC_DATA.xlsx to OneDrive folder for cloud sync."""
    try:
        if LOCAL_DATA_COPY.exists() and ONEDRIVE_DATA_COPY.parent.exists():
            shutil.copy2(LOCAL_DATA_COPY, ONEDRIVE_DATA_COPY)
    except Exception:
        pass  # OneDrive sync is best-effort, don't break app

@st.cache_data(show_spinner=False)
def workbook_sheets(data_file):
    return pd.ExcelFile(data_file, engine="openpyxl").sheet_names

@st.cache_data(show_spinner=False)
def load_data(data_file, sheet_name, _mtime=0):
    df = pd.read_excel(data_file, sheet_name=sheet_name, engine="openpyxl")
    df = normalize_columns(df)
    require_columns(df)
    for col in ["BUCKET","POS","EMI","TOTAL EMI DUE","DPIC CHARGES",
                "STAB AMOUNTWITH DPIC","RB AMOUNTWITH DPIC","Paid Amount",
                "TRAILS PENDING","DRA CASE%","AGENCY CASE%","DPD"]:
        df[col] = as_number(df[col])
    df["LOAN NO"]       = df["LOAN NO"].astype(str).str.strip()
    df["CUSTOMER NAME"] = df["CUSTOMER NAME"].astype(str).str.strip()
    df["TEAM"]          = clean_team(df["TEAM"])
    df["POS STATUS"]    = clean_status(df["POS STATUS"])
    df["BUCKET"]        = clean_bucket(df["BUCKET"])
    df["RECEIPT CUT"]   = df["RECEIPT CUT"].astype(str).str.strip().str.upper()
    df["Receipt Cut Count"] = (df["RECEIPT CUT"] == "PAID").astype(int)
    df["AREA"]          = df["AREA"].astype(str).str.strip()
    df["Total Need"]    = (df["STAB AMOUNTWITH DPIC"] + df["RB AMOUNTWITH DPIC"]).clip(lower=0)
    return df


# ─────────────────────────────────────────────
# STATS
# ─────────────────────────────────────────────

def resolution_stats(df):
    status = df["POS STATUS"]
    pos    = df["POS"]
    flow_c   = int((status == "FLOW").sum())
    stable_c = int((status == "STABLE").sum())
    rb_c     = int((status == "RB").sum())
    flow_p   = float(pos[status == "FLOW"].sum())
    stable_p = float(pos[status == "STABLE"].sum())
    rb_p     = float(pos[status == "RB"].sum())
    total_p  = flow_p + stable_p + rb_p
    res      = ((stable_p + rb_p) / total_p * 100) if total_p else 0
    return {"Flow": flow_c, "Stable": stable_c, "RB": rb_c,
            "Flow POS": flow_p, "Stable POS": stable_p, "RB POS": rb_p,
            "Total POS": total_p, "Resolution %": res}


# ─────────────────────────────────────────────
# UI COMPONENTS
# ─────────────────────────────────────────────

def metric_card(label, value, note="", tone=""):
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">{label}</div>
      <div class="metric-value">{value}</div>
      <div class="metric-note">{note}</div>
    </div>""", unsafe_allow_html=True)

def progress_metric(label, value, pct, note="", tone=""):
    safe = max(0, min(100, float(pct)))
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">{label}</div>
      <div class="metric-value">{value}</div>
      <div class="progress-track"><div class="progress-fill" style="width:{safe:.1f}%"></div></div>
      <div class="metric-note">{note}</div>
    </div>""", unsafe_allow_html=True)

def bucket_board(df):
    cards = []
    for bkt, grp in df.groupby("BUCKET", dropna=False):
        s   = resolution_stats(grp)
        t   = s["Total POS"]
        sp  = (s["Stable POS"]/t*100) if t else 0
        rp  = (s["RB POS"]/t*100) if t else 0
        res = s["Resolution %"]
        safe= max(0, min(100, float(res)))
        b   = int(bkt) if float(bkt).is_integer() else bkt
        cards.append(f"""
        <div class="bkt-card">
          <div class="bkt-title">Bucket {b}</div>
          <div class="bkt-value">{format_percent(res)}</div>
          <div class="progress-track" style="margin:12px 0">
            <div class="progress-fill" style="width:{safe:.1f}%"></div>
          </div>
          <div class="bkt-mini">
            <div class="bkt-mini-item"><div class="bkt-mini-label">Flow</div><div class="bkt-mini-value">{s["Flow"]:,}</div></div>
            <div class="bkt-mini-item"><div class="bkt-mini-label">Stable%</div><div class="bkt-mini-value">{sp:.1f}%</div></div>
            <div class="bkt-mini-item"><div class="bkt-mini-label">RB%</div><div class="bkt-mini-value">{rp:.1f}%</div></div>
          </div>
        </div>""")
    st.markdown(f'<div class="bucket-board">{"".join(cards)}</div>', unsafe_allow_html=True)


def hero_dashboard_cards(b1,b2,receipt,paid,unpaid,total,collection):
    safe_r = max(0, min(100, float(receipt)))
    b1_res = b1['Resolution %']
    b2_res = b2['Resolution %']

    def donut_svg(pct, color1, color2, label, val_str, val_color, uid):
        r = 40
        circ = 2 * 3.14159 * r
        safe_pct = max(0, min(100, float(pct)))
        fill = safe_pct / 100 * circ
        gap  = circ - fill
        return (
            f'<svg width="75" height="75" viewBox="0 0 100 100" style="transform:rotate(-90deg);display:block">'
            f'<circle cx="50" cy="50" r="{r}" fill="none" stroke="{"#0a1425" if THEME=="dark" else "#e2e8f0"}" stroke-width="12"/>'
            f'<circle cx="50" cy="50" r="{r}" fill="none" stroke="url(#{uid})" stroke-width="12" '
            f'stroke-dasharray="{fill:.1f} {gap:.1f}" stroke-linecap="round"/>'
            f'<defs><linearGradient id="{uid}" x1="0%" y1="0%" x2="100%" y2="0%">'
            f'<stop offset="0%" style="stop-color:{color1}"/>'
            f'<stop offset="100%" style="stop-color:{color2}"/>'
            f'</linearGradient></defs>'
            f'</svg>'
        )

    def render_b1_card(uid_suffix=""):
        b1_donut = donut_svg(b1_res, "#10b981", "#4ade80", "Total POS", format_indian(b1['Total POS']), "#4ade80", f"g_b1{uid_suffix}")
        st.markdown(f"""
        <div class="hero-card">
          <div class="hero-badge">🏦 BUCKET 1 &nbsp;·&nbsp; RESOLUTION</div>
          <div style="display:flex;align-items:center;gap:20px;margin:12px 0 8px 0">
            <div style="position:relative;width:75px;height:75px;flex-shrink:0">
              {b1_donut}
              <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center">
                <div style="font-size:.5rem;color:var(--muted);font-weight:700;text-transform:uppercase">Total POS</div>
                <div style="font-size:.8rem;color:var(--green);font-weight:800">{format_indian(b1['Total POS'])}</div>
              </div>
            </div>
            <div>
              <div style="color:var(--muted);font-size:.65rem;font-weight:700;text-transform:uppercase">Resolution %</div>
              <div style="font-size:2.2rem;font-weight:800;color:var(--green);line-height:1">{b1_res:.2f}%</div>
            </div>
          </div>
          <div style="color:var(--muted);font-size:.6rem;font-weight:700;text-transform:uppercase;margin:12px 0 6px 0">COUNTS</div>
          <div class="hero-grid">
            <div class="hero-box"><div class="hero-box-label">Flow</div><div class="hero-box-val">{b1['Flow']:,}</div></div>
            <div class="hero-box"><div class="hero-box-label">Stable</div><div class="hero-box-val">{b1['Stable']:,}</div></div>
            <div class="hero-box"><div class="hero-box-label">RB</div><div class="hero-box-val">{b1['RB']:,}</div></div>
          </div>
          <div style="color:var(--muted);font-size:.6rem;font-weight:700;text-transform:uppercase;margin:12px 0 6px 0">POS AMOUNT (INR)</div>
          <div class="hero-grid">
            <div class="hero-box"><div class="hero-box-label">Flow</div><div class="hero-box-val">{format_indian(b1['Flow POS'])}</div></div>
            <div class="hero-box"><div class="hero-box-label">Stable</div><div class="hero-box-val">{format_indian(b1['Stable POS'])}</div></div>
            <div class="hero-box"><div class="hero-box-label">RB</div><div class="hero-box-val">{format_indian(b1['RB POS'])}</div></div>
          </div>
          <div class="hero-total"><span class="hero-total-label">TOTAL POS</span><span class="hero-total-val">{format_indian(b1['Total POS'])}</span></div>
        </div>""", unsafe_allow_html=True)

    def render_b2_card(uid_suffix=""):
        b2_donut = donut_svg(b2_res, "#3b82f6", "#7dd3fc", "Total POS", format_indian(b2['Total POS']), "#7dd3fc", f"g_b2{uid_suffix}")
        st.markdown(f"""
        <div class="hero-card">
          <div class="hero-badge">🏦 BUCKET 2 &nbsp;·&nbsp; RESOLUTION</div>
          <div style="display:flex;align-items:center;gap:20px;margin:12px 0 8px 0">
            <div style="position:relative;width:75px;height:75px;flex-shrink:0">
              {b2_donut}
              <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center">
                <div style="font-size:.5rem;color:var(--muted);font-weight:700;text-transform:uppercase">Total POS</div>
                <div style="font-size:.8rem;color:var(--accent);font-weight:800">{format_indian(b2['Total POS'])}</div>
              </div>
            </div>
            <div>
              <div style="color:var(--muted);font-size:.65rem;font-weight:700;text-transform:uppercase">Resolution %</div>
              <div style="font-size:2.2rem;font-weight:800;color:var(--accent);line-height:1">{b2_res:.2f}%</div>
            </div>
          </div>
          <div style="color:var(--muted);font-size:.6rem;font-weight:700;text-transform:uppercase;margin:12px 0 6px 0">COUNTS</div>
          <div class="hero-grid">
            <div class="hero-box"><div class="hero-box-label">Flow</div><div class="hero-box-val">{b2['Flow']:,}</div></div>
            <div class="hero-box"><div class="hero-box-label">Stable</div><div class="hero-box-val">{b2['Stable']:,}</div></div>
            <div class="hero-box"><div class="hero-box-label">RB</div><div class="hero-box-val">{b2['RB']:,}</div></div>
          </div>
          <div style="color:var(--muted);font-size:.6rem;font-weight:700;text-transform:uppercase;margin:12px 0 6px 0">POS AMOUNT (INR)</div>
          <div class="hero-grid">
            <div class="hero-box"><div class="hero-box-label">Flow</div><div class="hero-box-val">{format_indian(b2['Flow POS'])}</div></div>
            <div class="hero-box"><div class="hero-box-label">Stable</div><div class="hero-box-val">{format_indian(b2['Stable POS'])}</div></div>
            <div class="hero-box"><div class="hero-box-label">RB</div><div class="hero-box-val">{format_indian(b2['RB POS'])}</div></div>
          </div>
          <div class="hero-total"><span class="hero-total-label">TOTAL POS</span><span class="hero-total-val">{format_indian(b2['Total POS'])}</span></div>
        </div>""", unsafe_allow_html=True)

    def render_receipt_card(uid_suffix=""):
        rc_donut = donut_svg(receipt, "#8b5cf6", "#ec4899", "Achievement", f"{receipt:.1f}%", "#f472b6", f"g_rc{uid_suffix}")
        st.markdown(f"""
        <div class="hero-card">
          <div class="hero-badge">🏆 RECEIPT CUT</div>
          <div style="display:flex;align-items:center;gap:20px;margin:12px 0 8px 0">
            <div style="position:relative;width:75px;height:75px;flex-shrink:0">
              {rc_donut}
              <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center">
                <div style="font-size:.5rem;color:var(--muted);font-weight:700;text-transform:uppercase">Achiv.</div>
                <div style="font-size:.8rem;color:var(--purple);font-weight:800">{receipt:.1f}%</div>
              </div>
            </div>
            <div>
              <div style="color:var(--muted);font-size:.65rem;font-weight:700;text-transform:uppercase">Receipt Cut %</div>
              <div style="font-size:2.2rem;font-weight:800;color:var(--purple);line-height:1">{receipt:.2f}%</div>
            </div>
          </div>
          <div class="hero-prog-track"><div class="hero-prog-fill" style="width:{safe_r:.1f}%; background:var(--purple)"></div></div>
          <div class="hero-pct-label">{receipt:.2f}%</div>
          <div class="receipt-stats">
            <div class="receipt-stat-box"><div class="receipt-stat-label">Paid</div><div class="receipt-stat-val paid">{paid:,}</div></div>
            <div class="receipt-stat-box"><div class="receipt-stat-label">Unpaid</div><div class="receipt-stat-val unpaid">{unpaid:,}</div></div>
            <div class="receipt-stat-box"><div class="receipt-stat-label">Total</div><div class="receipt-stat-val total">{total:,}</div></div>
          </div>
          <div class="hero-total" style="margin-top:12px">
            <span class="hero-total-label">💰 Total Collection</span>
            <span class="hero-total-val" style="color:var(--purple)">{format_indian(collection)}</span>
          </div>
        </div>""", unsafe_allow_html=True)

    # Desktop: side-by-side grid (hidden on mobile via CSS)
    b1_donut = donut_svg(b1_res, "#10b981", "#4ade80", "Total POS", format_indian(b1['Total POS']), "#4ade80", "g_b1")
    b2_donut = donut_svg(b2_res, "#3b82f6", "#7dd3fc", "Total POS", format_indian(b2['Total POS']), "#7dd3fc", "g_b2")
    rc_donut = donut_svg(receipt, "#8b5cf6", "#ec4899", "Achievement", f"{receipt:.1f}%", "#f472b6", "g_rc")
    st.markdown(f"""
    <div class="hero-desktop">
    <div class="hero-wrap">
      <div class="hero-card">
        <div class="hero-badge">🏦 BUCKET 1 · RESOLUTION</div>
        <div style="display:flex;align-items:center;gap:20px;margin:12px 0 8px 0">
          <div style="position:relative;width:75px;height:75px;flex-shrink:0">{b1_donut}<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center"><div style="font-size:.5rem;color:var(--muted);font-weight:700;text-transform:uppercase">Total POS</div><div style="font-size:.8rem;color:var(--green);font-weight:800">{format_indian(b1['Total POS'])}</div></div></div>
          <div><div style="color:var(--muted);font-size:.65rem;font-weight:700;text-transform:uppercase">Resolution %</div><div style="font-size:2.2rem;font-weight:800;color:var(--green);line-height:1">{b1_res:.2f}%</div></div>
        </div>
        <div style="color:var(--muted);font-size:.6rem;font-weight:700;text-transform:uppercase;margin:12px 0 6px 0">COUNTS</div>
        <div class="hero-grid"><div class="hero-box"><div class="hero-box-label">Flow</div><div class="hero-box-val">{b1['Flow']:,}</div></div><div class="hero-box"><div class="hero-box-label">Stable</div><div class="hero-box-val">{b1['Stable']:,}</div></div><div class="hero-box"><div class="hero-box-label">RB</div><div class="hero-box-val">{b1['RB']:,}</div></div></div>
        <div style="color:var(--muted);font-size:.6rem;font-weight:700;text-transform:uppercase;margin:12px 0 6px 0">POS AMOUNT (INR)</div>
        <div class="hero-grid"><div class="hero-box"><div class="hero-box-label">Flow</div><div class="hero-box-val">{format_indian(b1['Flow POS'])}</div></div><div class="hero-box"><div class="hero-box-label">Stable</div><div class="hero-box-val">{format_indian(b1['Stable POS'])}</div></div><div class="hero-box"><div class="hero-box-label">RB</div><div class="hero-box-val">{format_indian(b1['RB POS'])}</div></div></div>
        <div class="hero-total"><span class="hero-total-label">TOTAL POS</span><span class="hero-total-val">{format_indian(b1['Total POS'])}</span></div>
      </div>
      <div class="hero-card">
        <div class="hero-badge">🏦 BUCKET 2 · RESOLUTION</div>
        <div style="display:flex;align-items:center;gap:20px;margin:12px 0 8px 0">
          <div style="position:relative;width:75px;height:75px;flex-shrink:0">{b2_donut}<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center"><div style="font-size:.5rem;color:var(--muted);font-weight:700;text-transform:uppercase">Total POS</div><div style="font-size:.8rem;color:var(--accent);font-weight:800">{format_indian(b2['Total POS'])}</div></div></div>
          <div><div style="color:var(--muted);font-size:.65rem;font-weight:700;text-transform:uppercase">Resolution %</div><div style="font-size:2.2rem;font-weight:800;color:var(--accent);line-height:1">{b2_res:.2f}%</div></div>
        </div>
        <div style="color:var(--muted);font-size:.6rem;font-weight:700;text-transform:uppercase;margin:12px 0 6px 0">COUNTS</div>
        <div class="hero-grid"><div class="hero-box"><div class="hero-box-label">Flow</div><div class="hero-box-val">{b2['Flow']:,}</div></div><div class="hero-box"><div class="hero-box-label">Stable</div><div class="hero-box-val">{b2['Stable']:,}</div></div><div class="hero-box"><div class="hero-box-label">RB</div><div class="hero-box-val">{b2['RB']:,}</div></div></div>
        <div style="color:var(--muted);font-size:.6rem;font-weight:700;text-transform:uppercase;margin:12px 0 6px 0">POS AMOUNT (INR)</div>
        <div class="hero-grid"><div class="hero-box"><div class="hero-box-label">Flow</div><div class="hero-box-val">{format_indian(b2['Flow POS'])}</div></div><div class="hero-box"><div class="hero-box-label">Stable</div><div class="hero-box-val">{format_indian(b2['Stable POS'])}</div></div><div class="hero-box"><div class="hero-box-label">RB</div><div class="hero-box-val">{format_indian(b2['RB POS'])}</div></div></div>
        <div class="hero-total"><span class="hero-total-label">TOTAL POS</span><span class="hero-total-val">{format_indian(b2['Total POS'])}</span></div>
      </div>
      <div class="hero-card">
        <div class="hero-badge">🏆 RECEIPT CUT</div>
        <div style="display:flex;align-items:center;gap:20px;margin:12px 0 8px 0">
          <div style="position:relative;width:75px;height:75px;flex-shrink:0">{rc_donut}<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center"><div style="font-size:.5rem;color:var(--muted);font-weight:700;text-transform:uppercase">Achiv.</div><div style="font-size:.8rem;color:var(--purple);font-weight:800">{receipt:.1f}%</div></div></div>
          <div><div style="color:var(--muted);font-size:.65rem;font-weight:700;text-transform:uppercase">Receipt Cut %</div><div style="font-size:2.2rem;font-weight:800;color:var(--purple);line-height:1">{receipt:.2f}%</div></div>
        </div>
        <div class="hero-prog-track"><div class="hero-prog-fill" style="width:{safe_r:.1f}%; background:var(--purple)"></div></div>
        <div class="hero-pct-label">{receipt:.2f}%</div>
        <div class="receipt-stats"><div class="receipt-stat-box"><div class="receipt-stat-label">Paid</div><div class="receipt-stat-val paid">{paid:,}</div></div><div class="receipt-stat-box"><div class="receipt-stat-label">Unpaid</div><div class="receipt-stat-val unpaid">{unpaid:,}</div></div><div class="receipt-stat-box"><div class="receipt-stat-label">Total</div><div class="receipt-stat-val total">{total:,}</div></div></div>
        <div class="hero-total" style="margin-top:12px"><span class="hero-total-label">💰 Total Collection</span><span class="hero-total-val" style="color:var(--purple)">{format_indian(collection)}</span></div>
      </div>
    </div>
    </div>
    """, unsafe_allow_html=True)

    # Cards already stacked on mobile via CSS (hero-wrap grid-template-columns: 1fr on mobile)

    # Mobile tabs (CSS hides on desktop, shows on mobile)
    tab1, tab2, tab3 = st.tabs(["🏦 Bucket 1", "🏦 Bucket 2", "🏆 Receipt"])
    with tab1:
        render_b1_card("_tab")
    with tab2:
        render_b2_card("_tab")
    with tab3:
        render_receipt_card("_tab")
def section(title):
    st.markdown(f'<div class="section-head">{title}</div>', unsafe_allow_html=True)

def display_table(df, height=360, key=None):
    if df is None or df.empty:
        st.info("No records found.")
        return

    view = df.reset_index(drop=True).copy()
    percent_cols = ["Resolution %", "Stable %", "RB %", "Receipt Cut %", "DRA CASE%", "AGENCY CASE%"]
    money_cols = [
        "POS", "EMI", "TOTAL EMI DUE", "DPIC CHARGES", "STAB AMOUNTWITH DPIC",
        "RB AMOUNTWITH DPIC", "Total Need", "Paid Amount", "Collection Amount",
    ]
    count_cols = ["Cases", "Flow", "Stable", "RB", "Pending Trails", "Receipt Cut"]

    for col in view.columns:
        if col in percent_cols:
            view[col] = pd.to_numeric(view[col], errors="coerce").fillna(0).map(lambda x: f"{x:.2f}%")
        elif col in money_cols or col in count_cols:
            numeric = pd.to_numeric(view[col], errors="coerce")
            view[col] = numeric.map(lambda x: f'<div class="text-right">{x:,.0f}</div>' if not pd.isna(x) else "")
        else:
            # Use mono font for Loan numbers
            if col == "LOAN NO":
                view[col] = view[col].fillna("").astype(str).map(lambda x: f'<span class="col-mono">{x}</span>')
            else:
                view[col] = view[col].fillna("").astype(str)

    html = view.to_html(index=False, escape=False, classes="rcc-table")
    st.markdown(
        f'<div class="rcc-table-wrap" style="max-height:{int(height)}px">{html}</div>',
        unsafe_allow_html=True,
    )


def display_table_with_res_color(df, height=360):
    """Display table with color-coded Resolution % column using Chips"""
    if df is None or df.empty:
        st.info("No records found.")
        return
    view = df.reset_index(drop=True).copy()
    percent_cols = ["Resolution %", "Stable %", "RB %", "Receipt Cut %", "DRA CASE%", "AGENCY CASE%"]
    money_cols   = ["POS","EMI","TOTAL EMI DUE","DPIC CHARGES","STAB AMOUNTWITH DPIC",
                    "RB AMOUNTWITH DPIC","Total Need","Paid Amount","Collection Amount"]
    count_cols   = ["Cases","Flow","Stable","RB","Pending Trails","Receipt Cut"]
    for col in view.columns:
        if col == "Resolution %":
            view[col] = pd.to_numeric(view[col], errors="coerce").fillna(0).map(
                lambda x: f'<span class="chip {"chip-high" if x>=10 else ("chip-mid" if x>=5 else "chip-low")}">{x:.2f}%</span>'
            )
        elif col in percent_cols:
            view[col] = pd.to_numeric(view[col], errors="coerce").fillna(0).map(lambda x: f"{x:.2f}%")
        elif col in money_cols or col in count_cols:
            numeric = pd.to_numeric(view[col], errors="coerce")
            view[col] = numeric.map(lambda x: f'<div class="text-right">{x:,.0f}</div>' if not pd.isna(x) else "")
        else:
            if col == "LOAN NO":
                view[col] = view[col].fillna("").astype(str).map(lambda x: f'<span class="col-mono">{x}</span>')
            else:
                view[col] = view[col].fillna("").astype(str)
    html = view.to_html(index=False, escape=False, classes="rcc-table")
    st.markdown(f'<div class="rcc-table-wrap" style="max-height:{int(height)}px">{html}</div>', unsafe_allow_html=True)

def bucket_summary_df(df):
    rows = []
    total_flow_pos = total_stable_pos = total_rb_pos = total_pos = 0
    for bkt, grp in df.groupby("BUCKET", dropna=False):
        s = resolution_stats(grp)
        t = s["Total POS"]
        b = int(bkt) if float(bkt).is_integer() else bkt
        total_flow_pos   += s["Flow POS"]
        total_stable_pos += s["Stable POS"]
        total_rb_pos     += s["RB POS"]
        total_pos        += t
        rows.append({
            "Bucket":       b,
            "Flow POS":     format_indian(s["Flow POS"]),
            "Stable POS":   format_indian(s["Stable POS"]),
            "RB POS":       format_indian(s["RB POS"]),
            "Grand Total":  format_indian(t),
            "Stable %":     round(s["Stable POS"]/t*100, 2) if t else 0,
            "RB %":         round(s["RB POS"]/t*100, 2) if t else 0,
            "Resolution %": s["Resolution %"],
        })
    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values("Bucket").reset_index(drop=True)
        # Add totals row
        total_res = ((total_stable_pos + total_rb_pos) / total_pos * 100) if total_pos else 0
        totals = pd.DataFrame([{
            "Bucket":       "TOTAL",
            "Flow POS":     format_indian(total_flow_pos),
            "Stable POS":   format_indian(total_stable_pos),
            "RB POS":       format_indian(total_rb_pos),
            "Grand Total":  format_indian(total_pos),
            "Stable %":     round(total_stable_pos/total_pos*100, 2) if total_pos else 0,
            "RB %":         round(total_rb_pos/total_pos*100, 2) if total_pos else 0,
            "Resolution %": total_res,
        }])
        result = pd.concat([result, totals], ignore_index=True)
    return result

def executive_ranking_df(df):
    rows = []
    for team, grp in df.groupby("TEAM", dropna=False):
        paid_count      = int((grp["RECEIPT CUT"] == "PAID").sum())
        grand_total     = len(grp)
        unpaid_count    = grand_total - paid_count
        achievement_pct = round(paid_count / grand_total * 100, 2) if grand_total else 0
        rows.append({
            "Executive":     team if pd.notna(team) else "Unassigned",
            "Paid":          paid_count,
            "Unpaid":        unpaid_count,
            "Grand Total":   grand_total,
            "Achievement %": achievement_pct,
        })
    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values("Achievement %", ascending=False).reset_index(drop=True)
        result.insert(0, "Rank", range(1, len(result)+1))
        t_paid  = result["Paid"].sum()
        t_unpaid= result["Unpaid"].sum()
        t_grand = result["Grand Total"].sum()
        t_pct   = round(t_paid / t_grand * 100, 2) if t_grand else 0
        result = pd.concat([result, pd.DataFrame([{
            "Rank": "—", "Executive": "Grand Total",
            "Paid": t_paid, "Unpaid": t_unpaid,
            "Grand Total": t_grand, "Achievement %": t_pct
        }])], ignore_index=True)
    return result


def calc_payout_slab(resolution_pct, rb_pct, bucket):
    """
    Returns (slab%, rb_achieved) for a given bucket.
    Slab determined ONLY by resolution %.
    RB % only applies penalty (-2%) if target missed — but minimum slab is always 8%.

    BKT-1 slabs:
      < 85%          → 8%  (RB target: 15%)
      85% - 87.99%   → 10% (RB target: 15%)
      88% - 89.99%   → 12% (RB target: 20%)
      >= 90%         → 15% (RB target: 25%)

    BKT-2 slabs:
      < 60%          → 8%  (RB target: 15%)
      60% - 64.99%   → 10% (RB target: 15%)
      65% - 69.99%   → 12% (RB target: 20%)
      >= 70%         → 15% (RB target: 25%)

    BKT 3-6: Always flat 8%, no RB penalty.
    """
    # Bucket 3-6: flat 8%, no penalty
    if bucket not in (1, 2):
        return 8, True

    PAYOUT_CONFIG = {
        1: [
            # (min_res, max_res, slab%, rb_target%)
            (90,  999, 15, 25),
            (88,  89.99, 12, 20),
            (85,  87.99, 10, 15),
            (0,   84.99,  8, 15),
        ],
        2: [
            (70,  999, 15, 25),
            (65,  69.99, 12, 20),
            (60,  64.99, 10, 15),
            (0,   59.99,  8, 15),
        ],
    }

    slabs = PAYOUT_CONFIG.get(bucket, PAYOUT_CONFIG[2])
    payout = 8
    rb_target = 15

    for min_res, max_res, rate, rb_req in slabs:
        if min_res <= resolution_pct <= max_res:
            payout = rate
            rb_target = rb_req
            break

    rb_achieved = rb_pct >= rb_target
    if not rb_achieved:
        payout = max(8, payout - 2)  # Minimum 8%, never go below

    return payout, rb_achieved


def executive_payout_df(df):
    """Per-executive payout: BKT-1 + BKT-2 separate slabs."""
    rows = []
    for team, grp in df.groupby("TEAM", dropna=False):
        if not pd.notna(team):
            continue
        row = {"Executive": team}
        total_payout = 0.0

        for bkt in [1, 2]:
            bgrp = grp[grp["BUCKET"] == bkt]
            total_cases = len(bgrp)
            if total_cases == 0:
                row[f"BKT-{bkt} Res%"] = "—"
                row[f"BKT-{bkt} RB%"]  = "—"
                row[f"BKT-{bkt} Slab"] = "—"
                row[f"BKT-{bkt} Payout"] = 0
                continue

            stable = int((bgrp["POS STATUS"] == "STABLE").sum())
            rb     = int((bgrp["POS STATUS"] == "RB").sum())
            res_pct = round((stable + rb) / total_cases * 100, 2)
            rb_pct  = round(rb / total_cases * 100, 2)

            collection = float(bgrp["Paid Amount"].sum())
            slab, rb_ok = calc_payout_slab(res_pct, rb_pct, bkt)
            payout_amt  = collection * slab / 100

            row[f"BKT-{bkt} Res%"]    = f"{res_pct:.1f}%"
            row[f"BKT-{bkt} RB%"]     = f"{rb_pct:.1f}%"
            row[f"BKT-{bkt} Slab"]    = f"{slab}%" + ("" if rb_ok else " (-2% RB)")
            row[f"BKT-{bkt} Collection"] = collection
            row[f"BKT-{bkt} Payout"]  = payout_amt
            total_payout += payout_amt

        # Bucket 3-6: flat 8% slab
        other_grp = grp[~grp["BUCKET"].isin([1, 2])]
        other_collection = float(other_grp["Paid Amount"].sum())
        other_payout = other_collection * 8 / 100
        row["BKT 3-6 Collection"] = other_collection
        row["BKT 3-6 Payout"] = other_payout
        total_payout += other_payout

        row["Total Payout"] = total_payout
        rows.append(row)

    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values("Total Payout", ascending=False).reset_index(drop=True)
        result.insert(0, "Rank", range(1, len(result)+1))
    return result


def executive_tracker_df(df):
    rows = []
    for team, grp in df.groupby("TEAM", dropna=False):
        s = resolution_stats(grp)
        tc = len(grp)
        pc = int(grp["Receipt Cut Count"].sum())
        pt = int((grp["TRAILS PENDING"] == 0).sum())
        rows.append({"Executive": team, "Cases": tc,
                     "Flow": s["Flow"], "Stable": s["Stable"], "RB": s["RB"],
                     "Resolution %": s["Resolution %"],
                     "Collection Amount": float(grp["Paid Amount"].sum()),
                     "Receipt Cut": pc,
                     "Receipt Cut %": (pc/tc*100) if tc else 0,
                     "Pending Trails": pt})

    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values(["Resolution %","Collection Amount"], ascending=False).reset_index(drop=True)
        result.insert(0, "Rank", range(1, len(result)+1))
    return result
def login():
    if "user" not in st.session_state:
        st.session_state.user = None
    if st.session_state.user:
        return
    _, center, _ = st.columns([1, 1.1, 1])
    with center:
        with st.form("login_form"):
            st.markdown("""
            <div class="login-logo">R<span>CC</span></div>
            <div class="login-sub">Resolution Command Center<br>Sign in to continue</div>
            """, unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="ADMIN").strip().upper()
            password = st.text_input("Password", type="password", placeholder="Password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)
            st.markdown('<div class="login-foot">Offline dashboard · Auto-refresh every 30s</div>', unsafe_allow_html=True)
    if submitted:
        rec = CREDENTIALS.get(username)
        if rec and rec["password"] == password:
            st.session_state.user = {"username": username, "role": rec["role"]}
            st.rerun()
        st.error("Invalid username or password.")
    st.stop()


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def trails_public_view(df_full):
    """Public pending trails view - no login required"""
    st.markdown("""
    <div style="padding:16px 0 8px 0">
      <div class="rcc-logo" style="font-size:1.5rem">Resolution <span style="color:var(--accent)">Command</span> Center</div>
      <div style="color:var(--muted);font-size:.85rem;margin-top:2px">📌 Pending Trails View</div>
    </div>
    """, unsafe_allow_html=True)

    teams = sorted(df_full["TEAM"].dropna().unique().tolist())
    sel = st.selectbox("Select your name", ["-- Select --"] + teams)

    if sel == "-- Select --":
        st.info("Select your name above to view your pending trails.")
        st.stop()

    pending = df_full[
        (df_full["TEAM"] == sel) &
        (df_full["TRAILS PENDING"] == 0)
    ].reset_index(drop=True)

    total = len(pending)

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{'#1e3a5f' if THEME=='dark' else '#dbeafe'},{'#2563eb' if THEME=='dark' else '#3b82f6'});border-radius:10px;padding:14px 20px;display:flex;align-items:center;gap:16px;margin-bottom:12px">
      <span style="font-size:1.5rem">📋</span>
      <div>
        <div style="color:{'rgba(255,255,255,0.7)' if THEME=='dark' else 'rgba(30,64,175,.7)'};font-size:.65rem;font-weight:700;text-transform:uppercase">Pending Trails</div>
        <div style="color:{'#fff' if THEME=='dark' else '#1e3a8a'};font-size:1.9rem;font-weight:800;line-height:1.1">{total}</div>
      </div>
      <div style="margin-left:auto;color:{'rgba(255,255,255,0.8)' if THEME=='dark' else 'rgba(30,64,175,.8)'};font-size:.9rem;font-weight:600">{sel}</div>
    </div>
    """, unsafe_allow_html=True)

    if pending.empty:
        st.success("✅ No pending trails!")
    else:
        pending = pending.sort_values("AREA").reset_index(drop=True)
        rows_html = ""
        for _, row in pending.iterrows():
            loan = str(row["LOAN NO"])
            name = str(row["CUSTOMER NAME"])
            area = str(row.get("AREA", "—"))
            rows_html += f'<tr style="border-bottom:1px solid {T["border"]}"><td style="padding:9px 12px;font-family:monospace;font-size:.82rem;font-weight:700;color:{T["ink"]}">{loan}</td><td style="padding:9px 12px;font-size:.82rem;color:{T["ink"]}">{name}</td><td style="padding:9px 12px;font-size:.78rem;vertical-align:middle"><span style="background:{T["surface2"]};color:{T["blue_val"]};border-radius:4px;padding:3px 10px;font-size:.75rem;font-weight:700">{area}</span></td></tr>'

        st.markdown(f'<div style="overflow-x:auto;border-radius:10px;border:1px solid {T["border"]}"><table style="width:100%;border-collapse:collapse"><thead><tr style="background:{T["inner_bg2"]};border-bottom:2px solid {T["border"]}"><th style="padding:10px 12px;text-align:left;font-size:.7rem;font-weight:700;color:{T["muted"]};text-transform:uppercase">Loan No</th><th style="padding:10px 12px;text-align:left;font-size:.7rem;font-weight:700;color:{T["muted"]};text-transform:uppercase">Customer Name</th><th style="padding:10px 12px;text-align:left;font-size:.7rem;font-weight:700;color:{T["muted"]};text-transform:uppercase">Area</th></tr></thead><tbody>{rows_html}</tbody></table></div>', unsafe_allow_html=True)


def copy_to_clipboard(text):
    try:
        import subprocess
        subprocess.run(['clip'], input=text.encode(), check=True)
        return True
    except Exception:
        return False


def flowlist_public_view(df_full):
    """Public flow list view - no login required, shows executive's cases"""
    st.markdown("""
    <div style="padding:16px 0 8px 0">
      <div class="rcc-logo" style="font-size:1.5rem">Resolution <span style="color:var(--accent)">Command</span> Center</div>
      <div style="color:var(--muted);font-size:.85rem;margin-top:2px">📋 Flow List View</div>
    </div>
    """, unsafe_allow_html=True)

    teams = sorted(df_full["TEAM"].dropna().unique().tolist())
    sel = st.selectbox("👤 Select Executive", ["-- Select --"] + teams, key="flow_pub_exec")

    if sel == "-- Select --":
        st.info("Select your name above to view your flow cases.")
        st.stop()

    flow_df = df_full[(df_full["TEAM"] == sel) & (df_full["POS STATUS"] == "FLOW")].copy()
    flow_df["DRA CASE%"] = flow_df["DRA CASE%"] * 100

    # Bucket filter
    all_bkts = sorted(flow_df["BUCKET"].dropna().unique().tolist())
    if all_bkts:
        bkt_labels = [f"BKT-{int(b)}" for b in all_bkts]
        default_idx = bkt_labels.index("BKT-1") if "BKT-1" in bkt_labels else 0
        sel_bkt = st.radio("Bucket", bkt_labels, index=default_idx, horizontal=True, key="flow_pub_bkt")
        bkt_num = int(sel_bkt.replace("BKT-", ""))
        flow_df = flow_df[flow_df["BUCKET"] == bkt_num]

    st.markdown(f"**{sel}** — Flow Cases: **{len(flow_df)}**")

    if flow_df.empty:
        st.success("✅ No flow cases in this bucket!")
    else:
        flow_df = flow_df.sort_values("DRA CASE%", ascending=False).reset_index(drop=True)
        rows_html = ""
        for _, row in flow_df.iterrows():
            name = str(row["CUSTOMER NAME"])
            pv = int(row["POS"]) if row["POS"] >= 1 else 0
            s = str(pv)
            if len(s) <= 3:
                pos = s
            else:
                pos = s[-3:]
                s = s[:-3]
                while s:
                    pos = s[-2:] + "," + pos
                    s = s[:-2]
                pos = pos.lstrip(",")
            dra = f'{row["DRA CASE%"]:.1f}%'
            rows_html += f'<tr style="border-bottom:1px solid {T["border"]}"><td style="padding:8px 10px;font-size:.82rem;color:{T["ink"]}">{name}</td><td style="padding:8px 10px;font-size:.82rem;color:{T["green_val"]};font-family:var(--font-mono);text-align:center">{pos}</td><td style="padding:8px 10px;font-size:.82rem;color:{T["amber_val"]};font-family:var(--font-mono);text-align:center">{dra}</td></tr>'
        st.markdown(f"""
        <div style="overflow-x:auto;border-radius:10px;border:1px solid {T['border']}">
          <table style="width:100%;border-collapse:collapse">
            <thead><tr style="background:{T['inner_bg2']};border-bottom:2px solid {T['border']}">
              <th style="padding:8px 10px;text-align:left;font-size:.68rem;font-weight:700;color:{T['muted']};text-transform:uppercase">Customer Name</th>
              <th style="padding:8px 10px;text-align:right;font-size:.68rem;font-weight:700;color:{T['muted']};text-transform:uppercase">POS</th>
              <th style="padding:8px 10px;text-align:right;font-size:.68rem;font-weight:700;color:{T['muted']};text-transform:uppercase">DRA Case %</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>""", unsafe_allow_html=True)


def main():
    # Check URL params for public trails view
    params = st.query_params
    if params.get("view") == "trails":
        # Load data without login
        synced_file, _ = sync_source_excel()
        files = excel_files()
        if files:
            idx = next((i for i, f in enumerate(files) if f.name == DEFAULT_DATA_FILE), 0)
            sel_file  = files[idx]
            sheets    = workbook_sheets(str(sel_file))
            sel_sheet = DEFAULT_SHEET_NAME if DEFAULT_SHEET_NAME in sheets else sheets[0]
            file_mtime = sel_file.stat().st_mtime
            df_full = load_data(str(sel_file), sel_sheet, _mtime=file_mtime)
            trails_public_view(df_full)
        else:
            st.error("Data file not found.")
        return

    if params.get("view") == "flowlist":
        # Public flow list view - no login
        synced_file, _ = sync_source_excel()
        files = excel_files()
        if files:
            idx = next((i for i, f in enumerate(files) if f.name == DEFAULT_DATA_FILE), 0)
            sel_file  = files[idx]
            sheets    = workbook_sheets(str(sel_file))
            sel_sheet = DEFAULT_SHEET_NAME if DEFAULT_SHEET_NAME in sheets else sheets[0]
            file_mtime = sel_file.stat().st_mtime
            df_full = load_data(str(sel_file), sel_sheet, _mtime=file_mtime)
            flowlist_public_view(df_full)
        else:
            st.error("Data file not found.")
        return

    login()
    user = st.session_state.user

    # Auto-refresh every 30s
    st_autorefresh(interval=30000, key="rcc_refresh")

    # Sync network file
    synced_file, sync_msg = sync_source_excel()

    files = excel_files()
    if not files:
        st.error("No Excel file found. Place RCC_DATA.xlsx beside app.py.")
        st.stop()

    idx = next((i for i, f in enumerate(files) if f.name == DEFAULT_DATA_FILE), 0)
    sel_file  = files[idx]
    sheets    = workbook_sheets(str(sel_file))
    sel_sheet = DEFAULT_SHEET_NAME if DEFAULT_SHEET_NAME in sheets else sheets[0]

    file_mtime = sel_file.stat().st_mtime
    df_full = load_data(str(sel_file), sel_sheet, _mtime=file_mtime)

    df = df_full if user["role"] == "admin" else df_full[df_full["TEAM"] == user["username"]].copy()

    # ── HEADER ──
    # ── GLOBAL KPIs ──
    stats      = resolution_stats(df)
    bkt1_stats = resolution_stats(df[df["BUCKET"] == 1])
    bkt2_stats = resolution_stats(df[df["BUCKET"] == 2])
    total_cases  = len(df)
    paid_count   = int(df["Receipt Cut Count"].sum())
    unpaid_count = total_cases - paid_count
    receipt_ach  = round(paid_count / total_cases * 100, 2) if total_cases else 0

    # ── SIDEBAR NAVIGATION ──
    NAV_ITEMS = [
        ("📊 DASHBOARD",        "dashboard"),
        ("📌 PENDING TRAILS",   "trails"),
        ("📋 FLOW LIST",        "flowlist"),
        ("🎯 ACTION CENTER",    "action"),
        ("👤 EXECUTIVE TRACKER","exec"),
        ("🔍 LOAN SEARCH",      "search"),
    ]

    with st.sidebar:
        if "active_tab" not in st.session_state:
            st.session_state.active_tab = "dashboard"

        for label, key in NAV_ITEMS:
            is_active = st.session_state.active_tab == key
            btn_style = "primary" if is_active else "secondary"
            if st.button(label, key=f"nav_{key}", use_container_width=True, type=btn_style):
                st.session_state.active_tab = key
                st.rerun()

        st.markdown("---")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            sync_source_excel()
            st.rerun()
        # Theme toggle
        theme_icon = "☀️" if THEME == "dark" else "🌙"
        theme_label = f"{theme_icon} Light Mode" if THEME == "dark" else f"{theme_icon} Dark Mode"
        if st.button(theme_label, use_container_width=True, key="theme_toggle"):
            st.session_state.theme = "light" if THEME == "dark" else "dark"
            st.rerun()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()
        st.caption(sync_msg)

    active = st.session_state.active_tab

    # ── PAGE: DASHBOARD ──
    if active == "dashboard":
        from datetime import datetime

        # ── Sync health ──
        data_mtime = LOCAL_DATA_COPY.stat().st_mtime if LOCAL_DATA_COPY.exists() else 0
        last_sync_dt = datetime.fromtimestamp(data_mtime) if data_mtime else None
        now = datetime.now()
        if last_sync_dt:
            sync_ago = (now - last_sync_dt).total_seconds()
            sync_ago_min = int(sync_ago // 60)
            sync_time_short = last_sync_dt.strftime("%I:%M %p")
            if sync_ago_min < 2:
                sync_color = "#10b981"; sync_label = "Just now"
            elif sync_ago_min < 15:
                sync_color = "#10b981"; sync_label = f"{sync_ago_min}m ago"
            elif sync_ago_min < 60:
                sync_color = "#f59e0b"; sync_label = f"{sync_ago_min}m ago"
            else:
                sync_color = "#ef4444"; sync_label = f"{sync_ago_min//60}h ago"
            if sync_ago > 900:
                warn_bg = "#7f1d1d" if THEME == "dark" else "#fef2f2"
                warn_border = "#ef4444" if THEME == "dark" else "#fca5a5"
                warn_text = "#fca5a5" if THEME == "dark" else "#991b1b"
                st.markdown(f'''<div style="background:{warn_bg};border:1px solid {warn_border};border-radius:8px;padding:10px 16px;margin-bottom:10px;font-size:.8rem;color:{warn_text}">⚠️ Data stale — last sync {sync_ago_min}m ago. Check sync worker.</div>''', unsafe_allow_html=True)
        else:
            sync_color = "#ef4444"; sync_label = "No data"; sync_time_short = "N/A"

        today_date = now.strftime("%d %b %Y")
        role_badge = "Admin" if user["role"] == "admin" else "Executive"

        # ── Per-executive payout (current user or admin sees all) ──
        exec_df = df if user["role"] != "admin" else df_full

        # Admin: Executive filter on dashboard
        if user["role"] == "admin":
            all_executives = ["All"] + sorted(df_full["TEAM"].dropna().unique().tolist())
            sel_dashboard_exec = st.selectbox("👤 Executive Filter", all_executives, key="dash_exec_filter")
            if sel_dashboard_exec != "All":
                exec_df = df_full[df_full["TEAM"] == sel_dashboard_exec].copy()

        exec_payout = executive_payout_df(exec_df)

        # ── Team-level BKT stats ──
        def bkt_stats_for(data, bkt):
            g = data[data["BUCKET"] == bkt]
            total = len(g)
            if total == 0:
                return {"total": 0, "flow": 0, "stable": 0, "rb": 0,
                        "res_pct": 0.0, "rb_pct": 0.0, "collection": 0.0,
                        "slab": 8, "payout": 0.0, "rb_ok": True}
            flow   = int((g["POS STATUS"] == "FLOW").sum())
            stable = int((g["POS STATUS"] == "STABLE").sum())
            rb     = int((g["POS STATUS"] == "RB").sum())
            res_pct = round((stable + rb) / total * 100, 2)
            rb_pct  = round(rb / total * 100, 2)
            collection = float(g["Paid Amount"].sum())
            slab, rb_ok = calc_payout_slab(res_pct, rb_pct, bkt)
            payout = collection * slab / 100
            return {"total": total, "flow": flow, "stable": stable, "rb": rb,
                    "res_pct": res_pct, "rb_pct": rb_pct, "collection": collection,
                    "slab": slab, "payout": payout, "rb_ok": rb_ok}

        b1 = bkt_stats_for(exec_df, 1)
        b2 = bkt_stats_for(exec_df, 2)

        # Bucket 3-6: flat 8% slab, no cards — just add to total collection/payout
        other_bkts_collection = float(exec_df[~exec_df["BUCKET"].isin([1, 2])]["Paid Amount"].sum())
        other_bkts_payout = other_bkts_collection * 8 / 100

        total_collection = b1["collection"] + b2["collection"] + other_bkts_collection
        total_payout     = b1["payout"] + b2["payout"] + other_bkts_payout
        paid_cases       = int((exec_df["RECEIPT CUT"] == "PAID").sum())
        unpaid_cases     = len(exec_df) - paid_cases
        rc_pct           = round(paid_cases / len(exec_df) * 100, 2) if len(exec_df) else 0
        rc_target        = 65.0
        rc_gap           = round(rc_target - rc_pct, 2)

        # Next slab info for BKT-1
        def next_slab_info(res_pct, bkt):
            NEXT = {1: [(85,10,"85%"),(88,12,"88%"),(90,15,"90%")],
                    2: [(60,10,"60%"),(65,12,"65%"),(70,15,"70%")]}
            for thresh, rate, label in NEXT.get(bkt, []):
                if res_pct < thresh:
                    return rate, label
            return None, None

        b1_next_rate, b1_next_thresh = next_slab_info(b1["res_pct"], 1)
        b2_next_rate, b2_next_thresh = next_slab_info(b2["res_pct"], 2)

        # Extra possible if next slab achieved
        b1_extra = round(b1["collection"] * (b1_next_rate - b1["slab"]) / 100, 0) if b1_next_rate else 0
        b2_extra = round(b2["collection"] * (b2_next_rate - b2["slab"]) / 100, 0) if b2_next_rate else 0
        total_extra = b1_extra + b2_extra

        # Slab projections include BKT 3-6 at flat 8%
        all_collection = total_collection  # already includes bkt 3-6

        # ── HEADER ──
        st.markdown(f"""
        <div style="background:{T['glass']};backdrop-filter:blur(12px);border:1px solid {T['glass_border']};border-radius:16px;padding:16px 24px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;box-shadow:{T['card_shadow']}">
          <div>
            <div style="font-size:1.3rem;font-weight:800;color:{T['ink']}">Hello {user["username"].title()}! 👋</div>
            <div style="font-size:.75rem;color:{T['muted']};margin-top:2px">Here's your collection & payout overview</div>
          </div>
          <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
            <div style="display:flex;align-items:center;gap:5px;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.2);border-radius:20px;padding:4px 10px">
              <span style="width:7px;height:7px;border-radius:50%;background:{sync_color};display:inline-block"></span>
              <span style="font-size:.65rem;color:{sync_color};font-weight:600">{sync_label}</span>
            </div>
            <div style="background:rgba(59,130,246,.08);border:1px solid rgba(59,130,246,.2);border-radius:20px;padding:4px 10px;font-size:.65rem;color:{T['blue_val']};font-weight:600">📅 {today_date}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── PAYOUT SLAB CARD ──
        slab_10_amt = total_collection * 0.10
        slab_12_amt = total_collection * 0.12
        slab_15_amt = total_collection * 0.15

        def fmt_full_inr(v):
            """Format as full ₹ number with Indian commas: ₹1,23,456"""
            if v < 0: return f"-{fmt_full_inr(-v)}"
            v = int(round(v))
            s = str(v)
            if len(s) <= 3: return f"₹{s}"
            result = s[-3:]
            s = s[:-3]
            while s:
                result = s[-2:] + "," + result
                s = s[:-2]
            return f"₹{result.lstrip(',')}"

        current_payout_full = fmt_full_inr(total_payout)
        slab_10_full = fmt_full_inr(slab_10_amt)
        slab_12_full = fmt_full_inr(slab_12_amt)
        slab_15_full = fmt_full_inr(slab_15_amt)
        extra_full = fmt_full_inr(total_extra)

        st.markdown(f"""
        <div style="background:{'linear-gradient(135deg,#1a1040,#2d1b69)' if THEME=='dark' else 'linear-gradient(135deg,#eef2ff,#e0e7ff)'};border:1px solid {'rgba(139,92,246,.3)' if THEME=='dark' else 'rgba(99,102,241,.15)'};border-radius:16px;padding:20px;margin-bottom:16px;box-shadow:{T['card_shadow']}">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px">
            <div>
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
                <span style="font-size:1.2rem">💰</span>
                <span style="font-size:.72rem;font-weight:700;color:{T['muted']};text-transform:uppercase">Total Collection</span>
              </div>
              <div style="font-size:2.2rem;font-weight:900;color:{T['ink']};font-family:var(--font-mono);line-height:1">{fmt_full_inr(total_collection)}</div>
            </div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:flex-start">
              <div style="text-align:center;padding:8px 16px;border-radius:10px;background:{'rgba(239,68,68,.12)' if THEME=='dark' else 'rgba(239,68,68,.06)'};border:1px solid rgba(239,68,68,.25)">
                <div style="font-size:.55rem;color:{T['muted']};font-weight:700">CURRENT</div>
                <div style="font-size:1.3rem;font-weight:900;color:{T['red']}">{b1['slab']}%</div>
                <div style="font-size:.72rem;font-weight:700;color:{T['ink']};margin-top:3px">{current_payout_full}</div>
              </div>
              <div style="text-align:center;padding:8px 16px;border-radius:10px;background:{'rgba(245,158,11,.12)' if THEME=='dark' else 'rgba(245,158,11,.06)'};border:1px solid rgba(245,158,11,.25)">
                <div style="font-size:.55rem;color:{T['muted']};font-weight:700">10% SLAB</div>
                <div style="font-size:1.3rem;font-weight:900;color:{T['amber']}">10%</div>
                <div style="font-size:.72rem;font-weight:700;color:{T['ink']};margin-top:3px">{slab_10_full}</div>
              </div>
              <div style="text-align:center;padding:8px 16px;border-radius:10px;background:{'rgba(16,185,129,.12)' if THEME=='dark' else 'rgba(16,185,129,.06)'};border:1px solid rgba(16,185,129,.25)">
                <div style="font-size:.55rem;color:{T['muted']};font-weight:700">12% SLAB</div>
                <div style="font-size:1.3rem;font-weight:900;color:{T['green']}">12%</div>
                <div style="font-size:.72rem;font-weight:700;color:{T['ink']};margin-top:3px">{slab_12_full}</div>
              </div>
              <div style="text-align:center;padding:8px 16px;border-radius:10px;background:{'rgba(139,92,246,.12)' if THEME=='dark' else 'rgba(139,92,246,.06)'};border:1px solid rgba(139,92,246,.25)">
                <div style="font-size:.55rem;color:{T['muted']};font-weight:700">15% SLAB</div>
                <div style="font-size:1.3rem;font-weight:900;color:{T['purple']}">15%</div>
                <div style="font-size:.72rem;font-weight:700;color:{T['ink']};margin-top:3px">{slab_15_full}</div>
              </div>
              <div style="text-align:center;padding:8px 16px;border-radius:10px;background:{'linear-gradient(135deg,rgba(74,222,128,.12),rgba(59,130,246,.08))' if THEME=='dark' else 'linear-gradient(135deg,rgba(5,150,105,.08),rgba(37,99,235,.04))'};border:1px solid rgba(74,222,128,.3)">
                <div style="font-size:.55rem;color:{T['green_val']};font-weight:700">🚀 EXTRA</div>
                <div style="font-size:1.3rem;font-weight:900;color:{T['green_val']}">+{extra_full}</div>
                <div style="font-size:.6rem;color:{T['muted']};margin-top:3px">Next Slab Bonus</div>
              </div>
            </div>
          </div>
          <div style="font-size:.65rem;color:{T['muted']};margin-top:12px">ℹ️ Payout calculated on total collection of {fmt_full_inr(total_collection)}</div>
        </div>
        """, unsafe_allow_html=True)

        # ── BKT-1 / BKT-2 / RECEIPT CUT CARDS ──
        def bkt_card_v2(stats, bkt_num, next_rate, next_thresh):
            target_res = 90 if bkt_num == 1 else 70
            rb_target = 25 if bkt_num == 1 else (20 if stats["res_pct"] >= (65 if bkt_num==2 else 65) else 15)
            res_color = T["green_val"] if stats["res_pct"] >= target_res else T["amber_val"] if stats["res_pct"] >= (85 if bkt_num==1 else 60) else T["red_val"]
            rb_color = T["green_val"] if stats["rb_pct"] >= rb_target else T["red_val"]
            res_gap = round(target_res - stats["res_pct"], 1)
            rb_gap_val = round(rb_target - stats["rb_pct"], 1)
            parts = []
            if res_gap > 0: parts.append(f"Need +{res_gap}% Resolution")
            if rb_gap_val > 0: parts.append(f"Need +{rb_gap_val}% RB")
            hint = " · ".join(parts) if parts else "🏆 All targets achieved!"
            card_border = f"rgba({'16,185,129' if bkt_num==1 else '59,130,246'},.2)"
            total_cases = stats["flow"] + stats["stable"] + stats["rb"]
            bkt_collection = fmt_full_inr(stats["collection"])
            res_bar = min(stats["res_pct"], 100)
            rb_bar = min(stats["rb_pct"], 100)
            return f"""
            <div style="background:{T['card_bg']};border:1px solid {card_border};border-radius:14px;padding:20px;box-shadow:{T['card_shadow']}">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
                <div style="display:flex;align-items:center;gap:8px"><span style="font-size:1.2rem">🏦</span><span style="font-size:1rem;font-weight:800;color:{T['ink']}">BKT-{bkt_num}</span></div>
                <div style="font-size:.75rem;color:{T['muted']}">Cases: <span style="font-weight:800;color:{T['ink']}">{total_cases:,}</span></div>
              </div>
              <div style="margin-bottom:16px">
                <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:6px">
                  <div><div style="font-size:.65rem;color:{T['muted']};font-weight:700;margin-bottom:4px">Resolution</div><div style="font-size:1.8rem;font-weight:900;color:{res_color};font-family:var(--font-mono)">{stats['res_pct']:.0f}%</div></div>
                  <div style="font-size:.82rem;color:{T['muted']};font-weight:600">Target {target_res}%</div>
                </div>
                <div style="height:8px;background:{T['track_bg']};border-radius:99px;position:relative"><div style="position:absolute;left:0;top:0;height:100%;width:{res_bar:.1f}%;background:linear-gradient(90deg,{'#10b981,#4ade80' if bkt_num==1 else '#3b82f6,#7dd3fc'});border-radius:99px"></div><div style="position:absolute;left:{target_res}%;top:-4px;width:2px;height:16px;background:{T['amber']};border-radius:2px"></div></div>
                <div style="display:flex;justify-content:space-between;font-size:.6rem;color:{T['muted']};margin-top:4px"><span>0%</span><span>100%</span></div>
              </div>
              <div style="margin-bottom:16px">
                <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:6px">
                  <div><div style="font-size:.65rem;color:{T['muted']};font-weight:700;margin-bottom:4px">RB %</div><div style="font-size:1.8rem;font-weight:900;color:{rb_color};font-family:var(--font-mono)">{stats['rb_pct']:.0f}%</div></div>
                  <div style="font-size:.82rem;color:{T['muted']};font-weight:600">Target {rb_target}%</div>
                </div>
                <div style="height:8px;background:{T['track_bg']};border-radius:99px;position:relative"><div style="position:absolute;left:0;top:0;height:100%;width:{rb_bar:.1f}%;background:linear-gradient(90deg,#8b5cf6,#c4b5fd);border-radius:99px"></div><div style="position:absolute;left:{rb_target}%;top:-4px;width:2px;height:16px;background:{T['amber']};border-radius:2px"></div></div>
                <div style="display:flex;justify-content:space-between;font-size:.6rem;color:{T['muted']};margin-top:4px"><span>0%</span><span>100%</span></div>
              </div>
              <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:14px">
                <div style="background:{T['inner_bg']};border:1px solid {T['border']};border-radius:8px;padding:10px;text-align:center"><div style="font-size:.58rem;color:{T['muted']};font-weight:700">👥 Flow</div><div style="font-size:1.1rem;font-weight:800;color:{T['flow_color']};margin-top:2px">{stats['flow']:,}</div></div>
                <div style="background:{T['inner_bg']};border:1px solid {T['border']};border-radius:8px;padding:10px;text-align:center"><div style="font-size:.58rem;color:{T['muted']};font-weight:700">✅ Stable</div><div style="font-size:1.1rem;font-weight:800;color:{T['stable_color']};margin-top:2px">{stats['stable']:,}</div></div>
                <div style="background:{T['inner_bg']};border:1px solid {T['border']};border-radius:8px;padding:10px;text-align:center"><div style="font-size:.58rem;color:{T['muted']};font-weight:700">⚠️ RB</div><div style="font-size:1.1rem;font-weight:800;color:{T['rb_color']};margin-top:2px">{stats['rb']:,}</div></div>
              </div>
              <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 14px;background:{T['inner_bg']};border:1px solid {T['border']};border-radius:8px;margin-bottom:12px"><span style="font-size:.72rem;color:{T['muted']};font-weight:700">💰 Collection</span><span style="font-size:1rem;font-weight:800;color:{T['green_val']};font-family:var(--font-mono)">{bkt_collection}</span></div>
              <div style="background:{T['inner_bg']};border:1px solid {T['border']};border-radius:8px;padding:10px 14px;margin-bottom:12px">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px"><span style="font-size:.72rem;color:{T['muted']};font-weight:700">📊 Projection</span><span style="font-size:1rem;font-weight:900;color:{res_color};font-family:var(--font-mono)">{stats['res_pct']:.1f}%</span></div>
                <div style="height:4px;background:{T['track_bg']};border-radius:99px;position:relative"><div style="position:absolute;left:0;top:0;height:100%;width:{min(stats['res_pct'],100):.1f}%;background:linear-gradient(90deg,{'#10b981,#4ade80' if bkt_num==1 else '#3b82f6,#7dd3fc'});border-radius:99px"></div></div>
                <div style="font-size:.6rem;color:{T['muted']};margin-top:4px">Target: {target_res}% · Need {int(max(0,(target_res*(stats['flow']+stats['stable']+stats['rb'])/100-(stats['stable']+stats['rb']))/(1-target_res/100)))} more stable/RB</div>
              </div>
              <div style="background:{'rgba(245,158,11,.08)' if THEME=='dark' else 'rgba(245,158,11,.05)'};border:1px solid rgba(245,158,11,.2);border-radius:8px;padding:10px 14px;font-size:.72rem;color:{T['amber_val']};font-weight:600">{hint}</div>
            </div>
            """

        rc_bar = min(rc_pct / rc_target * 100, 100) if rc_target else 0
        # Bucket-wise collection
        bkt_collections = []
        for bkt_num in sorted(exec_df["BUCKET"].dropna().unique()):
            bkt_col = float(exec_df[exec_df["BUCKET"] == bkt_num]["Paid Amount"].sum())
            if bkt_col > 0:
                bkt_collections.append((int(bkt_num), bkt_col))
        bkt_col_html = ""
        for bnum, bcol in bkt_collections:
            bkt_col_html += f'<div style="display:flex;align-items:center;justify-content:space-between;padding:8px 14px;background:{T["surface2"]};border-radius:8px;border:1px solid {T["border"]}"><span style="font-size:.75rem;color:{T["muted"]};font-weight:600">BKT-{bnum}</span><span style="font-size:.85rem;font-weight:800;color:{T["ink"]};font-family:var(--font-mono)">{fmt_full_inr(bcol)}</span></div>'

        receipt_card_html = f"""
        <div style="background:{T['card_bg']};border:1px solid rgba(139,92,246,.2);border-radius:14px;padding:20px;box-shadow:{T['card_shadow']}">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px">
            <span style="font-size:1.2rem">📋</span>
            <span style="font-size:1rem;font-weight:800;color:{T['ink']}">RECEIPT CUT</span>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:8px">
            <div><div style="font-size:.65rem;color:{T['muted']};font-weight:700;margin-bottom:4px">Current</div><div style="font-size:2rem;font-weight:900;color:{T['green_val']};font-family:var(--font-mono)">{rc_pct:.0f}%</div></div>
            <div style="text-align:right"><div style="font-size:.65rem;color:{T['muted']};font-weight:700;margin-bottom:4px">Target</div><div style="font-size:2rem;font-weight:900;color:{T['accent']};font-family:var(--font-mono)">{rc_target:.0f}%</div></div>
          </div>
          <div style="height:8px;background:{T['track_bg']};border-radius:99px;overflow:hidden;margin-bottom:12px;position:relative">
            <div style="position:absolute;left:0;top:0;height:100%;width:{rc_bar:.1f}%;background:linear-gradient(90deg,{T['accent']},{T['green']});border-radius:99px"></div>
            <div style="position:absolute;left:65%;top:-4px;width:2px;height:16px;background:{T['amber']};border-radius:2px"></div>
          </div>
          <div style="display:flex;justify-content:space-between;font-size:.65rem;color:{T['muted']};margin-bottom:16px">
            <span>0%</span>
            <span style="color:{T['amber_val']};font-weight:700">Target 65%</span>
            <span>100%</span>
          </div>
          <div style="font-size:.78rem;color:{T['muted']};margin-bottom:16px">Gap <span style="color:{T['amber_val']};font-weight:800;font-size:.85rem">{max(rc_gap,0):.0f}%</span></div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px">
            <div style="background:{'rgba(16,185,129,.08)' if THEME=='dark' else 'rgba(5,150,105,.04)'};border:1px solid {'rgba(16,185,129,.2)' if THEME=='dark' else 'rgba(5,150,105,.15)'};border-radius:10px;padding:14px;text-align:center">
              <div style="font-size:.62rem;color:{T['muted']};font-weight:700;margin-bottom:4px">✅ Paid</div>
              <div style="font-size:1.6rem;font-weight:900;color:{T['green_val']};font-family:var(--font-mono)">{paid_cases:,}</div>
              <div style="font-size:.6rem;color:{T['muted']};margin-top:2px">{round(paid_cases/len(exec_df)*100,1) if len(exec_df) else 0}%</div>
            </div>
            <div style="background:{'rgba(239,68,68,.08)' if THEME=='dark' else 'rgba(220,38,38,.04)'};border:1px solid {'rgba(239,68,68,.2)' if THEME=='dark' else 'rgba(220,38,38,.15)'};border-radius:10px;padding:14px;text-align:center">
              <div style="font-size:.62rem;color:{T['muted']};font-weight:700;margin-bottom:4px">❌ Unpaid</div>
              <div style="font-size:1.6rem;font-weight:900;color:{T['red_val']};font-family:var(--font-mono)">{unpaid_cases:,}</div>
              <div style="font-size:.6rem;color:{T['muted']};margin-top:2px">{round(unpaid_cases/len(exec_df)*100,1) if len(exec_df) else 0}%</div>
            </div>
          </div>
          <div style="background:{T['inner_bg']};border-radius:12px;padding:16px;border:1px solid {T['border']}">
            <div style="font-size:.72rem;color:{T['muted']};font-weight:700;margin-bottom:12px">💰 Collection (Bucket-wise)</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px">
              {bkt_col_html}
            </div>
            <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 14px;background:{'rgba(16,185,129,.08)' if THEME=='dark' else 'rgba(5,150,105,.05)'};border:1px solid {'rgba(16,185,129,.2)' if THEME=='dark' else 'rgba(5,150,105,.15)'};border-radius:8px">
              <span style="font-size:.78rem;color:{T['muted']};font-weight:700">Total Collection</span>
              <span style="font-size:1.1rem;font-weight:900;color:{T['green_val']};font-family:var(--font-mono)">{fmt_full_inr(total_collection)}</span>
            </div>
          </div>
        </div>
        """

        # Render: 3 columns - stacks on mobile automatically
        dc1, dc2, dc3 = st.columns(3)
        with dc1:
            st.markdown(receipt_card_html, unsafe_allow_html=True)
        with dc2:
            st.markdown(bkt_card_v2(b1, 1, b1_next_rate, b1_next_thresh), unsafe_allow_html=True)
        with dc3:
            st.markdown(bkt_card_v2(b2, 2, b2_next_rate, b2_next_thresh), unsafe_allow_html=True)

        # Admin only — executive payout table
        if user["role"] == "admin":
            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            section("💰 Executive Payout Table")
            if not exec_payout.empty:
                disp = exec_payout.copy()
                for bkt in [1, 2]:
                    if f"BKT-{bkt} Collection" in disp.columns:
                        disp[f"BKT-{bkt} Collection"] = disp[f"BKT-{bkt} Collection"].apply(lambda x: format_indian(x) if isinstance(x, (int,float)) else x)
                    if f"BKT-{bkt} Payout" in disp.columns:
                        disp[f"BKT-{bkt} Payout"] = disp[f"BKT-{bkt} Payout"].apply(lambda x: format_indian(x) if isinstance(x, (int,float)) else x)
                if "BKT 3-6 Collection" in disp.columns:
                    disp["BKT 3-6 Collection"] = disp["BKT 3-6 Collection"].apply(lambda x: format_indian(x) if isinstance(x, (int,float)) else x)
                if "BKT 3-6 Payout" in disp.columns:
                    disp["BKT 3-6 Payout"] = disp["BKT 3-6 Payout"].apply(lambda x: format_indian(x) if isinstance(x, (int,float)) else x)
                disp["Total Payout"] = exec_payout["Total Payout"].apply(format_indian)
                display_table(disp, height=400)

    # ── PAGE: ACTION CENTER ──
    elif active == "action":
        section("📂 CASES")

        action_df = (
            df[df["Total Need"] > 0]
            .sort_values("Total Need", ascending=False)
            .copy()
        )

        search = st.text_input(
            "🔍 Search Loan No / Customer Name",
            placeholder="Loan No or First Name"
        )

        if search:
            q = search.strip().lower()

            action_df = action_df[
                action_df["LOAN NO"].astype(str).str.lower().str.contains(q, na=False)
                |
                action_df["CUSTOMER NAME"].astype(str).str.lower().str.contains(q, na=False)
            ]

        st.caption(f"Cases requiring action: {len(action_df):,}")

        for _, row in action_df.iterrows():
            with st.expander(
                f"🏦 {row['CUSTOMER NAME']} | "
                f"EMI ₹{row['EMI']:,.0f} | "
                f"DPIC ₹{row['DPIC CHARGES']:,.0f} | "
                f"STAB ₹{row['STAB AMOUNTWITH DPIC']:,.0f}"
            ):
                c1, c2 = st.columns(2)

                with c1:
                    st.markdown("### Basic Details")
                    st.write(f"**Loan No:** {row['LOAN NO']}")
                    st.write(f"**Customer:** {row['CUSTOMER NAME']}")
                    st.write(f"**Executive:** {row['TEAM']}")

                with c2:
                    st.markdown("### Recovery")
                    st.write(f"**EMI:** ₹{row['EMI']:,.0f}")
                    st.write(f"**EMI Due:** ₹{row['TOTAL EMI DUE']:,.0f}")
                    st.write(f"**Total Need:** ₹{row['Total Need']:,.0f}")

                st.divider()

                c3, c4 = st.columns(2)

                with c3:
                    st.write(f"**DPIC:** ₹{row['DPIC CHARGES']:,.0f}")
                    st.write(f"**STAB:** ₹{row['STAB AMOUNTWITH DPIC']:,.0f}")

                with c4:
                    st.write(f"**RB:** ₹{row['RB AMOUNTWITH DPIC']:,.0f}")
                    st.write(f"**DPD:** {row['DPD']}")

                st.divider()

                st.write(f"**Area:** {row['AREA']}")
                st.write(f"**Mobile:** {row['MOBILE']}")
                st.write(f"**Bucket:** {row['BUCKET']}")
                st.write(f"**POS Status:** {row['POS STATUS']}")
                st.write(f"**Receipt Cut:** {row['RECEIPT CUT']}")
                st.write(f"**Trails Pending:** {row['TRAILS PENDING']}")

    # ── PAGE: PENDING TRAILS ──
    elif active == "trails":
        pending_df = df[df["TRAILS PENDING"] == 0].copy()
        total_pending = len(pending_df)

        # Executive filter
        teams = ["All"] + sorted(pending_df["TEAM"].dropna().unique().tolist())
        if user["role"] == "admin":
            sel_team = st.selectbox("👤 EXECUTIVE", teams, key="trails_exec_filter")
            if sel_team != "All":
                pending_df = pending_df[pending_df["TEAM"] == sel_team]
        else:
            uname = user["username"]
            pending_df = pending_df[pending_df["TEAM"] == uname]

        showing = len(pending_df)
        base_url = "https://app.rccapp.xyz"
        share_url = f"{base_url}/?view=trails"
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,{'#1e3a5f' if THEME=='dark' else '#dbeafe'},{'#2563eb' if THEME=='dark' else '#3b82f6'});border-radius:10px;padding:14px 20px;display:flex;align-items:center;gap:16px;margin-bottom:12px">
              <span style="font-size:1.5rem">📋</span>
              <div>
                <div style="color:{'rgba(255,255,255,0.7)' if THEME=='dark' else 'rgba(30,64,175,.7)'};font-size:.65rem;font-weight:700;text-transform:uppercase">Total Pending Cases</div>
                <div style="color:{'#fff' if THEME=='dark' else '#1e3a8a'};font-size:1.9rem;font-weight:800;line-height:1.1">{total_pending}</div>
              </div>
              <div style="margin-left:auto;color:{'rgba(255,255,255,0.6)' if THEME=='dark' else 'rgba(30,64,175,.6)'};font-size:.8rem">Showing {showing}</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            if user["role"] == "admin":
                link_bg = "#1a2540" if THEME == "dark" else "#eff6ff"
                link_border = "#1e3460" if THEME == "dark" else "#bfdbfe"
                link_color = "#7dd3fc" if THEME == "dark" else "#1d4ed8"
                st.markdown(f'<div style="background:{link_bg};border:1px solid {link_border};border-radius:8px;padding:10px 14px;font-size:.72rem;color:{link_color};word-break:break-all;margin-bottom:6px;font-family:var(--font-mono)">{share_url}</div>', unsafe_allow_html=True)
                if st.button("📋 Copy Link", use_container_width=True, key="copy_trails_link"):
                    st.code(share_url)

        # Card list
        if pending_df.empty:
            st.info("No pending trails found.")
        else:
            pending_df = pending_df.sort_values("AREA").reset_index(drop=True)
            is_admin = user["role"] == "admin"
            exec_th = f'<th style="padding:10px 14px;text-align:left;font-size:.7rem;font-weight:700;color:{T["muted"]};text-transform:uppercase;letter-spacing:.03em">Executive</th>' if is_admin else ""
            rows_html = ""
            row_border = "#1e3460" if THEME == "dark" else "#edf2f7"
            area_bg = "#1e3460" if THEME == "dark" else "#e0e7ff"
            area_color = "#7dd3fc" if THEME == "dark" else "#3730a3"
            for idx_r, (_, row) in enumerate(pending_df.iterrows()):
                loan = str(row["LOAN NO"])
                name = str(row["CUSTOMER NAME"])
                area = str(row.get("AREA", "—"))
                team = str(row.get("TEAM", ""))
                exec_td = f'<td style="padding:10px 14px;font-size:.8rem;color:{T["blue_val"]}">{team}</td>' if is_admin else ""
                row_bg = T["inner_bg2"] if idx_r % 2 == 1 else T["surface"]
                rows_html += f'<tr style="background:{row_bg};border-bottom:1px solid {row_border}"><td style="padding:10px 14px;font-family:monospace;font-size:.84rem;font-weight:700;color:{T["ink"]}">{loan}</td><td style="padding:10px 14px;font-size:.84rem;color:{T["ink"]}">{name}</td><td style="padding:10px 14px;font-size:.8rem;vertical-align:middle"><span style="background:{area_bg};color:{area_color};border-radius:6px;padding:4px 12px;font-size:.72rem;font-weight:700;letter-spacing:.02em;display:inline-block">{area}</span></td>{exec_td}</tr>'
            table_border = "#1e3460" if THEME == "dark" else "#e2e8f0"
            table_shadow = "0 4px 16px rgba(0,0,0,.2)" if THEME == "dark" else "0 4px 12px rgba(0,0,0,.05)"
            thead_bg = "#0a1628" if THEME == "dark" else "linear-gradient(180deg,#f8fafc,#f1f5f9)"
            thead_border = "#1e3460" if THEME == "dark" else "#cbd5e1"
            st.markdown(f'<div style="overflow-x:auto;border-radius:12px;border:1px solid {table_border};box-shadow:{table_shadow};-webkit-overflow-scrolling:touch"><table style="width:100%;border-collapse:collapse;min-width:500px"><thead><tr style="background:{thead_bg};border-bottom:2px solid {thead_border}"><th style="padding:10px 14px;text-align:left;font-size:.7rem;font-weight:700;color:{T["muted"]};text-transform:uppercase;white-space:nowrap;letter-spacing:.03em">Loan No</th><th style="padding:10px 14px;text-align:left;font-size:.7rem;font-weight:700;color:{T["muted"]};text-transform:uppercase;white-space:nowrap;letter-spacing:.03em">Customer Name</th><th style="padding:10px 14px;text-align:left;font-size:.7rem;font-weight:700;color:{T["muted"]};text-transform:uppercase;white-space:nowrap;letter-spacing:.03em">Area</th>{exec_th}</tr></thead><tbody>{rows_html}</tbody></table></div>', unsafe_allow_html=True)

    # ── PAGE: FLOW LIST ──
    elif active == "flowlist":
        section("📋 FLOW LIST")

        # Status filter dropdown - FLOW, STABLE, RB
        status_options = ["FLOW", "STABLE", "RB"]
        sel_status = st.selectbox("POS Status", status_options, index=0, key="flow_status_filter")

        flow_df = df[df["POS STATUS"] == sel_status].copy()
        flow_df["DRA CASE%"] = flow_df["DRA CASE%"] * 100

        # Executive filter - Admin only
        if user["role"] == "admin":
            flow_teams = ["All"] + sorted(flow_df["TEAM"].dropna().unique().tolist())
            sel_flow_exec = st.selectbox("👤 Executive", flow_teams, key="flow_exec_filter")
            if sel_flow_exec != "All":
                flow_df = flow_df[flow_df["TEAM"] == sel_flow_exec]

        # Bucket filter - default BKT-1
        all_bkts = sorted(flow_df["BUCKET"].dropna().unique().tolist())
        if all_bkts:
            bkt_labels = [f"BKT-{int(b)}" for b in all_bkts]
            default_idx = bkt_labels.index("BKT-1") if "BKT-1" in bkt_labels else 0
            sel_bkt = st.radio("Bucket", bkt_labels, index=default_idx, horizontal=True, key="flow_bkt")
            bkt_num = int(sel_bkt.replace("BKT-", ""))
            flow_df = flow_df[flow_df["BUCKET"] == bkt_num]
        else:
            st.info(f"No {sel_status} cases found.")
            flow_df = flow_df.iloc[0:0]

        # Share link - only for admin
        if user["role"] == "admin":
            share_url = "https://app.rccapp.xyz/?view=flowlist"
            link_bg = "#1a2540" if THEME == "dark" else "#eff6ff"
            link_border = "#1e3460" if THEME == "dark" else "#bfdbfe"
            link_color = "#7dd3fc" if THEME == "dark" else "#1d4ed8"
            st.markdown(f'<div style="background:{link_bg};border:1px solid {link_border};border-radius:8px;padding:10px 14px;font-size:.72rem;color:{link_color};word-break:break-all;margin:8px 0;font-family:var(--font-mono)">{share_url}</div>', unsafe_allow_html=True)
            if st.button("📋 Copy Link", use_container_width=True, key="copy_flow_link"):
                st.toast("Link copied! Share on WhatsApp.")

        st.caption(f"Showing: {len(flow_df):,} {sel_status.lower()} cases")

        if flow_df.empty:
            st.info(f"No {sel_status} cases in this bucket.")
        else:
            is_admin = user["role"] == "admin"
            flow_df = flow_df.sort_values("POS", ascending=False).reset_index(drop=True)

            # Build table HTML - POS in Indian format, center aligned
            rows_flow = ""
            row_border = "#1e3460" if THEME == "dark" else "#e2e8f0"
            row_hover_bg = "rgba(59,130,246,.06)" if THEME == "dark" else "#f8fafc"
            for idx_r, (_, row) in enumerate(flow_df.iterrows()):
                name = str(row["CUSTOMER NAME"])
                pos_val = row["POS"]
                # Indian comma format: 1,23,456
                pv = int(pos_val) if pos_val >= 1 else 0
                s = str(pv)
                if len(s) <= 3:
                    pos = s
                else:
                    pos = s[-3:]
                    s = s[:-3]
                    while s:
                        pos = s[-2:] + "," + pos
                        s = s[:-2]
                    pos = pos.lstrip(",")
                
                dra = f'{row["DRA CASE%"]:.1f}%'
                team = str(row.get("TEAM", ""))
                row_bg = T["inner_bg2"] if idx_r % 2 == 1 else T["surface"]
                exec_td = f'<td class="flow-col-exec" style="padding:10px 14px;font-size:.8rem;color:{T["blue_val"]};text-align:center">{team}</td>' if is_admin else ""
                rows_flow += f'<tr style="background:{row_bg};border-bottom:1px solid {row_border}"><td style="padding:10px 14px;font-size:.84rem;font-weight:500;color:{T["ink"]}">{name}</td><td style="padding:10px 14px;font-size:.84rem;color:{T["green_val"]};font-family:var(--font-mono);text-align:center;font-weight:700">{pos}</td><td style="padding:10px 14px;font-size:.84rem;color:{T["amber_val"]};font-family:var(--font-mono);text-align:center;font-weight:600">{dra}</td>{exec_td}</tr>'

            exec_th = f'<th class="flow-col-exec" style="padding:10px 14px;text-align:center;font-size:.7rem;font-weight:700;color:{T["muted"]};text-transform:uppercase;letter-spacing:.03em">Executive</th>' if is_admin else ""

            table_border = "#1e3460" if THEME == "dark" else "#e2e8f0"
            table_shadow = "0 4px 16px rgba(0,0,0,.2)" if THEME == "dark" else "0 4px 12px rgba(0,0,0,.05)"
            thead_bg = "#0a1628" if THEME == "dark" else "linear-gradient(180deg,#f8fafc,#f1f5f9)"
            thead_border = "#1e3460" if THEME == "dark" else "#cbd5e1"
            html_out = f'<style>@media (max-width: 768px) {{ .flow-col-exec {{ display:none!important; }} }}</style><div style="overflow-x:auto;border-radius:12px;border:1px solid {table_border};box-shadow:{table_shadow}"><table style="width:100%;border-collapse:collapse"><thead><tr style="background:{thead_bg};border-bottom:2px solid {thead_border}"><th style="padding:10px 14px;text-align:left;font-size:.7rem;font-weight:700;color:{T["muted"]};text-transform:uppercase;letter-spacing:.03em">Customer Name</th><th style="padding:10px 14px;text-align:center;font-size:.7rem;font-weight:700;color:{T["muted"]};text-transform:uppercase;letter-spacing:.03em">POS</th><th style="padding:10px 14px;text-align:center;font-size:.7rem;font-weight:700;color:{T["muted"]};text-transform:uppercase;letter-spacing:.03em">DRA Case %</th>{exec_th}</tr></thead><tbody>{rows_flow}</tbody></table></div>'
            st.markdown(html_out, unsafe_allow_html=True)

    # ── PAGE: EXECUTIVE TRACKER ──
    elif active == "exec":
        section("👤 Executive Tracker")
        if user["role"] == "admin":
            teams = ["All"] + sorted(df["TEAM"].dropna().unique().tolist())
            sel_exec = st.selectbox("Executive", teams, key="exec_sel")
            detail_df = df if sel_exec == "All" else df[df["TEAM"] == sel_exec]
        else:
            detail_df = df

        es = resolution_stats(detail_df)
        ec = len(detail_df)
        etrails = int((detail_df["TRAILS PENDING"] == 0).sum())

        ek = st.columns(4)
        with ek[0]: progress_metric("Resolution %", format_percent(es["Resolution %"]), es["Resolution %"], "", "green")
        with ek[1]: metric_card("Cases", f"{ec:,}")
        with ek[2]: metric_card("Collection", format_indian(detail_df["Paid Amount"].sum()), "", "green")
        with ek[3]: metric_card("Pending Trails", f"{etrails:,}", "", "amber")

        if user["role"] == "admin":
            section("Executive Summary")
            esum = executive_tracker_df(df_full)
            display_table(esum, height=300)

        section("Case Details")
        case_cols = ["LOAN NO","CUSTOMER NAME","TEAM","BUCKET","POS STATUS","POS",
                     "Paid Amount","RECEIPT CUT","TRAILS PENDING","AREA"]
        case_df = detail_df[case_cols].sort_values(["TEAM","BUCKET","POS"], ascending=[True,True,False])
        display_table(case_df, height=440)

    # ── PAGE: LOAN SEARCH ──
    elif active == "search":
        section("🔍 Loan Search")
        search = st.text_input("Search by Loan No or Customer Name", placeholder="Type loan number or name...")
        if search:
            needle = search.strip().lower()
            matches = df[
                df["LOAN NO"].astype(str).str.lower().str.contains(needle, na=False) |
                df["CUSTOMER NAME"].astype(str).str.lower().str.contains(needle, na=False)
            ]
            st.caption(f"Found: {len(matches):,} results")
            if matches.empty:
                st.info("No results found. Try a different search term.")
            else:
                search_cols = ["LOAN NO", "CUSTOMER NAME", "TEAM", "BUCKET", "POS STATUS", "POS", "AREA", "MOBILE", "RECEIPT CUT", "Paid Amount"]
                display_cols = [c for c in search_cols if c in matches.columns]
                display_table(matches[display_cols], height=480)


if __name__ == "__main__":
    main()
