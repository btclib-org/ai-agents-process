#!/usr/bin/env python3
"""Run unpushed-branches.py on fixture repositories and check what it lists.

    python3 -I scripts/test-unpushed-branches.py

The fixtures sit in a temporary directory the test removes: a bare
repository as origin, which a configuration of the test's own names as
`https://github.com/own/repo.git` and in other forms, and clones of it.
Commits are made with `git commit-tree`, which signs nothing unless
asked, or written as objects, and the stand-in `gpg.program` fails a
fixture that ever asks. The fixtures' git calls and the script's run
with none of the caller's `GIT_` variables and no proxy variable:
`GIT_CONFIG_GLOBAL` names the test's configuration, no system
configuration is read, and `GIT_SSH_COMMAND` is `false`, or a stand-in
that refuses the login with ssh's lines, so that no case reaches a real
ssh. A stand-in for `gh`, first on the `PATH`, logs each call and
answers the pull requests the test gives each repository and branch, as
`gh` does: the open ones alone unless asked for every state, and no more
than its `--limit`, 30 where none is given. Each run's working directory
is an empty one, which must stay empty, and no run prints the credential
a URL of origin carries.

The cases, on one clone unless they say otherwise. Not listed:

- a branch at a branch of origin, one named with U+2028 included, behind
  a branch of origin whose commit the clone lacks, at a tag, or at a
  pull request's head the clone holds;
- a branch behind the head of a merged pull request the clone lacks,
  the 200th that `gh` names for that branch.

Listed: a branch with a commit no ref of origin holds, one only a
remote-tracking ref reaches, one only a `refs/pull/<n>/merge` reaches,
one pushed only to another remote, one behind a pull request's head that
`gh` does not name, whose commit stays unfetched, one named
`topic;>MARKER` and one named with U+2028, by those names, and one a
worktree has checked out. `gh` is asked about the branches still
unreached once origin's branches and tags are fetched, and about no
other. The run writes no ref, no `FETCH_HEAD`, no configuration, no
worktree entry and no file at the top of the git directory or in
`objects/info`, though the clone's configuration asks a fetch for every
tag and for a commit-graph, and asks for automatic maintenance at once;
and the clone's `reference-transaction` hook does not run.

Then:

- with `gh` failing, or printing a word that is no number, the branches
  the first run listed are listed and it exits 1;
- with `GIT_DIR`, `GIT_COMMON_DIR`, `GIT_OBJECT_DIRECTORY` or
  `GIT_ALTERNATE_OBJECT_DIRECTORIES` naming another repository, or
  `GIT_NAMESPACE` set, it lists the same;
- in a clone for each form of origin's URL on GitHub (https with and
  without `.git`, a trailing `/`, a credential or a port, ssh with and
  without a user or a port, scp-like with and without a user, the host
  in capitals or after `www.` in https and scp-like), a branch behind a pull request's head
  that `gh` names is cleared, `gh` being asked about `own/repo`;
- with an origin that has pull requests and a URL not on GitHub, holding
  a credential, it lists and exits 1; with no branch unreached, it exits
  0 and fetches nothing, though origin has a branch the clone lacks;
- where a clone that checks what it fetches is refused a branch's
  commit, or a pull request's head, with no author email, it lists and
  exits 1;
- a branch that a replace ref, or a graft, would make origin's main reach
  is listed;
- in a partial clone, a branch behind a pull request's head that `gh`
  does not name is listed, and the head is not fetched on demand;
- with an origin that has no pull request, `gh` is not run;
- with `GIT_TRACE` set, a checkout that is no repository, one with no
  remote named origin, one whose origin cannot be read, at an https, an
  http or an ssh URL with a credential, and one with a branch at a blob
  or at a tag are refused, and the next checkout is still read;
- where git or ssh prints a credential of origin's URL, as git is shown
  to first, each checkout is refused with git's diagnostic, the
  credential replaced by `****`: a server of the test on 127.0.0.1
  answering 401 to a token alone, percent-encoded, as the URL holds it
  and as `url.<base>.insteadOf` gives it; a URL with two `@`; and the
  stand-in ssh refusing a password. With trace2 on standard error in the
  global configuration, and curl's trace unredacted, neither the token's
  refusal nor that of a URL with a password prints a credential, in
  base64 included;
- no checkout, and an option before a checkout or after one, exit 2 with
  the usage.

The script prints each case that answers wrongly, and exits 1 where
there is one.
"""

from __future__ import annotations

import base64
import http.server
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

SCRIPT = Path(__file__).with_name("unpushed-branches.py")
URL = "https://github.com/own/repo.git"
# the password part of a URL, which no line the script prints may hold
MARK = "MARKINURL"
# the forms of origin's URL that name own/repo on GitHub
FORMS = (
    "https://github.com/own/repo",
    f"https://oauth2:{MARK}@github.com/own/repo.git",
    "ssh://git@github.com/own/repo.git",
    "git@github.com:own/repo.git",
    "https://GitHub.com/own/repo.git",
    "https://www.github.com/own/repo.git",
    "https://github.com:443/own/repo.git",
    "https://github.com/own/repo/",
    "ssh://github.com/own/repo.git",
    "ssh://git@github.com:22/own/repo.git",
    "github.com:own/repo.git",
    "git@www.github.com:own/repo.git",
)
OTHER = f"https://oauth2:{MARK}@example.invalid/own/repo.git"
BAD = "https://github.com/own/bad.git"
# the stand-in for gh: it answers, from $GHANSWERS, the numbers of the
# pull requests of the repository and the branch asked, open ones only
# unless asked for every state, as gh does
GH = """#!/bin/sh
printf '%s\\037' "$@" >> "$GHLOG"
printf '\\n' >> "$GHLOG"
if [ -n "${GH_FAIL:-}" ]; then
  echo 'gh: failing' >&2
  exit 1
fi
if [ -n "${GH_PRINT:-}" ]; then
  printf '%s\\n' "$GH_PRINT"
  exit 0
fi
head= repo= state=open limit=30
for a; do
  case $a in
    --head=*) head=${a#--head=} ;;
    --repo=*) repo=${a#--repo=} ;;
    --state=*) state=${a#--state=} ;;
    --limit=*) limit=${a#--limit=} ;;
  esac
done
H=$head R=$repo S=$state L=$limit awk -F '\\t' '$1 == ENVIRON["R"] &&
  $2 == ENVIRON["H"] && (ENVIRON["S"] == "all" || $4 == ENVIRON["S"]) &&
  n < ENVIRON["L"] + 0 { print $3; n++ }' "$GHANSWERS"
"""
# the stand-in for ssh: it answers -G as OpenSSH does, so that git passes
# it OpenSSH's options, and refuses the login with ssh's lines, the first
# as -v prints it
SSH = """#!/bin/sh
for a; do [ "$a" != -G ] || exit 0; done
while [ $# -gt 0 ]; do
  case $1 in -o|-p) shift 2 ;; -*) shift ;; *) break ;; esac
done
user=${1%@*} host=${1##*@}
echo "debug1: Authenticating to $host:22 as '$user'" >&2
echo "$user@$host: Permission denied (publickey)." >&2
exit 255
"""
failures: list[str] = []


def lines(out: str) -> list[str]:
    """The records of `out`, split at LF alone: a branch name can hold U+2028."""
    return [line for line in out.split("\n") if line]


def fail(text: str) -> None:
    failures.append(text)
    print(f"FAIL: {text}")


class Refuse(http.server.BaseHTTPRequestHandler):
    """Answer 401 to every request, asking for a password."""

    def do_GET(self) -> None:
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="fixture"')
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, *args: object) -> None:
        """Print nothing for a request."""


class Fixture:
    """The temporary directory, its environment and its git calls."""

    def __init__(self, tmp: Path) -> None:
        self.tmp = tmp
        self.clock = 1_700_000_000
        gpg = tmp / "gpg"
        gpg.write_text("#!/bin/sh\nexit 1\n")
        gpg.chmod(0o755)
        bin_ = tmp / "bin"
        bin_.mkdir()
        (bin_ / "gh").write_text(GH)
        (bin_ / "gh").chmod(0o755)
        self.origin = tmp / "origin.git"
        config = tmp / "gitconfig"
        rewrites = "".join(f"\tinsteadOf = {u}\n" for u in (URL, *FORMS, OTHER))
        config.write_text(
            f'[url "file://{self.origin}"]\n{rewrites}'
            f'[url "file://{tmp / "bad.git"}"]\n\tinsteadOf = {BAD}\n'
            f"[gpg]\n\tprogram = {gpg}\n"
            "[init]\n\tdefaultBranch = main\n"
            "[uploadpack]\n\tallowFilter = true\n"
            '[protocol "file"]\n\tallow = always\n'
        )
        self.ghlog = tmp / "gh.log"
        self.answers = tmp / "gh-answers"
        self.answers.write_text("")
        # no proxy, so that https to 127.0.0.1 stays on this machine
        self.env = {
            k: v
            for k, v in os.environ.items()
            if not k.startswith("GIT_") and not k.lower().endswith("_proxy")
        }
        self.env.update(
            # no case reaches a real ssh
            GIT_SSH_COMMAND="false",
            GIT_CONFIG_GLOBAL=str(config),
            GIT_CONFIG_NOSYSTEM="1",
            GIT_AUTHOR_NAME="Fixture",
            GIT_AUTHOR_EMAIL="fixture@example.invalid",
            GIT_COMMITTER_NAME="Fixture",
            GIT_COMMITTER_EMAIL="fixture@example.invalid",
            PATH=f"{bin_}{os.pathsep}{os.environ.get('PATH', '')}",
            GHLOG=str(self.ghlog),
            GHANSWERS=str(self.answers),
        )

    def git(self, repo: Path, *args: str) -> str:
        done = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            encoding="utf-8",
            env=self.env,
            stdin=subprocess.DEVNULL,
            check=False,
        )
        if done.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {done.stderr.strip()}")
        return done.stdout.strip()

    def bare(self, repo: Path) -> str:
        """A bare repository whose main holds one commit of the empty tree."""
        subprocess.run(
            ["git", "init", "-q", "--bare", str(repo)], env=self.env, check=True
        )
        tree = self.git(repo, "mktree")
        init = subprocess.run(
            ["git", "-C", str(repo), "commit-tree", "-m", "init", tree],
            capture_output=True,
            encoding="utf-8",
            env=self.env,
            stdin=subprocess.DEVNULL,
            check=True,
        ).stdout.strip()
        self.git(repo, "update-ref", "refs/heads/main", init)
        return init

    def commit(self, repo: Path, parent: str, subject: str) -> str:
        """A commit on `parent`, with its tree, that no ref holds yet."""
        self.clock += 60
        env = {
            "GIT_AUTHOR_DATE": f"{self.clock} +0000",
            "GIT_COMMITTER_DATE": f"{self.clock} +0000",
        }
        tree = self.git(repo, "rev-parse", f"{parent}^{{tree}}")
        done = subprocess.run(
            ["git", "-C", str(repo), "commit-tree", "-p", parent, "-m", subject, tree],
            capture_output=True,
            encoding="utf-8",
            env=dict(self.env, **env),
            stdin=subprocess.DEVNULL,
            check=True,
        )
        return done.stdout.strip()

    def raw(self, repo: Path, body: str) -> str:
        """A commit object written as `body` holds it, unchecked."""
        return subprocess.run(
            ["git", "-C", str(repo), "hash-object", "-t", "commit", "-w"]
            + ["--literally", "--stdin"],
            input=body,
            capture_output=True,
            encoding="utf-8",
            env=self.env,
            check=True,
        ).stdout.strip()

    def run(
        self, *args: str, extra: dict[str, str] | None = None
    ) -> tuple[int, list[str], str]:
        """The script's exit code, its lines and its standard error."""
        here = self.tmp / "cwd"
        here.mkdir(exist_ok=True)
        self.ghlog.write_text("")
        done = subprocess.run(
            [sys.executable, "-I", str(SCRIPT), *args],
            cwd=here,
            capture_output=True,
            encoding="utf-8",
            env=dict(self.env, **(extra or {})),
            stdin=subprocess.DEVNULL,
            check=False,
        )
        if any(here.iterdir()):
            fail(f"{args}: the run wrote {sorted(p.name for p in here.iterdir())}")
        return done.returncode, lines(done.stdout), done.stderr

    def asked(self) -> list[str]:
        """The branch of each `gh` call, in order."""
        heads: list[str] = []
        for line in lines(self.ghlog.read_text(encoding="utf-8")):
            for arg in line.split("\037"):
                if arg.startswith("--head="):
                    heads.append(arg.removeprefix("--head="))
        return heads


def state(fx: Fixture, repo: Path) -> tuple[str, ...]:
    """What the script must not write in `repo`."""
    gd = Path(fx.git(repo, "rev-parse", "--absolute-git-dir"))
    return (
        fx.git(repo, "for-each-ref", "--format=%(objectname) %(refname)"),
        fx.git(repo, "worktree", "list", "--porcelain"),
        (gd / "config").read_text(),
        str((gd / "FETCH_HEAD").exists()),
        str(sorted(p.name for p in (gd / "objects" / "info").iterdir())),
        str(sorted(p.name for p in gd.iterdir())),
    )


def has(fx: Fixture, repo: Path, sha: str) -> bool:
    out = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"{sha}^{{commit}}"],
        env=dict(fx.env, GIT_NO_LAZY_FETCH="1"),
        capture_output=True,
        check=False,
    )
    return out.returncode == 0


def expect(
    label: str,
    got: tuple[int, list[str], str],
    code: int,
    lines: list[str],
    err: str = "",
) -> None:
    rc, out, stderr = got
    if rc != code:
        fail(f"{label}: exit {rc}, not {code}: {out} {stderr}")
    if sorted(out) != sorted(lines):
        fail(f"{label}: listed {out}, not {lines}")
    if err not in stderr:
        fail(f"{label}: no {err!r} in {stderr!r}")
    if MARK in "".join(out) + stderr:
        fail(f"{label}: a credential of origin's URL was printed: {out} {stderr}")


def ls_remote(fx: Fixture, repo: Path, extra: dict[str, str]) -> str:
    """What `git ls-remote origin` prints on standard error in `repo`."""
    return subprocess.run(
        ["git", "-C", str(repo), "ls-remote", "origin"],
        capture_output=True,
        encoding="utf-8",
        env=dict(fx.env, **extra),
        stdin=subprocess.DEVNULL,
        check=False,
    ).stderr


def credentials(fx: Fixture, origin: Path) -> None:
    """Refusals where git's or ssh's text names a credential of origin's URL."""
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Refuse)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        here = f"127.0.0.1:{server.server_address[1]}"
        token = f"tok%5F{MARK}"
        password = f"{MARK}%5Fpw"
        asked = f"could not read Password for 'http://****@{here}': "
        ssh = fx.tmp / "ssh"
        ssh.write_text(SSH)
        ssh.chmod(0o755)
        cases = {
            "token": (f"http://{token}@{here}/x", asked),
            "insteadOf": ("https://example.invalid/rewritten", asked),
            "two @": (f"http://oauth2@{MARK}@{here}/x", f"'http://****@{here}/x/'"),
            "ssh": (
                f"ssh://oauth2:{password}@127.0.0.1/x",
                (
                    "debug1: Authenticating to 127.0.0.1:22 as '****:****'; "
                    "****:****@127.0.0.1: Permission denied (publickey)."
                ),
            ),
        }
        extra = {"GIT_SSH_COMMAND": str(ssh)}
        paths: dict[str, Path] = {}
        for label, (url, _) in cases.items():
            path = fx.tmp / f"cred-{len(paths)}"
            fx.git(fx.tmp, "clone", "-q", str(origin), str(path))
            fx.git(path, "remote", "set-url", "origin", url)
            paths[label] = path
        fx.git(
            paths["insteadOf"],
            "config",
            f"url.http://{token}@{here}/.insteadOf",
            "https://example.invalid/",
        )
        basic = fx.tmp / "cred-basic"
        fx.git(fx.tmp, "clone", "-q", str(origin), str(basic))
        fx.git(basic, "remote", "set-url", "origin", f"http://oauth2:{MARK}@{here}/x")
        # the fixtures' configuration with trace2 on standard error, which
        # spells the token as the URL does, and curl's trace unredacted,
        # which carries a user and a password in base64
        traced = fx.tmp / "gitconfig-traced"
        traced.write_text(
            Path(fx.env["GIT_CONFIG_GLOBAL"]).read_text()
            + "[trace2]\n\tnormalTarget = 2\n"
        )
        trace = {
            "GIT_CONFIG_GLOBAL": str(traced),
            "GIT_CURL_VERBOSE": "1",
            "GIT_TRACE_CURL": "1",
            "GIT_TRACE_REDACT": "0",
        }
        coded = base64.b64encode(f"oauth2:{MARK}".encode()).decode()
        # each control: git itself prints the credential
        for label, path in paths.items():
            if MARK not in ls_remote(fx, path, extra):
                fail(f"{label}: git names no credential")
        if token not in ls_remote(fx, paths["token"], trace):
            fail("trace: git does not spell the token as the URL does")
        if coded not in ls_remote(fx, basic, trace):
            fail("trace: curl's trace holds no Authorization header in base64")
        rc, out, err = fx.run(*map(str, paths.values()), extra=extra)
        expect("credentials", (rc, out, err), 1, [])
        for label, (_, shown) in cases.items():
            path = paths[label]
            if f"refused: {path}: git -C {path} ls-remote exited 128: " not in err:
                fail(f"{label}: is not refused by git ls-remote: {err}")
            if shown not in err:
                fail(f"{label}: no {shown!r} in {err!r}")
        rc, out, err = fx.run(str(paths["token"]), str(basic), extra=trace)
        expect("trace", (rc, out, err), 1, [])
        for path in (paths["token"], basic):
            if f"refused: {path}: git -C {path} ls-remote exited 128: " not in err:
                fail(f"trace: {path} is not refused by git ls-remote: {err}")
        if coded in err:
            fail(f"trace: the Authorization header was printed: {err}")
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def main() -> int:
    with tempfile.TemporaryDirectory() as name:
        fx = Fixture(Path(name).resolve())
        o = fx.origin
        init = fx.bare(o)

        # the partial clone's case, made first: lazy-base on origin, then gone
        c12 = fx.commit(o, init, "lazy-base")
        fx.git(o, "update-ref", "refs/heads/lazy-base", c12)
        c13 = fx.commit(o, c12, "lazy-pull")
        fx.git(o, "update-ref", "refs/pull/10/head", c13)
        pc = fx.tmp / "partial"
        fx.git(
            fx.tmp, "clone", "-q", "--filter=blob:none", "--no-checkout", URL, str(pc)
        )
        fx.git(pc, "branch", "lazy", c12)
        fx.git(o, "update-ref", "-d", "refs/heads/lazy-base")

        # each form of origin's URL: f-x at f1, which only form-base held,
        # behind the head of pull request 11, which gh names for f-x
        f1 = fx.commit(o, init, "form-base")
        fx.git(o, "update-ref", "refs/heads/form-base", f1)
        fx.git(o, "update-ref", "refs/pull/11/head", fx.commit(o, f1, "form-pull"))
        forms = []
        for i, url in enumerate(FORMS):
            fc = fx.tmp / f"form{i}"
            fx.git(fx.tmp, "clone", "-q", url, str(fc))
            fx.git(fc, "branch", "f-x", f1)
            forms.append((url, fc))
        other = fx.tmp / "other"
        fx.git(fx.tmp, "clone", "-q", OTHER, str(other))
        fx.git(other, "branch", "f-x", f1)
        fx.git(o, "update-ref", "-d", "refs/heads/form-base")

        ck = fx.tmp / "main"
        fx.git(fx.tmp, "clone", "-q", URL, str(ck))
        if fx.git(ck, "config", "--get", "remote.origin.url") != URL:
            fail("the clone does not name origin as github.com")

        def branch(name: str, subject: str) -> str:
            sha = fx.commit(ck, "origin/main", subject)
            fx.git(ck, "branch", name, sha)
            return sha

        def push(sha: str, ref: str) -> None:
            fx.git(ck, "push", "-q", "origin", f"{sha}:{ref}")

        pushed = branch("b-pushed", "pushed")
        push(pushed, "refs/heads/b-pushed")
        behind = branch("b-behind", "behind")
        push(behind, "refs/heads/b-behind")
        fx.git(o, "update-ref", "refs/heads/b-behind", fx.commit(o, behind, "on"))
        tagged = branch("b-tag", "tagged")
        push(tagged, "refs/heads/tmp")
        fx.git(o, "tag", "-a", "-m", "t", "t4", tagged)
        fx.git(o, "update-ref", "-d", "refs/heads/tmp")
        pr7 = branch("b-pr7", "pr7")
        push(pr7, "refs/pull/7/head")
        pr8 = branch("b-pr8", "pr8")
        push(pr8, "refs/heads/b-pr8")
        c7 = fx.commit(o, pr8, "pr8 moved")
        fx.git(o, "update-ref", "refs/pull/8/head", c7)
        fx.git(o, "update-ref", "-d", "refs/heads/b-pr8")
        pr9 = branch("b-pr9", "pr9")
        push(pr9, "refs/heads/tmp")
        c9 = fx.commit(o, pr9, "pr9 moved")
        fx.git(o, "update-ref", "refs/pull/9/head", c9)
        fx.git(o, "update-ref", "-d", "refs/heads/tmp")
        unpushed = branch("b-unpushed", "unpushed")
        gone = branch("b-gone", "gone")
        push(gone, "refs/heads/b-gone")
        fx.git(o, "update-ref", "-d", "refs/heads/b-gone")
        if not fx.git(ck, "rev-parse", "-q", "--verify", "refs/remotes/origin/b-gone"):
            fail("gone: no remote-tracking ref")
        # only refs/pull/12/merge, a merge GitHub makes, reaches it
        merged = branch("b-merge", "merge")
        push(fx.commit(ck, merged, "the merge"), "refs/pull/12/merge")
        # pushed to another remote alone
        fork = fx.tmp / "fork.git"
        fx.bare(fork)
        forked = branch("b-fork", "fork")
        fx.git(ck, "remote", "add", "fork", str(fork))
        fx.git(ck, "push", "-q", "fork", f"{forked}:refs/heads/b-fork")
        hostile = branch("topic;>MARKER", "hostile")
        # git allows U+2028 in a branch name, where str.splitlines() splits
        spaced = branch("topic\u2028name", "spaced")
        push(branch("\u2028pushed", "aside"), "refs/heads/\u2028pushed")
        held = branch("b-worktree", "worktree")
        fx.git(ck, "worktree", "add", "-q", str(fx.tmp / "wt"), "b-worktree")
        # pull request 8 is the 200th gh lists for b-pr8, which the
        # script's --limit=200 reaches
        fx.answers.write_text(
            "".join(f"own/repo\tb-pr8\t{1000 + i}\tclosed\n" for i in range(199))
            + "own/repo\tb-pr8\t8\tmerged\n"
            "own/repo\tb-pr9\t42\topen\n"
            "own/repo\tf-x\t11\topen\n"
            "own/bad\tb4\t1\topen\n"
        )
        # a fetch that follows these writes the tag t4 and a commit-graph
        fx.git(ck, "config", "remote.origin.tagOpt", "--tags")
        fx.git(ck, "config", "fetch.writeCommitGraph", "true")
        # and these, the automatic maintenance, at once and in the foreground
        fx.git(ck, "config", "gc.auto", "1")
        fx.git(ck, "config", "gc.autoPackLimit", "1")
        fx.git(ck, "config", "fetch.unpackLimit", "1")
        fx.git(ck, "config", "gc.autoDetach", "false")
        fx.git(ck, "config", "maintenance.autoDetach", "false")
        if has(fx, ck, c7) or has(fx, ck, c9):
            fail("the clone holds a pull request's head before the run")

        listed = [
            f"{ck}: b-fork {forked}",
            f"{ck}: b-gone {gone}",
            f"{ck}: b-merge {merged}",
            f"{ck}: b-pr9 {pr9}",
            f"{ck}: b-unpushed {unpushed}",
            f"{ck}: b-worktree {held}",
            f"{ck}: topic;>MARKER {hostile}",
            f"{ck}: topic\u2028name {spaced}",
        ]
        # a hook of the checkout is code the script does not run
        hook = ck / ".git" / "hooks" / "reference-transaction"
        ran = fx.tmp / "hook-ran"
        hook.write_text(f"#!/bin/sh\necho \"$1\" >> '{ran}'\n")
        hook.chmod(0o755)
        before = state(fx, ck)
        expect("one clone", fx.run(str(ck)), 0, listed)
        if state(fx, ck) != before:
            fail(f"one clone: the run wrote: {before} / {state(fx, ck)}")
        if ran.exists():
            fail(f"one clone: the hook ran: {ran.read_text()}")
        hook.unlink()
        want = [
            "b-fork",
            "b-gone",
            "b-merge",
            "b-pr8",
            "b-pr9",
            "b-unpushed",
            "b-worktree",
            "topic;>MARKER",
            "topic\u2028name",
        ]
        if sorted(fx.asked()) != want:
            fail(f"one clone: gh was asked about {fx.asked()}, not {want}")
        log = fx.ghlog.read_text(encoding="utf-8")
        if "--repo=own/repo" not in log.split("\037"):
            fail(f"one clone: gh was not asked about own/repo: {log}")
        if not has(fx, ck, c7):
            fail("one clone: the head of pull request 8 was not fetched")
        if has(fx, ck, c9):
            fail("one clone: the head of pull request 9 was fetched")

        expect(
            "gh fails",
            fx.run(str(ck), extra={"GH_FAIL": "1"}),
            1,
            listed,
            "no pull request lookup",
        )
        expect(
            "gh prints no number",
            fx.run(str(ck), extra={"GH_PRINT": "oops"}),
            1,
            listed,
            "gh pr list printed",
        )
        elsewhere = {
            "GIT_DIR": str(o),
            "GIT_COMMON_DIR": str(o),
            "GIT_OBJECT_DIRECTORY": str(o / "objects"),
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(o / "objects"),
            "GIT_NAMESPACE": "other",
        }
        for key, value in elsewhere.items():
            expect(key, fx.run(str(ck), extra={key: value}), 0, listed)

        for url, fc in forms:
            expect(url, fx.run(str(fc)), 0, [])
            log = fx.ghlog.read_text(encoding="utf-8")
            if "--repo=own/repo" not in log.split("\037"):
                fail(f"{url}: gh was not asked about own/repo")
        expect(
            "not on GitHub, a credential in the URL",
            fx.run(str(other)),
            1,
            [f"{other}: f-x {f1}"],
            f"no pull request lookup: {other}: origin names no repository on GitHub",
        )

        expect("partial clone", fx.run(str(pc)), 0, [f"{pc}: lazy {c12}"])
        if has(fx, pc, c13):
            fail("partial clone: the head of pull request 10 was fetched")

        o2 = fx.tmp / "plain.git"
        fx.bare(o2)
        plain = fx.tmp / "plain"
        fx.git(fx.tmp, "clone", "-q", str(o2), str(plain))
        u = fx.commit(plain, "origin/main", "plain unpushed")
        fx.git(plain, "branch", "u", u)
        expect("no pull request", fx.run(str(plain)), 0, [f"{plain}: u {u}"])
        if fx.asked():
            fail(f"no pull request: gh was asked about {fx.asked()}")

        # a commit with no author email, which a clone checking what it
        # fetches refuses
        def bad(repo: Path, parent: str) -> str:
            tree = fx.git(repo, "rev-parse", f"{parent}^{{tree}}")
            who = "1700000000 +0000"
            return fx.raw(
                repo,
                f"tree {tree}\nparent {parent}\nauthor Fixture {who}\n"
                f"committer Fixture <fixture@example.invalid> {who}\n\nbad\n",
            )

        o3 = fx.tmp / "fsck.git"
        init3 = fx.bare(o3)
        strict = fx.tmp / "strict"
        fx.git(fx.tmp, "clone", "-q", str(o3), str(strict))
        fx.git(strict, "config", "fetch.fsckObjects", "true")
        fx.git(o3, "update-ref", "refs/heads/bad", bad(o3, init3))
        w3 = fx.commit(strict, "origin/main", "strict unpushed")
        fx.git(strict, "branch", "w", w3)
        expect(
            "a fetch of a branch fails",
            fx.run(str(strict)),
            1,
            [f"{strict}: w {w3}"],
            f"no fetch: {strict}: ",
        )

        o4 = fx.tmp / "bad.git"
        fx.bare(o4)
        strict4 = fx.tmp / "strict4"
        fx.git(fx.tmp, "clone", "-q", BAD, str(strict4))
        fx.git(strict4, "config", "fetch.fsckObjects", "true")
        w4 = fx.commit(strict4, "origin/main", "strict4 unpushed")
        fx.git(strict4, "branch", "b4", w4)
        fx.git(strict4, "push", "-q", "origin", f"{w4}:refs/heads/tmp")
        fx.git(o4, "update-ref", "refs/pull/1/head", bad(o4, w4))
        fx.git(o4, "update-ref", "-d", "refs/heads/tmp")
        expect(
            "a fetch of a pull request's head fails",
            fx.run(str(strict4)),
            1,
            [f"{strict4}: b4 {w4}"],
            f"no fetch: {strict4}: ",
        )

        # a replace ref, and a graft, that would make origin's main reach a
        # commit pushed nowhere
        init2 = fx.git(o2, "rev-parse", "main")
        for how in ("replace", "graft"):
            rg = fx.tmp / how
            fx.git(fx.tmp, "clone", "-q", str(o2), str(rg))
            tree = fx.git(rg, "rev-parse", "HEAD^{tree}")
            root = fx.raw(
                rg,
                f"tree {tree}\nauthor Fixture <fixture@example.invalid> "
                f"1700000000 +0000\ncommitter Fixture <fixture@example.invalid> "
                f"1700000000 +0000\n\n{how} root\n",
            )
            fx.git(rg, "branch", "r", root)
            if how == "replace":
                fx.git(rg, "replace", init2, fx.commit(rg, root, "replacement"))
            else:
                (rg / ".git" / "info").mkdir(exist_ok=True)
                (rg / ".git" / "info" / "grafts").write_text(f"{init2} {root}\n")
            if fx.git(rg, "rev-list", "-n", "1", root, f"^{init2}"):
                fail(f"{how}: git still reads {root} as unreached from main")
            expect(how, fx.run(str(rg)), 0, [f"{rg}: r {root}"])

        local = fx.tmp / "local"
        fx.git(fx.tmp, "clone", "-q", str(o), str(local))
        v = fx.commit(local, "origin/main", "local unpushed")
        fx.git(local, "branch", "v", v)
        expect(
            "not on GitHub",
            fx.run(str(local)),
            1,
            [f"{local}: v {v}"],
            "names no repository on GitHub",
        )
        # nothing unreached: no lookup is needed, and nothing is fetched
        local2 = fx.tmp / "local2"
        fx.git(fx.tmp, "clone", "-q", str(o), str(local2))
        late = fx.commit(o, init, "late")
        fx.git(o, "update-ref", "refs/heads/late", late)
        expect("nothing unreached", fx.run(str(local2)), 0, [])
        if has(fx, local2, late):
            fail("nothing unreached: origin's branch late was fetched")
        fx.git(o, "update-ref", "-d", "refs/heads/late")

        alone = fx.tmp / "alone"
        subprocess.run(["git", "init", "-q", str(alone)], env=fx.env, check=True)
        lost = fx.tmp / "lost"
        fx.git(fx.tmp, "clone", "-q", str(o2), str(lost))
        fx.git(lost, "remote", "set-url", "origin", str(fx.tmp / "nowhere.git"))
        secret = fx.tmp / "secret"
        fx.git(fx.tmp, "clone", "-q", str(o2), str(secret))
        fx.git(secret, "remote", "set-url", "origin", f"https://x:{MARK}@127.0.0.1:9/x")
        secrets = [secret]
        for scheme in ("http", "ssh"):
            path = fx.tmp / f"secret-{scheme}"
            fx.git(fx.tmp, "clone", "-q", str(o2), str(path))
            url = f"{scheme}://x:{MARK}@127.0.0.1:9/x"
            fx.git(path, "remote", "set-url", "origin", url)
            secrets.append(path)
        odd = fx.tmp / "odd"
        fx.git(fx.tmp, "clone", "-q", str(o2), str(odd))
        blob = subprocess.run(
            ["git", "-C", str(odd), "hash-object", "-w", "--stdin"],
            input="blob\n",
            capture_output=True,
            encoding="utf-8",
            env=fx.env,
            check=True,
        ).stdout.strip()
        # git refuses to point a branch at a blob, so the ref is written by hand
        (odd / ".git" / "refs" / "heads" / "blob").write_text(f"{blob}\n")
        odd2 = fx.tmp / "odd2"
        fx.git(fx.tmp, "clone", "-q", str(o2), str(odd2))
        fx.git(odd2, "tag", "-a", "-m", "a tag", "t", "HEAD")
        tag = fx.git(odd2, "rev-parse", "refs/tags/t")
        (odd2 / ".git" / "refs" / "heads" / "tagged").write_text(f"{tag}\n")
        rc, out, err = fx.run(
            str(fx.tmp / "none"),
            str(alone),
            str(lost),
            str(odd),
            str(odd2),
            *map(str, secrets),
            str(plain),
            extra={"GIT_TRACE": "1"},
        )
        expect(
            "refused",
            (rc, out, err),
            1,
            [f"{plain}: u {u}"],
            f"refused: {alone}: no remote named origin",
        )
        for which in (
            "none",
            "lost",
            "odd",
            "odd2",
            "secret",
            "secret-http",
            "secret-ssh",
        ):
            if f"refused: {fx.tmp / which}: " not in err:
                fail(f"refused: {which} is not refused: {err}")

        credentials(fx, o2)

        expect("no checkout", fx.run(), 2, [], "usage:")
        expect("an option", fx.run("--all", str(plain)), 2, [], "usage:")
        expect("an option after", fx.run(str(plain), "--all"), 2, [], "usage:")
    if failures:
        return 1
    print("unpushed-branches.py answers as expected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
