#!/usr/bin/env python3
"""Run placeholder-last.py on small Markdown files and check its answer.

    python3 scripts/test-placeholder-last.py

Each case is one file, written to a new temporary directory and given
to the script. The script prints each case whose answer is wrong, and
exits 1 where there is one.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("placeholder-last.py")


def shell(*lines: str) -> str:
    return "Text.\n\n```shell\n" + "\n".join(lines) + "\n```\n"


OWN = "\n## This repository in particular\n\n"

# (name, file, the lines the script prints, after `<file>:`), and the
# file's name where it is not `case<i>.md`
CASES: list[tuple[str, str, list[str]] | tuple[str, str, list[str], str]] = [
    ("last on its line", shell("git -C <wt> fetch origin <sha>"), ["4: <wt>"]),
    ("an assignment", shell("wt=<wt>", 'git -C "${wt:?}" fetch'), []),
    ("a word of placeholders", shell("repo=<owner>/<repo>"), []),
    (
        "a word of placeholders, then more",
        shell("gh api repos/<owner>/<repo>/pulls --jq ."),
        ["4: repos/<owner>/<repo>/pulls"],
    ),
    (
        "a line that continues",
        shell("gh pr view <n> \\", "  --json state"),
        ["4: <n>"],
    ),
    ("a placeholder with a space", shell("x <gate wt> y"), ["4: <gate wt>"]),
    ("indented fence", "- item\n\n  ```shell\n  a <b> c\n  ```\n", ["4: <b>"]),
    ("in double quotes", shell('gh x --search "<issue> in:title" y'), []),
    ("in single quotes", shell("gh x --jq '.[<n>]' y"), []),
    (
        "single quotes across lines",
        shell("gh x --jq '", "  <n> | .a' y"),
        [],
    ),
    (
        "inside $( ) in double quotes",
        shell('x="$(realpath <gate wt>)" y'),
        ["4: <gate wt>"],
    ),
    ("a comment after it", shell("git <a> # note"), ["4: <a>"]),
    ("a comment's line", shell("# see <a> here", "true"), ["4: <a>"]),
    (
        "a quote a comment opens",
        shell("# the session's", "x <a> y", "# the reviewer's", "x <b> y"),
        ["7: <b>"],
    ),
    ("a heredoc's body", shell("cat <<EOF", "<a> b", "EOF", "x <c> y"), ["7: <c>"]),
    ("a quoted heredoc", shell("cat <<'EOF'", "<a> b", "EOF"), []),
    (
        "a heredoc's delimiter after a backslash",
        shell("cat <<\\EOF", "<a> b", "EOF", "cat <input> output"),
        ["7: <input>"],
    ),
    (
        "a heredoc's delimiter quoted in part",
        shell('cat <<E"O"F', "<a> b", "EOF", "cat <input> output"),
        ["7: <input>"],
    ),
    (
        "a heredoc's delimiter holding an escaped double quote",
        shell('cat <<"E\\"OF"', "<a> b", 'E"OF', "cat <input> output"),
        ["7: <input>"],
    ),
    (
        "a heredoc's delimiter in $' '",
        shell("cat <<$'E'", "x", "E", "true <a> m1"),
        ["7: <a>"],
    ),
    (
        "a heredoc's delimiter in $' ' with escapes",
        shell("cat <<$'E\\x4fF\\q'", "x", "EOFq", "true <a> m1"),
        ["7: <a>"],
    ),
    (
        "a heredoc's delimiter in $' ' holding an escaped apostrophe",
        shell("cat <<$'E\\''", "x", "E'", "true <a> m1"),
        ["7: <a>"],
    ),
    (
        "a heredoc's tabs taken off by <<-",
        shell("cat <<-EOF", "<a> b", "\tEOF", "x <c> y"),
        ["7: <c>"],
    ),
    (
        "a heredoc's tabs kept by <<",
        shell("cat <<EOF", "\tEOF", "x <c> y", "EOF"),
        [],
    ),
    (
        "a heredoc in an indented fence",
        "- item\n\n  ```shell\n  cat <<EOF\n  b\n  EOF\n  x <a> y\n  ```\n",
        ["7: <a>"],
    ),
    (
        "an indented fence's body indented further",
        "- item\n\n  ```shell\n  cat <<EOF\n    EOF\n  x <a> y\n  EOF\n  ```\n",
        [],
    ),
    ("redirections", shell('done < "$list" > out 2>&1', "cat <(ls) <<< x"), []),
    ("a text fence", "```text\na <b> c\n```\n", []),
    (
        "a closing fence with trailing spaces",
        "```shell\ntrue\n```  \n\n```text\na <b> c\n```\n",
        [],
    ),
    (
        "a closing fence with a trailing tab",
        "```shell\ntrue\n```\t\n\n```text\na <b> c\n```\n",
        [],
    ),
    (
        "a shorter fence inside a longer one",
        "````shell\n```\na <b> c\n````\n",
        ["3: <b>"],
    ),
    (
        "a fence with an info string inside one",
        "```shell\n```text\na <b> c\n```\n",
        ["3: <b>"],
    ),
    ("two fences", shell("a=<b>") + shell("c <d> e"), ["9: <d>"]),
    ("an operator after it", shell("a <b> && c"), ["4: <b>"]),
    ("a word that goes on past it", shell("cat <a>.txt"), ["4: <a>.txt"]),
    (
        "an apostrophe in a placeholder",
        shell("scratchpad=<the session's scratchpad>", "git -C <wt> fetch origin"),
        ["5: <wt>"],
    ),
    ("a double quote ends a placeholder", shell('cat <in"x">out'), []),
    ("a backquote ends a placeholder", shell("cat <in`x`>out"), []),
    ("an arithmetic shift", shell("echo $((1<<3))", "x <a> y"), ["5: <a>"]),
    ("an arithmetic comparison", shell("[ $((a<b)) ] && echo x > out"), []),
    ("an arithmetic command", shell("(( n <<= 1 ))", "x <a> y"), ["5: <a>"]),
    ("an old arithmetic shift", shell("echo $[1<<3]", "true <a> m1"), ["5: <a>"]),
    (
        "an old arithmetic in double quotes, and a subscript in one",
        shell('echo "$[1<<3]" $[a[1]<<2]', "true <a> m1"),
        ["5: <a>"],
    ),
    (
        "a command substitution in arithmetic",
        shell("echo $(( $(cat <a> b) + 1 ))"),
        ["4: <a>"],
    ),
    ("a parameter's default", shell("echo ${x:-<a>} y"), []),
    (
        "an apostrophe in a parameter's default in double quotes",
        shell('echo "${x:-don\'t}"', "cat <input> output"),
        ["5: <input>"],
    ),
    (
        "a quote in a parameter's default",
        shell("echo ${x:-'}'}", "cat <input> output"),
        ["5: <input>"],
    ),
    (
        "a backquote's last word",
        shell("echo `printf x`", 'echo "`printf y`"', "cat <input> output"),
        ["6: <input>"],
    ),
    (
        "a command substitution in a parameter's default",
        shell("echo ${x:-$(cat <input> output)}"),
        ["4: <input>"],
    ),
    (
        "a here-string, then a line",
        shell('cat <<< "$x"', "a <b> c"),
        ["5: <b>"],
    ),
    (
        "a copy of the standard, and its own part",
        shell("a <b> c") + OWN + shell("d <e> f"),
        ["12: <e>"],
        "CONTRIBUTING.md",
    ),
    (
        "a copy of the standard whose heading is spelt otherwise",
        shell("a <b> c") + "\n## This Repository In Particular\n\n" + shell("d <e> f"),
        [' lacks the heading "## This repository in particular"'],
        "REVIEWING.md",
    ),
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
            got = [line.split(":", 1)[1] for line in done.stdout.splitlines()]
            if got != want or done.returncode != (1 if want else 0):
                wrong.append(f"{name}: exit {done.returncode}, {got}, want {want}")
    if wrong:
        print("\n".join(wrong))
    sys.exit(1 if wrong else 0)


if __name__ == "__main__":
    main()
