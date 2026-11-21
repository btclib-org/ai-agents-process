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

Its own lines name no URL, which can carry a credential. git's messages
it passes on leave out a URL's userinfo, since it drops the caller's
`GIT_TRACE*` and `GIT_CURL_VERBOSE`, whose output on standard error
would carry it, as `GIT_TRACE`'s line for `git remote-https` does.

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

import os
import re
import subprocess
import sys
from typing import TextIO

USAGE = "usage: python3 -I scripts/unpushed-branches.py <checkout>..."
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


def run(args: list[str], data: str = "", shown: list[str] | None = None) -> str:
    """Run a command and return what it printed, naming it as `shown` says.

    :raises Failed: where it cannot start or exits other than 0.
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
        err = done.stderr.strip().replace("\n", "; ")
        name = " ".join((shown or args)[:4])
        raise Failed(f"{name} exited {done.returncode}: {err}")
    return done.stdout


def git(checkout: str, *args: str, data: str = "") -> str:
    hookless = ["git", "-c", "core.hooksPath=/dev/null"]
    return run([*hookless, "-C", checkout, *args], data, ["git", "-C", checkout, *args])


def held(checkout: str, remote: dict[str, str]) -> set[str]:
    """The commits and tags among origin's refs that the repository holds."""
    shas = sorted(set(remote.values()))
    if not shas:
        return set()
    out = git(
        checkout,
        "cat-file",
        "--batch-check=%(objectname) %(objecttype)",
        data="".join(f"{s}\n" for s in shas),
    )
    return {
        line.split()[0]
        for line in out.splitlines()
        if line.split()[1:] in (["commit"], ["tag"])
    }


def unreached(checkout: str, heads: dict[str, str], ends: set[str]) -> set[str]:
    """The branches of `heads` whose commit none of `ends` reaches."""
    if not heads:
        return set()
    data = "".join(f"{s}\n" for s in sorted(set(heads.values())))
    data += "".join(f"^{s}\n" for s in sorted(ends))
    left = set(git(checkout, "rev-list", "--stdin", data=data).split())
    return {b for b, s in heads.items() if s in left}


def fetch(checkout: str, refs: list[str]) -> None:
    git(checkout, *FETCH, data="".join(f"{r}\n" for r in refs))


def numbers(repo: str, branch: str) -> list[str]:
    """The pull requests of `repo`, open or not, whose head is `branch`."""
    out = run(
        ["gh", "pr", "list", f"--repo={repo}", f"--head={branch}", "--state=all"]
        + ["--limit=200", "--json=number", "--jq=.[].number"]
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
    remote: dict[str, str] = {}
    for line in git(checkout, "ls-remote", "origin").splitlines():
        sha, _, ref = line.partition("\t")
        if REACHES.fullmatch(ref.removesuffix("^{}")):
            remote[ref] = sha
    heads: dict[str, str] = {}
    form = "--format=%(objectname) %(objecttype) %(refname)"
    for line in git(checkout, "for-each-ref", form, "refs/heads/").splitlines():
        sha, kind, ref = line.split(" ", 2)
        if kind != "commit":
            raise Failed(f"{ref} names a {kind}, not a commit")
        heads[ref] = sha
    whole = True
    have = held(checkout, remote)
    left = unreached(checkout, heads, have)
    missing = [
        r
        for r, s in sorted(remote.items())
        if s not in have and not r.startswith("refs/pull/") and not r.endswith("^{}")
    ]
    if left and missing:
        try:
            fetch(checkout, missing)
        except Failed as error:
            say(sys.stderr, f"no fetch: {checkout}: {error}")
            whole = False
        have = held(checkout, remote)
        left = unreached(checkout, heads, have)
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
                    found = numbers(repo.group(1), ref.removeprefix("refs/heads/"))
                except Failed as error:
                    say(sys.stderr, f"no pull request lookup: {checkout}: {error}")
                    whole = False
                    break
                wanted |= {n for n in found if n in pulls and pulls[n] not in have}
            if wanted:
                try:
                    fetch(checkout, [f"refs/pull/{n}/head" for n in sorted(wanted)])
                except Failed as error:
                    say(sys.stderr, f"no fetch: {checkout}: {error}")
                    whole = False
                have = held(checkout, remote)
                left = unreached(checkout, heads, have)
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
