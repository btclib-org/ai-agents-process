#!/usr/bin/env python3
"""List each pointer to another file's section that does not name it.

    python3 scripts/pointer-files.py [<dir>]

`process/every-role.md`'s opening is the rule. `<dir>` is a git
checkout, by default the one holding this script. The script reads the
Markdown files `git ls-files` lists there but `CHANGELOG.md`, prints
`<file>:<line>: *<pointer>*: in <files>` for each pointer that does not
name its file, and exits 1 where it prints one. In `CONTRIBUTING.md`
and `REVIEWING.md`, whose text down to `## This repository in
particular` is the organization's copy and changes there first, it
reads the sections of the whole file and the pointers below that
heading.

A section is a heading, or a bold run (`**...**`) that opens a
paragraph, a list item or a sentence, its closing `.`, `,`, `:` or `;`
dropped. A pointer is an italic run (`*...*`) whose text is a section's
name, or, at three words or more, the start of one up to the end of a
word: *Debris goes when its work ends* is the start of a bold run that
goes on. A heading matches before a bold run, and a whole name before a
start; one or two words match no start, since a term set in italics, as
*The human*, would. Text in italics that names no section, as one
renamed or one of the organization's standard, is not read.

A pointer to a section of its own file needs no file. Any other names
its file where it follows a possessive, as `` `writing.md`'s ``, or
where its sentence names a file holding the section: by its path or its
name, as `process/writing.md` or `writing.md`; a skill's `SKILL.md` by
the skill, as `/btclib-pr`; a file of `agents/` as the `` `writer` ``
agent, or all of them as `agents/`. A possessive that names a file of
this tree prints `<file>:<line>: *<pointer>*: not in <name>` where that
file neither holds the section nor sends it on, in a table row of the
section in italics and a file, as `process/btclib-common.md` does. One
that names no file of this tree, as a file of a record's day, is left as
it is. A pointer after `the standard's` or `section <n>` is the
standard's, which is not in this tree.

Fenced code, inline code and HTML comments hold neither sections nor
pointers. A sentence ends at `.`, `?` or `!` before white space, at a
blank line, and where a list item starts, so `e.g.` ends one early.
"""

import re
import subprocess
import sys
from pathlib import Path

SKIPPED = re.compile(r"^CHANGELOG\.md$")
COPIES = ("CONTRIBUTING.md", "REVIEWING.md")
OWN = "\n## This repository in particular\n"
REDIRECT = re.compile(r"^\| \*(.+?)\* \| `([^`]+)` \|$", re.MULTILINE)
FENCE = re.compile(r"^ *(`{3,}|~{3,})")
HEADING = re.compile(r"^#{1,6} +(.*?)(?: +#+)? *$", re.MULTILINE)
PARAGRAPH = r"(?:(?!\n[ \t]*\n)[\s\S])"
CODE = re.compile(r"(`+)(?!`)(?:(?!\n[ \t]*\n).)*?(?<!`)\1(?!`)", re.DOTALL)
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
BOLD = re.compile(rf"(?<!\*)\*\*(?![*\s])({PARAGRAPH}+?)(?<![*\s])\*\*(?!\*)")
ITALIC = re.compile(
    r"(?<![*\w\\])\*(?![*\s])((?:(?!\n[ \t]*\n)[^*])+?)(?<![*\s\\])\*(?![*\w])"
)
ITEM = r"(?:\A|\n)[ \t]*(?:[-+*]|\d+[.)])[ \t]+(?:\[[ xX]\][ \t]+)?"
LEAD = re.compile(rf"(?:\A[ \t\n]*|\n[ \t]*\n[ \t]*|{ITEM}|[.?!:][ \t\n]+)\Z")
END = re.compile(rf"[.?!][ \t\n]+|\n[ \t]*\n|{ITEM}")
POSSESSIVE = re.compile(r"(?:`([^`\n]+)`|(/[a-z-]+))['’]s\s*\Z")
EXTERNAL = re.compile(r"(?:standard['’]s|[Ss]ection \d+(?:['’]s)?,?)\s*\Z")


def ws(text: str) -> str:
    """Collapse white space, as Markdown renders it."""
    return " ".join(text.split())


def masked(text: str) -> str:
    """The text, its fences, inline code and comments blanked with NULs.

    A newline stays, so that offsets and line numbers stay the text's.
    """

    def blank(found: re.Match[str]) -> str:
        return re.sub(r"[^\n]", "\0", found.group(0))

    lines = text.split("\n")
    mark = ""
    for i, line in enumerate(lines):
        opened = FENCE.match(line)
        if mark:
            if opened and opened.group(1).startswith(mark):
                mark = ""
        elif opened:
            mark = opened.group(1)
        else:
            continue
        lines[i] = "\0" * len(line)
    return CODE.sub(blank, COMMENT.sub(blank, "\n".join(lines)))


def sections(text: str) -> tuple[set[str], set[str]]:
    """A file's headings, and its bold runs that lead."""
    plain = masked(text)
    headings = {ws(text[m.start(1) : m.end(1)]) for m in HEADING.finditer(plain)}
    bold = {
        ws(text[m.start(1) : m.end(1)]).rstrip(".,:;")
        for m in BOLD.finditer(plain)
        if LEAD.search(plain[max(0, m.start() - 200) : m.start()])
    }
    return headings, bold


def rank(held: tuple[set[str], set[str]], pointer: str) -> int | None:
    """0 a heading of that name, 1 a bold run, 2 and 3 their starts."""
    for i, names in enumerate(held):
        if pointer in names:
            return i
    if len(pointer.split()) < 3:
        return None
    for i, names in enumerate(held):
        for name in names:
            if name.startswith(pointer) and name[len(pointer)] in " ,.:;(":
                return 2 + i
    return None


def mentions(path: str) -> list[str]:
    """The words that name a file."""
    p = Path(path)
    if p.parts[0] == "skills" and p.name == "SKILL.md":
        return [path, f"/{p.parent.name}"]
    if p.parts[0] == "agents":
        return [path, p.name, f"`{p.stem}` agent", "`agents/`"]
    return [path, p.name]


def bare(files: dict[str, str]) -> list[str]:
    """Each pointer to another file's section that does not name it."""
    held = {path: sections(text) for path, text in files.items()}
    redirects = {path: dict(REDIRECT.findall(text)) for path, text in files.items()}
    found = []
    for path, text in sorted(files.items()):
        start = 0
        if path in COPIES:
            start = text.find(OWN)
            if start < 0:
                continue
        plain = masked(text)
        for m in ITALIC.finditer(plain, start):
            pointer = ws(text[m.start(1) : m.end(1)])
            ranks = {}
            for other, there in held.items():
                if (r := rank(there, pointer)) is not None:
                    ranks[other] = r
            if not ranks or path in ranks:
                continue
            before = text[max(0, m.start() - 80) : m.start()]
            if EXTERNAL.search(before):
                continue
            line = text.count("\n", 0, m.start()) + 1
            if owner := POSSESSIVE.search(before):
                named = owner.group(1) or owner.group(2)
                files_named = [o for o in files if named in mentions(o)]
                if not files_named or any(
                    o in ranks or pointer in redirects[o] for o in files_named
                ):
                    continue
                found.append(f"{path}:{line}: *{pointer}*: not in {named}")
                continue
            best = min(ranks.values())
            targets = sorted(o for o, r in ranks.items() if r == best)
            left = max((e.end() for e in END.finditer(plain, 0, m.start())), default=0)
            right = END.search(plain, m.end())
            sentence = text[left : right.start() if right else len(text)]
            words = [w for t in targets for w in mentions(t)]
            if any(
                re.search(rf"(?<![\w.-]){re.escape(w)}(?![\w-])", sentence)
                for w in words
            ):
                continue
            found.append(f"{path}:{line}: *{pointer}*: in {', '.join(targets)}")
    return found


def main() -> None:
    if len(sys.argv) > 2:
        sys.exit(__doc__.split("\n\n")[1])
    root = Path(sys.argv[1]) if len(sys.argv) == 2 else Path(__file__).parent.parent
    listed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--", "*.md"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    files = {
        path: (root / path).read_text(encoding="utf-8")
        for path in listed.split("\0")
        if path and not SKIPPED.match(path)
    }
    found = bare(files)
    if found:
        print("\n".join(found))
    sys.exit(1 if found else 0)


if __name__ == "__main__":
    main()
