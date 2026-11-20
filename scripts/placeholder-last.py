#!/usr/bin/env python3
r"""List each bare placeholder that is not the last word of its line.

    python3 scripts/placeholder-last.py <file>...

Section 9 of the organization's standard, *A placeholder is bare, and
last*, is the rule: a value the reader sets goes in an assignment block
and is read as `${name:?}`. The script reads the `shell` fences of each
Markdown file it is given, prints `<file>:<line>: <word>` for each shell
word holding a bare placeholder that is not its line's last word, and
exits 1 where it prints one. In `CONTRIBUTING.md` and `REVIEWING.md`,
whose text down to `## This repository in particular` is the
organization's copy and changes there first, it reads only what follows
that heading.

A placeholder is `<`, a letter, then anything but a newline, a quote,
`<` or `>`, then `>`. It is bare where no quote holds it, and one inside
`$( )` is bare again, as the shell reads it. A word made of placeholders
and the text between them, as `<owner>/<repo>`, is one value the reader
fills, and is last where it ends in `>` and nothing follows it on its
line: pasted unfilled, that `>` meets the newline, and the shell refuses
the line before it runs any of it. Text after that `>`, in the word as
in `<a>.txt` or after it, a `\` that continues the line included, can
make it a redirection that writes, and so can a comment: to an
interactive `zsh` a `#` is a word. A comment, a heredoc's body and a
quoted string hold no placeholder this reads, and `<<<` is a
here-string, not a heredoc.
"""

import itertools
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^ *(`{3,}|~{3,})(.*)$")
PLACEHOLDER = re.compile(r"<[A-Za-z][^<>\n\"'`]*>")
COPIES = ("CONTRIBUTING.md", "REVIEWING.md")
OWN = "## This repository in particular"
OPERATORS = ("&&", "||", ";;", ";", "&", "|", "(", ")", "<", ">")


class Shell:
    """A shell text read as tokens: words, operators and line ends."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.i = 0
        self.tokens: list[tuple[str, int, str]] = []
        self.heredocs: list[tuple[str, bool]] = []

    def line(self) -> int:
        return self.text.count("\n", 0, self.i)

    def read(self, closer: str = "") -> None:
        """Read tokens up to the end of the text, or to `closer`."""
        text = self.text
        while self.i < len(text):
            c = text[self.i]
            if c in " \t":
                self.i += 1
            elif text.startswith("\\\n", self.i):
                self.i += 2
            elif c == "\n":
                self.tokens.append(("end", self.line(), ""))
                self.i += 1
                self.bodies()
            elif c == "#":
                self.tokens.append(("comment", self.line(), "#"))
                end = text.find("\n", self.i)
                self.i = len(text) if end < 0 else end
            elif closer and c == closer:
                self.tokens.append(("op", self.line(), c))
                self.i += 1
                return
            elif text.startswith("<<<", self.i):
                self.tokens.append(("op", self.line(), "<<<"))
                self.i += 3
            elif text.startswith("<<", self.i):
                self.heredoc()
            elif text.startswith(("<(", ">("), self.i):
                self.tokens.append(("op", self.line(), text[self.i]))
                self.i += 2
                self.read(")")
            elif c in "<>" and not PLACEHOLDER.match(text, self.i):
                self.tokens.append(("op", self.line(), c))
                self.i += 1
            elif c in ";&|()":
                op = next(o for o in OPERATORS if text.startswith(o, self.i))
                self.tokens.append(("op", self.line(), op))
                self.i += len(op)
            else:
                self.word()

    def word(self) -> None:
        """Read one word, and record it with whether it holds a placeholder."""
        text = self.text
        start, line, bare = self.i, self.line(), False
        while self.i < len(text):
            c = text[self.i]
            if c in " \t\n;&|()":
                break
            if c == "<" or c == ">":
                found = PLACEHOLDER.match(text, self.i)
                if not found:
                    break
                bare = True
                self.i = found.end()
            elif c == "\\":
                self.i += 2
            elif c == "'":
                end = text.find("'", self.i + 1)
                self.i = len(text) if end < 0 else end + 1
            elif c == '"':
                self.double()
            elif text.startswith("$(", self.i):
                self.i += 2
                self.read(")")
            elif text.startswith("${", self.i):
                end = text.find("}", self.i)
                self.i = len(text) if end < 0 else end + 1
            elif c == "`":
                self.i += 1
                self.read("`")
            else:
                self.i += 1
        self.tokens.append(("bare" if bare else "word", line, text[start : self.i]))

    def double(self) -> None:
        """Read a double-quoted string, whose `$( )` is read as shell."""
        text = self.text
        self.i += 1
        while self.i < len(text):
            c = text[self.i]
            if c == "\\":
                self.i += 2
            elif c == '"':
                self.i += 1
                return
            elif text.startswith("$(", self.i):
                self.i += 2
                self.read(")")
            elif c == "`":
                self.i += 1
                self.read("`")
            else:
                self.i += 1

    def heredoc(self) -> None:
        """Read `<<` and its delimiter; the body is skipped at the line's end."""
        found = re.compile(r"<<(-?)[ \t]*(['\"]?)([^\s'\";&|()<>]+)\2").match(
            self.text, self.i
        )
        if not found:
            self.tokens.append(("op", self.line(), "<<"))
            self.i += 2
            return
        self.heredocs.append((found.group(3), bool(found.group(1))))
        self.tokens.append(("op", self.line(), "<<"))
        self.i = found.end()

    def bodies(self) -> None:
        """Skip the bodies of the heredocs the line just ended opened."""
        for delimiter, tabs in self.heredocs:
            while self.i < len(self.text):
                end = self.text.find("\n", self.i)
                end = len(self.text) if end < 0 else end
                body = self.text[self.i : end]
                self.i = end + 1
                if (body.lstrip("\t") if tabs else body) == delimiter:
                    break
        self.heredocs = []


def fences(text: str) -> list[tuple[int, str]]:
    """Each `shell` fence's first line, counted from 1, and its body."""
    found = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        opened = FENCE.match(lines[i])
        if not opened:
            i += 1
            continue
        mark, info = opened.group(1), opened.group(2).strip()
        end = i + 1
        while end < len(lines):
            closed = FENCE.match(lines[end])
            if closed and closed.group(1).startswith(mark) and not closed.group(2):
                break
            end += 1
        if info == "shell":
            found.append((i + 2, "\n".join(lines[i + 1 : end])))
        i = end + 1
    return found


def check(path: str, text: str) -> list[str]:
    """Each bare placeholder of the file's fences that is not last."""
    found = []
    if Path(path).name in COPIES:
        head = text.find(f"\n{OWN}\n")
        text = "\n" * text.count("\n", 0, head) + text[head:] if head >= 0 else ""
    for first, body in fences(text):
        shell = Shell(body)
        shell.read()
        tokens = shell.tokens + [("end", -1, "")]
        for (kind, line, value), after in itertools.pairwise(tokens):
            if kind == "bare" and (after[0] != "end" or not value.endswith(">")):
                found.append(f"{path}:{first + line}: {value}")
    return found


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__.split("\n\n")[1])
    found = []
    for path in sys.argv[1:]:
        found += check(path, Path(path).read_text(encoding="utf-8"))
    if found:
        print("\n".join(found))
    sys.exit(1 if found else 0)


if __name__ == "__main__":
    main()
