---
id: 02-meeting-summary
title: Meeting Transcript → Structured Summary (long input, structured output)
type: long-context-structured-output
inputs: {}
rubric:
  - dimension: Information Completeness
    weight: 0.35
    desc: Captures the core topic, key decisions, and action items; nothing important missed
  - dimension: Structure Compliance
    weight: 0.20
    desc: Follows the required sections (topic / discussion / decisions / action items / open questions); clean formatting
  - dimension: Reasoning Quality
    weight: 0.25
    desc: Correctly identifies trade-offs, conflicting positions, and the rationale behind decisions; no fabricated info
  - dimension: Conciseness
    weight: 0.10
    desc: Distills to decision/action level, no transcript-style quoting
  - dimension: Style
    weight: 0.10
    desc: Natural prose, professional tone
---

You are a product manager's assistant. Below is a real meeting transcript
(may include filler, tangents, or unclear attributions). Distill it into
a structured meeting summary following these rules:

1. **Do not paraphrase line by line**. Compress to the level of decisions,
   actions, and key positions.
2. **Use this exact section structure** (keep the section headers even if empty):
   - 1. Meeting Topic & Context
   - 2. Key Discussion Points (each as a sub-section with positions + tentative conclusion)
   - 3. Decisions (what was decided to do / not do)
   - 4. Action Items (with owner and deadline if identifiable)
   - 5. Open Questions / Items Needing Follow-up
   - 6. Glossary (any acronyms or domain-specific terms used)
3. **Do not invent** information. If owner or deadline is unclear, write "TBD".
4. Output in English, markdown formatted.
5. No "Here is the meeting summary..." preamble. Start directly with the H1 title.

Transcript:

---

{file:inputs/02-meeting/transcript.txt}
