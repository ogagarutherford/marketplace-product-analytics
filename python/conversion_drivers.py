"""
What is associated with session conversion? Logistic regression on pre-experiment sessions.

- Data: sessions from 1 July to 2 November 2025 (before the experiment, so treatment can't contaminate it)
- Model: purchased ~ device + channel + visitor type + country + weekend
- Standard errors clustered by user, because sessions from the same user are not independent
- Output: odds ratios with 95% CIs, average marginal effects, a forest plot
- Interpretation: associations, not causal effects (see docs/experiment_readout.md)

Run from the repo root:  python python/conversion_drivers.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from warehouse import query

ROOT = Path(__file__).resolve().parents[1]
df = query("""
    select purchased, device, channel, visitor_type, country, user_id,
           case when dayofweek(session_date) in (0, 6) then 1 else 0 end as weekend
    from marts.fct_sessions
    where session_start < timestamp '2025-11-03'
""")
print(f"Sessions in model: {len(df):,}  (conversion {df.purchased.mean():.2%})")

formula = ("purchased ~ C(device, Treatment('desktop')) + C(channel, Treatment('organic_search'))"
           " + C(visitor_type, Treatment('new')) + C(country, Treatment('DE')) + weekend")
groups = pd.factorize(df.user_id)[0]
model = smf.logit(formula, data=df).fit(disp=False, cov_type="cluster", cov_kwds={"groups": groups})

ci = model.conf_int()
out = pd.DataFrame({"odds_ratio": np.exp(model.params), "ci_low": np.exp(ci[0]), "ci_high": np.exp(ci[1]),
                    "p_value": model.pvalues}).drop(index="Intercept")
mfx = model.get_margeff(at="overall").summary_frame()
out["avg_marginal_effect_pp"] = mfx["dy/dx"].values * 100
pretty = (out.index.str.replace(r"C\((\w+), Treatment\('[^']+'\)\)\[T\.", r"\1 = ", regex=True)
          .str.replace("]", "", regex=False).str.replace("weekend", "weekend = yes"))
out.index = pretty
out = out.sort_values("odds_ratio")
out.round(4).to_csv(ROOT / "results" / "conversion_drivers_odds_ratios.csv")
print(out.round(3).to_string())
print(f"\nPseudo R-squared: {model.prsquared:.3f}  |  baseline: desktop, organic search, new visitor, Germany, weekday")
import json
(ROOT / "results" / "conversion_drivers_meta.json").write_text(json.dumps({"sessions": int(len(df)), "pseudo_r2": float(model.prsquared)}, indent=2))

fig, ax = plt.subplots(figsize=(8, 4.8))
y = np.arange(len(out))
sig = out.p_value < 0.05
ax.errorbar(out.odds_ratio, y, xerr=[out.odds_ratio - out.ci_low, out.ci_high - out.odds_ratio],
            fmt="none", ecolor="#9AA4B5", capsize=3)
ax.scatter(out.odds_ratio, y, color=np.where(sig, "#16213B", "#9AA4B5"), zorder=3)
ax.axvline(1, color="black", lw=0.8)
ax.set_yticks(y, out.index); ax.set_xscale("log")
ticks = [0.5, 0.75, 1, 1.25, 1.5, 2]
ax.set_xticks(ticks, [f"{v:g}" for v in ticks]); ax.minorticks_off()
ax.set_xlabel("Odds ratio vs baseline (log scale, 95% CI, user-clustered)")
ax.set_title("What is associated with session conversion (pre-experiment)")
plt.tight_layout(); plt.savefig(ROOT / "docs" / "images" / "conversion_drivers.png", dpi=150)
