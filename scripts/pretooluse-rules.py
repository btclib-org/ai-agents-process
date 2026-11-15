#!/usr/bin/env python3
"""Hook: refuse a Bash command that breaks a rule of the process.

Claude Code runs it before each Bash call (`PreToolUse`), with the call
as JSON on stdin. Where the command breaks a rule in `RULES`, it prints
the section of the process that holds the rule, and its file, on stderr
and exits 2, which refuses the call. Otherwise it prints nothing and
exits 0, and the call goes on to the usual permission flow.

The sections are the rule; this is a net under them. It splits the
command into words as the shell would, follows `sh -c`, `eval`, `$(…)`,
backticks, subshells and wrappers such as `env`, `timeout` and
`uv run`, and skips quoted text, comments, heredoc bodies and function
bodies, so a rule named in a commit message or an `echo` is not a
breach. It refuses only what the words show for certain. Where options
repeat, the last decides, as the program reads them. A word holding an
unexpanded `$` might be any word, so a command passes where such a word
could make it comply, and a spelling the script cannot read passes. So
does a help request to git, gh, uv, pytest or coderabbit, a version
request to git, uv or pytest, input it cannot parse, and text with a
quote, a substitution or a group it never closes. Of `PYTEST_ADDOPTS`
it reads only a literal value assigned as a prefix of the pytest
command itself: set any other way, the variable is not read.
"""

import json
import os
import re
import shlex
import sys

# The files of the process that hold the rules.
EVERY = "process/every-session.md"
COMMON = "process/btclib-common.md"
# For each rule: what breaks it, its section, and the file holding that.
RULES = {
    "cd": (
        "the command opens with `cd`",
        "*Never open a command with `cd`*, in *Shell, checkouts and prose*",
        EVERY,
    ),
    "xdist": (
        "pytest runs with `-n auto` or `-n logical`",
        "*The machine is shared*, in *Shell, checkouts and prose*",
        EVERY,
    ),
    "watch": (
        "a gh watch asks more often than every 120 seconds",
        "*The forge's quota is shared*, in *Shell, checkouts and prose*",
        EVERY,
    ),
    "datadir": (
        "a Bitcoin Core program runs without an explicit `-datadir=`",
        (
            "*A Bitcoin Core program runs on a data directory of the scratch"
            " directory*, in *Shell, checkouts and prose*"
        ),
        EVERY,
    ),
    "stash": (
        "`git stash` writes the shared `refs/stash`",
        (
            "*Never the primary checkout, never `git stash`, never a push to"
            " `main`*, in *Where you work*"
        ),
        COMMON,
    ),
    "fetch-head": (
        "`git worktree add` at `FETCH_HEAD`",
        (
            "*A worktree for a pull request is added at its `headRefOid`*,"
            " in *Where you work*"
        ),
        COMMON,
    ),
    "prune": (
        "`uv cache prune --force`",
        "*Look at the free disk*, in *Before starting*",
        COMMON,
    ),
    "force": (
        "`git push` forces without a lease",
        (
            "*A force-push with lease, to a branch the session works only*,"
            " in *Committing and rebasing*"
        ),
        COMMON,
    ),
    "sign": (
        "git turns commit signing off",
        "*Signed and signed off*, in *Committing and rebasing*",
        COMMON,
    ),
    "credits": (
        "CodeRabbit's CLI runs with `--use-credits`",
        "*Sourcery and CodeRabbit before a push*, in *Writing work*",
        COMMON,
    ),
}

# How deep `sh -c` and `eval` strings are followed.
DEPTH = 8
ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
KEYWORDS = {"{", "}", "!", "if", "then", "else", "elif", "do", "while", "until"}
ADDOPTS = "PYTEST_ADDOPTS"
# The words before a command that leave it the command the text opens with.
PREFIXES = KEYWORDS | {"command", "builtin"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh"}
# Options of a wrapper that take the next word as their value.
WRAPPER_VALUES = {
    "env": {"-u", "--unset", "-C", "--chdir", "-P", "-L", "-U"},
    "exec": {"-a"},
    "nice": {"-n"},
    "timeout": {"-k", "-s"},
    "gtimeout": {"-k", "-s"},
    "xargs": {"-E", "-I", "-J", "-L", "-n", "-P", "-R", "-S", "-s", "-a", "-d"},
    "sandbox-exec": {"-f", "-n", "-p", "-D"},
    "time": set(),
    "nohup": set(),
    "command": set(),
    "builtin": set(),
}
# The options of `uv run` and `uvx` that take the next word as their value.
UV_VALUES = {
    "--extra",
    "--no-extra",
    "--group",
    "--no-group",
    "--only-group",
    "--no-editable-package",
    "--env-file",
    "-w",
    "--with",
    "--with-editable",
    "--with-requirements",
    "--package",
    "--python-platform",
    "--index",
    "--default-index",
    "-i",
    "--index-url",
    "--extra-index-url",
    "-f",
    "--find-links",
    "--index-strategy",
    "--keyring-provider",
    "-P",
    "--upgrade-package",
    "--upgrade-group",
    "--resolution",
    "--prerelease",
    "--prerelease-package",
    "--fork-strategy",
    "--exclude-newer",
    "--exclude-newer-package",
    "--no-sources-package",
    "--reinstall-package",
    "--link-mode",
    "-C",
    "--config-setting",
    "--config-settings-package",
    "--no-build-isolation-package",
    "--no-build-package",
    "--no-binary-package",
    "--cache-dir",
    "--refresh-package",
    "-p",
    "--python",
    "--color",
    "--allow-insecure-host",
    "--directory",
    "--project",
    "--config-file",
    "--from",
    "-c",
    "--constraints",
    "-b",
    "--build-constraints",
    "--overrides",
    "--torch-backend",
}
GIT_VALUES = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env"}
# The git commands that take `--no-gpg-sign`.
GIT_SIGNING = {
    "am",
    "cherry-pick",
    "commit",
    "commit-tree",
    "merge",
    "pull",
    "rebase",
    "revert",
}
# The options of those commands that take the next word as their value.
COMMIT_VALUES = {
    "-m",
    "-F",
    "--message",
    "--file",
    "-C",
    "-c",
    "--reuse-message",
    "--reedit-message",
    "--fixup",
    "--squash",
    "-t",
    "--template",
    "--author",
    "--date",
    "--trailer",
    "--cleanup",
    "-X",
    "--strategy-option",
    "--onto",
}
# The options of `git config` that only read.
CONFIG_READS = {
    "get",
    "list",
    "--get",
    "--get-all",
    "--get-regexp",
    "--get-urlmatch",
    "--get-color",
    "--get-colorbool",
    "-l",
    "--list",
}
# The short options of pytest that take the next word as their value,
# `-n` aside, as its parser declares them.
PYTEST_VALUES = {"-W", "-c", "-k", "-m", "-o", "-p", "-r"}
# The options with which those commands write no commit.
NO_COMMIT = {"--abort", "--quit", "--show-current-patch", "--dry-run"}
WORKTREE_VALUES = {"-b", "-B", "--reason"}
PUSH_VALUES = {"--repo", "--receive-pack", "--exec", "-o", "--push-option"}
# The programs whose options include `-datadir`, as `src/init.cpp`,
# `src/bitcoin-cli.cpp` and `src/bitcoin-wallet.cpp` declare it, and the
# commands of the `bitcoin` wrapper that run one of them.
BITCOIN = {
    "bitcoind",
    "bitcoin-node",
    "bitcoin-qt",
    "bitcoin-gui",
    "bitcoin-cli",
    "bitcoin-wallet",
}
BITCOIN_COMMANDS = {"node", "gui", "rpc", "wallet"}
FALSE = {"false", "no", "off", ""}
WATCH_INTERVAL = 120
# The options of `gh run watch` and `gh pr checks` other than the interval
# that take a value, as their `--help` lists them.
GH_VALUES = {"-R", "--repo", "-q", "--jq", "--json", "-t", "--template"}


class TooDeep(Exception):
    """The text nests deeper than the lexer follows."""


class Malformed(Exception):
    """The text holds a quote, a substitution or a group it never closes."""


# A run of a word the shell only unquotes: characters that mean nothing
# to it, a `$` that opens nothing the lexer follows, and quotes holding
# nothing it expands. The same inside double quotes. QUOTES removes the
# quotes from such a run.
SIMPLE = re.compile(
    r"""(?:[^\\'"`$<>()#;&| \t\n{]+|\$(?![({'"])|'[^']*'|"[^"\\`$]*")+"""
)
# A word the lexer reads as itself.
PLAIN = re.compile(r"[^\\'\"`$<>()#;&| \t\n{]+")
QUOTES = re.compile(r"'([^']*)'|\"([^\"\\`$]*)\"")
PLAIN_QUOTED = re.compile(r"(?:[^\\\"`$]+|\$(?![({]))+")
EMPTY_PARENS = re.compile(r"\(\s*\)")
# How deep the lexer follows subshells, `$(…)` and backticks.
NESTING = 100


# A command as the lexer splits it: its words, and whether the text
# opens with it.
Lexed = tuple[list[str], bool]
# A command once its wrappers are removed: its words, and the variables
# its prefix assignments set for it alone.
Found = tuple[list[str], dict[str, str]]


class Lexer:
    """Split shell text into simple commands, each a list of words.

    Quotes are removed as the shell removes them. What the shell would
    expand (`$x`, `$(…)`, a glob) stays as written, so a word holding
    `$` is unknown to the rules. Commands inside `$(…)`, backticks,
    `<(…)` and a subshell are collected too, after the one around them.
    The body of a function definition is not: defining runs nothing.
    """

    def __init__(self, text: str) -> None:
        self.s = text
        self.i = 0
        self.depth = 0
        self.commands: list[Lexed] = []

    def run(self) -> list[Lexed]:
        self.parse(None)
        return self.commands

    def nested(self, closer: str) -> None:
        self.depth += 1
        if self.depth > NESTING:
            raise TooDeep
        self.parse(closer)
        self.depth -= 1

    def parse(self, closer: str | None) -> None:
        s = self.s
        words: list[str] = []
        word: list[str] | None = None
        drop_next = False
        heredoc_next: bool | None = None
        heredocs: list[tuple[str, bool]] = []
        first = closer is None

        def add(text: str) -> None:
            nonlocal word
            if word is None:
                word = []
            word.append(text)

        def end_word() -> None:
            nonlocal word, drop_next, heredoc_next
            if word is None:
                return
            text = "".join(word)
            if heredoc_next is not None:
                heredocs.append((text, heredoc_next))
                heredoc_next = None
            elif drop_next:
                drop_next = False
            else:
                words.append(text)
            word = None

        def end_command() -> None:
            nonlocal words, first
            end_word()
            if words:
                self.commands.append((words, first))
                first = False
            words = []

        while self.i < len(s):
            c = s[self.i]
            nxt = s[self.i + 1] if self.i + 1 < len(s) else ""
            simple = SIMPLE.match(s, self.i)
            if simple:
                add(QUOTES.sub(r"\1\2", simple.group()))
                self.i = simple.end()
            elif closer == "`" and c == "`":
                end_command()
                self.i += 1
                return
            elif c == "\\":
                if nxt == "\n":
                    self.i += 2
                    continue
                add(nxt)
                self.i += 2
            elif c == "'":
                # SIMPLE takes a closed quote
                raise Malformed
            elif c == "$" and nxt == "'":
                add(self.ansi_c())
            elif c == '"':
                add(self.double_quoted())
            elif c == "`":
                self.i += 1
                self.nested("`")
                add("$(…)")
            elif c == "$" and nxt == "(":
                add(self.dollar_paren())
            elif c == "$" and nxt == "{":
                add(self.braced())
            elif c in "<>" and nxt == "(" and word is None:
                self.i += 2
                self.nested(")")
                add("$(…)")
            elif c == "#" and word is None:
                end = s.find("\n", self.i)
                self.i = len(s) if end < 0 else end
            elif c in " \t":
                end_word()
                self.i += 1
            elif c == "\n":
                end_command()
                self.i += 1
                for delimiter, strip in heredocs:
                    self.skip_heredoc(delimiter, strip)
                heredocs = []
            elif c == "&" and nxt == ">":
                end_word()
                drop_next = True
                self.i += 3 if s.startswith("&>>", self.i) else 2
            elif c in ";&|":
                end_command()
                self.i += 2 if nxt in ";&|" else 1
            elif c in "<>":
                if word is not None and "".join(word).isdigit():
                    word = None
                end_word()
                if s.startswith("<<<", self.i):
                    drop_next = True
                    self.i += 3
                elif s.startswith("<<-", self.i):
                    heredoc_next = True
                    self.i += 3
                elif s.startswith("<<", self.i):
                    heredoc_next = False
                    self.i += 2
                else:
                    drop_next = True
                    self.i += 2 if nxt in ">&|" else 1
            elif (
                c == "("
                and (word is not None or words)
                and EMPTY_PARENS.match(s, self.i)
                and "=" not in "".join(word or words[-1:])
            ):
                # `name()` or `name ()`, then the body: a definition, which
                # runs nothing
                self.i = s.index(")", self.i) + 1
                self.skip_body()
                word = None
                words = []
            elif (
                c == "{" and word is None and len(words) == 2 and words[0] == "function"
            ):
                self.skip_body()
                words = []
            elif c == "(" and word is None and all(w in KEYWORDS for w in words):
                end_command()
                self.i += 1
                self.nested(")")
                first = False
            elif c == ")" and closer == ")":
                end_command()
                self.i += 1
                return
            elif c == ")":
                end_command()
                self.i += 1
            else:
                add(c)
                self.i += 1
        if closer is not None:
            raise Malformed
        end_command()

    def skip_body(self) -> None:
        """Skip a function's body, and the commands its substitutions hold."""
        collected = len(self.commands)
        self.skip_group()
        del self.commands[collected:]

    def skip_group(self) -> None:
        """Skip a `{…}` or `(…)` group, quotes honoured."""
        s = self.s
        while self.i < len(s) and s[self.i] in " \t\n":
            self.i += 1
        if self.i >= len(s) or s[self.i] not in "{(":
            return
        opener = s[self.i]
        closer = "}" if opener == "{" else ")"
        depth = 0
        while self.i < len(s):
            c = s[self.i]
            if c == "\\":
                self.i += 2
                continue
            if c == "'":
                end = s.find("'", self.i + 1)
                if end < 0:
                    raise Malformed
                self.i = end + 1
                continue
            if c == '"':
                self.double_quoted()
                continue
            if c == "#" and (self.i == 0 or s[self.i - 1] in " \t\n;&|"):
                # a comment, whose braces close nothing
                end = s.find("\n", self.i)
                self.i = len(s) if end < 0 else end
                continue
            self.i += 1
            if c == opener:
                depth += 1
            elif c == closer:
                depth -= 1
                if depth == 0:
                    return
        raise Malformed

    def ansi_c(self) -> str:
        s, out = self.s, []
        self.i += 2
        escapes = {"n": "\n", "t": "\t", "'": "'", "\\": "\\", '"': '"'}
        while self.i < len(s) and s[self.i] != "'":
            if s[self.i] == "\\" and self.i + 1 < len(s):
                out.append(escapes.get(s[self.i + 1], "\\" + s[self.i + 1]))
                self.i += 2
            else:
                out.append(s[self.i])
                self.i += 1
        if self.i >= len(s):
            raise Malformed
        self.i += 1
        return "".join(out)

    def double_quoted(self) -> str:
        s, out = self.s, []
        self.i += 1
        while self.i < len(s) and s[self.i] != '"':
            c = s[self.i]
            nxt = s[self.i + 1] if self.i + 1 < len(s) else ""
            plain = PLAIN_QUOTED.match(s, self.i)
            if plain:
                out.append(plain.group())
                self.i = plain.end()
            elif c == "\\" and nxt in '$`"\\\n':
                out.append("" if nxt == "\n" else nxt)
                self.i += 2
            elif c == "`":
                self.i += 1
                self.nested("`")
                out.append("$(…)")
            elif c == "$" and nxt == "(":
                out.append(self.dollar_paren())
            elif c == "$" and nxt == "{":
                out.append(self.braced())
            else:
                out.append(c)
                self.i += 1
        if self.i >= len(s):
            raise Malformed
        self.i += 1
        return "".join(out)

    def dollar_paren(self) -> str:
        if self.s.startswith("$((", self.i):
            return self.braced("(", ")")
        self.i += 2
        self.nested(")")
        return "$(…)"

    def braced(self, opener: str = "{", closer: str = "}") -> str:
        """Copy `${…}` or `$((…))` to its matching close, unexpanded."""
        s, start, depth = self.s, self.i, 0
        self.i += 1
        while self.i < len(s):
            c = s[self.i]
            self.i += 1
            if c == opener:
                depth += 1
            elif c == closer:
                depth -= 1
                if depth <= 0 and (closer == "}" or s[self.i - 2] == ")"):
                    return "$" + s[start + 1 : self.i]
        raise Malformed

    def skip_heredoc(self, delimiter: str, strip: bool) -> None:
        s = self.s
        while self.i < len(s):
            end = s.find("\n", self.i)
            end = len(s) if end < 0 else end
            line = s[self.i : end]
            self.i = end + 1
            if (line.lstrip("\t") if strip else line) == delimiter:
                return


def name(word: str) -> str:
    return os.path.basename(word)


def split_assignments(words: list[str], at: int = 0) -> tuple[dict[str, str], int]:
    """The assignments from `words[at]` on, and the index after them."""
    assigned: dict[str, str] = {}
    while at < len(words) and ASSIGNMENT.match(words[at]):
        key, _, value = words[at].partition("=")
        assigned[key] = value
        at += 1
    return assigned, at


def skip_options(words: list[str], at: int, values: set[str]) -> int:
    """The index after the options of the wrapper at `words[at]`."""
    i = at + 1
    while i < len(words) and words[i].startswith("-") and words[i] != "-":
        if words[i] == "--":
            return i + 1
        i += 2 if words[i] in values else 1
    return i


def unwrap(words: list[str], depth: int) -> list[Found]:
    """The commands `words` runs: itself once its wrappers are removed,
    or what its `sh -c` or `eval` string runs."""
    assigned: dict[str, str] = {}
    # an index into `words`, not a slice of it, keeps this linear
    at = 0
    # the index from which every word is PLAIN, once an `eval` asks
    plain_from: int | None = None
    while True:
        while at < len(words) and words[at] in KEYWORDS:
            at += 1
        more, at = split_assignments(words, at)
        assigned.update(more)
        while at < len(words) and words[at] in KEYWORDS:
            at += 1
        if at >= len(words):
            return []
        program = name(words[at])
        if program == "command" and lookup(words, at):
            return []
        if program in WRAPPER_VALUES:
            if wrapper_help(words, at, WRAPPER_VALUES[program]):
                return []
            if program == "env" and env_clears(words, at):
                assigned.pop(ADDOPTS, None)
            at = skip_options(words, at, WRAPPER_VALUES[program])
            if program in ("timeout", "gtimeout"):
                at += 1
        elif program == "uv" and words[at + 1 : at + 2] == ["run"]:
            at = skip_options(words, at + 1, UV_VALUES)
        elif program == "uv" and words[at + 1 : at + 3] == ["tool", "run"]:
            at = skip_options(words, at + 2, UV_VALUES)
        elif program == "uvx":
            at = skip_options(words, at, UV_VALUES)
        elif program in SHELLS:
            script = shell_script(words[at:])
            if script is None:
                return [(words[at:], assigned)]
            return commands(script, depth + 1)
        elif program == "eval":
            if plain_from is None:
                plain_from = len(words)
                while plain_from > 0 and PLAIN.fullmatch(words[plain_from - 1]):
                    plain_from -= 1
            if at + 1 < plain_from:
                return commands(" ".join(words[at + 1 :]), depth + 1)
            # words the shell would read again as they stand: `eval` is
            # one more wrapper, and the text is not lexed again
            at += 1
        else:
            return [(words[at:], assigned)]


def wrapper_help(words: list[str], at: int, values: set[str]) -> bool:
    """Whether the wrapper at `words[at]` is asked for its help or its
    version, and so runs nothing."""
    i = at + 1
    while i < len(words) and words[i].startswith("-") and words[i] not in ("-", "--"):
        if words[i] in ("--help", "--version"):
            return True
        i += 2 if words[i] in values else 1
    return False


def env_clears(words: list[str], at: int) -> bool:
    """Whether the `env` at `words[at]` removes `PYTEST_ADDOPTS` from the
    command it runs, or might: `-i`, or `-u` naming it or a `$` word."""
    i = at + 1
    while i < len(words) and words[i].startswith("-") and words[i] != "-":
        arg = words[i]
        if arg == "--":
            break
        if arg in ("-i", "--ignore-environment"):
            return True
        if arg in ("-u", "--unset"):
            value = words[i + 1] if i + 1 < len(words) else ""
        elif arg.startswith("--unset="):
            value = arg.partition("=")[2]
        elif arg.startswith("-u"):
            value = arg[2:]
        else:
            value = ""
        if value == ADDOPTS or "$" in value:
            return True
        i += 2 if arg in WRAPPER_VALUES["env"] else 1
    return False


def shell_script(words: list[str]) -> str | None:
    """The string a shell's `-c` runs, or None where it runs no `-c`, or
    only reads it, as `-n` and `-o noexec` have it, the last deciding."""
    i, c_flag, noexec = 1, False, False
    while i < len(words) and len(words[i]) > 1 and words[i][0] in "-+":
        word = words[i]
        if word in ("-o", "+o"):
            if words[i + 1 : i + 2] == ["noexec"]:
                noexec = word == "-o"
            i += 1
        elif word in ("--rcfile", "--init-file"):
            i += 1
        elif word[1] != "-":
            if word[0] == "-" and "c" in word:
                c_flag = True
            if "n" in word:
                noexec = word[0] == "-"
        i += 1
    return words[i] if c_flag and not noexec and i < len(words) else None


def commands(text: str, depth: int) -> list[Found]:
    if depth > DEPTH:
        return []
    found = []
    try:
        lexed = Lexer(text).run()
    except Malformed:
        # it passes, as text the outer lexer cannot read passes
        return []
    for words, _ in lexed:
        found.extend(unwrap(words, depth))
    return found


def opens_with_cd(lexed: list[Lexed]) -> bool:
    for words, opening in lexed:
        if opening:
            _, at = split_assignments(words)
            while at < len(words) and words[at] in PREFIXES:
                at += 1
            return words[at : at + 1] == ["cd"]
    return False


def lookup(words: list[str], at: int) -> bool:
    """Whether the `command` at `words[at]` only looks its argument up, as
    `-v` and `-V` do."""
    i = at + 1
    while i < len(words) and words[i].startswith("-") and words[i] != "--":
        if "v" in words[i] or "V" in words[i]:
            return True
        i += 1
    return False


def unknown(words: list[str]) -> bool:
    return any("$" in word for word in words)


def false(value: str) -> bool:
    if "$" in value:
        return False
    if value.lower() in FALSE:
        return True
    try:
        return int(value) == 0
    except ValueError:
        return False


def options(args: list[str]) -> list[str]:
    """The words before `--`, after which git reads no option."""
    return args[: args.index("--")] if "--" in args else args


def git_rules(argv: list[str]) -> list[str]:
    i, configs = 1, []
    while i < len(argv) and argv[i].startswith("-"):
        if argv[i] in ("-h", "--help", "--version"):
            return []
        if argv[i] in GIT_VALUES:
            if argv[i] == "-c" and i + 1 < len(argv):
                configs.append(argv[i + 1])
            i += 2
        else:
            i += 1
    if i >= len(argv) or "$" in argv[i]:
        return []
    rest = argv[i + 1 :]
    sub, args = argv[i], options(rest)
    # git reads the words after `--` as operands
    after = rest[len(args) + 1 :]
    if "-h" in args or "--help" in args:
        return []
    broken = []
    if sub in GIT_SIGNING and not no_commit(args) and signing_off(configs, args):
        broken.append("sign")
    if sub == "config" and git_config_unsigns(args):
        broken.append("sign")
    reads = (["list"], ["show"])
    if sub == "stash" and not unknown(args[:1]) and args[:1] not in reads:
        broken.append("stash")
    if sub == "push" and push_forces(args, after):
        broken.append("force")
    if (
        sub == "worktree"
        and args[:1] == ["add"]
        and worktree_fetch_head(args[1:], after)
    ):
        broken.append("fetch-head")
    return broken


def no_commit(args: list[str]) -> bool:
    """Whether an option with which the command writes no commit is given,
    the values of the options before it skipped."""
    i = 0
    while i < len(args):
        if args[i] in NO_COMMIT:
            return True
        i += 2 if args[i] in COMMIT_VALUES else 1
    return False


def signing_off(configs: list[str], args: list[str]) -> bool:
    """Whether the last word that decides signing turns it off.

    An option of the command overrides `-c commit.gpgsign`, and among
    each the last wins. A word holding `$` might be either."""
    config: bool | None = None
    for item in configs:
        key, eq, value = item.partition("=")
        if "$" in key:
            # it might be `commit.gpgsign=true`
            config = None
        elif key.lower() == "commit.gpgsign":
            config = None if "$" in value else bool(eq) and false(value)
    option: bool | None = None
    decided = False
    values = {j + 1 for j, a in enumerate(args) if a in COMMIT_VALUES}
    for j, arg in enumerate(args):
        if j in values:
            continue
        if arg == "--no-gpg-sign":
            option, decided = True, True
        elif arg.startswith("--gpg-sign") or short_flag(arg, "S"):
            option, decided = False, True
        elif "$" in arg:
            option, decided = None, True
    if decided:
        return option is True
    return config is True


def short_flag(arg: str, letter: str) -> bool:
    """Whether a bundle of short options holds `letter`, before any
    letter whose option takes the rest of the word as its value."""
    if not arg.startswith("-") or arg.startswith("--"):
        return False
    for c in arg[1:]:
        if c == letter:
            return True
        if c in "mFCctXo":
            return False
    return False


def git_config_unsigns(args: list[str]) -> bool:
    """Whether `git config` sets `commit.gpgsign` false, at any scope, or
    unsets it in the global file, which holds it true. An unset without
    `--global` removes it from the repository's or the worktree's file
    only, and the global value still holds."""
    if unknown(args) or any(a in CONFIG_READS for a in args):
        return False
    for i, arg in enumerate(args):
        if arg.lower() != "commit.gpgsign":
            continue
        if any(a in ("--unset", "--unset-all", "unset") for a in args):
            return "--global" in args
        rest = [a for a in args[i + 1 :] if not a.startswith("-")]
        return bool(rest) and false(rest[0])
    return False


def push_forces(args: list[str], after: list[str]) -> bool:
    """Whether `git push` forces a ref with no lease: `--force`, `-f`, or
    a `+` refspec, before or after `--`, without `--force-with-lease`. A
    word holding `$` after the last force might be `--no-force`, and
    anywhere before `--` the lease."""
    if "--dry-run" in args or any(short_flag(a, "n") for a in args):
        return False
    force = lease = plus = False
    last = -1
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in PUSH_VALUES:
            i += 2
            continue
        if arg == "--force" or short_flag(arg, "f"):
            force, last = True, i
        elif arg == "--no-force":
            force = False
        elif arg.startswith("--force-with-lease"):
            lease = True
        elif arg == "--no-force-with-lease":
            lease = False
        elif arg.startswith("+"):
            plus = True
        i += 1
    if force and not unknown(args[last + 1 :]):
        return True
    plus = plus or any(w.startswith("+") for w in after)
    return plus and not lease and not unknown(args)


def worktree_fetch_head(args: list[str], after: list[str]) -> bool:
    """Whether `git worktree add` checks out `FETCH_HEAD`: its second
    operand, after the path, the options and their values skipped, and
    every word after `--` an operand."""
    operands, i = [], 0
    while i < len(args):
        if args[i] in WORKTREE_VALUES:
            i += 2
            continue
        if not args[i].startswith("-"):
            operands.append(args[i])
        i += 1
    revision = (operands + after + ["", ""])[1]
    return bool(re.fullmatch(r"FETCH_HEAD([~^@].*)?", revision))


def pytest_args(argv: list[str]) -> list[str] | None:
    program = name(argv[0])
    if program in ("pytest", "py.test"):
        return argv[1:]
    if program == "coverage" and argv[1:2] == ["run"]:
        for i, arg in enumerate(argv):
            if arg == "-m":
                return argv[i + 2 :] if argv[i + 1 : i + 2] == ["pytest"] else None
        return None
    if not re.fullmatch(r"python[0-9.]*", program):
        return None
    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg == "-m":
            return argv[i + 2 :] if argv[i + 1 : i + 2] == ["pytest"] else None
        if arg in ("-X", "-W"):
            i += 2
        elif arg.startswith("-") and arg != "-c":
            i += 1
        else:
            return None
    return None


def xdist_last(args: list[str]) -> tuple[str | None, bool]:
    """The last `-n` value pytest reads in `args`, before `--` and later
    over earlier, `""` for a help or version request and None for no `-n`, and
    whether a word holding `$` follows it."""
    args = options(args)
    if any(a in ("-h", "--help", "-V", "--version") for a in args):
        return "", False
    last, end, i = None, 0, 0
    while i < len(args):
        arg = args[i]
        n = arg in ("-n", "--numprocesses")
        step = 2 if n or arg in PYTEST_VALUES else 1
        if n:
            last = args[i + 1] if i + 1 < len(args) else None
        elif arg.startswith("--numprocesses="):
            last = arg.partition("=")[2]
        elif arg.startswith("-n") and not arg.startswith("--"):
            # `-nauto`, or `-n=auto`, which pytest's argparse reads alike
            last = arg[2:].removeprefix("=")
        else:
            i += step
            continue
        i += step
        end = i
    return last, unknown(args[end:])


def xdist_auto(args: list[str], addopts: tuple[str | None, bool]) -> bool:
    """Whether pytest runs `-n auto` or `-n logical`: `addopts` is what
    `xdist_last` gives for `PYTEST_ADDOPTS`, which pytest reads first."""
    last, later = xdist_last(args)
    if last == "" or addopts[0] == "":
        return False
    if last is None:
        last, later = addopts[0], addopts[1] or unknown(options(args))
    return last in ("auto", "logical") and not later


def datadir_missing(argv: list[str]) -> bool:
    program, args = name(argv[0]), argv[1:]
    if program == "bitcoin":
        i = 0
        while i < len(args) and args[i].startswith("-"):
            if args[i] in ("-v", "--version", "-h", "--help"):
                return False
            i += 1
        if args[i : i + 1] == [] or args[i] not in BITCOIN_COMMANDS:
            return False
        args = args[i + 1 :]
    elif program not in BITCOIN:
        return False
    value = ""
    # The first word that is not an option is a command, and Bitcoin
    # Core reads the words after it as its arguments, not as options. A
    # word holding `$` before it might be `-datadir=`.
    for arg in args:
        if "$" in arg and not arg.startswith(("-datadir=", "--datadir=")):
            return False
        if not arg.startswith("-") or arg == "-":
            break
        key, eq, given = arg.partition("=")
        if key in ("-datadir", "--datadir"):
            value = given if eq else ""
    return value == ""


def watch_too_often(argv: list[str]) -> bool:
    # gh reads no option after `--`
    argv = options(argv)
    if name(argv[0]) != "gh" or "--help" in argv or "-h" in argv:
        return False
    if argv[1:3] == ["pr", "checks"]:
        watching = False
        for arg in argv[3:]:
            if arg == "--watch":
                watching = True
            elif arg.startswith("--watch="):
                watching = arg.partition("=")[2].lower() in ("true", "t", "1")
        if not watching:
            return False
    elif argv[1:3] != ["run", "watch"]:
        return False
    interval, at = None, 2
    for i, arg in enumerate(argv):
        if arg in ("-i", "--interval"):
            interval, at = (argv[i + 1] if i + 1 < len(argv) else ""), i + 1
        elif arg.startswith(("--interval=", "-i=")):
            interval, at = arg.partition("=")[2], i
        elif arg.startswith("-i") and not arg.startswith("--"):
            interval, at = arg[2:], i
    # a word holding `$` after the last interval might set another, but
    # not where it is the value of another option
    rest = argv[at + 1 :]
    later = [
        w
        for j, w in enumerate(rest)
        if not (j and rest[j - 1] in GH_VALUES)
        and not w.startswith(tuple(o + "=" for o in GH_VALUES if o[1] == "-"))
    ]
    if unknown(later):
        return False
    if interval is None:
        return True
    try:
        return int(interval) < WATCH_INTERVAL
    except ValueError:
        return False


def prune_forced(argv: list[str]) -> bool:
    if name(argv[0]) != "uv":
        return False
    if any(a in ("-h", "--help", "-V", "--version") for a in argv):
        return False
    words = [a for a in argv[1:] if not a.startswith("-")]
    return words[:2] == ["cache", "prune"] and "--force" in argv


def credits_used(argv: list[str]) -> bool:
    """Whether CodeRabbit's CLI runs with `--use-credits`, which no word
    turns off: a word holding `$` might ask for help instead."""
    if name(argv[0]) != "coderabbit":
        return False
    args = options(argv[1:])
    if "--help" in args or "-h" in args or unknown(args):
        return False
    return "--use-credits" in args


def addopts(value: str | None) -> tuple[str | None, bool]:
    """What `xdist_last` reads in a `PYTEST_ADDOPTS` set as a prefix of
    the pytest command, split with `shlex.split` as pytest splits it. A
    value holding an expansion, or one shlex cannot split, is not read,
    nor is the variable set any other way."""
    if value is None or "$" in value:
        return None, False
    try:
        return xdist_last(shlex.split(value))
    except ValueError:
        return None, False


def broken_rules(text: str) -> list[str]:
    """The rules `text` breaks, by their keys in `RULES`. Text nested
    deeper than the lexer follows breaks none it can tell."""
    try:
        lexed = Lexer(text).run()
        found = [c for words, _ in lexed for c in unwrap(words, 0)]
    except (TooDeep, Malformed):
        return []
    broken = ["cd"] if opens_with_cd(lexed) else []
    for argv, assigned in found:
        if name(argv[0]) == "git":
            broken.extend(git_rules(argv))
        args = pytest_args(argv)
        if args is not None and xdist_auto(args, addopts(assigned.get(ADDOPTS))):
            broken.append("xdist")
        if datadir_missing(argv):
            broken.append("datadir")
        if watch_too_often(argv):
            broken.append("watch")
        if prune_forced(argv):
            broken.append("prune")
        if credits_used(argv):
            broken.append("credits")
    return list(dict.fromkeys(broken))


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except (ValueError, RecursionError):
        # input it cannot parse, nested deeper than the interpreter's
        # recursion limit lets json read, passes
        return
    if not isinstance(event, dict) or event.get("tool_name") != "Bash":
        return
    tool_input = event.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    broken = broken_rules(command) if isinstance(command, str) else []
    if not broken:
        return
    lines = ["pretooluse-rules.py refused this command:"]
    lines += [f"- {RULES[r][2]}, {RULES[r][1]}: {RULES[r][0]}." for r in broken]
    lines.append(
        "Write it again as that section asks, as *Hooks* in *Clients*, in"
        f" {COMMON}, says."
    )
    print("\n".join(lines), file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
