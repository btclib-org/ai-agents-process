#!/usr/bin/env python3
"""Run suite-reads.py on small trees and check what it finds.

    python3 scripts/test-suite-reads.py

Each case is a tree of a few files, staged in a new git repository, and
the changed paths given to the script. The script prints each case whose
answer is wrong, and exits 1 where there is one.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("suite-reads.py")
ROOT = "ROOT = Path(__file__).resolve().parents[1]\n"
SUB = "import subprocess\nimport sys\n"
PYPROJECT = '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n'

# (name, files, changed paths, whether the script finds a read)
CASES: list[tuple[str, dict[str, str], list[str], bool]] = [
    (
        "named in a comment only",
        {"tests/a_test.py": "# CONTRIBUTING.md\n"},
        ["CONTRIBUTING.md"],
        False,
    ),
    (
        "named in a docstring and a message only",
        {
            "tests/a_test.py": '"""CONTRIBUTING.md says."""\nX = "CONTRIBUTING.md\'s table"\n'
        },
        ["CONTRIBUTING.md"],
        False,
    ),
    (
        "named as a path",
        {"tests/a_test.py": ROOT + 'T = ROOT / "CONTRIBUTING.md"\n'},
        ["CONTRIBUTING.md"],
        True,
    ),
    (
        "named by its last parts",
        {"tests/a_test.py": 'T = "docs/a.md"\n'},
        ["x/docs/a.md"],
        True,
    ),
    (
        "a glob of its kind",
        {"tests/a_test.py": ROOT + 'P = list(ROOT.glob("*.md"))\n'},
        ["README.md"],
        True,
    ),
    (
        "a root glob, for a deeper file",
        {"tests/a_test.py": ROOT + 'P = list(ROOT.glob("*.md"))\n'},
        ["docs/a.md"],
        False,
    ),
    (
        "a deep glob, for a deeper file",
        {"tests/a_test.py": ROOT + 'P = list(ROOT.rglob("R*.md"))\n'},
        ["docs/README.md"],
        True,
    ),
    (
        "a glob of another kind",
        {"tests/a_test.py": ROOT + 'P = list(ROOT.rglob("*.py"))\n'},
        ["README.md"],
        False,
    ),
    (
        "a glob held in a name",
        {"tests/a_test.py": 'PATTERN = "**/*.md"\n'},
        ["docs/README.md"],
        True,
    ),
    (
        "a walk of another directory",
        {"tests/a_test.py": ROOT + 'P = list((ROOT / "fuzz").iterdir())\n'},
        ["README.md"],
        False,
    ),
    (
        "a walk of another directory, by parent",
        {
            "tests/a_test.py": 'D = Path(__file__).parent.parent / "fuzz"\nP = list(D.iterdir())\n'
        },
        ["README.md"],
        False,
    ),
    (
        "a walk of the root",
        {"tests/a_test.py": ROOT + "P = list(ROOT.iterdir())\n"},
        ["README.md"],
        True,
    ),
    (
        "a walk of a directory it cannot place",
        {"tests/a_test.py": "P = list(Path(x).iterdir())\n"},
        ["README.md"],
        True,
    ),
    (
        "an ast walk",
        {"tests/a_test.py": "import ast\nN = list(ast.walk(t))\n"},
        ["README.md"],
        False,
    ),
    (
        "a dotfile named as a path",
        {"tests/a_test.py": 'T = open(".pre-commit-config.yaml")\n'},
        [".pre-commit-config.yaml"],
        True,
    ),
    (
        "a recursive glob, for a file at its root",
        {"tests/a_test.py": ROOT + 'P = list(ROOT.glob("**/*.md"))\n'},
        ["README.md"],
        True,
    ),
    (
        "a recursive glob, for a nested file",
        {"tests/a_test.py": ROOT + 'P = list(ROOT.glob("**/*.md"))\n'},
        ["docs/README.md"],
        True,
    ),
    (
        "a runner imported by name",
        {"tests/a_test.py": 'from subprocess import run\nrun(["sh", "-c", "true"])\n'},
        ["README.md"],
        True,
    ),
    (
        "the old name of a rename",
        {"tests/a_test.py": 'T = open("docs/guide.md")\n'},
        ["docs/guide.md", "docs/new-guide.md"],
        True,
    ),
    (
        "a shell command naming it",
        {
            "tests/a_test.py": SUB
            + 'subprocess.check_output("cat docs/guide.md", shell=True)\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "a program that is neither git nor Python",
        {"tests/a_test.py": SUB + 'subprocess.run(["sh", "scripts/check.sh"])\n'},
        ["README.md"],
        True,
    ),
    (
        "a command it cannot name",
        {"tests/a_test.py": SUB + "subprocess.run(command)\n"},
        ["README.md"],
        True,
    ),
    (
        "Python code that names it",
        {
            "tests/a_test.py": SUB
            + 'subprocess.run([sys.executable, "-c", "open(\'README.md\')"])\n'
        },
        ["README.md"],
        True,
    ),
    (
        "Python code that does not",
        {"tests/a_test.py": SUB + 'subprocess.run([sys.executable, "-c", "pass"])\n'},
        ["README.md"],
        False,
    ),
    (
        "git ls-files",
        {"tests/a_test.py": 'import subprocess\nsubprocess.run(["git", "ls-files"])\n'},
        ["README.md"],
        True,
    ),
    (
        "git grep, of any kind",
        {
            "tests/a_test.py": 'import subprocess\nsubprocess.run(["git", "grep", "x", "--", "*.py"])\n'
        },
        ["README.md"],
        True,
    ),
    (
        "a conftest that collects its suffix",
        {
            "tests/conftest.py": 'def pytest_collect_file(file_path, parent):\n    return file_path.suffix == ".md"\n'
        },
        ["README.md"],
        True,
    ),
    (
        "its suffix outside a conftest",
        {"tests/a_test.py": 'S = ".md"\n'},
        ["README.md"],
        False,
    ),
    (
        "a doctest glob",
        {"pyproject.toml": PYPROJECT + 'addopts = "--doctest-glob=*.md"\n'},
        ["README.md"],
        True,
    ),
    (
        "a doctest glob of another kind",
        {"pyproject.toml": PYPROJECT + 'addopts = "--doctest-glob=*.rst"\n'},
        ["README.md"],
        False,
    ),
    (
        "named in an f-string",
        {"tests/a_test.py": 'T = f"{ROOT}/README.md"\n'},
        ["README.md"],
        True,
    ),
    ("named in a fixture", {"tests/data.json": '["README.md"]\n'}, ["README.md"], True),
    (
        "named in a shell script a test runs",
        {"tests/check.sh": "grep -q x README.md\n"},
        ["README.md"],
        True,
    ),
    (
        "named in a file outside testpaths",
        {"notes.txt": "README.md\n"},
        ["README.md"],
        False,
    ),
    (
        "a file under testpaths",
        {"pyproject.toml": PYPROJECT},
        ["tests/README.md"],
        True,
    ),
    ("a Python file", {}, ["scripts/a.py"], True),
    ("the lock", {}, ["uv.lock"], True),
    ("no testpaths", {"pyproject.toml": "[project]\n"}, ["README.md"], True),
    (
        "nothing reads it",
        {"pyproject.toml": PYPROJECT, "tests/a_test.py": "X = 1\n"},
        ["README.md"],
        False,
    ),
]


T = "def test_read():\n"
OPEN = T + '    assert open("docs/guide.md").read() == "ok"\n'
RES = "import importlib.resources as r\n" + T
# the reads a review found the scanner missed, each with the changed path
# whose edit made the test fail
REVIEWED: list[tuple[str, dict[str, str], list[str], bool]] = [
    (
        "a rename",
        {"tests/a_test.py": OPEN},
        ["docs/guide.md", "docs/new-guide.md"],
        True,
    ),
    (
        "cat in a shell string",
        {
            "tests/a_test.py": SUB
            + T
            + '    subprocess.check_output("cat docs/guide.md", shell=True)\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "a shell script outside testpaths",
        {
            "tests/a_test.py": SUB
            + T
            + '    subprocess.check_output(["sh", "scripts/read.sh"])\n',
            "scripts/read.sh": "cat docs/guide.md\n",
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "an alias of subprocess, a shell string",
        {
            "tests/a_test.py": "import subprocess as sp\n"
            + T
            + '    sp.check_output("cat docs/guide.md", shell=True)\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "an alias of subprocess, a script",
        {
            "tests/a_test.py": "import subprocess as sp\n"
            + T
            + '    sp.check_output(["sh", "scripts/read.sh"])\n',
            "scripts/read.sh": "cat docs/guide.md\n",
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "git ls-files in a shell string",
        {
            "tests/a_test.py": SUB
            + T
            + '    subprocess.check_output("git ls-files docs", shell=True)\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "git ls-tree in an argv",
        {
            "tests/a_test.py": SUB
            + T
            + '    subprocess.check_output(["git", "ls-tree", "-r", "--name-only", "HEAD", "docs"])\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "git -C ls-tree",
        {
            "tests/a_test.py": SUB
            + ROOT
            + T
            + '    subprocess.check_output(["git", "-C", str(ROOT), "ls-tree", "-r", "HEAD", "docs"])\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "a pathlib glob through **/",
        {"tests/a_test.py": ROOT + T + '    P = list(ROOT.glob("docs/**/*.md"))\n'},
        ["docs/guide.md"],
        True,
    ),
    (
        "glob.glob through **/",
        {
            "tests/a_test.py": "import glob\n"
            + T
            + '    P = glob.glob("docs/**/*.md", recursive=True)\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "a directory built with ..",
        {
            "tests/a_test.py": 'DOCS = Path(__file__).parent / ".." / "docs"\n'
            + T
            + '    P = list(DOCS.glob("*.md"))\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "a glob held in a name, flat",
        {
            "tests/a_test.py": ROOT
            + 'PATTERN = "docs/*"\n'
            + T
            + "    P = list(ROOT.glob(PATTERN))\n"
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "a glob held in a name, through **/",
        {
            "tests/a_test.py": ROOT
            + 'PATTERN = "docs/**/*.md"\n'
            + T
            + "    P = list(ROOT.glob(PATTERN))\n"
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "importlib.resources joinpath",
        {
            "pkg/__init__.py": "",
            "tests/a_test.py": RES
            + '    r.files("pkg").joinpath("guide.md").read_text()\n',
        },
        ["pkg/guide.md"],
        True,
    ),
    (
        "importlib.resources iterdir",
        {
            "pkg/__init__.py": "",
            "tests/a_test.py": RES + '    P = list(r.files("pkg").iterdir())\n',
        },
        ["pkg/guide.md"],
        True,
    ),
    (
        "importlib.resources joined with /",
        {
            "pkg/__init__.py": "",
            "tests/a_test.py": RES
            + '    (r.files("pkg") / "data" / "guide.md").read_text()\n',
        },
        ["pkg/data/guide.md"],
        True,
    ),
    ("a test outside testpaths", {"checks/a_test.py": OPEN}, ["docs/guide.md"], True),
    (
        "testpaths as a string",
        {
            "pyproject.toml": '[tool.pytest.ini_options]\ntestpaths = "tests"\n',
            "tests/a_test.py": "X = 1\n",
        },
        ["tests/vectors/v1.json"],
        True,
    ),
    (
        "testpaths as a list",
        {"tests/a_test.py": "X = 1\n"},
        ["tests/vectors/v1.json"],
        True,
    ),
    (
        "os.popen",
        {
            "tests/a_test.py": "import os\n"
            + T
            + '    os.popen("cat docs/guide.md").read()\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "a glob whose pattern is a parameter",
        {
            "tests/a_test.py": ROOT
            + "def files(pattern):\n    return list(ROOT.glob(pattern))\n"
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "a git read through a helper, in one string",
        {"tests/a_test.py": T + '    out("git ls-files docs")\n'},
        ["docs/guide.md"],
        True,
    ),
    (
        "an unrelated test",
        {"tests/a_test.py": T + "    assert 1 == 1\n"},
        ["docs/guide.md"],
        False,
    ),
]


# a later review's fixtures, by their names there; the one of them that
# runs `python -c` on a path built with `chr` is in ROUND_E
ROUND_D: list[tuple[str, dict[str, str], list[str], bool]] = [
    (
        "os-join",
        {
            "tests/test_read.py": 'import os\ndef test_read():\n    assert open(os.path.join("docs", "guide.md")).read() == "ok"\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "path-parents",
        {
            "tests/test_read.py": 'from pathlib import Path\ndef test_read():\n    assert (Path(__file__).resolve().parents[1] / "docs" / "guide.md").read_text() == "ok"\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "resources",
        {
            "pkg/__init__.py": "",
            "tests/test_read.py": 'import importlib.resources as r\ndef test_read():\n    assert r.files("pkg").joinpath("guide.md").read_text() == "ok"\n',
        },
        ["pkg/guide.md"],
        True,
    ),
    (
        "imported-constant",
        {
            "config.py": 'NAME = "docs/guide.md"\n',
            "tests/test_read.py": 'from config import NAME\ndef test_read():\n    assert open(NAME).read() == "ok"\n',
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "parametrize",
        {
            "tests/test_read.py": 'import pytest\n@pytest.mark.parametrize("filename", ["docs/guide.md", "docs/other.md"])\ndef test_read(filename):\n    assert open(filename).read() == "ok"\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "cat-argv",
        {
            "tests/test_read.py": 'import subprocess\ndef test_read():\n    assert subprocess.check_output(["cat", "docs/guide.md"]) == b"ok"\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "cat-shell",
        {
            "tests/test_read.py": 'import subprocess\ndef test_read():\n    assert subprocess.check_output("cat docs/guide.md", shell=True) == b"ok"\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "shell-under-testpaths",
        {
            "tests/test_read.py": 'import subprocess\ndef test_read():\n    assert subprocess.check_output(["sh", "tests/read.sh"]) == b"ok"\n',
            "tests/read.sh": "cat docs/guide.md\n",
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "shell-outside-testpaths",
        {
            "tests/test_read.py": 'import subprocess\ndef test_read():\n    assert subprocess.check_output(["sh", "scripts/read.sh"]) == b"ok"\n',
            "scripts/read.sh": "cat docs/guide.md\n",
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "other-test-directory",
        {
            "checks/test_read.py": 'def test_read():\n    assert open("docs/guide.md").read() == "ok"\n',
            "pyproject.toml": '[tool.pytest.ini_options]\ntestpaths = ["checks"]\n',
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "several-testpaths",
        {
            "checks/read.sh": "cat docs/guide.md\n",
            "checks/test_read.py": 'import subprocess\ndef test_read():\n    assert subprocess.check_output(["sh", "checks/read.sh"]) == b"ok"\n',
            "pyproject.toml": '[tool.pytest.ini_options]\ntestpaths = ["tests", "checks", "acceptance"]\n',
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "spaces",
        {
            "tests/test_read.py": 'def test_read():\n    assert open("docs/guide with spaces.md").read() == "ok"\n'
        },
        ["docs/guide with spaces.md"],
        True,
    ),
    (
        "deleted",
        {
            "tests/test_read.py": 'def test_read():\n    assert open("docs/guide.md").read() == "ok"\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "renamed",
        {
            "tests/test_read.py": 'def test_read():\n    assert open("docs/guide.md").read() == "ok"\n'
        },
        ["docs/guide.md", "docs/new-guide.md"],
        True,
    ),
    (
        "parents-deep-walk",
        {
            "tests/test_read.py": 'from pathlib import Path\ndef test_read():\n    assert any(p.read_text() == "ok" for p in Path(__file__).resolve().parents[1].rglob("*.md"))\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "unrelated-control",
        {"tests/test_read.py": "def test_read():\n    assert 1 == 1\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "nested-walk",
        {
            "tests/test_read.py": 'from pathlib import Path\ndef test_read():\n    for folder in Path(__file__).resolve().parents[1].iterdir():\n        if folder.is_dir():\n            assert any(p.read_text() == "ok" for p in folder.iterdir())\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "shell-git-walk",
        {
            "tests/test_read.py": 'import subprocess\ndef test_read():\n    for p in subprocess.check_output("git ls-files", shell=True, text=True).splitlines():\n        if p.endswith(".md"):\n            assert open(p).read() == "ok"\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "aliased-shell",
        {
            "tests/test_read.py": 'import subprocess as sp\ndef test_read():\n    assert sp.check_output(["sh", "scripts/read.sh"]) == b"ok"\n',
            "scripts/read.sh": "cat docs/guide.md\n",
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "glob-question",
        {
            "tests/test_read.py": 'from pathlib import Path\ndef test_read():\n    for p in Path("docs").glob("guide.?d"):\n        assert p.read_text() == "ok"\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "unplaced-class",
        {
            "tests/test_read.py": 'from pathlib import Path\ndef test_read():\n    assert all(p.read_text() == "ok" for p in Path("docs").glob("[g]uide.md"))\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "placed-class",
        {
            "tests/test_read.py": 'from pathlib import Path\nROOT = Path(__file__).resolve().parents[1]\ndef test_read():\n    assert all(p.read_text() == "ok" for p in (ROOT / "docs").glob("[g]uide.md"))\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "module-class",
        {
            "tests/test_read.py": 'import glob\ndef test_read():\n    assert all(open(p).read() == "ok" for p in glob.glob("docs/[g]uide.md"))\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "unplaced-parent",
        {
            "tests/test_read.py": 'from pathlib import Path\ndef test_read():\n    assert all(p.read_text() == "ok" for p in Path("tests").glob("../docs/*.md"))\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "glob-alias",
        {
            "tests/test_read.py": 'from glob import glob as collect\ndef test_read():\n    assert all(open(p).read() == "ok" for p in collect("docs/*"))\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "runner-assigned-alias",
        {
            "tests/test_read.py": 'import subprocess\nrunner = subprocess.check_output\ndef test_read():\n    assert runner(["sh", "scripts/read.sh"]) == b"ok"\n',
            "scripts/read.sh": "cat docs/guide.md\n",
        },
        ["docs/guide.md"],
        True,
    ),
    # the reads its rules ask for, and their controls
    (
        "a class glob of another file",
        {
            "tests/a_test.py": 'from pathlib import Path\nP = list(Path("docs").glob("[g]uide.rst"))\n'
        },
        ["docs/guide.md"],
        False,
    ),
    (
        "a class glob held in a string",
        {"tests/a_test.py": 'P = "docs/[g]uide.md"\n'},
        ["docs/guide.md"],
        True,
    ),
    (
        "a doctest glob with a class",
        {
            "pyproject.toml": '[tool.pytest.ini_options]\ntestpaths = ["tests"]\naddopts = "--doctest-glob=[R]EADME.md"\n'
        },
        ["README.md"],
        True,
    ),
    (
        "os imported with *",
        {"tests/a_test.py": "from os import *\n"},
        ["docs/guide.md"],
        True,
    ),
    (
        "subprocess imported by name",
        {
            "tests/a_test.py": 'import importlib\nS = importlib.import_module("subprocess")\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "a runner taken by getattr",
        {"tests/a_test.py": 'import subprocess\nR = getattr(subprocess, "run")\n'},
        ["docs/guide.md"],
        True,
    ),
    (
        "a runner in a partial",
        {
            "tests/a_test.py": "import functools\nimport subprocess\nR = functools.partial(subprocess.run, check=True)\n"
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "a path's glob bound to a name",
        {"tests/a_test.py": 'from pathlib import Path\nG = Path("docs").glob\n'},
        ["docs/guide.md"],
        True,
    ),
    (
        "shutil.copy bound to a name",
        {"tests/a_test.py": "import shutil\nC = shutil.copy\n"},
        ["docs/guide.md"],
        True,
    ),
    (
        "glob.glob bound to a name",
        {"tests/a_test.py": "import glob\nG = glob.glob\n"},
        ["docs/guide.md"],
        True,
    ),
    (
        "os.listdir bound to a name",
        {"tests/a_test.py": "import os\nL = os.listdir\n"},
        ["docs/guide.md"],
        True,
    ),
    (
        "importlib.metadata taken",
        {
            "tests/a_test.py": "import importlib\nE = importlib.metadata.PackageNotFoundError\n"
        },
        ["docs/guide.md"],
        False,
    ),
    (
        "shutil.copytree",
        {"tests/a_test.py": "import shutil\nshutil.copytree(src, dst)\n"},
        ["docs/guide.md"],
        True,
    ),
    (
        "os.walk imported by name",
        {"tests/a_test.py": "from os import walk as w\nP = list(w(top))\n"},
        ["docs/guide.md"],
        True,
    ),
    (
        "os.path.join bound to a name",
        {"tests/a_test.py": "import os\nJOIN = os.path.join\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "an error class of subprocess",
        {"tests/a_test.py": "import subprocess\nE = subprocess.CalledProcessError\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "an aliased glob of another kind",
        {
            "tests/a_test.py": 'from glob import glob as collect\nP = collect("docs/*.py")\n'
        },
        ["docs/guide.md"],
        False,
    ),
]


# a still later review's fixtures, by their names there, and the reads
# its rules ask for, with their controls
ROUND_E: list[tuple[str, dict[str, str], list[str], bool]] = [
    (
        "os.open",
        {
            "tests/test_read.py": 'import os\nreader = os.open\ndef test_read(filename):\n    fd = reader(filename, os.O_RDONLY)\n    try:\n        assert os.read(fd, 4096) == b"ok"\n    finally:\n        os.close(fd)\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "os.path.join",
        {"tests/test_read.py": "import os\nreader = os.path.join\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "os.pread",
        {"tests/test_read.py": "import os\nreader = os.pread\n"},
        ["docs/guide.md"],
        True,
    ),
    (
        "os.read",
        {"tests/test_read.py": "import os\nreader = os.read\n"},
        ["docs/guide.md"],
        True,
    ),
    (
        "os.readv",
        {"tests/test_read.py": "import os\nreader = os.readv\n"},
        ["docs/guide.md"],
        True,
    ),
    (
        "os.stat",
        {"tests/test_read.py": "import os\nreader = os.stat\n"},
        ["docs/guide.md"],
        True,
    ),
    (
        "shutil.copyfileobj",
        {"tests/test_read.py": "import shutil\nreader = shutil.copyfileobj\n"},
        ["docs/guide.md"],
        True,
    ),
    (
        "shutil.unpack_archive",
        {"tests/test_read.py": "import shutil\nreader = shutil.unpack_archive\n"},
        ["docs/guide.md"],
        True,
    ),
    (
        "shutil.which",
        {"tests/test_read.py": "import shutil\nreader = shutil.which\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "shutil-unpack",
        {
            "tests/test_read.py": 'import shutil\nfrom pathlib import Path\nunpacker = shutil.unpack_archive\ndef test_read(filename):\n    unpacker(filename, "out")\n    assert Path("out/result.txt").read_text() == "ok"\n'
        },
        ["docs/guide.zip"],
        True,
    ),
    (
        "scoped-import",
        {
            "tests/test_read.py": 'from glob import glob as collect\ndef unused():\n    from glob import escape as collect\n    return collect("unused")\ndef test_read():\n    assert all(open(p).read() == "ok" for p in collect("docs/*"))\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "scoped-directory",
        {
            "tests/test_read.py": 'from pathlib import Path\nROOT = Path(__file__).resolve().parent\ndef test_read():\n    ROOT = Path("docs")\n    assert all(p.read_text() == "ok" for p in ROOT.glob("*"))\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "python-inline-walk",
        {
            "tests/test_read.py": 'import subprocess\ndef test_read():\n    subprocess.run(["python3", "-c", "from pathlib import Path; assert all(p.read_text() == chr(111)+chr(107) for p in Path(chr(46)).rglob(chr(42)+chr(46)+chr(109)+chr(100)))"], check=True)\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "git log -p",
        {
            "tests/a_test.py": 'import subprocess\nsubprocess.run(["git", "log", "-p"])\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "git rev-parse",
        {
            "tests/a_test.py": 'import subprocess\nsubprocess.run(["git", "rev-parse", "HEAD"])\n'
        },
        ["docs/guide.md"],
        False,
    ),
    (
        "git -C rev-parse",
        {
            "tests/a_test.py": 'import subprocess\nfrom pathlib import Path\nROOT = Path(__file__).resolve().parents[1]\nsubprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"])\n'
        },
        ["docs/guide.md"],
        False,
    ),
    (
        "git with a subcommand it cannot read",
        {"tests/a_test.py": 'import subprocess\nsubprocess.run(["git", action])\n'},
        ["docs/guide.md"],
        True,
    ),
    (
        "git log given to a helper",
        {"tests/a_test.py": 'out(["git", "log", "-p"])\n'},
        ["docs/guide.md"],
        True,
    ),
    (
        "which git",
        {"tests/a_test.py": 'import shutil\nG = shutil.which("git")\n'},
        ["docs/guide.md"],
        False,
    ),
    (
        "exec of code that globs",
        {"tests/a_test.py": "exec(\"import glob\\nP = glob.glob('docs/*')\")\n"},
        ["docs/guide.md"],
        True,
    ),
    (
        "exec of code that reads nothing",
        {"tests/a_test.py": 'exec("x = 1")\n'},
        ["docs/guide.md"],
        False,
    ),
    (
        "a pattern that climbs",
        {
            "tests/a_test.py": 'from pathlib import Path\nROOT = Path(__file__).resolve().parents[1]\nP = list((ROOT / "tests").glob("../docs/*.md"))\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "asyncio.sleep bound to a name",
        {"tests/a_test.py": "import asyncio\nS = asyncio.sleep\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "asyncio's subprocess API bound to a name",
        {
            "tests/a_test.py": "import asyncio\nR = asyncio.subprocess.create_subprocess_exec\n"
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "asyncio's subprocess API called",
        {
            "tests/a_test.py": 'import asyncio\nasyncio.subprocess.create_subprocess_exec("sh", "x")\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "os imported twice alike",
        {
            "tests/a_test.py": "import os\ndef f():\n    import os\n    return os.environ\n"
        },
        ["docs/guide.md"],
        False,
    ),
    (
        "a constant of os",
        {"tests/a_test.py": "import os\nF = os.O_RDONLY\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "an error class of shutil",
        {"tests/a_test.py": "import shutil\nE = shutil.Error\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "a timeout class of subprocess",
        {"tests/a_test.py": "import subprocess\nE = subprocess.TimeoutExpired\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "os.path.getsize bound to a name",
        {"tests/a_test.py": "import os\nS = os.path.getsize\n"},
        ["docs/guide.md"],
        True,
    ),
    (
        "glob.glob1 called",
        {"tests/a_test.py": 'import glob\nP = glob.glob1(d, "x")\n'},
        ["docs/guide.md"],
        True,
    ),
]


# the seventh review's fixtures, by their names there, but for those
# whose reads the header names as misses, then the reads its rules ask
# for, with their controls
ROUND_F: list[tuple[str, dict[str, str], list[str], bool]] = [
    (
        "asyncio-loop-subprocess",
        {
            "tests/test_read.py": 'import asyncio\ndef test_read():\n    loop = asyncio.new_event_loop()\n    done = loop.create_future()\n    chunks = []\n    class Collect(asyncio.SubprocessProtocol):\n        def pipe_data_received(self, fd, data):\n            chunks.append(data)\n        def connection_lost(self, exc):\n            done.set_result(None)\n    transport, protocol = loop.run_until_complete(loop.subprocess_shell(Collect, "cat docs/*", stdout=-1))\n    loop.run_until_complete(done)\n    transport.close()\n    loop.close()\n    assert b"".join(chunks) == b"ok"\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "case-insensitive-glob",
        {
            "tests/test_read.py": 'from pathlib import Path\nROOT = Path(__file__).resolve().parents[1]\ndef test_read():\n    assert all(p.read_text() == "ok" for p in (ROOT / "docs").glob("*.md", case_sensitive=False))\n'
        },
        ["docs/GUIDE.MD"],
        True,
    ),
    (
        "default-git-argument",
        {"tests/test_read.py": 'def run(cmd=["git", "ls-files"]):\n    return cmd\n'},
        ["docs/guide.md"],
        False,
    ),
    (
        "exception-shaped-reader",
        {
            "tests/test_read.py": "import subprocess\nsubprocess.MyError = subprocess.run\nreader = subprocess.MyError\n"
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "git-inert-config",
        {
            "tests/test_read.py": 'import subprocess\nsubprocess.run(["git", "config"])\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "git-inert-init",
        {"tests/test_read.py": 'import subprocess\nsubprocess.run(["git", "init"])\n'},
        ["docs/guide.md"],
        True,
    ),
    (
        "git-inert-rev-parse",
        {
            "tests/test_read.py": 'import subprocess\nsubprocess.run(["git", "rev-parse"])\n'
        },
        ["docs/guide.md"],
        False,
    ),
    (
        "git-inert-symbolic-ref",
        {
            "tests/test_read.py": 'import subprocess\nsubprocess.run(["git", "symbolic-ref"])\n'
        },
        ["docs/guide.md"],
        False,
    ),
    (
        "git-inert-var",
        {"tests/test_read.py": 'import subprocess\nsubprocess.run(["git", "var"])\n'},
        ["docs/guide.md"],
        False,
    ),
    (
        "git-inert-version",
        {
            "tests/test_read.py": 'import subprocess\nsubprocess.run(["git", "version"])\n'
        },
        ["docs/guide.md"],
        False,
    ),
    (
        "git-init-template",
        {
            "tests/test_read.py": 'import subprocess\ndef test_read():\n    subprocess.run(["git", "init", "--template=templates", "target"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n    assert open("target/.git/description").read() == "ok"\n'
        },
        ["templates/description"],
        True,
    ),
    (
        "git-init-template-fresh",
        {
            "tests/test_read.py": 'import subprocess\nimport tempfile\ndef test_read():\n    target = tempfile.mkdtemp(dir=".")\n    subprocess.run(["git", "init", "--template=templates", target], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n    assert open(target + "/.git/description").read() == "ok"\n'
        },
        ["templates/description"],
        True,
    ),
    (
        "inert-glob-escape",
        {"tests/test_read.py": "import glob\nreader = glob.escape\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-glob-has_magic",
        {"tests/test_read.py": "import glob\nreader = glob.has_magic\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-glob-translate",
        {"tests/test_read.py": "import glob\nreader = glob.translate\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-altsep",
        {"tests/test_read.py": "import os\nreader = os.altsep\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-cpu_count",
        {"tests/test_read.py": "import os\nreader = os.cpu_count\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-curdir",
        {"tests/test_read.py": "import os\nreader = os.curdir\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-defpath",
        {"tests/test_read.py": "import os\nreader = os.defpath\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-devnull",
        {"tests/test_read.py": "import os\nreader = os.devnull\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-environ",
        {"tests/test_read.py": "import os\nreader = os.environ\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-environb",
        {"tests/test_read.py": "import os\nreader = os.environb\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-extsep",
        {"tests/test_read.py": "import os\nreader = os.extsep\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-fsdecode",
        {"tests/test_read.py": "import os\nreader = os.fsdecode\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-fsencode",
        {"tests/test_read.py": "import os\nreader = os.fsencode\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-fspath",
        {"tests/test_read.py": "import os\nreader = os.fspath\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-getcwd",
        {"tests/test_read.py": "import os\nreader = os.getcwd\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-getcwdb",
        {"tests/test_read.py": "import os\nreader = os.getcwdb\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-getenv",
        {"tests/test_read.py": "import os\nreader = os.getenv\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-getenvb",
        {"tests/test_read.py": "import os\nreader = os.getenvb\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-getpid",
        {"tests/test_read.py": "import os\nreader = os.getpid\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-getppid",
        {"tests/test_read.py": "import os\nreader = os.getppid\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-linesep",
        {"tests/test_read.py": "import os\nreader = os.linesep\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-name",
        {"tests/test_read.py": "import os\nreader = os.name\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-pardir",
        {"tests/test_read.py": "import os\nreader = os.pardir\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-path",
        {"tests/test_read.py": "import os\nreader = os.path\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-pathsep",
        {"tests/test_read.py": "import os\nreader = os.pathsep\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-putenv",
        {"tests/test_read.py": "import os\nreader = os.putenv\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-sep",
        {"tests/test_read.py": "import os\nreader = os.sep\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-os-unsetenv",
        {"tests/test_read.py": "import os\nreader = os.unsetenv\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-shutil-rmtree",
        {"tests/test_read.py": "import shutil\nreader = shutil.rmtree\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-shutil-which",
        {"tests/test_read.py": "import shutil\nreader = shutil.which\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "inert-subprocess-CompletedProcess",
        {
            "tests/test_read.py": "import subprocess\nreader = subprocess.CompletedProcess\n"
        },
        ["docs/guide.md"],
        False,
    ),
    (
        "os-path-getsize-submember",
        {"tests/test_read.py": "import os\nreader = os.path.getsize.__call__\n"},
        ["docs/guide.md"],
        True,
    ),
    (
        "rmtree-alias",
        {"tests/test_read.py": "import shutil\nreader = shutil.rmtree\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "shell-chain",
        {
            "tests/test_read.py": 'import subprocess\ndef test_read():\n    assert subprocess.check_output("git rev-parse --show-toplevel >/dev/null && cat docs/*", shell=True, text=True) == "ok"\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "shell-chain-python",
        {
            "tests/test_read.py": 'import subprocess\ndef test_read():\n    assert subprocess.check_output("python3 -c pass && cat docs/*", shell=True, text=True) == "ok"\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "sized-callable-full",
        {
            "tests/test_read.py": "import os\nsize = os.path.getsize.__call__\ndef test_read():\n    assert size(next(iter([p for p in [chr(100)+chr(111)+chr(99)+chr(115)+chr(47)+chr(103)+chr(117)+chr(105)+chr(100)+chr(101)+chr(46)+chr(109)+chr(100)]]))) == 2\n"
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "git config --file",
        {
            "tests/a_test.py": 'import subprocess\nsubprocess.run(["git", "config", "--file", "x.cfg", "--list"])\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "git config with an include",
        {
            "tests/a_test.py": 'import subprocess\nsubprocess.run(["git", "-c", "include.path=x", "config", "a.b"])\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "git config of a key",
        {
            "tests/a_test.py": 'import subprocess\nsubprocess.run(["git", "config", "user.name"])\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "config-short",
        {
            "tests/test_read.py": 'import subprocess\ndef test_read():\n    assert subprocess.check_output(["git", "config", "-fprefs/settings", "--get", "value.key"], text=True).strip() == "ok"\n'
        },
        ["prefs/settings"],
        True,
    ),
    (
        "a recursive glob of another kind",
        {
            "tests/a_test.py": 'import glob\nP = glob.glob("docs/**/*.py", recursive=True)\n'
        },
        ["docs/guide.md"],
        False,
    ),
    (
        "a glob with root_dir",
        {"tests/a_test.py": 'import glob\nP = glob.glob("*.py", root_dir="docs")\n'},
        ["docs/guide.md"],
        True,
    ),
    (
        "an inert command with its output redirected",
        {
            "tests/a_test.py": 'import subprocess\nsubprocess.run("git rev-parse HEAD > /dev/null", shell=True)\n'
        },
        ["docs/guide.md"],
        False,
    ),
    (
        "inert commands in a chain",
        {
            "tests/a_test.py": 'import subprocess\nsubprocess.run("python3 -c pass && git rev-parse HEAD", shell=True)\n'
        },
        ["docs/guide.md"],
        False,
    ),
    (
        "a command after a semicolon",
        {
            "tests/a_test.py": 'import subprocess\nsubprocess.run("git rev-parse HEAD; cat x", shell=True)\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "a substitution",
        {
            "tests/a_test.py": 'import subprocess\nsubprocess.run("git rev-parse $(cat x)", shell=True)\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "a backtick",
        {
            "tests/a_test.py": 'import subprocess\nsubprocess.run("git rev-parse `cat x`", shell=True)\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "a newline",
        {
            "tests/a_test.py": 'import subprocess\nsubprocess.run("git rev-parse HEAD\\ncat x", shell=True)\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "an input redirection",
        {
            "tests/a_test.py": 'import subprocess\nsubprocess.run("git rev-parse HEAD < x", shell=True)\n'
        },
        ["docs/guide.md"],
        True,
    ),
    (
        "the loop's subprocess_exec bound to a name",
        {"tests/a_test.py": "R = loop.subprocess_exec\n"},
        ["docs/guide.md"],
        True,
    ),
    (
        "a git chain given to a helper",
        {"tests/a_test.py": 'out("git rev-parse HEAD && cat docs/*")\n'},
        ["docs/guide.md"],
        True,
    ),
    (
        "an inert git command given to a helper",
        {"tests/a_test.py": 'out("git rev-parse HEAD")\n'},
        ["docs/guide.md"],
        False,
    ),
    (
        "a function of its own named walk",
        {"tests/a_test.py": "def walk(m):\n    return [walk(c) for c in m]\n"},
        ["docs/guide.md"],
        False,
    ),
    (
        "a walk the file does not bind",
        {"tests/a_test.py": "P = list(walk(top))\n"},
        ["docs/guide.md"],
        True,
    ),
]


def finds(files: dict[str, str], changed: list[str]) -> bool:
    """Say whether the script finds a read in a tree of these files."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        tree = {"pyproject.toml": PYPROJECT, **files}
        for name, text in tree.items():
            (root / name).parent.mkdir(parents=True, exist_ok=True)
            (root / name).write_text(text, encoding="utf-8")
        subprocess.run(["git", "init", "-q", tmp], check=True)
        subprocess.run(["git", "-C", tmp, "add", "."], check=True)
        done = subprocess.run(
            [sys.executable, "-I", str(SCRIPT), tmp, "--paths", *changed],
            capture_output=True,
            text=True,
            check=False,
        )
        if done.returncode not in (0, 1) or bool(done.stdout) != bool(done.returncode):
            sys.exit(f"suite-reads.py exited {done.returncode}: {done.stderr}")
        return done.returncode == 1


def main() -> None:
    """Print each case the script answers wrongly, and exit 1 on one."""
    wrong = [
        f"{'missed' if expected else 'found'}: {name}"
        for name, files, changed, expected in CASES
        + REVIEWED
        + ROUND_D
        + ROUND_E
        + ROUND_F
        if finds(files, changed) != expected
    ]
    if wrong:
        print("\n".join(wrong))
    sys.exit(1 if wrong else 0)


if __name__ == "__main__":
    main()
