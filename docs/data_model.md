# Data Model

```mermaid
erDiagram
    DIM_USER ||--o{ FCT_SESSIONS : user_id
    DIM_DATE ||--o{ FCT_SESSIONS : session_date
    FCT_SESSIONS ||--o{ FCT_EVENTS : session_id
    FCT_SESSIONS ||--o| FCT_ORDERS : session_id
    FCT_ORDERS ||--o{ FCT_ORDER_ITEMS : order_id
    DIM_PRODUCT ||--o{ FCT_ORDER_ITEMS : product_id
    DIM_SELLER ||--o{ DIM_PRODUCT : seller_id
    DIM_USER ||--o| FCT_EXPERIMENT_ASSIGNMENTS : user_id
```

| Table | Grain |
|---|---|
| `fct_sessions` | One row per session, with funnel flags (viewed, carted, checked out, purchased) and time to purchase |
| `fct_events` | One row per event (session_start, view_item, add_to_cart, begin_checkout, purchase) |
| `fct_orders` | One row per order: status, item revenue, shipping, item count |
| `fct_order_items` | One row per order line: product, seller, quantity, price |
| `fct_experiment_assignments` | One row per user in the experiment: variant and first exposure time |
| `dim_user` | One row per user: country, acquisition channel, primary device, first visit |
| `dim_product`, `dim_seller` | Catalogue and seller attributes |
| `dim_date` | Calendar |

The session fact is the core of the funnel analysis; the user-level experiment table drives the A/B test.
