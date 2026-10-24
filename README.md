# Kroma — Marketplace Product Analytics & Experimentation

> Product analytics for a two-sided home & lifestyle marketplace: funnel, acquisition, retention,
> an A/B test on a simplified checkout, and a regression on conversion drivers.
> **Hands-on portfolio project on synthetic data** ([assumptions](docs/data_assumptions.md)), not production experience.

## Business questions
See [docs/business_questions.md](docs/business_questions.md). In short: where do shoppers drop off, which
channels bring valuable customers, do buyers come back, and **should Product ship the simplified checkout?**

## Design before analysis
- [Metric specification](docs/metric_spec.md): every funnel, customer and acquisition metric defined once
- [Experiment design](docs/experiment_design.md): pre-registered hypothesis, metrics, guardrails and sample size (≈ 11,000 users per arm for a +1.0 pp MDE)
- [Data model](docs/data_model.md): session, event, order and experiment facts with their grains

## Stack
DuckDB (local analytical warehouse) · dbt (dbt-duckdb) · SQL · Python (pandas, statsmodels, SciPy) · Tableau Public · Git/GitHub

## Reproduce
```bash
pip install -r requirements.txt
python scripts/generate_data.py      # synthetic Parquet files in data/raw/
python scripts/load_to_duckdb.py     # loads warehouse/kroma.duckdb and prints a funnel check
```

## Progress
- [x] Day 8 — business questions, metric spec, experiment design, data model, synthetic data, DuckDB load
- [ ] Day 9 — dbt models: sessions, funnel, acquisition, cohorts, RFM
- [ ] Day 10 — A/B test analysis (SRM, z-test, bootstrap, segments) and regression
- [ ] Day 11 — dashboard, recommendation memo, README findings, v1.0
