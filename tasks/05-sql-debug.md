---
id: 05-sql-debug
title: SQL Debug Plan (code generation + domain reasoning)
type: code-generation-with-domain
inputs: {}
rubric:
  - dimension: SQL Correctness
    weight: 0.30
    desc: Syntax valid, field names match schema, JOIN relationships correct, queries are runnable
  - dimension: Debugging Approach
    weight: 0.30
    desc: Steps are logical (broad to narrow, hypothesis-driven); each step's purpose is clear
  - dimension: Domain Understanding
    weight: 0.20
    desc: Correctly understands the order/item/shipment state machine and how completion propagates
  - dimension: Safety Compliance
    weight: 0.10
    desc: Every query includes tenant_id filter and LIMIT; follows the prompt's safety rules
  - dimension: Root Cause Hypothesis
    weight: 0.10
    desc: The proposed root cause and fix direction are plausible and actionable
---

You are a senior product engineer doing SQL debugging. Below is a real
customer issue with database schema. Provide a debugging plan following
these rules:

1. **Step by step**: Each step starts with a one-sentence hypothesis,
   then the SQL.
2. **SQL must**:
   - Include `WHERE tenant_id = 'acme_test'` filter
   - Include `LIMIT` (even when you expect few results)
   - Use exact field names from the schema; do not invent fields
   - Use markdown code blocks tagged with `sql`
3. **Top-down**: Confirm the order status first, then items, then shipment events.
4. **Do not dump all SQL at once**. Each step should depend on what
   you'd find from the previous step. **Do not fabricate query results
   to drive your next step** — write hypotheses, not assumed outcomes.
5. **At the end, provide**:
   - **Most likely root cause** (1-2 sentences)
   - **Fix direction** (not "contact engineering", but specifics like
     "verify whether is_last_item is set correctly during item creation")
6. Output in English, markdown formatted.

---

{file:inputs/05-sql/scenario.md}
