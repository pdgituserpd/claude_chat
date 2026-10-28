# Research loop orchestrator (rlo)

A small command-line program that runs the automated parts of the research process and
stops wherever a human must decide. Claude authors with tools; a second model family
reviews without tools; two rounds; what is still disputed is routed to a coded test, to
the human gate, or to a blinded judge. Git is the database: every model call, every
round, every checklist and every log entry is a file in the target research repository.

This repository is the tool. A research repository (first target:
`pdgituserpd/auditable-research-loop`) is where it runs and writes.

## Status

Keep these apart.

**Done (runs, tested without spending tokens):**
- Stage 2 (measures) end to end with canned models: author, review round 1, author
  responses, review round 2, dispute routing, run log, gate checklist, pause, approve,
  decision log, judgment log, snapshot.
- Dispute routing: checkable error findings go to a coded test and the result decides;
  judgment findings go to the human gate with both positions; the rest go to a blinded
  judge with positions labelled A/B in random order, and the log records which family the
  judge sided with.
- A finding settled against the author that the author still rejects is escalated to the
  gate instead of being dropped.
- Budgets: the author stops and reports when it exceeds the model-call or tool-call cap.
- Sign-off rule: a re-run whose output fingerprints are identical is logged as auto
  signed off; a change in any fingerprint is logged as waiting for the human.
- Eleven tests (`python -m unittest discover -s tests`), all passing.

**Shown (written, not yet exercised against a live API):**
- `src/rlo/models/claude.py`: Claude as author (manual tool loop over the Messages API
  with four sandboxed tools) and as blinded judge (fresh conversation, structured output).
- `src/rlo/models/openai_reviewer.py`: the second family as reviewer, structured findings.
- The three prompts under `prompts/`. They are generic placeholders; the real ones stay private.

**Proposed (not built):**
- Stages 1, 3 and 4. Only `stages/stage2_measures.toml` exists.
- The full checking layers inside a stage (fast/slow build, blind rebuild, fake cases,
  rules, planted bugs, catch matrix). The loop can call them once they exist in the target.
- A render of the JSONL logs into the prototype repository's own log formats.
- Planting one known bug in every review batch to check the reviewer is awake.

## How it runs

```
rlo run     --target <repo> --stage stage2_measures --variable new_classes
rlo status  --target <repo> --logs 5
rlo approve --target <repo> --stage stage2_measures --variable new_classes --by Pouya
rlo reset   --target <repo> --stage stage2_measures --variable new_classes
```

`run` ends in one of three states: `waiting_human` (a checklist was written under
`gates/` in the target repo), `done` (an automatic gate signed off), or `stopped`
(budget exceeded; the state file says where).

`approve` refuses while any `Choice:` line in the checklist is empty. It then writes one
decision-log entry per item, one judgment-log entry for the gate, and a snapshot of the
stage's outputs.

A dry run with canned models, no keys needed:

```
cp -r examples/target_min /tmp/t
PYTHONPATH=src python -m rlo.cli run --target /tmp/t --stage stage2_measures \
  --variable new_classes --models fixtures --fixture tests/fixtures/stage2_happy.json
cat /tmp/t/gates/stage2_measures_new_classes.md
```

## What lands in the target repository

| Path | What |
|---|---|
| `.rlo/calls/*.json` | one raw record per model call: request, response, usage |
| `.rlo/rounds/*.json` | author output, findings and responses per round, resolution report |
| `.rlo/state_*.json` | where each stage/variable is |
| `.rlo/snapshots/*.json` | approved output fingerprints |
| `gates/<stage>_<variable>.md` | the checklist the human fills in |
| `logs/decision_log.jsonl` | one line per open choice: options, AI default, choice, overruled, reason, precedent, decided by |
| `logs/judgment_log.jsonl` | one line per gate: proposed, chosen, overruled |
| `logs/change_log.jsonl` | re-runs with identical or changed fingerprints |
| `logs/run_log.jsonl` | time, git commit, input and output fingerprints, settings, check counts |
| `logs/dispute_log.jsonl` | every surviving dispute: route, outcome, whether the judge sided with its own family |

Logs are built by the program from its own records, never from a model's summary.

## Layout

```
src/rlo/
  cli.py          run | status | approve | reset
  config.py       stage files under stages/ (TOML)
  loop.py         the stage loop and approve
  resolve.py      dispute routing and blinding
  gate.py         checklist render and parse
  logs.py         JSONL log writers with unique ids
  fingerprint.py  sha256 of outputs; sign-off comparison
  tools.py        sandboxed list/read/write/run for the author
  calls.py        raw call records
  state.py        .rlo/ store
  models/         base schemas, fixtures, claude, openai_reviewer
stages/           one TOML per stage
prompts/          author, reviewer, judge (generic)
tests/            unit and end-to-end tests with fixtures
examples/target_min/  a two-file stand-in for a research repo
```

## Requirements

Python 3.11 or newer. Core has no dependencies. Live runs need
`pip install anthropic openai` and the keys `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`.
Not OS-specific; paths go through `pathlib`, no shell scripts.

## Design decisions

- Claude does not judge disputes about Claude's work by default. Checkable disputes are
  settled by a test the author writes and runs; the test must be able to fail. Judgment
  calls are the human's. Only the residue goes to a judge, blinded, and the own-family
  rate is logged so the judge can be swapped if it runs high.
- The human approves by exception. Every open choice carries an AI default with its
  precedent, so a gate is one sitting, but the log records the human as decider on every
  item and counts how often the default was overruled.
- One session owns a target repository at a time. The orchestrator never rebases or
  force-pushes; it only writes files and leaves committing to the owner.
