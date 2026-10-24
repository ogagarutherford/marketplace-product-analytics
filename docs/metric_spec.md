# Metric Specification

Every metric is defined once here, before any SQL is written.

## Funnel (grain: session)

| Metric | Definition | Denominator | Notes |
|---|---|---|---|
| Sessions | Count of distinct `session_id` | — | A session belongs to one user, device and channel |
| Product view rate | Sessions with ≥1 `view_item` ÷ sessions | All sessions | |
| Add-to-cart rate | Sessions with `add_to_cart` ÷ sessions with `view_item` | Step-to-step | Also reported cumulatively (÷ all sessions) |
| Checkout rate | Sessions with `begin_checkout` ÷ sessions with `add_to_cart` | Step-to-step | |
| Checkout completion | Sessions with `purchase` ÷ sessions with `begin_checkout` | Step-to-step | The step the experiment targets |
| Session conversion | Sessions with `purchase` ÷ all sessions | All sessions | |
| Time to purchase | Minutes from `session_start` to `purchase` | Purchasing sessions | Report median and P90 |

A session counts at a step only once, and only if every earlier step occurred (checked in data-quality tests).

## Customer (grain: user)

| Metric | Definition | Notes |
|---|---|---|
| User conversion (period) | Users with ≥1 purchase in the period ÷ users with ≥1 session | Primary experiment metric, per user |
| Revenue per user | Net item revenue (quantity × unit price, excl. shipping, delivered + returned orders) ÷ users | Cancelled orders excluded |
| AOV | Net item revenue ÷ orders | Guardrail in the experiment |
| Repeat purchase rate (30/90d) | Buyers with a 2nd order within 30/90 days of the first ÷ first-time buyers | Only buyers with a full window observed |
| Cohort retention | Share of a first-purchase-month cohort ordering in month N | |
| RFM segment | Quintile scores on recency, frequency, monetary value | 5–6 named segments |

## Acquisition (grain: channel × period)

| Metric | Definition | Notes |
|---|---|---|
| Paid CAC (proxy) | Paid spend ÷ new buyers first acquired via that channel | Paid search, paid social, affiliate only |
| Channel conversion | Conversion of sessions by channel | Check mix effects (Simpson's paradox) before comparing over time |
