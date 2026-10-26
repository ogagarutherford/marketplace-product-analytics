select p.*, s.seller_country, s.seller_tier
from {{ ref('stg_products') }} p
left join {{ ref('stg_sellers') }} s using (seller_id)
