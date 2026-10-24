# Experiment Design (pre-registered before analysis)

**Experiment:** `checkout_simplification_2025_11`
**Change:** Treatment replaces the three-step checkout with a single-page checkout (fewer form fields, guest checkout first, add-on suggestions moved after purchase).
**Hypothesis:** A simpler checkout increases the share of users who complete a purchase, especially on mobile where form friction is highest.

| Item | Decision |
|---|---|
| Randomisation unit | **User** (deterministic 50/50 hash of `user_id`), so a user sees one checkout across sessions |
| Eligible population | Users with ≥1 session between 3 and 30 November 2025 |
| Exposure window | From a user's first session in the window (`assigned_at`) to 30 November |
| **Primary metric** | **User conversion:** share of assigned users with ≥1 purchase in the exposure window |
| Secondary metrics | Revenue per user; session conversion; checkout completion rate |
| Guardrails | AOV (must not fall materially); order cancellation and return rate; checkout latency (not available in synthetic data, noted) |
| Pre-specified segments | Device (mobile, desktop, tablet). All other cuts are exploratory. |

## Sample size

- **Baseline:** user conversion over a comparable four-week pre-period (1–28 October) = **7.1%**
- **Minimum detectable effect (MDE):** **+1.0 percentage point** absolute (≈ +14% relative): the smallest lift that justifies the engineering and design cost of maintaining a new checkout
- **α = 0.05** (two-sided), **power = 0.80**
- **Required sample:** **≈ 11,000 users per arm** (`statsmodels` `NormalIndPower`, Cohen's h)
- **Expected traffic:** October had ~24,600 unique users in four weeks; with November seasonality, four weeks should yield ≈ 30,000+ eligible users, comfortably above the ~22,000 needed
- **Duration:** four full weeks (covers weekly cycles); no early stopping or peeking at significance

## Analysis plan

1. **Sample-ratio mismatch (SRM):** chi-square test on users per arm; if p < 0.001, stop and investigate before reading any results.
2. **Primary metric:** two-proportion z-test; report absolute and relative lift with a 95% confidence interval; compare the interval with the MDE.
3. **Revenue per user and AOV:** skewed, so use bootstrap confidence intervals (10,000 resamples), with Mann-Whitney as a robustness check.
4. **Segments:** device only, with a Bonferroni-adjusted threshold; anything else is exploratory.
5. **Decision rule:** ship if the primary metric is significant, the interval is consistent with a commercially meaningful lift, and no guardrail breaches; otherwise iterate or stop.
