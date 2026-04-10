# SQL Debug Scenario

> [Mock scenario — for benchmark purposes only.]

## User Report

**Tenant**: acme_test
**Reported by**: support engineer
**Time**: 2024-10-15 morning
**Symptom**:

> A customer reports that after marking an order as "shipped" in our
> admin panel, the order status is still showing as "processing" on
> the customer-facing page. The shipping notification email also
> didn't go out.
>
> The order ID is `ORD-2024-1014-9921`. It has multiple line items.
> The customer says they clicked "Mark as Shipped" and the admin
> panel said success.

## Database Schema (simplified)

```sql
-- Orders table
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    order_no VARCHAR(64) UNIQUE,         -- public order number
    tenant_id VARCHAR(32),
    status VARCHAR(16),                   -- pending/processing/shipped/delivered/cancelled
    total_amount DECIMAL(10,2),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    deleted BOOLEAN DEFAULT FALSE
);

-- Order line items (one order has many items)
CREATE TABLE order_items (
    id BIGINT PRIMARY KEY,
    order_id BIGINT REFERENCES orders(id),
    sku VARCHAR(64),
    quantity INT,
    fulfilled_qty INT,                    -- how many of this item have shipped
    status VARCHAR(16),                   -- pending/picked/shipped
    is_last_item BOOLEAN,                 -- denormalized: is this the last item to ship for the order?
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    deleted BOOLEAN DEFAULT FALSE
);

-- Shipment events (one item can have multiple events)
CREATE TABLE shipment_events (
    id BIGINT PRIMARY KEY,
    order_item_id BIGINT REFERENCES order_items(id),
    event_type VARCHAR(16),               -- picked/packed/shipped/delivered
    quantity INT,
    actor_id VARCHAR(32),
    event_time TIMESTAMP,
    created_at TIMESTAMP,
    deleted BOOLEAN DEFAULT FALSE
);
```

## Your task

Provide a step-by-step SQL debugging plan with these requirements:

1. Each step should explain the hypothesis you're testing
2. SQL must include `WHERE tenant_id` and `LIMIT`; no full table scans
3. Field names must match the schema exactly; do not invent fields
4. Provide your best guess at the root cause + a fix direction
