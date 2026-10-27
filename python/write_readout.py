"""
Write docs/experiment_readout.md from results/ so every number in the memo comes from the analysis.
Run after experiment_analysis.py and conversion_drivers.py:  python python/write_readout.py
"""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
R = json.loads((ROOT / "results" / "experiment_results.json").read_text())
D = pd.read_csv(ROOT / "results" / "conversion_drivers_odds_ratios.csv", index_col=0)
META = json.loads((ROOT / "results" / "conversion_drivers_meta.json").read_text())
eur = lambda v: ("−" if v < 0 else "+") + f"€{abs(v):.2f}"
p, rv, a, g, s = R["primary"], R["revenue_per_user"], R["guardrail_aov"], R["guardrail_cancel_return"], R["segments"]
users = R["srm"]["control_users"] + R["srm"]["treatment_users"]
monthly = lambda x: users * x            # ~4 weeks of eligible users ≈ one month
pp = lambda v: f"{v:+.2f} pp"
fmt_or = lambda k: f"{D.loc[k, 'odds_ratio']:.2f}"

W = R["by_assignment_week"]
inside = [k for k, v in W.items() if v["ci_low_pp"] <= p["diff_pp"] <= v["ci_high_pp"]]
outside = [k for k in W if k not in inside]
sgn = lambda v: ("−" if v < 0 else "+") + f"{abs(v):.1f}"
novelty = (f"the weekly lift ranges from {sgn(min(v['diff_pp'] for v in W.values()))} to {sgn(max(v['diff_pp'] for v in W.values()))} pp. "
           f"{len(inside)} of {len(W)} weekly intervals include the overall estimate"
           + (f"; users assigned in the week of {', '.join(outside)} sit below it" if outside else "")
           + ". Users assigned later also had less time left in the test to convert, so the weeks aren't directly comparable. "
           "The data can't rule a novelty effect in or out, which is another reason to keep a holdout after launch.")
md = f"""# Experiment Readout: Simplified Checkout (November 2025)

> Synthetic data. Analysis follows the pre-registered plan in [experiment_design.md](experiment_design.md).

## Recommendation

**Based on the experiment and behavioural evidence, Product should roll out the simplified checkout to all users,
starting with mobile, and keep monitoring returns and cancellations for four weeks after launch.**

{R['decision']}

## Results at a glance

| Check | Result | Verdict |
|---|---|---|
| Sample-ratio mismatch | {R['srm']['control_users']:,} control vs {R['srm']['treatment_users']:,} treatment users (p = {R['srm']['p_value']:.2f}) | ✅ Randomisation healthy |
| **Primary: user conversion** | **{p['control_rate']:.2%} → {p['treatment_rate']:.2%}** ({pp(p['diff_pp'])}, {p['relative_lift']:+.1%} relative); 95% CI [{pp(p['ci_low_pp'])}, {pp(p['ci_high_pp'])}]; p = {p['p_value']:.3f} | ✅ Significant |
| Compared with the MDE (+{R['mde_pp']:.1f} pp) | Point estimate is below the MDE; the interval spans {pp(p['ci_low_pp'])} to {pp(p['ci_high_pp'])} | ⚠️ Real, but possibly smaller than planned |
| Revenue per user | €{rv['control']:.2f} → €{rv['treatment']:.2f} (+€{rv['diff']:.2f}; bootstrap 95% CI [+€{rv['ci_low']:.2f}, +€{rv['ci_high']:.2f}]); Mann-Whitney p = {rv['mann_whitney_p']:.3f} | ✅ Positive |
| Checkout completion (sessions reaching checkout) | {R['checkout_completion']['control_rate']:.1%} → {R['checkout_completion']['treatment_rate']:.1%} | ✅ Mechanism confirmed |
| Guardrail: AOV | €{a['control']:.2f} → €{a['treatment']:.2f} (95% CI {eur(a['ci_low'])} to {eur(a['ci_high'])}) | ✅ No decline |
| Guardrail: cancellations + returns | {g['control_rate']:.2%} → {g['treatment_rate']:.2%} (p = {g['p_value']:.2f}) | ⚠️ Not significant, but directionally up: monitor |

![Lift by device](images/experiment_lift_by_device.png)

## Who benefits (pre-specified segment: device; Bonferroni α = {s['bonferroni_alpha']:.4f})

| Device | Lift | 95% CI | p | Significant after correction? |
|---|---|---|---|---|
| Mobile | {pp(s['mobile']['diff_pp'])} | [{pp(s['mobile']['ci_low_pp'])}, {pp(s['mobile']['ci_high_pp'])}] | {s['mobile']['p_value']:.4f} | {'Yes' if s['mobile']['significant_after_bonferroni'] else 'No'} |
| Desktop | {pp(s['desktop']['diff_pp'])} | [{pp(s['desktop']['ci_low_pp'])}, {pp(s['desktop']['ci_high_pp'])}] | {s['desktop']['p_value']:.4f} | {'Yes' if s['desktop']['significant_after_bonferroni'] else 'No'} |
| Tablet | {pp(s['tablet']['diff_pp'])} | [{pp(s['tablet']['ci_low_pp'])}, {pp(s['tablet']['ci_high_pp'])}] | {s['tablet']['p_value']:.4f} | {'Yes' if s['tablet']['significant_after_bonferroni'] else 'No'} |

The effect is concentrated on mobile, where form friction is highest, which matches the original hypothesis.
Desktop shows no measurable change in either direction. Tablet points the same way as mobile but is too small a
segment to conclude anything on its own.

## Business value (rough sizing)

The test exposed {users:,} users in four weeks, about one month of eligible traffic. At +€{rv['diff']:.2f} revenue
per user, the simplified checkout is worth roughly **€{monthly(rv['diff']):,.0f} in additional item revenue per month**
(plausible range €{monthly(rv['ci_low']):,.0f} to €{monthly(rv['ci_high']):,.0f}, from the bootstrap interval).
This is revenue, not margin, and assumes November traffic levels.

## Why roll out to everyone rather than mobile only

- The primary metric is significant overall and no guardrail breaches.
- Desktop shows no harm, and maintaining two checkout flows adds engineering and QA cost.
- The desktop experience can be improved separately: a desktop-specific test is the natural follow-up.

## Risks and follow-ups

1. **Returns and cancellations:** {g['control_rate']:.1%} → {g['treatment_rate']:.1%}. Not significant, but a simpler checkout
   might let more impulse orders through. Track weekly after launch; escalate if the increase holds.
2. **Effect size:** the interval includes lifts below the +{R['mde_pp']:.1f} pp MDE. Keep a 5% holdout for four weeks to confirm
   the long-run effect.
3. **Novelty:** {novelty}

![Lift by assignment week](images/experiment_lift_by_week.png)

## What else drives conversion (regression, pre-experiment sessions)

A logistic regression on {META['sessions']:,} pre-experiment sessions, with standard errors clustered by user:

- **Mobile** sessions have {fmt_or('device = mobile')}× the odds of converting compared with desktop, and **paid social** {fmt_or('channel = paid_social')}× compared with organic search.
- **Returning visitors** convert at {fmt_or('visitor_type = returning')}× the odds of new visitors; **email** traffic at {fmt_or('channel = email')}×.
- Country and weekend show no meaningful association.

These are **associations, not causal effects**: mobile users may differ from desktop users in intent, not just device.
The model explains little individual variation (pseudo-R² {META['pseudo_r2']:.3f}), because purchase intent is not observed. Still, it
points to where to look next: mobile checkout (now addressed), paid social targeting, and bringing visitors back.

![Conversion drivers](images/conversion_drivers.png)
"""
(ROOT / "docs" / "experiment_readout.md").write_text(md)
print("Wrote docs/experiment_readout.md")
