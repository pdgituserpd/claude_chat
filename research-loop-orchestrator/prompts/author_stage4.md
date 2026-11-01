Stage 4, results, paper id `{{variable}}`.

1. Read the plan under `plan/`, the design under `design/`, the outputs under `results/` and `output/`, and the change log. Check every number, sign, unit and claim in any results summary against the tables themselves.
2. Write `results/{{variable}}_report.md`: what was found against each hypothesis in the plan, with the table and column each number comes from; every change made since the plan, each sorted into a class (correction, validity repair, choice among defensible options, exploratory addition, theory change) with its timing relative to seeing results; and your proposed call for this round with reasons: go, recycle (state the reason that does not depend on the result), hold, or kill.
3. Write `results/{{variable}}_choices.json` in the gate format. Include:
   - id "CALL": item "The round's call", options ["go", "recycle", "hold", "kill"], no default, precedent_type "none", reason = your proposal and why.
   - for each change since the plan, id "CHANGE-<n>-EITHER-WAY": item "<change>: would you make this change if the result had gone the other way?", options ["yes", "no"], no default; and id "CHANGE-<n>-CAN-FAIL": item "<change>: can the test still fail?", options ["yes", "no"], no default.
   - for any a priori hypothesis that is not supported, id "HYP-<n>": item "<hypothesis>: how to report it", options ["report as not supported", "other"], default "report as not supported", precedent "the plan", precedent_type "direct".
4. Stop. The call is the human's.
