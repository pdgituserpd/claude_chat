"""Human gates: the program writes a checklist and stops; `approve` reads it back.

The checklist is Markdown so it is pleasant to edit. Every item has a `Choice:` line that
must be filled in, and an optional `Note:` line. Defaults are pre-filled from the author's
precedent-based proposal; the human approves by exception, but the log records him as the
decider on every item.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GateItem:
    id: str
    item: str
    options: list[str]
    default: str
    precedent: str
    reason: str
    source: str = "author"  # author | dispute
    positions: dict = field(default_factory=dict)  # for disputes: author/reviewer text
    choice: str = ""
    note: str = ""


HEADER = """# Gate {gate_no}: {title}

Stage: {stage}    Variable: {variable}    Written: {when}

How to use this file
- Each item below has a `Choice:` line. Fill every one in. Leaving the AI default is fine;
  write it out anyway so the log records you as the decider.
- `Note:` is optional. Use it for the reason when you overrule the default.
- Then run:  rlo approve --target <repo> --stage {stage} --variable {variable}
- The command refuses to continue while any `Choice:` is empty.

"""

ITEM = """## {id}: {item}
Source: {source}
Options: {options}
AI default: {default}
Precedent: {precedent}
Reason: {reason}
{positions}Choice: {choice}
Note: {note}

"""


def render(items: list[GateItem], *, gate_no: int, title: str, stage: str, variable: str, when: str) -> str:
    out = HEADER.format(gate_no=gate_no, title=title, stage=stage, variable=variable, when=when)
    for it in items:
        pos = ""
        if it.positions:
            pos = f"Author position: {it.positions.get('author','')}\nReviewer position: {it.positions.get('reviewer','')}\n"
        out += ITEM.format(
            id=it.id, item=it.item, source=it.source, options=" | ".join(it.options), default=it.default,
            precedent=it.precedent or "not stated", reason=it.reason or "not stated", positions=pos,
            choice=it.choice, note=it.note,
        )
    return out


_ITEM_RE = re.compile(r"^## (?P<id>[^:\n]+): (?P<item>.*)$", re.M)


def parse(text: str) -> list[GateItem]:
    """Read a filled-in checklist back. Tolerant of edits to prose; strict on the field lines."""
    chunks = _ITEM_RE.split(text)
    # split yields: [preamble, id, item, body, id, item, body, ...]
    items: list[GateItem] = []
    for i in range(1, len(chunks), 3):
        id_, item, body = chunks[i].strip(), chunks[i + 1].strip(), chunks[i + 2]

        def line(key: str) -> str:
            m = re.search(rf"^{key}:[ \t]*(.*)$", body, re.M)
            return m.group(1).strip() if m else ""

        options = [o.strip() for o in line("Options").split("|") if o.strip()]
        positions = {}
        if line("Author position") or line("Reviewer position"):
            positions = {"author": line("Author position"), "reviewer": line("Reviewer position")}
        items.append(GateItem(
            id=id_, item=item, options=options, default=line("AI default"), precedent=line("Precedent"),
            reason=line("Reason"), source=line("Source") or "author", positions=positions,
            choice=line("Choice"), note=line("Note"),
        ))
    return items


def unanswered(items: list[GateItem]) -> list[str]:
    return [it.id for it in items if not it.choice]


def write_gate_file(path: Path, items: list[GateItem], **meta) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(items, **meta), encoding="utf-8")
    return path
