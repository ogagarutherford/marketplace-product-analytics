-- Fails if a session reached a later funnel step without the earlier ones.
select *
from {{ ref('fct_sessions') }}
where (purchased = 1 and began_checkout = 0)
   or (began_checkout = 1 and added_to_cart = 0)
   or (added_to_cart = 1 and viewed_item = 0)
