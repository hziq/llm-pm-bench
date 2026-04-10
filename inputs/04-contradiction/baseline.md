# Architectural Baseline (excerpt)

> [Mock baseline document — for benchmark purposes only.]

## Section 4.0 New Model: "Reserve-Then-Confirm" Order Flow (decided 2024-09-15)

> **⚠️ Major change: 2024-09-15** — flow flipped from
> "validate-then-charge" to "reserve-then-confirm". Sections 4.1–4.8
> describe the legacy flow and are kept for historical reference only.

**Core change**: When a customer clicks "Place Order", the backend
immediately creates a **soft reservation** in inventory and locks the
payment intent. Only after both reservation AND payment intent
succeed do we transition to "confirmed". The frontend shows
"reserving..." for at most 3 seconds.

**Data flow:**

```
User clicks Place Order
    ↓
Backend creates soft_reservation row (TTL = 90s)
    ↓
Backend creates payment_intent (Stripe)
    ↓
Both succeed → state = "confirmed", reservation becomes hard
Either fails → state = "rolled_back", reservation released
    ↓
Customer sees confirmation OR error
```

**Key decisions (2024-09-15 meeting):**

| # | Decision |
|---|---|
| 1 | Soft reservation is the source of truth for "is this item still available", NOT the inventory count column |
| 2 | Reservation TTL is 90 seconds; not configurable per SKU in v1 |
| 3 | Payment intent and reservation are created in parallel (not sequential) to minimize latency |
| 4 | Failed payments do NOT auto-retry; user must re-click Place Order |
| 5 | Inventory count column is updated by a background reconciler every 5 seconds, NOT in the order transaction path |
| 6 | Cancellations within 90s are free; after that, normal cancel rules apply |
| 7 | Anti-abuse: same user cannot hold more than 5 active reservations across all SKUs |
| 8 | Reservation IDs are exposed to frontend so users can see "your reservation expires in N seconds" |
| 9 | Audit log captures reservation create/expire/confirm/rollback events; retention = 30 days |
| 10 | Emergency manual override: ops can mark a reservation as "force_release" via admin tool |

**Comparison to legacy "validate-then-charge":**

| Aspect | Old (validate-then-charge) | New (reserve-then-confirm) |
|---|---|---|
| Inventory consistency | Read-then-decrement, race conditions possible | Reservation row, atomic |
| Payment timing | After inventory decrement | Parallel to reservation |
| User wait time | Often 5-8 seconds | Capped at 3 seconds |
| Oversells under flash sale | Common | Rare (TTL-bounded) |
