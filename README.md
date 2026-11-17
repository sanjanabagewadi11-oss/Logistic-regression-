# Manufacturing Digitalization Control Tower

A Streamlit prototype covering the three use cases:
1. Inbound reorder points under supplier lead-time variability (NumPy + Pandas).
2. Outbound first-mile, mid-mile and last-mile delay analysis (Pandas + Matplotlib).
3. Supplier disruption what-if impact control tower (Streamlit + Pandas + NumPy + Matplotlib).

## Run on Windows
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

The app uses synthetic demo data by default. Use the CSV templates included in this folder or upload data that matches the required columns shown in the app.

## Important
This is a prototype, not a production planning system. Reorder point estimates and penalty exposure depend on assumptions and supplied data. Validate data definitions, safety-stock policy, supplier capacity, inventory, BOMs, production schedules, customer due dates, and dataset licence before operational use.
