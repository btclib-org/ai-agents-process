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
  The same for a reviewer and a designer.
- **Before dispatching, ask whether the issue is collateral of a pull
  request this session worked** (*Collateral*).
- **The role map binds the brief.** A writer does not open pull requests;
  do not ask it to. The one exception, stated as such in the brief, is a
  one-line fix to a red `main`.
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
- **Re-measure every finding before passing it on**, the whole of it, not
  its cheap half. Answer each one: *accept* (say what changed) or
  *decline* (with the refuting measurement). A list found incomplete
  twice is deleted, not lengthened. From the second round, remind the
  reviewer of `REVIEWING.md`'s stopping criterion.
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
  collateral. *Clients* says how a worker is resumed, and that starting
  one always makes a new one.
- **Models**: in Claude Code the writer, the reviewer and the designer
  run on Opus at effort `high`, which their agent definitions set, so
  none follows the effort of the session that starts it: the exception
  *Which file wins* makes to the general model advice in `AGENTS.md`.
  Where that session's environment sets `CLAUDE_CODE_EFFORT_LEVEL`, the
  variable wins over the definition. A reviewer Codex starts with
  `claude -p --agent` takes the definition's model but not its effort,
  so its command in *Clients* names `--effort high`. The orchestrator
  may run on Opus. In Codex the agent files set no model: an agent runs
  on the one its spawn request names, else on the `[agents]` default of
  `config.toml`, else on the orchestrator's. A reviewer `codex exec`
  starts runs on `gpt-6.1-sol` at effort `high`, which its command in
  *Clients* names, rather than on `config.toml`'s `model` and
  `model_reasoning_effort`.
- **A worker that exceeds the time you set is interrupted**, not waited
  for.
- **Writing runs in parallel; heavy gating runs under the gate lock**
  (`every-session.md`'s *The machine is shared*). A reviewer that runs
  the gates itself is briefed with *The gates*.
- **A writer that has reported is sent nothing further until its
  reviewer has answered.**
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
  git -C "${PROCESS:?}" diff "${started:?}" "${next:?}" -- process/ skills/ scripts/
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

  Where the diff exited non-zero, or `process.sha` is missing or empty,
  the changed sections are not known. The session notes `HEAD` again as
  its skill's opening says, then re-reads whole every file under
  `process/`, `skills/` and `scripts/` it has read, and every one where
  it cannot tell. The next brief to each worker already running asks it
  to re-read its role's sections whole, and each file under `scripts/`
  it has read.

## Night mode

The human turns night mode on with `--night` in the arguments or in
words, and off in words, at any point. While it is on, the orchestrator
follows `$PROCESS/process/night-mode.md`, read whole when it is turned
on.

## Wrap-up

Before the wrap-up, *Collateral*'s last bullet holds.

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
  belongs. Nothing found is said in one line.
- **Where the process fell short of what the session needed**: a rule
  unclear when it mattered, a case it had no answer for. Say what and
  roughly where — a file under `process/` or a skill.
- **Each class of defect the local rounds missed**, and where the next
  session will read it, as *The classes of defect found carry forward*
  says.

These are proposals. Closing them is the human's call, and for the
process files the maintainer's, since they are shared. Each one that
needs their answer is put to them as its own decision
(`every-session.md`'s *When the human has to decide*).
