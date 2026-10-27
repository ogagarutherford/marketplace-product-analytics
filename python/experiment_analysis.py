"""
Checkout simplification experiment: analysis exactly as pre-registered in docs/experiment_design.md.

1. Sample-ratio mismatch (SRM) check
2. Primary metric: user conversion (two-proportion z-test, 95% CI, comparison with the MDE)
3. Secondary: revenue per user (bootstrap CI + Mann-Whitney), checkout completion
4. Guardrails: AOV (bootstrap CI), cancellation + return rate
5. Pre-specified segments: device, with a Bonferroni-adjusted threshold
6. Robustness: lift by assignment week (novelty check)

Outputs: results/experiment_results.json, docs/images/experiment_*.png, docs/experiment_readout.md
Run from the repo root:  python python/experiment_analysis.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import chisquare, mannwhitneyu
from statsmodels.stats.proportion import confint_proportions_2indep, proportions_ztest

from warehouse import query

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "images"; IMG.mkdir(parents=True, exist_ok=True)
(ROOT / "results").mkdir(exist_ok=True)
MDE_PP = 1.0            # pre-registered minimum detectable effect, percentage points
ALPHA = 0.05
SEGMENTS = ["mobile", "desktop", "tablet"]
rng = np.random.default_rng(42)
NAVY, YELLOW, GREY, GREEN, RED = "#16213B", "#F2B705", "#9AA4B5", "#1E7A4C", "#B3261E"

users = query("select * from marts.fct_experiment_users")
orders = query("""
    select a.variant, o.order_id, o.order_status, o.item_revenue_eur
    from marts.fct_orders o
    join staging.stg_experiment_assignments a on a.user_id = o.user_id
    where o.order_timestamp >= a.assigned_at and o.order_timestamp < timestamp '2025-12-01'
""")
sessions = query("""
    select a.variant, s.began_checkout, s.purchased
    from marts.fct_sessions s
    join staging.stg_experiment_assignments a on a.user_id = s.user_id
    where s.session_start >= a.assigned_at and s.session_start < timestamp '2025-12-01'
""")
C, T = users[users.variant == "control"], users[users.variant == "treatment"]
R = {}


def two_prop(x_t, n_t, x_c, n_c):
    _, p = proportions_ztest([x_t, x_c], [n_t, n_c])
    lo, hi = confint_proportions_2indep(x_t, n_t, x_c, n_c, method="newcomb")
    rc, rt = x_c / n_c, x_t / n_t
    return {"control_rate": rc, "treatment_rate": rt, "diff_pp": (rt - rc) * 100,
            "ci_low_pp": lo * 100, "ci_high_pp": hi * 100, "relative_lift": rt / rc - 1, "p_value": p}


def boot_diff(a, b, n=10_000):
    """Bootstrap 95% CI for mean(b) - mean(a)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    diffs = np.array([rng.choice(b, len(b)).mean() - rng.choice(a, len(a)).mean() for _ in range(n)])
    return float(b.mean() - a.mean()), float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5)), diffs


# 1. SRM
srm_p = chisquare([len(C), len(T)]).pvalue
R["srm"] = {"control_users": len(C), "treatment_users": len(T), "p_value": srm_p, "passed": srm_p >= 0.001}

# 2. Primary metric
R["primary"] = two_prop(T.converted.sum(), len(T), C.converted.sum(), len(C))

# 3. Secondary metrics
d, lo, hi, rev_draws = boot_diff(C.revenue_eur, T.revenue_eur)
R["revenue_per_user"] = {"control": C.revenue_eur.mean(), "treatment": T.revenue_eur.mean(),
                         "diff": d, "ci_low": lo, "ci_high": hi,
                         "mann_whitney_p": mannwhitneyu(T.revenue_eur, C.revenue_eur).pvalue}
sc, st = sessions[(sessions.variant == "control") & (sessions.began_checkout == 1)], sessions[(sessions.variant == "treatment") & (sessions.began_checkout == 1)]
R["checkout_completion"] = two_prop(st.purchased.sum(), len(st), sc.purchased.sum(), len(sc))

# 4. Guardrails
oc, ot = orders[orders.variant == "control"], orders[orders.variant == "treatment"]
okc, okt = oc[oc.order_status != "cancelled"], ot[ot.order_status != "cancelled"]
d, lo, hi, _ = boot_diff(okc.item_revenue_eur, okt.item_revenue_eur)
R["guardrail_aov"] = {"control": okc.item_revenue_eur.mean(), "treatment": okt.item_revenue_eur.mean(),
                      "diff": d, "ci_low": lo, "ci_high": hi, "breach": hi < -0.05 * okc.item_revenue_eur.mean()}
bad_c, bad_t = (oc.order_status != "delivered").sum(), (ot.order_status != "delivered").sum()
g = two_prop(bad_t, len(ot), bad_c, len(oc))
g["breach"] = g["ci_low_pp"] > 0 and g["p_value"] < ALPHA
R["guardrail_cancel_return"] = g

# 5. Segments (Bonferroni)
alpha_seg = ALPHA / len(SEGMENTS)
R["segments"] = {"bonferroni_alpha": alpha_seg}
for dev in SEGMENTS:
    c, t = C[C.first_exposure_device == dev], T[T.first_exposure_device == dev]
    s = two_prop(t.converted.sum(), len(t), c.converted.sum(), len(c))
    s.update({"control_users": len(c), "treatment_users": len(t), "significant_after_bonferroni": s["p_value"] < alpha_seg})
    R["segments"][dev] = s

# 6. Novelty check: lift by assignment week
users["assign_week"] = users.assigned_at.dt.to_period("W").dt.start_time.dt.date.astype(str)
R["by_assignment_week"] = {}
for wk, g_ in users.groupby("assign_week"):
    c, t = g_[g_.variant == "control"], g_[g_.variant == "treatment"]
    w_ = two_prop(t.converted.sum(), len(t), c.converted.sum(), len(c))
    R["by_assignment_week"][wk] = {"users": len(g_), "diff_pp": w_["diff_pp"], "ci_low_pp": w_["ci_low_pp"], "ci_high_pp": w_["ci_high_pp"]}

# Decision (rule from the design doc)
p = R["primary"]
sig = p["p_value"] < ALPHA
meaningful = p["ci_high_pp"] >= MDE_PP
guardrails_ok = not R["guardrail_aov"]["breach"] and not R["guardrail_cancel_return"]["breach"]
if not R["srm"]["passed"]:
    decision = "Stop: sample-ratio mismatch. Investigate assignment before reading results."
elif sig and guardrails_ok and p["ci_low_pp"] >= MDE_PP:
    decision = "Ship to all users."
elif sig and guardrails_ok:
    decision = "Ship, and keep measuring: the lift is real, but the interval includes effects smaller than the MDE."
else:
    decision = "Do not ship yet: iterate or extend."
R["decision"] = decision
R["mde_pp"] = MDE_PP
(ROOT / "results" / "experiment_results.json").write_text(json.dumps(R, indent=2, default=float))

# ---------------------------------------------------------------- charts
fig, ax = plt.subplots(figsize=(8, 3.6))
rows = [("All users", p)] + [(dev.capitalize(), R["segments"][dev]) for dev in SEGMENTS]
for i, (lab, s) in enumerate(rows[::-1]):
    colour = NAVY if lab == "All users" else (GREEN if s.get("significant_after_bonferroni") else GREY)
    ax.errorbar(s["diff_pp"], i, xerr=[[s["diff_pp"] - s["ci_low_pp"]], [s["ci_high_pp"] - s["diff_pp"]]],
                fmt="o", color=colour, capsize=4, lw=2)
    ax.text(s["ci_high_pp"] + 0.15, i, f"{s['diff_pp']:+.2f} pp", va="center", fontsize=9)
ax.axvline(0, color="black", lw=0.8); ax.axvline(MDE_PP, color=YELLOW, lw=2, ls="--", label=f"MDE (+{MDE_PP:.1f} pp)")
ax.set_yticks(range(len(rows)), [r[0] for r in rows[::-1]])
ax.set_xlabel("Treatment minus control, user conversion (percentage points, 95% CI)")
ax.set_title("Simplified checkout: the lift is driven by mobile")
ax.set_xlim(-1.8, 5.4); ax.legend(loc="upper right", fontsize=8); plt.tight_layout(); plt.savefig(IMG / "experiment_lift_by_device.png", dpi=150); plt.close()

fig, ax = plt.subplots(figsize=(7, 3.6))
ax.hist(rev_draws, bins=60, color=GREY)
ax.axvline(0, color="black", lw=0.8)
ax.axvline(R["revenue_per_user"]["ci_low"], color=NAVY, ls="--"); ax.axvline(R["revenue_per_user"]["ci_high"], color=NAVY, ls="--")
ax.set_title("Revenue per user: bootstrap distribution of the difference (10,000 resamples)")
ax.set_xlabel("Treatment minus control (EUR per user)"); plt.tight_layout(); plt.savefig(IMG / "experiment_revenue_bootstrap.png", dpi=150); plt.close()

wk = R["by_assignment_week"]
fig, ax = plt.subplots(figsize=(7, 3.4))
xs = list(wk); vals = [v["diff_pp"] for v in wk.values()]
ax.errorbar(xs, vals, yerr=[[v["diff_pp"] - v["ci_low_pp"] for v in wk.values()], [v["ci_high_pp"] - v["diff_pp"] for v in wk.values()]],
            fmt="o", color=NAVY, capsize=5, lw=2)
ax.axhline(0, color="black", lw=0.8); ax.axhline(p["diff_pp"], color=YELLOW, ls="--", lw=1.5, label="Overall lift")
ax.set_title("Lift by assignment week, with 95% CIs (novelty check)"); ax.set_ylabel("pp"); ax.legend(fontsize=8)
plt.tight_layout(); plt.savefig(IMG / "experiment_lift_by_week.png", dpi=150); plt.close()

# ---------------------------------------------------------------- console summary
print(f"SRM: control {len(C):,} vs treatment {len(T):,} users, p = {srm_p:.3f} -> {'pass' if R['srm']['passed'] else 'FAIL'}")
print(f"Primary: {p['control_rate']:.2%} -> {p['treatment_rate']:.2%}  ({p['diff_pp']:+.2f} pp, {p['relative_lift']:+.1%}), "
      f"95% CI [{p['ci_low_pp']:+.2f}, {p['ci_high_pp']:+.2f}] pp, p = {p['p_value']:.4f}")
rv = R["revenue_per_user"]
print(f"Revenue/user: EUR {rv['control']:.2f} -> {rv['treatment']:.2f}, diff {rv['diff']:+.2f} [{rv['ci_low']:+.2f}, {rv['ci_high']:+.2f}], Mann-Whitney p = {rv['mann_whitney_p']:.4f}")
a = R["guardrail_aov"]; print(f"Guardrail AOV: EUR {a['control']:.2f} -> {a['treatment']:.2f}, diff {a['diff']:+.2f} [{a['ci_low']:+.2f}, {a['ci_high']:+.2f}] -> {'BREACH' if a['breach'] else 'ok'}")
g = R["guardrail_cancel_return"]; print(f"Guardrail cancel+return: {g['control_rate']:.2%} -> {g['treatment_rate']:.2%}, p = {g['p_value']:.3f} -> {'BREACH' if g['breach'] else 'ok'}")
for dev in SEGMENTS:
    s = R["segments"][dev]
    print(f"  {dev:8s} {s['diff_pp']:+.2f} pp [{s['ci_low_pp']:+.2f}, {s['ci_high_pp']:+.2f}], p = {s['p_value']:.4f}"
          f"{'  (significant after Bonferroni)' if s['significant_after_bonferroni'] else ''}")
print("Decision:", decision)
