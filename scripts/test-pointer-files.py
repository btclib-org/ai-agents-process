#!/usr/bin/env python3
"""Run pointer-files.py on small trees and check its answer.

    python3 scripts/test-pointer-files.py

Each case is a tree of a few Markdown files, staged in a new git
repository that the script is given. A case may then change a file on
disk alone, with a text over the staged one or `None` for a file
removed, or make a file unmerged in the index, with the texts of its
three stages. The script prints each case whose answer is wrong, and
exits 1 where there is one.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("pointer-files.py")
B = "# B\n\n## The gates\n\nText.\n\n- **Debris goes when its work ends, not later.** Text.\n"

# (name, files besides process/b.md, the lines the script prints), and
# what then changes
Then = dict[str, str | None | tuple[str, str, str]]
CASES: list[
    tuple[str, dict[str, str], list[str]] | tuple[str, dict[str, str], list[str], Then]
] = [
    (
        "bare",
        {"process/a.md": "As *The gates* says.\n"},
        ["process/a.md:1: *The gates*: in process/b.md"],
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
        ["process/a.md:1: *The gates*: in process/b.md"],
    ),
    (
        "a sentence naming another file",
        {"process/a.md": "As `c.md` says, *The gates* holds.\n"},
        ["process/a.md:1: *The gates*: in process/b.md"],
    ),
    (
        "the start of a bold run",
        {"process/a.md": "As *Debris goes when its work ends* says.\n"},
        ["process/a.md:1: *Debris goes when its work ends*: in process/b.md"],
    ),
    (
        "a bold run that holds code",
        {
            "process/c.md": "- **`ref` is shared by every worktree.** Text.\n",
            "process/a.md": "As *`ref` is shared by every worktree* says.\n",
        },
        ["process/a.md:1: *`ref` is shared by every worktree*: in process/c.md"],
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
        ["REVIEWING.md:5: *The gates*: in process/b.md"],
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
        ["AGENTS.md:1: *The gates*: in process/b.md"],
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
        ["process/a.md:2: *Debris goes when its work ends*: in process/b.md"],
    ),
    (
        "its own file's bold start, another file's heading",
        {
            "process/c.md": "## A pull request's rounds\n",
            "process/a.md": "- **A pull request's rounds go fast.** Text.\n\n"
            "As *A pull request's rounds* says.\n",
        },
        ["process/a.md:3: *A pull request's rounds*: in process/c.md"],
    ),
    (
        "its own file's bold run, another file's heading",
        {
            "process/a.md": "- **The gates.** Text.\n\nAs *The gates* says.\n",
        },
        ["process/a.md:3: *The gates*: in process/b.md"],
    ),
    (
        "the first match over every file",
        {"process/c.md": "- **The gates.** Text.\n", "process/a.md": "*The gates*.\n"},
        ["process/a.md:1: *The gates*: in process/b.md"],
    ),
    (
        "a sentence naming a holder of a later match",
        {
            "process/c.md": "- **The gates.** Text.\n",
            "process/a.md": "As *The gates*, in `c.md`, says.\n",
        },
        [],
    ),
    (
        "a possessive of a file that does not hold it, its own file holding it",
        {
            "process/c.md": "# C\n",
            "process/a.md": "## The gates\n\nAs `c.md`'s *The gates* says.\n",
        },
        ["process/a.md:3: *The gates*: not in c.md"],
    ),
    (
        "a possessive of a file that does not hold it, across a line break",
        {"process/c.md": "# C\n", "process/a.md": "As `c.md`'s\n*The gates* says.\n"},
        ["process/a.md:2: *The gates*: not in c.md"],
    ),
    (
        "a possessive at the edge of what is read before a pointer",
        {
            f"process/{'c' * 64}.md": "# C\n",
            "process/a.md": f"As `process/{'c' * 64}.md`'s *The gates* says.\n",
        },
        [f"process/a.md:1: *The gates*: not in process/{'c' * 64}.md"],
    ),
    (
        "a possessive of a misspelt name",
        {"process/a.md": "As `bb.md`'s *The gates* says.\n"},
        [],
    ),
    (
        "a fence closed only by a line with nothing after its mark",
        {"process/a.md": "```text\n```shell\n*The gates*\n```\n"},
        [],
    ),
    (
        "a fence closed by a line of its mark and blanks",
        {"process/a.md": "```text\n```  \t\n*The gates*\n"},
        ["process/a.md:3: *The gates*: in process/b.md"],
    ),
    (
        "a fence closed only by a mark as long as its own",
        {"process/a.md": "````text\n```\n*The gates*\n````\n"},
        [],
    ),
    (
        "a sentence ended by a blank line",
        {"process/a.md": "Read `process/b.md`\n\n*The gates* says.\n"},
        ["process/a.md:3: *The gates*: in process/b.md"],
    ),
    (
        "a sentence ended by a list item",
        {"process/a.md": "- Read `process/b.md`\n- *The gates* says.\n"},
        ["process/a.md:2: *The gates*: in process/b.md"],
    ),
    (
        "a first-level heading",
        {
            "process/c.md": "# Release notes\n",
            "process/a.md": "As *Release notes* says.\n",
        },
        ["process/a.md:1: *Release notes*: in process/c.md"],
    ),
    (
        "a start that ends inside a word",
        {"process/a.md": "As *Debris goes when its wo* says.\n"},
        [],
    ),
    (
        "a name inside another file's name",
        {"process/a.md": "As *The gates*, in `ab.md` and `b.md-old`, says.\n"},
        ["process/a.md:1: *The gates*: in process/b.md"],
    ),
    (
        "a bold run's closing mark",
        {
            "process/c.md": "- **Stay put.** a\n- **Stay clean,** b\n"
            "- **Stay fast:** c\n- **Stay calm;** d\n",
            "process/a.md": "*Stay put*, *Stay clean*, *Stay fast*, *Stay calm*.\n",
        },
        [
            f"process/a.md:1: *Stay {w}*: in process/c.md"
            for w in ("put", "clean", "fast", "calm")
        ],
    ),
    (
        "a file the index lists and the disk lacks",
        {"process/a.md": "As *The gates* says.\n"},
        ["process/a.md:1: *The gates*: in process/b.md"],
        {"process/b.md": None},
    ),
    (
        "a file whose line ends are a carriage return and a newline",
        {"process/a.md": "```text\r\nx\r\n```\r\n*The gates*\r\n"},
        ["process/a.md:4: *The gates*: in process/b.md"],
    ),
    (
        "an unmerged file",
        {"process/a.md": "Text.\n"},
        [],
        {"process/a.md": ("As *The gates* says.\n",) * 3},
    ),
    (
        "a file whose disk text is not the index's",
        {"process/a.md": "As *The gates* says.\n"},
        ["process/a.md:1: *The gates*: in process/b.md"],
        {"process/a.md": "No pointer.\n"},
    ),
]


def run(files: dict[str, str], then: Then) -> tuple[int, list[str]]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["git", "init", "-q", tmp], env=env, check=True)
        for path, text in {"process/b.md": B, **files}.items():
            (Path(tmp) / path).parent.mkdir(parents=True, exist_ok=True)
            (Path(tmp) / path).write_text(text, encoding="utf-8")
        subprocess.run(["git", "-C", tmp, "add", "."], env=env, check=True)
        for path, change in then.items():
            if change is None:
                (Path(tmp) / path).unlink()
            elif isinstance(change, str):
                (Path(tmp) / path).write_text(change, encoding="utf-8")
            else:
                info = f"0 {'0' * 40}\t{path}\n"
                for stage, staged in enumerate(change, 1):
                    blob = subprocess.run(
                        ["git", "-C", tmp, "hash-object", "-w", "--stdin"],
                        input=staged,
                        capture_output=True,
                        text=True,
                        env=env,
                        check=True,
                    ).stdout.strip()
                    info += f"100644 {blob} {stage}\t{path}\n"
                subprocess.run(
                    ["git", "-C", tmp, "update-index", "--index-info"],
                    input=info,
                    text=True,
                    env=env,
                    check=True,
                )
        done = subprocess.run(
            [sys.executable, "-I", str(SCRIPT), tmp],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
    return done.returncode, done.stdout.splitlines()


def main() -> None:
    wrong = []
    for name, files, want, *then in CASES:
        code, got = run(files, then[0] if then else {})
        if got != want or code != (1 if want else 0):
            wrong.append(f"{name}: exit {code}, {got}, want {want}")
    if wrong:
        print("\n".join(wrong))
    sys.exit(1 if wrong else 0)


if __name__ == "__main__":
    main()
