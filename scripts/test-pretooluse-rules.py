#!/usr/bin/env python3
"""Feed commands to pretooluse-rules.py and check which rules it names.

    python3 -I scripts/test-pretooluse-rules.py

Each command in `CASES` goes to the script's `broken_rules`, which must
name exactly the rules listed beside it. A few more go in as hook events,
through the script's own entry point, for its exit code and output.
Long commands of each shape in `GROWTH` go in at two sizes, and the
script's CPU time must grow with their length, not its square; nested
`eval` must be lexed once. The test prints each case whose answer is
wrong, and exits 1 where there is one.
"""

import gc
import importlib.util
import json
import re
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

HOOK = Path(__file__).with_name("pretooluse-rules.py")

CASES: list[tuple[str, set[str]]] = [
    # a command opens with cd, and only that
    ("cd /w && git status", {"cd"}),
    ("cd /w; ls", {"cd"}),
    ("cd", {"cd"}),
    ("  cd /w", {"cd"}),
    ("# a note\ncd /w", {"cd"}),
    ("FOO=1 cd /w", {"cd"}),
    ("command cd /w", {"cd"}),
    ("{ cd /w; make; }", {"cd"}),
    ("(cd /w && make)", set()),
    ("git -C /w status && cd /x", set()),
    ("ls | cd /w", set()),
    ("echo cd /w", set()),
    ("cdk deploy", set()),
    ("sh -c 'cd /w && make'", set()),
    ('git commit -m "cd /w"', set()),
    ("cat <<'EOF'\ncd /w\nEOF", set()),
    ("cat <<-EOF\n\tgit stash\n\tEOF\necho done", set()),
    ("env -C /w make", set()),
    # pytest -n auto
    ("pytest -n auto", {"xdist"}),
    ("uv run pytest -n auto tests", {"xdist"}),
    ("uv run --project /w --with pytest-xdist pytest -nauto", {"xdist"}),
    ("uv run --env-file /w/.env --python 3.15 pytest -n auto", {"xdist"}),
    ("python3 -m pytest --numprocesses=auto", {"xdist"}),
    ("python -I -m pytest --numprocesses auto", {"xdist"}),
    (".venv/bin/pytest -n logical", {"xdist"}),
    ("env -C /w uv run pytest -n auto", {"xdist"}),
    ("timeout -k 60 900 uv run pytest -n auto", {"xdist"}),
    # PYTEST_ADDOPTS is read only as a literal prefix of pytest itself,
    # split as pytest splits it
    ("PYTEST_ADDOPTS='-n auto' uv run pytest", {"xdist"}),
    ("env PYTEST_ADDOPTS='-n auto' pytest", {"xdist"}),
    ("PYTEST_ADDOPTS=\"-n 'auto'\" pytest", {"xdist"}),
    ("PYTEST_ADDOPTS='-n auto' pytest -- -n 2", {"xdist"}),
    ("PYTEST_ADDOPTS=\"-o 'cache_dir=some -n auto '\" pytest", set()),
    ("PYTEST_ADDOPTS=\"-k 'some -n auto '\" pytest", set()),
    ('PYTEST_ADDOPTS="$OPTS -n auto" pytest', set()),
    ('PYTEST_ADDOPTS="-n \'auto" pytest', set()),
    ('PYTEST_ADDOPTS="-n auto" env -u PYTEST_ADDOPTS pytest', set()),
    ("PYTEST_ADDOPTS='-n auto' env -i pytest", set()),
    ("PYTEST_ADDOPTS='-n auto' sh -c pytest", set()),
    # set any other way, PYTEST_ADDOPTS is not read
    ("export PYTEST_ADDOPTS='-x -n auto'; pytest", set()),
    ("export PYTEST_ADDOPTS='-n auto'; pytest -n 2", set()),
    ("export PYTEST_ADDOPTS='-n 2'; pytest -n auto", {"xdist"}),
    ('export PYTEST_ADDOPTS="-n auto"; PYTEST_ADDOPTS+=" -n 2"; pytest', set()),
    (
        'export PYTEST_ADDOPTS="-n auto"; read -r PYTEST_ADDOPTS <<< "-n 2"; pytest',
        set(),
    ),
    (
        (
            'export PYTEST_ADDOPTS="-n auto"; for o in "-n 2"; do PYTEST_ADDOPTS=$o;'
            " done; pytest"
        ),
        set(),
    ),
    ("PYTEST_ADDOPTS='-n auto'; sh -c 'export PYTEST_ADDOPTS; pytest'", set()),
    ("PYTEST_ADDOPTS='-n auto'; export PYTEST_ADDOPTS; sh -c pytest", set()),
    ('export PYTEST_ADDOPTS="-n auto"; unset PYTEST_ADDOPTS; pytest', set()),
    ('export PYTEST_ADDOPTS="-n auto"; exec env -u PYTEST_ADDOPTS pytest', set()),
    ("export PYTEST_ADDOPTS='-n auto'; uv run --env-file /w/env pytest", set()),
    ('(export PYTEST_ADDOPTS="-n auto"); pytest', set()),
    ("(export PYTEST_ADDOPTS='-n auto'; pytest)", set()),
    ("false && export PYTEST_ADDOPTS='-n auto'; pytest", set()),
    ("export PYTEST_ADDOPTS='-n auto'; source /w/env; pytest", set()),
    # a version request runs nothing
    ("pytest -nauto --version", set()),
    ("pytest -nauto -V", set()),
    ("sh -c 'pytest -n auto'", {"xdist"}),
    ("uvx pytest -n auto", {"xdist"}),
    ("coverage run -m pytest -n auto", {"xdist"}),
    ("uv run pytest -x | tail -n 20 && pytest -n auto", {"xdist"}),
    ("pytest -n 2", set()),
    ("PYTEST_ADDOPTS='-n auto' pytest -n 2", set()),
    ('pytest -n auto -n "$GATE_LOCK_WORKERS"', set()),
    ("PYTEST_ADDOPTS='-n auto' printf '%s\\n' ok", set()),
    ("pytest -n auto -n 0", set()),
    ("pytest -n 2 -n auto", {"xdist"}),
    ("pytest -n 0", set()),
    # pytest reads no option after `--`, nor the value of `-k`
    ("pytest -- -n auto", set()),
    ("pytest -n auto -- -n 0", {"xdist"}),
    ('pytest -k "-nauto"', set()),
    ("pytest -k foo -n auto", {"xdist"}),
    ("pytest -m slow -nauto", {"xdist"}),
    ("pytest -n=auto", {"xdist"}),
    ("pytest -nauto -n 2", set()),
    ('uv run pytest -n "$GATE_LOCK_WORKERS"', set()),
    ("echo 'pytest -n auto'", set()),
    ('git commit -m "never -n auto"', set()),
    ("git commit -n -m x", set()),
    ("grep -rn auto .", set()),
    ("uv run --with pytest python script.py -n auto", set()),
    ("cat <<EOF\npytest -n auto\nEOF", set()),
    # a gh watch at 120 seconds or more
    ("gh pr checks 12 --watch", {"watch"}),
    ("gh pr checks 12 --repo o/r --watch --interval 30", {"watch"}),
    ("gh run watch 123", {"watch"}),
    ("gh run watch 123 -i 10", {"watch"}),
    ("gh pr checks 12 --watch --interval 120", set()),
    ("gh pr checks 12 --watch -i=300", set()),
    ("gh run watch 123 --interval=120 --exit-status", set()),
    ("gh run watch 1 --interval 120 -- --interval 10", set()),
    ("gh pr checks 12", set()),
    ("gh run watch --help", set()),
    ("gh pr checks 12 --watch=false", set()),
    ('gh pr checks 12 --watch -i "$I"', set()),
    # Bitcoin Core with an explicit -datadir
    ("bitcoind -version", {"datadir"}),
    ("bitcoin-cli getblockcount", {"datadir"}),
    ("/opt/bitcoin/bin/bitcoind -regtest -daemon", {"datadir"}),
    ("bitcoin-cli getblockcount -datadir=/s/d", {"datadir"}),
    ("bitcoind -datadir= -version", {"datadir"}),
    ("bitcoin node -regtest", {"datadir"}),
    ("bitcoin -m rpc getblockcount", {"datadir"}),
    ("timeout 30 bitcoin-cli -regtest stop", {"datadir"}),
    ("nohup ./bitcoind -regtest > /s/log 2>&1 &", {"datadir"}),
    ("bitcoind -datadir=/s/d -version", set()),
    ("bitcoin-cli --datadir=/s/d -regtest getblockcount", set()),
    ("bitcoin-wallet -datadir=/s/d info", set()),
    ('bitcoind -datadir="$S/node" -daemon', set()),
    ("bitcoin --version", set()),
    ("bitcoin-tx -create", set()),
    ("command -v bitcoind", set()),
    ("which bitcoin-cli", set()),
    ("pgrep -f bitcoind", set()),
    ("test/functional/test_runner.py feature_block.py", set()),
    ("BITCOIND=/b/bitcoind test/functional/wallet_basic.py", set()),
    ("echo bitcoind -version", set()),
    ("ls build/bin/bitcoind", set()),
    # git stash
    ("git stash", {"stash"}),
    ("git -C /w stash push -m wip", {"stash"}),
    ("git -C /w stash pop", {"stash"}),
    ("git -c core.x=y stash -u", {"stash"}),
    ("sh -c 'git stash'", {"stash"}),
    ("eval 'git stash'", {"stash"}),
    ("eval eval git stash", {"stash"}),
    ("eval " * 30 + "'git stash'", {"stash"}),
    ("eval echo git stash", set()),
    ("bash -n -c 'git stash'", set()),
    ("bash -nc 'git stash'", set()),
    ("sh -o noexec -c 'git stash'", set()),
    ("bash -n +n -c 'git stash'", {"stash"}),
    ("eval pytest -nauto \\$X", set()),
    ("echo `git stash`", {"stash"}),
    ('echo "$(git stash)"', {"stash"}),
    ("printf 'a\\n' | xargs git stash", {"stash"}),
    ("'git' \"stash\"", {"stash"}),
    ('g""it stash', {"stash"}),
    ('git -C "/a path" stash', {"stash"}),
    ("env GIT_DIR=/r/.git git stash", {"stash"}),
    ("bash -lc 'git stash'", {"stash"}),
    ("git log | head && git stash", {"stash"}),
    ("git stash list", set()),
    ("git stash --help", set()),
    ("git -C /w stash show -p", set()),
    ('git commit -m "never git stash"', set()),
    ("echo '$(git stash)'", set()),
    ("git grep stash", set()),
    ("echo git stash", set()),
    # a force-push without a lease
    ("git push --force origin b", {"force"}),
    ("git push -f origin b", {"force"}),
    ("git push --force-with-lease=refs/heads/b:abc --force origin b", {"force"}),
    ("git push -uf origin b", {"force"}),
    ("git push origin +b:b", {"force"}),
    ("true && git push --force origin b", {"force"}),
    ("git push --force-with-lease origin +b:b", set()),
    ("git push --force-with-lease --no-force-with-lease origin +b:b", {"force"}),
    ("git push --no-force-with-lease --force-with-lease origin +b:b", set()),
    ("git push --dry-run --force origin b", set()),
    ("git push -n -f origin b", set()),
    ("git push -- origin +HEAD:refs/heads/topic", {"force"}),
    ("git push -- --force", set()),
    ("git worktree add -- /scratch/wt FETCH_HEAD", {"fetch-head"}),
    ("git push --force-with-lease=refs/heads/b:abc origin HEAD:refs/heads/b", set()),
    ("git push -o ci.skip origin b", set()),
    ("git push origin b-r2", set()),
    ("git worktree remove --force /w", set()),
    # a worktree at FETCH_HEAD
    ("git worktree add /s/wt FETCH_HEAD", {"fetch-head"}),
    ("git -C /r worktree add --detach /s/wt FETCH_HEAD", {"fetch-head"}),
    ("git -C /r worktree add -b x /s/wt 'FETCH_HEAD^{commit}'", {"fetch-head"}),
    ("git -C /r worktree add /s/wt abc123", set()),
    ("git worktree add -b FETCH_HEAD /s/new abc123", set()),
    ("git worktree add -b x /s/wt FETCH_HEAD", {"fetch-head"}),
    ("git -C /r rev-parse FETCH_HEAD", set()),
    # uv cache prune --force
    ("uv cache prune --force", {"prune"}),
    ("uv cache prune", set()),
    ("uv --version cache prune --force", set()),
    ("uv -V cache prune --force", set()),
    # CodeRabbit's CLI with credits
    ("coderabbit review --agent --use-credits", {"credits"}),
    ("env -C /w timeout 1200 coderabbit review --use-credits --committed", {"credits"}),
    ("sh -c 'coderabbit review --use-credits'", {"credits"}),
    ("coderabbit review --agent --committed --fresh --base-commit abc", set()),
    ('coderabbit review --base-commit "$1" --use-credits', set()),
    ("coderabbit review --use-credits --help", set()),
    ("coderabbit review -- --use-credits", set()),
    ("echo 'never coderabbit review --use-credits'", set()),
    ('git commit -m "coderabbit --use-credits is refused"', set()),
    ("coderabbit usage", set()),
    ("uv cache clean --force", set()),
    # signing turned off
    ("git commit --no-gpg-sign -m x", {"sign"}),
    ("git -c commit.gpgsign=false commit -m x", {"sign"}),
    ("git -C /w -c commit.gpgSign=no commit --amend --no-edit", {"sign"}),
    ("git -c commit.gpgsign= commit -m x", {"sign"}),
    ('git -c "commit.gpgsign=false" rebase origin/main', {"sign"}),
    ("git rebase --no-gpg-sign origin/main", {"sign"}),
    ("git config --global commit.gpgsign false", {"sign"}),
    ("git config --global --unset commit.gpgsign", {"sign"}),
    ("git config unset --global commit.gpgsign", {"sign"}),
    ("git config --local commit.gpgsign false", {"sign"}),
    # an unset outside the global file leaves the global value
    ("git config --unset commit.gpgsign", set()),
    ("git config --local --unset commit.gpgsign", set()),
    ("git config --worktree --unset-all commit.gpgsign", set()),
    ("git config --system --unset commit.gpgsign", set()),
    (
        "env PATH=/w/.venv/bin:$PATH git -C /w -c commit.gpgsign=0 commit -s -m x",
        {"sign"},
    ),
    ("sh -c 'git -c commit.gpgsign=false commit -m x'", {"sign"}),
    ("git commit -s -m x", set()),
    ("git -c commit.gpgsign=true commit -m x", set()),
    ("git -c commit.gpgsign commit -m x", set()),
    ('git commit -m "never --no-gpg-sign"', set()),
    ("git commit -m --no-gpg-sign", set()),
    ("echo git -c commit.gpgsign=false commit", set()),
    ("git grep -n -e --no-gpg-sign", set()),
    ("git config --get commit.gpgsign", set()),
    ("git log --format='%h %G? %GS' origin/main..", set()),
    ("cat > /s/msg.txt <<'EOF'\ngit -c commit.gpgsign=false\nEOF", set()),
    # the last setting decides signing, and a read turns nothing off
    ("git -c commit.gpgsign=false -c commit.gpgsign=true commit -s -m x", set()),
    ("git -c commit.gpgsign=false commit -S -s -m x", set()),
    ("git commit --no-gpg-sign -S -s -m x", set()),
    ("git commit -S --no-gpg-sign -m x", {"sign"}),
    ('git -c commit.gpgsign=false commit -m "$msg"', {"sign"}),
    ("git config --get-regexp commit.gpgsign false", set()),
    ("git commit -s -m x -- --no-gpg-sign", set()),
    ("git -c commit.gpgsign=false status", set()),
    ('git -c commit.gpgsign=false -c "$CONFIG" commit -s -m x', set()),
    ('git -c "$CONFIG" -c commit.gpgsign=false commit -s -m x', {"sign"}),
    # options with which no commit is written
    ("git -c commit.gpgsign=false rebase --abort", set()),
    ("git -c commit.gpgsign=false rebase --show-current-patch", set()),
    ("git -c commit.gpgsign=false cherry-pick --quit", set()),
    ("git -c commit.gpgsign=false merge --abort", set()),
    ("git -c commit.gpgsign=false commit --dry-run -s -m x", set()),
    ("git -c commit.gpgsign=false rebase --continue", {"sign"}),
    ("git -c commit.gpgsign=false commit -m --dry-run", {"sign"}),
    ("git -c commit.gpgsign=false commit -m x --dry-run", set()),
    # several rules in one call, and text the shell does not run
    ("cd /w && git stash && pytest -n auto", {"cd", "stash", "xdist"}),
    ("git commit -m 'unterminated", set()),
    ('echo "unterminated', set()),
    ("command -p -v bitcoind", set()),
    ("f() { git stash; }", set()),
    ("function f { git stash; }", set()),
    ('f() { echo "$(git stash)"; }', set()),
    ("f () { git stash; }", set()),
    ("function f () { git stash; }", set()),
    ("f() {\n    # }\n    git stash\n}", set()),
    ('f() { echo "${#x}"; }; git stash', {"stash"}),
    ("f() (git stash)", set()),
    ('f() { echo "$(git stash)"; }; git stash', {"stash"}),
    ("arr=(); git stash", {"stash"}),
    ("if (git stash); then :; fi", {"stash"}),
    # quotes the shell only removes
    ("git \"st\"'ash'", {"stash"}),
    ('git st""ash', {"stash"}),
    ('echo "$$$"; git stash', {"stash"}),
    # text the shell refuses to run, which runs none of it
    ('git "stash', set()),
    ('echo "$(git stash', set()),
    ("echo `git stash", set()),
    ("(git stash", set()),
    ("echo ${x; git stash", set()),
    ('sh -c "git \'stash"', set()),
    ("git push --force --help", set()),
    ("uv cache prune --force --help", set()),
    ("pytest -n auto --help", set()),
    ("env --help git stash", set()),
    ("timeout --help 1 git stash", set()),
    ("nice --help git stash", set()),
    ("printf %s foo | env --help git stash", set()),
    ("env -C /w git stash", {"stash"}),
    # a word holding `$` where it could make the command comply
    ('git stash "$ACTION"', set()),
    ('bitcoin-cli "$DATADIR_OPT" getblockcount', set()),
    ('git push --force origin "$branch"', set()),
    ('git push "$LEASE" origin +b:b', set()),
    ('git -c commit.gpgsign=false commit "$OPTS"', set()),
    ('gh run watch "$run" --exit-status', set()),
    ('gh run watch 123 --interval 10 "$MORE"', set()),
    ('gh run watch 123 --interval 10 --repo "$REPO"', {"watch"}),
    ('gh run watch 123 --interval 10 -R "$REPO"', {"watch"}),
    ('gh run watch 123 --interval 10 --repo="$REPO"', {"watch"}),
    ('gh pr checks 1 --watch --interval 10 --json "$F" --jq "$Q"', {"watch"}),
    ('pytest -n auto "$@"', set()),
    ('pytest -nauto "$@"', set()),
    ('pytest --numprocesses=auto "$@"', set()),
    ('pytest -n 2 -nauto "$X"', set()),
    # nesting the lexer follows, and nesting it does not
    ("(" * 50 + "git stash" + ")" * 50, {"stash"}),
    ("(" * 1500 + "echo ok" + ")" * 1500, set()),
]

# Shapes of long command, each to pass, and the size n each is built at.
# The script's CPU time on the shape at 2n may be at most `GROWTH_BOUND`
# times its time at n, plus `SLACK` seconds for the clock: a cost that
# grows with the length is about 2, one with its square about 4.
GROWTH: list[tuple[str, Callable[[int], str], int]] = [
    ("a long word", lambda n: "echo " + "a" * n, 500_000),
    ("assignments", lambda n: "A=x " * n + "echo ok", 50_000),
    ("runs of $", lambda n: "echo " + "$" * n, 500_000),
    ("empty quotes", lambda n: "echo " + 'a""' * n, 150_000),
    (
        "pytest after an export",
        lambda n: "export PYTEST_ADDOPTS='" + "-q " * n + "'; " + "pytest; " * n,
        3_000,
    ),
    ("nested eval", lambda n: "eval " * n + "echo", 200_000),
]
GROWTH_BOUND = 3.0
SLACK = 0.02
# A measure that fails may be the clock's: it is taken again, this many
# times in all.
TRIES = 3
# Nested `eval` of words the shell reads again as they stand, which the
# script lexes once, and what it must name.
EVALS = ("eval " * 50 + "git stash", ["stash"])
# The seconds a hook event may take end to end, far over any it needs.
EVENT_TIMEOUT = 60

# (stdin, expected exit code, whether stderr names a section)
EVENTS: list[tuple[str, int, bool]] = [
    (
        json.dumps(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "git stash"},
            }
        ),
        2,
        True,
    ),
    (
        json.dumps(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "git -C /w status"},
            }
        ),
        0,
        False,
    ),
    (
        json.dumps(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Read",
                "tool_input": {"file_path": "/w/git stash"},
            }
        ),
        0,
        False,
    ),
    ('{"tool_name": "Bash", "tool_input": {}}', 0, False),
    ('{"tool_name": "Bash", "tool_input": null}', 0, False),
    ('{"tool_name": "Bash", "tool_input": {"command": 12}}', 0, False),
    ("{", 0, False),
    ("[]", 0, False),
    ("null", 0, False),
    ("[" * 1500 + "0" + "]" * 1500, 0, False),
]


def load() -> Any:
    # no __pycache__ beside the script, which would leave the tree dirty
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("pretooluse_rules", HOOK)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cpu(hook: Any, command: str) -> float:
    """The CPU seconds `broken_rules` takes on `command`, with no garbage
    collection inside the measure."""
    gc.collect()
    gc.disable()
    try:
        start = time.process_time()
        hook.broken_rules(command)
        return time.process_time() - start
    finally:
        gc.enable()


def growth(hook: Any, build: Callable[[int], str], n: int) -> str | None:
    """None where the time at 2n is within the bound of the time at n,
    else the two times."""
    small = large = 0.0
    for _ in range(TRIES):
        small, large = cpu(hook, build(n)), cpu(hook, build(2 * n))
        if large <= GROWTH_BOUND * small + SLACK:
            return None
    return f"{small:.3f} s at n, {large:.3f} s at 2n"


def lexings(hook: Any, command: str) -> int:
    """How many times `broken_rules` lexes text to read `command`."""
    count = 0
    run = hook.Lexer.run

    def counted(self: Any) -> Any:
        nonlocal count
        count += 1
        return run(self)

    hook.Lexer.run = counted
    try:
        hook.broken_rules(command)
    finally:
        hook.Lexer.run = run
    return count


def main() -> None:
    hook = load()
    wrong = []
    for command, expected in CASES:
        named = set(hook.broken_rules(command))
        if named != expected:
            wrong.append(f"{command!r}: named {sorted(named)}, not {sorted(expected)}")
    # each refusal names a file that holds its section, as a bold rule or
    # a heading, and the heading above it
    root = HOOK.parent.parent
    for key, (_, section, file) in hook.RULES.items():
        text = " ".join((root / file).read_text().split())
        rule, above = re.findall(r"\*([^*]+)\*", section)
        if f"**{rule}" not in text and f"# {rule}" not in text:
            wrong.append(f"{key}: {file} holds no rule *{rule}*")
        if f"# {above}" not in text:
            wrong.append(f"{key}: {file} holds no heading *{above}*")
    for label, build, n in GROWTH:
        named = set(hook.broken_rules(build(n)))
        failed = growth(hook, build, n)
        if named or failed:
            wrong.append(f"{label}: named {sorted(named)}, {failed}")
    command, evals_name = EVALS
    count = lexings(hook, command)
    if count != 1 or hook.broken_rules(command) != evals_name:
        wrong.append(f"{command[:20]!r}…: lexed {count} times")
    for stdin, code, section in EVENTS:
        try:
            run = subprocess.run(
                [sys.executable, "-I", str(HOOK)],
                input=stdin,
                capture_output=True,
                text=True,
                check=False,
                timeout=EVENT_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            wrong.append(f"{stdin}: no answer in {EVENT_TIMEOUT} s")
            continue
        names = "every-role.md" in run.stderr and "*Where you work*" in run.stderr
        if (run.returncode, run.stdout, names) != (code, "", section):
            wrong.append(f"{stdin}: exit {run.returncode}, stderr {run.stderr!r}")
    if wrong:
        print("\n".join(wrong))
    sys.exit(1 if wrong else 0)


if __name__ == "__main__":
    main()
