-- One row per session: which funnel steps were reached, and when.
select
    session_id,
    max(case when event_name = 'view_item'      then 1 else 0 end) as viewed_item,
    max(case when event_name = 'add_to_cart'    then 1 else 0 end) as added_to_cart,
    max(case when event_name = 'begin_checkout' then 1 else 0 end) as began_checkout,
    max(case when event_name = 'purchase'       then 1 else 0 end) as purchased,
    min(case when event_name = 'session_start'  then event_timestamp end) as session_start_ts,
    min(case when event_name = 'purchase'       then event_timestamp end) as purchase_ts
from {{ ref('stg_events') }}
group by session_id
