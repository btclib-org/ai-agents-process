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
that heading. Where either lacks that heading, spelt exactly so, it
prints `<file>: lacks the heading "## This repository in particular"`
and exits 1.

A placeholder is `<`, a letter, then anything but a newline, a double
quote, a backquote, `<` or `>`, then `>`. An apostrophe in it, as in
`<the session's scratchpad>`, belongs to the value the reader fills, so
this reads it as opening no quote. It is bare where no quote holds it,
and one inside a `$( )` or backquotes is bare again, as the shell reads
it. A word made of placeholders and the text between them, as
`<owner>/<repo>`, is one value the reader fills, and is last where it
ends in `>` and nothing follows it on its line: pasted unfilled, that
`>` meets the newline, and the shell refuses the line before it runs any
of it. Where its placeholders hold an odd number of apostrophes, the
last opens a quote instead, which holds the `>` and the newline: zsh
runs nothing until a later apostrophe closes the quote, and then reads
every line up to it as one. Text after a placeholder's `>`, in the word
as in `<a>.txt` or after it, a `\` that continues the line included, can
make it a redirection that writes, and so can a comment: to an
interactive `zsh` a `#` is a word, so a comment's line is read as any
other, its quotes included.

A heredoc's body, a quoted string, the text of `${ }` and an arithmetic
`$(( ))`, `(( ))` or `$[ ]` hold no placeholder this reads, but for one
inside a `$( )` or backquotes that is not in a heredoc's body or single
quotes. In arithmetic a double quote opens no string, as zsh reads it,
except inside a `${ }`. A `$((` or `((` whose first unmatched `)` is not
followed by another is a `$( (` or a `( (`, as zsh reads it. `<<<` is a
here-string, not a heredoc. A heredoc's delimiter is read with its
quotes taken off and the escapes of a `$'...'` decoded as zsh 5.9 on
macOS decodes them, so `<<\EOF` and `<<$'E\x4fF'` end at `EOF`, and
`<<-` takes the tabs off the start of each body line. A heredoc opened
inside a `$( )`, backquotes, a `<( )` or a `>( )` takes its body after a
line end inside them, and has none where they close first; one opened
before them waits for a line end after them, as zsh reads it. A fence
closes at a line of its own character, at least as long as its opening,
followed by nothing but spaces and tabs. An indented fence's body loses
up to the opening's indentation from each line, as CommonMark reads it.
"""

import itertools
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^( *)(`{3,}|~{3,})(.*)$")
PLACEHOLDER = re.compile(r"<[A-Za-z][^<>\n\"`]*>")
DELIMITER = re.compile(
    r"""<<(-?)[ \t]*((?:\$'(?:\\.|[^'\\])*'|\\.|'[^']*'|"(?:\\.|[^"\\])*"|"""
    r"""[^\s'"\\;&|()<>])+)"""
)
QUOTED = re.compile(r"""\$'((?:\\.|[^'\\])*)'|'([^']*)'|"((?:\\.|[^"\\])*)"|\\(.)""")
OCTAL = re.compile(rb"[0-7]{1,3}")
HEX = re.compile(rb"[ \t]*([-+]?)([0-9A-Fa-f]*)")
DIGITS = re.compile(rb"[0-9A-Fa-f]*")
NAMED = dict(zip(b"abeEfnrtv", b"\a\b\x1b\x1b\f\n\r\t\v", strict=True))
COPIES = ("CONTRIBUTING.md", "REVIEWING.md")
OWN = "## This repository in particular"
OPERATORS = ("&&", "||", ";;", ";", "&", "|", "(", ")", "<", ">")


def unquote(found: re.Match[str]) -> str:
    """A quoted part of a heredoc's delimiter, its quotes taken off."""
    ansi, single, double, escaped = found.groups()
    if ansi is not None:
        return decode(ansi).decode(errors="surrogateescape")
    if double is not None:
        return re.sub(r'\\([$`"\\\n])', r"\1", double)
    return escaped if single is None else single


def decode(text: str) -> bytes:
    """The text of a `$'...'`, as zsh 5.9 on macOS decodes it in UTF-8.

    `\\C-` and `\\M-`, their `-` optional, change the next byte that a
    `\\u` or `\\U` does not make. `\\x` reads the next two characters as
    a hex number, blanks and a sign included, and an octal escape up to
    three digits, each making one byte. `\\u` and `\\U` read up to four
    and eight hex digits. A character escaped that none of these nor
    `NAMED` holds, `c` among them, stands for itself.
    """
    data, out, i = text.encode(), bytearray(), 0
    control = meta = 0
    while i < len(data):
        c, i = data[i], i + 1
        if c == ord("\\") and i < len(data):
            c, i = data[i], i + 1
            if c in b"CM":
                i += data.startswith(b"-", i)
                if c == ord("C"):
                    control = 1
                else:
                    meta = 1 + control
                continue
            if c in b"uU":
                end = i + (4 if c == ord("u") else 8)
                found = DIGITS.match(data, i, end)
                assert found
                out += utf8(int(found.group() or b"0", 16))
                i = found.end()
                continue
            elif c in b"01234567":
                found = OCTAL.match(data, i - 1)
                assert found
                out.append(int(found.group(), 8) & 0xFF)
                i = found.end()
            elif c == ord("x"):
                found = HEX.match(data[i : i + 2])
                assert found
                sign, digits = found.groups()
                value = int(digits or b"0", 16)
                out.append((-value if sign == b"-" else value) & 0xFF)
                i += found.end()
            else:
                out.append(NAMED.get(c, c))
        else:
            out.append(c)
        if meta == 2:
            out[-1] |= 0x80
        if control:
            out[-1] = 0x7F if out[-1] == ord("?") else out[-1] & 0x9F
        if meta == 1:
            out[-1] |= 0x80
        control = meta = 0
    return bytes(out)


def utf8(value: int) -> bytes:
    """A `\\u` or `\\U` value as zsh encodes it, past U+10FFFF too."""
    if value < 0x80:
        return bytes([value])
    size = 2 + sum(value >= top for top in (0x800, 0x10000, 0x200000, 0x4000000))
    tail = [0x80 | (value >> 6 * k & 0x3F) for k in range(size - 2, -1, -1)]
    return bytes([(0xFC << 6 - size & 0xFC) | value >> 6 * (size - 1)] + tail)


class Shell:
    """A shell text read as tokens: words, operators and line ends."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.i = 0
        self.tokens: list[tuple[str, int, str]] = []
        self.heredocs: list[tuple[str, bool, int]] = []
        self.subshells: set[int] = set()

    def line(self) -> int:
        return self.text.count("\n", 0, self.i)

    def read(self, closer: str = "", scope: int | None = None) -> None:
        """Read tokens up to the end of the text, or to `closer`.

        A plain `( )` passes its caller's `scope`: its heredocs are the
        caller's, where those of a `$( )`, backquotes or a `<( )` are their
        own.
        """
        text = self.text
        start = self.i if scope is None else scope
        while self.i < len(text):
            c = text[self.i]
            if c in " \t":
                self.i += 1
            elif text.startswith("\\\n", self.i):
                self.i += 2
            elif c == "\n":
                self.tokens.append(("end", self.line(), ""))
                self.i += 1
                self.bodies(start)
            elif closer and c == closer:
                if scope is None:
                    self.heredocs = [h for h in self.heredocs if h[2] < start]
                self.tokens.append(("op", self.line(), c))
                self.i += 1
                return
            elif text.startswith("<<<", self.i):
                self.tokens.append(("op", self.line(), "<<<"))
                self.i += 3
            elif text.startswith("<<", self.i):
                self.heredoc()
            elif text.startswith("((", self.i) and self.arithmetic(2):
                pass
            elif text.startswith(("<(", ">("), self.i):
                self.tokens.append(("op", self.line(), text[self.i]))
                self.i += 2
                self.read(")")
            elif c in "<>" and not PLACEHOLDER.match(text, self.i):
                self.tokens.append(("op", self.line(), c))
                self.i += 1
            elif c == "(":
                self.tokens.append(("op", self.line(), c))
                self.i += 1
                self.read(")", start)
            elif c in ";&|()":
                op = next(o for o in OPERATORS if text.startswith(o, self.i))
                self.tokens.append(("op", self.line(), op))
                self.i += len(op)
            else:
                self.word(closer)

    def word(self, closer: str) -> None:
        """Read one word, and record it with whether it holds a placeholder."""
        text = self.text
        start, line, bare = self.i, self.line(), False
        while self.i < len(text):
            c = text[self.i]
            if c in " \t\n;&|()" or c == closer:
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
            elif not self.expansion():
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
            elif not self.expansion(quoted=True):
                self.i += 1

    def expansion(self, quoted: bool = False) -> bool:
        """Read a `$(( ))`, `$( )`, `${ }` or backquote that starts here."""
        text = self.text
        if text.startswith("$((", self.i) and self.arithmetic(3):
            pass
        elif text.startswith("$[", self.i):
            self.arithmetic(2, "]")
        elif text.startswith("$(", self.i):
            self.i += 2
            self.read(")")
        elif text.startswith("${", self.i):
            self.i += 2
            self.parameter(quoted)
        elif text.startswith("`", self.i):
            # backquotes end at the next backquote not escaped, and their
            # text is read on its own, as zsh reads it, so that a `(` it
            # leaves open ends with them
            start = end = self.i + 1
            while end < len(text) and text[end] != "`":
                end += 2 if text[end] == "\\" else 1
            self.i, self.text = start, text[:end]
            self.read("`")
            self.text = text
            self.heredocs = [h for h in self.heredocs if h[2] < start]
            self.tokens.append(("op", self.line(), "`"))
            self.i = min(end + 1, len(text))
        else:
            return False
        return True

    def parameter(self, quoted: bool) -> None:
        """Read the rest of a `${ }`, whose `$( )` is read as shell.

        Inside double quotes, an apostrophe in it opens no quote.
        """
        text = self.text
        while self.i < len(text):
            c = text[self.i]
            if c == "}":
                self.i += 1
                return
            if c == "\\":
                self.i += 2
            elif c == "'" and not quoted:
                end = text.find("'", self.i + 1)
                self.i = len(text) if end < 0 else end + 1
            elif c == '"':
                self.double()
            elif not self.expansion(quoted):
                self.i += 1

    def arithmetic(self, skip: int, closer: str = ")") -> bool:
        """Read a `$(( ))` or `(( ))` to its `))`, or a `$[ ]`, past `skip`.

        Where the first unmatched `)` is not followed by another, zsh reads
        a subshell: this then reads nothing, and returns False. It keeps
        the answer, so that a nested one is not read again at each depth.
        """
        text, start, kept = self.text, self.i, len(self.tokens)
        if start in self.subshells:
            return False
        opener, depth = "[" if closer == "]" else "(", 0
        self.i += skip
        while self.i < len(text):
            c = text[self.i]
            if c == closer and depth == 0:
                if closer == ")" and not text.startswith("))", self.i):
                    self.i = start
                    del self.tokens[kept:]
                    self.subshells.add(start)
                    return False
                self.i += 2 if closer == ")" else 1
                return True
            if c == opener:
                depth += 1
                self.i += 1
            elif c == closer:
                depth -= 1
                self.i += 1
            elif not self.expansion():
                self.i += 1
        return True

    def heredoc(self) -> None:
        """Read `<<` and its delimiter; the body is skipped at the line's end."""
        found = DELIMITER.match(self.text, self.i)
        if not found:
            self.tokens.append(("op", self.line(), "<<"))
            self.i += 2
            return
        # zsh compares bytes: the parts are joined as bytes, and a delimiter
        # that is not UTF-8 keeps its bytes as surrogates, which no line holds
        joined = QUOTED.sub(unquote, found.group(2)).encode(errors="surrogateescape")
        delimiter = joined.decode(errors="surrogateescape")
        self.heredocs.append((delimiter, bool(found.group(1)), self.i))
        self.tokens.append(("op", self.line(), "<<"))
        self.i = found.end()

    def bodies(self, start: int) -> None:
        """Skip the bodies of the heredocs opened since `start`."""
        for delimiter, tabs, at in self.heredocs:
            if at < start:
                continue
            while self.i < len(self.text):
                end = self.text.find("\n", self.i)
                end = len(self.text) if end < 0 else end
                body = self.text[self.i : end]
                self.i = end + 1
                if (body.lstrip("\t") if tabs else body) == delimiter:
                    break
        self.heredocs = [h for h in self.heredocs if h[2] < start]


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
        indent, mark = len(opened.group(1)), opened.group(2)
        end = i + 1
        while end < len(lines):
            closed = FENCE.match(lines[end])
            if (
                closed
                and closed.group(2).startswith(mark)
                and not closed.group(3).strip(" \t")
            ):
                break
            end += 1
        if opened.group(3).strip() == "shell":
            body = [
                line[min(indent, len(line) - len(line.lstrip(" "))) :]
                for line in lines[i + 1 : end]
            ]
            found.append((i + 2, "\n".join(body)))
        i = end + 1
    return found


def check(path: str, text: str) -> list[str]:
    """Each bare placeholder of the file's fences that is not last."""
    found = []
    if Path(path).name in COPIES:
        head = text.find(f"\n{OWN}\n")
        if head < 0:
            return [f'{path}: lacks the heading "{OWN}"']
        text = "\n" * text.count("\n", 0, head) + text[head:]
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
