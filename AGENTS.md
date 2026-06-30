# RCC Dashboard — Codex Instructions

## RULES (follow strictly, no exceptions)

1. **Read only what's needed.** Never inspect backup files, `.backup`, `.bak`, or any unrelated file.
2. **No thinking loops.** If a task takes more than 2 tool calls to understand, ask the user instead of looping.
3. **Direct edits only.** Use `str_replace` with exact unique strings. Never use `sed` for multi-line replacements.
4. **Verify once.** After an edit, read only the changed lines to confirm. Do not re-read the entire file.
5. **No backups.** Do not create `.backup` files unless explicitly asked.
6. **No dead code.** If replacing a function, remove the entire old function before inserting the new one.
7. **One task at a time.** Complete the current task fully before moving to the next.

---

## PROJECT CONTEXT

**Run:** `python -m streamlit run app.py` → `http://localhost:8501`

**Stack:** Python, Streamlit, Pandas, openpyxl, streamlit-autorefresh

**Data source:** `RCC_DATA.xlsx` (auto-copied from network path on load)

---

## KEY BUSINESS LOGIC

- **Resolution %** = (Stable POS + RB POS) / Total POS × 100 — POS amount based, NOT count
- **Receipt Cut %** = Paid receipts / Total cases × 100
- **Pending Trails** = rows where `TRAILS PENDING == 0`
- **DRA/Agency %** stored as decimal in Excel (0.39 = 39%) — multiply × 100 for display
- **Indian number format:** use `format_indian()` helper already in app.py

---

## KEY COLUMNS

| Column | Notes |
|---|---|
| LOAN NO, CUSTOMER NAME, TEAM, BUCKET | Core fields |
| POS | Principal outstanding amount |
| POS STATUS | FLOW / STABLE / RB |
| TRAILS PENDING | 0 = pending, >0 = done |
| RECEIPT CUT | "PAID" / "UNPAID" |
| DRA CASE%, AGENCY CASE% | Decimal in Excel, ×100 for display |

---

## FILE STRUCTURE

```
C:\Users\Admin\Desktop\RCC\
├── app.py          ← single file, all logic here
├── RCC_DATA.xlsx
├── requirements.txt
└── .streamlit\config.toml
```

---

## COMMON MISTAKES TO AVOID

- Do NOT use `sed` for Python function replacements — indentation breaks
- Do NOT read backup files to understand current code — read `app.py` directly
- Do NOT add imports that are already at the top of app.py
- Do NOT change login logic or user roles unless explicitly asked
- Do NOT modify `format_indian()`, `resolution_stats()`, or `sync_source_excel()` unless the task specifically requires it

---

## HOW TO MAKE AN EDIT

1. `grep -n "def function_name"` to find line number
2. `sed -n 'START,ENDp'` to read just that function
3. Make the edit with `str_replace` using a unique anchor string
4. `sed -n 'START,ENDp'` to verify only changed lines
5. Done — do not re-read the whole file

---

## CURRENT STATUS

| Feature | Status |
|---|---|
| Login (Admin + Executive) | ✅ Done |
| Dashboard tabs | ✅ Done |
| Bucket Summary table | ✅ Done |
| Executive Ranking | ✅ Done |
| Action Center | ✅ Done |
| Pending Trails | ✅ Done |
| DRA & Agency | ✅ Done |
| Executive Tracker | ✅ Done |
| Loan Search | ✅ Done |
| Hero Cards | 🔧 In Progress |
| Mobile responsive | 🔧 Partial |
| PTP Dashboard | ❌ Pending |
| Cloud hosting | ❌ Pending |
