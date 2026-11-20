#!/usr/bin/env python3
"""Run pointer-files.py on small trees and check its answer.

    python3 scripts/test-pointer-files.py

Each case is a tree of a few Markdown files, staged in a new git
repository that the script is given. The script prints each case whose
answer is wrong, and exits 1 where there is one.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("pointer-files.py")
B = "# B\n\n## The gates\n\nText.\n\n- **Debris goes when its work ends, not later.** Text.\n"

# (name, files besides process/b.md, the pointers the script prints)
CASES: list[tuple[str, dict[str, str], list[str]]] = [
    (
        "bare",
        {"process/a.md": "As *The gates* says.\n"},
        ["process/a.md:1: *The gates*"],
    ),
    ("own file", {"process/a.md": "## The gates\n\nAs *The gates* says.\n"}, []),
    ("a possessive", {"process/a.md": "As `b.md`'s *The gates* says.\n"}, []),
    (
        "a possessive of a file of its day",
        {"process/a.md": "As `old.md`'s *The gates* said.\n"},
        [],
    ),
    (
        "a possessive across a line break",
        {"process/a.md": "As `b.md`'s\n*The gates* says.\n"},
        [],
    ),
    (
        "its sentence names the file",
        {"process/a.md": "*The gates*, in `process/b.md`, says. *The gates* too.\n"},
        ["process/a.md:1: *The gates*"],
    ),
    (
        "a sentence naming another file",
        {"process/a.md": "As `c.md` says, *The gates* holds.\n"},
        ["process/a.md:1: *The gates*"],
    ),
    (
        "the start of a bold run",
        {"process/a.md": "As *Debris goes when its work ends* says.\n"},
        ["process/a.md:1: *Debris goes when its work ends*"],
    ),
    (
        "a bold run that holds code",
        {
            "process/c.md": "- **`ref` is shared by every worktree.** Text.\n",
            "process/a.md": "As *`ref` is shared by every worktree* says.\n",
        },
        ["process/a.md:1: *`ref` is shared by every worktree*"],
    ),
    ("two words start nothing", {"process/a.md": "As *Debris goes* says.\n"}, []),
    ("the standard's", {"process/a.md": "Section 9's *The gates* holds.\n"}, []),
    ("inline code", {"process/a.md": "As `*The gates*` says.\n"}, []),
    ("a fence", {"process/a.md": "```text\n*The gates*\n```\n"}, []),
    ("a comment", {"process/a.md": "<!-- *The gates* -->\n"}, []),
    (
        "a possessive of a file that does not hold it",
        {"process/c.md": "# C\n", "process/a.md": "As `c.md`'s *The gates* says.\n"},
        ["process/a.md:1: *The gates*: not in c.md"],
    ),
    (
        "a possessive of a file whose table redirects it",
        {
            "process/r.md": "| Section | File |\n| --- | --- |\n| *The gates* | `b.md` |\n",
            "process/a.md": "As `r.md`'s *The gates* says.\n",
        },
        [],
    ),
    (
        "a bold run inside a sentence is no section",
        {
            "process/c.md": "Text with **an inline bold run** inside.\n",
            "process/a.md": "As *an inline bold run* says.\n",
        },
        [],
    ),
    (
        "a copy of the standard, and its own part",
        {
            "REVIEWING.md": "As *The gates* says.\n\n"
            "## This repository in particular\n\nAs *The gates* holds.\n"
        },
        ["REVIEWING.md:5: *The gates*"],
    ),
    (
        "a copy of the standard whose heading is spelt otherwise",
        {
            "REVIEWING.md": "As *The gates* says.\n\n"
            "## This Repository In Particular\n\nAs *The gates* holds.\n"
        },
        ['REVIEWING.md: lacks the heading "## This repository in particular"'],
    ),
    (
        "the tree's AGENTS.md",
        {"AGENTS.md": "As *The gates* says.\n"},
        ["AGENTS.md:1: *The gates*"],
    ),
    ("the history", {"CHANGELOG.md": "As *The gates* says.\n"}, []),
    (
        "a skill",
        {
            "skills/x/SKILL.md": "## Landing\n",
            "process/a.md": "As `/x`'s *Landing* says. *Landing*, in `/x`, too.\n",
        },
        [],
    ),
    (
        "an agent",
        {
            "agents/writer.md": "## What holds\n",
            "process/a.md": "As the `writer` agent's *What holds* says.\n",
        },
        [],
    ),
    (
        "wrapped",
        {"process/a.md": "Text, as\n*Debris goes when its\nwork ends* says.\n"},
        ["process/a.md:2: *Debris goes when its work ends*"],
    ),
]


def run(files: dict[str, str]) -> tuple[int, list[str]]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["git", "init", "-q", tmp], env=env, check=True)
        for path, text in {"process/b.md": B, **files}.items():
            (Path(tmp) / path).parent.mkdir(parents=True, exist_ok=True)
            (Path(tmp) / path).write_text(text, encoding="utf-8")
        subprocess.run(["git", "-C", tmp, "add", "."], env=env, check=True)
        done = subprocess.run(
            [sys.executable, "-I", str(SCRIPT), tmp],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
    return done.returncode, [x.rsplit(": in ", 1)[0] for x in done.stdout.splitlines()]


def main() -> None:
    wrong = []
    for name, files, want in CASES:
        code, got = run(files)
        if got != want or code != (1 if want else 0):
            wrong.append(f"{name}: exit {code}, {got}, want {want}")
    if wrong:
        print("\n".join(wrong))
    sys.exit(1 if wrong else 0)


if __name__ == "__main__":
    main()
