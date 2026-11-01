Stage 3, statistical design, paper id `{{variable}}`.

1. Read the question under `question/`, the approved definitions under `spec/`, and the decision log. Propose the main model, the estimator, the robustness plan and the kill criteria. Name every assumption that must hold in this data (for example how an instrument is actually assigned). Do not reach for an impressive method when a standard one fits.
2. Write `design/{{variable}}_design.md` with those sections.
3. Write `plan/{{variable}}_plan.md`, dated today: the question; the hypotheses with their direction; the main measure for each key variable with its precedent; the main model and the planned robustness checks; the kill criteria; what has already been seen of the data. Go through the Wicherts et al. (2016) list of researcher choices and state each one.
4. Write `design/{{variable}}_choices.json` in the gate format ({"variable": ..., "choices": [{"id", "item", "options", "default", "precedent", "precedent_type", "reason"}]}): one item per design choice that has more than one defensible option (fixed effects, clustering, sample window, treatment of outliers, the kill thresholds). Defaults only where a direct precedent decides it.
5. Stop.
