-- Fails if order-level revenue does not add up to the order lines.
select
    (select sum(item_revenue_eur) from {{ ref('fct_orders') }})      as order_level,
    (select sum(item_revenue_eur) from {{ ref('stg_order_items') }}) as line_level
where abs((select sum(item_revenue_eur) from {{ ref('fct_orders') }})
        - (select sum(item_revenue_eur) from {{ ref('stg_order_items') }})) > 0.01
