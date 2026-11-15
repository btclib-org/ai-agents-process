#!/usr/bin/env python3
"""Run port-check.py on fixture repositories and check what it answers.

    python3 scripts/test-port-check.py

Each case builds a standard and a tree in a temporary directory with git
plumbing, which writes commits without signing them, runs the script,
and checks its exit code and the lines it must print. The fixtures' own
git calls run with none of the caller's `GIT_` variables. A case that makes
one git call fail puts a stand-in `git` first on `PATH`. The script
prints each case that answers wrongly, and exits 1 where there is one.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import TypeAlias

SCRIPT = Path(__file__).with_name("port-check.py")
M = "\n## This repository in particular\n"
README = """# The standard

## 14. Copied verbatim

**The same file in every repository**, and deliberately so.

- `A.md` — owed by every repository.
- `B.md` — owed by every repository; it wraps
  onto a second line.
- `C.toml` — owed where `*.toml`.
- `RELEASING.md` — owed where `release.yml`, and the source is this
  repository's `shared/RELEASING.md`.

**Decided per repository**: everything else.
"""
Files: TypeAlias = dict[str, str | tuple[str, str]]


def fixture_env() -> dict[str, str]:
    """Return the environment of a fixture's git call: none of the caller's `GIT_`."""
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


class Repo:
    """A bare repository the fixtures write objects into."""

    def __init__(self, path: Path) -> None:
        self.path = str(path)
        subprocess.run(
            ["git", "init", "-q", "--bare", self.path], check=True, env=fixture_env()
        )
        self.clock = 1_700_000_000
        self.last = ""

    def git(self, *args: str, data: bytes | None = None) -> str:
        done = subprocess.run(
            ["git", "-C", self.path, *args],
            input=data,
            capture_output=True,
            check=True,
            env=fixture_env(),
        )
        return done.stdout.decode().strip()

    def commit(self, files: Files, subject: str = "fixture", *parents: str) -> str:
        index = os.path.join(self.path, "fixture-index")
        if os.path.exists(index):
            os.remove(index)
        env = dict(fixture_env(), GIT_INDEX_FILE=index)
        for name, value in files.items():
            mode, text = value if isinstance(value, tuple) else ("100644", value)
            blob = text  # a gitlink names its commit
            if mode != "160000":
                blob = self.git("hash-object", "-w", "--stdin", data=text.encode())
            subprocess.run(
                ["git", "-C", self.path, "update-index", "--add", "--cacheinfo"]
                + [f"{mode},{blob},{name}"],
                env=env,
                check=True,
            )
        tree = subprocess.run(
            ["git", "-C", self.path, "write-tree"],
            env=env,
            capture_output=True,
            check=True,
        ).stdout.decode()
        self.clock += 60
        who = f"Fixture <fixture@example.invalid> {self.clock} +0000"
        body = f"tree {tree.strip()}\n"
        body += "".join(f"parent {p}\n" for p in parents)
        body += f"author {who}\ncommitter {who}\n\n{subject}\n"
        self.last = self.git(
            "hash-object", "-t", "commit", "-w", "--stdin", data=body.encode()
        )
        return self.last


class Case:
    """One run of the script and what it has to answer."""

    def __init__(
        self,
        label: str,
        build: Build,
        code: int,
        lines: tuple[str, ...] = (),
        absent: tuple[str, ...] = (),
        fail: tuple[str, str] | None = None,
    ) -> None:
        self.label, self.build, self.code = label, build, code
        self.lines, self.absent, self.fail = lines, absent, fail


Build: TypeAlias = Callable[[Repo, Repo], tuple[str, str, str]]


def std_at(std: Repo, extra: Files | None = None, readme: str = README) -> str:
    files: Files = {"README.md": readme, "A.md": "new\n", "B.md": "same\n"}
    files.update(extra or {})
    return std.commit(files, "standard")


def batch(tree: Repo, old: Files, new: Files, record: str = "") -> tuple[str, str]:
    root = tree.commit(old, "tree before")
    base = tree.commit(old, record, root) if record else root
    return base, tree.commit(new, "Port the batch", base)


OLD: Files = {"A.md": "old\n", "B.md": "same\n"}
NEW: Files = {"A.md": "new\n", "B.md": "same\n"}


def equal(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s = std_at(std)
    return (s, *batch(tree, OLD, NEW))


def unknown_standard(std: Repo, tree: Repo) -> tuple[str, str, str]:
    std_at(std)
    return ("not-a-ref", *batch(tree, OLD, NEW))


def unknown_base(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s = std_at(std)
    return (s, "0" * 40, batch(tree, OLD, NEW)[1])


def empty_batch(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s = std_at(std)
    base = batch(tree, OLD, NEW)[0]
    return (s, base, base)


def marked(std_own: str, base_own: str, head_own: str, head_top: str = "new") -> Build:
    def build(std: Repo, tree: Repo) -> tuple[str, str, str]:
        s = std_at(std, {"A.md": "new" + M + std_own})
        old = {**OLD, "A.md": "old" + M + base_own}
        new = {**NEW, "A.md": head_top + M + head_own}
        return (s, *batch(tree, old, new))

    return build


def heading_base_only(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s = std_at(std)
    return (s, *batch(tree, {**OLD, "A.md": "old" + M + "x\n"}, NEW))


def heading_standard_only(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s = std_at(std, {"A.md": "new" + M + "std\n"})
    return (s, *batch(tree, OLD, {**NEW, "A.md": "new" + M + "std\n"}))


def standard_adds(marker: str) -> Build:
    """List a `D.md` the tree lacks, its line opening with `marker`."""

    def build(std: Repo, tree: Repo) -> tuple[str, str, str]:
        readme = README.replace(
            "- `C.toml`", f"{marker}`D.md` — owed by every repository.\n- `C.toml`"
        )
        s = std_at(std, {"D.md": "added\n"}, readme)
        return (s, *batch(tree, OLD, NEW))

    return build


def standard_renames(std: Repo, tree: Repo) -> tuple[str, str, str]:
    readme = README.replace("`B.md`", "`E.md`")
    old = std.commit({"README.md": readme, "A.md": "old\n", "E.md": "same\n"})
    s = std.commit(
        {"README.md": readme, "A.md": "new\n", "E.md": "same\n"}, "standard", old
    )
    return (s, *batch(tree, OLD, NEW))


def symlink(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s = std_at(std)
    return (s, *batch(tree, OLD, {**NEW, "A.md": ("120000", "new\n")}))


def executable(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s = std_at(std)
    return (s, *batch(tree, OLD, {**NEW, "A.md": ("100755", "new\n")}))


def changed_not_in_standard(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s = std_at(std)
    return (s, *batch(tree, OLD, {**NEW, "extra.md": "x\n"}))


def off_main(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s = std_at(std)
    std.commit({"README.md": README, "A.md": "new\n", "B.md": "same\n"}, "other root")
    return (s, *batch(tree, OLD, NEW))


def base_not_parent(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s = std_at(std)
    base = batch(tree, OLD, NEW)[0]
    return (s, base, tree.commit(NEW, "unrelated head"))


def base_off_main(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s = std_at(std)
    base, head = batch(tree, OLD, NEW)
    os.environ["PORT_CHECK_TREE_MAIN"] = tree.commit(OLD, "another main")
    return (s, base, head)


def not_compared(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s = std_at(std, {"AUTHORS.md": "a\n"})
    return (s, *batch(tree, {**OLD, "AUTHORS.md": "b\n"}, {**NEW, "AUTHORS.md": "a\n"}))


def pathspec(carried: bool) -> Build:
    def build(std: Repo, tree: Repo) -> tuple[str, str, str]:
        readme = README.replace(
            "- `C.toml`", "- `D.md` — owed where `docs`.\n- `C.toml`"
        )
        s = std_at(std, {"D.md": "d\n"}, readme)
        extra: Files = {"docs/x.md": "x\n"} if carried else {}
        return (s, *batch(tree, {**OLD, **extra}, {**NEW, **extra}))

    return build


def not_utf8(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s = std_at(std)
    return (s, *batch(tree, OLD, {**NEW, "bad\udcff.md": "x\n"}))


def ordinary_add(std: Repo, tree: Repo) -> tuple[str, str, str]:
    old = std.commit({"README.md": README, "A.md": "old\n"})
    s = std.commit({"README.md": README, **NEW}, "standard", old)
    return (s, *batch(tree, {"A.md": "old\n"}, NEW))


def owed_deleted(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s = std_at(std)
    return (s, *batch(tree, OLD, {"A.md": "new\n"}))


def both_missing(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s = std_at(std)
    return (s, *batch(tree, {**OLD, "gone.md": "g\n"}, NEW))


def spaced(head_text: str) -> Build:
    def build(std: Repo, tree: Repo) -> tuple[str, str, str]:
        readme = README.replace(
            "- `C.toml`", "- `a b.md` — owed by every repository.\n- `C.toml`"
        )
        s = std_at(std, {"a b.md": "spaced\n"}, readme)
        old = {**OLD, "a b.md": "old\n"}
        return (s, *batch(tree, old, {**NEW, "a b.md": head_text}))

    return build


def bytes_of_a(std_text: str, head_text: str) -> Build:
    def build(std: Repo, tree: Repo) -> tuple[str, str, str]:
        s = std_at(std, {"A.md": std_text})
        return (s, *batch(tree, OLD, {**NEW, "A.md": head_text}))

    return build


def toml(carried: bool) -> Build:
    def build(std: Repo, tree: Repo) -> tuple[str, str, str]:
        s = std_at(std, {"C.toml": "c = 1\n"})
        extra: Files = {"x.toml": "y = 2\n"} if carried else {}
        return (s, *batch(tree, {**OLD, **extra}, {**NEW, **extra}))

    return build


def releasing(head_text: str) -> Build:
    def build(std: Repo, tree: Repo) -> tuple[str, str, str]:
        s = std_at(std, {"shared/RELEASING.md": "rel\n"})
        old = {**OLD, "release.yml": "r\n", "RELEASING.md": "old rel\n"}
        new = {**NEW, "release.yml": "r\n", "RELEASING.md": head_text}
        return (s, *batch(tree, old, new))

    return build


def no_list(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s = std_at(std, readme="# The standard\n")
    return (s, *batch(tree, OLD, NEW))


def failed_read(listing: bool) -> Build:
    """Make one read of the base fail: its listing, or the blob it lists.

    The base carries a record, so that only the comparison reads it.
    """

    def build(std: Repo, tree: Repo) -> tuple[str, str, str]:
        s = std_at(std)
        base, head = batch(tree, OLD, NEW, f"Port btclib-org/.github@{s}")
        blob = tree.git("hash-object", "--stdin", data=b"old\n")
        fail = f"ls-tree -z --full-tree {base}" if listing else f"cat-file blob {blob}"
        os.environ["PORT_CHECK_FAIL"] = fail
        return (s, base, head)

    return build


def recorded(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s1 = std_at(std)
    s2 = std.commit(
        {"README.md": README, "A.md": "new\n", "B.md": "same\n"}, "later", s1
    )
    return (s2, *batch(tree, OLD, NEW, f"Port btclib-org/.github@{s1[:12]} (#5)"))


def two_records(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s1 = std_at(std)
    s2 = std.commit(
        {"README.md": README, "A.md": "new\n", "B.md": "same\n"}, "later", s1
    )
    root = tree.commit(OLD, f"Port btclib-org/.github@{s1}")
    mid = tree.commit(OLD, "Port btclib-org/.github@not-a-sha", root)
    base = tree.commit(OLD, f"Port btclib-org/.github@{s2[:7]} (issue x#1)", mid)
    os.environ["PORT_CHECK_EXPECT"] = s2
    return (s2, base, tree.commit(NEW, "Port the batch", base))


def stale_record(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s = std_at(std)
    return (s, *batch(tree, OLD, NEW, "Port btclib-org/.github@" + "ab" * 20))


def failed_log(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s = std_at(std)
    os.environ["PORT_CHECK_FAIL"] = "-z --format=%s"
    os.environ["PORT_CHECK_PRINT"] = f"Port btclib-org/.github@{s}"
    return (s, *batch(tree, OLD, NEW))


def history(
    std: Repo, tops: list[tuple[str, str]], extra: list[Files] | None = None
) -> list[str]:
    """Commit the standard's `A.md` as `(above, own)` pairs, oldest first."""
    parent: list[str] = []
    out: list[str] = []
    for i, (top, own) in enumerate(tops):
        files: Files = {"README.md": README, "A.md": top + M + own, "B.md": "same\n"}
        files.update((extra or [{}] * len(tops))[i])
        c = std.commit(files, f"standard {i}", *parent)
        parent, out = [c], out + [c]
    return out


def guess_run(std: Repo, tree: Repo) -> tuple[str, str, str]:
    cs = history(std, [("t", "1\n"), ("t", "2\n"), ("t", "3\n")])
    old: Files = {"A.md": "t" + M + "mine\n", "B.md": "same\n"}
    os.environ["PORT_CHECK_EXPECT"] = cs[0]
    return (cs[-1], *batch(tree, old, {**old, "x.md": "y\n"}))


def guess_newest_run(std: Repo, tree: Repo) -> tuple[str, str, str]:
    cs = history(std, [("t", "1\n"), ("u", "1\n"), ("t", "2\n")])
    old: Files = {"A.md": "t" + M + "mine\n", "B.md": "same\n"}
    os.environ["PORT_CHECK_EXPECT"] = cs[2]
    return (cs[-1], *batch(tree, old, {**old, "x.md": "y\n"}))


def unported_workflow(std: Repo, tree: Repo) -> tuple[str, str, str]:
    wf: list[Files] = [{"w.yml": "v1\n"}, {"w.yml": "v2\n"}, {"w.yml": "v2\n"}]
    cs = history(std, [("t", "1\n"), ("t", "1\n"), ("t", "2\n")], wf)
    old: Files = {"A.md": "t" + M + "mine\n", "B.md": "same\n", "w.yml": "v1\n"}
    os.environ["PORT_CHECK_EXPECT"] = cs[0]
    return (cs[-1], *batch(tree, old, {**old, "x.md": "y\n"}))


def guess_newest_start(std: Repo, tree: Repo) -> tuple[str, str, str]:
    bs: list[Files] = [{"B.md": "b0\n"}, {}, {}]
    cs = history(std, [("t", "1\n"), ("t", "1\n"), ("t", "1\n")], bs)
    old: Files = {"A.md": "t" + M + "mine\n", "B.md": "same\n"}
    os.environ["PORT_CHECK_EXPECT"] = cs[1]
    return (cs[-1], *batch(tree, old, {**old, "x.md": "y\n"}))


def guess_read_error(std: Repo, tree: Repo) -> tuple[str, str, str]:
    cs = history(std, [("t", "1\n"), ("t", "2\n"), ("t", "3\n")])
    old: Files = {"A.md": "t" + M + "mine\n", "B.md": "same\n"}
    os.environ["PORT_CHECK_FAIL"] = f"ls-tree -z --full-tree {cs[1]}"
    return (cs[-1], *batch(tree, old, {**old, "x.md": "y\n"}))


def guess_read_error_between(std: Repo, tree: Repo) -> tuple[str, str, str]:
    cs = history(std, [("t", "1\n"), ("u", "1\n"), ("t", "2\n")])
    old: Files = {"A.md": "t" + M + "mine\n", "B.md": "same\n"}
    os.environ["PORT_CHECK_FAIL"] = f"ls-tree -z --full-tree {cs[1]}"
    return (cs[-1], *batch(tree, old, {**old, "x.md": "y\n"}))


def ignored_submodules(local: bool) -> Build:
    """Change a gitlink with `diff.ignoreSubmodules=all` set, locally or not."""

    def build(std: Repo, tree: Repo) -> tuple[str, str, str]:
        s = std_at(std)
        one = tree.commit({"v": "1\n"}, "submodule one")
        two = tree.commit({"v": "2\n"}, "submodule two", one)
        ignore(tree, local)
        return (
            s,
            *batch(
                tree,
                {**OLD, "vendor": ("160000", one)},
                {**NEW, "vendor": ("160000", two)},
            ),
        )

    return build


def ignore(tree: Repo, local: bool) -> None:
    if local:
        tree.git("config", "diff.ignoreSubmodules", "all")
    else:
        os.environ["GIT_CONFIG_COUNT"] = "1"
        os.environ["GIT_CONFIG_KEY_0"] = "diff.ignoreSubmodules"
        os.environ["GIT_CONFIG_VALUE_0"] = "all"


def owed_by_a_gitlink(std: Repo, tree: Repo) -> tuple[str, str, str]:
    readme = README.replace("- `C.toml`", "- `D.md` — owed where `vendor`.\n- `C.toml`")
    s = std_at(std, {"D.md": "d\n"}, readme)
    one = tree.commit({"v": "1\n"}, "submodule")
    ignore(tree, True)
    link: Files = {"vendor": ("160000", one)}
    return (s, *batch(tree, {**OLD, **link}, {**NEW, **link}))


def own_part_overwritten(heading: str, at_start: bool) -> Build:
    """Replace the tree's own part with the standard's, the heading as given."""

    def build(std: Repo, tree: Repo) -> tuple[str, str, str]:
        top = "" if at_start else "new\n"
        s = std_at(std, {"A.md": top + heading + "std\n"})
        old = {**OLD, "A.md": ("" if at_start else "old\n") + heading + "tree\n"}
        return (s, *batch(tree, old, {**NEW, "A.md": top + heading + "std\n"}))

    return build


def before_the_record(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s1 = std_at(std)
    s2 = std.commit(
        {"README.md": README, "A.md": "newer\n", "B.md": "same\n"}, "later", s1
    )
    base, head = batch(tree, OLD, NEW, f"Port btclib-org/.github@{s2}")
    return (s1, base, head)


def callers_git_dir(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s = std_at(std)
    base, head = batch(tree, OLD, {**NEW, "A.md": "off\n"})
    os.environ["PORT_CHECK_GIT_DIR"] = tree.path
    return (s, base, head)


def replaced(std: Repo, tree: Repo) -> tuple[str, str, str]:
    """Make the head's copy read as the standard's through a replace object."""
    s = std_at(std)
    base, head = batch(tree, OLD, {**NEW, "A.md": "off\n"})
    off = tree.git("hash-object", "-w", "--stdin", data=b"off\n")
    new = tree.git("hash-object", "-w", "--stdin", data=b"new\n")
    tree.git("replace", "-f", off, new)
    return (s, base, head)


def no_git(std: Repo, tree: Repo) -> tuple[str, str, str]:
    os.environ["PORT_CHECK_NO_GIT"] = "1"
    return equal(std, tree)


def guess_nothing(std: Repo, tree: Repo) -> tuple[str, str, str]:
    cs = history(std, [("t", "1\n")])
    old: Files = {"A.md": "other" + M + "mine\n", "B.md": "different\n"}
    return (cs[-1], *batch(tree, old, {**old, "x.md": "y\n"}))


def guess_nothing_equal(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s = std_at(std)
    return (s, *batch(tree, {"A.md": "other\n", "B.md": "different\n"}, NEW))


def no_copies(std: Repo, tree: Repo) -> tuple[str, str, str]:
    s = std_at(std)
    return (s, *batch(tree, {"x.md": "y\n"}, {**NEW, "x.md": "y\n"}))


CASES = [
    Case("equal", equal, 0, ("equal A.md", "equal B.md", "(guessed")),
    Case("an unknown <S>", unknown_standard, 2, ("FAILED:",)),
    Case("an unknown base", unknown_base, 2, ("FAILED:",)),
    Case("an empty batch", empty_batch, 2, ("FAILED: the batch changes no file",)),
    Case("own part kept", marked("std\n", "tree\n", "tree\n"), 0, ("equal A.md",)),
    Case("own part changed", marked("std\n", "tree\n", "trea\n"), 1, ("DIFFERS A.md",)),
    Case(
        "one byte off above", marked("s\n", "t\n", "t\n", "neW"), 1, ("DIFFERS A.md",)
    ),
    Case("heading in base only", heading_base_only, 1, ("DIFFERS A.md: the heading",)),
    Case(
        "heading in <S> only", heading_standard_only, 1, ("DIFFERS A.md: the heading",)
    ),
    Case(
        "<S> adds a file",
        standard_adds("- "),
        1,
        ("DIFFERS D.md: missing in the tree",),
    ),
    *(
        Case(
            f"<S> adds a file under {marker!r}",
            standard_adds(marker),
            2,
            ("FAILED: a line of section 14's list is not a dash bullet",),
            ("DIFFERS",),
        )
        for marker in ("* ", "+ ", "1. ", " - ")
    ),
    Case(
        "<S> renames a file",
        standard_renames,
        1,
        ("DIFFERS E.md: missing in the tree",),
    ),
    Case("a symlink", symlink, 1, ("DIFFERS A.md: mode 120000",)),
    Case("an executable", executable, 1, ("DIFFERS A.md: mode 100755",)),
    Case(
        "not in <S>",
        changed_not_in_standard,
        1,
        ("DIFFERS extra.md: not a copy section 14 compares",),
    ),
    Case(
        "not compared, at <S>'s bytes",
        not_compared,
        1,
        ("DIFFERS AUTHORS.md: not a copy section 14 compares",),
    ),
    Case("a pathspec condition met", pathspec(True), 1, ("DIFFERS D.md: missing",)),
    Case("a pathspec condition unmet", pathspec(False), 0, ("equal A.md",), ("D.md",)),
    Case("a path that is not UTF-8", not_utf8, 2, ("FAILED:",)),
    Case("<S> off the standard's main", off_main, 2, ("FAILED: <S>",)),
    Case("<base> not before <head>", base_not_parent, 2, ("FAILED: <base>",)),
    Case("<base> off the tree's main", base_off_main, 2, ("FAILED: <base>",)),
    Case("an ordinary add", ordinary_add, 0, ("equal A.md", "equal B.md")),
    Case("owed, deleted", owed_deleted, 1, ("DIFFERS B.md: missing in the tree",)),
    Case(
        "missing on both",
        both_missing,
        1,
        ("DIFFERS gone.md: not a copy section 14 compares",),
    ),
    Case("a name with a space", spaced("spaced\n"), 0, ("equal a b.md",)),
    Case("a name with a space, off", spaced("spaceD\n"), 1, ("DIFFERS a b.md",)),
    Case("two empty copies", bytes_of_a("", ""), 0, ("equal A.md",)),
    Case("an empty copy, off", bytes_of_a("", "\n"), 1, ("DIFFERS A.md",)),
    Case("CRLF on both", bytes_of_a("x\r\ny\r\n", "x\r\ny\r\n"), 0, ("equal A.md",)),
    Case("CRLF turned LF", bytes_of_a("x\r\ny\r\n", "x\ny\n"), 1, ("DIFFERS A.md",)),
    Case("*.toml not carried", toml(False), 0, ("equal A.md",), ("C.toml",)),
    Case("*.toml carried", toml(True), 1, ("DIFFERS C.toml: missing in the tree",)),
    Case("RELEASING.md source", releasing("rel\n"), 0, ("equal RELEASING.md",)),
    Case("RELEASING.md off", releasing("rel!\n"), 1, ("DIFFERS RELEASING.md",)),
    Case("no section 14", no_list, 2, ("FAILED: section 14",)),
    Case("a base read fails", failed_read(False), 2, ("FAILED:",), ("equal",)),
    Case("a base listing fails", failed_read(True), 2, ("FAILED:",), ("equal",)),
    Case("a record", recorded, 0, ("(recorded: Port btclib-org/.github@", "later")),
    Case("the newest record", two_records, 0, ("(recorded: Port btclib-org/.github@",)),
    Case("a record the standard lacks", stale_record, 2, ("FAILED:",)),
    Case("git log fails", failed_log, 2, ("FAILED:",), ("last port",)),
    Case("guess: oldest of the run", guess_run, 1, ("guessed", "DIFFERS x.md")),
    Case("guess: newest run only", guess_newest_run, 1, ("guessed",)),
    Case("guess: the newest file's run", guess_newest_start, 1, ("guessed",)),
    Case("guess: unported workflow", unported_workflow, 1, ("guessed", "standard 1")),
    Case("guess: a read fails", guess_read_error, 2, ("FAILED:",), ("last port",)),
    Case("guess: a read fails between runs", guess_read_error_between, 2, ("FAILED:",)),
    Case("guess: nothing matches", guess_nothing, 2, ("last port: unknown",)),
    Case(
        "guess: nothing matches, copies equal",
        guess_nothing_equal,
        2,
        ("equal A.md", "FAILED: the last port is unknown"),
    ),
    Case("a tree without copies", no_copies, 2, ("FAILED: the last port is unknown",)),
    Case(
        "a gitlink, submodules ignored by the caller",
        ignored_submodules(False),
        1,
        ("DIFFERS vendor: not a copy section 14 compares",),
    ),
    Case(
        "a gitlink, submodules ignored by the tree",
        ignored_submodules(True),
        1,
        ("DIFFERS vendor: not a copy section 14 compares",),
    ),
    Case("owed where a gitlink is", owed_by_a_gitlink, 1, ("DIFFERS D.md: missing",)),
    Case(
        "own part overwritten, heading in CRLF",
        own_part_overwritten("\r\n## This repository in particular\r\n", False),
        2,
        ("FAILED:",),
        ("equal A.md",),
    ),
    Case(
        "own part overwritten, heading at byte zero",
        own_part_overwritten("## This repository in particular\n", True),
        2,
        ("FAILED:",),
        ("equal A.md",),
    ),
    Case("<S> before the record", before_the_record, 2, ("FAILED: the recorded",)),
    Case("git not on PATH", no_git, 2, ("FAILED:",)),
    Case("the caller's GIT_DIR", callers_git_dir, 1, ("DIFFERS A.md",)),
    Case("a replace object", replaced, 1, ("DIFFERS A.md",)),
]

STAND_IN = """#!/bin/sh
case "$*" in
*"$PORT_CHECK_FAIL"*) printf '%s' "$PORT_CHECK_PRINT"; exit 73 ;;
esac
exec {git} "$@"
"""


KEYS = (
    "PORT_CHECK_FAIL",
    "PORT_CHECK_PRINT",
    "PORT_CHECK_EXPECT",
    "PORT_CHECK_TREE_MAIN",
    "PORT_CHECK_NO_GIT",
    "GIT_CONFIG_COUNT",
    "GIT_CONFIG_KEY_0",
    "GIT_CONFIG_VALUE_0",
    "PORT_CHECK_GIT_DIR",
)


def run(case: Case, root: Path) -> str | None:
    """Run one case and return what it got wrong, or None."""
    for key in KEYS:
        os.environ.pop(key, None)
    std, tree = Repo(root / "standard"), Repo(root / "tree")
    s, base, head = case.build(std, tree)
    std.git("update-ref", "refs/remotes/origin/main", std.last)
    main = os.environ.get("PORT_CHECK_TREE_MAIN", base)
    known = subprocess.run(
        ["git", "-C", tree.path, "cat-file", "-e", f"{main}^{{commit}}"],
        capture_output=True,
        check=False,
        env=fixture_env(),
    )
    if known.returncode == 0:
        tree.git("update-ref", "refs/remotes/origin/main", main)
    env = dict(os.environ)
    if "PORT_CHECK_FAIL" in env:
        real = subprocess.run(["which", "git"], capture_output=True, check=True)
        shim = root / "bin"
        shim.mkdir()
        (shim / "git").write_text(
            STAND_IN.replace("{git}", real.stdout.decode().strip())
        )
        (shim / "git").chmod(0o755)
        env["PATH"] = f"{shim}{os.pathsep}{env['PATH']}"
    if "PORT_CHECK_GIT_DIR" in env:
        env["GIT_DIR"] = env["PORT_CHECK_GIT_DIR"]
    if "PORT_CHECK_NO_GIT" in env:
        (root / "empty").mkdir()
        env["PATH"] = str(root / "empty")
    done = subprocess.run(
        [sys.executable, str(SCRIPT), std.path, s, tree.path, base, head],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    out = done.stdout
    wrong = []
    if done.returncode != case.code:
        wrong.append(f"exit {done.returncode}, not {case.code}")
    wrong += [f"no {line!r}" for line in case.lines if line not in out]
    wrong += [f"{line!r} printed" for line in case.absent if line in out]
    expect = os.environ.get("PORT_CHECK_EXPECT")
    if expect and f"last port: {expect}" not in out:
        wrong.append(f"last port is not {expect}")
    return "; ".join(wrong) + f"\n{out}{done.stderr}" if wrong else None


def main() -> None:
    if sys.argv[1:] == ["--list"]:
        print("\n".join(case.label for case in CASES))
        return
    wrong = []
    for case in CASES:
        with tempfile.TemporaryDirectory() as root:
            why = run(case, Path(root))
        if why:
            wrong.append(f"{case.label}: {why}")
    if wrong:
        print("\n".join(wrong))
    sys.exit(1 if wrong else 0)


if __name__ == "__main__":
    main()
