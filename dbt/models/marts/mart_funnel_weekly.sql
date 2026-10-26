-- Grain: week x device x channel x visitor type. Sum the counts to any level, then divide;
-- never average pre-computed rates (mix changes can reverse trends: Simpson's paradox).
select
    session_week,
    device,
    channel,
    visitor_type,
    count(*)              as sessions,
    sum(viewed_item)      as viewed_item,
    sum(added_to_cart)    as added_to_cart,
    sum(began_checkout)   as began_checkout,
    sum(purchased)        as purchased,
    sum(net_revenue_eur)  as net_revenue_eur
from {{ ref('fct_sessions') }}
group by 1, 2, 3, 4
