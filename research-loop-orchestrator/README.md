# Research loop orchestrator (rlo)

A small command-line program that runs the automatic parts of the research process and stops
wherever a human must decide. Claude authors with tools; a second model family reviews without
tools; two rounds; what is still disputed goes to a coded test, to the human gate, or to a
blinded judge. Git is the database: every model call, every round, every checklist and every
log entry is a file in the target research repository.

This repository is the tool. A research repository (first target:
`pdgituserpd/auditable-research-loop`) is where it runs and writes.

## Status

Keep these apart.

**Done (runs, tested here without spending tokens or calling either program):**
- A step engine. A stage is an ordered list of steps in a config file (`stages/*.toml`):
  `task`, `check`, `compare`, `planted_bugs`, `human`, `snapshot`. Progress is saved after
  every model call and every check, so an interrupted run (budget, rate limit, crash, manual
  hand-off) resumes where it stopped.
- Stages 1 to 4 and the two build stages as configs with prompts: `stage1_question`,
  `stage2_measures`, `build_variable` (full checks for a key variable), `build_control`
  (light checks), `stage3_design` (with the dated plan), `stage4_results` (hostile review,
  change classification, the round's call, the two-recycles-then-kill-review house rule).
- The review loop: structured findings, author responses, a second round on rejections.
- Dispute routing. Checkable errors: the author writes a test and a copy of the file carrying
  the claimed error; the test counts only if it fails on that copy and the reviewer confirms
  the copy carries its claim; then its result on the real file decides. Judgment calls go to
  you with both positions. The rest go to a blinded judge, order randomized, own-family rate
  logged. A settled finding the author still rejects is escalated to the gate.
- Gates with the direct-precedent default rule: an AI default is shown only where a direct
  published precedent decides the item; otherwise no default, you choose. Every item needs an
  explicit choice; the log records accepted-default, overruled-default and chose separately.
- The build layers as engine steps: blind rebuild by the builder role in an isolated folder
  that holds only the definition, keys and data; row-by-row CSV comparison on the unit key;
  coded checks the author must fix at the root when they fail (never the check itself);
  planted bugs drawn from the error log by the planter role, approved by you, each run
  through every layer in a copy of the repo, with a catch matrix in `report/`; escaped bugs
  get one check-adding round, then a gate item.
- Logs as JSON lines with unique ids: decision, judgment, change, run (with software
  versions), dispute, error (silent errors only, the three tests enforced), stopped papers,
  and `rlo counts` for rates.
- Three transports behind the same roles: `cli` (subscriptions, below), `manual` (paste
  into any chat window), `fixtures` (tests). 24 tests, all passing.

**Shown (written, not yet exercised against the real thing):**
- `cli` mode: `src/rlo/models/cli.py` drives Claude Code (`claude -p`) for author, builder,
  planter and judge, and Codex (`codex exec`) for the reviewer. Tested only against stand-in
  executables that produce the same output shapes. Real flags live in `cli_settings.toml`.
- `api` mode: the Anthropic and OpenAI SDK adapters.
- The prompts under `prompts/`. Generic placeholders; the real ones stay private.
- The build stage assumes R scripts at fixed paths (see `stages/build_variable.toml`). The
  test runs a Python stand-in because R is not installed here.

**Proposed (not built):**
- A tool-using Codex adapter, so the blind rebuild runs on the other family. Today the
  builder runs on Claude Code with a different model in an isolated folder.
- Rendering the JSON-line logs into the prototype repository's own log formats.
- The capture-recapture floor and cross-generation known-answer tasks from the process doc.

## Running it

```
rlo run     --target <repo> --stage stage2_measures --variable new_classes
rlo approve --target <repo> --stage stage2_measures --variable new_classes --by Pouya
rlo status  --target <repo> --logs 5
rlo reset   --target <repo> --stage stage2_measures --variable new_classes
rlo ingest  --target <repo> --stage ... --variable ... --file reply.json     (manual mode)
rlo log-error / log-stop / counts --target <repo>
```

`--mode cli` is the default (subscriptions). `--mode manual` writes a bundle under
`.rlo/manual/` for you to paste into a chat window and stops; save the reply as JSON next to
it (or `rlo ingest` it) and run again. `--mode api` uses keys. `--mode fixtures` is for tests.

`run` ends in one of: `waiting_human` (a checklist under `gates/`; fill it in, then
`rlo approve`, which logs the decisions and continues the stage), `waiting_manual`,
`stopped` (budget, failed check after fixes, or you chose stop; fix and run again), `done`.

Dry run, no keys, no programs:

```
cp -r examples/target_min /tmp/t
PYTHONPATH=src python -m rlo.cli run --target /tmp/t --stage stage2_measures --variable new_classes \
  --mode fixtures --fixture tests/fixtures/stage2.json
cat /tmp/t/gates/stage2_measures_new_classes_gate2.md
```

Tests: `PYTHONPATH=src:. python -m unittest discover -s tests -t .`

## Subscription mode

Both programs must be installed and signed in on the machine that runs `rlo`:
Claude Code under the Claude subscription, Codex under the ChatGPT subscription. Each call is
a fresh non-interactive session started in the work folder. The prompt goes in on standard
input, the full output is saved as the raw call record, and the structured record is read
from a file the agent writes (Claude Code) or from the last message (Codex). Flags differ
between versions: edit `cli_settings.toml` if yours do. Subscriptions meter use in rolling
windows; a run that hits the cap stops and resumes with the next `rlo run`.

## What lands in the target repository

| Path | What |
|---|---|
| `.rlo/calls/*.json` | one raw record per model call |
| `.rlo/rounds/*.json` | task results, findings, responses, fixes per step |
| `.rlo/state_*.json` | where each stage/variable is, with resumable progress |
| `.rlo/work/` | isolated folders for blind rebuilds and planted-bug copies |
| `.rlo/manual/` | manual-mode bundles and answers |
| `.rlo/snapshots/*.json` | approved output fingerprints |
| `gates/*.md` | checklists you fill in |
| `report/` | comparison reports, planted bug lists, catch matrices |
| `logs/*.jsonl` | decision, judgment, change, run, dispute, error, stopped-papers |

## Path conventions in a target repository

`spec/<v>_definition.md`, `spec/<v>_keys.json` (`{"key": [...]}`), `spec/<v>_choices.json`;
`R/<v>_fast.R` and `R/<v>_slow.R` writing `output/<v>_fast.csv` and `output/<v>_slow.csv`;
`python/<v>_blind.py` writing `output/<v>_blind.csv`; `tests/<v>_{fake_cases,rules,data_checks,source_check}.R`
each exiting non-zero on failure; `report/<v>_planted_bugs.json`. Stages 1, 3 and 4 use
`question/`, `design/` + `plan/`, and `results/` with `<paper id>` as the variable.

## Layout

```
src/rlo/
  cli.py          commands and the role factory for each mode
  engine.py       the step engine, review loop, dispute routing, gates, planted bugs
  config.py       stage files (TOML) -> Step/StageConfig; {{variable}} substitution
  checks.py       command runner, CSV comparison, dispute tests, repo copies
  gate.py         checklist render/parse, the default rule
  logs.py         JSONL writers, software versions, counts
  fingerprint.py  sha256 of outputs; sign-off comparison
  tools.py        sandboxed tools and the one command allow-list
  calls.py        raw call records
  state.py        .rlo/ store
  models/         base schemas and protocols; prompts shared by adapters;
                  fixtures, manual, cli (subscriptions), claude + openai_reviewer (API)
stages/           one TOML per stage
prompts/          one Markdown file per role and stage
tests/            unit and end-to-end tests with fixtures and a Python stand-in build stage
examples/         two tiny target repositories used by the tests
```

Python 3.11 or newer; the core has no dependencies. `api` mode needs `pip install anthropic openai`.
