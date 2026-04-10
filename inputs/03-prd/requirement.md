# Feature Request: Soft Delete & Restore for User Documents

> [Mock requirement — for benchmark purposes only. Replace with your own.]

## Source Tickets

- **CUST-1024 (P1)**: User accidentally deleted a project folder, lost
  3 days of work. Wants ability to undo delete within 24 hours.
- **CUST-1156 (P0)**: Enterprise admin reports an employee deleted
  shared docs before being terminated. Legal needs ability to recover
  even after 30 days.
- **CUST-1190 (P2)**: Mobile users complain delete is permanent and
  there's no warning dialog.
- **Internal feedback (CSM team)**: Top complaint in NPS survey
  Q2 was "no undo for delete". Cited by 18% of detractors.

## What Already Exists

- `documents` table has a `deleted` boolean column (currently set to
  `true` and rows are kept indefinitely — but no UI to view/restore)
- Audit log captures every delete event (action=delete, actor_id, timestamp)
- Mobile app shows a confirmation dialog only on web, not on mobile

## Constraints

- Must not break existing API contracts (third-party integrations rely
  on `GET /documents` returning only non-deleted)
- Storage cost concern: legal mentions GDPR right-to-erasure, so
  "keep forever" is not acceptable for personal data
- Mobile team capacity: limited, only 1 sprint available this quarter

## Open Questions

1. Should restore be self-serve (user clicks undo) or admin-mediated?
2. How long should documents be recoverable? 24h? 30d? 90d? Forever
   for enterprise tier only?
3. Does "delete" mean the same thing for shared docs as for personal
   docs? (Shared doc deleted by one collaborator — what happens to
   the others?)
4. Should the trash/recycle bin be a first-class navigation item or
   hidden in settings?
5. What about deleted folders containing many docs? Restore folder
   restores all? Or one at a time?
