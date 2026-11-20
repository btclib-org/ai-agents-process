#!/usr/bin/env python3
"""Run assignment-fence.py on small Markdown files and check its answer.

    python3 scripts/test-assignment-fence.py

Each case is one file, written to a directory of its own inside one
temporary directory and given to the script. This prints each case whose
answer is wrong, and exits 1 where there is one.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("assignment-fence.py")


def shell(*lines: str) -> str:
    return "Text.\n\n```shell\n" + "\n".join(lines) + "\n```\n"


def listed(names: str, line: int, what: str) -> list[str]:
    """The line the script prints for a fence whose first assignment is line 4."""
    return [f"4: {names} share a fence with a write on line {line} ({what})"]


OWN = "\n## This repository in particular\n\n"
N = "n=<n>"

# (name, file, the lines the script prints, after `<file>:`), and the
# file's name where it is not `case<i>.md`
CASES: list[tuple[str, str, list[str]] | tuple[str, str, list[str], str]] = [
    ("a write", shell(N, 'gh pr close "${n:?}"'), listed("n", 5, "gh pr close")),
    ("a read", shell(N, 'gh pr view "${n:?}"'), []),
    (
        "the assignment in a fence of its own",
        shell(N) + shell('gh pr close "${n:?}"'),
        [],
    ),
    (
        "two names and a later write",
        shell(N, "repo=<owner>/<repo>", "gh pr view", 'git -C "$w" fetch'),
        listed("n, repo", 7, "git fetch"),
    ),
    (
        "set --",
        shell("set -- <the heads>", 'git merge "$@"'),
        listed("set --", 5, "git merge"),
    ),
    ("a derived value", shell("d=${x:?}/y", 'rm -f "${d:?}"'), []),
    ("a quoted placeholder", shell('x="<a>"', 'rm -f "$x"'), []),
    (
        "a placeholder with an apostrophe",
        shell("s=<the session's dir>", 'mkdir -p "$s"'),
        listed("s", 5, "mkdir"),
    ),
    (
        "an indented fence",
        "- item\n\n  ```shell\n  n=<n>\n  rm x\n  ```\n",
        listed("n", 5, "rm"),
    ),
    ("a redirection", shell(N, 'echo x > "${f:?}"'), listed("n", 5, ">")),
    ("an append", shell(N, "echo x >> log"), listed("n", 5, ">")),
    ("/dev/null", shell(N, "git show x > /dev/null 2>&1"), []),
    ("a descriptor", shell(N, "echo x >&2"), []),
    ("a read redirection", shell(N, 'read -r a < "$f"'), []),
    ("git fetch", shell(N, "git -C w fetch origin"), listed("n", 5, "git fetch")),
    (
        "git reads",
        shell(N, "git -C w show x", "git log", "git merge-tree --write-tree a b"),
        [],
    ),
    ("git branch, read", shell(N, "git branch --show-current"), []),
    ("git branch, a name", shell(N, "git branch new"), listed("n", 5, "git branch")),
    ("git config, read", shell(N, "git config --get a.b"), []),
    ("git config, set", shell(N, "git config a.b c"), listed("n", 5, "git config")),
    ("git worktree list", shell(N, "git worktree list"), []),
    (
        "git worktree add",
        shell(N, "git worktree add d"),
        listed("n", 5, "git worktree"),
    ),
    ("gh api, read", shell(N, 'gh api "repos/x/pulls/${n:?}" --jq .a'), []),
    ("gh api, a method", shell(N, "gh api -X PATCH repos/x"), listed("n", 5, "gh api")),
    ("gh api, a field", shell(N, "gh api repos/x -f a=b"), listed("n", 5, "gh api")),
    ("gh api, a field and GET", shell(N, "gh api -X GET repos/x -f a=b"), []),
    ("graphql, a query", shell(N, "gh api graphql -f query='query { a }'"), []),
    (
        "graphql, a mutation",
        shell(N, "gh api graphql -f query='mutation { a }'"),
        listed("n", 5, "gh api"),
    ),
    ("gh search", shell(N, "gh search prs x"), []),
    ("uv sync", shell(N, "env -C w uv sync --locked"), listed("n", 5, "uv sync")),
    ("uv python dir", shell(N, 'x="$(uv python dir)"'), []),
    (
        "uv run, a script that reads",
        shell(N, "uv run --no-project --python 3.15 python -I s/pointer-files.py"),
        [],
    ),
    (
        "uv run, a script it does not name",
        shell(N, "uv run --no-project --python 3.15 python -I x.py"),
        listed("n", 5, "python"),
    ),
    (
        "uvx pre-commit run",
        shell(N, "uvx pre-commit run --all-files"),
        listed("n", 5, "pre-commit run"),
    ),
    ("a parameter alone", shell(N, '"$@" uv sync'), listed("n", 5, "uv sync")),
    ("timeout", shell(N, "timeout -k 60 9 rm x"), listed("n", 5, "rm")),
    ("xargs", shell(N, "printf x | xargs -0 rm -f"), listed("n", 5, "rm")),
    ("in $( )", shell(N, "list=$(mktemp)"), listed("n", 5, "mktemp")),
    ("in a backquote", shell(N, "a=`rm x`"), listed("n", 5, "rm")),
    ("in <( )", shell(N, "cat <(rm x)"), listed("n", 5, "rm")),
    ("sh -c", shell(N, "sh -c 'rm -f x' sh"), listed("n", 5, "rm")),
    ("python -c", shell(N, 'python3 -c \'open("x", "w")\''), []),
    ("find -exec", shell(N, "find . -name x -exec mv {} y \\;"), listed("n", 5, "mv")),
    (
        "find -delete",
        shell(N, "find . -name x -delete"),
        listed("n", 5, "find -delete"),
    ),
    ("find -print", shell(N, "find . -name x -print"), []),
    ("sed -i", shell(N, "sed -i '' s/a/b/ f"), listed("n", 5, "sed")),
    ("sed -n", shell(N, "sed -n 1p f"), []),
    ("perl -pi", shell(N, "perl -pi -e s/a/b/ f"), listed("n", 5, "perl")),
    ("kill -0", shell(N, 'kill -0 "$p"'), []),
    ("kill", shell(N, 'kill "$p"'), listed("n", 5, "kill")),
    ("a function's body", shell(N, "f() {", "  rm x", "}"), listed("n", 6, "rm")),
    (
        "sweep.sh",
        shell(N, 'sh "${P:?}/scripts/sweep.sh" work w'),
        listed("n", 5, "sweep.sh"),
    ),
    ("another script", shell(N, 'sh "${P:?}/scripts/x.sh" w'), listed("n", 5, "x.sh")),
    (
        "a heredoc's body, then a write",
        shell(N, "cat <<EOF", "rm x", "EOF", "touch y"),
        listed("n", 8, "touch"),
    ),
    ("a comment", shell(N, "# rm x", "true"), []),
    ("a comment that would write", shell(N, "# echo x > f", "true"), []),
    ("a text fence", "```text\nn=<n>\nrm x\n```\n", []),
    ("nice -n", shell(N, 'nice -n 5 rm "$n"'), listed("n", 5, "rm")),
    (
        "git config --unset",
        shell(N, "git config --unset a.b"),
        listed("n", 5, "git config"),
    ),
    (
        "in $( ) in ${ }",
        shell(N, 'printf x "${c:-$(touch m)}"'),
        listed("n", 5, "touch"),
    ),
    (
        "a closing fence with a trailing space",
        "Text.\n\n```shell\nn=<n>\n``` \n\n```shell\nrm x\n```\n",
        [],
    ),
    (
        "gh api --method=",
        shell(N, "gh api repos/x --method=DELETE"),
        listed("n", 5, "gh api"),
    ),
    ("gh api -XDELETE", shell(N, "gh api -XDELETE repos/x"), listed("n", 5, "gh api")),
    (
        "gh api --field=",
        shell(N, "gh api repos/x --field=a=b"),
        listed("n", 5, "gh api"),
    ),
    (">& a file", shell(N, "printf x >&out.log"), listed("n", 5, ">")),
    (">&-", shell(N, "exec 3>&-"), []),
    (
        "find, a read -exec, then -delete",
        shell(N, "find . -exec printf x {} \\; -delete"),
        listed("n", 5, "find -delete"),
    ),
    ("after then", shell("if true; then n=<n>; fi", 'rm "$n"'), listed("n", 5, "rm")),
    ("<in >out", shell(N, "sort <in >out"), listed("n", 5, ">")),
    ("<in 2>err", shell(N, "tr a b <in 2>err"), listed("n", 5, ">")),
    (
        "a placeholder with a space, then /",
        shell("d=<gate wt>/x", "rm y"),
        listed("d", 5, "rm"),
    ),
    ("perl -0pi", shell(N, "perl -0pi -e 's/a/b/' f"), listed("n", 5, "perl")),
    ("perl -Mstrict -ne", shell(N, "perl -Mstrict -ne 'print' f"), []),
    ("perl -MList::Util=sum", shell(N, "perl -MList::Util=sum -le 'print' f"), []),
    ("perl -ne", shell(N, "perl -ne 'print' f"), []),
    ("sh -ec", shell(N, "sh -ec 'rm -rf x'"), listed("n", 5, "rm")),
    ("bash -lc", shell(N, "bash -lc 'rm x'"), listed("n", 5, "rm")),
    (
        "bash -euo pipefail -c",
        shell(N, "bash -euo pipefail -c 'rm x'"),
        listed("n", 5, "rm"),
    ),
    ("bash -c", shell(N, "bash -c 'rm x'"), listed("n", 5, "rm")),
    ("bash -c, a read", shell(N, "bash -c 'ls x'"), []),
    ("uv -q sync", shell(N, "uv -q sync"), listed("n", 5, "uv sync")),
    (
        "uv --directory d sync",
        shell(N, "uv --directory d sync"),
        listed("n", 5, "uv sync"),
    ),
    (
        "uv --directory d run",
        shell(N, "uv --directory d run python s/port-check.py"),
        [],
    ),
    (">|", shell(N, "echo x >| f"), listed("n", 5, ">")),
    ("<>", shell(N, "exec 3<> f"), listed("n", 5, ">")),
    ("&>", shell(N, "make &> log"), listed("n", 5, ">")),
    ("git tag, a name", shell(N, "git tag v1"), listed("n", 5, "git tag")),
    ("git tag -l", shell(N, "git tag -l"), []),
    ("git hash-object -w", shell(N, "git hash-object -w f"), []),
    ("git hash-object", shell(N, "git hash-object f"), []),
    (
        "a <<- heredoc's body, then a write",
        shell(N, "cat <<-EOF", "\trm x", "\tEOF", "touch y"),
        listed("n", 8, "touch"),
    ),
    ("a continued line", shell(N, "true &&", "  rm \\", "  x"), listed("n", 6, "rm")),
    (
        "a copy of the standard, and its own part",
        shell(N, "rm") + OWN + shell(N, "rm y"),
        ["13: n share a fence with a write on line 14 (rm)"],
        "CONTRIBUTING.md",
    ),
    (
        "a copy of the standard whose heading is spelt otherwise",
        shell(N, "rm") + "\n## This Repository In Particular\n\n" + shell(N, "rm y"),
        ['(stderr) lacks the heading "## This repository in particular"'],
        "REVIEWING.md",
    ),
    # F1: a redirection that looks like a placeholder
    ('2>"$e"', shell(N, 'sort <in 2>"$e"'), listed("n", 5, ">")),
    ("2>/tmp/e", shell(N, "sort <in 2>/tmp/e"), listed("n", 5, ">")),
    ("2>${e:?}", shell(N, "sort <in 2>${e:?}"), listed("n", 5, ">")),
    ("<f; then 2>", shell(N, 'cat <f; echo x 2>"$o"'), listed("n", 5, ">")),
    ("<in, a tab, >out", shell(N, "sort <in\t>out"), listed("n", 5, ">")),
    ("<in, a tab, 2>err", shell(N, "sort <in\t2>err"), listed("n", 5, ">")),
    ("<a, a tab, b>c", shell(N, "cat <a\tb>c"), listed("n", 5, ">")),
    ("a placeholder with a tab", shell("d=<a\tb>", "rm y"), listed("d", 5, "rm")),
    # F2: sed's in-place forms
    ("sed -Ei", shell(N, "sed -Ei '' 's/a/b/' f"), listed("n", 5, "sed")),
    ("sed -ni", shell(N, "sed -ni 's/a/b/p' f"), listed("n", 5, "sed")),
    ("sed --in-place", shell(N, "sed --in-place 's/a/b/' f"), listed("n", 5, "sed")),
    ("sed -I", shell(N, "sed -I '' 's/a/b/' f"), listed("n", 5, "sed")),
    ("sed -e i", shell(N, "sed -e i\\x f"), []),
    # F3
    (
        "function f { }",
        shell(N, "function f { touch x; }"),
        listed("n", 5, "touch"),
    ),
    ("a call of a function the fence defines", shell(N, "f() { :; }", "f"), []),
    # F4: git forms that write
    (
        "git archive -o",
        shell(N, "git archive -o f HEAD"),
        listed("n", 5, "git archive"),
    ),
    (
        "git archive --output=",
        shell(N, "git archive --output=f HEAD"),
        listed("n", 5, "git archive"),
    ),
    ("git archive", shell(N, "git archive HEAD | wc -c"), []),
    ("git diff --output=", shell(N, "git diff --output=f"), listed("n", 5, "git diff")),
    ("git log --output=", shell(N, "git log --output=f"), listed("n", 5, "git log")),
    (
        "git branch --unset-upstream",
        shell(N, "git branch --unset-upstream"),
        listed("n", 5, "git branch"),
    ),
    (
        "git branch --set-upstream-to=",
        shell(N, "git branch --set-upstream-to=o/x"),
        listed("n", 5, "git branch"),
    ),
    ("git branch --contains", shell(N, "git branch --contains abc"), []),
    (
        "git with an unknown option",
        shell(N, "git --exec-path=x status"),
        listed("n", 5, "git"),
    ),
    # F6: uv
    ("uv build", shell(N, "uv build --out-dir d"), listed("n", 5, "uv build")),
    ("uv venv", shell(N, "uv venv d"), listed("n", 5, "uv venv")),
    ("uv export", shell(N, "uv export -o r.txt"), listed("n", 5, "uv export")),
    ("uv publish", shell(N, "uv publish"), listed("n", 5, "uv publish")),
    (
        "uv --color never sync",
        shell(N, "uv --color never sync"),
        listed("n", 5, "uv sync"),
    ),
    ("uv, an unknown option", shell(N, "uv --frob x sync"), listed("n", 5, "uv")),
    ("uv version", shell(N, "uv version"), []),
    # F7
    ("env -S", shell(N, "env -S 'touch x'"), listed("n", 5, "touch")),
    ("env -S, attached", shell(N, "env '-Stouch x'"), listed("n", 5, "touch")),
    ("env -S, a read", shell(N, "env -S 'ls x'"), []),
    ("command -v", shell(N, "command -v touch"), []),
    ("command", shell(N, "command touch x"), listed("n", 5, "touch")),
    # F8: no redirection, and gh's own option
    ("(( > ))", shell(N, "(( a > 5 )) && echo y"), []),
    ("if (( > ))", shell(N, "if (( a > 5 )); then echo y; fi"), []),
    ("$(( > ))", shell(N, "echo $(( a > 5 ))"), []),
    ("[[ > ]]", shell(N, '[[ "$a" > "$b" ]]'), []),
    ("if [[ > ]]", shell(N, 'if [[ "$a" > "$b" ]]; then :; fi'), []),
    ("[[ ]] then >", shell(N, '[[ "$a" ]] && echo y > f'), listed("n", 5, ">")),
    ("[ > ]", shell(N, '[ "$a" > "$b" ]'), listed("n", 5, ">")),
    ("gh -R", shell(N, "gh -R o/r pr view 5"), []),
    ("gh -R, a write", shell(N, "gh -R o/r pr close 5"), listed("n", 5, "gh pr close")),
    # F9: what the script does not know writes
    ("dd of=", shell(N, "dd if=a of=f"), listed("n", 5, "dd")),
    ("curl -o", shell(N, "curl -o f https://x"), listed("n", 5, "curl")),
    ("killall", shell(N, "killall x"), listed("n", 5, "killall")),
    ("eval", shell(N, "eval 'touch x'"), listed("n", 5, "touch")),
    ("eval, a read", shell(N, "eval 'ls x'"), []),
    ("trap", shell(N, "trap 'rm -f x' EXIT"), listed("n", 5, "rm")),
    ("find -fprint", shell(N, "find . -fprint out"), listed("n", 5, "find -fprint")),
    ("gsed -i", shell(N, "gsed -i s/a/b/ f"), listed("n", 5, "gsed")),
    (
        "a script the tree runs",
        shell(N, "s/agents-toml.py x"),
        listed("n", 5, "agents-toml.py"),
    ),
    ("source", shell(N, '. "$P/x.sh"'), listed("n", 5, "x.sh")),
    ("source gate-lock.sh", shell(N, '. "$P/scripts/gate-lock.sh"'), []),
    ("python -", shell(N, "gh api x | python3 -I - a"), []),
    ("for", shell(N, "for i in $(seq 3); do echo $i; done"), []),
    ("a comment after a word", shell(N, "echo x # > f"), []),
    ("case", shell(N, 'case "$x" in', "  a) rm y ;;", "esac"), listed("n", 6, "rm")),
    ("case, a pattern", shell(N, 'case "$x" in', "  a>b) echo ;;", "esac"), []),
    ("case on one line", shell(N, 'case "$x" in a) rm y;; esac'), listed("n", 5, "rm")),
    # F12: the helpers
    ("perl -0x0Api", shell(N, "perl -0x0Api -e s/a/b/ f"), listed("n", 5, "perl")),
    ("perl -l0pi", shell(N, "perl -l0pi -e s/a/b/ f"), listed("n", 5, "perl")),
    ("a bare bash -c", shell(N, "bash -c"), listed("n", 5, "bash")),
    ("env NAME=", shell(N, "env A=1 true"), []),
    ("env NAME=, a write", shell(N, "env A=1 rm x"), listed("n", 5, "rm")),
    ("xargs -I {}", shell(N, "xargs -I {} echo {}"), []),
    ("xargs -I {}, a write", shell(N, "xargs -I {} rm {}"), listed("n", 5, "rm")),
    ("sandbox-exec -f", shell(N, "sandbox-exec -f p true"), []),
    ("sandbox-exec, a write", shell(N, "sandbox-exec -f p rm x"), listed("n", 5, "rm")),
    ("gh api --input", shell(N, "gh api --input f repos/x"), listed("n", 5, "gh api")),
    ("git tag -l 'v*'", shell(N, "git tag -l 'v*'"), []),
    ("git tag -d", shell(N, "git tag -d v1"), listed("n", 5, "git tag")),
    ("in >( )", shell(N, "echo x >(rm y)"), listed("n", 5, "rm")),
    ("a placeholder, then a letter", shell(N, "printf %s <word>s"), []),
    ('<in, a tab, >"$o"', shell(N, 'sort <in\t>"$o"'), listed("n", 5, ">")),
    ("perl -xi", shell(N, "perl -xi x.pl"), []),
    ("[[ ]] >", shell(N, '[[ -n "$a" ]] > f'), listed("n", 5, ">")),
    (
        "case, a second pattern",
        shell(N, 'case "$x" in', "  a) echo ;;", "  b>c) echo ;;", "esac"),
        [],
    ),
    ("sed -ei", shell(N, "sed -ei f"), []),
    ("sort -o", shell(N, "sort -o out in"), listed("n", 5, "sort")),
    ("sort -uo", shell(N, "sort -uo out in"), listed("n", 5, "sort")),
    ("sort -u", shell(N, "sort -u in"), []),
    ("uniq in out", shell(N, "uniq in out"), listed("n", 5, "uniq")),
    ("uniq in", shell(N, "uniq in"), []),
    ("sysctl -w", shell(N, "sysctl -w a.b=1"), listed("n", 5, "sysctl")),
    ("sysctl name=value", shell(N, "sysctl a.b=1"), listed("n", 5, "sysctl")),
    ("sysctl -n", shell(N, "sysctl -n hw.ncpu"), []),
]


def main() -> None:
    wrong = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, (name, text, want, *named) in enumerate(CASES):
            path = Path(tmp) / str(i) / (named[0] if named else f"case{i}.md")
            path.parent.mkdir()
            path.write_text(text, encoding="utf-8")
            done = subprocess.run(
                [sys.executable, "-I", str(SCRIPT), str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
            got = [line.split(":", 1)[-1] for line in done.stdout.splitlines()]
            got += [
                "(stderr)" + line.split(":", 1)[-1] for line in done.stderr.splitlines()
            ]
            if got != want or done.returncode != (1 if want else 0):
                wrong.append(f"{name}: exit {done.returncode}, {got}, want {want}")
    if wrong:
        print("\n".join(wrong))
    sys.exit(1 if wrong else 0)


if __name__ == "__main__":
    main()
