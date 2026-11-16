"""Run the rebase clearance comparison on small branches and check it.

    python3 scripts/test-rebase-clearance.py

The comparison is the shell block of process/orchestration.md's *A
rebase and the clearance* that hashes two diffs, read from that file.
Each case is a repository whose cleared commit makes one text edit and
whose new tip, on a base that has moved, makes the same edit and
possibly one change more. The script prints each case whose answer is
wrong, and exits 1 where there is one.
"""

import os
import shlex
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "process" / "orchestration.md"
ENV = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}
BASE = {
    "a.txt": b"one\ntwo\nthree\n",
    "b.txt": b"kept\n",
    "c.bin": bytes(range(256)),
    "d.sh": b"echo d\n",
}


def write(root: Path, name: str, data: bytes) -> None:
    """Write a file of the tree."""
    (root / name).write_bytes(data)


def nothing(root: Path) -> None:
    """Change nothing more."""


def rename(root: Path) -> None:
    """Rename a file, its content kept."""
    (root / "b.txt").rename(root / "e.txt")


def mode(root: Path) -> None:
    """Make a file executable, its content kept."""
    (root / "d.sh").chmod(0o755)


def binary(root: Path) -> None:
    """Change a binary file's content."""
    write(root, "c.bin", bytes(reversed(range(256))))


def text(root: Path) -> None:
    """Edit another text file."""
    write(root, "b.txt", b"changed\n")


# (name, the change the new tip makes beside the edit, whether the
# clearance stands)
CASES: list[tuple[str, Callable[[Path], None], bool]] = [
    ("the edit alone", nothing, True),
    ("a rename", rename, False),
    ("a mode change", mode, False),
    ("a binary change", binary, False),
    ("another text edit", text, False),
]


def git(root: Path, *args: str) -> str:
    """Run git in the repository and return what it prints."""
    done = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=True,
        env=ENV,
    )
    return done.stdout.strip()


def commit(root: Path, message: str) -> str:
    """Commit the whole tree and return the commit's sha."""
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", message)
    return git(root, "rev-parse", "HEAD")


def block() -> str:
    """Return the comparison's shell block."""
    doc = DOC.read_text(encoding="utf-8")
    start = doc.index("```shell\nhdr=") + len("```shell\n")
    return doc[start : doc.index("```", start)]


def stands(change: Callable[[Path], None]) -> bool:
    """Say whether the comparison keeps the clearance over this change."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        git(root, "init", "-q")
        for name, data in BASE.items():
            write(root, name, data)
        base = commit(root, "base")
        write(root, "a.txt", b"one\nTWO\nthree\n")
        cleared = commit(root, "the edit")
        git(root, "checkout", "-q", base)
        write(root, "m.txt", b"main moved\n")
        commit(root, "main")
        write(root, "a.txt", b"one\nTWO\nthree\n")
        change(root)
        tip = commit(root, "the edit, rebased")
        script = (
            block()
            .replace("<wt>", shlex.quote(tmp))
            .replace("<cleared sha>", cleared)
            .replace("<new tip>", tip)
        )
        done = subprocess.run(
            ["sh", "-c", script],
            capture_output=True,
            text=True,
            check=True,
            env=ENV,
        )
        lines = done.stdout.split("\n")
        return lines[0] == lines[1] and lines[2] != "0"


def main() -> None:
    """Print each case the comparison answers wrongly, and exit 1 on one."""
    wrong = [
        f"{'refused' if expected else 'kept'}: {name}"
        for name, change, expected in CASES
        if stands(change) != expected
    ]
    if wrong:
        print("\n".join(wrong))
    sys.exit(1 if wrong else 0)


if __name__ == "__main__":
    main()
