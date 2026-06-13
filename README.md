# Recovery Command Center

Offline Streamlit dashboard for resolution management.

## Files

- `app.py` - main dashboard
- `STATUS JUNE.xlsx` - Excel data source, expected beside `app.py`

## Run

```powershell
python -m streamlit run app.py
```

Open:

```text
http://localhost:8501
```

After saving changes in Excel, refresh the browser with Ctrl+F5 or use the app's Refresh data button.

## Excel Source

- File: `STATUS JUNE.xlsx`
- Sheet: `MAIN`

The app validates required columns at startup and shows any missing column names.
