#!/usr/bin/env python3
"""Run the clearance comparison of a rebase on fixture commits.

    python3 scripts/test-rebase-clearance.py

The comparison is the shell block of `process/*.md` that diffs
`<cleared sha>^` and `<new tip>^` (*A rebase and the clearance*). The test reads it from the
process, so it runs the commands a session pastes. Each case builds a
cleared commit and its rebased counterpart in a bare repository with git
plumbing, which writes commits without signing them, and runs the block
with `sh` on the two. It checks that the two hashes are equal where the
branch makes the same change to each file, and differ where it does not.
The fixtures' git calls run with none of the caller's `GIT_` variables
and no global or system git configuration; a case may set inert keys of
the fixture repository's own configuration and attributes. The script prints each case that answers
wrongly, and exits 1 where there is one.
"""

from __future__ import annotations

import os
import random
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


class Executable(str):
    """A file's text, committed with mode 100755 where a `str` is 100644."""


class Gitlink(str):
    """A submodule's commit id, committed as a gitlink with mode 160000."""


def fixture_env() -> dict[str, str]:
    """Return a fixture's environment: no `GIT_` of the caller's, no git config."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    return env


def find_block() -> str:
    """Return the one shell block of the process that diffs both commits."""
    found: list[str] = [
        block
        for path in sorted(PROCESS.glob("*.md"))
        for block in FENCE.findall(path.read_text())
        if "'<cleared sha>^'" in block and "'<new tip>^'" in block
    ]
    if len(found) != 1:
        sys.exit(f"{len(found)} blocks diff both commits, not one")
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
            if isinstance(text, Gitlink):
                blob, mode = str(text), "160000"
            else:
                blob = self.git("hash-object", "-w", "--stdin", data=text.encode())
                mode = "100755" if isinstance(text, Executable) else "100644"
            self.git(
                "update-index",
                "--add",
                "--cacheinfo",
                f"{mode},{blob},{name}",
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
    own git configuration, and `attributes` the lines of its
    `info/attributes`, as a reader's may set them: inert ones only, never a
    key or an attribute that names a program to run. `fails` says that git
    fails on them after printing the diff of a file before the failing one,
    so the block's run prints git's error. `environ` holds
    variables of the block's environment, as a reader's shell may export them.
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
        attributes: str = "",
        fails: bool = False,
        environ: tuple[tuple[str, str], ...] = (),
    ) -> None:
        self.label, self.equal, self.config = label, equal, config
        self.attributes, self.fails = attributes, fails
        self.environ = environ
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
# a NUL makes git read a file as binary
BINARY: Files = {**BASE, "C.bin": "\0a\n"}
# under an attribute that makes git read C.bin as text, a hunk holds a NUL
BYTES: Files = {**BASE, "C.bin": "base\0\n"}
SUB: Files = {**BASE, "S": Gitlink("1" * 40)}


def chunk(seed: int, alphabet: str) -> str:
    """Return 8192 characters drawn from `alphabet` by a generator seeded `seed`."""
    draw = random.Random(seed)
    return "".join(draw.choice(alphabet) for _ in range(8192))


# four chunks of bytes, NUL and newline among them, and four of text lines;
# git's binary patch of A+B to B+A copies from the old blob, so it reads
# the same as that of C+D to D+C
RAW = "".join(map(chr, range(128)))
TEXT = "abcdefghij \n"
BIN = [chunk(seed, RAW) for seed in range(4)]
TXT = [chunk(seed, TEXT) for seed in range(4)]

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
        "the same edit, rebased past lines added above it, under color.diff=always",
        BASE,
        {**BASE, "A.md": EDITED},
        {**BASE, "A.md": "z\n" * 9 + LINES},
        {**BASE, "A.md": "z\n" * 9 + EDITED},
        equal=True,
        config=(("color.diff", "always"),),
    ),
    Case(
        "the same edit, rebased past a change to the line above it",
        BASE,
        {**BASE, "A.md": EDITED},
        {**BASE, "A.md": LINES.replace("c", "C")},
        {**BASE, "A.md": EDITED.replace("c", "C")},
        equal=True,
    ),
    Case(
        "the same rename and edit, rebased past lines added above the edit",
        BASE,
        {"B.md": LINES, "C.md": EDITED},
        {**BASE, "A.md": "z\n" * 9 + LINES},
        {"B.md": LINES, "C.md": "z\n" * 9 + EDITED},
        equal=True,
    ),
    Case(
        "the same edit, rebased past a line above it emptied, under "
        "diff.suppressBlankEmpty",
        BASE,
        {**BASE, "A.md": EDITED},
        {**BASE, "A.md": LINES.replace("c", "")},
        {**BASE, "A.md": EDITED.replace("c", "")},
        equal=True,
        config=(("diff.suppressBlankEmpty", "true"),),
    ),
    Case(
        "the same rename and edit, rebased past lines added above the edit, "
        "under diff.renames=false",
        BASE,
        {"B.md": LINES, "C.md": EDITED},
        {**BASE, "A.md": "z\n" * 9 + LINES},
        {"B.md": LINES, "C.md": "z\n" * 9 + EDITED},
        equal=True,
        config=(("diff.renames", "false"),),
    ),
    Case(
        "the same two renames and edits, rebased past lines added above the "
        "edits, under diff.renameLimit=1",
        {"A.md": LINES, "B.md": LINES.upper()},
        {"C.md": EDITED, "D.md": LINES.upper().replace("D", "X")},
        {"A.md": "z\n" * 9 + LINES, "B.md": "z\n" * 9 + LINES.upper()},
        {
            "C.md": "z\n" * 9 + EDITED,
            "D.md": "z\n" * 9 + LINES.upper().replace("D", "X"),
        },
        equal=True,
        config=(("diff.renameLimit", "1"),),
    ),
    Case(
        "the same binary change, rebased past a commit to another file",
        BINARY,
        {**BINARY, "C.bin": "\0b\n"},
        {**BINARY, "D.md": "d\n"},
        {**BINARY, "C.bin": "\0b\n", "D.md": "d\n"},
        equal=True,
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
        "the same edit, rebased with another file renamed",
        BASE,
        {**BASE, "A.md": EDITED},
        BASE,
        {"A.md": EDITED, "C.md": LINES},
        equal=False,
    ),
    Case(
        "the same edit, rebased with another file made executable",
        BASE,
        {**BASE, "A.md": EDITED},
        BASE,
        {"A.md": EDITED, "B.md": Executable(LINES)},
        equal=False,
    ),
    Case(
        "a file made executable, rebased as the same file made not executable",
        BASE,
        {**BASE, "B.md": Executable(LINES)},
        {**BASE, "B.md": Executable(LINES)},
        BASE,
        equal=False,
    ),
    Case(
        "a new file, rebased as the same file added executable",
        BASE,
        {**BASE, "C.md": LINES},
        BASE,
        {**BASE, "C.md": Executable(LINES)},
        equal=False,
    ),
    Case(
        "an empty file added, rebased as an empty file deleted",
        BASE,
        {**BASE, "C.md": ""},
        {**BASE, "C.md": ""},
        BASE,
        equal=False,
    ),
    Case(
        "a line added at the end, rebased as the same line with no newline",
        BASE,
        {**BASE, "A.md": LINES + "g\n"},
        BASE,
        {**BASE, "A.md": LINES + "g"},
        equal=False,
    ),
    Case(
        "a binary file changed, rebased as changed to other bytes",
        BINARY,
        {**BINARY, "C.bin": "\0b\n"},
        BINARY,
        {**BINARY, "C.bin": "\0c\n"},
        equal=False,
    ),
    Case(
        "the same binary change, rebased past a commit to another file, under "
        "the attribute diff",
        BYTES,
        {**BYTES, "C.bin": "ab\0c\n"},
        {**BYTES, "D.md": "d\n"},
        {**BYTES, "C.bin": "ab\0c\n", "D.md": "d\n"},
        equal=True,
        attributes="*.bin diff\n",
    ),
    Case(
        "a binary file changed, rebased as changed to other bytes, under the "
        "attribute diff",
        BYTES,
        {**BYTES, "C.bin": "ab\0c\n"},
        BYTES,
        {**BYTES, "C.bin": "a\0bc\n"},
        equal=False,
        attributes="*.bin diff\n",
    ),
    Case(
        "a binary file changed, rebased as changed to other bytes, under a "
        "diff driver with binary=false",
        BYTES,
        {**BYTES, "C.bin": "ab\0c\n"},
        BYTES,
        {**BYTES, "C.bin": "a\0bc\n"},
        equal=False,
        config=(("diff.x.binary", "false"),),
        attributes="*.bin diff=x\n",
    ),
    Case(
        "a binary file's halves swapped, rebased as two other halves swapped",
        {**BASE, "C.bin": BIN[0] + BIN[1]},
        {**BASE, "C.bin": BIN[1] + BIN[0]},
        {**BASE, "C.bin": BIN[2] + BIN[3]},
        {**BASE, "C.bin": BIN[3] + BIN[2]},
        equal=False,
    ),
    Case(
        "a file's halves swapped, rebased as two other halves swapped, under "
        "the attribute -diff",
        {**BASE, "C.bin": TXT[0] + TXT[1]},
        {**BASE, "C.bin": TXT[1] + TXT[0]},
        {**BASE, "C.bin": TXT[2] + TXT[3]},
        {**BASE, "C.bin": TXT[3] + TXT[2]},
        equal=False,
        attributes="*.bin -diff\n",
    ),
    Case(
        "the same edit, rebased past lines added above it, under the attribute -diff",
        BASE,
        {**BASE, "A.md": EDITED},
        {**BASE, "A.md": "z\n" * 9 + LINES},
        {**BASE, "A.md": "z\n" * 9 + EDITED},
        equal=True,
        attributes="*.md -diff\n",
    ),
    Case(
        "the same edit to A.md, rebased with Z.bin changed to other bytes, where "
        "git diff fails at Z.bin",
        {"A.md": "a\n", "Z.bin": "base\0\n"},
        {"A.md": "b\n", "Z.bin": "one\0\n"},
        {"A.md": "a\n", "Z.bin": "base\0\n"},
        {"A.md": "b\n", "Z.bin": "two\0\n"},
        equal=False,
        config=(("diff.x.xfuncname", "["),),
        attributes="Z.bin diff=x\n",
        fails=True,
    ),
    Case(
        "the same edits, rebased past a commit to another file, where git diff "
        "fails at Z.bin",
        {"A.md": "a\n", "Z.bin": "base\0\n"},
        {"A.md": "b\n", "Z.bin": "one\0\n"},
        {"A.md": "a\n", "Z.bin": "base\0\n", "D.md": "d\n"},
        {"A.md": "b\n", "Z.bin": "one\0\n", "D.md": "d\n"},
        equal=False,
        config=(("diff.x.xfuncname", "["),),
        attributes="Z.bin diff=x\n",
        fails=True,
    ),
    Case(
        "a binary file changed, rebased as changed to other bytes, under "
        "GREP_OPTIONS=-m1",
        BYTES,
        {**BYTES, "C.bin": "one\0\n"},
        BYTES,
        {**BYTES, "C.bin": "two\0\n"},
        equal=False,
        environ=(("GREP_OPTIONS", "-m1"),),
    ),
    Case(
        "the same edits, rebased past a commit to another file, where git diff "
        "fails at Z.bin, under GREP_OPTIONS=-m1",
        {"A.md": "a\n", "Z.bin": "base\0\n"},
        {"A.md": "b\n", "Z.bin": "one\0\n"},
        {"A.md": "a\n", "Z.bin": "base\0\n", "D.md": "d\n"},
        {"A.md": "b\n", "Z.bin": "one\0\n", "D.md": "d\n"},
        equal=False,
        config=(("diff.x.xfuncname", "["),),
        attributes="Z.bin diff=x\n",
        fails=True,
        environ=(("GREP_OPTIONS", "-m1"),),
    ),
    Case(
        "a binary line's CR dropped, rebased past a commit to another file, "
        "under PERLIO=:crlf",
        BYTES,
        {**BYTES, "C.bin": "a\0\r\n"},
        {**BYTES, "D.md": "d\n"},
        {**BYTES, "C.bin": "a\0\n", "D.md": "d\n"},
        equal=False,
        environ=(("PERLIO", ":crlf"),),
    ),
    Case(
        "the same edit, rebased past lines added above it, under GIT_DIFF_OPTS=-u0",
        BASE,
        {**BASE, "A.md": EDITED},
        {**BASE, "A.md": "z\n" * 9 + LINES},
        {**BASE, "A.md": "z\n" * 9 + EDITED},
        equal=True,
        environ=(("GIT_DIFF_OPTS", "-u0"),),
    ),
    Case(
        "a submodule moved, rebased as moved elsewhere, under "
        "diff.ignoreSubmodules=all",
        SUB,
        {**SUB, "A.md": EDITED, "S": Gitlink("2" * 40)},
        SUB,
        {**SUB, "A.md": EDITED, "S": Gitlink("3" * 40)},
        equal=False,
        config=(("diff.ignoreSubmodules", "all"),),
    ),
    Case(
        "a submodule moved, rebased as moved to a commit of the same short id, "
        "under diff.submodule=log",
        SUB,
        {**SUB, "A.md": EDITED, "S": Gitlink("2" * 40)},
        SUB,
        {**SUB, "A.md": EDITED, "S": Gitlink("2" * 7 + "3" * 33)},
        equal=False,
        config=(("diff.submodule", "log"),),
    ),
    Case(
        "the edit changes a line it adds, under core.bigFileThreshold",
        BASE,
        {**BASE, "A.md": EDITED},
        BASE,
        {**BASE, "A.md": EDITED.replace("D", "X")},
        equal=False,
        config=(("core.bigFileThreshold", "8"),),
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
    if case.attributes:
        Path(repo.path, "info", "attributes").write_text(case.attributes)
    cleared = repo.commit(case.cleared, repo.commit(case.old))
    rebased = repo.commit(case.rebased, repo.commit(case.new))
    for commit in (cleared, rebased) if case.fails else ():
        diff = subprocess.run(
            [
                "git",
                "-C",
                repo.path,
                "diff",
                "--no-color",
                "--text",
                f"{commit}^",
                commit,
            ],
            capture_output=True,
            env=fixture_env(),
            check=False,
        )
        if not diff.returncode or not diff.stdout.startswith(b"diff --git "):
            return f"git diff does not fail partway: exit {diff.returncode}"
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
        env={**fixture_env(), **dict(case.environ)},
        check=False,
    )
    out = done.stdout.split("\n")
    shape = len(out) == 4 and out[3] == "" and out[2].isdigit()
    if done.returncode or bool(done.stderr) != case.fails or not shape or out[2] == "0":
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
