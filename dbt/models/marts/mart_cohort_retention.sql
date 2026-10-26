-- Grain: first-purchase month cohort x months since first purchase.
-- A buyer is active in a month if they placed a non-cancelled order in it.
with orders as (
    select o.user_id, date_trunc('month', o.order_date) as order_month, u.first_order_month
    from {{ ref('fct_orders') }} o
    join {{ ref('dim_users') }} u using (user_id)
    where o.order_status <> 'cancelled'
),

activity as (
    select distinct
        first_order_month,
        user_id,
        datediff('month', first_order_month, order_month) as months_since_first_order
    from orders
),

cohorts as (
    select first_order_month, count(distinct user_id) as cohort_buyers
    from activity group by 1
)

select
    a.first_order_month,
    a.months_since_first_order,
    c.cohort_buyers,
    count(distinct a.user_id)                                 as active_buyers,
    count(distinct a.user_id) * 1.0 / c.cohort_buyers         as retention_rate
from activity a
join cohorts c using (first_order_month)
group by 1, 2, 3
