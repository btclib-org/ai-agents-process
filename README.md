# ai-agents-process

The process the btclib-org maintainers follow with the coding agents
[Claude Code](https://claude.com/claude-code) and
[Codex](https://developers.openai.com/codex):

- `skills/btclib-iss/SKILL.md` — the `/btclib-iss` skill, from an issue
  to an open pull request, followed as its author;
- `skills/btclib-pr/SKILL.md` — the `/btclib-pr` skill, from an open
  pull request to the decision to approve, and to `main`;
- `skills/btclib-pr/review-quota.md` — what `/btclib-pr` does while the
  review bot's quota is exhausted, read only then;
- `skills/btclib-inbox/SKILL.md` — the `/btclib-inbox` skill, the issues
  and pull requests of the organization that wait on the maintainer,
  which only reads;
- `skills/btclib-inbox/measure.sh` — the script `/btclib-inbox` runs to
  read them;
- `scripts/test-inbox-measure.sh` — `sh scripts/test-inbox-measure.sh`
  checks what `skills/btclib-inbox/measure.sh` prints on answers a
  stand-in for `gh` serves; it needs `jq` on the `PATH`, as
  `measure.sh` does;
- `skills/btclib-table/SKILL.md` — the `/btclib-table` skill, one table
  of every repository of the organization, which only reads;
- `skills/btclib-table/measure.sh` — the script `/btclib-table` runs to
  read that table;
- `skills/night-mode/SKILL.md` — the `/night-mode` skill, which turns
  night mode on or off in any session, or says whether it is on;
- `skills/funds-recovery/SKILL.md` — the `/funds-recovery` skill, which
  helps somebody find the funds of a mnemonic with `seed-scan`, working
  on its public bundle alone and never on the mnemonic;
- `process/every-session.md` — the rules every session follows; its
  opening says when it is read;
- `process/every-role.md` — what binds every role of `/btclib-iss` and
  `/btclib-pr`; its opening says which role reads which file;
- `process/writing.md` — the writer's rules, from before it starts to
  the commit it hands over;
- `process/local-review.md` — how the local review rounds run;
- `process/orchestration.md` — the orchestrator's rules and the wrap-up;
- `process/btclib-common.md` — a table of the file that holds each
  section a citation of it names;
- `process/night-mode.md` — how night mode is turned on and off, and
  what a session follows while it is on, read when it is turned on;
- `process/load-generator.md` — how a timing measurement takes every
  slot of the gate lock, read before running one;
- `process/replay-set.md` — the pull requests a change to the reviewer
  is tried on before it lands;
- `agents/designer.md` — the agent that weighs how an issue could be
  answered, before a writer starts;
- `agents/writer.md` — the agent that writes a change in its own
  worktree;
- `agents/reviewer.md` — the agent that reviews it at fresh context;
- `agents/*.toml` — the same agents for Codex, which
  `scripts/agents-toml.py` writes from the `.md` files;
- `hooks.json` and `scripts/git-c-allow.py` — the hook that approves a
  fixed set of `git -C` commands;
- `scripts/gate-lock.sh` — the gate lock every worker of every session
  takes before its heavy gates, and `gate_peak`, which records the peak
  memory and the wall time of what runs through it: the gates of the
  lock's block, and the reviewers an orchestrator starts as a command;
- `scripts/test-gate-lock.sh` — `sh scripts/test-gate-lock.sh` shows
  sessions taking that lock's slots and waiting while every slot is
  held, and `gate_peak` recording a peak;
- `scripts/gate-sandbox.sb` — the sandbox an outside contributor's gates
  run in, as `process/writing.md`'s *The gates* says;
- `scripts/test-gate-sandbox.sh` — the gate blocks of
  `process/writing.md`'s *The gates* on macOS, with a gate that writes a
  repository under a gitlink's directory and forges the clean-tree
  check: which git calls outside the sandbox read that repository, and
  whether the check refuses the forgery, run by the `test-gate-sandbox`
  hook;
- `scripts/test-gate-blocks.sh` — blocks of `process/writing.md`'s *The
  gates* under each shell it finds: the trees `gated_tree` refuses, a
  signal while it runs, the hooks block under `set -u`, the hooks block,
  the docs build's check and the sandbox's hooks gate under noclobber,
  the gate lock's block with hooks or a next gate that write a tracked
  file, and the block for hooks whose run carries over, on a staged tree
  and then on its commit, run by the `test-gate-blocks` hook;
- `scripts/sweep.sh` — the script that removes the directory of a piece
  of work, which `process/every-role.md`'s *Debris goes when its work
  ends* runs;
- `scripts/test-sweep.sh` — the fixture directories `sweep.sh` must
  remove and must refuse, run by the `test-sweep` hook;
- `scripts/test-git-c-allow.py` — the commands `git-c-allow.py` must
  approve and must refuse, run by the `test-git-c-allow` hook;
- `scripts/pretooluse-rules.py` — the hook that refuses a command
  breaking a rule `process/every-role.md`'s *Clients* names;
- `scripts/test-pretooluse-rules.py` — the commands
  `pretooluse-rules.py` must refuse and must let through, run by the
  `test-pretooluse-rules` hook;
- `scripts/port-check.py` — the check of a tree's batch of ports against
  the standard (`/btclib-iss`'s *Ports of the standard*);
- `scripts/test-port-check.py` — the fixture repositories
  `port-check.py` must answer, run by the `test-port-check` hook;
- `scripts/pointer-files.py` — the check that a pointer to another
  file's section names that file, as `process/every-role.md`'s opening
  says, run by the `pointer-files` hook;
- `scripts/test-pointer-files.py` — the trees `pointer-files.py` must
  answer, run by the `test-pointer-files` hook;
- `scripts/placeholder-last.py` — the check that a bare placeholder of a
  shell fence is the last word of its line, run by the
  `placeholder-last` hook;
- `scripts/test-placeholder-last.py` — the fences `placeholder-last.py`
  must answer, run by the `test-placeholder-last` hook;
- `scripts/assignment-fence.py` — the check that a value the reader sets
  shares no shell fence with a line that writes, run by the
  `assignment-fence` hook;
- `scripts/test-assignment-fence.py` — the fences `assignment-fence.py`
  must answer, run by the `test-assignment-fence` hook.

`process/every-role.md`'s opening says how these files divide the
process, and its *Clients*, with `process/orchestration.md`'s *Agents in
each client* and *Starting the reviewer in the other client*, says what
differs between the two agents.

## Prerequisites

- Claude Code and Codex, both: a session runs in one, and its pull
  requests' fresh reviewer in the other (`process/local-review.md`'s *A
  pull request's rounds*).
- `gh`, logged in (`gh auth login`).
- CodeRabbit's CLI, logged in by the maintainer (`coderabbit auth
  login`), which `process/writing.md`'s *Sourcery and CodeRabbit before
  a push* runs.
- `uv`.
- `jq` on the `PATH`, which commands of the files under `process/` run.
- `python3` on the `PATH`, which runs the hooks' scripts.
- git signing your commits: `commit.gpgsign = true` and a key registered
  on GitHub. The process signs every commit it writes
  (`process/writing.md`'s *Signed and signed off*).

## Setup

Clone the repository, and export its path as `PROCESS`, in this shell
and where every later shell reads it, `~/.zshenv` for zsh: each command
either agent runs is a new shell, and the process finds its files
through `$PROCESS`. The clone can sit at any absolute path without `"`,
`$`, `` ` ``, `\`, `|` or `&`, which the hooks below cannot carry;
`~/Git/ai-agents-process` is only an example:

```shell
export PROCESS=~/Git/ai-agents-process
```

```shell
printf 'export PROCESS=%q\n' "${PROCESS:?}" >> ~/.zshenv
```

```shell
git clone https://github.com/btclib-org/ai-agents-process "${PROCESS:?}"
```

Then link its files where each agent reads them. Each link holds the
clone's path as it was when the link was made: a clone moved later
leaves the links pointing at nothing; remove them and make them again
from the new path. `ln -s` refuses to overwrite an existing file: move
any file of the same name you already have out of the way first.

### Claude Code

Claude Code reads its files from `$CLAUDE_CONFIG_DIR` where that is set,
and from `~/.claude` otherwise. Run these once for each configuration
directory your sessions use, with `CLAUDE_CONFIG_DIR` set to it:

```shell
mkdir -p "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills" \
  "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/agents"
```

```shell
ln -s "${PROCESS:?}/skills/btclib-iss" "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/btclib-iss"
```

```shell
ln -s "${PROCESS:?}/skills/btclib-pr" "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/btclib-pr"
```

```shell
ln -s "${PROCESS:?}/skills/btclib-inbox" "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/btclib-inbox"
```

```shell
ln -s "${PROCESS:?}/skills/btclib-table" "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/btclib-table"
```

```shell
ln -s "${PROCESS:?}/skills/night-mode" "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/night-mode"
```

```shell
ln -s "${PROCESS:?}/skills/funds-recovery" "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/funds-recovery"
```

```shell
ln -s "${PROCESS:?}/agents/writer.md" "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/agents/writer.md"
```

```shell
ln -s "${PROCESS:?}/agents/reviewer.md" "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/agents/reviewer.md"
```

```shell
ln -s "${PROCESS:?}/agents/designer.md" "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/agents/designer.md"
```

Add the hooks under `hooks` in that directory's `settings.json`, with the
clone's path written out for `$PROCESS`, since a hook's shell need not
have it. Claude Code runs them before every Bash call:

```json
"PreToolUse": [
  {
    "matcher": "Bash",
    "hooks": [
      {
        "type": "command",
        "command": "\"$PROCESS/scripts/git-c-allow.py\"",
        "timeout": 5
      },
      {
        "type": "command",
        "command": "python3 -I \"$PROCESS/scripts/pretooluse-rules.py\"",
        "timeout": 5
      }
    ]
  }
]
```

Check it in a new session: `echo "$PROCESS"` prints the clone's path,
`/btclib-iss`, `/btclib-pr`, `/btclib-inbox`, `/btclib-table`,
`/night-mode` and `/funds-recovery` are listed among the skills,
`/agents` lists `writer`, `reviewer` and `designer`, `/hooks` lists the
`PreToolUse` hooks, and the command `cd /` is refused.

### Codex

```shell
mkdir -p ~/.agents/skills ~/.codex/agents
```

```shell
ln -s "${PROCESS:?}/skills/btclib-iss" ~/.agents/skills/btclib-iss
```

```shell
ln -s "${PROCESS:?}/skills/btclib-pr" ~/.agents/skills/btclib-pr
```

```shell
ln -s "${PROCESS:?}/skills/btclib-inbox" ~/.agents/skills/btclib-inbox
```

```shell
ln -s "${PROCESS:?}/skills/btclib-table" ~/.agents/skills/btclib-table
```

```shell
ln -s "${PROCESS:?}/skills/night-mode" ~/.agents/skills/night-mode
```

```shell
ln -s "${PROCESS:?}/skills/funds-recovery" ~/.agents/skills/funds-recovery
```

```shell
ln -s "${PROCESS:?}/agents/writer.toml" ~/.codex/agents/writer.toml
```

```shell
ln -s "${PROCESS:?}/agents/reviewer.toml" ~/.codex/agents/reviewer.toml
```

```shell
ln -s "${PROCESS:?}/agents/designer.toml" ~/.codex/agents/designer.toml
```

Codex reads its hooks from `~/.codex/hooks.json`. Write it from
`hooks.json`, with the clone's path for `$PROCESS`. Where the file
exists already, add the `PermissionRequest` entry to it by hand instead.
Codex runs the hook when a command needs approval, and refuses the
`PreToolUse` answer Claude Code uses:

```shell
sed 's|\$PROCESS|'"${PROCESS:?}"'|' "${PROCESS:?}/hooks.json" > ~/.codex/hooks.json
```

Codex reads `~/.codex/AGENTS.md` in every session. Point it at the
process, so that a session started without a skill still finds it:

```shell
printf 'Work in a btclib-org repository follows %s, read whole first.\n' \
  "${PROCESS:?}/process/every-role.md" >> ~/.codex/AGENTS.md
```

Check it in a new session: `echo "$PROCESS"` prints the clone's path,
`/skills` lists `btclib-iss`, `btclib-pr`, `btclib-inbox`,
`btclib-table`, `night-mode` and `funds-recovery`, Codex names
`writer`, `reviewer` and `designer` when asked which custom agents it
can spawn, and `/hooks` lists the `PermissionRequest` hook. Codex runs a
hook only once you have trusted it there.

### A machine set up before the skills

A machine set up before the commands became skills has links into the
clone that the process no longer reads. Remove the ones it has, then
make the links above. Like the links, run these once for each
configuration directory your sessions use, with `CLAUDE_CONFIG_DIR` set
to it:

```shell
rm "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/commands/btclib-iss.md" \
  "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/commands/btclib-pr.md" \
  "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/commands/btclib-table.md"
```

```shell
rm "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/process/btclib-common.md" \
  "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/scripts/gate-lock.sh"
```

A machine set up before the commands were split also has
`commands/btclib-org.md` there:

```shell
rm "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/commands/btclib-org.md"
```

A hook in a `settings.json` that runs a copy of `git-c-allow.py`
outside the clone is pointed at the clone's, as above.

## Use

```text
/btclib-iss <issue URLs or numbers>
```

takes issues to open pull requests, locally reviewed, and follows them
as their author.

```text
/btclib-pr [pull request URLs or numbers]
```

answers what the reviewers raised, gets CI green, and takes them to the
decision to approve and to `main`. With no argument it sweeps the
organization's open pull requests: by day it proposes which to work, at
night it works them without asking, as `skills/btclib-pr/SKILL.md`'s
*The sweep* says.

```text
/btclib-inbox [--since <hours> | <time>]
```

lists the issues and pull requests of the organization that wait on the
maintainer, newest first, marking those new since the time `--since`
gives, 24 hours back by default. Where the session can read his mail, it
also lists his threads with `btclib.org`. It only reads.

```text
/btclib-table
```

shows one table of every repository of the organization that is not
archived: open issues, open pull requests, CI and README badge status,
the last release, and whether a new one is due. It only reads.

```text
/night-mode [on|off|status]
```

turns night mode on or off, in any session, or says whether it is on,
since when, and what it has deferred so far.
`skills/night-mode/SKILL.md` says what each word does, and what the
command does with none; `process/night-mode.md` says what the night
does.

```text
/funds-recovery [the bundle's path]
```

helps somebody find the funds of a mnemonic with `seed-scan`. They run
`seed-scan identify` in a terminal of their own, and the session works
on the public bundle it writes, never on the mnemonic.
`skills/funds-recovery/SKILL.md` says what the session refuses, and what
its answer states.

In Codex each starts with `$` instead of `/`: `$btclib-iss`.

`/btclib-iss` and `/btclib-pr` work in every repository of `btclib-org`;
`process/every-role.md`'s *Where you work* says how the repository is
named. `/btclib-pr`'s *The decision* and *Landing* say when a session
approves and when it lands, `--land` included.

## Updating

Pull, with `PROCESS` exported as in *Setup*:

```shell
git -C "${PROCESS:?}" pull --ff-only
```

A skill or agent added since the machine was set up has no link yet:
make it as *Setup* says. *A machine set up before the skills* says what
an older machine removes. A change to `hooks.json` reaches Codex only once
`~/.codex/hooks.json` is updated from it as *Setup* says, and trusted
again in `/hooks`.

The links then point at the new text. Do not edit the clone the links
point at: change the process through a pull request from a worktree,
reviewed by another person, like any other btclib-org repository.
[AGENTS.md](https://github.com/btclib-org/ai-agents-process/blob/main/AGENTS.md)
shows the worktree commands.

## Contributing

Software development in btclib-org is mainly LLM-driven, but human
beings are welcome too. A contribution must have been read and
understood by the person who submits it.
[`CONTRIBUTING.md`](https://github.com/btclib-org/ai-agents-process/blob/main/CONTRIBUTING.md#working-with-an-llm)
has the rules.

## Status

<!-- Section 2 of the organization's standard says which badges sit here. -->
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/btclib-org/ai-agents-process/main.svg)](https://results.pre-commit.ci/latest/github/btclib-org/ai-agents-process/main)
[![lint](https://github.com/btclib-org/ai-agents-process/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/btclib-org/ai-agents-process/actions/workflows/lint.yml?query=branch%3Amain)
[![links](https://github.com/btclib-org/ai-agents-process/actions/workflows/links.yml/badge.svg?branch=main)](https://github.com/btclib-org/ai-agents-process/actions/workflows/links.yml?query=branch%3Amain)
