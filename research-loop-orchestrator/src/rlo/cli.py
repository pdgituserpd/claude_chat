"""Command line: rlo run | status | approve | reset."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

from .calls import CallLog
from .config import load_stage
from .state import Store


def _build_models(args, cfg, store, calls):
    if args.models == "fixtures":
        from .models.fixtures import FixtureAuthor, FixtureJudge, FixtureReviewer, load_fixture

        spec = load_fixture(Path(args.fixture))
        return (
            FixtureAuthor(spec, store.target, calls),
            FixtureReviewer(spec, calls),
            FixtureJudge(spec, calls),
            "fixture", "fixture",
        )
    from .models.claude import ClaudeAuthor, ClaudeJudge
    from .models.openai_reviewer import OpenAIReviewer

    author = ClaudeAuthor(
        model=cfg.author_model, target=store.target, readable=cfg.inputs, calls=calls,
        system_prompt=cfg.prompt_text("author"), max_model_calls=cfg.budget.max_model_calls,
        max_tool_calls=cfg.budget.max_tool_calls,
    )
    reviewer = OpenAIReviewer(model=cfg.reviewer_model, calls=calls, system_prompt=cfg.prompt_text("reviewer"))
    judge = ClaudeJudge(model=cfg.judge_model, calls=calls, system_prompt=cfg.prompt_text("judge"))
    return author, reviewer, judge, "anthropic", "anthropic"


def cmd_run(args) -> int:
    from .loop import run_stage

    cfg = load_stage(args.stage)
    store = Store(Path(args.target))
    calls = CallLog(store.calls_dir)
    author, reviewer, judge, author_family, judge_family = _build_models(args, cfg, store, calls)
    rng = random.Random(args.seed) if args.seed is not None else None
    st = run_stage(
        cfg=cfg, target=store.target, variable=args.variable, author=author, reviewer=reviewer, judge=judge,
        store=store, calls=calls, author_family=author_family, judge_family=judge_family, rng=rng,
    )
    print(f"{st.stage}/{st.variable}: {st.status}")
    if st.gate_file:
        print(f"waiting for you: edit {st.gate_file}, then run `rlo approve`")
    for n in st.notes:
        print(f"note: {n}")
    return 0


def cmd_status(args) -> int:
    store = Store(Path(args.target))
    states = store.all_states()
    if not states:
        print("no stages started in this repository")
    for st in states:
        line = f"{st.stage:<16} {st.variable:<24} {st.status:<14} round {st.round}  updated {st.updated_at}"
        if st.gate_file:
            line += f"  gate: {st.gate_file}"
        print(line)
    if args.logs:
        for name in ("decision_log", "judgment_log", "change_log", "run_log", "dispute_log"):
            rows = store.read_jsonl(f"{name}.jsonl")
            print(f"\n{name}: {len(rows)} entries")
            for r in rows[-args.logs:]:
                print("  " + json.dumps({k: r[k] for k in list(r)[:6]}, ensure_ascii=False))
    return 0


def cmd_approve(args) -> int:
    from .loop import approve_stage

    cfg = load_stage(args.stage)
    store = Store(Path(args.target))
    try:
        out = approve_stage(cfg=cfg, target=store.target, variable=args.variable, store=store, decided_by=args.by)
    except RuntimeError as e:
        print(f"not approved: {e}", file=sys.stderr)
        return 2
    print(f"approved {out['total']} items; {out['overruled']} AI defaults overruled; decisions logged")
    if out["off_list"]:
        print(f"choices outside the listed options: {out['off_list']}")
    return 0


def cmd_reset(args) -> int:
    store = Store(Path(args.target))
    p = store.root / f"state_{args.stage}_{args.variable}.json"
    if p.exists():
        p.unlink()
        print(f"removed {p.relative_to(store.target)} (logs and call records are kept)")
    else:
        print("nothing to reset")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="rlo", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--target", required=True, help="path to the target research repository")
        p.add_argument("--stage", required=True, help="stage name, e.g. stage2_measures")
        p.add_argument("--variable", required=True, help="variable or item name, e.g. new_classes")

    p = sub.add_parser("run", help="run a stage until it finishes or stops at a human gate")
    common(p)
    p.add_argument("--models", choices=["live", "fixtures"], default="live")
    p.add_argument("--fixture", help="fixture JSON when --models fixtures")
    p.add_argument("--seed", type=int, default=None, help="seed for blinding order (tests)")
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("status", help="show every stage's state in the target repository")
    p.add_argument("--target", required=True)
    p.add_argument("--logs", type=int, default=0, help="also print the last N entries of each log")
    p.set_defaults(fn=cmd_status)

    p = sub.add_parser("approve", help="read the filled-in gate checklist, log the decisions, continue")
    common(p)
    p.add_argument("--by", default="Pouya", help="who decided")
    p.set_defaults(fn=cmd_approve)

    p = sub.add_parser("reset", help="forget a stage's state (keeps logs and call records)")
    common(p)
    p.set_defaults(fn=cmd_reset)

    args = ap.parse_args(argv)
    if args.cmd == "run" and args.models == "fixtures" and not args.fixture:
        ap.error("--fixture is required with --models fixtures")
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
