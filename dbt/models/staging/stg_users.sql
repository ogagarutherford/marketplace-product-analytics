select
    user_id,
    cast(first_visit_date as date)                 as first_visit_date,
    date_trunc('month', cast(first_visit_date as date)) as first_visit_month,
    country,
    acquisition_channel,
    primary_device
from {{ source('raw', 'raw_users') }}
