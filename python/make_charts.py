"""
Charts for the README: funnel by device, acquisition quality, cohort retention, RFM segments.
Run from the repo root:  python python/make_charts.py
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from warehouse import query

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "images"; IMG.mkdir(parents=True, exist_ok=True)
NAVY, YELLOW, GREY, RED = "#16213B", "#F2B705", "#9AA4B5", "#B3261E"

# 1. Funnel step rates by device
f = query("""select device, sum(sessions) s, sum(viewed_item) v, sum(added_to_cart) c, sum(began_checkout) k, sum(purchased) p
             from marts.mart_funnel_weekly group by 1""").set_index("device").loc[["desktop", "tablet", "mobile"]]
steps = {"Product view\n(of sessions)": f.v / f.s, "Add to cart\n(of viewers)": f.c / f.v,
         "Checkout\n(of carts)": f.k / f.c, "Purchase\n(of checkouts)": f.p / f.k}
fig, ax = plt.subplots(figsize=(9, 4.2)); x = np.arange(len(steps)); w = 0.26
for i, (dev, col) in enumerate(zip(f.index, [NAVY, GREY, YELLOW])):
    vals = [v[dev] * 100 for v in steps.values()]
    bars = ax.bar(x + (i - 1) * w, vals, w, label=dev.capitalize(), color=col)
    for b, v in zip(bars, vals): ax.text(b.get_x() + b.get_width() / 2, v + 1, f"{v:.0f}", ha="center", fontsize=8)
ax.set_xticks(x, list(steps)); ax.set_ylabel("Step conversion (%)"); ax.set_ylim(0, 88)
ax.legend(loc="upper center", ncol=3, frameon=False)
ax.set_title("Mobile loses ground at add-to-cart and, most of all, at final purchase")
plt.tight_layout(); plt.savefig(IMG / "funnel_by_device.png", dpi=150); plt.close()

# 2. Acquisition: 30-day buyer rate and paid CAC
a = query("""select acquisition_channel ch, 100.0 * sum(new_buyers_30d) / sum(new_users) rate,
                    sum(paid_spend_eur) / nullif(sum(new_buyers_30d), 0) cac
             from marts.mart_acquisition_monthly where full_window_observed group by 1 order by rate""")
fig, ax = plt.subplots(figsize=(8, 3.8))
bars = ax.barh(a.ch.str.replace("_", " "), a.rate, color=[RED if c == "paid_social" else NAVY for c in a.ch])
for b, r, c in zip(bars, a.rate, a.cac):
    ax.text(r + 0.1, b.get_y() + b.get_height() / 2, f"{r:.1f}%" + (f"  ·  CAC €{c:.0f}" if c == c else ""), va="center", fontsize=9)
ax.set_xlabel("New users who buy within 30 days (%)"); ax.set_xlim(0, a.rate.max() * 1.45)
ax.set_title("Paid social brings the weakest buyers")
plt.tight_layout(); plt.savefig(IMG / "acquisition_quality.png", dpi=150); plt.close()

# 3. Cohort retention curve
r = query("""select months_since_first_order m, 100.0 * sum(active_buyers) / sum(cohort_buyers) pct
             from marts.mart_cohort_retention where first_order_month <= date '2025-09-01' group by 1 order by 1""")
r = r[r.m <= 3]
fig, ax = plt.subplots(figsize=(7, 3.6))
ax.plot(r.m, r.pct, marker="o", color=NAVY, lw=2)
for m, p in zip(r.m, r.pct): ax.text(m + 0.08, p + 4, f"{p:.1f}%", ha="left", fontsize=9)
ax.set_xticks(r.m, [f"Month {int(m)}" for m in r.m]); ax.set_ylim(0, 112); ax.set_ylabel("Buyers ordering again (%)")
ax.set_title("Almost no one buys a second time")
plt.tight_layout(); plt.savefig(IMG / "cohort_retention.png", dpi=150); plt.close()

# 4. RFM segments
s = query("""select rfm_segment seg, count(*) n, sum(monetary_eur) rev from marts.mart_rfm group by 1 order by n""")
fig, ax = plt.subplots(figsize=(8, 3.6))
bars = ax.barh(s.seg, s.n, color=NAVY)
for b, n, rev in zip(bars, s.n, s.rev): ax.text(n + 30, b.get_y() + b.get_height() / 2, f"{n:,} buyers  ·  €{rev/1000:,.0f}k", va="center", fontsize=9)
ax.set_xlim(0, s.n.max() * 1.4); ax.set_xlabel("Buyers")
ax.set_title("Buyers by RFM segment: loyal customers are a tiny group")
plt.tight_layout(); plt.savefig(IMG / "rfm_segments.png", dpi=150); plt.close()
print("Charts written: funnel_by_device, acquisition_quality, cohort_retention, rfm_segments")
