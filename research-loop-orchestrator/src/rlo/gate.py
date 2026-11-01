"""Human gates: the program writes a checklist and stops; `approve` reads it back.

Default rule (after review): an AI default is shown only where a direct published precedent
decides the choice, because the precedent rule already made that choice. Where the precedent
is only the closest one, or there is none, the AI lists options and reasons but makes no
pick, and you choose. Every item still needs an explicit `Choice:`; the log records
"accepted the default", "overruled the default" and "chose" separately.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

PRECEDENT_TYPES = ("direct", "closest", "none")
NO_DEFAULT = "(none: no direct precedent, you choose)"


@dataclass
class GateItem:
    id: str
    item: str
    options: list[str]
    default: str = ""
    precedent: str = ""
    precedent_type: str = "none"  # direct | closest | none
    reason: str = ""
    source: str = "author"        # author | dispute | check | system
    positions: dict = field(default_factory=dict)
    choice: str = ""
    note: str = ""

    def shown_default(self) -> str:
        return self.default if (self.precedent_type == "direct" and self.default) else ""

    def outcome(self) -> str:
        d = self.shown_default()
        if not d:
            return "chose"
        return "accepted_default" if self.choice == d else "overruled_default"

    @classmethod
    def from_choice_dict(cls, d: dict, source: str = "author") -> "GateItem":
        pt = d.get("precedent_type", "none")
        if pt not in PRECEDENT_TYPES:
            raise ValueError(f"gate item {d.get('id')}: precedent_type must be one of {PRECEDENT_TYPES}")
        return cls(id=d["id"], item=d["item"], options=list(d["options"]), default=d.get("default", ""),
                   precedent=d.get("precedent", ""), precedent_type=pt, reason=d.get("reason", ""), source=source)


HEADER = """# Gate {gate_no}: {title}

Stage: {stage}    Variable: {variable}    Written: {when}

How to use this file
- Each item has a `Choice:` line. Fill every one in, by typing one of the options.
- Where a direct published precedent decides the item, the AI's default is shown and you may
  take it. Where there is none, no default is shown and the choice is yours.
- `Note:` is optional. Use it for the reason when you overrule a default or pick "other".
- Then run:  rlo approve --target <repo> --stage {stage} --variable {variable}
- The command refuses to continue while any `Choice:` is empty.

"""

ITEM = """## {id}: {item}
Source: {source}
Options: {options}
Precedent: {precedent} [{precedent_type}]
AI default: {default}
Reason: {reason}
{positions}Choice: {choice}
Note: {note}

"""


def render(items: list[GateItem], *, gate_no: int, title: str, stage: str, variable: str, when: str) -> str:
    out = HEADER.format(gate_no=gate_no, title=title, stage=stage, variable=variable, when=when)
    for it in items:
        pos = ""
        if it.positions:
            pos = (f"Author position: {it.positions.get('author', '')}\n"
                   f"Reviewer position: {it.positions.get('reviewer', '')}\n")
        out += ITEM.format(id=it.id, item=it.item, source=it.source, options=" | ".join(it.options),
                           precedent=it.precedent or "not stated", precedent_type=it.precedent_type,
                           default=it.shown_default() or NO_DEFAULT, reason=it.reason or "not stated",
                           positions=pos, choice=it.choice, note=it.note)
    return out


_ITEM_RE = re.compile(r"^## (?P<id>[^:\n]+): (?P<item>.*)$", re.M)
_PREC_RE = re.compile(r"^(?P<p>.*?)\s*\[(?P<t>direct|closest|none)\]\s*$")


def parse(text: str) -> list[GateItem]:
    chunks = _ITEM_RE.split(text)
    items: list[GateItem] = []
    for i in range(1, len(chunks), 3):
        id_, item, body = chunks[i].strip(), chunks[i + 1].strip(), chunks[i + 2]

        def line(key: str) -> str:
            m = re.search(rf"^{key}:[ \t]*(.*)$", body, re.M)
            return m.group(1).strip() if m else ""

        prec_raw = line("Precedent")
        m = _PREC_RE.match(prec_raw)
        precedent, ptype = (m.group("p"), m.group("t")) if m else (prec_raw, "none")
        default = line("AI default")
        if default.startswith("(none"):
            default = ""
        positions = {}
        if line("Author position") or line("Reviewer position"):
            positions = {"author": line("Author position"), "reviewer": line("Reviewer position")}
        items.append(GateItem(id=id_, item=item, options=[o.strip() for o in line("Options").split("|") if o.strip()],
                              default=default, precedent="" if precedent == "not stated" else precedent,
                              precedent_type=ptype, reason=line("Reason"), source=line("Source") or "author",
                              positions=positions, choice=line("Choice"), note=line("Note")))
    return items


def unanswered(items: list[GateItem]) -> list[str]:
    return [it.id for it in items if not it.choice]


def write_gate_file(path: Path, items: list[GateItem], **meta) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(items, **meta), encoding="utf-8")
    return path
