-- Grain: one row per order. Net revenue excludes cancelled orders (returns are kept; refunds are not modelled).
with orders as (
    select o.*, t.order_lines, t.units, t.item_revenue_eur, t.shipping_eur
    from {{ ref('stg_orders') }} o
    join {{ ref('int_order_totals') }} t using (order_id)
)

select
    *,
    case when order_status = 'cancelled' then 0 else item_revenue_eur end as net_revenue_eur,
    row_number() over (partition by user_id order by order_timestamp, order_id) as user_order_number,
    case when row_number() over (partition by user_id order by order_timestamp, order_id) = 1
         then true else false end as is_first_order
from orders
