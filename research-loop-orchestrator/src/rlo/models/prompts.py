"""Prompt text shared by every adapter, so the API, command-line and manual paths ask the same thing."""

from __future__ import annotations

import json


def bundle_artifacts(artifacts: dict[str, str]) -> str:
    return "\n".join(f"===== FILE: {name} =====\n{artifacts[name]}\n" for name in sorted(artifacts))


def review_prompt(task: str, bundle: str) -> str:
    return ("Review the artifacts below against the task description. Report every deviation from the definition, "
            "every unstated choice, and every judgment call that should go to the human. Do not pad: an empty list "
            "is a valid answer.\n\nTASK\n" + task + "\n\nARTIFACTS\n" + bundle)


def rereview_prompt(rejected, bundle: str) -> str:
    pairs = [{"finding": vars(f), "author_response": vars(r)} for f, r in rejected]
    return ("The author rejected the findings below with reasons. Re-examine each against the current artifacts. "
            "Return only the findings you still stand behind, with the same ids and strengthened evidence; drop the "
            "ones the author's reason settles.\n\nREJECTED\n" + json.dumps(pairs, indent=2) + "\n\nARTIFACTS\n" + bundle)


def confirm_prompt(finding, diff: str) -> str:
    return ("You claimed the error below. The author wrote a copy of the file that is meant to carry exactly that "
            "error, so a test can be shown to catch it. Read the diff between the real file and the copy and say "
            "whether the copy carries the error you claimed, not a weaker or different one.\n\nFINDING\n"
            + json.dumps(vars(finding), indent=2) + "\n\nDIFF (real -> copy)\n" + diff)


def respond_prompt(findings) -> str:
    return ("A reviewer from a different model family returned the findings below on your work. For each one, either "
            "accept it and make the change in the work folder, or reject it with a reason that points at the "
            "definition, the data or the literature. Do not accept to be agreeable; do not reject to save work.\n\n"
            + json.dumps([vars(f) for f in findings], indent=2))


def plan_test_prompt(finding) -> str:
    return ("You and a reviewer disagree on the finding below, and a coded check can settle it. Do three things in the "
            "work folder: (1) write a small test that reads the environment variable RLO_SUBJECT as the path of the "
            "file under test and exits non-zero when the claimed error is present; (2) write a copy of the real file "
            "that carries exactly the error the reviewer claims, as the mutant; (3) report the test command (as a list "
            "starting with python or Rscript), the real file path and the mutant path, all relative to the work "
            "folder. The test must fail on the mutant, or it does not count.\n\n" + json.dumps(vars(finding), indent=2))


def judge_prompt(finding, position_a: str, position_b: str) -> str:
    return ("Two parties disagree about the finding below. Decide which position is better supported by the "
            "definition, the data and the literature. You are not told who wrote which.\n\nFINDING\n"
            + json.dumps(vars(finding), indent=2) + f"\n\nPOSITION A\n{position_a}\n\nPOSITION B\n{position_b}")


def record_instruction(schema: dict, path: str | None) -> str:
    where = f"write it to the file {path}" if path else "reply with it as your final message and nothing else"
    return ("\n\nWhen you are done, produce one JSON object matching this schema and " + where + ":\n"
            + json.dumps(schema, indent=2))
