"""Coded checks the engine runs itself: commands, CSV comparisons, dispute tests, mutant copies."""

from __future__ import annotations

import csv
import difflib
import shutil
from pathlib import Path

from .models.base import TestOutcome, TestPlan
from .tools import ToolError, run_command


def run_check(workdir: Path, command: list[str]) -> dict:
    try:
        r = run_command(workdir, command)
    except ToolError as e:
        return {"ok": False, "returncode": None, "stdout": "", "stderr": str(e)}
    return {"ok": r["returncode"] == 0, **r}


def _read_csv(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def _same(a: str, b: str, tol: float) -> bool:
    if a == b:
        return True
    try:
        return abs(float(a) - float(b)) <= tol
    except ValueError:
        return False


def compare_csv(left: Path, right: Path, key: list[str], tolerance: float = 0.0, max_report: int = 50) -> dict:
    """Row-by-row comparison on key columns. Compares whole rows, not only the final measure."""
    if not left.exists() or not right.exists():
        return {"ok": False, "error": f"missing file: {left if not left.exists() else right}"}
    lcols, lrows = _read_csv(left)
    rcols, rrows = _read_csv(right)
    missing = [k for k in key if k not in lcols or k not in rcols]
    if missing:
        return {"ok": False, "error": f"key columns missing: {missing}"}
    common = [c for c in lcols if c in rcols]

    def index(rows):
        idx = {}
        dups = []
        for r in rows:
            k = tuple(r[c] for c in key)
            if k in idx:
                dups.append(k)
            idx[k] = r
        return idx, dups

    li, ldups = index(lrows)
    ri, rdups = index(rrows)
    only_left = sorted(set(li) - set(ri))
    only_right = sorted(set(ri) - set(li))
    mismatches = []
    for k in sorted(set(li) & set(ri)):
        for c in common:
            if c in key:
                continue
            if not _same(li[k][c], ri[k][c], tolerance):
                mismatches.append({"key": k, "column": c, "left": li[k][c], "right": ri[k][c]})
    ok = not (only_left or only_right or mismatches or ldups or rdups)
    return {
        "ok": ok, "rows_left": len(lrows), "rows_right": len(rrows), "columns_compared": [c for c in common if c not in key],
        "columns_only_left": [c for c in lcols if c not in rcols], "columns_only_right": [c for c in rcols if c not in lcols],
        "duplicate_keys_left": len(ldups), "duplicate_keys_right": len(rdups),
        "only_left": [list(k) for k in only_left[:max_report]], "only_right": [list(k) for k in only_right[:max_report]],
        "n_only_left": len(only_left), "n_only_right": len(only_right),
        "mismatches": mismatches[:max_report], "n_mismatches": len(mismatches),
    }


def file_diff(workdir: Path, subject: str, mutant: str) -> str:
    a = (workdir / subject).read_text(encoding="utf-8", errors="replace").splitlines()
    b = (workdir / mutant).read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(difflib.unified_diff(a, b, fromfile=subject, tofile=mutant, lineterm=""))


def run_test_plan(workdir: Path, plan: TestPlan, reviewer_confirmed: bool | None) -> TestOutcome:
    """The test must fail on the mutant to count. Then its result on the real file decides."""
    workdir = Path(workdir)
    for rel in (plan.subject, plan.mutant):
        if not (workdir / rel).exists():
            return TestOutcome(plan.finding_id, plan, None, None, reviewer_confirmed, False, f"missing file {rel}")
    on_mutant = _run_with_subject(workdir, plan.test_command, plan.mutant)
    mutant_failed = not on_mutant["ok"]
    on_subject = _run_with_subject(workdir, plan.test_command, plan.subject)
    subject_passed = on_subject["ok"]
    valid = bool(mutant_failed and reviewer_confirmed)
    output = (f"on mutant: rc={on_mutant['returncode']} {on_mutant['stderr'][-300:]}\n"
              f"on subject: rc={on_subject['returncode']} {on_subject['stderr'][-300:]}")
    return TestOutcome(plan.finding_id, plan, mutant_failed, subject_passed, reviewer_confirmed, valid, output)


def _run_with_subject(workdir: Path, command: list[str], subject: str) -> dict:
    try:
        r = run_command(workdir, command, env={"RLO_SUBJECT": subject})
    except ToolError as e:
        return {"ok": False, "returncode": None, "stdout": "", "stderr": str(e)}
    return {"ok": r["returncode"] == 0, **r}


def copy_tree(src: Path, dst: Path, exclude: list[str]) -> None:
    """Copy a repository into a work folder, skipping excluded top-level names (e.g. .git, data)."""
    if dst.exists():
        shutil.rmtree(dst)

    def ignore(d, names):
        return [n for n in names if n in exclude] if Path(d) == src else [n for n in names if n in (".git", ".rlo")]

    shutil.copytree(src, dst, ignore=ignore)


def copy_matching(src: Path, dst: Path, globs: list[str]) -> list[str]:
    """Copy files matching globs from src into dst, preserving relative paths. Returns the relative paths."""
    from .tools import files_matching

    out = []
    for p in files_matching(src, globs):
        rel = p.relative_to(src)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)
        out.append(str(rel))
    return out
