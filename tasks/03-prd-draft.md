---
id: 03-prd-draft
title: PRD Draft Generation (instruction following + long output)
type: instruction-following-long-output
inputs: {}
rubric:
  - dimension: Domain Understanding
    weight: 0.30
    desc: Truly understands the product context; doesn't just apply a generic PRD template
  - dimension: Structure Compliance
    weight: 0.20
    desc: Follows the required sections; each section has substantive content
  - dimension: Source Reuse
    weight: 0.20
    desc: Effectively uses customer signals, existing implementation, and open questions from the source material
  - dimension: Practicality
    weight: 0.20
    desc: The output can serve as a real starting point for review (not just placeholders)
  - dimension: Conciseness
    weight: 0.10
    desc: No fluff, no header-stacking
---

You are a product manager. Below is a feature request with source tickets,
existing implementation, constraints, and open questions. Write an
**initial PRD draft** that can serve as the starting point for design review.

Requirements:
1. **Do not just reformat the source material**. Synthesize it into a
   PRD framework that teammates can review.
2. **Required sections**:
   - 1. Background & Target Users
   - 2. Core Scenarios (3-5 scenarios, each with trigger / current pain / desired state)
   - 3. Scope (what's in / what's explicitly out)
   - 4. Key Design Decisions (for each open question, give your initial position or two-option comparison)
   - 5. Relationship to Existing Functionality (what existing modules are affected)
   - 6. Open Items Needing Alignment (specific roles to involve, specific things to confirm)
3. **Section 4 is the highest-value part**: for each open question in
   the source, do not just restate the question. Give a 1-2 sentence
   recommendation OR a comparison of two options.
4. **Use correct domain terms** for the feature area.
5. No "Here is the PRD..." preamble; start directly with the H1 title.
6. Output in English, markdown formatted.

Source material:

---

{file:inputs/03-prd/requirement.md}
