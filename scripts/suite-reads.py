#!/usr/bin/env python3
"""Print each place where a tree's pytest suite may read a changed file.

    scripts/suite-reads.py <worktree> <base>
    scripts/suite-reads.py <worktree> --paths <changed path>...

The first form reads the changed paths from `git diff --no-renames
<base>...HEAD`, so a rename gives both its names. Each line printed is
`<file>:<line>: <reason>`. Nothing printed, and exit 0, means no test
reads a file of the diff; any other exit means one may. Where it is not
sure, it prints a line: a needless local suite costs less than a red CI.

It reads every tracked Python file of the worktree, outside comments and
docstrings, the files under `testpaths`, and the lines of
`pyproject.toml`, `pytest.ini`, `setup.cfg` and `tox.ini` that name a
doctest option. A line is printed for:

- a changed path the suite imports or that configures it: a Python file,
  one of those settings files, `uv.lock`, or a path under `testpaths`;
- a string that names a changed path, whole or by its last parts, or a
  glob holding `*.` or `[`, as `"*.md"` or `"[g]uide.md"`, that matches
  one; in a `conftest.py`, also the suffix of one, such as `".md"`;
- the name of a changed file in a file under `testpaths` that is not
  Python, as a fixture or a shell script;
- a doctest option that names or globs a changed path, on its own line,
  and the value of a `--doctest-glob` on a later line;
- a walk or a glob that may list a changed path: a walk of a directory
  not built from `Path(__file__)`, a glob whose pattern is not a literal,
  and a literal pattern that matches a changed path below its directory,
  or below any directory where the scan cannot place it; a pattern
  holding `..`; and a glob given an option other than `recursive`; a
  `[...]` stands for any one character;
- a call that runs a command, unless each of its simple commands has a
  literal git or Python program, `sys.executable` among them, and words
  that name no changed path, for git a subcommand of `GIT_INERT`, and
  for Python no word that is Python code in which this scan prints a
  line. A shell string is split into simple commands at
  `SHELL_SEPARATORS`, and past the target of an output redirection; one
  holding a newline, `$(`, a backtick, an input redirection or another
  operator is not split, and prints a line. The words of
  `create_subprocess_exec` are all its arguments;
- a git command given as an argument to any other call, unless each of
  its simple commands is git with a subcommand so named;
- the event loop's `subprocess_shell` and `subprocess_exec`, on any
  object;
- a member of `glob`, `os`, `subprocess`, `asyncio`, `shutil` or
  `importlib.resources` taken other than by a call, as when it is bound
  to a name, unless `INERT` or the rules above it name the member as one
  that reads no file's content, lists no directory and runs no command;
  and any attribute `glob`, `iglob`, `rglob`, `iterdir`, `listdir`,
  `scandir` or `walk`, so taken;
- one of those modules taken other than through its members, imported
  with `*`, or imported by `import_module` or `__import__` by its name;
- a use of a name the scan reads through, an import from those modules
  or a module-level assignment, that the file binds more than once, in
  any scope;
- a Python file that does not parse.

A call through a name an import binds, `as` aliases among them, is read
as a call of what the name is bound to; a bare `walk`, `glob` and the
like that the file binds otherwise, as a function of its own, is not a
walk, since an uncalled read it is bound to prints its own line. The
strings `exec`, `eval` and
`compile` are given are read as Python code, as above.

Not found:

- a path that no string of the tree's Python names, as above, and no
  file under `testpaths` names: one built from pieces, or read from a
  data file outside `testpaths`;
- a read made by code outside the tree, as a library a test calls, or
  by code `exec`, `eval` or `compile` runs from a string that is not a
  literal;
- a read through a module that `import_module` or `__import__` imports
  by a name that is not a literal, or by a keyword, or through an alias
  of either;
- code given to `compile` by a keyword, or to an alias of `exec`, `eval`
  or `compile`;
- a file a glob or a walk reaches through a symbolic link, since the
  scan places a directory where its path names it.

CI's run of the suite on the pull request still makes the read.
"""

import ast
import posixpath
import re
import shlex
import subprocess
import sys
import tomllib
from collections.abc import Callable
from pathlib import Path, PurePosixPath

SETTINGS = ("pyproject.toml", "pytest.ini", "setup.cfg", "tox.ini")
IMPORTED = (".py", ".pyi", ".pyx", ".pth")
WALKS = {"listdir", "scandir", "iterdir", "glob", "iglob", "rglob", "walk"}
READ_MODULES = ("glob", "os", "subprocess", "asyncio", "shutil", "importlib.resources")
# Every member of a read module reads or lists files or runs a command,
# except an UPPER_CASE constant, an exception class, asyncio outside its
# subprocess API, and these, none of which reads a file's content or
# runs a command, nor lists a directory but to remove it:
INERT = {
    "os": {
        # path strings, and os.path's tests of a path (but SIZED)
        *("path", "fspath", "fsencode", "fsdecode"),
        # the environment
        *("environ", "environb", "getenv", "getenvb", "putenv", "unsetenv"),
        # the separators and the other lowercase constants
        *("sep", "altsep", "extsep", "pathsep", "curdir", "pardir", "defpath"),
        *("linesep", "devnull", "name"),
        # the process's own state
        *("getcwd", "getcwdb", "getpid", "getppid", "cpu_count"),
    },
    # a program's path on PATH; and removing a tree, which lists its
    # directories only to remove them, the same whatever its files hold
    "shutil": {"which", "rmtree"},
    # string work on a pattern
    "glob": {"escape", "translate", "has_magic"},
    # the result of a run, as a type
    "subprocess": {"CompletedProcess"},
}
# os.path's answers that a file's content changes
SIZED = {"getsize", "getmtime", "getatime", "getctime"}
# the calls that list a directory, globs aside
DIRECTORY_READS = {
    ("os", "listdir"),
    ("os", "scandir"),
    ("os", "walk"),
    ("os", "fwalk"),
    ("shutil", "copytree"),
    ("shutil", "make_archive"),
    ("importlib.resources", "contents"),
}
# git subcommands that read no file of the tree; `config` is not one, since
# its options and includes can name any file
GIT_INERT = {"rev-parse", "version", "var", "symbolic-ref"}
# the glob options the scan models: `**` is always read as recursive
GLOB_OPTIONS = {"recursive"}
# the event loop's subprocess API, on any object
LOOP_RUNS = {"subprocess_shell", "subprocess_exec"}
# the shell's command separators, and its redirections of output
SHELL_SEPARATORS = {"&&", "||", ";", "|", "&", "|&"}
SHELL_OUTPUT = {">", ">>", ">&", "&>", ">|"}
# git options that take the next word as their value
GIT_VALUED = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env"}
PYTHON = re.compile(r"python[0-9.]*")


def tails(path: str) -> list[str]:
    """A path and each of its shorter endings: `a/b.md`, `b.md`."""
    parts = PurePosixPath(path).parts
    return ["/".join(parts[i:]) for i in range(len(parts))]


def glob_regex(pattern: str) -> re.Pattern[str]:
    """The regular expression of a path glob, `**/` matching no directory too."""
    out = ""
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif pattern[i] == "?":
            out, i = out + "[^/]", i + 1
        elif pattern[i] == "[" and (end := class_end(pattern, i)) is not None:
            out, i = out + ".", end + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out)


def class_end(pattern: str, start: int) -> int | None:
    """The index of the `]` closing the class a `[` opens, as `fnmatch` reads it."""
    end = start + 1
    if pattern[end : end + 1] == "!":
        end += 1
    if pattern[end : end + 1] == "]":
        end += 1
    end = pattern.find("]", end)
    return None if end == -1 else end


def is_glob(text: str) -> bool:
    """Say whether a string reads as a path glob, as `*.md` or `[g]uide.md`."""
    return (
        re.search(r"[*?[]", text) is not None
        and re.fullmatch(r"[\w./*?!\[\]-]+", text) is not None
    )


def plain(text: str) -> str:
    """A path string without its leading `./`, `../` or `/`."""
    return re.sub(r"^((\.\.?)?/)+", "", text).rstrip("/")


def names(text: str, path: str) -> bool:
    """Say whether a string names a path, or is a `*.` or `[` glob matching it."""
    if plain(text) in tails(path):
        return True
    if not is_glob(text):
        return False
    regex = glob_regex(plain(text))
    kind = "*." in text or "[" in text
    return kind and any(regex.fullmatch(t) for t in tails(path))


def words(text: str) -> list[str]:
    """The path-like words of a string, as those of a shell command."""
    return re.findall(r"[\w./*-]+", text)


def runs_commands(module: str, name: str) -> bool:
    """Say whether a member of a runner module runs a command."""
    if module == "subprocess":
        return name[:1].islower() or name == "Popen"
    if module == "os":
        return name in ("system", "popen") or name.startswith(
            ("exec", "spawn", "posix_spawn")
        )
    last = name.rpartition(".")[2]
    return module == "asyncio" and last.startswith("create_subprocess")


def split(name: str) -> tuple[str, str] | None:
    """A dotted name as one of the read modules and its member, or None."""
    for module in READ_MODULES:
        if name == module or name.startswith(f"{module}."):
            return module, name[len(module) + 1 :]
    return None


def tracked(name: str) -> bool:
    """Say whether a dotted name is in a read module or leads to one."""
    return split(name) is not None or any(
        m.startswith(f"{name}.") for m in READ_MODULES
    )


def reads(module: str, member: str) -> bool:
    """Say whether a member of a read module may read or list files, or run."""
    head, _, rest = member.partition(".")
    error = head[:1].isupper() and head.endswith(("Error", "Exception", "Expired"))
    if head.isupper() or error:
        return False
    if module == "asyncio":
        return head == "subprocess" or head.startswith("create_subprocess")
    if module == "os" and head == "path":
        return rest.split(".")[0] in SIZED
    return head not in INERT.get(module, set())


def git_reads(words: list[str | None]) -> bool:
    """Say whether a git command, as its words, may read or list files.

    A word the scan cannot read is None.
    """
    i = 1
    while i < len(words) and words[i] is not None and str(words[i]).startswith("-"):
        i += 2 if words[i] in GIT_VALUED else 1
    return i >= len(words) or words[i] not in GIT_INERT


def simple_commands(text: str) -> list[list[str]] | None:
    """The simple commands of a shell string, or None where it cannot split it.

    It splits on the separators of `SHELL_SEPARATORS` and drops the target
    of an output redirection. A newline, `$(`, a backtick, an input
    redirection or any other shell operator is not split.
    """
    if "\n" in text or "$(" in text or "`" in text:
        return None
    lexer = shlex.shlex(text, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:
        return None
    commands: list[list[str]] = [[]]
    skip = False
    for token in tokens:
        if skip:
            skip = False
        elif token in SHELL_SEPARATORS:
            commands.append([])
        elif token in SHELL_OUTPUT:
            skip = True
        elif token and set(token) <= set("<>&|;()"):
            return None
        else:
            commands[-1].append(token)
    return [command for command in commands if command] or None


def binding_values(tree: ast.Module) -> dict[str, set[object]]:
    """What each name of a file is bound to, at each place, in any scope.

    An import gives the name it binds; any other binding is its own value.
    """
    values: dict[str, set[object]] = {}
    for node in ast.walk(tree):
        found: list[tuple[str, object]] = []
        if isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Load):
            found = [(node.id, id(node))]
        elif isinstance(node, ast.arg):
            found = [(node.arg, id(node))]
        elif isinstance(
            node,
            ast.FunctionDef
            | ast.AsyncFunctionDef
            | ast.ClassDef
            | ast.TypeVar
            | ast.ParamSpec
            | ast.TypeVarTuple,
        ):
            found = [(node.name, id(node))]
        elif isinstance(node, ast.ExceptHandler | ast.MatchAs | ast.MatchStar):
            found = [(node.name, id(node))] if node.name else []
        elif isinstance(node, ast.MatchMapping) and node.rest:
            found = [(node.rest, id(node))]
        elif isinstance(node, ast.Import):
            for alias in node.names:
                first = alias.name.split(".")[0]
                target = alias.name if alias.asname else first
                found.append((alias.asname or first, target))
        elif isinstance(node, ast.ImportFrom):
            origin = "." * node.level + (node.module or "")
            for alias in node.names:
                if alias.name != "*":
                    found.append((alias.asname or alias.name, f"{origin}.{alias.name}"))
        for name, value in found:
            values.setdefault(name, set()).add(value)
    return values


def bindings(tree: ast.Module) -> tuple[dict[str, str], list[int]]:
    """The dotted name each imported name is bound to, and the lines of `*` imports."""
    bound: dict[str, str] = {}
    stars: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                target = alias.name if alias.asname else alias.name.split(".")[0]
                if tracked(target):
                    bound[alias.asname or target] = target
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            for alias in node.names:
                if alias.name == "*":
                    if split(node.module) is not None:
                        stars.append(node.lineno)
                elif tracked(f"{node.module}.{alias.name}"):
                    bound[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return bound, stars


class Scan:
    """The walks, commands and strings of one Python file, read against the diff."""

    def __init__(self, file: str, tree: ast.Module, changed: list[str]) -> None:
        """Bind the module-level names a directory or a pattern may come from."""
        self.file = PurePosixPath(file)
        self.changed = changed
        self.bound = {
            target.id: node.value
            for node in tree.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        }
        self.imported, self.stars = bindings(tree)
        # each use of these prints a line, so what they resolve to is moot
        values = binding_values(tree)
        self.local = set(values)
        twice = {name for name, seen in values.items() if len(seen) > 1}
        self.ambiguous = twice & (set(self.bound) | set(self.imported))

    def qualify(self, node: ast.expr) -> str | None:
        """The dotted name, through imports, of a name or an attribute."""
        if isinstance(node, ast.Name):
            return self.imported.get(node.id)
        if isinstance(node, ast.Attribute):
            base = self.qualify(node.value)
            return None if base is None else f"{base}.{node.attr}"
        return None

    def member(self, node: ast.expr) -> tuple[str, str] | None:
        """The read module and member a name or an attribute is, or None."""
        name = self.qualify(node)
        return None if name is None else split(name)

    def literal(self, node: ast.expr | None, depth: int = 0) -> str | None:
        """The string an expression is, through module-level names."""
        if isinstance(node, ast.Name) and depth < 20:
            return self.literal(self.bound.get(node.id), depth + 1)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    def directory(self, node: ast.expr | None, depth: int = 0) -> str | None:
        """The directory, from the root, an expression on `Path(__file__)` names."""
        found = self._directory(node, depth)
        if found is None:
            return None
        normal = posixpath.normpath(found)
        return None if normal.startswith("..") else normal

    def _directory(self, node: ast.expr | None, depth: int) -> str | None:
        if node is None or depth > 20:
            return None
        if isinstance(node, ast.Name):
            return self._directory(self.bound.get(node.id), depth + 1)
        if isinstance(node, ast.Call):
            func = node.func
            if (
                isinstance(func, ast.Name)
                and func.id == "Path"
                and len(node.args) == 1
                and getattr(node.args[0], "id", None) == "__file__"
            ):
                return str(self.file)
            if isinstance(func, ast.Attribute) and func.attr in ("resolve", "absolute"):
                return self._directory(func.value, depth + 1)
            return None
        if isinstance(node, ast.Attribute) and node.attr == "parent":
            inner = self._directory(node.value, depth + 1)
            return None if inner is None else posixpath.join(inner, "..")
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute):
            index = node.slice
            if node.value.attr != "parents" or not isinstance(index, ast.Constant):
                return None
            inner = self._directory(node.value.value, depth + 1)
            if inner is None or not isinstance(index.value, int):
                return None
            return posixpath.join(inner, *[".."] * (index.value + 1))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            left = self._directory(node.left, depth + 1)
            right = self.literal(node.right)
            return (
                None if left is None or right is None else posixpath.join(left, right)
            )
        return None

    def kind(self, call: ast.Call) -> tuple[str, ast.expr | None] | None:
        """The walk a call is and the path it is a method of, or None."""
        func = call.func
        if self.qualify(func) is not None:
            found = self.member(func)
            if found in DIRECTORY_READS or (
                found is not None and found[0] == "glob" and reads(*found)
            ):
                return found[1], None
            return None
        if isinstance(func, ast.Attribute):
            ast_walk = func.attr == "walk" and getattr(func.value, "id", "") == "ast"
            return (
                None if ast_walk or func.attr not in WALKS else (func.attr, func.value)
            )
        name = getattr(func, "id", "")
        return (name, None) if name in WALKS and name not in self.local else None

    def walk(self, call: ast.Call) -> str | None:
        """Why a walk or a glob may list a changed path, or None where it cannot."""
        found = self.kind(call)
        if found is None:
            return None
        name, owner = found
        args = list(call.args)
        pattern = None
        if name in ("glob", "rglob", "iglob"):
            options = {keyword.arg for keyword in call.keywords} - GLOB_OPTIONS
            if options:
                return f"{name} takes an option the scan does not read"
            pattern = self.literal(args[0]) if args else None
            if pattern is None:
                return f"{name} takes a pattern the scan cannot read"
            if name == "rglob":
                pattern = "**/" + pattern
        if pattern is not None and ".." in PurePosixPath(pattern).parts:
            return f"{name} takes a pattern that climbs with .."
        where = None if owner is None else self.directory(owner)
        if where is None:
            if pattern is None:
                return f"{name} lists a directory the scan cannot place"
            regex = glob_regex(plain(pattern))
            for path in self.changed:
                if any(regex.fullmatch(t) for t in tails(path)):
                    return (
                        f"{name} of a directory the scan cannot place may list {path}"
                    )
            return None
        for path in self.changed:
            rel = posixpath.relpath(path, where) if where != "." else path
            if rel.startswith(".."):
                continue
            if pattern is None or glob_regex(plain(pattern)).fullmatch(rel):
                return f"{name} lists {path}"
        return None

    def command(self, call: ast.Call, texts: list[str]) -> str | None:
        """Why a call that runs a command may read a changed path, or None."""
        runner = self.member(call.func)
        if runner is None or not runs_commands(*runner):
            return None
        first = call.args[0] if call.args else None
        commands: list[list[str | None]]
        if runner[0] == "asyncio" and runner[1].endswith("create_subprocess_exec"):
            commands = [[self.word(arg) for arg in call.args]]
        elif isinstance(first, ast.List | ast.Tuple):
            commands = [[self.word(item) for item in first.elts]]
        else:
            text = self.literal(first)
            split = simple_commands(text) if text is not None else None
            if text is not None and split is None:
                return "runs a shell string the scan cannot split"
            unread: list[list[str | None]] = [[None]]
            commands = unread if split is None else [list(c) for c in split]
        for command in commands:
            reason = self.simple(command)
            if reason is not None:
                return reason
        every = {w for text in texts for w in words(text)} | set(texts)
        for word in every:
            for path in self.changed:
                if names(word, path):
                    return f"runs a command whose word {word!r} matches {path}"
        return None

    def word(self, node: ast.expr) -> str | None:
        """A word of a command: a literal, or `python` for `sys.executable`."""
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "executable"
            and getattr(node.value, "id", "") == "sys"
        ):
            return "python"
        return self.literal(node)

    def simple(self, command: list[str | None]) -> str | None:
        """Why one simple command may read a changed path, or None."""
        name = command[0] if command else None
        program = PurePosixPath(name).name if name else "?"
        if program != "git" and not PYTHON.fullmatch(program):
            return f"runs {program}, whose reads are not read"
        if program == "git" and git_reads(command):
            return "runs a git command that may read or list files"
        for word in command:
            if word is None:
                continue
            if program != "git":
                reason = code_reads(word, str(self.file), self.changed)
                if reason is not None:
                    return f"runs Python code that {reason}"
            for path in self.changed:
                if names(word, path):
                    return f"runs a command whose word {word!r} matches {path}"
        return None

    def taken(self, node: ast.expr, inner: set[int]) -> str | None:
        """Why a name or an attribute that is not called may hide a read, or None.

        `inner` holds the ids of the nodes called or read an attribute of.
        """
        if id(node) in inner:
            return None
        if not isinstance(node, ast.Name | ast.Attribute):
            return None
        name = self.qualify(node)
        if name is None:
            if not isinstance(node, ast.Attribute) or node.attr not in WALKS:
                return None
            if node.attr == "walk" and getattr(node.value, "id", "") == "ast":
                return None
            return f"takes {node.attr} without a call, so its walk is not read"
        found = split(name)
        if found is None and not tracked(name):
            return None
        if found is None or found[1] == "":
            return f"takes {name} other than through its members"
        if reads(*found):
            return f"takes {name} without a call, so its reads are not read"
        return None


def imports_by_name(call: ast.Call) -> bool:
    """Say whether a call imports a read module by a literal name."""
    func = call.func
    name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
    if name not in ("import_module", "__import__"):
        return False
    first = call.args[0] if call.args else None
    if not isinstance(first, ast.Constant) or not isinstance(first.value, str):
        return False
    return tracked(first.value)


def argv(
    node: ast.expr, literal: Callable[[ast.expr], str | None]
) -> list[list[str | None]]:
    """The simple commands of an argument: a list's items, or a string's.

    A string the scan cannot split gives its first word, then None.
    """
    if isinstance(node, ast.List | ast.Tuple):
        return [[literal(item) for item in node.elts]]
    text = literal(node)
    if text is None:
        return [[None]]
    split = simple_commands(text)
    if split is None:
        return [[*words(text)[:1], None]]
    return [list(command) for command in split]


def is_git(command: list[str | None]) -> bool:
    """Say whether a simple command runs git with at least one word after it."""
    first = command[0] if len(command) > 1 else None
    return first is not None and PurePosixPath(first).name == "git"


def code_reads(text: str, file: str, changed: list[str]) -> str | None:
    """Why a string of Python code may read a changed file, or None."""
    try:
        ast.parse(text)
    except SyntaxError:
        return None
    hits = scan_python(text, file, changed)
    return hits[0].split(": ", 1)[1] if hits else None


def runs_code(call: ast.Call, file: str, changed: list[str]) -> str | None:
    """Why `exec`, `eval` or `compile` of a literal may read a changed file."""
    if getattr(call.func, "id", "") not in ("exec", "eval", "compile"):
        return None
    first = call.args[0] if call.args else None
    if not isinstance(first, ast.Constant) or not isinstance(first.value, str):
        return None
    found = code_reads(first.value, file, changed)
    return None if found is None else f"runs Python code that {found}"


def docstrings(tree: ast.AST) -> set[int]:
    """The ids of the string nodes that stand alone, docstrings among them."""
    return {
        id(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
    }


def scan_python(source: str, file: str, changed: list[str]) -> list[str]:
    """The lines of one Python file that may read a changed file."""
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return [f"{file}:{error.lineno}: does not parse, so it cannot be read"]
    skip = docstrings(tree)
    scan = Scan(file, tree, changed)
    conftest = PurePosixPath(file).name == "conftest.py"
    hits = [f"{file}:{line}: imports a read module with *" for line in scan.stars]
    inner = {id(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
    inner |= {id(n.value) for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    for node in ast.walk(tree):
        if isinstance(node, ast.expr):
            reason = scan.taken(node, inner)
            if reason is not None:
                hits.append(f"{file}:{node.lineno}: {reason}")
        if (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id in scan.ambiguous
        ):
            reason = f"{node.id} is bound more than once, so the scan cannot say which"
            hits.append(f"{file}:{node.lineno}: {reason}")
        if isinstance(node, ast.Attribute) and node.attr in LOOP_RUNS:
            hits.append(f"{file}:{node.lineno}: runs a command through an event loop")
        if isinstance(node, ast.Call) and imports_by_name(node):
            hits.append(f"{file}:{node.lineno}: imports a read module by its name")
        if isinstance(node, ast.Call):
            reason = runs_code(node, file, changed)
            if reason is not None:
                hits.append(f"{file}:{node.lineno}: {reason}")
        if isinstance(node, ast.Call):
            texts = [
                n.value
                for n in ast.walk(node)
                if isinstance(n, ast.Constant)
                and isinstance(n.value, str)
                and id(n) not in skip
            ]
            for reason in (scan.walk(node), scan.command(node, texts)):
                if reason is not None:
                    hits.append(f"{file}:{node.lineno}: {reason}")
            runner = scan.member(node.func)
            given = [] if runner and runs_commands(*runner) else node.args
            for arg in given:
                commands = argv(arg, scan.literal)
                gits = [is_git(command) for command in commands]
                inert = [g and not git_reads(c) for g, c in zip(gits, commands)]
                if any(gits) and not all(inert):
                    hits.append(f"{file}:{node.lineno}: a git command may read files")
            if scan.kind(node) is not None:
                skip |= {id(arg) for arg in node.args if isinstance(arg, ast.Constant)}
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        if id(node) in skip:
            continue
        for path in changed:
            suffix = PurePosixPath(path).suffix
            if names(node.value, path) or (
                conftest and suffix and node.value == suffix
            ):
                hits.append(f"{file}:{node.lineno}: {node.value!r} matches {path}")
    return hits


def scan_settings(text: str, file: str, changed: list[str]) -> list[str]:
    """The doctest options that may collect a changed file."""
    hits = []
    for number, line in enumerate(text.splitlines(), start=1):
        code = line.split("#", 1)[0]
        if "doctest" not in code:
            continue
        values = re.findall(r"[\w*?./!\[\]-]+", code)
        if any(names(v.split("=")[-1], p) for v in values for p in changed):
            hits.append(f"{file}:{number}: a doctest option collects a changed path")
    code = "\n".join(line.split("#", 1)[0] for line in text.splitlines())
    for match in re.finditer(r"--doctest-glob[\s=\"',]+([^\s\"',\]]+)", code):
        number = code.count("\n", 0, match.start()) + 1
        if any(names(match.group(1), p) for p in changed):
            hits.append(f"{file}:{number}: a doctest glob collects a changed path")
    return hits


def scan_text(text: str, file: str, changed: list[str]) -> list[str]:
    """The lines of a fixture or a script that name a changed file."""
    hits = []
    for path in changed:
        name = re.escape(PurePosixPath(path).name)
        for number, line in enumerate(text.splitlines(), start=1):
            if re.search(rf"(?<![\w.-]){name}(?![\w-])", line):
                hits.append(f"{file}:{number}: names {path}")
    return hits


def testpaths(root: Path) -> list[str]:
    """The `testpaths` of `pyproject.toml`, a string or a list; else the root."""
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        return ["."]
    table = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    options = table.get("tool", {}).get("pytest", {}).get("ini_options", {})
    found = options.get("testpaths", ["."])
    if isinstance(found, str):
        found = found.split()
    return [posixpath.normpath(str(p)) for p in found] or ["."]


def main() -> int:
    """Print what may read the diff and exit 1, or exit 0 silently."""
    root = Path(sys.argv[1])
    if sys.argv[2] == "--paths":
        changed = sys.argv[3:]
    else:
        diff = subprocess.run(
            ["git", "-C", str(root), "diff", "-z", "--name-only", "--no-renames"]
            + [f"{sys.argv[2]}...HEAD"],
            capture_output=True,
            check=True,
            text=True,
        )
        changed = [path for path in diff.stdout.split("\0") if path]
    hits = []
    roots = testpaths(root)

    def under(path: str) -> bool:
        return any(r == "." or path == r or path.startswith(f"{r}/") for r in roots)

    for path in changed:
        name = PurePosixPath(path).name
        if path.endswith(IMPORTED) or name in (*SETTINGS, "uv.lock") or under(path):
            hits.append(f"{path}:1: the suite imports or configures it")
    listed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        capture_output=True,
        check=True,
        text=True,
    )
    for file in filter(None, listed.stdout.split("\0")):
        target = root / file
        if not target.is_file():
            continue
        text = target.read_text(encoding="utf-8", errors="replace")
        if file.endswith(".py"):
            hits.extend(scan_python(text, file, changed))
        elif PurePosixPath(file).name in SETTINGS:
            hits.extend(scan_settings(text, file, changed))
        elif under(file):
            hits.extend(scan_text(text, file, changed))
    for hit in hits:
        print(hit)
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
