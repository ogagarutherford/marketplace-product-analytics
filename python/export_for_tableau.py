"""
Export dashboard-ready tables to one Excel file for Tableau Public: exports/kroma_dashboard_data.xlsx
Run from the repo root (after experiment_analysis.py):  python python/export_for_tableau.py
"""
import json
from pathlib import Path
import pandas as pd
from warehouse import query

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "exports"; OUT.mkdir(exist_ok=True)
R = json.loads((ROOT / "results" / "experiment_results.json").read_text())

sheets = {
    "funnel_weekly": query("select * from marts.mart_funnel_weekly order by session_week"),
    "acquisition": query("select * from marts.mart_acquisition_monthly order by first_visit_month"),
    "cohorts": query("select * from marts.mart_cohort_retention order by first_order_month, months_since_first_order"),
    "rfm": query("select user_id, recency_days, frequency, monetary_eur, rfm_segment from marts.mart_rfm"),
    "experiment": pd.DataFrame([{"segment": "All users", **{k: R["primary"][k] for k in ("control_rate", "treatment_rate", "diff_pp", "ci_low_pp", "ci_high_pp", "p_value")}}]
                               + [{"segment": d.capitalize(), **{k: R["segments"][d][k] for k in ("control_rate", "treatment_rate", "diff_pp", "ci_low_pp", "ci_high_pp", "p_value")}} for d in ("mobile", "desktop", "tablet")]),
}
for name in ("funnel_weekly", "acquisition", "cohorts"):
    for col in sheets[name].columns:
        if "week" in col or "month" in col and sheets[name][col].dtype != "int64":
            sheets[name][col] = pd.to_datetime(sheets[name][col]).dt.date
with pd.ExcelWriter(OUT / "kroma_dashboard_data.xlsx") as xl:
    for name, df in sheets.items():
        df.to_excel(xl, sheet_name=name, index=False)
print(f"Wrote exports/kroma_dashboard_data.xlsx with sheets: {', '.join(sheets)}")
