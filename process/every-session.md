# What every session reads first

Every session reads this file whole before its first command, in any
repository; a writer creates its worktree first, as the `writer` agent's
*What holds whatever the process* says. It holds the part of the
btclib-org process that binds every session, whatever its role. Where a
rule here rests on a section of another file beside this one, it names
that file and when to read it. `every-role.md`, `writing.md`,
`local-review.md` and `orchestration.md` hold the rest, and the opening
of `every-role.md` says what each role reads and which file wins where
two disagree.

## Shell, checkouts and prose

- **Never open a command with `cd`.** The working directory resets to
  the primary checkout between tool calls, so a `cd` in one call and the
  command in the next runs it in the primary checkout, and both report
  success. Bind the directory in the command itself: `git -C <dir> …`,
  `env -C <dir> …`, or `git -C <checkout> show <sha>:<path>`, which needs
  no working directory. This holds for reads too.
- **Read a checkout only after bringing it forward.** `git fetch` moves
  `origin/<branch>` and leaves the files on disk behind. A primary or
  reference checkout (not your own worktree) is read after:

  ```shell
  checkout=<checkout>
  branch=<branch>
  ```

  ```shell
  git -C "${checkout:?}" rev-parse --abbrev-ref HEAD
  git -C "${checkout:?}" status --porcelain
  git -C "${checkout:?}" fetch origin
  git -C "${checkout:?}" pull --ff-only
  git -C "${checkout:?}" rev-parse HEAD "origin/${branch:?}"
  ```

  The first `git` command prints `main` or `master`, the second nothing,
  and the last the same sha twice. Where it is not on its default branch
  or not clean, stop and say so.
- **Write plainly.** Everything written — code comments, docs, these
  process files, commit messages, pull request and issue bodies,
  comments, reports — must be clear, simple and no longer than it needs
  to be: the point first, plain words, one fact per sentence. A clause
  whose removal loses nothing a reader needs is cut. **Say a thing once;
  elsewhere, point to it** (the standard's section 9, *One fact in one
  place*): a summary names the section that holds a rule and does not
  restate it. A text the reader has to read twice has failed, however
  correct. **English in the tree**: code comments, docstrings, documents,
  the messages a script prints, logs and commit messages are in English,
  whatever language the conversation that produced them was in.
- **What is posted on a forge** — an issue, a pull request, a comment or
  a reply, in any repository — meets these limits, and every reviewer
  checks them as a blocking item:
    - **The first line is the point**: the verdict of a pull request
      review, the problem an issue or pull request addresses, the answer
      a reply gives. A reader who stops there knows it.
    - **A verdict is given only on a pull request, and only where the
      review supports it.** In btclib-org only the deciding review gives
      one, as `REVIEWING.md`'s *The verdict* says. The deciding review's
      summary keeps the shape `REVIEWING.md`'s *The verdict* gives it,
      its findings one bullet each; the limits below hold for every
      other review.
    - **A review that gives no verdict states its finding on its first
      line**, with no `Comment:` prefix and no "a comment, not a
      review".
    - **Then purpose, finding, conclusion**: what was checked and why,
      what was found, and what follows for the pull request or the next
      step. One point per text; no sha or line-number chains, no
      preemptive rebuttals, plain words.
    - **A comment or reply is about 250 words, and never more than 300**
      (`wc -w <file>`), with no list and no heading: the first line,
      then at most three paragraphs. In a review they are the
      measurement, the technical findings, and what the change leaves
      unfixed (next bullet). A review that reports measurements says in
      one sentence how they were measured, and links the detail.
    - **What the reviewed change leaves unfixed gets one paragraph of its
      own**, apart from the measurement. Where the review neither asks
      for a fix in the same pull request nor gives it, the paragraph
      links the pull request we open with the fix, and the review is
      posted once that pull request is open.
    - **A pull request or issue body is at most two short paragraphs**
      before any code block or required template section.
    - **"ACK" appears only in an ACK, and every ACK is a review on the
      head sha it names.** Another reviewer's verdict, quoted as that
      reviewer gave it, is not a use of the word, as in a row of the
      findings record or a link of an approval's body. A hit of
      `grep -nE '(^|[^[:alnum:]])(ut|re|cr|t|N)?ACK' <file>` outside a
      verdict line and outside such a quote is the defect.
    - **A gendered pronoun for a person stands only as that person
      states it**, in our own files too. This lists each one to check:
      `grep -nwiE 'he|him|his|himself|she|her|hers|herself' <file>`.
    - **A text over a limit is not posted but returned cut**, unless a
      maintainer asked for exactly that detail.
    - **The findings record is a record, not a reply**
      (`orchestration.md`'s *The findings record*, read before keeping
      one): no limit on a comment's length, lists or headings binds it,
      and its first line is still the point.
- **Parallelize as much as you can.** Reads, remote work, writers and
  reviewers run side by side, within the machine's CPU load, memory
  pressure and free disk (*The machine is shared*, below, and
  `writing.md`'s *The gates* and *Before starting*, read before starting
  work in parallel).
- **The machine is shared.** Heavy local work — a suite, the hooks
  except where `writing.md`'s *The gates* says, a docs build — runs
  under the gate lock, as `writing.md`'s *The gate lock* says, read
  before running a gate. Everything else runs in parallel with the
  gates. Targeted test runs use `-n 0` or `-n 2`, never `-n auto`. The
  whole suite runs as the tree's gate says; where the tree runs it under
  pytest-xdist, with `-n "$GATE_LOCK_WORKERS"` (`writing.md`'s *The gate
  lock*), which overrides an `-n auto` in its `addopts`. Other sessions'
  processes are not yours to kill.

  A job that takes no slot and weighs on memory — an agent, a local
  Codex run, a targeted test run, a build outside the gate lock — starts
  only at a memory pressure level below 4
  (`sysctl -n kern.memorystatus_vm_pressure_level`), and only where the
  share of memory free (`memory_pressure -Q | tail -1`) stays above
  about 30% once the job's peak is added. Otherwise it waits. While any
  job waits, the session reads again every 120 seconds, and whenever one
  of its jobs ends. Where the level cannot be read, as in Codex's
  sandbox, the share free decides alone. The readings decide how many
  jobs run, never a fixed count.

  The peaks to add are those measured, until the ledger of
  ISS btclib-org/ai-agents-process#582 replaces them: a local Codex run
  about 0.2 GiB (185 to 221 MiB on 2026-11-18), and this repository's
  pre-commit hooks about 1 GiB (0.94 to 1.12 GiB that day). Each is the
  largest resident set of a single process, as `/usr/bin/time -l` prints
  it, so a lower bound for a job of several processes, as both are. A
  job whose peak is not measured adds none, an agent among them. In
  Claude Code an agent shares the session's own process, which `time`
  cannot isolate. A Claude Code reviewer that Codex starts with
  `claude -p` is a process of its own, and has no figure above. So
  after starting any job, the session starts the next only on a fresh
  reading, taken at the first of these: the job has ended,
  `GATE_LOCK_SETTLE` seconds (60) have passed since its start, or, for
  an agent or a Codex run, its first tool call has returned.
- **The forge's quota is shared.** Every session and agent on this
  machine calls the forge through the same `gh` login, and so draws on
  the same hourly quotas: `core` for REST, `graphql` for what `gh pr
  checks` asks. A wait on checks or runs asks every 120 seconds or more:
  a loop sleeps `120`, and a `--watch` or a `gh run watch` takes
  `--interval 120`, never `gh`'s default. One wait at a time per pull
  request, not one per agent. Where either quota has under 500 left,
  waits stop until the reset it prints, and the report says so:

  ```shell
  gh api rate_limit --jq '.resources | {core, graphql} | to_entries[]
    | "\(.key) \(.value.remaining) reset \(.value.reset | todate)"'
  ```

- **A Bitcoin Core program runs on a data directory of the scratch
  directory.** Every call of one that takes `-datadir`, as `bitcoind`
  and `bitcoin-cli` do, carries an explicit `-datadir=<scratch>`,
  `-version` included. Without it the call uses the machine's default
  data directory, which may hold a real node: `bitcoind` writes its
  `settings.json` there before it acts on `-version`, and `bitcoin-cli`
  reads its configuration and cookie there and so reaches that node.
  Bitcoin Core's functional tests are the exception: their framework
  starts each node with a `-datadir` of its own.
- **`timeout` may not be installed, so a command that uses it checks
  `command -v timeout` first.** Where that prints nothing, the command
  runs without a time limit, and the report says so. On macOS,
  Homebrew's coreutils provides it, and it exits `124` when time runs
  out, or `137` where its `-k` had to send KILL. Coreutils installs its
  GNU versions of the commands macOS already ships, such as `date` and
  `stat`, under a `g` prefix (`gdate`, `gstat`); the unprefixed ones
  stay BSD.
- **A filter that prints `false` exits `0`**, in `gh`'s `--jq` as in
  `jq`, so what a command prints is tested by its value, as
  `[ "$(…)" = true ]`, never by its exit code. `jq -e` exits `1` on
  `false` or `null`; `gh` has no such flag.
- **`grep` and `find` in the tool's shell may be functions** (`type
  grep`). `grep` over `ugrep -G --ignore-files` skips what `.gitignore`
  covers under the search root and reads a `$` mid-pattern as an anchor,
  both silently: prefer `git grep`, or `-F` and `[$]`. `find` as bfs
  (`find --version`) refuses GNU's `-newermt 'today'` on stderr: a sweep
  uses ISO-8601 timestamps, never discards stderr, and runs a path known
  to match as its control.
- **macOS `sed` reads `\b` as a plain `b`.** `sed -i '' 's/\bx\b/y/g'`
  edits `bxb`, never the word `x`, and exits `0`. Use `perl -pi -e`, and
  read the edit in `git diff`, never in the exit code.
- **In `zsh` a word beginning with `=` is a command lookup** (`echo ====`
  fails the whole line), `path` is the `PATH` array and never a variable
  name, and a glob after `env -C <dir>` expands in the caller's
  directory: quote `=` words and pass absolute paths. BSD `env` takes
  `-C` and `-u` before any `NAME=val`; after one, `-C` is read as the
  command and exits `127`.

## When the human has to decide

**One decision per message, and the next as soon as it is answered.**
The message that takes an answer also puts the next decision, in the
same turn, so the human never waits on the session to be asked. Never a
batch or a numbered list of decisions, even where the human asks for
"the open questions": those are put the same way, starting now. Put
first the one that blocks the most work. A report may list what waits on
the human, one line each; it asks none of it, and it closes by putting
the first one.

**No decision is held back.** One that can be asked is asked now, not at
the end of a task. One whose shape is missing a measurement gets that
measurement started at once, and is asked when it returns.

**The work does not wait for the answer.** While a decision is open,
everything that does not depend on it goes on in parallel.

**A question the rules already answer is not a decision:** apply the
rule, and report the outcome in one line.

**Each decision comes in one shape**, and is not asked until it has it:

- the context, in full every time, even for an item discussed before:
  the linked repository and number, the title, the author, the state
  (reviews, verdicts, open questions), what we did and found, why work
  stops here, and the full texts at stake;
- the recommendation first, with its reason;
- the other alternatives, each with what it costs;
- where an alternative changes a pull request's diff, the delta it
  brings, written as the diff balance is (`every-role.md`'s *How an
  issue and a pull request are named*, read before putting such a
  decision), measured on the alternative drafted in a scratch worktree,
  or else estimated and marked as an estimate.

Number the alternatives, so that one number answers.

**This holds wherever work stops for the human.** The repository
question is the exception: it lists the candidates without recommending
one, since the repository is never inferred (`every-role.md`'s *Where
you work*, read before working in a repository). It is still asked on
its own.

**A writer, reviewer or designer puts a decision in its report**, in
this shape, and the orchestrator asks it.

**Where the human is not the maintainer, a decision on what a change
does goes to the maintainer**: its design, its scope, a decision its
issue reserved, a disagreement on its pull request that survives a
second exchange. Such a decision is not put to the human: it is recorded
as a hold whose comment @-mentions the maintainer. These stay the
human's: which pull requests to work, an approval, the session's own
review rounds (`local-review.md`'s *The rounds*, read before running
them), a finding its reviewer still holds included.

**A design question a writer raises on a branch, which its issue did not
reserve, is filed as its own issue** (`every-role.md`'s *Collateral*,
read before filing it) and decided there. Ask what each answer would do
to what the branch's issue asks. The branch waits for the answer only
where one answer would undo or replace that; otherwise it is judged as
written. An answer that changes only the lines carrying the question is
left to the question's own issue.

**At night**, `night-mode.md`, beside this file and read when night mode
is turned on, says what becomes of a decision.

**A hold is recorded on the issue or pull request**, in the same turn it
is told to the human: a comment saying why it waits, and its label where
the repository has it. A question put to the human or the maintainer
takes `decision`. Any other wait takes the label naming its reason, the
comment giving the detail: `needs-maintainer`, `needs-contributors`,
`waits-release`, `waits-github`, `waits-issue`, `flaky-watch` or
`needs-hardware`, whose meanings `.github/labels.yml` of
`btclib-org/.github` gives, or `upstream-dependent` for an upstream
project. A pause the human decided takes `on-hold`. An awaited review
takes no label: the review request shows it. A wait on the author's
changes takes none either: the review that asked for them
shows it. An exhausted review quota is handled as
`/btclib-pr`'s *Rebase and CI* says. A hold kept only in the session's
context does not exist, and another session will take the work.

**A publishing tree's `RELEASING.md` says in *Release to PyPI* when a
release pull request carries `release-hold`** and what the label holds,
and `/btclib-pr`'s *Landing* how a session reads it.
