-- Grain: one row per session, with funnel flags, time to purchase and attributed order revenue.
select
    s.session_id,
    s.user_id,
    s.session_start,
    s.session_date,
    date_trunc('week', s.session_date)                              as session_week,
    s.channel,
    s.device,
    case when s.is_returning then 'returning' else 'new' end        as visitor_type,
    u.acquisition_channel,
    u.country,
    1                                                               as session_count,
    f.viewed_item,
    f.added_to_cart,
    f.began_checkout,
    f.purchased,
    datediff('second', f.session_start_ts, f.purchase_ts) / 60.0    as minutes_to_purchase,
    o.order_id,
    coalesce(o.net_revenue_eur, 0)                                  as net_revenue_eur
from {{ ref('stg_sessions') }} s
join {{ ref('int_session_funnel') }} f using (session_id)
join {{ ref('stg_users') }} u using (user_id)
left join {{ ref('fct_orders') }} o using (session_id)
