-- Grain: one row per buyer. RFM as of the day after the last order in the data.
-- Frequency uses fixed thresholds (most buyers order once, so quintiles would split ties arbitrarily).
with base as (
    select
        user_id,
        max(order_date)       as last_order_date,
        count(*)              as frequency,
        sum(net_revenue_eur)  as monetary_eur
    from {{ ref('fct_orders') }}
    where order_status <> 'cancelled'
    group by user_id
),

as_of as (
    select max(order_date) + interval 1 day as as_of_date from {{ ref('fct_orders') }}
),

scored as (
    select
        b.*,
        datediff('day', b.last_order_date, a.as_of_date)          as recency_days,
        6 - ntile(5) over (order by datediff('day', b.last_order_date, a.as_of_date))  as r_score,
        case when b.frequency = 1 then 1 when b.frequency = 2 then 3
             when b.frequency = 3 then 4 else 5 end              as f_score,
        ntile(5) over (order by b.monetary_eur)                  as m_score
    from base b cross join as_of a
)

select
    *,
    case
        when r_score >= 4 and f_score >= 4 then 'Champions'
        when f_score >= 4                  then 'Loyal customers'
        when r_score >= 4 and f_score <= 2 then 'New or promising'
        when r_score <= 2 and f_score >= 3 then 'At risk'
        when r_score <= 2                  then 'Hibernating'
        else 'Needs attention'
    end as rfm_segment
from scored
