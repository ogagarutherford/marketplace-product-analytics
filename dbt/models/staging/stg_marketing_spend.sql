select
    cast(spend_date as date)                          as spend_date,
    date_trunc('month', cast(spend_date as date))     as spend_month,
    channel,
    clicks,
    spend_eur
from {{ source('raw', 'raw_marketing_spend') }}
