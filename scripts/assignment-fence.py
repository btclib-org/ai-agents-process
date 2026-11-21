#!/usr/bin/env python3
r"""List each `shell` fence that sets a value the reader fills and also writes.

    python3 scripts/assignment-fence.py <file>...

Section 9 of the organization's standard, *A placeholder is bare, and
last*, is the rule: a value the reader sets goes in an assignment block
above the fence, and a line that writes gets a fence of its own. Pasted
into an interactive shell with a value left unfilled, the assignment
fails at the parse and the shell runs the next line on whatever value it
held. The script reads the `shell` fences of each Markdown file it is
given, and prints on stdout `<file>:<line>: <names> share a fence with a
write on line <line> (<what>)` for each fence that holds both, on the
line of its first assignment. `<what>` is the command that writes, as
`gh pr close`, or `>` for a redirection. It exits 1 where it prints one.
For paths that hold no newline, this counts the fences over the tree, as
the hook reads it:

    git ls-files -z '*.md' ':!CHANGELOG.md' |
      xargs -0 python3 scripts/assignment-fence.py | wc -l

In `CONTRIBUTING.md` and `REVIEWING.md`, whose text down to `## This
repository in particular` is the organization's copy and changes there
first, it reads only what follows that heading. Where either lacks that
heading, spelt exactly so, it prints `<file>: lacks the heading "## This
repository in particular"` on stderr, and exits 1.

An assignment is a command made only of `<name>=<value>` words, after
any keyword as `then`, one of them holding a bare placeholder, as
`n=<n>`, or a `set --` whose words hold one, as `set -- <the heads>`. A
placeholder is `<`, a letter, then anything but a newline, a quote, a
backquote, `;`, `&`, `|`, `(`, `)`, `$`, `<` or `>`, then `>`, and it is
bare where no quote holds it. An apostrophe in it, as in `<the session's
scratchpad>`, belongs to the value the reader fills. One that holds a
space or a tab is read as redirections where its `>` follows a space or
a tab and then only spaces, tabs and digits, or where a letter, a digit
or `_` follows its `>`: `sort <in >out`, `tr a b <in 2>err` and `cat <a
b>c` write.

**A line writes unless every command on it is one the script reads as
reading only, and it redirects no output but to `/dev/null` or to a
descriptor.** The default is the safe side: a command the script does
not know, an option it does not know before a subcommand, or a script
it does not name, lists the fence. What reads only is:

- a command `READS` names, by the last part of its path, as `grep`,
  `jq` or `gate_wait`, and `command -v`;
- `sed` without `-i`, `-I` or `--in-place`, alone or in a cluster as
  `-Ei`; `perl` without `-i`, alone or in a cluster as `-pi` or `-0pi`;
  `sort` without `-o`; `uniq` with at most one operand; `kill -0` and
  `kill -l`; `sysctl` without `-w` or a `name=value`;
- `find` without `-delete`, `-fprint`, `-fprint0`, `-fprintf` or
  `-fls`, and whose `-exec` and `-ok` clauses read only;
- a script `SCRIPT_READS` names, run by itself, by a shell, by `.` or
  `source`, or by `python`, and `python` or `python3` with `-c` or `-`;
- `git`, past the global options `GIT_OPTIONS` and `VALUED` name, with a
  subcommand `GIT_READS` names, in the forms `git_writes` reads:
  `--output` makes `archive`, `diff`, `log` and `show` write; `branch`,
  `config`, `tag` and `worktree` read only in their listing and getting
  forms. `hash-object -w`, `merge-tree` and `write-tree` are read as
  reading: they add only objects, which no ref names, so no later
  command finds them by a name;
- `gh`, past `-R`, with a verb `GH_READS` names, as `gh pr view`, and
  `gh search`; `gh api` with no method but `GET`, and no field but with
  `-X GET`, and on `graphql` no `mutation`;
- `uv`, past the global options `UV_OPTIONS` and `VALUED` name, with
  `version`, `help`, or `dir`, `find` or `list` after `python`, `cache`
  or `tool`; `pre-commit` with a subcommand `PRE_COMMIT_READS` names;
- a call of a function the fence defines, whose body is read where it
  is defined.

The command is read past what only runs the next one: `env`, its `-S`
string read as a command line, `timeout`, `xargs`, `nice`, `nohup`,
`command`, `exec`, `time`, `sandbox-exec`, `uv run` and `uvx`, with the
options `VALUED` names, and a word that is a parameter alone, as `"$@"`
or `$t`. A `$( )` or a backquote, inside a `${ }` too, a `<( )` or `>(
)`, the program of `sh`, `bash`, `zsh` or `dash` with `-c`, alone or in
a cluster as `-ec`, and the programs of `eval` and `trap` are read as
commands, and a write in one is reported on the line of its own command.
An arithmetic `(( ))` or `$(( ))`, a `[[ ]]`'s `<` and `>`, a `case`'s
patterns, a heredoc's body and a comment hold no redirection the script
reads, and of them it reads a command only in a `$( )` or a backquote
of a `[[ ]]`.

Out of reach, so read as reading only: the program of an interpreter
the script does not read, as `awk`, `perl -e`, `sed`'s `w`, `python -c`
or what `python -` reads on stdin, which can write; what a script
`SCRIPT_READS` names does; `uv run` without `--no-project`, which locks
and syncs the project; a `$( )` or a backquote inside an arithmetic, a
`case` pattern or an unquoted heredoc's body, which the shell runs; and
a shell this reading does not parse as the shell does, such as a quote
a `${ }` opens across lines.
"""

import re
import sys
from pathlib import Path

FENCE = re.compile(r"^ *(`{3,}|~{3,})(.*)$")
PLACEHOLDER = re.compile(r"<[A-Za-z][^<>\n\"'`;&|()$]*(?:'[^<>\n\"`;&|()$]*)*>")
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
ALONE = re.compile(r'"?\$[^/]*"?')
COPIES = ("CONTRIBUTING.md", "REVIEWING.md")
OWN = "## This repository in particular"

READS = {
    ":", "[", "[[", "test", "for", "select", "case", "true", "false", "echo", "printf",
    "read", "set", "shift", "unset", "export", "local", "return", "exit",
    "break", "continue", "cd", "wait", "sleep", "type", "awk", "basename",
    "cat", "cmp", "comm", "cut", "date", "df", "diff", "dirname", "du",
    "expr", "getconf", "grep", "head", "id", "jq", "log", "ls",
    "memory_pressure", "pgrep", "ps", "pwd", "realpath", "seq", "shasum",
    "stat", "tail", "tr", "uname", "uptime", "wc", "yes",
    # functions the tree defines in one fence and calls in another
    "gate_wait", "gated_tree",
}  # fmt: skip
SCRIPT_READS = {
    "suite-reads.py", "port-check.py", "pointer-files.py",
    "placeholder-last.py", "assignment-fence.py", "gate-lock.sh",
}  # fmt: skip
GIT_OPTIONS = {"--no-pager", "-P", "--no-optional-locks", "--bare"}
GIT_READS = {
    "archive", "blame", "cat-file", "check-attr", "check-ignore",
    "describe", "diff", "for-each-ref", "grep", "hash-object", "log",
    "ls-files", "ls-remote", "ls-tree", "merge-base", "merge-tree",
    "rev-list", "rev-parse", "show", "show-ref", "status", "version",
    "write-tree", "branch", "config", "tag", "worktree",
}  # fmt: skip
# the options that put `git branch` in list mode, where its operands are patterns
BRANCH_LISTS = {
    "--list", "-l", "--contains", "--no-contains", "--merged", "--no-merged",
    "--points-at",
}  # fmt: skip
BRANCH_READS = BRANCH_LISTS | {
    "--show-current", "-a", "--all", "-r", "--remotes", "-v", "-vv",
    "--verbose", "--format", "--sort",
}  # fmt: skip
CONFIG_READS = {
    "--get", "--get-all", "--get-regexp", "--list", "-l", "--show-scope",
    "--show-origin", "--no-includes", "--global", "--local", "--system",
    "--name-only", "--type", "--default", "-z", "--null",
}  # fmt: skip
GH_READS = {"checks", "diff", "list", "status", "view", "watch"}
UV_OPTIONS = {
    "-q", "--quiet", "-v", "--verbose", "--no-cache", "--offline",
    "--no-config", "--no-progress", "--native-tls", "--isolated",
}  # fmt: skip
PRE_COMMIT_READS = {"validate-config", "validate-manifest", "help", "sample-config"}
RESERVED = {"!", "{", "}", "if", "then", "elif", "else", "fi", "while"}
RESERVED |= {"until", "do", "done", "esac"}
WRAPPERS = {"nohup", "exec", "time", "command"}
# the options that take the next word as their value
VALUED = {
    "env": {"-C", "-u", "-P"},
    "timeout": {"-k", "-s", "--kill-after", "--signal"},
    "xargs": {"-I", "-n", "-P", "-L", "-d", "-E", "-s"},
    "sandbox-exec": {"-f", "-p", "-n", "-D"},
    "nice": {"-n"},
    "git": {"-C", "-c", "--git-dir", "--work-tree", "--namespace"},
    "gh": {"-R", "--repo"},
    "uv": {"--directory", "--project", "--cache-dir", "--config-file"}
    | {"--color", "--python", "-p"},
    "uv run": {"--python", "-p", "--with", "--with-requirements", "--project"}
    | {"--directory", "--only-group", "--group", "--extra", "--package"}
    | {"--env-file", "--index"},
    "uvx": {"--from", "--with", "--python", "-p", "--exclude-newer", "--index"},
}
# the options of `uv run` and `uvx` that take no value
FLAGS = {
    "--no-project", "--isolated", "--no-config", "--locked", "--frozen",
    "--no-sync", "--all-groups", "--all-extras", "--no-dev", "-q",
    "--quiet", "--offline", "--no-cache",
}  # fmt: skip
SHELLS = {"sh", "bash", "zsh", "dash"}


def placeholder(text: str, i: int) -> re.Match[str] | None:
    """The placeholder at `i`, but the redirections that look like one."""
    found = PLACEHOLDER.match(text, i)
    if found is None or not re.search(r"[ \t]", found.group()):
        return found
    after = text[found.end() : found.end() + 1]
    if re.search(r"[ \t][ \t0-9]*>$", found.group()) or re.match(r"\w", after):
        return None
    return found


class Word:
    """One shell word: its text, the same with its quotes taken off, its line."""

    def __init__(self, raw: str, plain: str, bare: bool, line: int) -> None:
        self.raw, self.plain, self.bare, self.line = raw, plain, bare, line


Command = tuple[list[Word], list[tuple[str, int]]]


class Shell:
    """A shell text read as simple commands: words, and the files they write."""

    def __init__(self, text: str, first: int) -> None:
        self.text, self.i, self.first = text, 0, first
        self.commands: list[Command] = []
        self.nested: list[tuple[str, int]] = []
        self.functions: set[str] = set()
        self.heredocs: list[tuple[str, bool]] = []
        self.words: list[Word] = []
        self.redirs: list[tuple[str, int]] = []
        self.cases = 0
        self.pattern = False

    def line(self) -> int:
        return self.first + self.text.count("\n", 0, self.i)

    def head(self) -> list[str]:
        """The words of the command read so far, past its keywords."""
        plain = [w.plain for w in self.words]
        while plain and plain[0] in RESERVED:
            plain = plain[1:]
        return plain

    def testing(self) -> bool:
        """Whether a `[[` is open in the command read so far."""
        plain = [w.plain for w in self.words]
        opened = max((k for k, p in enumerate(plain) if p == "[["), default=-1)
        return opened > max((k for k, p in enumerate(plain) if p == "]]"), default=-1)

    def end(self) -> None:
        if self.words or self.redirs:
            self.commands.append((self.words, self.redirs))
        self.words, self.redirs = [], []

    def read(self) -> "Shell":
        text = self.text
        while self.i < len(text):
            c = text[self.i]
            if c in " \t":
                self.i += 1
            elif text.startswith("\\\n", self.i):
                self.i += 2
            elif c == "\n":
                self.end()
                self.i += 1
                self.bodies()
            elif c == "#":
                end = text.find("\n", self.i)
                self.i = len(text) if end < 0 else end
            elif self.pattern and re.match(r"esac\b", text[self.i : self.i + 5]):
                self.pattern = False
            elif self.pattern:
                self.patterns()
            elif text.startswith("((", self.i) and not self.head():
                self.i += 2
                self.arithmetic()
            elif c in "<>" and self.testing():
                self.i += 1
            elif text.startswith(("<(", ">("), self.i):
                self.i += 2
                self.nest(")")
            elif text.startswith("<<<", self.i):
                self.i += 3
                self.word()
            elif text.startswith("<<", self.i):
                self.heredoc()
            elif text.startswith("&>", self.i) or (
                c in "<>" and not placeholder(text, self.i)
            ):
                self.redirect()
            elif text.startswith("()", self.i) and len(self.words) == 1:
                self.functions.add(self.words[0].plain)
                self.words = []
                self.i += 2
            elif c in ";&|()":
                self.end()
                if text.startswith((";;", ";&"), self.i) and self.cases:
                    self.pattern = True
                    self.i += 3 if text.startswith(";;&", self.i) else 2
                else:
                    self.i += 2 if text.startswith(("&&", "||"), self.i) else 1
            else:
                word = self.word()
                if word is not None:
                    self.words.append(word)
                head = self.head()
                if head[:1] == ["case"] and head[2:] == ["in"]:
                    self.end()
                    self.cases += 1
                    self.pattern = True
                elif head == ["esac"] and self.cases:
                    self.cases -= 1
        self.end()
        return self

    def patterns(self) -> None:
        """Skip a `case`'s patterns up to their `)`, quotes included."""
        text = self.text
        while self.i < len(text) and text[self.i] != ")":
            if text[self.i] in "'\"":
                end = text.find(text[self.i], self.i + 1)
                self.i = len(text) if end < 0 else end + 1
            else:
                self.i += 1
        self.i += 1
        self.pattern = False

    def arithmetic(self) -> None:
        """Skip an arithmetic expression up to its `))`."""
        depth = 0
        while self.i < len(self.text):
            if self.text.startswith("))", self.i) and depth == 0:
                self.i += 2
                return
            depth += (self.text[self.i] == "(") - (self.text[self.i] == ")")
            self.i += 1

    def redirect(self) -> None:
        """Read a redirection, and keep the file it writes, if any."""
        text, line = self.text, self.line()
        found = re.compile(r"&>>?|>>|>\||<>|>&|>|<&|<").match(text, self.i)
        assert found
        self.i = found.end()
        target = self.word()
        name = target.plain if target else ""
        if found.group() in ("<", "<&") or name == "/dev/null":
            return
        if found.group() == ">&" and re.fullmatch(r"[0-9]+-?|-", name):
            return
        self.redirs.append((name, line))

    def word(self) -> Word | None:
        """Read one word; a `$( )` or backquote in it is kept to be read too."""
        text = self.text
        while self.i < len(text) and text[self.i] in " \t":
            self.i += 1
        start, line, plain, bare = self.i, self.line(), "", False
        while self.i < len(text):
            c = text[self.i]
            if c in " \t\n;&|()":
                break
            if c in "<>":
                found = placeholder(text, self.i)
                if not found:
                    break
                bare = True
                plain += found.group()
                self.i = found.end()
            elif c == "\\":
                plain += text[self.i + 1 : self.i + 2]
                self.i += 2
            elif c == "'":
                end = text.find("'", self.i + 1)
                end = len(text) if end < 0 else end
                plain += text[self.i + 1 : end]
                self.i = end + 1
            elif c == '"':
                plain += self.double()
            elif c in "$`":
                begin = self.i
                if not self.expansion():
                    self.i += 1
                plain += text[begin : self.i]
            else:
                plain += c
                self.i += 1
        raw = text[start : self.i]
        if raw.isdigit() and text.startswith((">", "<"), self.i):
            return None
        return Word(raw, plain, bare, line) if raw else None

    def expansion(self) -> bool:
        """Read a `$(( ))`, `$( )`, `${ }` or backquote that starts here."""
        text = self.text
        if text.startswith("$((", self.i):
            self.i += 3
            self.arithmetic()
        elif text.startswith("$(", self.i) or text.startswith("`", self.i):
            closer = "`" if text[self.i] == "`" else ")"
            self.i += 1 if closer == "`" else 2
            self.nest(closer)
        elif text.startswith("${", self.i):
            self.parameter()
        else:
            return False
        return True

    def double(self) -> str:
        """Read a double-quoted string; a `$( )` in it is kept to be read too."""
        text = self.text
        self.i += 1
        begin = self.i
        while self.i < len(text):
            c = text[self.i]
            if c == "\\":
                self.i += 2
            elif c == '"':
                self.i += 1
                return text[begin : self.i - 1]
            elif not (c in "$`" and self.expansion()):
                self.i += 1
        return text[begin:]

    def parameter(self) -> None:
        """Read a `${ }`; its `$( )` or backquote is kept to be read too."""
        text = self.text
        self.i += 2
        while self.i < len(text) and text[self.i] != "}":
            c = text[self.i]
            if c == "\\":
                self.i += 2
            elif c == "'":
                end = text.find("'", self.i + 1)
                self.i = len(text) if end < 0 else end + 1
            elif c == '"':
                self.double()
            elif not (c in "$`" and self.expansion()):
                self.i += 1
        self.i += 1

    def nest(self, closer: str) -> None:
        """Keep the text up to `closer`, at its own depth, to be read as commands."""
        text, line, depth, begin = self.text, self.line(), 0, self.i
        while self.i < len(text):
            c = text[self.i]
            if c == "\\":
                self.i += 2
                continue
            if c == "'" and closer == ")":
                end = text.find("'", self.i + 1)
                self.i = len(text) if end < 0 else end + 1
                continue
            if c == closer and depth == 0:
                break
            if closer == ")":
                depth += (c == "(") - (c == ")")
            self.i += 1
        self.nested.append((text[begin : self.i], line))
        self.i += 1

    def heredoc(self) -> None:
        """Read `<<` and its delimiter; the body is skipped at the line's end."""
        found = re.compile(r"<<(-?)[ \t]*(['\"]?)([^\s'\";&|()<>]+)\2").match(
            self.text, self.i
        )
        if not found:
            self.i += 2
            return
        self.heredocs.append((found.group(3), bool(found.group(1))))
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


def options(words: list[str], i: int, valued: set[str]) -> int:
    """The index of the first word from `i` that is not an option."""
    while i < len(words) and words[i].startswith("-") and words[i] not in ("-", "--"):
        i += 2 if words[i] in valued else 1
    return i + (i < len(words) and words[i] == "--")


def known(words: list[str], i: int, valued: set[str], flags: set[str]) -> int:
    """As `options`, but -1 where an option is in neither set."""
    while i < len(words) and words[i].startswith("-") and words[i] not in ("-", "--"):
        name = words[i].split("=", 1)[0]
        if name in valued:
            i += 1 if "=" in words[i] else 2
        elif name in flags:
            i += 1
        else:
            return -1
    return i + (i < len(words) and words[i] == "--")


def cluster(arg: str, flag: str, valued: str) -> bool:
    """Whether a word of short options holds one of `flag` before one in `valued`."""
    if not arg.startswith("-") or arg.startswith("--"):
        return False
    for c in arg[1:]:
        if c in flag:
            return True
        if c in valued:
            return False
    return False


def perl_inplace(arg: str) -> bool:
    """Whether a word of `perl`'s switches holds `-i`, as `-pi` or `-0x0Api`."""
    return cluster(re.sub(r"0x[0-9A-Fa-f]*", "0", arg), "i", "eEFMmIdDx")


def shell_operand(args: list[str]) -> int:
    """Where a shell's first operand is, negated past 0 where `-c` makes it a program.

    `-c` may stand in a cluster, as `-ec` or `-lc`, and `-o` takes a value,
    as in `-euo pipefail -c`.
    """
    program, i = False, 0
    while i < len(args) and args[i][:1] in "-+" and args[i] not in ("-", "--"):
        if re.fullmatch(r"-[A-Za-z]*c[A-Za-z]*", args[i]):
            program = True
        if re.fullmatch(r"[-+][A-Za-z]*[oO]", args[i]):
            i += 1
        i += 1
    i += i < len(args) and args[i] == "--"
    return -(i + 1) if program and i < len(args) else i


def git_writes(args: list[str]) -> str:
    """What writes in `git` with these words, or an empty string."""
    i = known(args, 0, VALUED["git"], GIT_OPTIONS)
    if i < 0 or i >= len(args):
        return "git" if i < 0 else ""
    sub, rest = args[i], args[i + 1 :]
    flags = {a.split("=")[0] for a in rest if a.startswith("-")}
    others = [a for a in rest if not a.startswith("-")]
    if sub not in GIT_READS:
        return f"git {sub}"
    if sub == "archive":
        reads = not flags & {"-o", "--output"}
    elif sub in ("diff", "log", "show"):
        reads = "--output" not in flags
    elif sub == "branch":
        reads = flags <= BRANCH_READS and (not others or bool(flags & BRANCH_LISTS))
    elif sub == "config":
        reads = flags <= CONFIG_READS and (
            len(others) <= 1 or bool(flags & {"--get", "--get-all", "--get-regexp"})
        )
    elif sub == "tag":
        reads = not others or bool(flags & {"-l", "--list", "-v", "--verify"})
    elif sub == "worktree":
        reads = others[:1] == ["list"]
    else:
        reads = True
    return "" if reads else f"git {sub}"


def gh_writes(args: list[str]) -> str:
    """What writes in `gh` with these words, or an empty string."""
    args = args[options(args, 0, VALUED["gh"]) :]
    if not args or args[0] == "search":
        return ""
    if args[0] != "api":
        return "" if args[1:2] and args[1] in GH_READS else " ".join(["gh", *args[:2]])
    method, fields = "", False
    for flag, value in zip(args, [*args[1:], ""], strict=True):
        if flag in ("-X", "--method"):
            method = value.upper()
        elif flag.startswith("--method="):
            method = flag.split("=", 1)[1].upper()
        elif flag.startswith("-X") and len(flag) > 2:
            method = flag[2:].upper()
        elif flag.split("=", 1)[0] in ("-f", "-F", "--field", "--raw-field", "--input"):
            fields = True
    if "graphql" in args:
        return "gh api" if any("mutation" in a for a in args) else ""
    return "gh api" if method not in ("", "GET") or (fields and not method) else ""


def reads(name: str, args: list[str]) -> bool:
    """Whether a command with no rule of its own reads only."""
    operands = [a for a in args if not a.startswith("-")]
    if name == "sed":
        return not any(
            a.startswith("--in-place") or cluster(a, "iI", "efl") for a in args
        )
    if name == "perl":
        return not any(perl_inplace(a) for a in args)
    if name == "sort":
        return not any(
            a.startswith("--output") or cluster(a, "o", "ktST") for a in args
        )
    if name == "uniq":
        return len(operands) <= 1
    if name == "kill":
        return args[:1] in (["-0"], ["-l"])  # a test, and a list of signals
    if name == "sysctl":
        return "-w" not in args and not any("=" in a for a in operands)
    if name in ("python", "python3"):
        at = options(args, 0, {"-W", "-X"})
        script = args[at].rsplit("/", 1)[-1] if at < len(args) else ""
        return args[at - 1 : at] == ["-c"] or script == "-" or script in SCRIPT_READS
    return name in READS or name in SCRIPT_READS


def split_string(words: list[Word], i: int) -> Word | None:
    """The string of `env -S`, from its options at `i`, as one word, or None."""
    while i < len(words) and words[i].plain.startswith("-"):
        arg = words[i].plain
        if arg in ("-S", "--split-string"):
            return words[i + 1] if i + 1 < len(words) else None
        for lead in ("-S", "--split-string="):
            if arg.startswith(lead):
                return Word(arg, arg[len(lead) :], False, words[i].line)
        i += 2 if arg in VALUED["env"] else 1
    return None


def writes(words: list[Word], functions: set[str]) -> str:
    """What writes in a simple command's words, or an empty string."""
    plain = [w.plain for w in words]
    i = 0
    while i < len(plain):
        if plain[i] in RESERVED or NAME.match(words[i].raw):
            i += 1
        elif plain[i] == "function":
            functions.add(plain[i + 1] if i + 1 < len(plain) else "")
            i += 2
        else:
            break
    while i < len(plain):
        name = plain[i]
        if ALONE.fullmatch(words[i].raw):
            i += 1
        elif name == "env":
            program = split_string(words, i + 1)
            if program is not None:
                inner = scan(program.plain, program.line)
                return inner[0][1] if inner else ""
            i = options(plain, i + 1, VALUED["env"])
            while i < len(plain) and NAME.match(words[i].raw):
                i += 1
        elif name in ("timeout", "xargs", "sandbox-exec", "nice"):
            i = options(plain, i + 1, VALUED[name]) + (name == "timeout")
        elif name == "command" and plain[i + 1 : i + 2] in (["-v"], ["-V"]):
            return ""
        elif name in WRAPPERS:
            i = options(plain, i + 1, set())
        elif name == "uv":
            sub = known(plain, i + 1, VALUED["uv"], UV_OPTIONS)
            if sub < 0 or plain[sub : sub + 1] != ["run"]:
                break
            i = known(plain, sub + 1, VALUED["uv run"], FLAGS)
            if i < 0:
                return "uv run"
        elif name == "uvx":
            i = known(plain, i + 1, VALUED["uvx"], FLAGS)
            if i < 0:
                return "uvx"
        else:
            break
    if i >= len(plain):
        return ""
    name, args = plain[i].rsplit("/", 1)[-1], plain[i + 1 :]
    if name in SHELLS:
        at = shell_operand(args)
        if at < 0:
            program = words[i - at]
            inner = scan(program.plain, program.line)
            return inner[0][1] if inner else ""
        if at < len(args):
            name, args = args[at].rsplit("/", 1)[-1], args[at + 1 :]
    if name in (".", "source"):
        name, args = (args[0].rsplit("/", 1)[-1], args[1:]) if args else ("", [])
    if name in ("eval", "trap"):
        line = " ".join(args if name == "eval" else args[:1])
        inner = scan(line, words[i].line)
        return inner[0][1] if inner else ""
    if name in functions:
        return ""
    if name == "find":
        prints = {"-delete", "-fprint", "-fprint0", "-fprintf", "-fls"}
        for at, arg in enumerate(args):
            if arg in ("-exec", "-execdir", "-ok", "-okdir"):
                end = next(
                    (e for e in range(at + 1, len(args)) if args[e] in (";", "+")),
                    len(args),
                )
                inner_what = writes(words[i + 2 + at : i + 1 + end], functions)
                if inner_what:
                    return inner_what
        return next((f"find {a}" for a in args if a in prints), "")
    if name == "git":
        return git_writes(args)
    if name == "gh":
        return gh_writes(args)
    if name == "uv":
        sub = known(args, 0, VALUED["uv"], UV_OPTIONS)
        if sub < 0:
            return "uv"
        first, then = (args[sub:] + ["", ""])[:2]
        if first in ("version", "help") or (
            first in ("python", "cache", "tool") and then in ("dir", "find", "list")
        ):
            return ""
        return f"uv {first}".strip()
    if name == "pre-commit":
        return (
            ""
            if args[:1] and args[0] in PRE_COMMIT_READS
            else "pre-commit " + (args[0] if args else "")
        )
    return "" if reads(name, args) else name


def scan(text: str, first: int = 0) -> list[tuple[int, str]]:
    """Each line of the text, counted from `first`, that writes, and what writes."""
    shell = Shell(text, first).read()
    found = []
    for words, redirs in shell.commands:
        found += [(line, ">") for _, line in redirs]
        what = writes(words, shell.functions) if words else ""
        if what:
            found.append((words[0].line, what))
    for nested, line in shell.nested:
        found += scan(nested, line)
    return sorted(found)


def assignments(text: str) -> list[tuple[int, str]]:
    """Each assignment the reader fills in the text: its line, and what it sets."""
    found = []
    for words, redirs in Shell(text, 0).read().commands:
        while words and words[0].plain in RESERVED:
            words = words[1:]
        if redirs or not words:
            continue
        if [w.plain for w in words[:2]] == ["set", "--"]:
            if any(w.bare for w in words[2:]):
                found.append((words[0].line, "set --"))
        elif all(NAME.match(w.raw) for w in words) and any(w.bare for w in words):
            found.append((words[0].line, words[0].raw.split("=", 1)[0]))
    return found


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
            if (
                closed
                and closed.group(1).startswith(mark)
                and not closed.group(2).strip()
            ):
                break
            end += 1
        if info == "shell":
            found.append((i + 2, "\n".join(lines[i + 1 : end])))
        i = end + 1
    return found


def check(path: str, text: str) -> list[str] | None:
    """Each fence of the file that sets a value the reader fills, and writes.

    None where the file is a copy of the organization's that lacks its own part.
    """
    found = []
    if Path(path).name in COPIES:
        head = text.find(f"\n{OWN}\n")
        if head < 0:
            return None
        text = "\n" * text.count("\n", 0, head) + text[head:]
    for first, body in fences(text):
        set_ = assignments(body)
        written = scan(body)
        if set_ and written:
            names = ", ".join(dict.fromkeys(name for _, name in set_))
            line, what = written[0]
            found.append(
                f"{path}:{first + set_[0][0]}: {names} share a fence with a "
                f"write on line {first + line} ({what})"
            )
    return found


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__.split("\n\n")[1])
    failed = False
    for path in sys.argv[1:]:
        found = check(path, Path(path).read_text(encoding="utf-8"))
        if found is None:
            print(f'{path}: lacks the heading "{OWN}"', file=sys.stderr)
            failed = True
        elif found:
            print("\n".join(found))
            failed = True
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
