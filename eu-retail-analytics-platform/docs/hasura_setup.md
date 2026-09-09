# Hasura quick setup

1. Open http://localhost:8085  
2. Admin secret: `adminsecret` (from compose; change in prod)  
3. Data → Track All for schema `oltp`  
4. Add suggested relationships:
   - `orders.customer_id` → `customers.customer_id`
   - `orders.store_id` → `stores.store_id`
   - `order_items.order_id` → `orders.order_id`
   - `order_items.product_id` → `products.product_id`
   - `payments.order_id` → `orders.order_id`

## Sample GraphQL

```graphql
query RecentOrders {
  oltp_orders(limit: 10, order_by: {order_ts: desc}) {
    order_number
    order_status
    order_ts
    currency_code
    customer {
      full_name
      country_code
    }
    order_items {
      quantity
      line_total
      product {
        product_name
        category
      }
    }
  }
}
```

Export metadata later:

```bash
# from hasura CLI if installed
hasura metadata export --project infra/hasura
```
