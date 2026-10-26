select seller_id, seller_country, seller_tier, cast(joined_date as date) as joined_date
from {{ source('raw', 'raw_sellers') }}
