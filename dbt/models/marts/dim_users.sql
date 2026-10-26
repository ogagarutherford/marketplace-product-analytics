-- Grain: one row per user, with lifetime order summary (cancelled orders excluded).
with buyers as (
    select
        user_id,
        min(order_timestamp)                        as first_order_ts,
        count(*)                                    as orders,
        sum(net_revenue_eur)                        as lifetime_revenue_eur
    from {{ ref('fct_orders') }}
    where order_status <> 'cancelled'
    group by user_id
)

select
    u.*,
    b.first_order_ts,
    cast(b.first_order_ts as date)                          as first_order_date,
    date_trunc('month', cast(b.first_order_ts as date))     as first_order_month,
    coalesce(b.orders, 0)                                   as orders,
    coalesce(b.lifetime_revenue_eur, 0)                     as lifetime_revenue_eur,
    b.user_id is not null                                   as is_buyer
from {{ ref('stg_users') }} u
left join buyers b using (user_id)
