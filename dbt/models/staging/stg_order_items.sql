select
    order_id || '_' || cast(order_item_seq as varchar) as order_item_id,
    order_id,
    order_item_seq,
    product_id,
    seller_id,
    quantity,
    unit_price_eur,
    shipping_fee_eur,
    quantity * unit_price_eur as item_revenue_eur
from {{ source('raw', 'raw_order_items') }}
