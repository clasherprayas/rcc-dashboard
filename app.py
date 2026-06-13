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

/* ── PREMIUM DARK THEME ── */
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
}

@keyframes fadeInUp { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }
@keyframes fillBar { from { width:0; } }

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
.rcc-logo { font-size:1.5rem; font-weight:800; color:#fff; letter-spacing:-.5px; }
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
.progress-track { height:6px; background:#0a1425; border-radius:99px; overflow:hidden; margin:4px 12px 12px; }
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
.rcc-table tbody td { background:var(--surface); color:var(--ink); border-bottom:1px solid rgba(45,59,82,.5); padding:6px 12px; white-space:nowrap; transition:background .15s; }
.rcc-table tbody tr:nth-child(even) td { background:rgba(11,17,32,.5); }
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
[data-testid="stTabs"] [role="tab"] { color:var(--muted)!important; font-weight:600; font-size:.78rem; padding:10px 18px; transition:var(--transition); border-radius:6px 6px 0 0; }
[data-testid="stTabs"] [role="tab"]:hover { color:var(--ink)!important; background:var(--surface2); }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { color:var(--accent)!important; border-bottom:2px solid var(--accent)!important; background:rgba(59,130,246,.05); }

/* Inputs & Buttons */
div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] > div { background:var(--surface2)!important; border:1px solid var(--border)!important; color:var(--ink)!important; border-radius:6px; transition:var(--transition); }
div[data-testid="stTextInput"] input:focus { border-color:var(--accent)!important; box-shadow:0 0 0 2px rgba(59,130,246,.2)!important; }
.stButton button { background:var(--surface2)!important; border:1px solid var(--border)!important; color:var(--ink)!important; border-radius:6px; font-weight:600; transition:var(--transition)!important; }
.stButton button:hover { border-color:var(--accent)!important; background:rgba(59,130,246,.1)!important; transform:translateY(-1px); box-shadow:0 4px 12px rgba(59,130,246,.15)!important; }

/* Login form */
div[data-testid="stForm"] { width:min(400px,100%); background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:36px; margin:10vh auto 0; box-shadow:var(--shadow-lg); animation:fadeInUp .5s ease-out; }
.login-logo { font-size:1.6rem; font-weight:900; color:#fff; margin-bottom:4px; }
.login-logo span { color:var(--accent); }
.login-sub { color:var(--muted); font-size:.82rem; margin-bottom:24px; }
div[data-testid="stForm"] .stButton button, div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button { background:var(--accent)!important; color:#fff!important; border:none!important; border-radius:6px; font-weight:700; min-height:44px; }
div[data-testid="stForm"] .stButton button:hover, div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button:hover { background:#2563eb!important; box-shadow:0 4px 16px rgba(59,130,246,.3)!important; }

/* Hero Cards */
.hero-desktop { display:block; animation:fadeInUp .5s ease-out; }
.hero-wrap { display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:16px; margin:16px 0 24px; }
.hero-card { background:linear-gradient(145deg,var(--surface),rgba(26,37,64,.6)); border:1px solid var(--border); border-radius:12px; padding:18px; position:relative; transition:var(--transition); box-shadow:var(--shadow-sm); overflow:hidden; }
.hero-card::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:linear-gradient(90deg,var(--green),var(--accent)); opacity:.6; }
.hero-card:hover { border-color:rgba(59,130,246,.4); box-shadow:0 8px 32px rgba(59,130,246,.08); transform:translateY(-2px); }
.hero-badge { display:inline-flex; align-items:center; gap:6px; background:rgba(59,130,246,.08); border:1px solid rgba(59,130,246,.2); border-radius:20px; padding:4px 12px; font-size:.62rem; font-weight:700; color:var(--muted); text-transform:uppercase; margin-bottom:16px; }
.hero-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-top:12px; }
.hero-box { background:rgba(11,17,32,.6); border:1px solid var(--border); border-radius:6px; padding:10px 6px; text-align:center; transition:var(--transition); }
.hero-box:hover { border-color:var(--accent); }
.hero-box-label { color:var(--muted); font-size:.58rem; font-weight:700; text-transform:uppercase; margin-bottom:4px; letter-spacing:.03em; }
.hero-box-val { color:var(--ink); font-size:1rem; font-weight:700; font-family:var(--font-mono); }
.hero-total { margin-top:16px; padding:10px 14px; border-radius:6px; background:rgba(11,17,32,.6); border:1px solid var(--border); color:#fff; font-weight:700; display:flex; justify-content:space-between; align-items:center; }
.hero-total-label { color:var(--muted); font-size:.62rem; text-transform:uppercase; letter-spacing:.03em; }
.hero-total-val { font-size:1.2rem; font-weight:800; font-family:var(--font-mono); }
.hero-prog-track { height:8px; background:rgba(11,17,32,.8); border-radius:99px; overflow:hidden; margin:12px 0; }
.hero-prog-fill { height:100%; border-radius:99px; background:linear-gradient(90deg,var(--purple),#ec4899); animation:fillBar .8s ease-out; }
.hero-pct-label { display:flex; justify-content:flex-end; color:var(--muted); font-size:.62rem; margin-top:4px; font-family:var(--font-mono); }
.receipt-stats { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-top:12px; }
.receipt-stat-box { background:rgba(11,17,32,.6); border:1px solid var(--border); border-radius:6px; padding:10px; text-align:center; transition:var(--transition); }
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
    .hero-mobile { display:block!important; }
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
    if pd.isna(value): return "0"
    v = float(value)
    if abs(v) >= 1_00_00_000: return f"{v/1_00_00_000:.2f} Cr"
    if abs(v) >= 1_00_000:    return f"{v/1_00_000:.2f} L"
    if abs(v) >= 1_000:       return f"{v/1_000:.1f} K"
    return f"{v:,.0f}"

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
            f'<circle cx="50" cy="50" r="{r}" fill="none" stroke="#0a1425" stroke-width="12"/>'
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

    # Mobile: tabs (hidden on desktop via CSS)
    st.markdown('<div class="hero-mobile">', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["🏦 Bucket 1", "🏦 Bucket 2", "🏆 Receipt"])
    with tab1:
        render_b1_card("_tab")
    with tab2:
        render_b2_card("_tab")
    with tab3:
        render_receipt_card("_tab")
    st.markdown('</div>', unsafe_allow_html=True)
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
    <div style="background:linear-gradient(135deg,#1e3a5f,#2563eb);border-radius:10px;padding:14px 20px;display:flex;align-items:center;gap:16px;margin-bottom:12px">
      <span style="font-size:1.5rem">📋</span>
      <div>
        <div style="color:rgba(255,255,255,0.7);font-size:.65rem;font-weight:700;text-transform:uppercase">Pending Trails</div>
        <div style="color:#fff;font-size:1.9rem;font-weight:800;line-height:1.1">{total}</div>
      </div>
      <div style="margin-left:auto;color:rgba(255,255,255,0.8);font-size:.9rem;font-weight:600">{sel}</div>
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
            rows_html += f'<tr style="border-bottom:1px solid #1a2540"><td style="padding:9px 12px;font-family:monospace;font-size:.82rem;font-weight:700;color:#f1f5f9">{loan}</td><td style="padding:9px 12px;font-size:.82rem;color:#f1f5f9">{name}</td><td style="padding:9px 12px;font-size:.78rem;vertical-align:middle"><span style="background:#1e3460;color:#7dd3fc;border-radius:4px;padding:3px 10px;font-size:.75rem;font-weight:700">{area}</span></td></tr>'

        st.markdown(f'<div style="overflow-x:auto;border-radius:10px;border:1px solid #1e3460"><table style="width:100%;border-collapse:collapse"><thead><tr style="background:#0a1628;border-bottom:2px solid #1e3460"><th style="padding:10px 12px;text-align:left;font-size:.7rem;font-weight:700;color:#7a8ba8;text-transform:uppercase">Loan No</th><th style="padding:10px 12px;text-align:left;font-size:.7rem;font-weight:700;color:#7a8ba8;text-transform:uppercase">Customer Name</th><th style="padding:10px 12px;text-align:left;font-size:.7rem;font-weight:700;color:#7a8ba8;text-transform:uppercase">Area</th></tr></thead><tbody>{rows_html}</tbody></table></div>', unsafe_allow_html=True)


def copy_to_clipboard(text):
    try:
        import subprocess
        subprocess.run(['clip'], input=text.encode(), check=True)
        return True
    except Exception:
        return False


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
        ("🎯 ACTION CENTER",    "action"),
        ("🚨 DRA & AGENCY",     "dra"),
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
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()
        st.caption(sync_msg)

    active = st.session_state.active_tab

    # ── PAGE: DASHBOARD ──
    if active == "dashboard":
        role_badge = "Admin" if user["role"] == "admin" else "Executive"

        # Sync health indicator
        from datetime import datetime, timezone
        data_mtime = LOCAL_DATA_COPY.stat().st_mtime if LOCAL_DATA_COPY.exists() else 0
        last_sync_dt = datetime.fromtimestamp(data_mtime) if data_mtime else None
        now = datetime.now()
        if last_sync_dt:
            sync_ago = (now - last_sync_dt).total_seconds()
            sync_ago_min = int(sync_ago // 60)
            sync_time_str = last_sync_dt.strftime("%d %b %Y, %H:%M")
            if sync_ago_min < 15:
                sync_color = "#10b981"
                sync_icon = "🟢"
                sync_label = f"Synced {sync_ago_min}m ago"
            elif sync_ago_min < 60:
                sync_color = "#f59e0b"
                sync_icon = "🟡"
                sync_label = f"Synced {sync_ago_min}m ago"
            else:
                sync_color = "#ef4444"
                sync_icon = "🔴"
                hours = sync_ago_min // 60
                sync_label = f"Stale: {hours}h {sync_ago_min % 60}m ago"
        else:
            sync_color = "#ef4444"
            sync_icon = "🔴"
            sync_label = "No data file"
            sync_time_str = "N/A"

        # Show red warning banner if stale > 15 min
        if last_sync_dt and sync_ago > 900:
            st.markdown(f"""
            <div style="background:#7f1d1d;border:1px solid #ef4444;border-radius:8px;padding:10px 16px;margin-bottom:12px;display:flex;align-items:center;gap:10px">
              <span style="font-size:1.2rem">⚠️</span>
              <div>
                <div style="color:#fca5a5;font-size:.8rem;font-weight:700">Data may be outdated</div>
                <div style="color:#fecaca;font-size:.7rem">Last sync: {sync_time_str} ({sync_ago_min} minutes ago). Check if sync worker is running.</div>
              </div>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="rcc-header">
          <div>
            <div class="rcc-logo">Resolution <span>Command</span> Center</div>
            <div class="rcc-tagline">Resolution Management Dashboard · {len(df):,} active accounts</div>
          </div>
          <div style="display:flex;align-items:center;gap:12px">
            <div style="text-align:right">
              <div style="font-size:.6rem;color:var(--muted);font-weight:700;text-transform:uppercase">Last Sync</div>
              <div style="font-size:.7rem;color:{sync_color};font-weight:700">{sync_icon} {sync_label}</div>
            </div>
            <div class="rcc-badge">{role_badge} · {user["username"].title()}</div>
          </div>
        </div>""", unsafe_allow_html=True)
        hero_dashboard_cards(
            bkt1_stats, bkt2_stats, receipt_ach,
            paid_count, unpaid_count, total_cases,
            df["Paid Amount"].sum()
        )
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        section("📊 Bucket Details (POS Amount)")
        bsum = bucket_summary_df(df)
        display_table_with_res_color(bsum, height=300)

        if user["role"] == "admin":
            section("Executive Ranking")
            erank = executive_ranking_df(df_full)
            display_table(erank, height=360)

            # ── Receipt Cut & POS by Bucket (Executive-wise) ──
            section("📊 Receipt Cut Analysis")

            from datetime import date
            sel_date = st.date_input("📅 Payment Date", value=date.today(), key="rc_date_filter")
            sel_date_str = sel_date.strftime("%d.%m.%y")  # Match Excel format dd.mm.yy
            display_date = sel_date.strftime("%d.%m.%Y")

            # Filter only PAID receipts with selected payment date
            paid_df = df_full[
                (df_full["RECEIPT CUT"] == "PAID") &
                (df_full["Payment Date"].astype(str).str.strip() == sel_date_str)
            ].copy()
            total_cases = len(df_full)
            paid_count = len(paid_df)

            # Movement %
            receipt_cut_mov = (paid_count / total_cases * 100) if total_cases else 0
            bkt1_total = df_full[df_full["BUCKET"] == 1]["POS"].sum()
            bkt1_resolved = df_full[(df_full["BUCKET"] == 1) & (df_full["POS STATUS"].isin(["STABLE","RB"]))]["POS"].sum()
            bkt1_mov = (bkt1_resolved / bkt1_total * 100) if bkt1_total else 0
            bkt2_total = df_full[df_full["BUCKET"] == 2]["POS"].sum()
            bkt2_resolved = df_full[(df_full["BUCKET"] == 2) & (df_full["POS STATUS"].isin(["STABLE","RB"]))]["POS"].sum()
            bkt2_mov = (bkt2_resolved / bkt2_total * 100) if bkt2_total else 0

            # Build tables - ONLY executives who have PAID receipts
            if not paid_df.empty:
                rc_pivot = paid_df.pivot_table(index="TEAM", columns="BUCKET", values="LOAN NO", aggfunc="count", fill_value=0)
                bkt_cols = sorted(rc_pivot.columns.tolist())
                rc_pivot = rc_pivot[bkt_cols]
                rc_pivot["TOTAL"] = rc_pivot.sum(axis=1)
                rc_pivot = rc_pivot.reset_index().rename(columns={"TEAM": "TEAM"})
                rc_pivot = rc_pivot.sort_values("TEAM").reset_index(drop=True)
                t_row = {"TEAM": "TOTAL"}
                for col in rc_pivot.columns:
                    if col != "TEAM":
                        t_row[col] = int(rc_pivot[col].sum())
                rc_pivot = pd.concat([rc_pivot, pd.DataFrame([t_row])], ignore_index=True)

                pos_pivot = paid_df.pivot_table(index="TEAM", columns="BUCKET", values="POS", aggfunc="sum", fill_value=0)
                pos_bkt_cols = sorted(pos_pivot.columns.tolist())
                pos_pivot = pos_pivot[pos_bkt_cols]
                pos_pivot = pos_pivot.reset_index().rename(columns={"TEAM": "EXECUTIVE"})
                pos_pivot = pos_pivot.sort_values("EXECUTIVE").reset_index(drop=True)
                gt_row = {"EXECUTIVE": "Grand Total"}
                for col in pos_pivot.columns:
                    if col != "EXECUTIVE":
                        gt_row[col] = pos_pivot[col].sum()
                pos_pivot = pd.concat([pos_pivot, pd.DataFrame([gt_row])], ignore_index=True)

                # Receipt Cut table rows - compact
                rc_headers = "".join([f'<th style="padding:5px 8px;text-align:center;font-size:.65rem;font-weight:700;color:#64748b;border-bottom:2px solid #2d3b52">BKT {int(c)}</th>' for c in bkt_cols])
                rc_rows = ""
                for _, row in rc_pivot.iterrows():
                    en = row["TEAM"]
                    is_t = en == "TOTAL"
                    bg = "background:#0f1b2e;" if is_t else ""
                    fw = "font-weight:800;" if is_t else ""
                    cells = f'<td style="padding:5px 8px;font-size:.72rem;color:#e8edf5;{fw}{bg}white-space:nowrap">{en}</td>'
                    for c in bkt_cols:
                        v = int(row[c]) if row[c] > 0 else ""
                        cells += f'<td style="padding:5px 8px;text-align:center;font-size:.75rem;color:#e8edf5;{fw}{bg}font-family:var(--font-mono)">{v}</td>'
                    tv = int(row["TOTAL"])
                    cells += f'<td style="padding:5px 8px;text-align:center;font-size:.75rem;color:#4ade80;{fw}{bg}font-family:var(--font-mono)">{tv}</td>'
                    rc_rows += f'<tr style="border-bottom:1px solid #1e2d45">{cells}</tr>'

                # POS table rows - compact
                pos_headers = "".join([f'<th style="padding:5px 8px;text-align:right;font-size:.65rem;font-weight:700;color:#64748b;border-bottom:2px solid #2d3b52">BKT {int(c)}</th>' for c in pos_bkt_cols])
                pos_rows = ""
                for _, row in pos_pivot.iterrows():
                    en = row["EXECUTIVE"]
                    is_t = en == "Grand Total"
                    bg = "background:#0f1b2e;" if is_t else ""
                    fw = "font-weight:800;" if is_t else ""
                    cells = f'<td style="padding:5px 8px;font-size:.72rem;color:#e8edf5;{fw}{bg}white-space:nowrap">{en}</td>'
                    for c in pos_bkt_cols:
                        v = row[c]
                        disp = f"{v:,.0f}" if v > 0 else ""
                        cells += f'<td style="padding:5px 8px;text-align:right;font-size:.72rem;color:#7dd3fc;{fw}{bg}font-family:var(--font-mono)">{disp}</td>'
                    pos_rows += f'<tr style="border-bottom:1px solid #1e2d45">{cells}</tr>'

                # Compact screenshot card
                st.markdown(f"""
                <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin:8px 0">
                  <!-- Header line -->
                  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
                    <div style="font-size:.7rem;color:var(--muted)">📅 <span style="color:#7dd3fc;font-weight:700">{display_date}</span> · Receipt Cut: <b style="color:#4ade80">PAID</b></div>
                    <div style="font-size:.55rem;color:var(--muted);font-weight:700;text-transform:uppercase;border:1px solid var(--border);padding:2px 8px;border-radius:4px">RCC</div>
                  </div>

                  <!-- Movement row -->
                  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:14px">
                    <div style="background:#064e3b;border-radius:6px;padding:8px;text-align:center">
                      <div style="color:#86efac;font-size:.5rem;font-weight:700;text-transform:uppercase">RC Movement</div>
                      <div style="color:#4ade80;font-size:1.2rem;font-weight:800;font-family:var(--font-mono)">{receipt_cut_mov:.2f}%</div>
                    </div>
                    <div style="background:#1e3a5f;border-radius:6px;padding:8px;text-align:center">
                      <div style="color:#93c5fd;font-size:.5rem;font-weight:700;text-transform:uppercase">BKT-1 Res</div>
                      <div style="color:#60a5fa;font-size:1.2rem;font-weight:800;font-family:var(--font-mono)">{bkt1_mov:.2f}%</div>
                    </div>
                    <div style="background:#3b1764;border-radius:6px;padding:8px;text-align:center">
                      <div style="color:#c4b5fd;font-size:.5rem;font-weight:700;text-transform:uppercase">BKT-2 Res</div>
                      <div style="color:#a78bfa;font-size:1.2rem;font-weight:800;font-family:var(--font-mono)">{bkt2_mov:.2f}%</div>
                    </div>
                  </div>

                  <!-- Receipt Cut Count -->
                  <div style="color:#64748b;font-size:.6rem;font-weight:700;text-transform:uppercase;margin-bottom:4px">Count of Receipt Cut</div>
                  <div style="overflow-x:auto;border-radius:6px;border:1px solid #1e2d45;margin-bottom:12px">
                    <table style="width:100%;border-collapse:collapse">
                      <thead><tr style="background:#0a1628">
                        <th style="padding:5px 8px;text-align:left;font-size:.6rem;font-weight:700;color:#64748b;border-bottom:2px solid #2d3b52">TEAM</th>
                        {rc_headers}
                        <th style="padding:5px 8px;text-align:center;font-size:.65rem;font-weight:700;color:#4ade80;border-bottom:2px solid #2d3b52">TOTAL</th>
                      </tr></thead>
                      <tbody>{rc_rows}</tbody>
                    </table>
                  </div>

                  <!-- Sum of POS -->
                  <div style="color:#64748b;font-size:.6rem;font-weight:700;text-transform:uppercase;margin-bottom:4px">Sum of POS</div>
                  <div style="overflow-x:auto;border-radius:6px;border:1px solid #1e2d45">
                    <table style="width:100%;border-collapse:collapse">
                      <thead><tr style="background:#0a1628">
                        <th style="padding:5px 8px;text-align:left;font-size:.6rem;font-weight:700;color:#64748b;border-bottom:2px solid #2d3b52">EXECUTIVE</th>
                        {pos_headers}
                      </tr></thead>
                      <tbody>{pos_rows}</tbody>
                    </table>
                  </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No PAID receipts found.")

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
            <div style="background:linear-gradient(135deg,#1e3a5f,#2563eb);border-radius:10px;padding:14px 20px;display:flex;align-items:center;gap:16px;margin-bottom:12px">
              <span style="font-size:1.5rem">📋</span>
              <div>
                <div style="color:rgba(255,255,255,0.7);font-size:.65rem;font-weight:700;text-transform:uppercase">Total Pending Cases</div>
                <div style="color:#fff;font-size:1.9rem;font-weight:800;line-height:1.1">{total_pending}</div>
              </div>
              <div style="margin-left:auto;color:rgba(255,255,255,0.6);font-size:.8rem">Showing {showing}</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            if user["role"] == "admin":
                st.markdown(f'<div style="background:#1a2540;border:1px solid #1e3460;border-radius:8px;padding:8px 12px;font-size:.7rem;color:#7dd3fc;word-break:break-all;margin-bottom:6px">{share_url}</div>', unsafe_allow_html=True)
                if st.button("📋 Copy Link", use_container_width=True, key="copy_trails_link"):
                    st.code(share_url)

        # Card list
        if pending_df.empty:
            st.info("No pending trails found.")
        else:
            pending_df = pending_df.sort_values("AREA").reset_index(drop=True)
            is_admin = user["role"] == "admin"
            exec_th = '<th style="padding:10px 12px;text-align:left;font-size:.7rem;font-weight:700;color:#7a8ba8;text-transform:uppercase">Executive</th>' if is_admin else ""
            rows_html = ""
            for _, row in pending_df.iterrows():
                loan = str(row["LOAN NO"])
                name = str(row["CUSTOMER NAME"])
                area = str(row.get("AREA", "—"))
                team = str(row.get("TEAM", ""))
                exec_td = f'<td style="padding:9px 12px;font-size:.78rem;color:#7dd3fc">{team}</td>' if is_admin else ""
                rows_html += f'<tr style="border-bottom:1px solid #1a2540"><td style="padding:9px 12px;font-family:monospace;font-size:.82rem;font-weight:700;color:#f1f5f9">{loan}</td><td style="padding:9px 12px;font-size:.82rem;color:#f1f5f9">{name}</td><td style="padding:9px 12px;font-size:.78rem;vertical-align:middle"><span style="background:#1e3460;color:#7dd3fc;border-radius:4px;padding:3px 10px;font-size:.75rem;font-weight:700;letter-spacing:.02em">{area}</span></td>{exec_td}</tr>'
            st.markdown(f'<div style="overflow-x:auto;border-radius:10px;border:1px solid #1e3460;-webkit-overflow-scrolling:touch"><table style="width:100%;border-collapse:collapse;min-width:500px"><thead><tr style="background:#0a1628;border-bottom:2px solid #1e3460"><th style="padding:8px 10px;text-align:left;font-size:.68rem;font-weight:700;color:#7a8ba8;text-transform:uppercase;white-space:nowrap">Loan No</th><th style="padding:8px 10px;text-align:left;font-size:.68rem;font-weight:700;color:#7a8ba8;text-transform:uppercase;white-space:nowrap">Customer Name</th><th style="padding:8px 10px;text-align:left;font-size:.68rem;font-weight:700;color:#7a8ba8;text-transform:uppercase;white-space:nowrap">Area</th>{exec_th}</tr></thead><tbody>{rows_html}</tbody></table></div>', unsafe_allow_html=True)

    # ── PAGE: DRA & AGENCY ──
    elif active == "dra":
        section("🚨 DRA & Agency")
        tracker_df = df.copy()
        tracker_df["DRA CASE%"]    = tracker_df["DRA CASE%"]    * 100
        tracker_df["AGENCY CASE%"] = tracker_df["AGENCY CASE%"] * 100

        all_buckets = sorted(df["BUCKET"].dropna().unique().tolist())
        bkt_options = ["All"] + [f"BKT-{int(b)}" for b in all_buckets]
        bkt_filter  = st.radio("Bucket filter", bkt_options, horizontal=True)

        if bkt_filter != "All":
            bkt_num = int(bkt_filter.replace("BKT-",""))
            tracker_df = tracker_df[tracker_df["BUCKET"] == bkt_num]

        st.caption(f"Showing: {len(tracker_df):,} cases")
        tcols = ["LOAN NO","CUSTOMER NAME","TEAM","BUCKET","POS","DRA CASE%","AGENCY CASE%","POS STATUS"]
        display_table(tracker_df[tcols].sort_values("DRA CASE%", ascending=False), height=480)

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
