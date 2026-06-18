"""
RCC Mobile API — FastAPI backend for PWA mobile app.
Reads same RCC_DATA.xlsx and serves JSON endpoints.
Run: python api.py
"""

import math
import os
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

APP_DIR = Path(__file__).resolve().parent
DATA_FILE = APP_DIR / "RCC_DATA.xlsx"
SHEET_NAME = "MAIN"

# ── CLOUD MODE — download from OneDrive if ONEDRIVE_SHARE_URL is set ──
CLOUD_MODE = os.environ.get("RCC_CLOUD", "0") == "1"
ONEDRIVE_SHARE_URL = os.environ.get("ONEDRIVE_SHARE_URL", "")

def _sync_from_onedrive():
    """Download RCC_DATA.xlsx from OneDrive share link (cloud mode)."""
    import requests
    if not ONEDRIVE_SHARE_URL:
        return False
    try:
        share_url = ONEDRIVE_SHARE_URL.strip()
        
        # Append &download=1 to force direct download from OneDrive
        separator = "&" if "?" in share_url else "?"
        download_url = f"{share_url}{separator}download=1"
        
        print(f"☁️ Attempting OneDrive download...")
        resp = requests.get(download_url, timeout=60, allow_redirects=True)
        
        # Verify it's actual Excel content (not HTML error page)
        if resp.status_code == 200 and len(resp.content) > 1000:
            if b'<!DOCTYPE' in resp.content[:200] or b'<html' in resp.content[:200]:
                print(f"⚠️ Got HTML instead of Excel. Download failed.")
                return False
            
            DATA_FILE.write_bytes(resp.content)
            print(f"☁️ Fresh data downloaded from OneDrive ({len(resp.content)} bytes)")
            return True
        else:
            print(f"⚠️ OneDrive download failed (HTTP {resp.status_code})")
            return False
    except Exception as e:
        print(f"⚠️ OneDrive sync error: {e}")
        return False

# ── CACHING — Excel sirf tab reload hoga jab file change ho ──
_cache = {"df": None, "mtime": 0}

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

app = FastAPI(title="RCC Mobile API")

@app.on_event("startup")
async def startup_preload():
    """Pre-load Excel data when server starts (for Render/cloud)."""
    if CLOUD_MODE and ONEDRIVE_SHARE_URL:
        print("☁️ Cloud mode — downloading from OneDrive...")
        _sync_from_onedrive()
    load_data()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve PWA static files (no-cache during dev)
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if "/mobile/" in str(request.url):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response

app.add_middleware(NoCacheMiddleware)

# ── VISITOR TRACKING ──
from datetime import datetime as _dt
_visitor_logs = []  # In-memory log (max 500 entries)

@app.post("/api/track")
async def track_visit(request: Request):
    """Log public page visits — called from public pages."""
    body = await request.json()
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    if "," in ip:
        ip = ip.split(",")[0].strip()
    ua = request.headers.get("user-agent", "")
    device = "Mobile" if any(k in ua.lower() for k in ["android", "iphone", "mobile"]) else "Desktop"
    entry = {
        "time": _dt.now().strftime("%d %b, %I:%M %p"),
        "timestamp": _dt.now().isoformat(),
        "page": body.get("page", "--"),
        "executive": body.get("executive", "--"),
        "device": device,
        "ip": ip[:20],
    }
    _visitor_logs.insert(0, entry)
    if len(_visitor_logs) > 500:
        _visitor_logs.pop()
    return {"ok": True}

@app.get("/api/visitor-logs")
async def get_visitor_logs():
    """Admin endpoint — returns recent visitor logs."""
    return {"logs": _visitor_logs[:100]}

# ── PUBLIC LINKS ACCESS CONTROL ──
_public_access = {"enabled": True, "password_required": False, "password": "rcc123", "show_projection": False}
_search_access = {"enabled": False, "password": "rcc@admin"}

@app.get("/api/public-access")
async def get_public_access():
    return {
        "enabled": _public_access["enabled"],
        "password_required": _public_access["password_required"],
        "password": _public_access["password"],
        "show_projection": _public_access["show_projection"],
        "search_enabled": _search_access["enabled"],
        "search_password": _search_access["password"]
    }

@app.post("/api/public-access")
async def set_public_access(request: Request):
    body = await request.json()
    if "enabled" in body:
        _public_access["enabled"] = body["enabled"]
    if "password_required" in body:
        _public_access["password_required"] = body["password_required"]
    if "password" in body:
        _public_access["password"] = body["password"]
    if "show_projection" in body:
        _public_access["show_projection"] = body["show_projection"]
    if "search_enabled" in body:
        _search_access["enabled"] = body["search_enabled"]
    if "search_password" in body:
        _search_access["password"] = body["search_password"]
    return {
        "enabled": _public_access["enabled"],
        "password_required": _public_access["password_required"],
        "password": _public_access["password"],
        "show_projection": _public_access["show_projection"],
        "search_enabled": _search_access["enabled"],
        "search_password": _search_access["password"]
    }

@app.post("/api/public-verify")
async def verify_public_password(request: Request):
    body = await request.json()
    entered = body.get("password", "")
    verify_type = body.get("type", "general")
    if verify_type == "search":
        if entered == _search_access["password"]:
            return {"verified": True}
        return {"verified": False}
    if not _public_access["password_required"]:
        return {"verified": True}
    if entered == _public_access["password"]:
        return {"verified": True}
    return {"verified": False}

# ── PUBLIC PAGES (no login required) — must be before StaticFiles mount ──
from fastapi.responses import HTMLResponse

@app.get("/public/trails")
async def public_trails_page():
    if not _public_access["enabled"]:
        return HTMLResponse(content="""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Access Disabled</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Inter',sans-serif;background:#f0f4f8;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:20px}.card{background:white;border-radius:16px;padding:40px;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,0.08);max-width:360px}.icon{font-size:48px;margin-bottom:16px}.title{font-size:18px;font-weight:700;color:#1e293b;margin-bottom:8px}.msg{font-size:14px;color:#64748b}</style></head><body><div class="card"><div class="icon">🔒</div><div class="title">Access Disabled</div><div class="msg">This link has been disabled by the admin. Contact your administrator for access.</div></div></body></html>""", status_code=403)
    return FileResponse(str(APP_DIR / "mobile" / "public_trails.html"))

@app.get("/public/flowlist")
async def public_flowlist_page():
    if not _public_access["enabled"]:
        return HTMLResponse(content="""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Access Disabled</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Inter',sans-serif;background:#f0f4f8;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:20px}.card{background:white;border-radius:16px;padding:40px;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,0.08);max-width:360px}.icon{font-size:48px;margin-bottom:16px}.title{font-size:18px;font-weight:700;color:#1e293b;margin-bottom:8px}.msg{font-size:14px;color:#64748b}</style></head><body><div class="card"><div class="icon">🔒</div><div class="title">Access Disabled</div><div class="msg">This link has been disabled by the admin. Contact your administrator for access.</div></div></body></html>""", status_code=403)
    return FileResponse(str(APP_DIR / "mobile" / "public_flowlist.html"))

@app.get("/public/search")
async def public_search_page():
    if not _search_access["enabled"]:
        return HTMLResponse(content="""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Access Disabled</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Inter',sans-serif;background:#f0f4f8;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:20px}.card{background:white;border-radius:16px;padding:40px;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,0.08);max-width:360px}.icon{font-size:48px;margin-bottom:16px}.title{font-size:18px;font-weight:700;color:#1e293b;margin-bottom:8px}.msg{font-size:14px;color:#64748b}</style></head><body><div class="card"><div class="icon">🔒</div><div class="title">Access Disabled</div><div class="msg">Action Center is currently disabled. Contact your administrator.</div></div></body></html>""", status_code=403)
    return FileResponse(str(APP_DIR / "mobile" / "public_search.html"))

# ── FORCE SYNC API (admin can trigger manual refresh) ──
@app.post("/api/force-sync")
async def force_sync():
    """Force re-download from OneDrive and reload data."""
    if CLOUD_MODE and ONEDRIVE_SHARE_URL:
        success = _sync_from_onedrive()
        if success:
            _cache["df"] = None  # Force reload
            _cache["mtime"] = 0
            load_data()
            return {"status": "ok", "message": "Data synced from OneDrive"}
        return {"status": "error", "message": "OneDrive download failed"}
    else:
        _cache["df"] = None
        _cache["mtime"] = 0
        load_data()
        return {"status": "ok", "message": "Data reloaded from file"}

app.mount("/mobile", StaticFiles(directory=str(APP_DIR / "mobile"), html=True), name="mobile")


import time as _time
_last_onedrive_check = {"t": 0}

def load_data():
    """Load and clean Excel data with caching — only re-reads when file changes."""
    # In cloud mode, check OneDrive every 5 minutes for fresh data
    if CLOUD_MODE and ONEDRIVE_SHARE_URL:
        now = _time.time()
        if now - _last_onedrive_check["t"] > 120:  # 2 min
            _last_onedrive_check["t"] = now
            _sync_from_onedrive()

    if not DATA_FILE.exists():
        return None
    
    # Check file modification time
    current_mtime = os.path.getmtime(DATA_FILE)
    if _cache["df"] is not None and _cache["mtime"] == current_mtime:
        return _cache["df"]
    
    print(f"📂 Loading Excel (file changed)...")
    df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME, engine="openpyxl")
    df.columns = [str(col).strip() for col in df.columns]
    
    num_cols = ["BUCKET", "POS", "EMI", "TOTAL EMI DUE", "DPIC CHARGES",
                "STAB AMOUNTWITH DPIC", "RB AMOUNTWITH DPIC", "Paid Amount",
                "TRAILS PENDING", "DRA CASE%", "AGENCY CASE%", "DPD"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", "").str.replace("₹", "").str.strip(),
                errors="coerce"
            ).fillna(0)
    
    if "LOAN NO" in df.columns:
        df["LOAN NO"] = df["LOAN NO"].astype(str).str.strip()
    if "CUSTOMER NAME" in df.columns:
        df["CUSTOMER NAME"] = df["CUSTOMER NAME"].astype(str).str.strip()
    if "TEAM" in df.columns:
        df["TEAM"] = df["TEAM"].astype(str).str.strip().str.upper()
    if "POS STATUS" in df.columns:
        df["POS STATUS"] = df["POS STATUS"].astype(str).str.strip().str.upper()
    if "BUCKET" in df.columns:
        df["BUCKET"] = pd.to_numeric(
            df["BUCKET"].astype(str).str.extract(r"(\d+)", expand=False),
            errors="coerce"
        ).fillna(0).astype(int)
    if "RECEIPT CUT" in df.columns:
        df["RECEIPT CUT"] = df["RECEIPT CUT"].astype(str).str.strip().str.upper()
    if "AREA" in df.columns:
        df["AREA"] = df["AREA"].astype(str).str.strip()
    
    # Store in cache
    _cache["df"] = df
    _cache["mtime"] = current_mtime
    print(f"✅ Cached! {len(df)} rows loaded.")
    
    return df


def resolution_stats(df):
    """Calculate resolution stats from dataframe."""
    pos = df["POS"]
    status = df["POS STATUS"]
    flow_c = int((status == "FLOW").sum())
    stable_c = int((status == "STABLE").sum())
    rb_c = int((status == "RB").sum())
    flow_p = float(pos[status == "FLOW"].sum())
    stable_p = float(pos[status == "STABLE"].sum())
    rb_p = float(pos[status == "RB"].sum())
    total_p = flow_p + stable_p + rb_p
    res = ((stable_p + rb_p) / total_p * 100) if total_p else 0
    return {
        "flow": flow_c, "stable": stable_c, "rb": rb_c,
        "flow_pos": flow_p, "stable_pos": stable_p, "rb_pos": rb_p,
        "total_pos": total_p, "resolution_pct": round(res, 2)
    }


def calc_payout_slab(resolution_pct, rb_pct, bucket):
    """Calculate payout slab."""
    if bucket not in (1, 2):
        return 8, True
    
    PAYOUT_CONFIG = {
        1: [(90, 999, 15, 25), (88, 89.99, 12, 20), (85, 87.99, 10, 15), (0, 84.99, 8, 15)],
        2: [(70, 999, 15, 25), (65, 69.99, 12, 20), (60, 64.99, 10, 15), (0, 59.99, 8, 15)],
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
        payout = max(8, payout - 2)
    
    return payout, rb_achieved


# ── API ENDPOINTS ──

@app.post("/api/login")
async def login(request: Request):
    body = await request.json()
    username = body.get("username", "").strip().upper()
    password = body.get("password", "")
    
    rec = CREDENTIALS.get(username)
    if not rec or rec["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {"username": username, "role": rec["role"]}


@app.get("/api/dashboard")
async def dashboard(user: str = "", role: str = "executive"):
    df = load_data()
    if df is None:
        raise HTTPException(status_code=500, detail="Data file not found")
    
    username = user.strip().upper()
    
    # Filter by user if executive
    if role != "admin" and username:
        exec_df = df[df["TEAM"] == username].copy()
    else:
        exec_df = df.copy()
    
    total_cases = len(exec_df)
    if total_cases == 0:
        return {"total_cases": 0, "error": "No data found"}
    
    # Overall stats
    paid_count = int((exec_df["RECEIPT CUT"] == "PAID").sum())
    unpaid_count = total_cases - paid_count
    rc_pct = round(paid_count / total_cases * 100, 2) if total_cases else 0
    total_collection = float(exec_df["Paid Amount"].sum())
    
    # Bucket stats
    def bkt_stats(data, bkt):
        g = data[data["BUCKET"] == bkt]
        total = len(g)
        if total == 0:
            return {"total": 0, "flow": 0, "stable": 0, "rb": 0,
                    "res_pct": 0, "rb_pct": 0, "collection": 0, "slab": 8, "payout": 0}
        flow = int((g["POS STATUS"] == "FLOW").sum())
        stable = int((g["POS STATUS"] == "STABLE").sum())
        rb = int((g["POS STATUS"] == "RB").sum())
        
        # Calculate resolution & RB% using POS amounts (not case counts)
        total_pos = float(g["POS"].sum())
        stable_pos = float(g[g["POS STATUS"] == "STABLE"]["POS"].sum())
        rb_pos = float(g[g["POS STATUS"] == "RB"]["POS"].sum())
        
        if total_pos > 0:
            res_pct = round((stable_pos + rb_pos) / total_pos * 100, 2)
            rb_pct = round(rb_pos / total_pos * 100, 2)
        else:
            res_pct = 0
            rb_pct = 0
        
        collection = float(g["Paid Amount"].sum())
        slab, rb_ok = calc_payout_slab(res_pct, rb_pct, bkt)
        payout = collection * slab / 100
        return {"total": total, "flow": flow, "stable": stable, "rb": rb,
                "res_pct": res_pct, "rb_pct": rb_pct, "collection": collection,
                "slab": slab, "payout": round(payout, 2), "rb_ok": rb_ok}
    
    b1 = bkt_stats(exec_df, 1)
    b2 = bkt_stats(exec_df, 2)
    
    # BKT 3-6
    other_collection = float(exec_df[~exec_df["BUCKET"].isin([1, 2])]["Paid Amount"].sum())
    other_payout = other_collection * 8 / 100
    
    total_payout = b1["payout"] + b2["payout"] + other_payout
    
    # Slab projections
    slab_10 = total_collection * 0.10
    slab_12 = total_collection * 0.12
    slab_15 = total_collection * 0.15
    
    return {
        "total_cases": total_cases,
        "paid": paid_count,
        "unpaid": unpaid_count,
        "receipt_pct": rc_pct,
        "total_collection": round(total_collection, 2),
        "total_payout": round(total_payout, 2),
        "bkt1": b1,
        "bkt2": b2,
        "other_collection": round(other_collection, 2),
        "other_payout": round(other_payout, 2),
        "slab_10": round(slab_10, 2),
        "slab_12": round(slab_12, 2),
        "slab_15": round(slab_15, 2),
    }


@app.get("/api/trails")
async def trails(user: str = "", role: str = "executive", auth: str = ""):
    # Block if public access is disabled and no auth token
    if not _public_access["enabled"] and auth != "rcc-admin-token":
        raise HTTPException(status_code=403, detail="Access disabled")
    df = load_data()
    if df is None:
        raise HTTPException(status_code=500, detail="Data file not found")
    
    username = user.strip().upper()
    
    # Admin sees all pending trails, executive sees only their own
    if role == "admin":
        pending = df[df["TRAILS PENDING"] == 0]
    else:
        pending = df[(df["TEAM"] == username) & (df["TRAILS PENDING"] == 0)]
    
    result = []
    for _, row in pending.iterrows():
        result.append({
            "loan_no": str(row["LOAN NO"]),
            "customer_name": str(row["CUSTOMER NAME"]),
            "team": str(row["TEAM"]),
            "area": str(row.get("AREA", "—")),
        })
    
    return {"total": len(result), "trails": result}


@app.get("/api/flowlist")
async def flowlist(user: str = "", bucket: int = 1, role: str = "executive", auth: str = ""):
    # Block if public access is disabled and no auth token
    if not _public_access["enabled"] and auth != "rcc-admin-token":
        raise HTTPException(status_code=403, detail="Access disabled")
    df = load_data()
    if df is None:
        raise HTTPException(status_code=500, detail="Data file not found")
    
    username = user.strip().upper()
    
    # Admin sees all flow cases, executive sees only their own
    if role == "admin":
        flow_df = df[(df["POS STATUS"] == "FLOW") & (df["BUCKET"] == bucket)]
    else:
        flow_df = df[(df["TEAM"] == username) & (df["POS STATUS"] == "FLOW") & (df["BUCKET"] == bucket)]
    
    flow_df = flow_df.sort_values("POS", ascending=False)
    
    result = []
    for _, row in flow_df.iterrows():
        result.append({
            "customer_name": str(row["CUSTOMER NAME"]),
            "team": str(row["TEAM"]),
            "pos": float(row["POS"]),
            "dra_pct": round(float(row["DRA CASE%"]) * 100, 1),
            "mobile": str(row.get("MOBILE", "")),
            "area": str(row.get("AREA", "")),
            "projection": str(row.get("PROJECTION", "")),
        })
    
    return {"total": len(result), "bucket": bucket, "cases": result}


@app.get("/api/search")
async def search_loan(q: str = "", user: str = "", role: str = "executive", bucket: int = 0, status: str = ""):
    df = load_data()
    if df is None:
        raise HTTPException(status_code=500, detail="Data file not found")
    
    username = user.strip().upper()
    
    if role != "admin" and username:
        search_df = df[df["TEAM"] == username]
    else:
        search_df = df
    
    # Bucket filter
    if bucket > 0:
        search_df = search_df[search_df["BUCKET"] == bucket]
    
    # POS Status filter (FLOW / STABLE / RB)
    if status and status.upper() in ("FLOW", "STABLE", "RB"):
        search_df = search_df[search_df["POS STATUS"] == status.upper()]
    
    # If no query, return all cases sorted by STAB amount
    if not q.strip():
        results = search_df.sort_values("STAB AMOUNTWITH DPIC", ascending=False).head(50)
    else:
        query = q.strip().upper()
        mask = (
            search_df["LOAN NO"].str.startswith(query, na=False) |
            search_df["CUSTOMER NAME"].str.upper().str.contains(query, na=False)
        )
        results = search_df[mask].sort_values("STAB AMOUNTWITH DPIC", ascending=False).head(50)
    
    items = []
    for _, row in results.iterrows():
        items.append({
            "loan_no": str(row["LOAN NO"]),
            "customer_name": str(row["CUSTOMER NAME"]),
            "team": str(row["TEAM"]),
            "bucket": int(row["BUCKET"]),
            "pos": float(row["POS"]),
            "pos_status": str(row["POS STATUS"]),
            "emi": float(row["EMI"]),
            "emi_due": float(row["TOTAL EMI DUE"]),
            "stab_amount": float(row["STAB AMOUNTWITH DPIC"]),
            "rb_amount": float(row["RB AMOUNTWITH DPIC"]),
            "dpic": float(row["DPIC CHARGES"]),
            "receipt_cut": str(row["RECEIPT CUT"]),
            "area": str(row.get("AREA", "")),
            "mobile": str(row.get("MOBILE", "")),
            "dra_pct": round(float(row["DRA CASE%"]) * 100, 1),
            "paid_amount": float(row["Paid Amount"]),
            "dpd": int(row.get("DPD", 0)),
            "trails_pending": int(row.get("TRAILS PENDING", 0)),
        })
    
    return {"results": items}


@app.get("/api/executives")
async def executives():
    df = load_data()
    if df is None:
        raise HTTPException(status_code=500, detail="Data file not found")
    
    teams = sorted(df["TEAM"].dropna().unique().tolist())
    return {"executives": teams}


@app.get("/api/projection")
async def projection(bucket: int = 1, user: str = ""):
    """BKT-wise projection pivot — TEAM × PROJECTION(FLOW/STABLE/RB) with Resolution%."""
    df = load_data()
    if df is None:
        raise HTTPException(status_code=500, detail="Data file not found")
    
    bkt_df = df[df["BUCKET"] == bucket]
    
    # If specific user requested, filter for that user only
    username = user.strip().upper()
    if username:
        user_df = bkt_df[bkt_df["TEAM"] == username]
        if user_df.empty:
            return {"bucket": bucket, "user": username, "resolution": 0, "stable_pct": 0, "rb_pct": 0, "current_res": 0, "teams": [], "grand_total": {}}
        # Projection (from PROJECTION column)
        proj_grp = user_df.groupby("PROJECTION")["POS"].sum()
        flow_val = float(proj_grp.get("FLOW", 0))
        stable_val = float(proj_grp.get("STABLE", 0))
        rb_val = float(proj_grp.get("RB", 0))
        total_val = flow_val + stable_val + rb_val
        s_pct = round(stable_val / total_val * 100, 2) if total_val else 0
        r_pct = round(rb_val / total_val * 100, 2) if total_val else 0
        res = round(s_pct + r_pct, 2)
        # Current Resolution (from POS STATUS column — actual real-time)
        cur_grp = user_df.groupby("POS STATUS")["POS"].sum()
        cur_stable = float(cur_grp.get("STABLE", 0))
        cur_rb = float(cur_grp.get("RB", 0))
        cur_total = float(cur_grp.sum())
        cur_res = round((cur_stable + cur_rb) / cur_total * 100, 2) if cur_total else 0
        return {"bucket": bucket, "user": username, "resolution": res, "stable_pct": s_pct, "rb_pct": r_pct,
                "current_res": cur_res,
                "flow": round(flow_val, 2), "stable": round(stable_val, 2), "rb": round(rb_val, 2), "grand_total": round(total_val, 2)}
    
    if bkt_df.empty:
        return {"bucket": bucket, "teams": [], "grand_total": {}}
    
    # Group by TEAM and PROJECTION column (FLOW/STABLE/RB)
    pivot = bkt_df.groupby(["TEAM", "PROJECTION"])["POS"].sum().unstack(fill_value=0)
    
    # Ensure all columns exist
    for col in ["FLOW", "STABLE", "RB"]:
        if col not in pivot.columns:
            pivot[col] = 0.0
    
    pivot["grand_total"] = pivot["FLOW"] + pivot["STABLE"] + pivot["RB"]
    pivot["stable_pct"] = (pivot["STABLE"] / pivot["grand_total"] * 100).round(2).fillna(0)
    pivot["rb_pct"] = (pivot["RB"] / pivot["grand_total"] * 100).round(2).fillna(0)
    pivot["resolution"] = (pivot["stable_pct"] + pivot["rb_pct"]).round(2)
    
    # Sort by resolution descending
    pivot = pivot.sort_values("resolution", ascending=False)
    
    teams = []
    for team_name, row in pivot.iterrows():
        teams.append({
            "team": str(team_name),
            "flow": round(float(row["FLOW"]), 2),
            "stable": round(float(row["STABLE"]), 2),
            "rb": round(float(row["RB"]), 2),
            "grand_total": round(float(row["grand_total"]), 2),
            "stable_pct": float(row["stable_pct"]),
            "rb_pct": float(row["rb_pct"]),
            "resolution": float(row["resolution"]),
        })
    
    # Grand total row
    total_flow = pivot["FLOW"].sum()
    total_stable = pivot["STABLE"].sum()
    total_rb = pivot["RB"].sum()
    total_all = total_flow + total_stable + total_rb
    grand = {
        "flow": round(total_flow, 2),
        "stable": round(total_stable, 2),
        "rb": round(total_rb, 2),
        "grand_total": round(total_all, 2),
        "stable_pct": round(total_stable / total_all * 100, 2) if total_all else 0,
        "rb_pct": round(total_rb / total_all * 100, 2) if total_all else 0,
        "resolution": round((total_stable + total_rb) / total_all * 100, 2) if total_all else 0,
    }
    
    # Current Resolution from POS STATUS (actual real-time)
    cur_grp = bkt_df.groupby("POS STATUS")["POS"].sum()
    cur_stable = float(cur_grp.get("STABLE", 0))
    cur_rb = float(cur_grp.get("RB", 0))
    cur_total = float(cur_grp.sum())
    grand["current_res"] = round((cur_stable + cur_rb) / cur_total * 100, 2) if cur_total else 0
    
    return {"bucket": bucket, "teams": teams, "grand_total": grand}


@app.get("/api/ranking")
async def ranking():
    df = load_data()
    if df is None:
        raise HTTPException(status_code=500, detail="Data file not found")
    
    rows = []
    for team, grp in df.groupby("TEAM", dropna=False):
        if not pd.notna(team):
            continue
        total = len(grp)
        paid = int((grp["RECEIPT CUT"] == "PAID").sum())
        stats = resolution_stats(grp)
        collection = float(grp["Paid Amount"].sum())
        rows.append({
            "executive": team,
            "cases": total,
            "paid": paid,
            "unpaid": total - paid,
            "receipt_pct": round(paid / total * 100, 2) if total else 0,
            "resolution_pct": stats["resolution_pct"],
            "collection": round(collection, 2),
        })
    
    rows.sort(key=lambda x: x["resolution_pct"], reverse=True)
    for i, r in enumerate(rows):
        r["rank"] = i + 1
    
    return {"ranking": rows}


# Root → device-based redirect (with query params forwarding)
@app.get("/")
async def root(request: Request):
    user_agent = request.headers.get("user-agent", "").lower()
    query_string = str(request.query_params)
    suffix = f"?{query_string}" if query_string else ""

    mobile_keywords = [
        "android",
        "iphone",
        "ipad",
        "mobile"
    ]

    if any(keyword in user_agent for keyword in mobile_keywords):
        return RedirectResponse(
            url=f"/mobile/{suffix}",
            status_code=302
        )

    return RedirectResponse(
        url=f"https://dashboard.rccapp.xyz{suffix}",
        status_code=302
    )


if __name__ == "__main__":
    # Pre-load data at startup so first request is instant
    print("⏳ Pre-loading Excel data...")
    load_data()
    port = int(os.environ.get("PORT", 8000))
    print(f"\n🚀 RCC Mobile PWA running!")
    print(f"📱 Open on phone: http://<your-pc-ip>:{port}")
    print(f"💻 Local: http://localhost:{port}\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
