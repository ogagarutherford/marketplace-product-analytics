select product_id, category, seller_id, list_price_eur, avg_rating
from {{ source('raw', 'raw_products') }}
