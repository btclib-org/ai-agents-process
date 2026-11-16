# The btclib-org process: what binds every role

Two skills carry work in every repository of `btclib-org`:

- `/btclib-iss` takes issues to open pull requests, locally reviewed,
  and follows them as their author;
- `/btclib-pr` takes open pull requests through their reviews and CI to
  the decision to approve, and to `main`.

`/btclib-pr`'s *The decision* and *Landing* say when a pull request is
approved and when it lands.

This file binds both, with three files beside it: `writing.md`,
`local-review.md` and `orchestration.md`. The four hold the rules the
skills share, or name the file under `process/` that holds them, except
those `/btclib-iss`'s *Following it* reads in `/btclib-pr`. A section of
the process they name in italics with no file is in one of the four.
Both skills open by having `process/every-session.md` and the four read
whole, and each holds only what is its own. The `writer`, `reviewer` and
`designer` agents are generic: the brief names `every-session.md`, the
skill and the files of the four that its role reads, and they read
`every-session.md` whole and the files and sections the maps give them.
Change a rule in the file that holds it or in the skill where it fires,
not in an agent.

**Which sections are yours.** A heading that is not yours is genuinely
not yours; one that is cannot be skipped as somebody else's.

- **Everybody**: `every-session.md` and this file, whole.
- **The writer**: `writing.md`, whole, and the sections of the skill its
  brief names.
- **The reviewer**: `local-review.md`, whole; `writing.md`'s *Writing
  work*, whole, which it judges; and the sections of the skill its brief
  names.
- **The designer**: `writing.md`'s *Before starting*, its first bullet,
  and the sections of the skill its brief names.
- **The orchestrator**: the four files, whole, and all of its skill.

**Which file wins.** Where two texts state the same point differently,
the more specific one wins: a repository's own `AGENTS.md`,
`CONTRIBUTING.md` and `REVIEWING.md` over a skill, a skill over this
file and the files under `process/` it names, and those over a client's
global instructions (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`). A
repository's own file that has drifted from the standard in
`btclib-org/.github` is a defect, tracked there, and the standard wins
until it is brought in line. The process, a repository's own files
included, wins over the generic agents, except that on the model and its
effort the agent definition is the more specific text (*Models*), and
each agent's *What holds whatever the process* holds as its heading
says. A brief never overrides the process. Any other contradiction is
still a defect, and it is fixed in the more general file.

**Three roles this file names.** *The human* is whoever runs the
session: they answer its questions and receive its reports, and the
session acts through their `gh` login and their signing key. *The
author* of a pull request is the login that opened it. *The maintainer*
is the one `btclib-org/.github`'s `GOVERNANCE.md` names, who takes the
decisions the written rules leave open. They may be the same person.
This prints the maintainer's login, read from that file's *Roles*:

```shell
gh api -H 'Accept: application/vnd.github.raw' \
  repos/btclib-org/.github/contents/GOVERNANCE.md \
  | sed -n '/^- \*\*The maintainer\*\*/,/^- /p' \
  | grep -o 'https://github\.com/[A-Za-z0-9-]*' | head -n 1 | sed 's|.*/||'
```

## How an issue and a pull request are named

An issue is **`ISS owner/repo#123`** and a pull request is
**`PR owner/repo#45`**, wherever you write, with the repository even
where it is the one you work in. Two trackers hold the same number, and
GitHub numbers issues and pull requests together: the repository says
which tracker, the prefix says which kind.

- **Where GitHub renders the text** — an issue, a pull request, a
  comment, a commit message — write it plain:
  `ISS btclib-org/btclib#123`. GitHub links the qualified form and shows
  its title and kind on hover. It does not link `btclib#123`.
- **Where it does not** — a report to the human, a brief, a note — the
  token is a link, and inside `btclib-org` the repository's name alone:

  ```text
  [ISS btclib#123](https://github.com/btclib-org/btclib/issues/123)
  [PR bitcoin/bitcoin#33000](https://github.com/bitcoin/bitcoin/pull/33000)
  ```

A workflow run, a job or an environment approval named to the human
carries its URL.

A pull request named to the human — in a decision, a report or a
table — carries its diff balance, written `2 files, +50/-4`: the files
changed, then the lines added and removed (`1 file` when it is one).
For a pull request the counts are the forge's, `gh pr view` or
`gh pr list` with `--json additions,deletions,changedFiles`. The forge
counts against the branch the pull request targets, so a stacked pull
request is measured against its parent. A branch not yet a pull
request takes the same counts from
`git diff --shortstat <base>...<head>`, `<base>` being the branch it
will target.

A bare `#123` stands only where the forge or the standard fixes the
form: the closing keyword in a pull request body, and the `(closes #N)`
or `(issue #N)` on the subject that lands (*Citations and closing
keywords*). A repository's own files follow the standard's *A reference
to another repository is qualified*.

## What binds every role

These bind every role alike.

### Clients

The process runs in Claude Code and in Codex. `$PROCESS` is the path of
this repository's clone, exported as `README.md`'s *Setup* says, and
the process names its own files by their path under it. Claude Code's
`~/.claude` in this file is `$CLAUDE_CONFIG_DIR` where that is set.

- **Skills.** Claude Code reads them from `~/.claude/skills/`, Codex
  from `~/.agents/skills/`. Claude Code runs one as `/btclib-iss`, Codex
  as `$btclib-iss`; this text writes the first form. Claude Code puts
  the words after the skill's name in place of `$ARGUMENTS`. Codex
  leaves `$ARGUMENTS` as written, and it means the same words.
- **The reviewer in the other client** (*A pull request's rounds*) is
  started from the shell (`orchestration.md`'s *Starting the reviewer in
  the other client*), and reviews a detached worktree at the sha. Its
  brief holds what a fresh reviewer's brief holds, the bot's prompt
  included. A new run of the same command, whose brief adds its last
  verdict and the sha that verdict named, is how it is resumed: for *The
  rounds* it is the same reviewer, though a new process. A run that
  times out exits `124`.

  In Codex it runs under `workspace-write` with one writable root: its
  own directory, `<work>/<name>`, which is also its working directory.
  There it writes the inputs of *Every reviewer tries to break the
  change* and runs them offline. Where the worktree holds a `uv.lock`,
  they run with `uv run --project <wt>`, from the worktree's `.venv`,
  which the session syncs, and from a `UV_CACHE_DIR` inside the
  reviewer's directory, which holds what that sync had to download.
  Otherwise they run with `uv run --no-project`, on the standard library
  alone. An input that needs a package these do not hold is named in the
  verdict as not run. The session runs it after reading it, where and as
  it runs the gates (*The gates*), and resumes the reviewer with its
  result on the record (*The rounds*). A write anywhere else fails with
  `Operation not permitted`, the worktree it reviews included, and so do
  `git fetch` and `git merge-tree --write-tree`, which write in the git
  directory, and a heredoc in the `zsh` Codex runs commands in, which
  puts its temporary file under `/tmp`. `git log --format=%G?` reads a
  signed commit as `N`, and the network is off (`orchestration.md`'s
  *Starting the reviewer in the other client*). The reviewer relies on
  the runs its brief carries on the record, says so, and reads the
  worktree with `git -C <wt> show` and `git -C <wt> diff` at shas, which
  the sandbox allows.

  An input a reviewer names as not run may be one the session cannot run
  either. The branch then goes to the human as one decision
  (`every-session.md`'s *When the human has to decide*), which carries
  the input and why no one could run it. One such input needs a package
  that an outside contributor's branch adds: the sandbox of *The gates*
  does not hold it, and CI, on which *The gates* then relies, runs no
  reviewer's input. The branch is held as `every-session.md`'s *A hold
  is recorded* says. The human's answer stands in for the input's
  result: the reviewer's resumed run, or the dedicated reviewer that
  takes over from it (`orchestration.md`'s *Where the other client is
  unavailable*), gets the answer on the record in its place. The pull
  request body records the decision and the answer.

  A Claude Code reviewer's Bash commands run in Claude Code's own
  sandbox, so that the inputs it writes and runs are held as a Codex
  reviewer's are, since an input runs the branch's code: they write only
  in the reviewer's directory, which is its working directory, and in a
  temporary directory of the run's own, and reach no host. The reviewer
  reads the worktree and runs its inputs with `uv run` the same way. An
  input that needs a package neither the worktree's `.venv` nor the
  standard library holds is handled as a Codex reviewer's is, above.

- **Hooks.** Claude Code reads them from `~/.claude/settings.json`,
  Codex from `~/.codex/hooks.json`. Both run `scripts/git-c-allow.py`.

  Claude Code also runs `scripts/pretooluse-rules.py`. It refuses a Bash
  command that breaks a rule of these sections, and names the section
  and the file that holds it: *Never open a command with `cd`*, *The
  machine is shared*, *The forge's quota is shared* and *A Bitcoin Core
  program runs on a data directory of the scratch directory*, in
  `every-session.md`; *Never the primary checkout, never `git stash`,
  never a push to `main`* and *A worktree for a pull request is added at
  its `headRefOid`*, in this file; *Look at the free disk*, *Sourcery
  and CodeRabbit before a push*, *A force-push with lease, to a branch
  the session works only* and *Signed and signed off*, in `writing.md`.
  Its `RULES` says what it refuses of each. The sections stay the rule,
  and the hook is a net under them: it refuses what the command's words
  show for certain, so a command it lets through may still break one. It
  also refuses some spellings that break no rule, which its docstring
  names. Codex runs no such hook, so its own sessions have the sections
  alone.

  A command the hook refuses is written again as the section it names
  asks: the refusal is that section's, not a denied permission (*A
  denied permission is a stop*). A refused command that breaks no rule,
  and that the script's docstring does not name, is a defect of the
  script, filed as *Collateral* says.

- **Git writes under Codex.** Its `workspace-write` sandbox keeps each
  writable root's `.git`, and the git directory it points to, read-only,
  and `~/.gnupg` outside the workspace. Each git write — `worktree add`
  and `remove`, a commit, an amend, a rebase, a push — runs outside the
  sandbox, through an escalation request or a `.rules` entry that allows
  it (`orchestration.md`'s *Escalation under Codex*), and never with
  signing turned off (*Signed and signed off*).

### Shell, checkouts and prose

This section is in `every-session.md`, beside this file.

### Where you work

- **The repository is named, never inferred.** An issue or pull request
  URL names it, and so does `<owner>/<repo>#<n>`; a bare number does not.
  Neither the session's starting directory, nor an additional working
  directory, nor `pwd` says which repository the work is for, and the
  wrong tree answers every read promptly and correctly. Where the human
  named none, ask **before any tracker is read**. A worker gets it in
  its brief; where the brief's tree and the issue do not belong together,
  stop and report.
- **Your own worktree, from origin/main, from the first edit**, in the
  directory of its piece of work (*The scratchpad is shared*), named
  **`wt-<tracker>-<issue>-<repo>-<role>`**, most general part first:
  `tracker` because an issue number is unique only within one tracker;
  `issue` because worktrees are keyed on their basename in the one shared
  `.git`, and a collision there is silent; `repo` because one issue
  ported to several trees shares one scratchpad; `role` for a writer and
  its reviewer holding one at once. `ISS btclib-org/.github#255` worked
  in `btclib` by a writer is `wt-github-255-btclib-writer`. A pull request
  stands in for the issue where there is none: `wt-btclib-pr812-btclib-writer`.
- **Never the primary checkout, never `git stash`, never a push to
  `main`.** `refs/stash` is shared across worktrees and sessions: commit
  to your own branch instead.
- **The primary checkout is not written — except the fast-forward that
  brings it forward (`every-session.md`'s *Shell, checkouts and prose*)
  — and an accident in it is undone only where it is provably yours**,
  as `orchestration.md`'s *Orchestration* says.
- **Every command that writes carries an explicit absolute path.** Shell
  state does not survive between calls (`every-session.md`'s *Never open
  a command with `cd`*), so `WT=…` in one call is empty in the next. A
  fresh worktree and the checkout are byte-identical, so reads look
  right and only the write shows it. Use `git -C <abs>`, `env -C <abs>`,
  absolute paths in every edit, an explicit target for `git clone`;
  never a relative `>` or a `sed -i` on a bare filename.
- **A command can write without your meaning it to, and `.gitignore`
  hides it.** `compileall`, a linter cache, a build inspected in place
  all leave files `git status` does not show. Ask even read-only
  questions from a worktree; where it has happened, look for the
  artefact by name. What the session itself just created there —
  gitignored, identified by name and by a time inside the session — is
  removed and reported; anything older, or not certainly the session's,
  is reported and left.
- **The scratchpad is shared, so each piece of work has one directory in
  it.** Everything a session creates for one issue, or for a pull
  request where there is none, sits under one directory,
  `<scratchpad>/<tracker>-<issue>-<repo>/`, which the process calls
  `<work>`. Its parts are named as the worktree's are (*Your own
  worktree*). The exception is a temporary file or directory that
  `mktemp` makes and that goes as soon as the command using it ends, as
  `writing.md`'s docs-build list does and as `<tmp>` does, which
  `orchestration.md`'s *Starting the reviewer in the other client* keeps
  on a short path for a Claude Code reviewer's run and the session
  removes once that run ends. `<work>` holds:

    - each worktree, under the whole name *Your own worktree* gives it;
    - each reviewer's directory in the other client (*Clients*), under a
      `<name>` that no role and no other reviewer in `<work>` uses, and
      the files `orchestration.md`'s *Starting the reviewer in the other
      client* puts beside it;
    - the gate's basetemp (*The gates*) and the findings record's file
      (`orchestration.md`'s *The findings record*);
    - everything else a role writes, in its own directory,
      `<work>/<role>/`, which the process calls that role's scratch
      directory, `<scratch>`, each file under a name that is its own
      (`msg-<branch>.txt`).

  A role makes its `<scratch>` before the first file it writes there,
  such as the base pin of *`refs/remotes/origin/main` is shared by every
  worktree*:

  ```shell
  mkdir -p <work>/<role>
  ```

  What the orchestrator keeps for the whole session belongs to no piece
  of work and stays in `<scratchpad>/orchestrator/`, as the sha of *The
  process is re-read when `main` changes it* does. So do the files of a
  text that belongs to no issue yet, as the draft of an issue still to
  be filed and its findings record.

  **Read back from the repository what you wrote from a file**:
  `git show -s --format=%B HEAD` after a `-F`, the committed file after a
  fixer.
- **A deletion under test prints its path first.** Where a test, a
  fixture or a rehearsal runs `rm` or another deletion on a path that a
  tilde, a variable or a glob builds, expand it once, in the shell that
  deletes, into a variable (an array for a glob, `set --` in POSIX
  `sh`), and print each value with `printf '[%s]\n'`. Run the deletion
  on those values, never on the expression again, and only where the
  `realpath` of every value starts with the `realpath` of your scratch
  directory and a `/`, and the `realpath` of the directory that holds
  it is your scratch directory or inside it. A path that `realpath`
  cannot resolve fails the check. Compared as text, a path inside your
  scratch directory can pass through a symbolic link that leads out of
  it; resolved, a link outside it can lead in.

  A tilde can escape a fixture's `HOME`: after a script assigns `HOME`,
  Homebrew's bash can expand `~` to an earlier home, while `$HOME`
  prints the new value
  ([ISS ai-agents-process#273](https://github.com/btclib-org/ai-agents-process/issues/273)).

  A cleanup is not under test: the deletion of a file or directory that
  the same script or session made, or of a path below it through no
  symbolic link and no `..`, on a path built from the variable that
  holds it or from any variable set from it, as `rm -r "$tmp"` after
  `tmp=$(mktemp -d)` or `rm -rf "${clone:?}"`.
- **A measurement that must hold is taken against shas**, `git show
  <sha>:<path>`, `git diff` and `git merge-tree` on explicit shas, not
  from a working file another session might share.
- **A worktree for a pull request is added at its `headRefOid`**, or at
  the sha `git ls-remote origin refs/pull/<n>/head` prints, and the
  report names that sha. Never at `FETCH_HEAD`: the next fetch in the
  same checkout overwrites it, another session's included. A fetch that
  another fetch has locked out (`cannot lock ref`) is retried.
- **Debris goes when its work ends, not at the wrap-up**, because a long
  session otherwise fills the disk. A worktree goes, with its basetemp
  and build directories, once the session hands the pull request over to
  whom it waits on, or it lands or closes: a clean, pushed worktree is
  recreated in seconds if review sends the branch back, and one with
  uncommitted or unpushed work stays (*Before removing or discarding
  anything that could be work*). A gate's basetemp and build directories
  go once that branch's gates are done. A reviewer's worktree, exports,
  repositories and reports go before it hands back its verdict, and a
  writer's clones as `writing.md` says where it makes them.

  **A piece of work's `<work>` goes when the last pull request of its
  issue lands or is closed**, or when the pull request that stands in for
  the issue does. It is the last only where the searches of *Before
  starting* find no other open pull request for the issue, and `<work>`
  holds no worktree on another branch and no file named for one, as
  `msg-<branch>.txt` or `findings-<branch>.md`. The orchestrator first
  fetches origin in the repository of each linked worktree directly in
  `<work>`, and there the head of each pull request opened from a branch
  one of those worktrees holds. An issue ported to several trees has a
  `<work>` for each (*Your own worktree*), so each fetches the pull
  requests of its own repository, not only the one that ended. The
  script counts a ref of origin only where the repository holds its
  commit, and a landing's commit is made on the forge, as is a head that
  a bot moved on or that was pushed from another clone; a worktree whose
  head was not fetched is refused as holding an unpushed commit. The
  default fetch does not bring `refs/pull/*`:

  ```shell
  git -C <checkout> fetch origin
  ```

  For each worktree `<wt>`, with `<owner>/<repo>` the repository its
  origin names, the `gh` command prints the numbers of the pull requests,
  open or not, of the branch the worktree holds, read from git rather
  than typed, since a branch name may hold `;` or `>`. A detached
  worktree holds no branch, so nothing is looked up for it and a commit
  it holds that origin lacks leaves it refused. The lookup does not
  filter on the head repository, so a fork's branch of the same name
  adds a number too, which is harmless: the fetch reads origin's own
  `refs/pull/<n>/head`, and a commit that ref reaches is on origin. The
  fetch, run for each `<n>`, writes only `FETCH_HEAD` and objects:

  ```shell
  wt=<wt>
  repo=<owner>/<repo>
  ```

  ```shell
  branch=$(git -C "${wt:?}" branch --show-current)
  [ -z "$branch" ] || gh pr list --repo "${repo:?}" --head "$branch" \
    --state all --json number --jq '.[].number'
  ```

  ```shell
  git -C <checkout> fetch origin refs/pull/<n>/head
  ```

  It then moves each findings record at the top of `<work>`,
  `findings-*.md`, to `<scratchpad>/orchestrator/` under `<work>`'s name,
  where `orchestration.md`'s *The findings record* reads it after the
  landing. `mv -n` replaces no record already there, and the script
  refuses a `<work>` that still holds one anywhere, so that a name taken
  stops the sweep with both records kept:

  ```shell
  work=<work>
  ```

  ```shell
  while [ "${work:?}" != "${work%/}" ]; do work=${work%/}; done &&
    keep=${work%/*}/orchestrator/${work##*/} &&
    mkdir -p "$keep" &&
    find "$work" -maxdepth 1 -name 'findings-*.md' -exec mv -n {} "$keep"/ \;
  ```

  Last it runs `scripts/sweep.sh`, whose header says what it refuses, and
  names each refusal in its report to the human. A `<work>` that holds
  any other repository is refused and left for the human, since the
  script runs git in no repository it cannot tell is a linked worktree of
  the session's:

  ```shell
  work=<work>
  ```

  ```shell
  sh "${PROCESS:?}/scripts/sweep.sh" work "${work:?}"
  ```

- **The orchestrator, never a writer, sweeps what a session that no
  longer runs left**, when the disk is short (*Before starting*). It
  removes only a worktree that is clean and pushed, and that session's
  scratch where none of its worktrees stays, never another live
  session's (*Before removing or discarding anything that could be
  work*). Where it is not certain a session has ended, it asks the human
  (*A branch left by a session that no longer runs*).
- **Long jobs run in the background with a timeout; kill what you
  started.** Do not end your turn waiting for one — nothing wakes a
  stopped agent. Poll within the same turn, or hand back saying what
  is outstanding. Find your job by its worktree's absolute path, written
  out (`pgrep -f '/abs/path/wt-….*pytest'`), never by command name. Its
  completion notification says the shell exited, not its children: each
  gate writes its exit code to the log (`EXIT_<gate>=$?`) and a terminal
  marker as its last line, and those are read, never the wrapper's code.
- **A denied permission is a stop.** No substitute for the refused act
  (`find -delete`, the same `rm` without the flag, `shutil.rmtree`),
  except the `-r2` fallback for a refused force-push in *Committing and
  rebasing*: the
  test is whether the thing is still there afterwards. No delegating it
  to another worker. Put the exact command in your report and in a
  comment on the issue, and tell the human. Their word does not lift the
  classifier's refusal, so a retry is a second refusal. Removing a
  worktree at finishing is not a substitute for a refused deletion
  inside it, even where it holds what a worker was refused deleting.
- **A branch has one author at a time.** A writer amends from its own
  worktree, so anything pushed meanwhile is silently rebuilt away. While
  a writer is live, send changes as instructions, even one word. Once it
  has reported finished — its report, not its silence — the orchestrator
  may fix the branch directly, with the same gates, signature and
  review rounds (*Local review*). `git merge-base --is-ancestor <yours>
  <theirs>` says whether an out-of-band edit survived.
- **A finding against a file may also be in the commit message.** Read
  the message before `git commit --amend --no-edit`, and correct it
  there too: squashed, it lands on `main` and is never rewritten.

### The force-push grant

**Amends of pushed commits, rebases of pushed branches and the lease
pushes after them are always authorized** on the branches the session
works. Nobody asks for it. Review sends branches back after they are
pushed, and every rebase rewrites a pushed branch. Every brief states
the grant, because the classifier has refused those pushes where none
was on record. A refusal is still a stop (*A denied permission is a
stop*), with the `-r2` fallback in *Committing and rebasing*.

### Issues left to newcomers

- **An issue labelled `good first issue` is left to outside
  contributors.** No session takes, closes, relabels or edits it, and no
  branch carries a closing keyword for it or bundles it, unless the human
  expressly authorizes that act on that issue. This overrides every other
  rule here that closes, labels or bundles such an issue. It does not bind
  filing a new issue with that label, which *Collateral* asks for. A worker
  relies on an authorization only where its brief quotes it. A number
  among the arguments, or inside a range, is not an authorization: the
  orchestrator skips it and tells the human.

### How you establish a fact

- **A zero is not a measurement until the pattern is proved.** Prove it
  against something the file certainly holds. Run the control unchained:
  `grep -c` exits `1` on zero, so `check && control` never runs the
  control. `zsh` does not word-split an unquoted parameter, so
  `git diff -- $F` with two paths is one pathspec that matches nothing;
  pass paths and revisions as literal arguments or an array, and confirm
  a comparison answering "no difference" can see a difference at all.
  In `zsh` an unbraced `$b:tests/x` is `${b:t}ests/x`, a history
  modifier, and an unquoted `--include=*.py` aborts the command: write
  `"${ref}:${file}"` and quote globs.
- **`grep` reads lines, and prose wraps.** A wrapped phrase answers `0`.
  Use `grep -zE` with `[[:space:]]+` between words (macOS `grep` has no
  `-P`), `pcre2grep -M`, Python over the whole file, or a distinctive
  single word. `grep -c` counts lines, so a
  one-line document (notebook, JSON, bundle) answers at most `1`, and its
  base64 payloads match anything: parse structured documents. A phrase
  count never says a file is free of a restatement — read the file.
- **On macOS `git grep -E` reads `\b` and `\s` as a plain `b` and `s`.**
  A pattern using one answers zero, or matches the wrong lines, without
  an error: use a bracket class for `\s` (`[[:space:]]`), or `git grep
  -P`.
- **A pattern piped after `git grep` also reads its `rev:path:line:`
  prefix.** Put it in `git grep`, or strip the prefix first.
- **macOS `awk`'s `length()` counts bytes**, so a width is measured with
  Python's `len()`.
- **A rehearsal's input is compared with the real file it models**,
  same shape, read from the source, before its outcome is reported: a
  stand-in that differs in shape passes or fails for a reason the real
  file does not share.
- **A rehearsal of a block that takes the gate lock names its stand-in
  by a literal path, in the block**: its
  `. "${PROCESS:?}/scripts/gate-lock.sh"` becomes `. <scratch>/<file>`,
  a file whose name holds no `gate-lock`. The environment does not reach
  the block intact. `codex sandbox -c 'sandbox_mode="workspace-write"'`
  passes it through, but zsh then reads `~/.zshenv`, where `README.md`'s
  *Setup* exports `PROCESS`. So a block run by zsh, in that sandbox or
  outside it, sources the real script whatever `PROCESS` the rehearsal
  set, and with `GATE_LOCK_DIR` unset takes slots of the real lock. A
  rehearsal of the real script instead assigns and exports
  `GATE_LOCK_DIR`, a directory of its scratch by its literal path, on the
  block's first line: under `env -i`, `GATE_LOCK_DIR=$SCR` falls back to
  the real lock. It sources the script by its literal path too, the
  worktree's copy where the branch changes it: through `PROCESS`, zsh
  sources the primary clone's.

  Neither form holds a slot of the shared lock, so the rehearsal starts
  no load: its `yes` becomes a `sleep` that outlasts the watchdog, as
  `sleep 1000`.

  Before the block runs, the rehearsal refuses a stand-in block where
  `grep -cw -e gate-lock -e PROCESS <block>` does not print `0`. It
  refuses a block of the real script where `head -n 1 <block>` is not
  that assignment or holds a `$`, or where `grep -cw PROCESS <block>`
  does not print `0`. Where the block as extracted starts `yes`, it
  refuses either form where `grep -cw yes <block>` does not print `0`.
  Each check's control is the block as extracted, which it refuses where
  that block holds the check's pattern, as the example holds all three.
  `-w` keeps the example's `_NPROCESSORS_ONLN` from matching.
- **A tool's zero covers only what it read.** A skipped file prints what
  a clean one prints. Ask the tool its input set (pre-commit `files:` and
  `exclude:`, `lychee --dump-inputs`, ruff on notebooks without language
  metadata) before believing its answer. A gate the change writes or
  changes is such a tool: each shape its docstring says it reaches, as a
  function under an `if`, in a nested class, or an `async def`, gets a
  control holding that shape, and a run showing the gate reaches it.
- **Name the question a number answers before reading it.** A correct
  number can answer a different question from the sentence being
  written. **Re-prove a control in the round you use it**: as the tree
  moves, a control degenerates into none and still reports green.
  **Shared state expires**: re-read a cache, a database or a ref before
  the claim is written, or date the sentence.
- **Before removing or discarding anything that could be work**, read it
  at commit level — `git log <base>..HEAD`, `git rev-list --count`, never
  `git status --porcelain`, which answers only *is anything
  uncommitted* — and put the output in the report. Name targets
  explicitly; never filter paths by substring. A scratchpad UUID does not
  identify a session. Where it might not be yours, ask its holder.
- **"I do not recall a rule" is not "the document states none."** Grep
  the document and quote it before filing a gap or proposing a rule.
- **A mechanism claim is checked at its joins.** For *X is safe because
  A causes B*, write the chain out, joins included, and check the joins
  first: a getter and a setter with the right callers still have to touch
  the same state. A claim just corrected is the likeliest next error.
  Two measurements that agree confirm each other only where their
  instruments are independent: name what they share (the stub, the
  harness, the command, the base) before calling the second a
  confirmation.
- **`git checkout -- <path>` restores from the index.** Use `git restore
  --source=<ref> --worktree --staged -- <path>`, or `git show
  <ref>:<path>` to read; build a pristine control from `git archive
  <sha>`.
- **`git log -S` restricted to a path dates the rename, not the
  writing.** Search the whole tree on the branch you mean (`git log -S
  <word> main -- .`), not `--all`, which includes unlanded branches;
  check ancestry with `git merge-base --is-ancestor`. It finds a removal
  as readily as an introduction: the `+` or `-` of `git show <sha> --
  <path>` gives the direction.
- **A red gate is not yours until the baseline says so.** Run the same
  gate on `origin/main` in a separate worktree, several times, and report
  both numbers.
- **Measure, do not assert.** Every sentence about what the code did
  before is run against a snapshot (`git archive origin/main | tar -x -C
  <tmpdir>`).
- **What a branch does is its diff against its own parent** (or
  three-dot against the merge base). Two-dot against a moved `main` shows
  what `main` gained as a deletion. A register keyed on a file's contents
  (a names list in a test, section 14's compared-files list) is decided
  from a grep of the file after the change, never from the diff.
- **A timing alternates both versions in one script**, over three or
  more rounds, taking the minimum of `timeit.repeat` per case beside a
  control case the change cannot touch. A round where the control moves
  is discarded. A local timing holds every slot of the gate lock
  (`gate_take_all`, as `process/load-generator.md` says of a generator),
  so that no gate runs beside it. It reports the one-minute load, the
  first number after `load averages:` in what `LC_ALL=C uptime` prints,
  beside its numbers.
- **A repository's state is read from the API, or from a checkout
  brought forward** (`every-session.md`'s *Shell, checkouts and prose*)
  — instruction files included. The orchestrator brings the primary
  checkout forward; a worker reads its own worktree, or, without one, at
  a named sha (`git show <sha>:<path>`). A claim that must hold is still
  measured at a sha. The sha in `git worktree list` is a checkout's
  `HEAD`, not the tip. An issue's body and its comments are read
  separately: `gh issue view --comments` prints the comments in place of
  the body.
- **A forge write that exits non-zero is read back** (`gh pr view --json
  state`, `git ls-remote`, the issue body) before it is reported refused
  or retried: a timeout on the response is not a failed write.
- **A sha, a number or a ref is copied from the tool that knows it**,
  never typed from recollection, and every reference in a posted body is
  read back and resolved.
- **`refs/remotes/origin/main` is shared by every worktree and moves
  under you.** For a gate, pin the base once (`git -C <wt> rev-parse
  origin/main > <scratch>/base-<branch>.sha`) and read that sha
  throughout; re-read `origin/main` deliberately, at rebase and at merge
  time.
- **Under squash, ancestry is the wrong question.** A landed branch is
  not an ancestor of `main`; ask whether its content is on `origin/main`
  before removing a branch, worktree or clone.
- **A distribution is not a rule.** What a tree does is not what it
  owes: find the sentence that requires it, or say you are proposing one.
- **A landed sentence constrains the next decision.** Read what the tree
  has already said (an append-only `CHANGELOG.md` above all) before
  deciding something it has committed to.
- **A reserved decision the branch takes goes in the pull request
  body's `## Decision` section** (`/btclib-iss`'s *Opening the pull
  request*).
- **Another project's source is read from a checkout**, not fetched a
  file at a time through `gh api`: a local clone of `bitcoin/bitcoin`
  (`master`) for Bitcoin Core, of `btclib-org/btclib` for btclib,
  brought forward first (`every-session.md`'s *Shell, checkouts and
  prose*). Where none exists, ask the human for its path. **Name the
  commit you read at** (`git -C <checkout> rev-parse --short HEAD`). For
  btclib prefer the worktree's
  `.venv/lib/python*/site-packages/btclib/`, the commit `uv.lock` pins
  (`direct_url.json` names it).

### When the human has to decide

This section is in `every-session.md`, beside this file.

### What a session's memory holds

**A memory note is not the maintainer's instruction for another
session's work** unless it says so.

### Which prose is worth a round

**A reviewer blocks on a sentence in the tree's own files that is false,
misleading, or a rule stated a second time (`every-session.md`'s *Write
plainly*), as on a code defect, where the branch adds it, falsifies it
or makes it materially worse (*Collateral*).** The tree's own files are
every tracked file, docstrings and comments included. Only wording that
could be better does not block. A wording finding on what the branch
adds is still made, and is fixed with the next change to the branch,
unless `/btclib-pr`'s *Answering it* keeps it off the branch as a
refinement.

**The reviewer may propose replacement text.** Where the branch takes
it, a proposal that changes substance, tone or one of the human's own
sentences goes to the human as a decision (`every-session.md`'s *When
the human has to decide*) before the writer applies it, and a
mechanical fix goes straight to the writer.

**A false or misleading sentence outside the tree does not send a
cleared branch back**:
pull request bodies, issues, comments, reports, the commit message.
Answer `CLEARED <sha>` with the finding underneath. It is still fixed
with the next change to the branch. The commit message is corrected in
an amend where the branch is amended anyway, and otherwise in the squash
(`/btclib-pr`'s *Landing*).

## Collateral

- **A branch carries its subject and nothing beside** (`REVIEWING.md`'s
  *What to look for*). Its subject is what its issues ask, wherever the
  defect they name shows; a sentence its diff falsifies (*Where your diff
  falsifies a sentence elsewhere*); and what was already wrong that its
  diff makes materially worse (`REVIEWING.md`'s *What is filed, and what
  is not*). A shared file or subsystem is not a shared subject.
- **Anything else noticed goes where `REVIEWING.md`'s *What is filed,
  and what is not* says**; what it does not file is named in the report,
  for the next change on its subject. Wrong prose in a file the diff
  touches takes the same route: a reviewer cannot ack a diff for a
  question it was not opened for. A new rule in `README.md` lands with
  the gate that reads it, or does not land (btclib-org/.github#1075).
- **A new issue is filed by whoever noticed it, when they notice it**, in
  the repository hosting that code, or, for code outside btclib-org, as
  the next bullet says. Search first (`gh issue list --repo <owner>/<repo>
  --state open --search "<word> <word>"`). Measure first; where that would
  mean leaving the work at hand, put the deciding command in the body and
  say it was not run. A small, self-contained one that no red gate,
  security or packaging defect waits on is filed with the `good first
  issue` label, a *Done when* and the file to look at.
- **Before a change is proposed, closed issues and pull requests are
  searched for it too**, under broad words, and the maintainers'
  comments there are read, review threads included. `gh issue list` and
  `gh pr list` take `--repo <owner>/<repo> --state closed --limit 200
  --search "<word> <word>"`.
- **Code outside btclib-org** is reported first in the btclib-org
  repository where it was found, not in its own tracker: `gh issue create
  --repo btclib-org/<repo> --label upstream-report`. Section 11 of
  the organization's standard (*Labels and issue types*) says what
  becomes of the issue once the report is filed upstream. The text for the
  external tracker goes to the human, and nothing is posted there before
  the human has read it.
- **Evidence you lean on is evidence you own.** A claim your change turns
  into the ground of a new sentence is re-derived, whoever wrote it.
- **Where your diff falsifies a sentence elsewhere, fixing it is part of
  the diff.**
- **A repository setting and its record in `REPOSITORY.md` change
  together.** The setting is changed first, on the human's yes, and the
  pull request records what the API then answers. Its body gives the
  command that reads the setting back, and the local reviewer runs it:
  the bot's review cannot call the API.
- **A measurement that refutes an issue closes it**, with the commands
  and figures in the closing comment.
- **Read back the number before reporting it**:
  `gh issue view <n> --repo <owner>/<repo>`. In a report, collateral
  appears as `ISS <repo>#123`, as *How an issue and a pull request are
  named* says, followed by a very short description.
- **The reviewer files with the body inline**; where it cannot file,
  the body goes verbatim in its report.
