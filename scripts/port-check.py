#!/usr/bin/env python3
"""Check a tree's batch of ports against a commit of the standard.

    python3 scripts/port-check.py <standard> <S> <tree> <base> <head>

`<standard>` is a checkout of btclib-org/.github and `<S>` the commit of
it the batch ports to. `<tree>` is the receiving tree's checkout,
`<base>` the batch's parent on its `main` and `<head>` the batch's head.
`skills/btclib-iss/SKILL.md`'s *Ports of the standard* is the rule.
Before anything else it refuses an `<S>` that is not an ancestor of the
standard's `origin/main`, and a `<base>` that is not an ancestor of both
`<head>` and the tree's `origin/main`.

It prints these lines, in this order:

- `last port: <sha> (recorded: <subject>)`, where the newest
  `Port btclib-org/.github@<sha>` subject in `<base>`'s history records
  the last port;
- otherwise a guess: for each file below that `<base>` carries, the
  oldest commit of the newest run of the standard's commits whose copy,
  above the heading, and mode equal the tree's, and the newest of those,
  since the tree holds that copy. It prints
  `no commit of the standard matches <path>` for each file that matches
  none, then `last port: <sha> (guessed: no batch has landed)`, or
  `last port: unknown (...)` where no file matches;
- `<short sha> <subject>` for each commit of the standard after the last
  port, up to `<S>`, where the last port is known;
- `equal <path>` or `DIFFERS <path>: <reason>` for each file it
  compares;
- `FAILED: <reason>` where it cannot tell, as its last line.

A wrong number of arguments prints the usage on standard error.

Every git call runs with no `GIT_` variable of the caller's, no global
or system configuration and no replace objects, and with explicit
options where a repository's own configuration would change the answer:
`--ignore-submodules=none`, `--no-renames`, `--no-relative`,
`--no-ext-diff` and `--no-textconv` on each diff, `--no-show-signature`
on each log, and blobs read with `cat-file`.

The files it compares are those section 14 of the standard's `README.md`
at `<S>` compares and owes the tree at `<head>`, missing copies
included, and every file the batch changes. A condition `owed where`
names is a git pathspec, matched against the files `<head>` tracks. A
file the batch changes that section 14 does not compare is not a copy,
and differs. A file is equal where its entry at `<head>` has the mode
and the bytes of the standard's at `<S>`, the part from `## This
repository in particular` on being `<base>`'s own, unchanged. A file
missing on either side, a heading on one side only, or a mode other than
the standard's, a symbolic link among them, is not equal. Two empty
copies are. The heading counts only as section 14's test reads it, a
line of its own after a newline, ending in LF; a copy holding it
otherwise, at its first byte or ending in CRLF, has a boundary this
cannot place.

Section 14's list is read as its own test reads it, by `bulleted` in
btclib-org/.github's `tests/__init__.py`. `bulleted` below is a port of
it, and says which lines it joins to a bullet, which it passes over as a
paragraph's, and which it refuses. A line it refuses is a section 14 it
cannot read.

It exits 0 only where every file is equal, 1 where one differs, and 2
where it cannot tell: a git call that fails, a section 14 it cannot
read, a path that is not UTF-8, a boundary it cannot place, a refused
`<S>` or `<base>`, a recorded last port that is not an ancestor of
`<S>`, a last port it cannot find, or a batch that changes no file. A
git call that fails, git missing from `PATH` among them, is never read
as an absent or empty file.
"""

from __future__ import annotations

import itertools
import os
import re
import subprocess
import sys

USAGE = "python3 scripts/port-check.py <standard> <S> <tree> <base> <head>"
MARKER = b"\n## This repository in particular\n"
HEADING = re.compile(rb"(?m)^## This repository in particular\r?$")
RECORD = re.compile(r"^Port btclib-org/\.github@([0-9a-f]{7,40})(?:[ (].*)?$")
OPENING = "**The same file in every repository**"
CLOSING = "**Decided per repository**"
SUBJECT = re.compile(r"^- `([^`]+)` — (.+)")
EVERYWHERE = re.compile(r"^owed by every repository(?=[,;:.]|$)")
CONDITIONAL = re.compile(r"^owed where `([^`]+)`(?=[,;:.]|$)")
SOURCE = re.compile(r"the source is this repository's `([^`]+)`")
SECTION = re.compile(r"from `(#{1,6} [^`]+)`")

ITEM = re.compile(r"^[ \t]*(?:[-*+]|[0-9]{1,9}[.)])(?:[ \t]|$)")
"""A line that may open a list item, whatever its marker and its indent.

CommonMark's markers. A thematic break such as `* * *`, a wrapped line
opening `14. ` and a marker inside a fenced block match too, though
Markdown reads none of them as an item: `bulleted` then refuses a line
it could have passed over, which is the safe side to be wrong on.
"""

QUOTE = re.compile(r"^[ \t]*>")
"""A line that opens a block quote, which may hold a list of its own."""

SPACE = " \t"
"""Markdown's whitespace, the only characters an indent or a blank line holds.

`str.strip` with no argument also removes a no-break space, which
Markdown reads as a character, so a line holding one is not blank.
"""

OPENER = re.compile(
    r"[ \t]|#{1,6}(?:[ \t]|$)|\||:?-+:?[ \t]*\||<|`{3}|~{3}"
    r"|(?:[-*_][ \t]*){3,}$|(?:=+|-+)[ \t]*$"
)
"""A line that opens a block which is no paragraph's.

An indent, a heading, a table's row or its delimiter row, HTML, a fence
of backticks or tildes, a thematic break and a setext underline. With
`DEFINITION`, `QUOTE` and `ITEM` these are the blocks CommonMark and
GitHub's tables and footnotes start. `bulleted` matches a line outside
a bullet as it stands, so an indent there is refused, and a line inside
one after its indent, and reads any other line that is not blank as a
paragraph's. A paragraph opening with an autolink's `<` or a `|` is
refused with the block it looks like, the safe side to be wrong on.
"""

DEFINITION = re.compile(r"\[(?:[^\\\[\]]|\\.)+\]:", re.DOTALL)
"""The definition of a link reference or a footnote, from its first line.

It is matched, the indent removed, against the lines from there to the
next blank one, since CommonMark lets a label wrap. A label is what lies
between `[` and `]:`, and holds no bracket that a backslash does not
escape. A definition that wraps its destination or its title onto later
lines is refused at its first line all the same. A label CommonMark
rejects for its length, or for holding only whitespace, is refused too,
the safe side.
"""


class Unknown(Exception):
    """Something the check cannot establish, which is never a pass."""


ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
ENV.update(
    GIT_CONFIG_GLOBAL=os.devnull,
    GIT_CONFIG_NOSYSTEM="1",
    GIT_NO_REPLACE_OBJECTS="1",
    GIT_TERMINAL_PROMPT="0",
)
DIFF = (
    "--ignore-submodules=none",
    "--no-renames",
    "--no-relative",
    "--no-ext-diff",
    "--no-textconv",
)


def launch(repo: str, args: tuple[str, ...]) -> subprocess.CompletedProcess[bytes]:
    """Run one git command in `repo`, with the environment above.

    :raises Unknown: where git cannot be started.
    """
    try:
        return subprocess.run(
            ["git", "-C", repo, *args], capture_output=True, env=ENV, check=False
        )
    except OSError as error:
        msg = f"git -C {repo} {' '.join(args)} could not start: {error}"
        raise Unknown(msg) from error


def refused(
    repo: str, args: tuple[str, ...], done: subprocess.CompletedProcess[bytes]
) -> Unknown:
    err = done.stderr.decode(errors="replace").strip()
    return Unknown(f"git -C {repo} {' '.join(args)} exited {done.returncode}: {err}")


def git(repo: str, *args: str) -> bytes:
    """Run one git command in `repo` and return what it printed.

    :raises Unknown: where it cannot start or exits other than 0.
    """
    done = launch(repo, args)
    if done.returncode != 0:
        raise refused(repo, args, done)
    return done.stdout


def ancestor(repo: str, older: str, newer: str) -> bool:
    """Say whether `older` is an ancestor of `newer`, or the same commit.

    :raises Unknown: where git answers neither yes nor no.
    """
    args = ("merge-base", "--is-ancestor", older, newer)
    done = launch(repo, args)
    if done.returncode in (0, 1):
        return done.returncode == 0
    raise refused(repo, args, done)


def boundary(body: bytes, where: str) -> int:
    """Return where a copy's own part starts, or -1 where it has none.

    :raises Unknown: where the heading is there but not as section 14's
        test reads it.
    """
    loose = HEADING.search(body)
    exact = body.find(MARKER)
    if loose is None and exact < 0:
        return -1
    if loose is None or exact < 0 or exact + 1 != loose.start():
        msg = f"the heading of {where} is not on a line of its own ending in LF"
        raise Unknown(msg)
    return exact


def entry(repo: str, rev: str, path: str) -> tuple[str, bytes] | None:
    """Read a path's mode and bytes at a revision, or None where it is absent.

    Absence is what `ls-tree` answers with nothing; a read that fails
    raises, so that it never reads as an absent or empty file.
    """
    listed = git(repo, "ls-tree", "-z", "--full-tree", rev, "--", path)
    for item in listed.split(b"\0"):
        if not item:
            continue
        meta, _, name = item.partition(b"\t")
        fields = meta.decode().split(" ")
        if len(fields) != 3:
            msg = f"ls-tree printed {item!r} for {path}"
            raise Unknown(msg)
        mode, kind, sha = fields
        if name.decode() == path:
            if kind != "blob":
                return (mode, b"")
            return (mode, git(repo, "cat-file", "blob", sha))
    return None


def unplaced(line: str, *, inside: bool, lazy: bool, block: bool) -> str:
    """Say why `bulleted` refuses a line it does not join to a bullet.

    :param line: the line, which is not blank and opens no bullet.
    :param inside: whether it is indented under a bullet.
    :param lazy: whether it follows a bullet's line with no blank line
        between them.
    :param block: whether it opens a block `OPENER` or `DEFINITION`
        names, after its indent.
    :returns: what the refusal says of it, empty where it is a
        paragraph's.
    """
    if QUOTE.match(line):
        return "opens a block quote"
    if ITEM.match(line):
        return "opens an item, not a bullet"
    if inside:
        return "opens a block inside a bullet"
    if lazy:
        return "continues a bullet unindented"
    return "is no bullet and no paragraph" if OPENER.match(line) or block else ""


def bulleted(lines: list[str], start: int, end: int) -> list[str]:
    """Read section 14's list between two lines, one string per bullet.

    A bullet is a line starting `- ` and every line indented by two
    spaces or a tab after it, joined by a space. A paragraph's line opens
    none of the blocks `OPENER`, `DEFINITION`, `QUOTE` and `ITEM` name,
    and one after a blank line ends a bullet.

    Every other line that is not blank is refused rather than passed
    over, since a copy whose item is dropped is a copy nothing compares.
    Among them are a list item other than a bullet, as `* `, `+ `, `1. `,
    ` - `, an item nested under a bullet and an indented marker after a
    paragraph; a block quote, which may hold a list; a line under a
    bullet that opens any other block after its indent, as a footnote,
    which may hold a list too; and a line of prose not indented right
    after a bullet, which Markdown reads as part of that bullet.

    :param lines: README.md's lines, split where Markdown splits them.
    :param start: the index of the line the list follows.
    :param end: the index of the line the list stops at.
    :returns: the bullets, in the order the list gives them.
    :raises Unknown: where a line between the two is one this refuses.
    """
    bullets: list[str] = []
    within = blank = False
    for number, line in enumerate(lines[start + 1 : end], start + 2):
        if not line.strip(SPACE):
            blank = True
            continue
        inside = within and line.startswith(("  ", "\t"))
        inner = ITEM.match(line) or QUOTE.match(line)
        paragraph = itertools.takewhile(
            lambda text: text.strip(SPACE), lines[number - 1 : end]
        )
        block = bool(
            OPENER.match(line.lstrip(SPACE))
            or DEFINITION.match("\n".join(paragraph).lstrip(SPACE))
        )
        if line.startswith("- "):
            bullets.append(line)
            within = True
        elif inside and not (inner or block):
            bullets[-1] += f" {line.strip(SPACE)}"
        elif refusal := unplaced(
            line, inside=inside, lazy=within and not blank, block=block
        ):
            msg = f"README.md:{number} {refusal}: {line!r}"
            raise Unknown(msg)
        else:
            within = False
        blank = False
    return bullets


def obligations(std: str, at: str, tree: str, head: str) -> dict[str, str]:
    """Read section 14's compared paths the tree owes, each against its source.

    README.md's lines end where Markdown's do, as section 14's test splits
    them: at a line feed, at a carriage return before one, and at a
    carriage return alone. `splitlines` would also end one at U+2028 and
    the other separators Markdown keeps inside a line.

    :raises Unknown: where the list is not found once, `bulleted` refuses
        a line of it, a bullet has no subject, or a clause is one this
        does not read.
    """
    text = git(std, "cat-file", "blob", f"{at}:README.md").decode()
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    starts = [i for i, line in enumerate(lines) if OPENING in line]
    ends = [i for i, line in enumerate(lines) if CLOSING in line]
    if len(starts) != 1 or len(ends) != 1 or ends[0] < starts[0]:
        msg = "section 14's list is not found once in README.md"
        raise Unknown(msg)
    bullets = bulleted(lines, starts[0], ends[0])
    empty = git(tree, "hash-object", "-t", "tree", "/dev/null").decode().strip()
    owed: dict[str, str] = {}
    for bullet in bullets:
        found = SUBJECT.match(bullet)
        if found is None:
            msg = f"a bullet of section 14 names no path: {bullet!r}"
            raise Unknown(msg)
        path, clause = found.group(1), found.group(2)
        if SECTION.search(clause):
            msg = f"section 14 compares one section of {path}, which this does not"
            raise Unknown(msg)
        where = CONDITIONAL.match(clause)
        if where is None and EVERYWHERE.match(clause) is None:
            msg = f"section 14's clause for {path} is not one this reads"
            raise Unknown(msg)
        if where is None or git(
            tree, "diff", *DIFF, "--name-only", "-z", empty, head, "--", where.group(1)
        ):
            source = SOURCE.search(clause)
            owed[path] = source.group(1) if source else path
    if not owed:
        msg = "section 14 owes the tree nothing"
        raise Unknown(msg)
    return owed


def last_port(
    std: str, at: str, tree: str, base: str, owed: dict[str, str]
) -> str | None:
    """Find the tree's last port, and print how it was found.

    :returns: the commit of the standard the changes are listed from, or
        None where no record exists and no copy matches.
    """
    log = git(tree, "log", "--no-show-signature", "-z", "--format=%s", base).decode()
    for subject in log.split("\0"):
        found = RECORD.match(subject.strip("\n"))
        if found:
            raw = git(std, "rev-parse", "--verify", f"{found.group(1)}^{{commit}}")
            sha = raw.decode().strip()
            if not ancestor(std, sha, at):
                msg = f"the recorded last port {sha} is not an ancestor of <S> {at}"
                raise Unknown(msg)
            print(f"last port: {sha} (recorded: {subject.strip()})")
            return sha
    guesses: list[str] = []
    for path, source in owed.items():
        mine = entry(tree, base, path)
        if mine is None:
            continue
        run: str | None = None
        revs = git(std, "rev-list", at, "--", source).decode().split()
        for commit in revs:
            theirs = entry(std, commit, source)
            if (
                theirs is not None
                and theirs[0] == mine[0]
                and shared(theirs[1], f"{source} at {commit}")
                == shared(mine[1], f"{path} at <base>")
            ):
                run = commit
            elif run is not None:
                break
        if run is None:
            print(f"no commit of the standard matches {path}")
        else:
            guesses.append(run)
    if not guesses:
        print("last port: unknown (no record, and no copy matches the standard)")
        return None
    order = git(std, "rev-list", at).decode().split()
    newest = min(guesses, key=order.index)
    print(f"last port: {newest} (guessed: no batch has landed)")
    return newest


def shared(body: bytes, where: str) -> bytes:
    """Return the part of a copy above the marker, as section 14 compares it."""
    cut = boundary(body, where)
    return (body if cut < 0 else body[:cut]).rstrip(b"\n") + b"\n"


def compare(
    std: str, at: str, tree: str, base: str, head: str, path: str, source: str | None
) -> str | None:
    """Say why a file of the batch is not the standard's, or None where it is.

    `source` is None for a path section 14 does not compare.
    """
    if source is None:
        return "not a copy section 14 compares"
    theirs = entry(std, at, source)
    mine = entry(tree, head, path)
    if theirs is None or mine is None:
        return "missing in " + ("the standard" if theirs is None else "the tree")
    if theirs[0] != mine[0] or not theirs[0].startswith("100"):
        return f"mode {mine[0]} where the standard has {theirs[0]}"
    old = entry(tree, base, path)
    std_cut = boundary(theirs[1], f"{source} at <S>")
    base_cut = -1 if old is None else boundary(old[1], f"{path} at <base>")
    boundary(mine[1], f"{path} at <head>")
    if (std_cut < 0) != (base_cut < 0):
        return "the heading is on one side only"
    want = theirs[1]
    if std_cut >= 0 and old is not None:
        want = theirs[1][:std_cut] + old[1][base_cut:]
    return None if want == mine[1] else "bytes differ"


def main(argv: list[str]) -> int:
    if len(argv) != 5:
        print(f"usage: {USAGE}", file=sys.stderr)
        return 2
    std, at, tree, base, head = argv
    try:
        at = git(std, "rev-parse", "--verify", f"{at}^{{commit}}").decode().strip()
        if not ancestor(std, at, "origin/main"):
            msg = f"<S> {at} is not an ancestor of the standard's origin/main"
            raise Unknown(msg)
        if not ancestor(tree, base, head) or not ancestor(tree, base, "origin/main"):
            msg = f"<base> {base} is not an ancestor of <head> and origin/main"
            raise Unknown(msg)
        owed = obligations(std, at, tree, head)
        since = last_port(std, at, tree, base, owed)
        if since is not None:
            log = git(
                std, "log", "--no-show-signature", "--format=%h %s", f"{since}..{at}"
            )
            sys.stdout.write(log.decode())
        changed = git(tree, "diff", *DIFF, "-z", "--name-only", base, head)
        names = [p.decode() for p in changed.split(b"\0") if p]
        if not names:
            msg = "the batch changes no file"
            raise Unknown(msg)
        paths: dict[str, str | None] = dict(owed)
        paths.update({p: owed.get(p) for p in names})
        rc = 0
        for path, source in paths.items():
            why = compare(std, at, tree, base, head, path, source)
            print(f"equal {path}" if why is None else f"DIFFERS {path}: {why}")
            rc = rc if why is None else 1
        if since is None:
            msg = "the last port is unknown, so no change since it is listed"
            raise Unknown(msg)
    except (Unknown, UnicodeDecodeError) as error:
        print(f"FAILED: {error}")
        return 2
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
