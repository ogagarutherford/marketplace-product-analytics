select
    order_id,
    session_id,
    user_id,
    order_timestamp,
    cast(order_timestamp as date) as order_date,
    order_status
from {{ source('raw', 'raw_orders') }}
