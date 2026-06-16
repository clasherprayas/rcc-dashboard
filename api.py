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
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

APP_DIR = Path(__file__).resolve().parent
DATA_FILE = APP_DIR / "RCC_DATA.xlsx"
SHEET_NAME = "MAIN"

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
app.mount("/mobile", StaticFiles(directory=str(APP_DIR / "mobile"), html=True), name="mobile")


def load_data():
    """Load and clean Excel data with caching — only re-reads when file changes."""
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
        res_pct = round((stable + rb) / total * 100, 2)
        rb_pct = round(rb / total * 100, 2)
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
async def trails(user: str = "", role: str = "executive"):
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
async def flowlist(user: str = "", bucket: int = 1, role: str = "executive"):
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
        })
    
    return {"total": len(result), "bucket": bucket, "cases": result}


@app.get("/api/search")
async def search_loan(q: str = "", user: str = "", role: str = "executive", bucket: int = 0):
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


# Serve PWA root — detect mobile vs desktop
@app.get("/")
async def root(request: Request):
    user_agent = request.headers.get("user-agent", "").lower()
    mobile_keywords = ["mobile", "android", "iphone", "ipad", "ipod", "webos", "opera mini", "opera mobi"]
    is_mobile = any(kw in user_agent for kw in mobile_keywords)
    
    if is_mobile:
        return FileResponse(str(APP_DIR / "mobile" / "index.html"))
    else:
        # Desktop — redirect to Streamlit
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="https://rccapp.xyz", status_code=302)


if __name__ == "__main__":
    # Pre-load data at startup so first request is instant
    print("⏳ Pre-loading Excel data...")
    load_data()
    port = int(os.environ.get("PORT", 8000))
    print(f"\n🚀 RCC Mobile PWA running!")
    print(f"📱 Open on phone: http://<your-pc-ip>:{port}")
    print(f"💻 Local: http://localhost:{port}\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
