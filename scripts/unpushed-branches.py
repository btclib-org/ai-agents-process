#!/usr/bin/env python3
"""List the local branches of each checkout that no ref of origin reaches.

    python3 -I scripts/unpushed-branches.py <checkout>...

`process/every-role.md`'s *Debris goes when its work ends* says which
local branch may go: one whose head a branch, a tag or a pull request's
`refs/pull/<n>/head` of origin reaches, as `git ls-remote origin` prints
them, the repository holding that ref's commit. This lists every other
local branch: work, which goes only on the human's word. It reads origin
alone, so a branch pushed only to another remote is listed. It deletes
nothing, and writes no ref, no configuration, no `FETCH_HEAD` and no
commit-graph. A remote-tracking ref proves nothing, since it outlives
the branch on origin, and neither does a `refs/pull/<n>/merge`, a merge
GitHub makes.

Before it lists a branch, it fetches what it needs to tell, objects
alone:

- the branches and tags of origin whose commit the repository lacks, as
  where origin moved on to a commit pushed from elsewhere;
- then, for each branch still unreached, the head of each pull request
  that `gh pr list --head <branch> --state all --limit 200` names in
  origin's repository on GitHub, where the repository lacks it: a
  checkout does not fetch `refs/pull/*` by default. Of a head branch
  name more than 200 pull requests share, the older ones are not read.
  A pull request whose head branch has another name is not looked up, so
  a branch whose only reaching ref is that pull request's head is listed
  where the repository lacks the head. Origin's URL names a repository
  on GitHub where its host is `github.com` or `www.github.com`, in any
  letter case: an https or ssh URL, with a user and a port or without,
  or an scp-like address, with a user or without.

No git call fetches a missing object on demand (`GIT_NO_LAZY_FETCH`),
which a partial clone would do one object at a time, or reads a replace
ref or a graft (`GIT_NO_REPLACE_OBJECTS`, and `GIT_GRAFT_FILE` naming an
empty file), which could make origin's history reach a commit it does
not hold. No git call runs a hook of the checkout
(`core.hooksPath=/dev/null`).

Its own lines name no URL, which can carry a credential. In what it
passes on of the standard error of git, ssh and `gh`, from
`git ls-remote origin` on, it replaces each piece of the userinfo of
origin's URLs by `****`. The URLs are those
`git remote get-url --all origin` prints, with `url.<base>.insteadOf`
applied. Their userinfo is what precedes the last `@` after
`<scheme>://`, or the last `@` before the first `:` of an address
without `://`, as an scp-like one, and its pieces lie between its `:`
and `@`. A piece is replaced wherever it stands, inside other words
too: a short user, as `git`, is replaced in `git-upload-pack`. Each
character of a piece may stand as itself or percent-encoded, with hex
digits in either case, so git's decoded spelling is replaced as the raw
one is. Where git or ssh prints part of a piece on its own, cut at
another character, that part is not replaced: a token holding a raw `/`
ends the host git reads there, and git names that host.

It drops the caller's `GIT_TRACE*` and `GIT_CURL_VERBOSE`: under
`GIT_TRACE_REDACT=0`, curl's trace carries the credential in base64, in
its `Authorization` header, where no piece stands as itself.

It prints `<checkout>: <branch> <sha>` for each branch it lists. Where a
fetch or a lookup fails, it lists the branches it could not clear and
says why on standard error. It refuses a checkout that git cannot read,
one with a branch whose head is no commit, one with no remote named
origin, and one whose origin cannot be read, prints why, and goes on to
the next.

It exits 0 where it read every checkout whole; 1 where it refused one,
where a fetch or a lookup failed, or where a lookup it needed could not
be made, origin naming no repository on GitHub; and 2, after the usage,
where it is given no checkout or an argument starting with `-`.
"""

from __future__ import annotations

import itertools
import os
import re
import subprocess
import sys
import urllib.parse
from collections.abc import Sequence
from typing import TextIO

USAGE = "usage: python3 -I scripts/unpushed-branches.py <checkout>..."
HIDDEN = "****"
REACHES = re.compile(r"refs/(?:heads/.+|tags/.+|pull/[0-9]+/head)")
PULL = re.compile(r"refs/pull/([0-9]+)/head")
GITHUB = re.compile(
    r"(?:(?:https|ssh)://(?:[^@/]+@)?(?:www\.)?github\.com(?::[0-9]+)?/"
    r"|(?:[^@/:]+@)?(?:www\.)?github\.com:)"
    r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/?",
    re.IGNORECASE,
)
# the caller's variables that would point every git call at one
# repository, and those whose trace would print a URL whole
ENV = {
    k: v
    for k, v in os.environ.items()
    if not k.startswith("GIT_TRACE")
    and k
    not in (
        "GIT_CURL_VERBOSE",
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_NAMESPACE",
    )
}
ENV.update(
    GIT_TERMINAL_PROMPT="0",
    GIT_NO_LAZY_FETCH="1",
    GIT_NO_REPLACE_OBJECTS="1",
    GIT_GRAFT_FILE=os.devnull,
)
# objects alone: an empty --refmap updates no remote-tracking ref
FETCH = (
    "fetch",
    "--quiet",
    "--no-tags",
    "--no-write-fetch-head",
    "--refmap=",
    "--no-auto-maintenance",
    "--no-write-commit-graph",
    "--no-recurse-submodules",
    "--stdin",
    "origin",
)


class Failed(Exception):
    """A command that did not answer."""


def say(stream: TextIO, text: str) -> None:
    """Write a line as git spelled it, bytes that are not UTF-8 included."""
    stream.flush()
    stream.buffer.write(text.encode("utf-8", "surrogateescape") + b"\n")
    stream.flush()


def lines(out: str) -> list[str]:
    """The records of `out`, split at LF alone: a branch name can hold U+2028."""
    return [line for line in out.split("\n") if line]


def spelled(piece: str) -> re.Pattern[str]:
    """Group 1 at each place `piece` stands, a character as itself or encoded."""
    raw = piece.encode("utf-8", "surrogateescape")
    text = urllib.parse.unquote_to_bytes(raw).decode("utf-8", "surrogateescape")
    chars = []
    for c in text:
        coded = "".join(
            f"%[{b >> 4:X}{b >> 4:x}][{b & 15:X}{b & 15:x}]"
            for b in c.encode("utf-8", "surrogateescape")
        )
        chars.append(f"(?:{coded}|{re.escape(c)})")
    return re.compile(f"(?=({''.join(chars)}))")


def pieces(urls: str) -> list[re.Pattern[str]]:
    """A pattern for each piece of the userinfo of `urls`, one URL a line."""
    found: set[str] = set()
    for url in lines(urls):
        _, sep, rest = url.partition("://")
        address = rest if sep else url.partition(":")[0]
        found.update(p for p in re.split("[:@]", address.rpartition("@")[0]) if p)
    return [spelled(p) for p in sorted(found)]


def hidden(text: str, hide: Sequence[re.Pattern[str]]) -> str:
    """`text` with each run of characters a pattern of `hide` covers as HIDDEN."""
    covered = [False] * len(text)
    for pattern in hide:
        for m in pattern.finditer(text):
            covered[m.start(1) : m.end(1)] = [True] * (m.end(1) - m.start(1))
    return "".join(
        HIDDEN if gone else "".join(c for _, c in group)
        for gone, group in itertools.groupby(zip(covered, text), lambda x: x[0])
    )


def run(
    args: list[str],
    data: str = "",
    shown: list[str] | None = None,
    hide: Sequence[re.Pattern[str]] = (),
) -> str:
    """Run a command and return what it printed, naming it as `shown` says.

    :raises Failed: where it cannot start or exits other than 0, its
        standard error with what `hide` covers replaced.
    """
    try:
        done = subprocess.run(
            args,
            input=data,
            capture_output=True,
            encoding="utf-8",
            errors="surrogateescape",
            env=ENV,
            check=False,
        )
    except OSError as error:
        raise Failed(f"{args[0]} could not start: {error}") from error
    if done.returncode != 0:
        err = hidden(done.stderr, hide).strip().replace("\n", "; ")
        name = " ".join((shown or args)[:4])
        raise Failed(f"{name} exited {done.returncode}: {err}")
    return done.stdout


def git(
    checkout: str, *args: str, data: str = "", hide: Sequence[re.Pattern[str]] = ()
) -> str:
    hookless = ["git", "-c", "core.hooksPath=/dev/null"]
    shown = ["git", "-C", checkout, *args]
    return run([*hookless, "-C", checkout, *args], data, shown, hide)


def held(
    checkout: str, remote: dict[str, str], hide: Sequence[re.Pattern[str]]
) -> set[str]:
    """The commits and tags among origin's refs that the repository holds."""
    shas = sorted(set(remote.values()))
    if not shas:
        return set()
    out = git(
        checkout,
        "cat-file",
        "--batch-check=%(objectname) %(objecttype)",
        data="".join(f"{s}\n" for s in shas),
        hide=hide,
    )
    return {
        line.split()[0]
        for line in lines(out)
        if line.split()[1:] in (["commit"], ["tag"])
    }


def unreached(
    checkout: str,
    heads: dict[str, str],
    ends: set[str],
    hide: Sequence[re.Pattern[str]],
) -> set[str]:
    """The branches of `heads` whose commit none of `ends` reaches."""
    if not heads:
        return set()
    data = "".join(f"{s}\n" for s in sorted(set(heads.values())))
    data += "".join(f"^{s}\n" for s in sorted(ends))
    left = set(git(checkout, "rev-list", "--stdin", data=data, hide=hide).split())
    return {b for b, s in heads.items() if s in left}


def fetch(checkout: str, refs: list[str], hide: Sequence[re.Pattern[str]]) -> None:
    git(checkout, *FETCH, data="".join(f"{r}\n" for r in refs), hide=hide)


def numbers(repo: str, branch: str, hide: Sequence[re.Pattern[str]]) -> list[str]:
    """The pull requests of `repo`, open or not, whose head is `branch`."""
    out = run(
        ["gh", "pr", "list", f"--repo={repo}", f"--head={branch}", "--state=all"]
        + ["--limit=200", "--json=number", "--jq=.[].number"],
        hide=hide,
    )
    found = out.split()
    if not all(n.isdigit() for n in found):
        raise Failed(f"gh pr list printed {out!r}")
    return found


def check(checkout: str) -> bool:
    """Print the unreached branches of `checkout`; say whether it read it whole.

    :raises Failed: where it cannot read the checkout.
    """
    git(checkout, "rev-parse", "--git-dir")
    try:
        url = git(checkout, "config", "--get", "remote.origin.url").strip()
    except Failed:
        raise Failed("no remote named origin") from None
    hide = pieces(git(checkout, "remote", "get-url", "--all", "origin"))
    remote: dict[str, str] = {}
    for line in lines(git(checkout, "ls-remote", "origin", hide=hide)):
        sha, _, ref = line.partition("\t")
        if REACHES.fullmatch(ref.removesuffix("^{}")):
            remote[ref] = sha
    heads: dict[str, str] = {}
    form = "--format=%(objectname) %(objecttype) %(refname)"
    for line in lines(git(checkout, "for-each-ref", form, "refs/heads/", hide=hide)):
        sha, kind, ref = line.split(" ", 2)
        if kind != "commit":
            raise Failed(f"{ref} names a {kind}, not a commit")
        heads[ref] = sha
    whole = True
    have = held(checkout, remote, hide)
    left = unreached(checkout, heads, have, hide)
    missing = [
        r
        for r, s in sorted(remote.items())
        if s not in have and not r.startswith("refs/pull/") and not r.endswith("^{}")
    ]
    if left and missing:
        try:
            fetch(checkout, missing, hide)
        except Failed as error:
            say(sys.stderr, f"no fetch: {checkout}: {error}")
            whole = False
        have = held(checkout, remote, hide)
        left = unreached(checkout, heads, have, hide)
    pulls = {m.group(1): s for r, s in remote.items() if (m := PULL.fullmatch(r))}
    if left and pulls:
        repo = GITHUB.fullmatch(url)
        if repo is None:
            why = "origin names no repository on GitHub"
            say(sys.stderr, f"no pull request lookup: {checkout}: {why}")
            whole = False
        else:
            wanted: set[str] = set()
            for ref in sorted(left):
                try:
                    branch = ref.removeprefix("refs/heads/")
                    found = numbers(repo.group(1), branch, hide)
                except Failed as error:
                    say(sys.stderr, f"no pull request lookup: {checkout}: {error}")
                    whole = False
                    break
                wanted |= {n for n in found if n in pulls and pulls[n] not in have}
            if wanted:
                try:
                    refs = [f"refs/pull/{n}/head" for n in sorted(wanted)]
                    fetch(checkout, refs, hide)
                except Failed as error:
                    say(sys.stderr, f"no fetch: {checkout}: {error}")
                    whole = False
                have = held(checkout, remote, hide)
                left = unreached(checkout, heads, have, hide)
    for ref in sorted(left):
        say(sys.stdout, f"{checkout}: {ref.removeprefix('refs/heads/')} {heads[ref]}")
    return whole


def main(argv: list[str]) -> int:
    if not argv or any(a.startswith("-") for a in argv):
        say(sys.stderr, USAGE)
        return 2
    rc = 0
    for checkout in argv:
        try:
            if not check(checkout):
                rc = 1
        except Failed as error:
            say(sys.stderr, f"refused: {checkout}: {error}")
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
