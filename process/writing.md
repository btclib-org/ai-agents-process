# The btclib-org process: writing

`every-role.md`, beside this file, opens the process: its opening says
which role reads this file. A section named here in italics with no file
is in one of the four files that opening names.

## Before starting

The writer does this for its issue or pull request; the orchestrator
does it before briefing anybody.

- Read `AGENTS.md`, `CONTRIBUTING.md` and `REVIEWING.md` from
  `origin/main`. The pull request is judged against `REVIEWING.md`.
- **Look for another session on it, all four ways**, each seeing what
  the others cannot: `git worktree list` (a session that has just
  started), remote branches, recent comments on the issue or pull
  request, and open pull requests citing the issue, by both commands
  below. The second, GitHub's search, also finds the issue cited only by
  its URL:

  ```shell
  gh pr list --repo <owner>/<repo> --state open --limit 200 \
    --json number,title,body \
    --jq '.[] | select((.title + .body) | test("#<issue>\\b")) | .number'
  ```

  ```shell
  gh pr list --repo <owner>/<repo> --state open --limit 200 \
    --search "<issue> in:title,body" --json number,title
  ```

  Each hit is read, since a number can be cited in passing. A pull
  request for the issue counts whatever its `closingIssuesReferences`
  says: a `(closes #<issue>)` in its title alone leaves that empty.
  `/btclib-iss`'s *Where a pull request is already open for an issue*
  says whose it is.

- **The agent of `claude-implement.yml` is another session.** It takes
  the issues that the header of `reusable-claude-implement.yml` in
  `btclib-org/.github` names under *Who starts it*, among them one an
  administrator labels `agent` and one a member opens, a session's own
  collateral included. It runs only in a repository whose `main` holds
  `.github/workflows/claude-implement.yml`. Where this answers `Not
  Found` (HTTP 404), no agent runs there and the rest of this bullet
  does not apply:

  ```shell
  gh api repos/<owner>/<repo>/contents/.github/workflows/claude-implement.yml \
    --jq .name
  ```

  Elsewhere, until its run on the issue has completed, no session takes
  the issue. A run carries the issue's title, not its number, and this
  prints the title of each run not completed:

  ```shell
  gh run list --repo <owner>/<repo> --workflow claude-implement.yml \
    --limit 200 --json displayTitle,status \
    --jq '.[] | select(.status != "completed") | .displayTitle'
  ```

  Its assessment is a comment by `claude`, and its pull request comes
  from `claude/issue-<n>`, which the checks above find.

- **Claim it before work starts.** The orchestrator comments on the
  issue or pull request that a session is taking it, in a comment
  starting `Claimed`; that comment is what the next session's check
  reads. On another person's pull request it also holds the branch
  (*A claim holds a pull request's branch*).
- **A branch left by a session that no longer runs is unreviewed work in
  progress**, however finished it looks. No process listing proves a
  session gone — an idle live session shows its id in no command line.
  Judge from the four checks above, the branch's last commit time and
  the worktree's last modification, and ask the human where it is not
  certain. Then hand it to a writer as a take-over, which makes the
  branch the writer's own: re-derive *Done when*
  against both `origin/main` and the branch, finish, rebase where it
  conflicts with `main`, gate, and a fresh review of the whole diff
  from its parent. Its worktree can be reused, reinstalling the build
  first (a flagged build may be in its `.venv`).
- **Look at the machine.** `uptime`, and `ps -eo pid,etime,pcpu,command |
  sort -k3 -rn | head`. Report to the human anything that looks orphaned;
  killing it is not yours (`every-session.md`'s *The machine is
  shared*).
- **Look at the free disk** before cloning, building or adding a
  worktree: `df -g <scratchpad>`. Under 30 GB available, the
  orchestrator sweeps (*The orchestrator, never a writer, sweeps*), runs
  `uv cache prune`, and reads it again; a writer tells the orchestrator.
  Still under 30 GB, stop and tell the human: work not yet started needs
  room to clone and build. A gate on work already started runs down to
  `GATE_LOCK_DISK`, 20 GB. `uv cache prune` removes the cache's unused
  entries and its cached environments, `uvx`'s among them, which the next
  `uvx` rebuilds offline. It waits while another uv process runs, without
  holding back one that starts meanwhile. It exits `2` once
  `UV_LOCK_TIMEOUT` passes, 5 minutes by default
  ([uv's *Clearing the cache*](https://docs.astral.sh/uv/concepts/cache/#clearing-the-cache)),
  and the second read goes on without it. `--force` skips that wait and
  is not used.

## Writing work

The writer's section; the reviewer judges its result.

**Before handing over, every item holds:**

- [ ] the tip is pushed, and `git ls-remote origin <branch>` matches
      `HEAD`, unless *Committing and rebasing* holds the push
- [ ] `git log --format='%h %G? %GS' <base>..` shows no `N` on the
      session's own commits (*Signed and signed off*)
- [ ] the `Sign-off` script exits `0` on `<base>..`, or after a merge of
      `main` on the ranges that leave out `main`'s commits (*Signed and
      signed off*)
- [ ] every gate *The gates* asks of this tip ran on it, committed,
      with exit code `0`, as it says
- [ ] *Sourcery and CodeRabbit before a push* holds
- [ ] `git status --porcelain` is empty in the worktree, checked after
      the last gate, and on an outside contributor's branch in the
      status file of each gate too (*The gates*)
- [ ] the subject that lands carries the right citation, and the body
      carries no stray closing keyword
- [ ] the commit message was re-read, not carried by `--no-edit`
- [ ] every claim in prose that lands was measured
- [ ] the diff's added lines were searched for a numeral beside an
      upstream name (*No counts*)
- [ ] an edit inside a filled paragraph refilled it whole, proved
      whitespace-only against the committed text (`git diff
      --word-diff=porcelain <sha> -- <file> | sed '1,/^@@/d' | grep -c
      '^[-+]'` answers `0`): width gates bound the longest line, not the
      fill
- [ ] collateral filed, by number
- [ ] where the change touches a rule the tree states, or makes a
      sentence false or narrower, the search of *A rule stated more
      than once* is in the report
- [ ] where the change removes tests, each refusal they asserted that a
      public caller still reaches is asserted again through that caller
- [ ] the fix of a blocking finding that rests on an input adds that
      input as a test, where the tree tests that code
- [ ] the report says what was **not** checked, and why

### A rule stated more than once

**Before writing, search for every sentence that states the rule you
change**, and for every sentence the change makes false or narrows, rule
or not: a claim narrowed in one comment still stands, unnarrowed, in the
docstring and the documents beside it (*Where your diff falsifies a
sentence elsewhere*). Run one search over every file `git ls-files`
lists, with a pattern for each way the rule or the claim is worded,
matched across line breaks (*`grep` reads lines, and prose wraps*). List
each hit as `file:line` with what you do with it. Change them all in one
round. A restatement becomes a pointer to the section that holds the
rule (`every-session.md`'s *Write plainly*), and a sentence made false
is corrected. The report carries the patterns and the hits. The reviewer
runs the same search, adds the patterns it would have used, and reads
the files where the rule or the claim is stated. A sentence either
search finds and the list lacks is a finding.

**A tree-wide sweep starts from a census** of every spelling over `git
ls-files`, and ends at the census re-run answering zero, its exceptions
listed. It names any file class it left out.

**A pointer keeps every condition of the text it replaces**: the target
states each one, or the condition stays where it was.

**Each item of a list states its own condition**, or the list's opening
states it for every item: a condition one item carries does not reach
the items beside it.

**The organization's copies are in the list.** Section 14 of the
organization's standard lists the files copied verbatim into every tree,
and their rules count too. A copy the change cannot touch is filed in
btclib-org/.github's tracker as collateral (*Collateral*).

### What the prose that lands may say

- **No entry in `CHANGELOG.md` or `RELEASE_NOTES.md`.** In a tree that
  publishes, section 9 of the organization's standard (*`CHANGELOG.md`
  and `RELEASE_NOTES.md`*) says which pull request adds an entry under
  `changelog/next/`, and what the entry holds. A tree's
  `CONTRIBUTING.md` that still asks for an entry in either file is a
  drifted copy, and the standard wins (*Which file wins*). An entry in
  either file found on a branch is dropped. A release's own pull request
  writes that release's section, and so does the pull request that moves
  an entry left in `changelog/next/` into it, as section 9 says.
- **Backward compatibility is not a constraint.** Choose the most
  rational design and document what it breaks in the commit message and
  the pull request body.
- **No counts** — not entries, tests, errors or files. Exhaustive words
  ("the only three", "every other") hold only where a command counted
  them, and then the command is written, not the total. A sentence about
  several walks, functions or files is checked against each one it
  covers, not only the one in view. A count that decided the change
  belongs in the report and the pull request body. A figure of an
  upstream source, as a vector file's cases or a tool's version, stands
  only in the file that pins it (a vendored vector's pin, a tool's
  version in its configuration), and nowhere where none does: the
  diff's added lines are searched for a numeral beside an upstream name
  (vectors, cases, tests, a tool and its version). A list of call sites
  reads as the whole population and goes stale at the next call: state
  what decides membership, and label names as examples.
- **Say what is true now.** No "was", "has always", "is now". The
  exception is the defect being corrected, and that "before" is measured
  against a snapshot. A rule carries no attribution or date: its pull
  request records who decided it and when.
- **Do not restate the code in a comment.**
- **A second reason gets its own paragraph.** A clause grafted into a
  standing paragraph inherits its subject, and every later sentence
  becomes false of it.

### Citations and closing keywords

These are written first by the writer, in the commit, and re-checked by
the orchestrator in the pull request. A batch of ports cites the issues
in its pull request's body, not its subject, as `/btclib-iss`'s *Ports
of the standard* says.

- **The citation goes on the subject that lands.** Read the setting:
  `gh api repos/<owner>/<repo> --jq .squash_merge_commit_title`. At
  `COMMIT_OR_PR_TITLE` a one-commit branch lands under its commit's
  subject; a multi-commit branch under the pull request's title.
- **`(closes #N)` where the branch closes the issue, `(issue #N)` where
  it advances it without closing, nothing where it does neither** — on
  the subject. Across trackers: `(closes owner/repo#N)`. This is the
  standard's rule (section 11, *What a pull request says it is*); a
  tree's landed subjects may drift from it and are not the model.
  Nothing landed is rewritten.
- **An issue owed by several trees is closed by the last landing only.**
  Where switching that last tree's `(issue …)` to `closes` would send an
  already cleared branch back to review, land it as cleared and close the
  issue by hand once it lands, with a comment listing every landing and
  the trees that needed nothing. Where the last tree goes back to review
  anyway, switch it in the same amend. A port of the standard is the
  exception: `/btclib-iss`'s *Ports of the standard* says how its issue
  closes.
- **An issue several pull requests of one repository advance is closed by
  the one that meets its *Done when*.** That pull request carries
  `(closes #N)`, even where each earlier one carried `(issue #N)`. Read
  the *Done when* against the branch before choosing the word.
- **GitHub reads a word, not a sentence.** Close, closes, closed, fix,
  fixes, fixed, resolve, resolves and resolved all arm the reference
  adjacent to them, adjective included, and "this does not close #N"
  closes it. A qualified `owner/repo#N` fires from any repository; a
  bare `#N` only in its own. The sentence declaring there is no keyword
  is the likeliest to carry one: write it without the number or without
  the verb.
- **One keyword closes one issue, and does not cross a newline.** "Closes
  #1, #2" closes `#1`. Write the closing block one keyword per line.
- **No `@` mention in a pull request body or a commit message**, in any
  repository. A mention goes in a comment, so a hold's comment that
  mentions the maintainer stays (`every-session.md`'s *When the human
  has to decide*).
- **Sweep before handing over**: grep the commit body (and later the pull
  request body) for every form of the three words next to a reference.
  The same sweep finds bare references with `perl -ne 'print if
  /(?<![\/A-Za-z0-9.\-])#[0-9]+/'`, whose `0-9` keeps
  `btclib-org/btclib-secp256k1#N` from reading as bare. It finds a
  mention with
  `grep -nE '(^|[^][:alnum:]._+-])_*@[[:alnum:]]' -- <file>`, which
  exits `1` where it finds none and `2` where it cannot read the file.
  It skips an `@` after a letter, a digit, `]`, `.`, `+` or `-`, or
  after a run of `_` that follows one of these, as in
  `noreply@anthropic.com` and `claude[bot]@users.noreply.github.com`,
  and lists one after `_` elsewhere, as in `_@name_`. It lists the
  non-ASCII codepoints (Python, `ord(c) > 127`) of both texts, and of
  every other text posted on a forge, other than the em dash and the
  ellipsis this file uses: a CJK character mid-word is a generation
  artefact no gate reads.

### The gates

- **The gates are the tree's**: `CONTRIBUTING.md`'s last section. Where
  it is silent, what CI runs — typically the suite with its coverage
  floor, `pre-commit run --all-files`, and the docs build with `-W`,
  which pre-commit rarely covers. **Run all of them** unless that
  section, or else the bullets from here to *Every commit you hand over
  is gated*, scale them by what the diff touches. "This gate does not
  read the changed files" is a claim like any other and is measured
  first: a docs build may include `CHANGELOG.md`, a test may read every
  tracked file. `<base>` below is the pinned `origin/main`
  (*`refs/remotes/origin/main` is shared by every worktree*). The report
  and the pull request's `## Evidence` give a gate those bullets leave
  to CI as `left to CI`, with the command that decided it and its exit
  code.
- **The hooks run on the changed files**: the tree's own `pre-commit
  run`, here `uvx pre-commit run`, takes `--from-ref` and `--to-ref` in
  place of `--all-files`. pre-commit then reads the changed files from
  `git diff <base>...HEAD`, and exits non-zero where that diff fails. A
  hook with `pass_filenames: false` or `always_run: true` still reads
  what its own command reads, as btclib-node's `core-citation-pin` reads
  what `git ls-files` lists. Where the suite is left to CI and the diff
  changes only Markdown, the hooks run outside the gate lock:

  ```shell
  wt=<wt>
  base=<base>
  env -C "${wt:?}" uvx pre-commit run --from-ref "${base:?}" --to-ref HEAD
  ```

- **The suite is left to CI where no test of the tree reads a file of
  the diff.** This prints each place where a pytest suite may read one,
  a renamed file under both its names, and prints nothing and exits `0`
  where none does. Any line, or another exit, runs the suite, and so
  does a suite that is not pytest's. The script's header says what it
  misses, which CI's run reads. It runs outside the gate lock:

  ```shell
  scratch=<scratch>
  wt=<wt>
  base=<base>
  env -C "${scratch:?}" uv run --no-project --python 3.15 \
    python -I "${PROCESS:?}/scripts/suite-reads.py" "${wt:?}" "${base:?}"
  ```

- **The docs build runs only where the diff touches what it builds**: a
  file under the directory it builds, the package whose docstrings it
  renders, `pyproject.toml` or `uv.lock`, or a file a page names. This
  lists the pages that name a changed file. It reads each path of the
  diff as data, NUL-terminated, never as shell text, and `--no-renames`
  gives a renamed file under both its names, where a plain
  `--name-only` gives the new one alone. It exits `1` with no output
  where no page names any. Where HEAD holds no source directory, or git
  fails, it exits `2` with a message. Any other exit runs the build.
  Elsewhere it is left to CI:

  ```shell
  wt=<wt>
  base=<base>
  src=<docs source>
  rc=1
  list=$(mktemp)
  if ! git -C "${wt:?}" cat-file -e "HEAD:${src:?}"; then
    echo "HEAD holds no ${src}" >&2
    rc=2
  elif ! git -C "${wt:?}" diff -z --name-only --no-renames \
    "${base:?}...HEAD" > "$list"; then
    rc=2
  else
    while IFS= read -r -d '' name; do
      got=0
      out=$(git -C "${wt:?}" grep -l -F -e "$name" HEAD -- "${src:?}" 2>&1) ||
        got=$?
      if [ "$got" -eq 0 ]; then
        printf '%s\n' "$out"
        [ "$rc" -eq 2 ] || rc=0
      elif [ "$got" -ne 1 ] || [ -n "$out" ]; then
        printf '%s\n' "$out" >&2
        rc=2
      fi
    done < "$list"
  fi
  rm -f "$list"
  (exit "$rc")
  ```

- **A merge of `main` asks for no new local gate** where it resolved
  nothing (`local-review.md`'s *A merge of `main` and the clearance*),
  brings in no file the branch changes, and `main` is green: the latest
  completed push run of each of its workflows succeeded, read when the
  session looks, with no wait for a run in progress. CI gates the merged
  head. Each command below holds only where it prints nothing and exits
  `0`. The first prints each file both sides change, and `pipefail`
  makes a stage that fails fail it. The second prints each workflow
  whose latest completed run did not succeed, or `no runs` where none
  has completed. It reads the newest 200 completed push runs, so a
  workflow whose last run is older than those, or that has no completed
  run, is not read:

  ```shell
  wt=<wt>
  m=<merge>
  a=$(git -C "${wt:?}" diff --name-only --no-renames "${m:?}^2...${m:?}^1") &&
    b=$(git -C "${wt:?}" diff --name-only --no-renames "${m:?}^1" "${m:?}") &&
    (set -o pipefail; printf '%s\n' "$a" "$b" | grep . | sort | uniq -d)
  ```

  ```shell
  repo=<owner>/<repo>
  gh run list --repo "${repo:?}" --branch main --event push \
    --status completed --limit 200 --json workflowName,conclusion \
    --jq 'if length == 0 then "no runs" else reduce .[] as $r ({};
    .[$r.workflowName] //= $r.conclusion) | to_entries[]
    | select(.value != "success") | .key end'
  ```

- **Every commit you hand over is gated, after it is committed.** The
  merge of `main` above is exempt, and so is a commit kept only to
  preserve work in progress, amended away before anything is offered. A
  run before the commit does not count, even where the content looks
  identical: a hook at commit time can change what is committed. Where a
  gate's fixer changes files, commit the change and run that gate again.
  `pre-commit run --all-files` walks `git ls-files`, so a file the
  branch adds is gated only once staged: the report says the gate saw
  the new files.
- **Read exit codes, not output.** `… > log 2>&1; echo $?`. A
  multi-batch hook's tail can show a clean batch after a failed one.
- **A local gate run that fails because the network is down has not
  run.** Its log names a failed name resolution or connection, as git's
  `Could not resolve host:` or uv's `dns error` do, and a known host
  fails in the same minute: `git -C <wt> ls-remote origin`. The log
  alone does not say the network is down, since a dead host or a lapsed
  domain prints the same. The gate is re-run once that host answers, and
  the earlier exit is never reported as its result; until then it is
  reported as not run. A failure that repeats once the network answers
  is the gate's red. The re-run is not the retry *A failure that does
  not reproduce is measured* forbids. A CI check is re-run as
  `/btclib-pr`'s *Rebase and CI* says, and a sandbox with the network
  off by design is the case of *An outside contributor's branch*.
- **A gate can leave the tree dirty**: in-place fixers exit having
  modified files. Check `git status --porcelain` afterwards. On an
  outside contributor's branch it runs in a sandboxed call of its own,
  as *An outside contributor's branch* says.
- **An install that Aikido Device Protection refuses is a stop.**
  Nothing goes around it: no build from a clone or a `git archive`, no
  other index, no wheel fetched by hand, no TLS change, no `aikidoctl
  pause`. The gate it holds is reported as not run.
- **An outside contributor's branch, or a tree that merges its head, is
  gated in a sandbox with no network and no credentials** (`/btclib-pr`'s
  *Outside contributors*, and the octopus of its *Landing*). Its gates
  run code nobody in btclib-org wrote: `uv sync` builds the branch's
  project with the backend its `[build-system]` names, and the suite and
  the hooks run its code. Outside the sandbox the session fetches only
  what `main` names and installs, from a new detached worktree at
  `origin/main` and one at the branch's merge base (below), into a new
  directory `<sbx>` in the scratch directory.
  The fetch and every gate take the same variables, so that pre-commit
  picks the same hook environments outside and inside:

  ```shell
  mkdir -p <sbx>/home <sbx>/tmp
  ```

  ```shell
  env -i -C <main wt> HOME=<sbx>/home PATH="$PATH" TMPDIR=<sbx>/tmp \
    UV_PYTHON_INSTALL_DIR="$(uv python dir)" UV_CACHE_DIR=<sbx>/uv-cache \
    UV_TOOL_DIR=<sbx>/uv-tools PRE_COMMIT_HOME=<sbx>/pre-commit \
    sh -c 'uv sync --locked --all-groups && uv run pre-commit install-hooks'
  ```

  A tree with no uv project, with no `pyproject.toml` as in this
  repository, has nothing to sync. Its fetch takes pre-commit with
  `uvx`, at its newest release since nothing locks it, and the hooks
  `main`'s `.pre-commit-config.yaml` pins. It runs from the same
  worktrees, never from the branch: the install builds what the
  branch's `.pre-commit-config.yaml` names, and would run the
  contributor's code with the network on:

  ```shell
  env -i -C <main wt> HOME=<sbx>/home PATH="$PATH" TMPDIR=<sbx>/tmp \
    UV_PYTHON_INSTALL_DIR="$(uv python dir)" UV_CACHE_DIR=<sbx>/uv-cache \
    UV_TOOL_DIR=<sbx>/uv-tools PRE_COMMIT_HOME=<sbx>/pre-commit \
    uvx pre-commit install-hooks
  ```

  Then each gate runs offline, under `sandbox-exec`, in `<gate wt>`,
  never in `<wt>`, the branch's worktree where the session commits.
  `<gate wt>` is a new worktree detached at `<sha>`, the commit it
  gates, named as *Your own worktree* says with `gate-<short sha>` for
  its role; for the octopus it is the worktree that merges the heads.
  Its git directories, its gitlinks' paths and its configuration are
  read before its first gate, into files of the scratch directory
  outside `<sbx>`, where the gate cannot write:

  ```shell
  git -C <wt> worktree add --detach <gate wt> <sha>
  ```

  ```shell
  gwt=<gate wt>
  git -C "${gwt:?}" rev-parse --path-format=absolute --git-dir \
    --git-common-dir > <scratch>/<name>-git-dirs &&
  git -C "${gwt:?}" ls-files -s |
    awk -F '\t' '$1 ~ /^160000 / { print $2 }' > <scratch>/<name>-gitlinks &&
  git -C "${gwt:?}" config --list --show-scope --no-includes \
    > <scratch>/<name>-config
  ```

  The shell that runs the gates sets the sandbox's command first:

  ```shell
  { read -r gd && read -r gc; } < <scratch>/<name>-git-dirs &&
  set -- env -i -C <gate wt> HOME=<sbx>/home PATH="$PATH" TMPDIR=<sbx>/tmp \
    UV_PYTHON_INSTALL_DIR="$(uv python dir)" UV_CACHE_DIR=<sbx>/uv-cache \
    UV_TOOL_DIR=<sbx>/uv-tools PRE_COMMIT_HOME=<sbx>/pre-commit UV_OFFLINE=1 \
    sandbox-exec -f "${PROCESS:?}/scripts/gate-sandbox.sb" \
    -D WT="$(realpath <gate wt>)" -D SBX="$(realpath <sbx>)" \
    -D HOME="$(realpath "$HOME")" -D UV_PYTHON="$(uv python dir)" \
    -D GIT_DIR="${gd:?}" -D GIT_COMMON_DIR="${gc:?}"
  ```

  Each gate is `"$@"` followed by its command, the first `uv sync
  --locked`:

  ```shell
  "$@" uv sync --locked
  ```

  A tree with no uv project has no sync gate, and its hooks gate below
  runs `uvx pre-commit run` in place of `uv run pre-commit run`.

  Once the gate's call has returned, `git status --porcelain` runs as a
  sandboxed call of its own. Its output goes to a file of the scratch
  directory outside `<sbx>`, which the sandbox lets no process open for
  writing, and the shell outside opens it and appends the exit, so no
  process the gate left holds it. It reads no file the gate can write
  but the tree itself, and a file an `include` or `includeIf` of the
  repository's configuration names, which can lie under `<sbx>/home`:

    - `GIT_CONFIG_GLOBAL` and `GIT_CONFIG_NOSYSTEM` leave it the
      repository's own configuration, where `<sbx>/home/.gitconfig` is
      the gate's to write;
    - `core.attributesFile` and `core.excludesFile` drop the attributes
      and the ignore rules git reads by default under
      `<sbx>/home/.config/git/`, which the first two leave in place;
    - `--ignore-submodules=all` starts no `git status` inside a
      gitlink's directory, which would read the configuration of a
      repository the gate left there, and through its `core.worktree`
      could report a directory of its choosing;
    - `core.fsmonitor=false` leaves no file-system monitor to tell git
      which files changed;
    - `--ignored` lists an ignored file too, as one a `.gitignore` the
      gate wrote hides.

  ```shell
  "$@" env GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 \
    git -c core.attributesFile=/dev/null -c core.excludesFile=/dev/null \
    -c core.fsmonitor=false status --porcelain --ignored \
    --ignore-submodules=all > <scratch>/<name>-status
  echo "EXIT_status=$?" >> <scratch>/<name>-status
  ```

  What a gitlink's directory holds is then read by the shell outside,
  with `find` and no git. It adds a line to the same file for each
  `.git` below `<gate wt>` but its own, file, directory or link, in any
  case, since macOS's file system may ignore case; for each gitlink whose
  path is not an empty directory; where `find` or `ls` fails; and for
  each `include` the repository's configuration held before the gate:

  ```shell
  gwt=<gate wt>
  st=<scratch>/<name>-status
  find "${gwt:?}" -mindepth 1 -iname .git ! -path "${gwt:?}/.git" \
    -exec printf 'nested: %s\n' {} + >> "${st:?}" ||
    echo "EXIT_find=$?" >> "${st:?}"
  while IFS= read -r p; do
    d=${gwt:?}/$p
    { [ -d "$d" ] && [ ! -L "$d" ] && [ -z "$(ls -A "$d" 2>&1)" ]; } ||
      printf 'gitlink: %s\n' "$p" >> "${st:?}"
  done < <scratch>/<name>-gitlinks
  grep -iE '^(local|worktree)[[:space:]]+include' <scratch>/<name>-config |
    sed 's/^/include: /' >> "${st:?}"
  ```

  The gate left the tree clean only where that file holds
  `EXIT_status=0` and no other line but a `!!` line for what the gates
  write and the tree's own `.gitignore` files name: `.venv/`,
  `__pycache__/`, `.coverage` and the tools' caches show there on every
  run (*A gate can leave the tree dirty*). Any other line is a change,
  and so is a line of the check above. Nothing the gate prints counts. A
  fixer's change is read with `git diff`, run the same way, and made
  again in `<wt>`.

  On the octopus, `git status` lists the files the merge staged before
  any gate runs. So the status block also runs once before the first
  gate, with `<scratch>/<name>-base` in place of
  `<scratch>/<name>-status`, and a line that file holds is no change. A
  gate that writes a staged file changes that file's line, as
  `scripts/test-gate-sandbox.sh` shows.

  A process the gate leaves running keeps the sandbox's limits, and can
  still write in `<gate wt>` and `<sbx>` after the check, as
  `scripts/test-gate-sandbox.sh` shows. The process does not bound it:
  the check says what the gate had changed when it ran.

  A change the check does not see stays in `<gate wt>` and goes with it:
  nothing of `<gate wt>` reaches `<wt>` but a fixer's change the session
  reads and makes again.
  A gate that passes is no proof that it tested the committed files
  unchanged, since the branch's code runs in it and the check shows only
  what git sees. The session reads the gate's result with the status
  file, and reports both.

  A branch's lock can be an older `main`'s, as on PR
  btclib-org/btclib#3079, whose head locked a build backend `main` had
  since bumped: the offline `uv sync --locked` then wants a version that
  fetch did not bring and the branch did not add. In a tree with no uv
  project, the branch's `.pre-commit-config.yaml` can pin an older
  `main`'s hooks the same way. So the fetch runs a second time, into the
  same `<sbx>`, from a new detached worktree at the branch's merge base
  with `origin/main`, which this prints, wherever that is not
  `origin/main` itself. The merge base is a commit of `main`, so nothing
  it names is the contributor's; where the branch has merged `main`, it is
  that `main`:

  ```shell
  wt=<wt>
  git -C "${wt:?}" merge-base origin/main HEAD
  ```

  In the sandbox, the hooks gate names the diff's files with `--files`,
  in place of `--from-ref` and `--to-ref`. Given neither `--files` nor
  `--all-files`, pre-commit first stashes the unstaged changes, and its
  stash runs `git write-tree`, which takes `index.lock` in the git
  directory the profile keeps read-only: the run exits `3` before any
  hook runs. `--diff-filter=d` leaves out a deleted file, which
  pre-commit's own `--from-ref` skips too. Where the diff only deletes,
  the list is empty, and an empty `--files` stashes again, so the hooks
  run with `--all-files` instead. The paths are read NUL-terminated,
  never as shell text. Each is passed as `./<path>`, so that a name
  starting with `-` is not read as one of pre-commit's options, as `-h`
  would print its help and exit `0`; pre-commit turns it back into the
  path. pre-commit runs once, so the exit is its own; where git fails,
  it exits `2`. It runs in the shell that set the sandbox's command, as
  `"$@"` followed by pre-commit, and git reads the list in `<wt>`. On
  the octopus `<sha>` is the `main` its worktree was added at, so the
  list is empty and the hooks read the whole merge:

  ```shell
  wt=<wt>
  sha=<sha>
  base=<base>
  rc=0
  files=()
  list=$(mktemp)
  if ! git -C "${wt:?}" diff -z --name-only --diff-filter=d \
    "${base:?}...${sha:?}" > "$list"; then
    rc=2
  else
    while IFS= read -r -d '' name; do
      files+=("./$name")
    done < "$list"
    if [ "${#files[@]}" -eq 0 ]; then
      files=(--all-files)
    else
      files=(--files "${files[@]}")
    fi
    "$@" uv run pre-commit run "${files[@]}" || rc=$?
  fi
  rm -f "$list"
  (exit "$rc")
  ```

  `scripts/gate-sandbox.sb` says what the sandbox allows, and why the
  paths go through `realpath`. It reads no file under `$HOME` but uv's
  interpreters, `<gate wt>`, `<sbx>` and the worktree's git directories,
  so the keychain and `git credential fill` fail inside it, and
  `~/.gnupg` and the tokens of `gh` and Codex cannot be read; files
  outside `$HOME` are read, other sessions' scratch directories
  included. It writes in `<gate wt>` and `<sbx>` only, never in a git
  directory, and signals only its own processes.

  Apple Events still leave it, so code inside can drive any application
  the session's host application holds Automation permission for:
  Terminal's `do script`, for one, runs a command outside the sandbox,
  with the network and the credentials. Where such a permission is held,
  the sandbox does not keep the network and the credentials from the
  branch's code.

  **No git command runs outside the sandbox in `<gate wt>` or `<sbx>`
  once a gate has run there.** A gate can leave a repository there,
  under a gitlink's directory, and git outside the sandbox then reads
  that repository's configuration, whose keys can name a program to run.
  `git status` reads it even with `--ignore-submodules=all`, and so do a
  commit and a merge (ISS btclib-org/ai-agents-process#548). The one
  exception is the removal,
  `git -C <wt> worktree remove --force <gate wt>`. It parses no
  configuration the gate left under a gitlink's directory, as
  `scripts/test-gate-sandbox.sh` shows. It does read `<gate wt>/.git`,
  the file that names the git directory, and exits `128` where that file
  is not valid; the sandbox denies the gate writing it. A commit, a
  merge of `main`, a push, the Sign-off check and the CodeRabbit CLI run
  in `<wt>`, where no gate runs.

  Nothing in `<wt>`, `<gate wt>` or `<sbx>` runs outside the sandbox,
  except the Codex reviewer's inputs, which run from `<gate wt>`'s
  `.venv` in its own sandbox (*Clients*). That one has the network off
  too, though it reads `~/.codex/auth.json` and `~/.gnupg`. `<sbx>` and
  `<gate wt>` are new for each head. The Sign-off check runs as *Signed
  and signed off* says. A commit or a merge in `<wt>` runs with `git -c
  core.hooksPath=/dev/null`, which runs no hook, where `git commit
  --no-verify` still lets `prepare-commit-msg` and `post-commit` run,
  and with no path under `<wt>`, `<gate wt>` or `<sbx>` on `PATH`.
  `<gate wt>`, `<sbx>` and the worktrees at `origin/main` and at the
  merge base go once the head's gates, and every reviewer's inputs the
  session runs there, are done (*Debris goes when its work ends*).

  The dedicated reviewer runs none of the branch's code
  (`local-review.md`'s *Every reviewer tries to break the change*). It
  runs in the writer's client, whose commands have the session's network
  and credentials, and a brief cannot make each command it writes take
  the sandbox's form; the session already runs that form for the gates.
  Its brief says the branch is an outside contributor's, and carries the
  session's sync and gate runs of this sandbox on the record. The
  reviewer writes its inputs in its own directory. The session reads
  each, copies it into `<sbx>`, and runs it as a gate, with `uv run` in
  place of `uv sync --locked`, then resumes the reviewer with the
  results on the record. An input a resumed verdict names as not run is
  run the same way. `local-review.md`'s *The rounds* says which
  `CLEARED` counts as the dedicated reviewer's.

  A gate or an input that fails in the sandbox for want of the network,
  or of a package, a version of one or a hook that the branch adds or
  changes and neither fetch holds, is not run locally. For a gate, the
  session relies on CI's run of it on the head, and says so; an input
  goes to the human as *Clients* says. A test whose bind or connection
  is refused, loopback included, fails for want of the network. A suite
  with such a failure is then not run locally, however few tests failed:
  it is not read as passing apart from them, nor rerun with them
  deselected (`REVIEWING.md`'s *Whole, whoever runs it*).

  The sandbox refuses with an error that carries `[Errno 1]`, as
  `PermissionError: [Errno 1] Operation not permitted`.
  `[Errno 13] Permission denied`, as on a Unix socket's path, is not the
  sandbox's refusal. A test that catches the refusal can fail with no
  errno: btclib-org/btclib-node's `PortPool.draw`, in
  `tests/__init__.py`, raises an `OSError` saying every port is held.
  What shows the refusal is the kernel's line for it,
  `deny(1) network-bind` or `deny(1) network-outbound`, naming a process
  of the gate, which `grep -F 'deny(1) network-'` finds. `log show` can
  lose those lines, so `log stream` records them while the gate runs,
  into a file of the scratch directory outside `<sbx>`, where the gate
  cannot write. The session starts it in the gate's shell, after the
  gate's `gate_wait`:

  ```shell
  /usr/bin/log stream --style compact \
    --predicate 'sender == "Sandbox" AND eventMessage CONTAINS "network"' \
    > <scratch>/<name>-sandbox.log & stream=$!
  ```

  The gate then runs as *The gate lock*'s block says, and the session
  stops the collector before the gate's `echo`:

  ```shell
  kill "${stream:?}" || echo "log stream had ended"
  ```

  Where `log stream` had already exited, the `||` keeps a shell under
  `set -e` from ending at the `kill`, before the gate's code is printed.

  The kernel does not log every refusal. Where neither `[Errno 1]` nor a
  kernel line shows one, the test failed. In `zsh`, `log` is a builtin,
  hence `/usr/bin/log`.
- **The whole suite, never a narrowed run**, for anything you write
  down. `-k` and single files relax the coverage floor.
- **A suite that a required check runs in more than one lane is run in
  each**, and a coverage floor on their union is a gate too, as the
  tree's `CONTRIBUTING.md` gives them (btclib's *Reproducing what CI
  runs*). A test that needs what one lane lacks skips itself there by
  the tree's own means: an `import` of it at the top of the module fails
  that lane's collection.
- **Coverage at 100% and defensive branches.** Move the safety where a
  test can trip it (usually a fixture) and write the test. Before saying
  the floor required a test, delete it and run the whole suite.
- **A failure that does not reproduce is measured, not retried.** Rule
  out load first; measure the rate on a quiet machine, then open an
  issue. A branch that fails differently on every run cannot land,
  whatever the last run says.
- **Every worker that gates reports the CPU idle percentage, the load,
  the memory pressure level, the percentage of memory free and the disk
  free at each run** (what `gate_wait` prints, naming the readings it
  could not make), a reviewer running the gates itself included.
- **Call `gate_wait` before each heavy gate** inside the lock (*The gate
  lock*): the suite, the hooks there, and the docs build. `gate_take`
  waits once, at the start, and the load, the memory and the disk move
  while a worker holds a slot. `gate_wait` returns once the idle CPU,
  the load, the memory and the disk admit a gate, as the header comment
  of `$PROCESS/scripts/gate-lock.sh` says, and prints the readings the
  report copies.
- **`--basetemp=<work>/pytest-<branch>`** (*The scratchpad is shared*),
  outside the worktree, the same name on every run of that branch,
  removed once the branch's gates are done (*Debris goes when its work
  ends*). A teardown `OSError` or `FileNotFoundError` on `popen-gw*` is a
  neighbour's run on a shared path (`ps` shows it), not a failing test.
- **Build artefacts outside the worktree** (`uv build --out-dir
  <scratch>/…`): an untracked file inside it fails `check-sdist` while
  `git status` reads clean.
- **A workflow change is dispatched on the branch**: `gh workflow run
  <file>.yml --ref <branch>`. A workflow that has never landed on the
  default branch is exercised first by the pull request's own run, which
  is read before merging. A script extracted
  from the workflow tests the shell, not what the runner supplies. Read
  the log for *why* it is green, and quote it in the report.
- **Platform-dependent behaviour** (timeouts, clocks, sockets, paths,
  signals, C extensions, runtime limits) dispatches the `os-*` sweeps on
  the branch: `gh workflow run os-windows.yml --ref <branch>`, and
  `os-macos.yml` where macOS is in question. Which sweeps a tree has,
  and what its pull requests already cover, is read from
  `.github/workflows/` on `origin/main`.
- **The gate lock.** A worker holds one of the lock's slots while it
  runs a heavy gate (`every-session.md`'s *The machine is shared*).
  Sourcing the script sets `GATE_LOCK_WORKERS`, the `-n` of a suite.
  Release the slot the moment the gates finish. A slot is taken and
  released only through `$PROCESS/scripts/gate-lock.sh`, sourced in the
  same background shell call as the gates (*Long jobs run in the
  background*), never by a hand-written `mkdir` or `rmdir`:

  ```shell
  . "${PROCESS:?}/scripts/gate-lock.sh"
  gate_take <worktree> && {
    gate_wait; rc=0
    gate_peak <gate> <worktree> timeout -k 60 <seconds> … a gate … || rc=$?
    echo "EXIT_<gate>=$rc"
    gate_wait; rc=0
    gate_peak <next gate> <worktree> \
      timeout -k 60 <seconds> … the next gate … || rc=$?
    echo "EXIT_<next gate>=$rc"
    gate_release
  }
  ```

  `gate_peak` runs the gate, returns its exit code, and records its peak
  memory, as the script's header comment says.

  The timeout goes around each gate inside the block, never around the
  whole call: `gate_take` waits in the queue with no bound, so a timeout
  around it also counts the time queued for a slot. Inside the block, a
  gate that fails or runs out of time leaves `gate_release` to run:
  `|| rc=$?` keeps its exit code, and keeps a shell under `set -e` from
  ending there. `timeout` cannot wrap `gate_wait`, a shell function, and
  where `command -v timeout` prints nothing the gates run without it
  (`every-session.md`'s *Shell, checkouts and prose*).

  `-k 60` sends KILL where the gate's command still runs a minute after
  TERM. Without it, a command that ignores TERM keeps `timeout` waiting
  until it ends, and its slot held.

  `gate_release` runs in the same shell as `gate_take`, not after
  `$(gate_take …)` or `gate_take | …`, whose shell has exited. No
  session removes a slot any other way: a failed `mkdir` or an old slot
  says nothing about whose it is. The script's header comment says how
  the lock works: the defaults of the slots, the workers, the load
  ceiling and the directory, the queue, the stagger, the settle, stale
  slots, and what `gate_take` waits for, with no bound. It gives the
  command that names the holders, and says who removes a slot that is
  never reclaimed.

  Before running a load generator, read
  `$PROCESS/process/load-generator.md`.

### Sourcery and CodeRabbit before a push

The findings of these local runs are answered as `/btclib-pr`'s
*Answering it* says, and the writer's report lists each with its answer.

- **Sourcery reads each commit before it is pushed**, in a tree that runs
  the `sourcery` check, from a clone of the worktree in the scratch
  directory, as the standard's section 10, *The set, and its cadence*,
  says. The writer runs it on each commit it hands over, after the
  gates, so that the reviewers of *The rounds* read the fixes it calls
  for; the orchestrator runs it on a commit it made itself (*A branch
  has one author at a time*). A finding that does not hold is answered
  at its own site, as section 10 says. The clone goes once the run ends
  (*Debris goes when its work ends*).
- **CodeRabbit reads the branch once, before its first push.** The
  writer runs its CLI from the branch's worktree on the first commit it
  hands over, after the gates. A review takes minutes, so the writer
  starts this as a background call (*Long jobs run in the background
  with a timeout*). The CLI reads the branch from its merge base with
  `<target>`, the branch the pull request will target: `main`, or the
  parent of a stacked branch. The timeout is longer than the
  `expectedDuration` of the CLI's `review_context` event, since a review
  stopped early is discarded. The timeout follows `every-session.md`'s
  *Shell, checkouts and prose*:

  ```shell
  wt=<wt>
  target=<target>
  base=$(git -C "${wt:?}" merge-base "origin/${target:?}" HEAD)
  ```

  ```shell
  env -C "${wt:?}" sh -c 'rc=0 t=
    command -v timeout > /dev/null && t="timeout -k 60 1200"
    $t coderabbit review --agent --committed --fresh --deep \
      --base-commit "$1" || rc=$?
    echo "EXIT_coderabbit=$rc"' sh "${base:?}" \
    > <scratch>/<name>-coderabbit.log 2>&1
  ```

  The CLI read the branch only where this command exits `0`: the log
  ends `EXIT_coderabbit=0`, holds no `error` event, and holds one
  `complete` event outside sign-in that reports a whole, fresh review:

  ```shell
  jq -enR '[inputs] as $l | ($l | last) == "EXIT_coderabbit=0" and (
    [$l[] | fromjson? | objects] as $a
    | [$a[] | select(.type == "complete" and .phase != "auth")] as $c
    | ($c | length) == 1 and $c[0].status == "review_completed"
    and $c[0].findings == ([$a[] | select(.type == "finding")] | length)
    and ($c[0].outcome // "") != "failed"
    and ($c[0].unreviewedFileCount // 0) == 0
    and ($c[0].reused // false | not)
    and ([$a[] | select(.type == "error")] | length) == 0
    and (($c[0].message // "")
      | startswith("No fresh detailed file review") | not))' \
    <scratch>/<name>-coderabbit.log
  ```

  It runs under the login `README.md`'s *Prerequisites* asks for, never
  with `--use-credits`, and only where `coderabbit usage` shows an
  included review left. Otherwise it is skipped. Where it is skipped or
  shows no read, the pull request body's `## Evidence` says so. It
  stands in for no reviewer of *The rounds*, and it is not CodeRabbit's
  review on GitHub either. On PR btclib-org/ecc#598, read at one sha,
  that review reached the base file through the diff and the issues the
  branch cites, and applied the tree's `path_instructions`, while the
  CLI reached neither the base file nor the issues
  (ISS btclib-org/ai-agents-process#587). Whether the CLI applies
  `.coderabbit.yaml` is not measured; its `-c` takes the file as added
  instructions (`coderabbit review --help`). So a CLI read with no
  finding leaves that review owed, and every local reviewer looks for
  what it finds, as `local-review.md`'s *A pull request's rounds* says.

### Committing and rebasing

- **A branch's first push waits for the gates.** Push a commit or an
  amend only once a gate run on that very commit exited 0, never after a
  failed one, unless *The gates* asks no gate of it. A fix the gates
  find before the first push amends a commit not yet pushed. Check `git
  ls-remote origin <branch>` against `HEAD` after every push. On an open
  pull request, a fix is pushed only once the rounds of *Local review*
  have ended, and the orchestrator then has the writer push it. An armed
  pull request is disarmed before any push to it (`/btclib-pr`'s
  *Merging*).
- **An embargoed fix is the exception: it is pushed to `origin` only
  once its release commit is ready on top of it.** It is gated locally.
  The standard's section 12, *A security advisory is worked in this
  order*, says how it is written in the advisory's temporary private
  fork and lands by a public pull request. Before the advisory is
  published, any pull request left open in the fork is closed, because
  an open one blocks the publication:

  ```shell
  gh api -X PATCH -f state=closed repos/<owner>/<fork>/pulls/<n>
  ```

- **Before the pull request is opened, the branch converges by amend.**
  **Once it is open, a fix is a new signed commit on top**: the reviewer
  reads what changed since their review, and the squash lands the
  commits as one. A rebase still rewrites the branch.
- **A force-push with lease, to a branch the session works only**:

  ```shell
  git push --force-with-lease=refs/heads/<branch>:<sha you built on> \
    origin HEAD:refs/heads/<branch>
  ```

  Never a bare `--force`, never another branch. *The force-push grant*
  covers it. Where the classifier refuses the push under the grant, push
  the rewritten, gated commit without force to `<branch>-r2` and report
  both names; the orchestrator opens the pull request from it and closes
  the old one. This is the one route around a refusal the process
  sanctions. The old branch is deleted once its replacement has landed
  on `main`.
- **A claim holds a pull request's branch.** Before every push to an
  open pull request's branch, read the claim that stands on it, made by
  a login other than its author's:

  ```shell
  gh pr view <n> --repo <owner>/<repo> --json author,comments --jq '
    .author.login as $a | [.comments[] | select(.author.login != $a)
    | select(.body | startswith("Claimed") or startswith("Released"))]
    | last // empty | select(.body | startswith("Claimed")) | .author.login'
  ```

  Where it prints a login other than the human's
  (`gh api user --jq .login`), push nothing and report it. Where it
  prints nothing and the branch is another person's (`/btclib-pr`'s
  *Another person's branch*), nothing is pushed until the orchestrator
  has claimed it (*Before starting*). The claim stands until the pull
  request lands, or until the claiming session posts a comment starting
  `Released`: once it hands the pull request over to whom it waits on,
  and at the latest before it ends. A claim whose
  session no longer runs (*Before starting*) is released by its human.
- **One git write per Bash call, nothing chained to it.** A commit, an
  amend, a rebase or a push chained with `cp`, `rm`, a gate or another
  git write is refused as a whole. Run each in its own call.
- **Signed and signed off.** Commit with `-s`: `main` requires the
  `Sign-off` check, which refuses a commit without a `Signed-off-by:`
  trailer naming its author's address. It reads no merge commit, and no
  commit of a bot, the agent included, whose addresses the script's
  `BOTS` holds. After a rebase, cherry-pick or amend, check the whole
  range. In `git log --format='%h %G? %GS' <base>..` any valid signer
  is fine and `N` is the defect.

  On a branch whose earlier commits are not the session's, an outside
  contributor's or the agent's (`/btclib-pr`'s *Whose pull request it
  is*), that check reads the session's own commits only:
  `<theirs>..`, `<theirs>` being the pull request's head before the
  session's first commit. Those before it stay as they are, signed or
  not, and are added to and never rewritten, as `/btclib-pr`'s *Add,
  never rewrite* says. The agent's commit reads `N`, since its workflow
  does not sign it, and that is expected.

  A merge of `main` into the branch after `<base>` or `<theirs>` brings
  `main`'s squashes into `<base>..` or `<theirs>..`. The `Sign-off` job
  reads the pull request's commits, which leave those out, and the
  script can refuse one whose `Signed-off-by:` does not name its
  author's address. After such merges, `<base>..` is `<merge>^2..` on
  the session's own branch, `<merge>` being the last of them. A merge
  before `<theirs>` leaves `<theirs>..` as it is. One after it splits
  `<theirs>..` into `<theirs>..<merge>^1` and `<merge>..`, and each
  further one splits the last range the same way. Each range is checked
  on its own. This lists those merges, oldest first, with `<base>` in
  place of `<theirs>` on the session's own branch:

  ```shell
  git -C <wt> log --merges --first-parent --reverse --format=%H \
    '<theirs>..'
  ```

  The `Sign-off` job's script exits `0` on each range:

  ```shell
  gh api -H 'Accept: application/vnd.github.raw' \
    repos/btclib-org/.github/contents/.github/scripts/check_sign_off.py |
    env -C <scratch> GIT_DIR="$(git -C <wt> rev-parse --absolute-git-dir)" \
      uv run --no-config --no-project --python 3.15 python -I - <base>..
  ```

  It runs in the scratch directory, with git pointed at the worktree,
  whoever wrote the branch. From the worktree, uv would run the
  interpreter of a `.venv` there, whose `.pth` files run even under
  `python -I`, would read a `uv.toml` there, and Python would import a
  `subprocess.py` there in place of the standard library's.

  Its control is commit `c1786962edc1` of `btclib-org/.github`, which
  carries no `Signed-off-by:` trailer. A tree's own commits may all carry
  one, so the control is this one commit for every tree. The script reads
  only commits, so a blobless clone in your scratch directory serves:

  ```shell
  git clone --bare --filter=blob:none https://github.com/btclib-org/.github <clone>
  ```

  The same command, with `<clone>` for `<wt>` and
  `c1786962edc1~1..c1786962edc1` for `<base>..`, exits `1`. A failed
  fetch pipes an empty script, which exits `0`. The clone goes once the
  control has run, since the sweep of *Debris goes when its work ends*
  refuses a `<work>` that holds it:

  ```shell
  clone=<clone>
  ```

  ```shell
  rm -rf "${clone:?}"
  ```

  An amend with `--no-edit` and a rebase keep the trailer. A commit that
  lacks it gets it from `git rebase --signoff <base>`, or at the tip from
  `git commit --amend --no-edit -s`.

  A session makes no commit with signing turned off, a scratch
  repository built for a measurement included: not by `--no-gpg-sign`,
  by `commit.gpgsign=false` at any scope, by `git commit-tree` without
  `-S`, which `commit.gpgsign` does not reach, or under an emptied or
  replaced git config. A fixture commit that a test script of the tree
  writes by plumbing, as `scripts/test-sweep.sh` does, is not a
  session's commit. A measurement that needs no commit goes without one:
  `git diff --no-index` compares two directories, and `git add` then
  `git write-tree`, with `GIT_INDEX_FILE` naming a path that does not
  exist yet, give a tree without touching the repository's index.
  `index` in a directory that `mktemp -d` made is such a path. An empty
  file, which `mktemp` makes, is refused: git exits `128`. Where a
  commit is needed, it is a plain one, which `commit.gpgsign = true`
  signs.
- **A clean rebase is not a correct one.** Re-run the gates, and look for
  what `main` added around what you remove.
- **A rebase continued after a conflict drops every body line beginning
  with `#`**, such as a wrapped `#1406, …`, from that commit's message.
  Compare each commit's `git show -s --format=%B` before and after the
  rebase, and restore the tip's message with `git commit --amend
  --cleanup=verbatim -F <saved message>`. Better, never wrap a body line
  so that it begins with `#`.
- **A failed hook can make `git commit --amend` a no-op** that looks
  successful. Put the venv on `PATH` in the same call
  (`env PATH=/abs/wt/.venv/bin:$PATH git -C /abs/wt commit …`) and read
  the commit back. On an outside contributor's branch the commit runs as
  *The gates* says instead.
