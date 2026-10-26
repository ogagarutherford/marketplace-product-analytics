-- One row per order: item count, item revenue and shipping.
select
    order_id,
    count(*)                 as order_lines,
    sum(quantity)            as units,
    sum(item_revenue_eur)    as item_revenue_eur,
    sum(shipping_fee_eur)    as shipping_eur
from {{ ref('stg_order_items') }}
group by order_id
