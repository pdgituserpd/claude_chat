"""Output fingerprints and the sign-off rule.

A change that leaves every output fingerprint identical goes through without the human.
Anything that moves a fingerprint waits for him.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fingerprint_outputs(target: Path, globs: list[str]) -> dict[str, str]:
    target = Path(target)
    out: dict[str, str] = {}
    for g in globs:
        for p in sorted(target.glob(g)):
            if p.is_file() and ".git" not in p.parts and ".rlo" not in p.parts:
                out[str(p.relative_to(target))] = sha256_file(p)
    return out


def compare(before: dict[str, str], after: dict[str, str]) -> dict:
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(k for k in set(before) & set(after) if before[k] != after[k])
    return {
        "identical": not (added or removed or changed),
        "added": added,
        "removed": removed,
        "changed": changed,
    }


def save_snapshot(path: Path, fp: dict[str, str], meta: dict | None = None) -> None:
    path.write_text(json.dumps({"fingerprints": fp, "meta": meta or {}}, indent=2), encoding="utf-8")


def load_snapshot(path: Path) -> dict[str, str] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))["fingerprints"]
