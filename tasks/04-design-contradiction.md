---
id: 04-design-contradiction
title: Design Contradiction Detection (reasoning)
type: reasoning
inputs: {}
rubric:
  - dimension: Contradiction Detection Accuracy
    weight: 0.40
    desc: Correctly identifies all key conflicts between proposal and baseline; no misses, no false positives
  - dimension: Reasoning Depth
    weight: 0.25
    desc: Explains WHY each item is a contradiction, not just that they differ
  - dimension: Domain Understanding
    weight: 0.20
    desc: Correctly understands the underlying technical concepts (inventory, transactions, eventual consistency)
  - dimension: Structure
    weight: 0.10
    desc: Output is well organized (numbered, tabular, or sectioned), not a wall of prose
  - dimension: Balanced Judgment
    weight: 0.05
    desc: Avoids "the proposal is completely wrong" or "the baseline is wrong" — engages with merits of both
---

You are a senior architect. Below are two documents:

1. **A. Current architectural baseline** (decided 2024-09-15 by the team)
2. **B. A challenge proposal** (mock — argues for rolling back to the legacy flow)

Analyze each item in proposal B against baseline A. For each:

1. **Per-item analysis**: B has 5 arguments. Evaluate each one separately.
2. **For each item, provide**:
   - Conflict verdict: **hard conflict / soft conflict / no conflict**
   - Specific technical description of the conflict (not "these are
     different", but "decision X in A directly contradicts claim Y in B")
   - If accepting B, list which decision numbers in A would need to be rolled back
3. **Final overall judgment**: Is B's direction worth reconsidering?
   1-2 sentences only.
4. Use markdown, one `###` subsection per item.
5. Do not be wishy-washy / non-committal. But also do not blindly side
   with one camp.

---

## A. Current Baseline (excerpt from architectural baseline doc)

{file:inputs/04-contradiction/baseline.md}

---

## B. Challenge Proposal (mock)

{file:inputs/04-contradiction/proposal.md}

---

Begin analysis:
