Stage 2, measures, variable `{{variable}}`.

1. Read `spec/` and anything under `literature/`. Find the precedent for this variable. Rule: use a direct precedent if one exists, otherwise the closest one, and only then the most reasonable measure. Say which case applies and cite the source. Check how prior papers handled each data linkage before proposing one.
2. Write `spec/{{variable}}_definition.md`: a plain-words definition that a separate agent could rebuild the variable from without seeing any code. Mark every point where a choice had to be made.
3. Write `spec/{{variable}}_keys.json` as {"key": ["<unit id column>", "<time column>"]}: the columns that identify one row of the output.
4. Write `spec/{{variable}}_choices.json` with this exact shape:
   {"variable": "{{variable}}", "choices": [{"id": "C1", "item": "...", "options": ["...", "..."], "default": "...", "precedent": "...", "precedent_type": "direct|closest|none", "reason": "..."}]}
   List every open choice: window edges, filing vs grant year, first-listed vs all codes, empty cases, panel edges, duplicates, missing values, sample filters, linkage rules, and the source-check sample size (always include this one, options 100 and 300). Fill `default` only when `precedent_type` is "direct", citing the paper; the precedent rule already decides those. With "closest" or "none", leave `default` empty and give the reasons for each option instead. Also include one choice with id "KEY" asking whether this variable is key or a control.
5. Stop when the files are written and consistent. Do not build code in this stage.
