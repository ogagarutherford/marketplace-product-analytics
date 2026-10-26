"""
Synthetic marketplace dataset generator: "Kroma", a fictional DACH home & lifestyle marketplace.
Period: 2025-07-01 to 2025-12-31. All data is SYNTHETIC (seed 42). Assumptions: docs/data_assumptions.md

Embedded experiment: a simplified checkout tested 2025-11-03 to 2025-11-30, randomised 50/50 by user.
The true effect is deliberately not documented until the analysis is done.

Usage:  python scripts/generate_data.py      -> Parquet files in data/raw/
"""
from pathlib import Path
import hashlib
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
OUT = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

START, END = pd.Timestamp("2025-07-01"), pd.Timestamp("2025-12-31")
DAYS = pd.date_range(START, END, freq="D")
EXP_START, EXP_END = pd.Timestamp("2025-11-03"), pd.Timestamp("2025-11-30")

# ------------------------------------------------------------------ catalogue
CATEGORIES = {  # name: (share of catalogue, median price EUR)
    "Furniture": (0.10, 240), "Lighting": (0.12, 75), "Decor": (0.20, 32), "Textiles": (0.16, 45),
    "Kitchen": (0.15, 38), "Garden": (0.09, 60), "Storage": (0.10, 42), "Bath": (0.08, 28)}
N_SELLERS, N_PRODUCTS = 320, 1500
sellers = pd.DataFrame({
    "seller_id": [f"S{i:04d}" for i in range(1, N_SELLERS + 1)],
    "seller_country": rng.choice(["DE", "AT", "CH", "NL", "PL"], N_SELLERS, p=[.55, .12, .10, .13, .10]),
    "seller_tier": rng.choice(["standard", "pro", "premium"], N_SELLERS, p=[.6, .3, .1]),
    "joined_date": [(pd.Timestamp("2022-01-01") + pd.Timedelta(days=int(d))).date()
                    for d in rng.integers(0, 1200, N_SELLERS)],
})
cat_names = list(CATEGORIES)
cat = rng.choice(cat_names, N_PRODUCTS, p=[CATEGORIES[c][0] for c in cat_names])
products = pd.DataFrame({
    "product_id": [f"P{i:05d}" for i in range(1, N_PRODUCTS + 1)],
    "category": cat,
    "seller_id": rng.choice(sellers.seller_id, N_PRODUCTS),
    "list_price_eur": np.round([CATEGORIES[c][1] * rng.lognormal(0, 0.45) for c in cat], 2),
    "avg_rating": np.round(np.clip(rng.normal(4.2, 0.4, N_PRODUCTS), 2.5, 5.0), 1),
})
pop = rng.pareto(1.2, N_PRODUCTS) + 1          # long-tail product popularity
pop = pop / pop.sum()

# ------------------------------------------------------------------ users
N_USERS = 95_000
day_w = (np.linspace(1.0, 1.6, len(DAYS)) * np.where(DAYS.month == 11, 1.35, 1.0)
         * np.where(DAYS.month == 12, 1.25, 1.0))
first_day = rng.choice(len(DAYS), N_USERS, p=day_w / day_w.sum())
CHANNELS = ["organic_search", "paid_search", "paid_social", "affiliate", "direct", "email"]
acq = rng.choice(CHANNELS[:5], N_USERS, p=[.30, .25, .20, .10, .15])
device = rng.choice(["mobile", "desktop", "tablet"], N_USERS, p=[.62, .32, .06])
engagement = rng.gamma(2.0, 0.5, N_USERS) * np.select(
    [acq == "paid_social", acq == "affiliate", acq == "organic_search"], [0.75, 0.85, 1.15], 1.0)
users = pd.DataFrame({
    "user_id": [f"U{i:06d}" for i in range(1, N_USERS + 1)],
    "first_visit_date": DAYS[first_day].date,
    "country": rng.choice(["DE", "AT", "CH"], N_USERS, p=[.70, .15, .15]),
    "acquisition_channel": acq,
    "primary_device": device,
})

# ------------------------------------------------------------------ sessions
n_sess = 1 + rng.poisson(2.6 * engagement)
u_idx = np.repeat(np.arange(N_USERS), n_sess)
k = np.concatenate([np.arange(n) for n in n_sess])              # session number per user
gap = np.where(k == 0, 0, rng.exponential(12, len(u_idx)))
offset = np.ceil(pd.Series(gap).groupby(u_idx).cumsum().values).astype(int)
s_day = first_day[u_idx] + offset
keep = s_day < len(DAYS)                       # drop sessions that would fall after the period ends
u_idx, k, s_day = u_idx[keep], k[keep], s_day[keep]
N_S = len(u_idx)
s_channel = np.where(k == 0, acq[u_idx], rng.choice(CHANNELS, N_S, p=[.22, .12, .08, .05, .33, .20]))
s_device = np.where(rng.random(N_S) < 0.85, device[u_idx],
                    rng.choice(["mobile", "desktop", "tablet"], N_S, p=[.6, .34, .06]))
returning = k > 0
s_time = DAYS[s_day] + pd.to_timedelta(rng.integers(6 * 60, 24 * 60, N_S), unit="m")

# experiment assignment: deterministic 50/50 hash on user_id, for users with a session in the window
in_window = np.asarray((DAYS[s_day] >= EXP_START) & (DAYS[s_day] <= EXP_END))
exp_users = np.unique(u_idx[in_window])
uid = users.user_id.values
variant_of = {u: ("treatment" if int(hashlib.md5(uid[u].encode()).hexdigest(), 16) % 2 else "control")
              for u in exp_users}
s_variant = np.array([variant_of.get(u) if w else None for u, w in zip(u_idx, in_window)], dtype=object)

# funnel probabilities
dev_cart = np.select([s_device == "desktop", s_device == "tablet"], [1.20, 1.05], 0.90)
ch_cart = np.select([s_channel == "paid_social", s_channel == "email", s_channel == "direct"], [0.70, 1.25, 1.15], 1.0)
p_view = np.clip(0.60 + 0.06 * returning, 0, 1)
p_cart = np.clip(0.15 * dev_cart * ch_cart * (1 + 0.25 * returning)
                 * np.clip(engagement[u_idx], 0.4, 2.0) ** 0.3, 0, 0.9)
p_chk = np.full(N_S, 0.55)
p_buy = np.select([s_device == "desktop", s_device == "tablet"], [0.66, 0.60], 0.55)
lift = np.select([s_device == "mobile", s_device == "tablet"], [0.110, 0.060], 0.035)
p_buy = p_buy + np.where(s_variant == "treatment", lift, 0.0)
viewed = rng.random(N_S) < p_view
carted = viewed & (rng.random(N_S) < p_cart)
checkout = carted & (rng.random(N_S) < p_chk)
purchased = checkout & (rng.random(N_S) < p_buy)

sessions = pd.DataFrame({
    "session_id": [f"SE{i:07d}" for i in range(1, N_S + 1)],
    "user_id": uid[u_idx], "session_start": s_time, "channel": s_channel, "device": s_device,
    "is_returning": returning,
})

# events: one row per funnel step reached
steps = [("session_start", np.ones(N_S, bool), 0), ("view_item", viewed, 1), ("add_to_cart", carted, 3),
         ("begin_checkout", checkout, 5), ("purchase", purchased, 7)]
ev = []
for name, mask, base_min in steps:
    idx = np.where(mask)[0]
    ts = s_time[idx] + pd.to_timedelta(base_min + rng.exponential(2.0, len(idx)) * (base_min > 0), unit="m")
    ev.append(pd.DataFrame({"session_id": sessions.session_id.values[idx], "user_id": uid[u_idx][idx],
                            "event_name": name, "event_timestamp": ts}))
events = pd.concat(ev).sort_values(["session_id", "event_timestamp"]).reset_index(drop=True)
events.insert(0, "event_id", [f"E{i:08d}" for i in range(1, len(events) + 1)])

# orders and order items
b_idx = np.where(purchased)[0]
N_O = len(b_idx)
purchase_ts = events[events.event_name == "purchase"].set_index("session_id")["event_timestamp"]
orders = pd.DataFrame({
    "order_id": [f"O{i:07d}" for i in range(1, N_O + 1)],
    "session_id": sessions.session_id.values[b_idx], "user_id": uid[u_idx][b_idx],
    "order_timestamp": purchase_ts.loc[sessions.session_id.values[b_idx]].values,
    "order_status": rng.choice(["delivered", "cancelled", "returned"], N_O, p=[.93, .03, .04]),
})
n_items = 1 + rng.poisson(0.55, N_O)
o_rep = np.repeat(np.arange(N_O), n_items)
prod_idx = rng.choice(N_PRODUCTS, len(o_rep), p=pop)
treat_item = (s_variant[b_idx] == "treatment")[o_rep]
qty = 1 + rng.poisson(0.15, len(o_rep))
price = products.list_price_eur.values[prod_idx] * rng.uniform(0.85, 1.0, len(o_rep))
price = np.where(treat_item & (rng.random(len(o_rep)) < 0.10), price * 0.85, price)
order_items = pd.DataFrame({
    "order_id": orders.order_id.values[o_rep],
    "order_item_seq": np.concatenate([np.arange(1, n + 1) for n in n_items]),
    "product_id": products.product_id.values[prod_idx], "seller_id": products.seller_id.values[prod_idx],
    "quantity": qty, "unit_price_eur": np.round(price, 2),
    "shipping_fee_eur": np.round(np.where(price > 49, 0.0, 4.95), 2),
})

first_exp = pd.Series(s_time[in_window], index=u_idx[in_window]).groupby(level=0).min()
assignments = pd.DataFrame({
    "user_id": [uid[u] for u in exp_users],
    "experiment_id": "checkout_simplification_2025_11",
    "variant": [variant_of[u] for u in exp_users],
    "assigned_at": first_exp.loc[exp_users].values,
})

# daily paid marketing spend
paid_cpc = {"paid_search": 1.55, "paid_social": 1.20, "affiliate": 0.95}
per_day = pd.DataFrame({"d": DAYS[s_day].date, "ch": s_channel}).value_counts()
rows = []
for (d, ch), n in per_day.items():
    if ch in paid_cpc:
        rows.append({"spend_date": d, "channel": ch, "clicks": int(n * rng.uniform(1.05, 1.2)),
                     "spend_eur": round(n * paid_cpc[ch] * rng.uniform(0.9, 1.15), 2)})
marketing_spend = pd.DataFrame(rows).sort_values(["spend_date", "channel"]).reset_index(drop=True)

tables = {"users": users, "sessions": sessions, "events": events, "orders": orders,
          "order_items": order_items, "products": products, "sellers": sellers,
          "experiment_assignments": assignments, "marketing_spend": marketing_spend}
for name, df in tables.items():
    df.to_parquet(OUT / f"raw_{name}.parquet", index=False)
    print(f"raw_{name:24s} {len(df):>9,d} rows")
