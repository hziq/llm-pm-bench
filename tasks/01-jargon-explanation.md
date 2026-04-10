---
id: 01-jargon-explanation
title: Domain Jargon Explanation (short output, strong constraint)
type: domain-knowledge
inputs:
  terms:
    - SLI
    - blast radius
    - feature flag
    - canary deployment
    - postmortem
rubric:
  - dimension: Accuracy
    weight: 0.4
    desc: Each definition matches the standard SRE / DevOps usage; no factual errors
  - dimension: Practicality
    weight: 0.3
    desc: Includes a concrete usage scenario or example, not just an abstract definition
  - dimension: Conciseness
    weight: 0.2
    desc: Stays under the word limit; no filler or repetition
  - dimension: Style
    weight: 0.1
    desc: Reads naturally; no awkward phrasing
---

You are a senior SRE / DevOps practitioner. Briefly explain the following terms.
For each term, write a single paragraph (max 100 words) containing both
**definition** and **a typical usage scenario**.

{terms}

Constraints:
- Plain text paragraphs, no tables or code blocks
- Start directly with the definition; no "Here are the explanations..." preamble
- Do not pad with theoretical or historical context
