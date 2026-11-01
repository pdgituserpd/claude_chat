Stage 1, research question, paper id `{{variable}}`.

1. Read the master literature files under `literature/`. Brainstorm candidate research questions. For each, score contribution potential: what gap it fills, which papers it sits beside, what data it needs, and the main risk.
2. Write `question/{{variable}}_candidates.md`: one section per candidate (id Q1, Q2, ...), with the scores and the papers it draws on. Do not invent citations; cite only rows in the literature files.
3. Write `question/{{variable}}_choices.json`:
   {"variable": "{{variable}}", "choices": [{"id": "QUESTION", "item": "Which research question to pursue", "options": ["Q1", "Q2", "..."], "default": "", "precedent": "not stated", "precedent_type": "none", "reason": "<one line per candidate on why it could be the pick>"}]}
   A research question is a judgment call: give no default. Add further choices only if a candidate carries a choice the human must settle before stage 2.
4. Stop. Picking is the human's job.
