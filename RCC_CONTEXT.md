# RECOVERY COMMAND CENTER — FULL CONTEXT

## RUN
```
cd C:\Users\Admin\Desktop\RCC
python -m streamlit run app.py
```
URL: http://localhost:8501

## FOLDER STRUCTURE
```
C:\Users\Admin\Desktop\RCC\
├── app.py
├── RCC_DATA.xlsx       ← auto-copied from network
├── requirements.txt
└── .streamlit\
    └── config.toml
```

## DATA FLOW
```
\\Hdfc1\d\HDFC\ALLOCATION FILE\TW FILES\JUNE 26\TW ALLOCATION JUNE 26.xlsx
        ↓ auto-copy on load
RCC_DATA.xlsx → Dashboard (auto-refresh every 30s)
```

## STACK
- Python 3.14, Streamlit, Pandas, openpyxl, streamlit-autorefresh

## LOGIN
| Username | Password | Role |
|---|---|---|
| ADMIN | Admin@123 | admin — full dashboard |
| AKSHAY KARALE | akshay@123 | executive |
| AMIT GADE | amit@123 | executive |
| AMOL DHUMAL | amol@123 | executive |
| ANWAR SHAIKH | anwar@123 | executive |
| HARIDAS DIVATE | haridas@123 | executive |
| HEMANT WALUNJ | hemant@123 | executive |
| KIRAN KHAIRNAR | kiran@123 | executive |
| NITIN KADAM | nitin@123 | executive |
| PARMESHWAR KOTULE | parmeshwar@123 | executive |
| SACHIN INGALE | sachini@123 | executive |
| SACHIN KHAPRE | sachink@123 | executive |
| SAGAR DONGRE | sagar@123 | executive |
| SANDEEP KHAIRNAR | sandeep@123 | executive |
| SUNNY SHINDE | sunny@123 | executive |
| SWAPNIL JADHAV | swapnil@123 | executive |
| TANAJI SURVASE | tanaji@123 | executive |
| UDAY SOHANE | uday@123 | executive |
| VIKRAM GAIKWAD | vikram@123 | executive |

Executive login → sirf apna TEAM data dikhta hai.

## KEY COLUMNS
| Column | Notes |
|---|---|
| LOAN NO, CUSTOMER NAME, TEAM, BUCKET, POS STATUS | Core fields |
| POS | Principal outstanding amount |
| POS STATUS | FLOW / STABLE / RB |
| TRAILS PENDING | 0 = pending, >0 = done |
| RECEIPT CUT | "PAID" / "UNPAID" text |
| DRA CASE%, AGENCY CASE% | Stored as decimal (0.39 = 39%) |
| STAB AMOUNTWITH DPIC, RB AMOUNTWITH DPIC | Action center amounts |

## BUSINESS LOGIC
- Resolution % = (Stable POS + RB POS) / Total POS × 100 — POS AMOUNT based, NOT count
- Receipt Cut Achievement = Paid receipts / Total cases × 100
- Pending Trails = TRAILS PENDING == 0
- DRA/Agency % display = value × 100

## TABS
1. Dashboard — hero cards (BKT-1, BKT-2, Receipt Cut) + Bucket Summary table + Executive Ranking
2. Action Center — loans where Total Need > 0, sorted descending
3. Pending Trails — TRAILS PENDING == 0, filter by executive (admin), share link button
4. DRA & Agency — all buckets 1-6, filter by bucket
5. Executive Tracker — per executive KPIs + case details
6. Loan Search — search by loan no or customer name

## PUBLIC TRAILS VIEW
URL: http://localhost:8501/?view=trails
No login needed. Team selects their name, sees their pending trails.

## DASHBOARD HERO CARDS
- 3 cards: BKT-1 Resolution | BKT-2 Resolution | Receipt Cut Achievement
- Each has: SVG donut ring, Resolution %, counts (Flow/Stable/RB), POS amounts, Total POS
- CSS class: hero-wrap (grid 3 columns)
- Donut SVG renders via unsafe_allow_html — gradient IDs: g_b1, g_b2, g_rc

## KNOWN ISSUES (fix these)
1. Mobile layout — hero cards too large on mobile, need 2-column compact grid
2. Donut SVG — not rendering properly, shows blob instead of ring
3. Table CSS — white background table with dark navy header row

## BUCKET SUMMARY TABLE
- Columns: Bucket | Flow POS | Stable POS | RB POS | Grand Total | Stable % | RB % | Resolution %
- TOTAL row at bottom — dark navy background
- Resolution % color coded: Green ≥10%, Amber ≥5%, Red <5%
- Numbers in Indian format: K / L / Cr

## ROADMAP
| Phase | Status |
|---|---|
| KPI + Ranking + Search + Action Center | ✅ Done |
| Pending Trails | ✅ Done |
| DRA & Agency | ✅ Done |
| Login (Admin + Executive) | ✅ Done |
| Tab navigation + Auto-refresh | ✅ Done |
| Hero dashboard cards | ✅ Done |
| Mobile responsive | 🔧 Partial |
| Donut ring fix | ❌ Pending |
| PTP Dashboard | ❌ Pending |
| Google Sheets + Streamlit Cloud | ❌ Pending |

## config.toml (.streamlit folder)
```toml
[theme]
base = "dark"
backgroundColor = "#0b1120"
secondaryBackgroundColor = "#1a2540"
textColor = "#f1f5f9"
font = "sans serif"
primaryColor = "#3b82f6"
```

## requirements.txt
```
streamlit
pandas
openpyxl
streamlit-autorefresh
```
