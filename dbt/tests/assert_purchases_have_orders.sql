-- Fails if a session has a purchase event but no order, or an order without a purchase event.
select session_id
from {{ ref('fct_sessions') }}
where (purchased = 1) <> (order_id is not null)
