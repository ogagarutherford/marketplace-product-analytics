-- Grain: first-visit month x acquisition channel.
-- new_buyers_30d counts users who bought within 30 days of their first visit; months without a full
-- 30-day window are flagged. Paid CAC (proxy) = paid spend in the month / new buyers in 30 days.
with users as (
    select
        first_visit_month,
        acquisition_channel,
        count(*) as new_users,
        sum(case when first_order_date is not null
                  and first_order_date <= first_visit_date + interval 30 day then 1 else 0 end) as new_buyers_30d
    from {{ ref('dim_users') }}
    group by 1, 2
),

spend as (
    select spend_month, channel, sum(spend_eur) as paid_spend_eur
    from {{ ref('stg_marketing_spend') }}
    group by 1, 2
)

select
    u.first_visit_month,
    u.acquisition_channel,
    u.new_users,
    u.new_buyers_30d,
    u.new_buyers_30d * 1.0 / nullif(u.new_users, 0)                 as buyer_rate_30d,
    s.paid_spend_eur,
    s.paid_spend_eur / nullif(u.new_buyers_30d, 0)                  as paid_cac_eur,
    u.first_visit_month + interval 1 month + interval 30 day
        <= (select max(session_date) from {{ ref('fct_sessions') }}) + interval 1 day as full_window_observed
from users u
left join spend s
    on s.spend_month = u.first_visit_month and s.channel = u.acquisition_channel
