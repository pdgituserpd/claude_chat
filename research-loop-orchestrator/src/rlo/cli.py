"""Command line: rlo run | approve | status | reset | ingest | log-error | log-stop | counts."""

from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from pathlib import Path

from .calls import CallLog
from .config import StageConfig, load_stage
from .engine import Engine, Roles, approve_stage
from .state import Store

MODES = ("cli", "api", "manual", "fixtures")


def build_roles(mode: str, cfg: StageConfig, store: Store, calls: CallLog, fixture: str | None = None) -> Roles:
    rp, jp = cfg.prompt_text(cfg.reviewer_prompt), cfg.prompt_text(cfg.judge_prompt)
    tool_system = ("You are a careful research engineer working inside one folder. Use plain words. Do not invent "
                   "citations. When unsure, say so in the files you write.")
    if mode == "fixtures":
        from .models.fixtures import FixtureJudge, FixtureReviewer, FixtureToolAgent, load_fixture

        spec = load_fixture(Path(fixture))
        return Roles(author=FixtureToolAgent(spec, calls, "author"), reviewer=FixtureReviewer(spec, calls),
                     judge=FixtureJudge(spec, calls), builder=FixtureToolAgent(spec, calls, "builder"),
                     planter=FixtureToolAgent(spec, calls, "planter"))
    if mode == "manual":
        from .models.manual import ManualJudge, ManualReviewer, ManualToolAgent

        md = store.manual_dir
        return Roles(author=ManualToolAgent(calls, md, tool_system, "author"), reviewer=ManualReviewer(calls, md, rp, "reviewer"),
                     judge=ManualJudge(calls, md, jp, "judge"), builder=ManualToolAgent(calls, md, tool_system, "builder"),
                     planter=ManualToolAgent(calls, md, tool_system, "planter"))
    if mode == "cli":
        from .models.cli import ClaudeCLIAgent, ClaudeCLIJudge, CodexCLIReviewer, load_settings

        s = load_settings()
        out = store.work_dir / "cli_out"
        mk = lambda role: ClaudeCLIAgent(cfg.model(role), calls, tool_system, role, cfg.budget.max_tool_calls, s, out)  # noqa: E731
        # The builder is the other family. With two subscriptions that is Codex with tools; until a tool-using
        # Codex adapter is tested, the builder runs on Claude Code with a different model and an isolated folder.
        return Roles(author=mk("author"), reviewer=CodexCLIReviewer(cfg.model("reviewer"), calls, rp, store.work_dir, s),
                     judge=ClaudeCLIJudge(cfg.model("judge"), calls, jp, s, store.work_dir), builder=mk("builder"),
                     planter=mk("planter"))
    if mode == "api":
        from .models.claude import ClaudeAPIAgent, ClaudeAPIJudge
        from .models.openai_reviewer import OpenAIReviewer

        b = cfg.budget
        mk = lambda role: ClaudeAPIAgent(cfg.model(role), calls, tool_system, role, b.max_model_calls, b.max_tool_calls)  # noqa: E731
        return Roles(author=mk("author"), reviewer=OpenAIReviewer(cfg.model("reviewer"), calls, rp),
                     judge=ClaudeAPIJudge(cfg.model("judge"), calls, jp), builder=mk("builder"), planter=mk("planter"))
    raise ValueError(f"unknown mode {mode}")


def _report(st) -> None:
    print(f"{st.stage}/{st.variable}: {st.status}" + (f" (step {st.current_step})" if st.status != "done" else ""))
    if st.status == "waiting_human":
        print(f"waiting for you: fill in {st.gate_file}, then run `rlo approve`")
    if st.status == "waiting_manual":
        print(f"waiting for you: follow {st.manual_file}, save the answer file, then run `rlo run` again")
    for n in st.notes[-5:]:
        print(f"note: {n}")


def cmd_run(args) -> int:
    cfg = load_stage(args.stage, args.variable)
    store = Store(Path(args.target))
    calls = CallLog(store.calls_dir)
    roles = build_roles(args.mode, cfg, store, calls, args.fixture)
    rng = random.Random(args.seed) if args.seed is not None else None
    st = Engine(cfg, args.variable, roles, store, calls, rng).run()
    _report(st)
    return 0 if st.status in ("done", "waiting_human", "waiting_manual") else 1


def cmd_approve(args) -> int:
    cfg = load_stage(args.stage, args.variable)
    store = Store(Path(args.target))
    try:
        out = approve_stage(cfg=cfg, store=store, variable=args.variable, decided_by=args.by)
    except RuntimeError as e:
        print(f"not approved: {e}", file=sys.stderr)
        return 2
    j = out["judgment"]
    print(f"approved {j['items']} items: {j['accepted_default']} defaults kept, {j['overruled_default']} overruled, "
          f"{j['chose']} chosen without a default; decisions {j['decision_ids'][0]}..{j['decision_ids'][-1]}")
    if out["off_list"]:
        print(f"choices outside the listed options (recorded as given): {out['off_list']}")
    if out["stopped"]:
        print("you chose stop; the stage is stopped")
        return 0
    if args.no_continue or out["status"] == "done":
        print(f"status: {out['status']}")
        return 0
    return cmd_run(args)


def cmd_status(args) -> int:
    store = Store(Path(args.target))
    states = store.all_states()
    if not states:
        print("no stages started in this repository")
    for st in states:
        line = f"{st.stage:<18} {st.variable:<20} {st.status:<15} step {st.current_step or '-':<14} done {len(st.steps_done)}  {st.updated_at}"
        if st.gate_file:
            line += f"  gate: {st.gate_file}"
        if st.manual_file:
            line += f"  manual: {st.manual_file}"
        print(line)
    if args.logs:
        for name in ("decision_log", "judgment_log", "change_log", "run_log", "dispute_log", "error_log", "stopped_papers_log"):
            rows = store.read_jsonl(f"{name}.jsonl")
            print(f"\n{name}: {len(rows)} entries")
            for r in rows[-args.logs:]:
                print("  " + json.dumps({k: r[k] for k in list(r)[:7]}, ensure_ascii=False)[:300])
    return 0


def cmd_reset(args) -> int:
    store = Store(Path(args.target))
    p = store.root / f"state_{args.stage}_{args.variable}.json"
    if p.exists():
        p.unlink()
        print(f"removed {p.relative_to(store.target)} (logs, rounds and call records are kept)")
    else:
        print("nothing to reset")
    return 0


def cmd_ingest(args) -> int:
    """Validate a manual-mode answer and place it where the pending request expects it."""
    from .models.manual import SCHEMAS

    store = Store(Path(args.target))
    st = store.load(args.stage, args.variable)
    if st.status != "waiting_manual" or not st.manual_file:
        print("nothing is waiting for a manual answer", file=sys.stderr)
        return 2
    bundle = store.target / st.manual_file
    answer = bundle.with_name(bundle.name.replace(".md", ".answer.json"))
    text = Path(args.file).read_text(encoding="utf-8")
    from .models.base import extract_json

    data = json.loads(extract_json(text))
    head = bundle.read_text(encoding="utf-8").split("\n", 1)[0]
    purpose = head.rsplit("/", 1)[-1].strip()
    schema_name = {"task": "summary", "respond": "responses", "fix": "responses", "review": "findings", "rereview": "findings"}.get(
        purpose, "test_plan" if purpose.startswith("test_") else "confirm" if purpose.startswith("confirm_") else "verdict" if purpose.startswith("judge_") else "summary")
    required = SCHEMAS[schema_name]["required"]
    missing = [k for k in required if k not in data]
    if missing:
        print(f"answer is missing fields {missing} (expected a {schema_name} record)", file=sys.stderr)
        return 2
    answer.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"placed {answer.relative_to(store.target)}; run `rlo run` to continue")
    return 0


def cmd_log_error(args) -> int:
    from . import logs

    store = Store(Path(args.target))
    try:
        rec = logs.log_error(store, type_=args.type, produced_by=args.produced_by, how_found=args.how_found,
                             found_by=args.found_by, how_far=args.how_far, effect=args.effect,
                             confirmed_by_rerun=args.confirmed_by_rerun, fix=args.fix, check_added=args.check_added,
                             silent=args.silent, wrong=args.wrong, in_research=args.in_research,
                             variable=args.variable or "", stage=args.stage or "", in_development=args.in_development)
    except ValueError as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    print(f"logged {rec['id']}")
    return 0


def cmd_log_stop(args) -> int:
    from . import logs

    store = Store(Path(args.target))
    try:
        rec = logs.log_stop(store, paper=args.paper, call=args.call, reason=args.reason, decided_by=args.by)
    except ValueError as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    print(f"logged {rec['id']}")
    return 0


def cmd_counts(args) -> int:
    from . import logs

    print(json.dumps(logs.counts(Store(Path(args.target))), indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="rlo", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, stage=True):
        p.add_argument("--target", required=True, help="path to the target research repository")
        if stage:
            p.add_argument("--stage", required=True, help="stage name, e.g. stage2_measures")
            p.add_argument("--variable", required=True, help="variable, paper or item name, e.g. new_classes")

    def modes(p):
        p.add_argument("--mode", choices=MODES, default="cli", help="cli = subscriptions (default), api = keys, manual = paste by hand, fixtures = tests")
        p.add_argument("--fixture", help="fixture JSON when --mode fixtures")
        p.add_argument("--seed", type=int, default=None, help="seed for the judge's blinding order (tests)")

    p = sub.add_parser("run", help="run a stage until it finishes, stops, or waits for you")
    common(p); modes(p); p.set_defaults(fn=cmd_run)

    p = sub.add_parser("approve", help="read the filled-in gate checklist, log the decisions, continue the stage")
    common(p); modes(p)
    p.add_argument("--by", default="Pouya", help="who decided")
    p.add_argument("--no-continue", action="store_true", help="approve only; do not run the remaining steps")
    p.set_defaults(fn=cmd_approve)

    p = sub.add_parser("status", help="show every stage's state in the target repository")
    common(p, stage=False)
    p.add_argument("--logs", type=int, default=0, help="also print the last N entries of each log")
    p.set_defaults(fn=cmd_status)

    p = sub.add_parser("reset", help="forget a stage's state (keeps logs and call records)")
    common(p); p.set_defaults(fn=cmd_reset)

    p = sub.add_parser("ingest", help="manual mode: validate and place an answer file for the pending request")
    common(p); p.add_argument("--file", required=True); p.set_defaults(fn=cmd_ingest)

    p = sub.add_parser("log-error", help="add a silent-error entry (refused unless silent, wrong and in-research)")
    common(p, stage=False)
    p.add_argument("--type", required=True); p.add_argument("--produced-by", default="not stated")
    p.add_argument("--how-found", required=True); p.add_argument("--found-by", required=True)
    p.add_argument("--how-far", required=True); p.add_argument("--effect", required=True)
    p.add_argument("--confirmed-by-rerun", action="store_true"); p.add_argument("--fix", required=True)
    p.add_argument("--check-added", default=""); p.add_argument("--variable", default=""); p.add_argument("--stage", default="")
    p.add_argument("--silent", action="store_true"); p.add_argument("--wrong", action="store_true")
    p.add_argument("--in-research", action="store_true"); p.add_argument("--in-development", action="store_true")
    p.set_defaults(fn=cmd_log_error)

    p = sub.add_parser("log-stop", help="record a shelved or killed paper")
    common(p, stage=False)
    p.add_argument("--paper", required=True); p.add_argument("--call", required=True, choices=["shelved", "killed"])
    p.add_argument("--reason", required=True); p.add_argument("--by", default="Pouya")
    p.set_defaults(fn=cmd_log_stop)

    p = sub.add_parser("counts", help="variables, runs, errors and rates from the logs")
    common(p, stage=False); p.set_defaults(fn=cmd_counts)

    args = ap.parse_args(argv)
    if getattr(args, "mode", None) == "fixtures" and not args.fixture:
        ap.error("--fixture is required with --mode fixtures")
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
