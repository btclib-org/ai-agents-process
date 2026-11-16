#!/usr/bin/env python3
"""Run the clearance comparison of a rebase on fixture commits.

    python3 scripts/test-rebase-clearance.py

The comparison is the shell block of `process/*.md` that assigns `before`
and `after` (*A rebase and the clearance*). The test reads it from the
process, so it runs the commands a session pastes. Each case builds a
cleared commit and its rebased counterpart in a bare repository with git
plumbing, which writes commits without signing them, and runs the block
with `sh` on the two. It checks that the two hashes are equal where the
branch's added and removed lines are unchanged, and differ where they
are not: an edit that lands in another file, and one that a line
printing as another file's `---` and `+++` hides, included. The
fixtures' git calls run with none of the caller's `GIT_` variables and
no global or system git configuration; a case may set inert keys of the
fixture repository's own. The script prints each case that answers
wrongly, and exits 1 where there is one.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TypeAlias

PROCESS = Path(__file__).resolve().parent.parent / "process"
FENCE = re.compile(r"^```shell\n(.*?)^```$", re.MULTILINE | re.DOTALL)
Files: TypeAlias = dict[str, str]


def fixture_env() -> dict[str, str]:
    """Return a fixture's environment: no `GIT_` of the caller's, no git config."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    return env


def find_block() -> str:
    """Return the one shell block of the process that assigns both streams."""
    found: list[str] = [
        block
        for path in sorted(PROCESS.glob("*.md"))
        for block in FENCE.findall(path.read_text())
        if "before=$(" in block and "after=$(" in block
    ]
    if len(found) != 1:
        sys.exit(f"{len(found)} blocks assign before and after, not one")
    return found[0]


class Repo:
    """A bare repository the fixtures write commits into."""

    def __init__(self, path: Path) -> None:
        self.path = str(path)
        subprocess.run(
            ["git", "init", "-q", "--bare", self.path], check=True, env=fixture_env()
        )
        self.clock = 1_700_000_000

    def git(self, *args: str, data: bytes | None = None, index: str = "") -> str:
        env = fixture_env()
        if index:
            env["GIT_INDEX_FILE"] = index
        done = subprocess.run(
            ["git", "-C", self.path, *args],
            input=data,
            capture_output=True,
            check=True,
            env=env,
        )
        return done.stdout.decode().strip()

    def commit(self, files: Files, parent: str = "") -> str:
        """Write a commit whose tree holds exactly `files`."""
        index = os.path.join(self.path, "fixture-index")
        if os.path.exists(index):
            os.remove(index)
        for name, text in files.items():
            blob = self.git("hash-object", "-w", "--stdin", data=text.encode())
            self.git(
                "update-index",
                "--add",
                "--cacheinfo",
                f"100644,{blob},{name}",
                index=index,
            )
        tree = self.git("write-tree", index=index)
        self.clock += 60
        who = f"Fixture <fixture@example.invalid> {self.clock} +0000"
        body = f"tree {tree}\n" + (f"parent {parent}\n" if parent else "")
        body += f"author {who}\ncommitter {who}\n\nfixture\n"
        return self.git(
            "hash-object", "-t", "commit", "-w", "--stdin", data=body.encode()
        )


class Case:
    """A cleared commit, its rebased counterpart, and whether they compare equal.

    `old` is the base the cleared commit was reviewed on and `new` the base
    it is rebased onto; `cleared` and `rebased` are the trees of the two
    commits on top of them. `config` holds keys of the fixture repository's
    own git configuration, as a reader's may set them: inert ones only, never
    a key that names a program to run.
    """

    def __init__(
        self,
        label: str,
        old: Files,
        cleared: Files,
        new: Files,
        rebased: Files,
        equal: bool,
        config: tuple[tuple[str, str], ...] = (),
    ) -> None:
        self.label, self.equal, self.config = label, equal, config
        self.old, self.cleared, self.new, self.rebased = old, cleared, new, rebased


LINES = "a\nb\nc\nd\ne\nf\n"
EDITED = "a\nb\nc\nD\ne\nf\n"
BASE: Files = {"A.md": LINES, "B.md": LINES}
# A.md holds a line that, removed and added, prints as B.md's `---` and
# `+++` lines; the gaps keep its three edits in three hunks
GAP = "g\n" * 8
FORGE: Files = {"A.md": f"x\n{GAP}-- a/B.md\n{GAP}u\n", "B.md": "u\n"}
IN_A: Files = {"A.md": f"y\n{GAP}++ b/B.md\n{GAP}v\n", "B.md": "u\n"}
IN_A_AND_B: Files = {"A.md": f"y\n{GAP}-- a/B.md\n{GAP}u\n", "B.md": "v\n"}

CASES = (
    Case(
        "the same edit, rebased past a commit to another file",
        BASE,
        {**BASE, "A.md": EDITED},
        {**BASE, "C.md": "c\n"},
        {**BASE, "A.md": EDITED, "C.md": "c\n"},
        equal=True,
    ),
    Case(
        "the same edit, rebased past lines added above it in its file",
        BASE,
        {**BASE, "A.md": EDITED},
        {**BASE, "A.md": "z\n" * 9 + LINES},
        {**BASE, "A.md": "z\n" * 9 + EDITED},
        equal=True,
    ),
    Case(
        "the edit changes a line it adds",
        BASE,
        {**BASE, "A.md": EDITED},
        BASE,
        {**BASE, "A.md": EDITED.replace("D", "X")},
        equal=False,
    ),
    Case(
        "the edit changes a line it adds, under color.diff=always",
        BASE,
        {**BASE, "A.md": EDITED},
        BASE,
        {**BASE, "A.md": EDITED.replace("D", "X")},
        equal=False,
        config=(("color.diff", "always"), ("color.diff.meta", "")),
    ),
    Case(
        "the same edit lands in another file",
        BASE,
        {**BASE, "A.md": EDITED},
        BASE,
        {**BASE, "B.md": EDITED},
        equal=False,
    ),
    Case(
        "the same file is added under another name",
        BASE,
        {**BASE, "C.md": LINES},
        BASE,
        {**BASE, "D.md": LINES},
        equal=False,
    ),
    Case(
        "another file of the same lines is deleted",
        BASE,
        {"B.md": LINES},
        BASE,
        {"A.md": LINES},
        equal=False,
    ),
    Case(
        "a new file, rebased as the same lines added to an empty file",
        BASE,
        {**BASE, "C.md": LINES},
        {**BASE, "C.md": ""},
        {**BASE, "C.md": LINES},
        equal=False,
    ),
    Case(
        "a deleted file, rebased as the same file emptied of its lines",
        BASE,
        {"B.md": LINES},
        BASE,
        {**BASE, "A.md": ""},
        equal=False,
    ),
    Case(
        "edits in A.md alone, rebased as edits in A.md and B.md",
        FORGE,
        IN_A,
        FORGE,
        IN_A_AND_B,
        equal=False,
    ),
    Case(
        "edits in A.md and B.md, rebased as edits in A.md alone",
        FORGE,
        IN_A_AND_B,
        FORGE,
        IN_A,
        equal=False,
    ),
)


def run(case: Case, block: str, root: Path) -> str | None:
    """Run the block on one case and return what it got wrong, or None."""
    repo = Repo(root / "repo")
    for key, value in case.config:
        repo.git("config", key, value)
    cleared = repo.commit(case.cleared, repo.commit(case.old))
    rebased = repo.commit(case.rebased, repo.commit(case.new))
    script = (
        block.replace("<wt>", shlex.quote(repo.path))
        .replace("<cleared sha>", cleared)
        .replace("<new tip>", rebased)
    )
    left = re.findall(r"<[a-z][a-z ]*>", script)
    if left:
        return f"placeholders the test does not fill: {left}"
    done = subprocess.run(
        ["sh", "-c", script],
        capture_output=True,
        text=True,
        env=fixture_env(),
        check=False,
    )
    out = done.stdout.split("\n")
    shape = len(out) == 4 and out[3] == "" and out[2].isdigit()
    if done.returncode or done.stderr or not shape or out[2] == "0":
        return f"exit {done.returncode}\n{done.stdout}{done.stderr}"
    if (out[0] == out[1]) != case.equal:
        return f"hashes {'differ' if case.equal else 'are equal'}\n{done.stdout}"
    return None


def main() -> None:
    block = find_block()
    wrong = []
    for case in CASES:
        with tempfile.TemporaryDirectory() as root:
            why = run(case, block, Path(root))
        if why:
            wrong.append(f"{case.label}: {why}")
    if wrong:
        print("\n".join(wrong))
    sys.exit(1 if wrong else 0)


if __name__ == "__main__":
    main()
