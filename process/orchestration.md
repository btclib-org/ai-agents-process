# The btclib-org process: orchestration

`every-role.md`, beside this file, opens the process: its opening says
which role reads this file, and where a section named here in italics
with no file is.

## Orchestration

- **Dispatching a writer**: the paths of the files under
  `$PROCESS/process/` the map gives its role, `every-session.md`'s and
  the skill's, and the sections of those files and the skill that are
  its role's, the issue or pull request, the repository, the worktree
  and scratch paths, the force-push grant, and the claims you measured.
  The same for a reviewer and a designer, and for a designer the
  `origin/main` sha it reads the tree at.
- **Before dispatching, ask whether the issue is collateral of a pull
  request this session worked** (*Closing collateral*).
- **The role map binds the brief.** A writer does not open pull requests;
  do not ask it to.
- **Every claim in a brief carries its command, or the words saying it
  is unmeasured.** A writer writes a false premise into prose that lands.
  `ls -d` a path before naming it; a missing checkout is a question for
  the human. What a brief omits misleads as much as what it gets
  wrong.
- **Do not hand the reviewer your hypothesis as a premise.**
- **After a rebase or a new commit, the gates *The gates* asks of the
  new sha run before any reviewer is asked**, and the report you hand it
  names that sha.
- **Do not retract part of a brief mid-round.** Let the round finish and
  discard the finding. Where it cannot wait, say why the brief was wrong,
  and that a reviewer reading it as a contradiction should say so rather
  than comply.
- **The writer's report crosses to the reviewer whole**, in its own words;
  what you add is appended and marked as yours. Name every gate with its
  exit code, the one the repository calls the gate of record first.
  Where you fixed the branch yourself, your own runs are reported the
  same way.
- **Re-measure each finding before passing it on**, as `/btclib-pr`'s
  *Answering it* says, and pass on only what holds. That section says
  how the writer answers what is passed on, and how you decline the
  rest. A list found incomplete twice is deleted, not lengthened. From
  the second round, remind the reviewer of `REVIEWING.md`'s stopping
  criterion.
- **From the sixth round of a branch's local review, the brief names the
  round**, and the rule of *The rounds* that files a finding on a shape
  no tree and no caller holds.
- **Weigh a finding by who reads the text and how often** before sending
  it on.
- **Workers writing in one repository at once contend for regions of a
  file.** Tell each which regions the others hold, and to stop and
  report rather than cross. The number of workers is set by the disjoint
  regions and your own capacity to review and land, within the machine's
  limits (`every-session.md`'s *Parallelize as much as you can*).
- **A quiet worker is asked for status, not stopped.** Where the
  human asks for a kill, say what will be lost and leave the
  worktree standing.
- **A pull request's writer and reviewer are stopped once it lands or
  its work passes to another worker** (`TaskStop` in Claude Code): one
  that ended its turn with a background job registered counts as running
  for days.
- **A diagnosis that has failed twice gets two independent attempts at
  once**, each given the other's hypothesis as a lead to test, and asked
  for the disagreement.
- **Reuse.** A writer takes a new, unrelated pull request only after
  `/compact`; its own deferred half and its own collateral it takes
  uncompacted. *The rounds* says which worker stays for which rounds;
  the dedicated reviewer comes back only for its pull request's
  collateral. *Agents in each client* and *Clients* say how a worker is
  resumed, and that starting one always makes a new one.
- **Models**: in Claude Code the writer, the reviewer and the designer
  run on Opus at effort `high`, which their agent definitions set, so
  none follows the effort of the session that starts it: the exception
  *Which file wins* makes to the general model advice in `AGENTS.md`.
  Where that session's environment sets `CLAUDE_CODE_EFFORT_LEVEL`, the
  variable wins over the definition. A reviewer Codex starts with
  `claude -p --agent` takes the definition's model but not its effort,
  so its command in *Starting the reviewer in the other client* names
  `--effort high`. The orchestrator may run on Opus. In Codex the agent
  files set no model: an agent runs on the one its spawn request names,
  else on the `[agents]` default of `config.toml`, else on the
  orchestrator's. A reviewer `codex exec` starts runs on `gpt-6.1-sol`
  at effort `high`, which its command in *Starting the reviewer in the
  other client* names, rather than on `config.toml`'s `model` and
  `model_reasoning_effort`.
- **A worker that exceeds the time you set is interrupted**, not waited
  for.
- **Writing runs in parallel; heavy gating runs under the gate lock**
  (`every-session.md`'s *The machine is shared*). A reviewer that runs
  the gates itself is briefed with *The gates*.
- **A writer that has reported is sent nothing further until its
  reviewer has answered.**
- **The orchestrator checks `git status --porcelain` in the primary
  checkout between rounds.** Where it is dirty, diff it against the
  worktree that should have held the change. Where the dirty content is
  byte-identical to that worktree's own version — its uncommitted change
  or the blob on its branch — and nothing is staged or committed in the
  checkout, undo it and report it: a modified path with
  `git -C <checkout> restore -- <paths>`, an untracked stray file by
  removing it by name. Anything else — a path no worktree explains, a
  difference of one byte, a staged or committed change — is reported and
  left for the human.
- **A session that runs long re-reads what can arrive meanwhile**
  between rounds: new pull requests, new reviews and comments on the
  ones it works, and the process (*The process is re-read when `main`
  changes it*).
- **The process is re-read when `main` changes it.** The session notes
  `$PROCESS`'s `HEAD` in `<scratchpad>/orchestrator/process.sha` before
  it first reads `every-role.md`, as its skill's opening says. Between
  rounds, and before it briefs a worker, it brings `$PROCESS` forward
  (`every-session.md`'s *Shell, checkouts and prose*) and notes the
  `HEAD` it compares:

  ```shell
  scratchpad=<the session's scratchpad>
  git -C "${PROCESS:?}" rev-parse HEAD > "${scratchpad:?}/orchestrator/process.next"
  ```

  It compares that sha with the noted one:

  ```shell
  scratchpad=<the session's scratchpad>
  started=$(cat "${scratchpad:?}/orchestrator/process.sha")
  next=$(cat "${scratchpad:?}/orchestrator/process.next")
  git -C "${PROCESS:?}" diff "${started:?}" "${next:?}" -- \
    process/ skills/ scripts/ agents/
  ```

  Where the diff prints anything, the session re-reads each section it
  touches, and whole each file it touches that is not markdown, such as
  a script. It reads them at `next`, as
  `git -C "$PROCESS" show "${next:?}:<file>"` prints them: the hunks'
  line numbers are `next`'s, and another session may have moved the
  checkout since. A markdown hunk's header shows a body line, not a
  heading: a hunk's sections are the last heading above its first line
  and every heading within its lines, among those that output piped to
  `grep -n '^#'` lists. In a markdown file, a heading the diff removes,
  a line starting `-#`, and adds nowhere is a section that is gone: the
  session stops following it. A file the diff lists that `next` no
  longer holds, a deleted script for one, is gone too: `git show` cannot
  print it, and the session stops following it. Where the diff exited
  `0`, the compared sha becomes the noted one, since another session may
  have moved `HEAD` meanwhile:

  ```shell
  scratchpad=<the session's scratchpad>
  mv "${scratchpad:?}/orchestrator/process.next" "${scratchpad:?}/orchestrator/process.sha"
  ```

  A brief to a worker already running names the changed sections that
  are its role's, and those gone. Where a map of *Which sections are
  yours* changed, it also names each section the map now gives that
  role, changed or not, and each it no longer gives, which the worker
  stops following. It also names each file under `scripts/` the diff
  lists, such as `scripts/gate-lock.sh`: the worker re-reads whole each
  one it has read, and stops following each one `next` no longer holds.

  A file under `agents/` is the definition a worker of its role is
  started from (*Agents in each client*, *Starting the reviewer in the
  other client*), and a worker already running keeps the one it started
  with. Where the diff lists the file a running worker was started from,
  the next brief names it too: the worker reads it whole and follows it
  in place of the text it started with. The model, the effort and the
  tools Claude Code takes from its frontmatter cannot change for a
  running worker; only a worker started from the new file can take them.

  Where the diff exited non-zero, or `process.sha` is missing or empty,
  the changed sections are not known. The session notes `HEAD` again as
  its skill's opening says, then re-reads whole every file under
  `process/`, `skills/`, `scripts/` and `agents/` it has read, and every
  one where it cannot tell; it stops following each one the checkout no
  longer holds. The next brief to each worker already running asks it to
  re-read whole its role's sections, each file under `scripts/` it has
  read and the file it was started from, as above, and to stop following
  each one the checkout no longer holds.

## Running the rounds

- **The orchestrator checks that the rounds converge**, on the findings
  record (*The findings record*). The rounds do not converge where a
  closed finding comes back blocking, from any reviewer, where a fix
  leaves the reviewer that asked for it with as many findings as before,
  or more, not counting a finding closed by filing (*The findings
  record*), or where the third fresh reviewer since the dedicated
  reviewer last cleared, or any after it, gives a first verdict of
  `CHANGES REQUESTED` with a finding a prose-only fix cannot answer.
  Then the orchestrator puts it to the human as one decision
  (`every-session.md`'s *When the human has to decide*): another round,
  the branch as it stands, or a cut-back, with the writer's and the
  reviewer's positions. The rounds wait for the answer.
- **A session restart replaces each reviewer it lost.** A restart can
  lose the reviewers the session started, and the rounds keep no record
  of one in flight. So after a restart, the verdict file of a reviewer
  in the other client, `<name>.last.md` of a Codex one and `<name>.log`
  of a Claude Code one (*Starting the reviewer in the other client*), is
  read first, and a whole verdict there (*The verdict*) is received.
  Each review whose verdict was not received runs again on the latest
  version, with a new reviewer. A reviewer that has a fix to read and
  can no longer be resumed (*Agents in each client*, *Clients*) is
  replaced by a new one whose brief carries its last verdict and the sha
  that verdict named. Each new reviewer takes the lost one's place: for
  *The rounds* it is the same reviewer, in the count of the convergence
  check above too.
- **The classes of defect found carry forward.** The findings record
  (*The findings record*) gives each finding its class: the shape of
  input or the step of reasoning it broke. The brief of each later
  reviewer of the branch, and of the writer and the reviewer of another
  branch of the session on the same files, lists the classes of the
  findings that held, and asks the writer to guard against each and the
  reviewer to try each first. A finding a forge review makes after a
  local `CLEARED`, and that holds (the fix accepts it or the human
  upholds it), is marked in the record as one the local rounds missed,
  and the session's report to the human names its class and proposes
  where the next session will read it: for a btclib-org tree, its
  `REVIEWING.md`'s *This repository in particular*, or the shared part
  in `btclib-org/.github` where the class is not that tree's own
  (*Wrap-up*). The report also proposes the pull request as a case of
  `$PROCESS/process/replay-set.md`.
- **Where the other client is unavailable, the branch goes on without
  the fresh reviewer.** Unavailable means the client refuses the run.
  The first run is judged when the rounds reach the fresh reviewer: it
  is tried, and once refused it is not retried, even where the client
  comes back before the branch lands. A refusal the session cannot
  clear, as Codex's `Your workspace is out of credits` is, also holds
  for the session's later branches: they go on without the fresh
  reviewer, with no new try. A limit that names a reset time within the
  session is not one: once the reset has passed, a later branch tries
  the run again. The hold on later branches ends with the session: a new
  session tries the run again at its first branch not already refused.
  The rounds end at the dedicated reviewer's `CLEARED` of the head,
  which stands wherever the process asks for the latest fresh
  reviewer's. Where the dedicated reviewer's last `CLEARED` names an
  earlier sha, it is resumed on the head first. The branch is opened,
  and lands once everything else `/btclib-pr` asks of it holds, its *The
  reviews on GitHub* included, which says how an absent one is recorded.
  The pull request body, a later branch's included, says that the fresh
  review in the other client is missing, and quotes the refusal that
  holds for it: the error the client printed, and the time it came. No
  review in the other client is owed after it lands.

  A fresh reviewer is owed a resumed run where it answered
  `CHANGES REQUESTED` and has not cleared, or where its verdict names an
  input its sandbox left unrun (*Clients*). Where the client refuses
  that run, or the hold on later branches keeps it from being tried, the
  refusal is judged then. Where the session can clear it, what that
  reviewer is owed waits for it, and the resumed run is tried again once
  the refusal is cleared. Where it cannot, the dedicated reviewer takes
  over what that reviewer is owed: it re-reviews the fix of its
  findings, and judges the result of each input it left unrun, or the
  human's answer that stands in for it, as *Clients* says. Where the
  fresh reviewer left inputs unrun, the dedicated reviewer's `CLEARED`
  of the head ends the rounds only where it came after their results or
  answers. The branch then goes on as above, without the fresh reviewer,
  the hold on later branches included. The pull request body says that
  the fresh reviewer's re-review is missing, where it would say the
  fresh review is, and that the dedicated reviewer took it over.

  A fork's pull request body is the outside contributor's. What this
  bullet, or *Clients*, has the body record goes in a comment of the
  session's own on the pull request instead, posted before the approval
  is asked for and naming the head it holds for. A comment, unlike an
  approval review, is there whoever approves, and on a fork the approval
  goes to the human (`/btclib-pr`'s *Outside contributors*).
- **Codex reads the branch locally before each round on the forge**
  (*The rounds*): the whole head before the pull request is opened, and
  before a later push the delta from the last head Codex read. It is a
  Codex `reviewer`, started as *Starting the reviewer in the other
  client* says, from Claude Code by its `codex exec` command. A
  `CLEARED` of the head by a Codex reviewer of the rounds stands for it,
  and so does the port check of the next bullet. A rebase that keeps the
  `CLEARED` (*A rebase and the clearance*) asks for no new pass. The
  pass's findings go in the findings record, answered as `/btclib-pr`'s
  *Answering it* answers a bot's, and each is closed there before the
  head goes to the forge. Where Codex refuses the run, the head goes
  without it, the refusal judged and recorded as *Where the other client
  is unavailable* says of the fresh reviewer's.
- **A port of the standard goes to no local reviewer where
  `scripts/port-check.py` exits `0` on the head that lands, run again
  after each rebase or merge of `main` as the gates are, and no change
  it lists asks the tree for more than the standard's copies**
  (`/btclib-iss`'s *Ports of the standard*): the standard's text was
  reviewed where it landed, and the script compares only the copies.
  That check stands wherever the process asks for the latest fresh
  reviewer's `CLEARED`, and the reviews on GitHub still read the port.

## The findings record

**Every finding on a branch goes in one record, which the orchestrator
keeps**: its own reviewers' and those of every review on the forge, a
review bot's and a maintainer's included. Until the pull request exists,
the record is a file of the orchestrator's,
`<work>/findings-<branch>.md` (`every-role.md`'s *The scratchpad is
shared*). Once the pull request is open, the record is kept as a comment
on it, as below. A session that takes the pull request over then reads
every finding, its outcome and the head it was last checked on, which a
file in another session's scratch directory would not give it. An
embargoed fix's record stays in the file until its advisory is published
(*Committing and rebasing*). So does the record on a tree whose
`CONTRIBUTING.md` does not yet exempt it from the comment limits: that
file wins over `every-session.md`'s exemption (*Which file wins*) until
the standard's *Write plainly* carries it, as btclib-org/.github#2306
asks, and the tree takes the port. A text to be posted keeps its record
in the file alone, `findings-<text file>.md` in `<work>`, or, for a text
that belongs to no issue yet, in the directory `every-role.md`'s *The
scratchpad is shared* gives it. The hash `shasum -a 256 <text file>`
prints for each version stands for a head. When `<work>` is swept, its
record files move to `<scratchpad>/orchestrator/` under `<work>`'s name
(`every-role.md`'s *Debris goes when its work ends*), and are read
there.

**The record lists every round, local or on the forge, as *The rounds*
counts them**: its head, each reviewer that read the head in that round
and its verdict, a round that brought no finding included.

**An entry holds** the finding in a sentence, with its class (*The
classes of defect found carry forward*); who raised it; the head it was
raised on; the lines it rests on, quoted, with the sha they are read at
(`local-review.md`'s *A finding quotes the lines it rests on*, and
below); its outcome; and the head it was last checked on. The outcome is
open until the finding is answered as `/btclib-pr`'s *Answering it*
says: accepted, with what fixes it, which is the commit, the corrected
sentence or its removal for a sentence of the pull request body, or the
corrected subject or sentence, read at the landing, for a commit-message
finding fixed only in the squash (`/btclib-pr`'s *Landing*); declined,
with the measurement that refutes it or shows it a refinement; filed, as
`ISS <repo>#<n>`; or a decision, waiting on the human or the maintainer.
An accepted, declined or filed finding is closed for the convergence
check of *Running the rounds*.

For a review on the forge the orchestrator quotes the lines a finding
rests on from its thread's `path`, from `original_start_line`, where it
is set, to `original_line`, read at the thread's `original_commit_id`,
or, where the thread's `side` is `LEFT`, at the commit that
`git merge-base <original_commit_id> origin/<base>` prints where it
exits `0`; a non-zero exit leaves the finding unquoted, which is a stop.
A forge finding with no `original_line`, on a file or in a review's
summary, quotes the lines it names, which the orchestrator finds by its
own search and reads at the head, with that search as the entry's
command; where it names none, the entry quotes the finding's own
sentence and the command that looked.

**The orchestrator checks a local reviewer's quote before passing the
finding to the writer.** It writes the excerpt to a file of its own,
ending in a newline, and this exits `0` only where the excerpt is not
empty and the lines from `<line>` at `<sha>`, the sha the entry names,
equal it exactly. A finding whose quote fails goes back to its reviewer,
not on to the writer: its lines are not the branch's. A finding that
quotes a command and its output instead is checked by running the
command at the sha, and fails where what it prints differs from the
output quoted.

```shell
wt=<wt>
sha=<sha>
file=<path>
line=<line>
quote=<excerpt file>
n=$(wc -l < "${quote:?}")
[ "$n" -gt 0 ] && (set -o pipefail
git -C "${wt:?}" show "${sha:?}:${file:?}" |
  sed -n "${line:?},$((line + n - 1))p" | cmp -s - "${quote:?}")
```

**On each new head, every entry is assessed again against the code**,
whether or not a reviewer raised it again, and its last checked head
becomes the new one. An open finding is fixed only where the new head
fixes it, by lines the entry then quotes or by removing the lines it
quoted, with the commit named; an accepted one stays fixed only while
that still holds. A finding on the pull request body is assessed again
on each new head and before the landing, against
`gh pr view <n> --repo <owner>/<repo> --json body --jq .body`: it is
fixed only where the body holds the corrected sentence the entry quotes,
or no longer holds the one the finding rests on.
A read that exits non-zero is a stop, not a finding left unfixed: it
says nothing about the body. A reply, the author's or the writer's,
settles nothing.

**Two findings are one where they share their mechanism and their
consequence**, whatever their titles or lines. A new finding that
matches an entry is that entry, and one that matches a closed entry is a
closed finding come back (*Running the rounds*).

**The comment is a table, one details block per finding, and the marker
line last**, a shape `every-session.md`'s *What is posted on a forge*
allows a record. The bracketed sentence is written only where the record
supersedes another login's (below):

````markdown
Findings on <head>: <open> open. [Supersedes <earlier record's URL>.]

| Round | Head | Reviewer | Verdict |
| --- | --- | --- | --- |
| 1 | 1a2b3c4 | dedicated reviewer | CHANGES REQUESTED |
| 2 | 5d6e7f8 | dedicated reviewer | CLEARED |

| # | Raised by | On | Where | Outcome | Checked on |
| --- | --- | --- | --- | --- | --- |
| 1 | dedicated reviewer | 1a2b3c4 | `x.md:120` | accepted, 5d6e7f8 | 5d6e7f8 |

<details><summary>1. <the finding, in a sentence></summary>

Class: <the shape of input or the step of reasoning it broke>.

`<path>` from line <line> at <sha>:

```text
<the lines, exactly>
```

<the outcome: the lines that fix it, the measurement, or the issue>

</details>

<!-- btclib-findings-record -->
````

**A record is a comment whose last line is the marker line**, posted by
an owner, a member or a collaborator of the repository, and one login
has one at most. This prints every record's id, login and URL, the least
recently updated first; the last line is the active record. It prints
nothing where there is none, and exits non-zero where a read failed or
one login posted more than one, which it names:

```shell
repo=<owner>/<repo>
n=<n>
(set -o pipefail
gh api --paginate "repos/${repo:?}/issues/${n:?}/comments?per_page=100" |
  jq -rs '[.[][] | select((.author_association
      | IN("OWNER", "MEMBER", "COLLABORATOR"))
    and ((.body // "") | rtrimstr("\n") | split("\n") | last
        | rtrimstr("\r"))
      == "<!-- " + "btclib-findings-record" + " -->")]
  | sort_by(.updated_at) as $r
  | ($r | group_by(.user.login) | map(select(length > 1))) as $twice
  | if ($twice | length) > 0
    then error("more than one record by \($twice[0][0].user.login)")
    else $r[] | "\(.id) \(.user.login) \(.html_url)" end')
```

**A non-zero exit is a stop**: the session reports it, and neither edits
nor posts. Where it exits `0` and a line names the session's login
(`gh api user --jq .login`), the session edits that comment, whether or
not another login's is later:

```shell
gh api -X PATCH repos/<owner>/<repo>/issues/comments/<id> \
  -F body=@<record file>
```

Where no line does, it posts its own record:

```shell
gh pr comment <n> --repo <owner>/<repo> --body-file <record file>
```

Where the active record is another login's, the record the session
writes names it on its first line, by its URL, as superseded, as the
shape above shows, and carries every entry of it forward: a session does
not edit a record another login posted.

## A rebase and the clearance

**A rebase that applies without a conflict keeps the `CLEARED`.** No
reviewer reads it. It voids the gates: they run again on the new tip,
and so does the check of *Signed and signed off*. This holds where the
rebase replays the cleared commits and no others. Then these two
commands print the same subjects in the same order, `<old base>` being
the parent the cleared sha was reviewed on:

```shell
git -C <wt> log --reverse --format=%s '<old base>..<cleared sha>'
git -C <wt> log --reverse --format=%s '<new base>..<new tip>'
```

It holds even where `main` already carried a hunk, which the rebased
commit then lacks.

**A rebase that applies without a conflict but replays other commits, or
drops one, keeps the `CLEARED` only where the branch's own added and
removed lines are unchanged.** Otherwise a fresh reviewer reads the
whole branch. For a one-commit branch, "unchanged" is proved by
comparing every added and removed line — bullets and blank lines
included, headers dropped — with explicit shas, each revision a separate
argument:

```shell
hdr='^(diff --git |index |@@ |--- (a/|/dev/null)|\+\+\+ (b/|/dev/null))'
before=$(git -C <wt> diff '<cleared sha>^' '<cleared sha>' \
           | grep -vE "$hdr" | grep -E '^[+-]')
after=$(git -C <wt> diff '<new tip>^' '<new tip>' \
          | grep -vE "$hdr" | grep -E '^[+-]')
printf '%s\n' "$before" | shasum
printf '%s\n' "$after"  | shasum
printf '%s\n' "$before" "$after" | grep -c .   # not zero
```

Equal hashes over a non-empty stream, and the clearance stands. A
branch of several commits is compared the same way over `<base>..<tip>`
at both ends.

**A rebase that resolved a conflict goes to a fresh reviewer**, who
reads the whole branch: the resolution is a change no reviewer has seen.
Say in the pull request which case it was.

**"This branch has conflicts" on GitHub is real** even where a local
rebase exits `0`: the forge does not apply a tree's `merge=union`.
Rebase, or merge `main` where `/btclib-pr`'s *Rebase and CI* says, run
the gates, and push.

**Where `main` has moved past the `origin/main` sha the verdict read the
prose on**, the orchestrator re-reads the branch's added lines on the
merge with the new `origin/main`, by the commands of *A pull request's
rounds*, at the rebase or at `/btclib-pr`'s *Landing*. The `CLEARED`
stands. A sentence the re-read finds false there is fixed in a new
commit, or by amend before the pull request is open (*Committing and
rebasing*). A fresh reviewer reviews that fix, and the branch is merged
only after its `CLEARED`, which ends the rounds (*The rounds*).

## Agents in each client

**Agents.** Claude Code reads them from `~/.claude/agents/*.md`. It
starts one with the `Agent` tool, naming the agent, and resumes one
with `SendMessage` to its id. That id is taken from the notification
whose summary names the agent's task, never from the dispatch several
turns back: a resume sent to the wrong id is a brief for another task.
Codex reads them from `~/.codex/agents/*.toml`. It starts one when
asked to spawn the custom agent of that name, and resumes one by a
follow-up to its agent thread. Starting always makes a new agent.

## Starting the reviewer in the other client

The session that starts a Codex reviewer, whose sandbox
`every-role.md`'s *Clients* describes, first runs, outside the
reviewer's sandbox, `git fetch origin`, the `merge-tree` of *A pull
request's rounds*, the checks of *Signed and signed off* with the
sign-off control, `uv sync --locked` where the worktree holds a
`uv.lock`, and the gates where no run on the sha is on the record, the
last two in the sandbox of *The gates* on an outside contributor's
branch. The brief carries them as runs on the record, the merge's tree
sha included, names the worktree, and asks for no heredoc. The session
removes the reviewer's directory once that reviewer's rounds end
(*Debris goes when its work ends*).

Claude Code starts a Codex reviewer with `codex exec`. That spawns no
custom agent by name, so the brief's first sentence says to read
`~/.codex/agents/reviewer.toml` and follow it. `-o` writes its last
message, the verdict, to a file. `-m` and `model_reasoning_effort` set
the model and the effort *Models* names. The other `-c` settings replace
any `writable_roots` of `config.toml` with the reviewer's directory,
turn off the network, which `config.toml` may turn on, and drop `/tmp`
and `$TMPDIR`, which `workspace-write` otherwise makes writable, a
worktree under `/tmp` included. `--ignore-rules` keeps out the user's
`.rules` files, whose allowed commands run outside the sandbox
(*Escalation under Codex*). `env -i` passes it only `HOME`, where Codex
finds its login, `PATH`, `UV_CACHE_DIR`, `UV_OFFLINE` and a `TMPDIR`
inside the reviewer's directory, where `mktemp` writes, so the variables
of the session that starts it, its tokens included, do not reach what
the reviewer runs.

The network is off because an input runs the branch's code, and the
sandbox still reads credentials such as `~/.codex/auth.json` and
`~/.gnupg`. With the network on, it could send them to any host, and
it could read the keychain too, through `gh auth token` and
`git credential fill`.

The session creates the reviewer's directory, syncs the worktree where
it holds a `uv.lock`, removes the verdict file, and starts the
reviewer. `-o` does not empty that file when a run starts. So a
resumed run's brief takes the last verdict from the file first, and a
verdict found there is the latest run's (*The rounds*). The `-u` keeps
the sync in the worktree's `.venv`, where the reviewer's `uv run`
looks for it. On an outside contributor's branch the sync is the
sandboxed one of *The gates* instead of the second command:

```shell
mkdir -p <work>/<name>/tmp
```

```shell
env -C <wt> -u UV_PROJECT_ENVIRONMENT \
  UV_CACHE_DIR=<work>/<name>/uv-cache uv sync --locked
```

```shell
rm -f <work>/<name>.last.md
```

```shell
env -i -C <work>/<name> HOME="$HOME" PATH="$PATH" \
  UV_CACHE_DIR=<work>/<name>/uv-cache UV_OFFLINE=1 \
  TMPDIR=<work>/<name>/tmp \
  timeout 900 codex exec -s workspace-write --skip-git-repo-check \
  --ignore-rules -m gpt-6.1-sol -c model_reasoning_effort=high \
  -c 'sandbox_workspace_write.writable_roots=["<work>/<name>"]' \
  -c sandbox_workspace_write.network_access=false \
  -c sandbox_workspace_write.exclude_slash_tmp=true \
  -c sandbox_workspace_write.exclude_tmpdir_env_var=true \
  -o <work>/<name>.last.md - \
  < <work>/<name>-brief.txt > <work>/<name>.log 2>&1
```

Codex starts a Claude Code reviewer with `claude -p --agent reviewer`,
outside its sandbox through an escalation request, as it does a git
write (*Git writes under Codex*). The brief goes on stdin, because
`--allowedTools` takes every argument after it, a trailing prompt
included. The session prepares the reviewer and its brief, and removes
its directory, as it does for a Codex reviewer.

The flags make its sandbox (`every-role.md`'s *Clients*) hold whatever
the user's settings say. `--setting-sources project` loads no user
settings, because the sandbox makes each directory their
`additionalDirectories` names writable. The reviewer agent is then found
through a link in the reviewer's directory. `--settings` turns the
sandbox on, refuses every host, and runs no command outside the sandbox,
even where it cannot start. `--permission-mode dontAsk` refuses a call
that would otherwise wait for an answer.

The sandbox also makes Claude Code's temporary directory writable. On
macOS that is `/tmp/claude-<uid>`, which holds Claude Code sessions'
scratchpads and the worktrees in them. So each run moves it to a new
directory with `CLAUDE_CODE_TMPDIR`, on a short path: past some length
Claude Code falls back to the default for sandboxed commands. `env -i`
passes only `PATH`, `CLAUDE_CODE_TMPDIR`, `ZDOTDIR`, the two `UV_`
variables, and what `claude` needs to find its login: `HOME`, `USER`,
and `CLAUDE_CONFIG_DIR` where it is set. On macOS, `claude` starts two
`zsh` shells outside the sandbox, and the reviewer's commands run in
`zsh` inside it. Each reads its startup files from `ZDOTDIR`, or from
`HOME` where that is unset. `ZDOTDIR` is `/var/empty`, which macOS
ships empty and owned by root, so neither the user's `~/.zshenv` nor a
file the reviewer writes is read. One it wrote in its own directory
would run outside the sandbox at the next run, a resumed one included.
The session's variables, its tokens included, then do not reach what
the reviewer runs.

The login the run finds is the one `claude auth login` saves. `env -i`
drops `ANTHROPIC_API_KEY` and `CLAUDE_CODE_OAUTH_TOKEN`, and
`--setting-sources project` drops an `apiKeyHelper` in the user's
settings. Without a saved login the run prints `Not logged in · Please
run /login` and exits `1`.

The session creates the reviewer's directory, links the agent into it,
and makes the run's temporary directory. `mktemp` prints its path,
which stands for `<tmp>` in the two blocks after it. The session then
starts the reviewer, and removes the temporary directory once the run
ends. The run starts `claude` only where `CLAUDE_CODE_TMPDIR` names a
directory, so an empty or missing value stops it:

```shell
mkdir -p <work>/<name>/.claude/agents
```

```shell
ln -s "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/agents/reviewer.md" \
  <work>/<name>/.claude/agents/reviewer.md
```

```shell
mktemp -d /tmp/rv.XXXXXX
```

```shell
sbx='{"sandbox":{"enabled":true,"failIfUnavailable":true,'
sbx="${sbx}"'"allowUnsandboxedCommands":false,'
sbx="${sbx}"'"network":{"strictAllowlist":true}}}'
env -i -C <work>/<name> HOME="$HOME" USER="$USER" PATH="$PATH" \
  ${CLAUDE_CONFIG_DIR:+"CLAUDE_CONFIG_DIR=$CLAUDE_CONFIG_DIR"} \
  CLAUDE_CODE_TMPDIR=<tmp> UV_CACHE_DIR=<work>/<name>/uv-cache \
  UV_OFFLINE=1 ZDOTDIR=/var/empty \
  sh -c 'test -d "${CLAUDE_CODE_TMPDIR:?}" && exec "$@"' sh timeout 1800 \
  claude -p --agent reviewer --effort high --max-turns 80 \
  --output-format text \
  --setting-sources project --permission-mode dontAsk \
  --settings "${sbx:?}" --allowedTools Bash,Read,Grep,Glob \
  < <work>/<name>-brief.txt > <work>/<name>.log 2>&1
```

```shell
rm -rf <tmp>
```

## Escalation under Codex

Under the approval policy `never`, which `~/.codex/config.toml` may
set, Codex makes no escalation request: its instructions then read
"Approval policy is currently never. Do not provide the
`sandbox_permissions` for any reason, commands will be rejected."
In Codex 0.163.0, the runs of `codex exec` measured ran under these
policies. `--approve-for-me`, which refuses `-s`, ran it under
`on-request` whatever `approval_policy` said. Without it,
`-c approvals_reviewer="auto_review"`, an automatic reviewer of the
requests, ran it under `on-request` where `approval_policy` was
`on-request` or set nowhere, and under `never` where it was `never`,
in `config.toml` or in a `-c`. With `approvals_reviewer` left at
`user`, it ran under `never`, `-c approval_policy="on-request"`
included. An `-a` before `exec` did not reach it. These are the
settings measured, not every one.

Interactive sessions in Codex 0.167.2 were measured with a `touch`
outside every writable root, which the sandbox refused, each started
with `-C` on a scratch directory, so the target was outside the
session's own directory, which is a writable root
([ISS ai-agents-process#278](https://github.com/btclib-org/ai-agents-process/issues/278)).
Under `never` it made no request; the model said the session forbids
them.
Started with `-a on-request` it asked, and ran the command once the
human approved. Started with `--approve-for-me` it asked, and the
automatic reviewer approved. So an interactive session that has to
escalate starts with `-a on-request` or `--approve-for-me`.

A command a `.rules` entry allows runs outside the sandbox with no
request in an interactive session under `never` and `on-request`, and in
`codex exec` under `never`. A rule allowing `git` makes every git write
`every-role.md`'s *Git writes under Codex* lists run that way, and an
interactive session has no `--ignore-rules` to set it aside.

Each run records its policy in its rollout, with credits or without,
so this re-checks a setting before an escalation is relied on. It runs
as one block, since Codex later compresses a rollout to `.jsonl.zst`,
which the glob does not match. `<settings>` are the flags under test,
`-s workspace-write` among them except with `--approve-for-me`:

```shell
set -- <settings>
id=$(codex exec --json --skip-git-repo-check "$@" 'Reply ok.' < /dev/null |
  jq -r 'select(.type == "thread.started") | .thread_id')
jq -c 'select(.type == "turn_context") | .payload
  | {approval_policy, approvals_reviewer}' \
  ~/.codex/sessions/*/*/*/rollout-*-"${id:?}".jsonl
```

## Writing a session's memory

**A client's persistent memory, as Claude Code's file-based memory, is
read only by that client's sessions on the maintainer's machine.** The
other client, the agent of `claude-implement.yml` and a contributor's
agent do not read it. So nothing another agent or a contributor must
follow lives only there, and each kind of fact goes where its readers
find it:

- how work is done, a technical lesson included, goes in the process,
  proposed as *Wrap-up* says;
- a decision about one issue or pull request goes on that issue or pull
  request, as `every-session.md`'s *When the human has to decide* and
  *A hold is recorded* say;
- the maintainer's standing permissions and preferences, and a
  permission given for a limited time, go in the memory of each client
  whose sessions are to follow them.

**A permission given for a limited time carries its end in memory**, and
is deleted once that end has passed.

## Closing collateral

- **Collateral is closed within the same session**, whoever filed it —
  writer, reviewer or orchestrator — and is worked as `/btclib-iss`
  says. What was filed while a pull request was worked goes, once the
  session is done with that pull request, to the same writer/reviewer
  pair; what was filed outside any, to a new pair. Each is taken to an
  open pull request or closed with the measurement that refutes it. The
  only exceptions are an issue in another repository or labelled
  `upstream-report`, one the maintainer suspended, one a `BACKLOG` row or
  an `EXPECTED_DRIFT` entry already points at, and one labelled `good
  first issue`; each is named in the report with its reason.
- **The session is not done while an issue it opened has no pull
  request** outside those exceptions. One that waits on the human is a
  question, or at night a deferred item, never a silent leftover.

## Night mode

`$PROCESS/process/night-mode.md` says how night mode is turned on and
off, and what the orchestrator follows while it is on.

## Wrap-up

Before the wrap-up, *Closing collateral*'s last bullet holds.

**Release every pull request the session claimed** (*A claim holds a
pull request's branch*).

**Remove what is left of what the session created** (*Debris goes when
its work ends*): worktrees, build directories, and caches in its scratch
directories. A worktree with uncommitted or unpushed work stays, and so
does anything another session made. Name both in the report. A read-only
tree, as Go's module cache is, is made writable first:

```shell
chmod -R u+w <dir>
```

```shell
rm -rf <dir>
```

At the end of a session, report these to the human, and edit none of
the files they name on your own:

- **What the session learned that could improve `AGENTS.md`**: a
  stable fact needed to work in this tree, what it says, and where it
  belongs.
- **Where the process fell short of what the session needed**: a rule
  unclear when it mattered, a case it had no answer for. Say what and
  roughly where — a file under `process/` or a skill.
- **Each class of defect the local rounds missed**, and where the next
  session will read it, as *The classes of defect found carry forward*
  says.

**A nil answer to any of these is one line in the report.**

These are proposals. Closing them is the human's call, and for the
process files the maintainer's, since they are shared. Each one that
needs their answer is put to them as its own decision
(`every-session.md`'s *When the human has to decide*).
