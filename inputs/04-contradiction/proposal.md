# Challenge Proposal (mock — for benchmark purposes only)

## Proposal: Roll back the "reserve-then-confirm" model in favor of the legacy flow

I want to argue we should revert the 2024-09-15 decision and go back
to "validate-then-charge". Here's why:

1. **Reservation TTL adds latency to legitimate users**: 90 seconds
   is too short for users on slow connections. Many drop off when
   they see "your reservation expires in 30 seconds" anxiety
   messaging. Let's go back to no reservations.

2. **Inventory count column is the natural source of truth**: Every
   downstream system (search, recommendations, warehouse) reads from
   the inventory count column. Having reservations as a separate
   source of truth creates a consistency lag and confuses people.

3. **Parallel payment creation is risky**: If payment fails AFTER
   reservation creates, we've held inventory for 90 seconds for
   nothing. Better to validate inventory FIRST, then charge — the
   sequential approach is simpler.

4. **Background reconciler hides bugs**: A 5-second reconciler
   between reservation and inventory count means there's always a
   window where the count is wrong. This violates principle of
   least surprise. Let's update inventory count synchronously in
   the order transaction.

5. **Reservation expiry timer in the UI is bad UX**: Showing users
   a countdown adds anxiety and lowers conversion. Real e-commerce
   sites don't show this.
