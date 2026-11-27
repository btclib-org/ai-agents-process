# The replay set

The pull requests a change to the local reviewer is tried on before it
lands: those where the local rounds cleared a defect that a later review
found. A clean one, where no review found any, belongs there too (*What
a case holds*).

**A change to the reviewer's model, its effort or its tools, or a change
to the files of its brief that adds, alters or removes a rule it applies
in judging a branch, is run on every case here first**, but one that *A
case's tree can hold this file* leaves out, and its pull request adds
the run to *Runs* and names it in `## Evidence`. The model and the
effort are those `orchestration.md`'s *Models* gives. The tools are
those the `tools` key of `agents/reviewer.md`'s frontmatter gives a
Claude Code reviewer; the generated `.toml` carries no such key. The
brief's part this repository holds is the files and sections
`every-role.md`'s map gives the reviewer under *Everybody* and *The
reviewer*, the reviewer's sections of the skill the brief names,
`agents/reviewer.md` with its generated `.toml`, and this tree's
`REVIEWING.md`; another tree's `REVIEWING.md` and the review bot's
prompt, which the brief also carries, change in their own trees. Without
the run, such a change is judged on the next pull requests, whose
defects nobody knows in advance.

**A change to the brief's files that changes none of these owes no
run**: a pointer that moves, a sentence made more exact without changing
what it asks, a rule only the writer or the orchestrator acts on. Its
pull request says in `## Evidence` why it owes none.

## What a case holds

- the repository, and the base and head shas of the commit the miss was
  made on, frozen before the fix;
- for a defect, the defect in one sentence, and where it was found
  later;
- for a clean change, how it was measured clean.

**The expected finding is kept out of the reviewer's input.** The run
briefs a fresh reviewer of the head, as `local-review.md`'s *A pull
request's rounds* says, with the head's commit message standing for the
pull request. Its brief names neither this file nor anything posted
after the head, since both state the defect. The reviewer cannot reach
the fix either: the case's tree is a repository that holds only the head
and its ancestors, since a worktree reads every branch of the checkout
it was added from, and one of those may hold the fix. The process it is
briefed with is the configuration under test, at the `$PROCESS` sha the
run records. The reviewer reads that process from a copy that leaves
this file out, and the discard of *A case's tree can hold this file* is
the backstop. The reviewer reads the prose at the head itself, not on
the merge with `origin/main` that `local-review.md`'s *A pull request's
rounds* asks for, since `main` has moved past the case, a defect's fix
included. Where the run changes this tree's `REVIEWING.md`, a reviewer
of this repository's cases reads the changed file in place of the
head's, without the sentences that describe a case's defect, such as PR
btclib-org/ai-agents-process#317's in its *This repository in
particular*. The run records what it withheld. Where the change under
test rewrites such a sentence, its case is recorded as unable to
evaluate the change, beside a case that tests the instruction without
stating its answer, where one is needed.

**A reviewer carries more than its brief.** Claude Code loads into the
`reviewer` agent, as this tree's `agents/reviewer.md` defines it, the
installed agent definition, the instruction files, as
`~/.claude/CLAUDE.md`, and the session's memory index, `MEMORY.md` in
`~/.claude/projects/<project>/memory/`. Its documentation says that the
main conversation's auto memory is not loaded into a non-fork subagent
([*What loads at
startup*](https://code.claude.com/docs/en/sub-agents#what-loads-at-startup)),
but in the runs of 2026-11-20 `reviewer` agents cited a line of it.

A Codex reviewer, started as `orchestration.md`'s *Starting the reviewer
in the other client* says, carries its own. Its instruction file is
`~/.codex/AGENTS.md`, and its index is the memory summary,
`~/.codex/memories/memory_summary.md`, under a `## Memory` heading that
points to `MEMORY.md` beside it for a search. On 2026-11-27, at Codex
0.169.0, a run started that way, from a new directory of the scratchpad
that no git repository holds, with a brief asking for one word, recorded
both files whole in its session record under `~/.codex/sessions/`. It
recorded no `AGENTS.md` of its working directory, which held none. That
machine's `~/.codex/config.toml` set `use_memories = true`.

A switch keeps Claude Code's index from one reviewer. One is
`omitClaudeMd: true` in the agent's definition, which drops the
instruction files too. The others serve a reviewer that `claude -p`
starts as a process of its own: the variable
`CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, or `autoMemoryEnabled` set to
`false` in the settings that `--settings` passes. A later `--settings`
replaces an earlier one, so the setting goes inside the one the run
already passes, as the sandbox's in `orchestration.md`'s *Starting the
reviewer in the other client*. On 2026-11-21, at Claude Code 2.1.330, a
subagent defined with `omitClaudeMd: true` reported neither a
`MEMORY.md` nor a `CLAUDE.md` block in its context, and one with `false`
reported both. A plain `claude -p` session, started from a directory
whose project holds an index, reported no `MEMORY.md` block with either
of the other switches, and reported one without them. The reviewer that
section starts, run from its own new directory, whose project holds no
index, reported none with no switch; with the same flags from a
directory whose project holds one, and the definition passed by
`--agents`, it reported one, and none with the setting inside the
sandbox's settings. `agents/reviewer.md` sets no `omitClaudeMd`, so a
reviewer the `Agent` tool starts from it carries the index, and the run
records and discards as below. Whether a run should start its reviewers
with a switch is the question of ISS btclib-org/ai-agents-process#739.
The agent definition belongs to the configuration under test. The
instruction files and the index belong to neither the configuration nor
the case, and either can state the change under test or a case's
finding, as a note of the maintainer's answer that a candidate turns
into a rule does.

So the reviewer may carry them, and may rest no finding on them. Before
the first reviewer starts, and again after the last verdict, since other
sessions write the index meanwhile, the orchestrator reads the
instruction files and the index its reviewers carry, as above. The run's
entry names, in its own words and quoting none of it, each note of
either that states the change under test or a case's finding, or says
that none does. The brief says that neither is a ground for a finding,
and has the verdict end with the line `Outside the brief: none`, or with
`Outside the brief:` followed by each note of either that the verdict
relies on or quotes. That line comes after the coverage list that
`local-review.md`'s *The rounds* has a first verdict end with, so that
the block below reads it. The orchestrator saves each verdict to a file
in its own `<scratch>`, outside `<work>/reviewer/<name>`, which the run
removes. This prints `unaided` only where the file's last line that
holds text is `Outside the brief: none`, and where no line holds, case
ignored, any of these:

- `memory.md` or `claude.md`;
- `auto` and `memory` with at most one character between them;
- `memory`, a space, and `index`, `note`, `file` or `director`;
- `session`, then any characters other than a space, or none, then a
  space and `memory`, as in "session's memory";
- `instruction file`, `global instruction` or `persistent note`;
- `projects/` and then `/memory` with no space between them.

```shell
v=<verdict>
```

```shell
last=$(grep -v '^[[:space:]]*$' "${v:?}" | tail -n 1) &&
  [ "$last" = 'Outside the brief: none' ] &&
  { rc=0; LC_ALL=C.UTF-8 grep -n -i -E \
    -e 'memory\.md|claude\.md|auto.?memory' \
    -e 'memory (index|note|file|director)|session[^ ]* memory' \
    -e 'instruction file|global instruction|persistent note' \
    -e 'projects/[^ ]*/memory' "$v" || rc=$?; [ "$rc" -eq 1 ]; } &&
  echo unaided
```

The second `grep` runs in the `C.UTF-8` locale, which `locale -a` lists
on macOS, so that "at most one character" counts a character of UTF-8,
not a byte, whatever the caller's locale. Under `LC_ALL=C`,
`/usr/bin/grep` reads U+00A0 as two bytes and U+2013 as three, and the
block without the pin prints `unaided` for `auto` and `memory` joined by
either. A locale the system lacks raises no error, and the block then
misses them too.

It is a first screen: a verdict can name the index or an instruction
file in other words, or across a line break, so `unaided` does not show
it free of them. The orchestrator therefore reads every verdict for a
ground outside the brief as it scores it (*How a run is scored*),
whatever the block printed. It reads first each verdict for which the
block does not print `unaided`, starting from the lines it lists where
it lists any. One that rests a finding on a note of the index or of an
instruction file, or quotes one, is discarded and run again, as one that
reads a copy of this file is (*A case's tree can hold this file*); one
that names them only as not relied on is kept. Where the repeat is
discarded too, the case is recorded as unable to evaluate the change.

**Each reviewer writes in a scratch directory of its own**, which its
brief names: `<work>/reviewer/<name>`, in the reviewer's `<scratch>`
(`every-role.md`'s *The scratchpad is shared*), under a `<name>` that no
other reviewer of the run uses. Two reviewers left to choose can choose
the same name, and the cleanup of one then removes the other's inputs.
The run makes `<work>/reviewer` as that section says, then the directory
before the reviewer starts, with a `mkdir` that refuses a path that
exists:

```shell
dir=<work>/reviewer/<name>
```

```shell
mkdir -- "${dir:?}"
```

Where it refuses, the run takes another `<name>` and makes that one. The
run removes the directory once the verdict is saved, since the sweep of
`every-role.md`'s *Debris goes when its work ends* refuses a `<work>`
that holds a repository an input made there:

```shell
dir=<work>/reviewer/<name>
```

```shell
rm -rf "${dir:?}"
```

The case's tree is built at a new path from a checkout that holds the
head, named by its path, so that the fetch needs no network and the
tree keeps no remote. The first command refuses a path that exists,
since `git init` keeps the objects of a repository already there, and a
refusal there stops the build. It sets `created` to the tree only where
its `git init` succeeds, and the fetch and the checkout run only where
`created` names the tree. So a paste that goes on past a refusal writes
nothing: not in a repository at the path, nor in one above it, which
`git -C` reaches from a directory that is no repository. The fetch runs
in the tree, so it makes the checkout's path absolute first: a relative
one would be read from the tree. The three values are set first:

```shell
tree=<tree>
checkout=<checkout>
head=<head>
```

```shell
created= && [ ! -e "${tree:?}" ] && git init "$tree" && created=$tree
```

```shell
[ "${created:-}" = "${tree:?}" ] && src=$(realpath "${checkout:?}") &&
  git -C "$tree" fetch "$src" "${head:?}"
```

```shell
[ "${created:-}" = "${tree:?}" ] &&
  git -C "$tree" checkout --detach FETCH_HEAD
```

This prints `isolated` only where each read succeeds, the tree has no
remote, its `HEAD` is the head, and every commit its refs reach is the
head or one of its ancestors:

```shell
remotes=$(git -C "${tree:?}" remote) &&
  top=$(git -C "$tree" rev-parse HEAD) &&
  all=$(git -C "$tree" rev-list --all) &&
  ancestry=$(git -C "$tree" rev-list HEAD) &&
  [ -z "$remotes" ] && [ "$top" = "${head:?}" ] && [ "$all" = "$ancestry" ] &&
  echo isolated
```

**A case's tree can hold this file**: a case of this repository whose
head descends from `2ef0de4`, which added it, holds it at its head. That
copy is the head's own, and `REVIEWING.md`'s last bullet sends a
reviewer of this repository to it, so the reviewer reads it as any file
of the head. A version of it, at the head or at any commit of the tree,
can state a case's finding: its entry under *Cases*, a score or a
finding under *Runs*, or the paragraph that makes it a clean case. This
lists each commit of the tree whose version of this file names the case,
as `<repo>#<n>` or `<repo>/pull/<n>`, with or without its owner, and
prints `unnamed` only where each read succeeds and none does. It refuses
an `n` that is not a number and a `repo` that is not one owner and one
name. `-F` reads the reference as a literal, `-w` keeps `#31` from
matching `#317`, and the `printf` splits the commits into words in `zsh`
too, which does not split a variable. `git grep` exits `1` on a blob it
cannot read, so the block also requires that it wrote no error:

```shell
repo=<owner>/<repo>
n=<n>
```

```shell
case ${n:?} in *[!0-9]*) false ;; esac &&
  case ${repo:?} in */*/* | *[!A-Za-z0-9._/-]*) false ;; ?*/?*) ;;
    *) false ;; esac && name=${repo#*/} &&
  revs=$(git -C "${tree:?}" log --format=%H HEAD) && [ -n "$revs" ] &&
  { rc=0; err=$(git -C "$tree" grep -l -w -F -e "${name}#${n}" \
    -e "${name}/pull/${n}" $(printf '%s\n' "$revs") \
    -- process/replay-set.md 2>&1 1>&3 3>&-) || rc=$?; } 3>&1 &&
  printf '%s' "$err" >&2 && [ -z "$err" ] && [ "$rc" -le 1 ] &&
  { [ "$rc" -eq 0 ] || echo unnamed; }
```

The check finds a case only by its reference and reads no other file of
the tree, so a version that states a finding without naming its case
passes it. The orchestrator reads the sentences that name the case in
each version the check lists. The case is left out of the run only where
one of them states the case's finding, its score or that it is clean; a
sentence that names it only as the change a run tested states none of
them. The run's entry names the versions read and why the case stays or
goes. A run is discarded and run again where its verdict lists as read,
or quotes, a copy of this file other than its case tree's own: one at
the run's `$PROCESS` sha, on `main` or in another checkout. A verdict
that lists this file as not read is not discarded for it.

The tree goes once the run is recorded in *Runs*, since the sweep of
`every-role.md`'s *Debris goes when its work ends* refuses a `<work>`
that holds it:

```shell
tree=<tree>
```

```shell
rm -rf "${tree:?}"
```

The copy the reviewer reads the process from
(*The expected finding is kept out of the reviewer's input*) is built
from a clone that holds the run's `$PROCESS` sha. The exclude pathspec
keeps this file out of the archive, so it is never written. The build
refuses a path that holds a control character: a command substitution
drops the newlines that end what `dirname` and `basename` print, so the
guard would test one path and `tar` write another. It refuses a path
that exists, a symbolic link included, and `tar` makes the directory
itself. `pipefail` makes a failed `git archive` fail the build, where
`tar` would extract nothing and exit `0`. The three values are set
first:

```shell
copy=<copy>
clone=<clone>
sha=<sha>
```

```shell
case ${copy:?} in *[[:cntrl:]]*) false ;; esac && [ ! -e "$copy" ] &&
  [ ! -L "$copy" ] && parent=$(dirname -- "$copy") &&
  name=$(basename -- "$copy") &&
  (set -o pipefail && git -C "${clone:?}" archive --prefix="$name/" \
    "${sha:?}" -- process ':(exclude)process/replay-set.md' |
    tar -x -C "$parent")
```

This prints `copied` only where each read succeeds, the copy is a
directory holding `process/` alone, every entry under it is a directory
or a regular file named with letters, digits, `.`, `_` and `-` only,
nothing stands at `process/replay-set.md`, and the files are those of
the sha's `process/` but this file, byte for byte:

```shell
[ ! -L "${copy:?}" ] && [ -d "$copy" ] &&
  top=$(env -C "$copy" find . -mindepth 1 -maxdepth 1) &&
  [ "$top" = ./process ] &&
  odd=$(env -C "$copy" LC_ALL=C find . ! -type d ! -type f -o \
    -name '*[!A-Za-z0-9._-]*') &&
  [ -z "$odd" ] && [ ! -e "$copy/process/replay-set.md" ] &&
  [ ! -L "$copy/process/replay-set.md" ] &&
  want=$(git -C "${clone:?}" ls-tree -r --format='%(objectname) %(path)' \
    "${sha:?}" -- process) && [ -n "$want" ] &&
  got=$(env -C "$copy" find process -type f -exec sh -c 'for f; do
    o=$(git hash-object --no-filters -- "$f") || exit; echo "$o $f"; done' \
    sh {} +) &&
  [ "$(printf '%s\n' "$got" | LC_ALL=C sort)" = "$(printf '%s\n' "$want" |
    grep -v ' process/replay-set\.md$' | LC_ALL=C sort)" ] &&
  echo copied
```

A forge finding gives a case its head, the commit its thread names:

```shell
repo=<owner>/<repo>
id=<comment id>
gh api "repos/${repo:?}/pulls/comments/${id:?}" \
  --jq .original_commit_id
```

The head gives its base: the commit the head was built on, on the branch
its pull request targets, `main` or a stacked branch's parent. So a
stacked case leaves out its parent's change. That branch can have moved
off the head's history since. A stacked parent rewritten after the head
no longer holds the commit the head was built on. A parent that lands is
squashed onto `main`. Its child is then retargeted onto `main`
(`CONTRIBUTING.md`'s *One subject, opened as soon as it is written*),
where the head's merge base comes before the parent's commits.

The base is therefore read from the tips of the target that the forge
recorded:

- `baseRefOid`, the target's tip as the forge last recorded it;
- the commits before and after each force-push of the target;
- the heads of the pull requests opened from the target and from each
  branch the target was changed from, and the commits before and after
  each force-push of those pull requests' heads.

For each tip, this prints how many commits the head is ahead of it, their
merge base, and how many merges lie between the two, the smallest count
first. It reads a branch's name from the forge, never from a paste,
since a name may hold `;`. It then prints the base, the merge base on
the first line whose count is above `0`. It prints no base, and exits
non-zero, where:

- a read fails, or a force-push it reads lacks a commit;
- no tip leaves the head ahead;
- that line's compare lists fewer commits than it counts;
- a merge lies between that merge base and the head.

```shell
repo=<owner>/<repo>
n=<n>
head=<head>
(set -o pipefail
  tips=$(gh api graphql --paginate -F owner="${repo%%/*}" \
    -F repo="${repo#*/}" -F n="${n:?}" -f query='query($owner: String!,
      $repo: String!, $n: Int!, $endCursor: String) {
      repository(owner: $owner, name: $repo) { pullRequest(number: $n) {
        baseRefName baseRefOid timelineItems(first: 100, after: $endCursor,
          itemTypes: [BASE_REF_FORCE_PUSHED_EVENT, BASE_REF_CHANGED_EVENT,
            AUTOMATIC_BASE_CHANGE_SUCCEEDED_EVENT]) {
          pageInfo { hasNextPage endCursor } nodes { __typename
            ... on BaseRefForcePushedEvent {
              beforeCommit { oid } afterCommit { oid } }
            ... on BaseRefChangedEvent { previousRefName }
            ... on AutomaticBaseChangeSucceededEvent { oldBase } } } } } }' \
    --jq '.data.repository.pullRequest | (.baseRefOid // error("no base")),
      "branch \(.baseRefName // error("no base"))",
      (.timelineItems.nodes[] | if .__typename == "BaseRefForcePushedEvent"
      then (.beforeCommit.oid // error("a force-push without its before")),
        (.afterCommit.oid // error("a force-push without its after"))
      else "branch \(.previousRefName // .oldBase // error("no branch"))"
      end)' | awk '!s[$0]++' |
  while IFS= read -r tip; do
    case $tip in
      ('branch '*) gh api -X GET --paginate "repos/${repo:?}/pulls" \
        -f state=all -f head="${repo%%/*}:${tip#branch }" \
        --jq '.[] | "\(.number) \(.head.sha)"' |
        while read -r p sha; do
          printf '%s\n' "$sha"
          gh api graphql --paginate -F owner="${repo%%/*}" \
            -F repo="${repo#*/}" -F n="$p" -f query='query($owner: String!,
              $repo: String!, $n: Int!, $endCursor: String) {
              repository(owner: $owner, name: $repo) {
                pullRequest(number: $n) { timelineItems(first: 100,
                  after: $endCursor, itemTypes: [HEAD_REF_FORCE_PUSHED_EVENT]) {
                  pageInfo { hasNextPage endCursor } nodes {
                    ... on HeadRefForcePushedEvent {
                      beforeCommit { oid } afterCommit { oid } } } } } } }' \
            --jq '.data.repository.pullRequest.timelineItems.nodes[] |
              (.beforeCommit.oid // error("a force-push without its before")),
              (.afterCommit.oid // error("a force-push without its after"))' ||
            exit
        done || exit ;;
      (*) printf '%s\n' "$tip" ;;
    esac
  done | sort -u) &&
  lines=$(printf '%s\n' "$tips" | while IFS= read -r tip; do
    gh api "repos/${repo:?}/compare/${tip}...${head:?}" --jq '[.ahead_by,
      .merge_base_commit.sha, if (.commits | length) == .ahead_by
      then [.commits[] | select(.parents | length > 1)] | length
      else "?" end] | map(tostring) | join(" ")' || exit
  done | sort -n) &&
  printf '%s\n' "$lines" | awk '{ print }
    $1 > 0 && !n { n = 1; m = $3; b = $2 }
    END { if (!n) e = "no tip leaves the head ahead"
      else if (m == "?") e = "the compare lists fewer commits than it counts"
      else if (m != "0") e = "a merge lies between the base and the head"
      if (e) { print e > "/dev/stderr"; exit 1 }
      print "base " b }')
```

Where the head's commits since the base hold no merge, a tip that
descends from the commit the head was built on, and holds none of the
head's own commits, gives that commit. A tip that does not descend from
it, as a rewritten parent or `main` after a parent's landing, gives one
further from the head. A count of `0` is a tip that holds the head.

A head that merged its target has no one commit it was built on, as a
branch that merges `main` once its parent lands. Ranking its counts can
pick a merge base whose diff carries what the target gained, so such a
case is left out of the set.

The tips are only what the forge recorded. A pull request's timeline
records the force-pushes of its own branch, and those of a branch while
that branch is its target. The block reads no push made without force,
as a commit added to the parent, and sees one only through a later tip
that descends from it. So the commit the head was built on can be on no
tip and in no tip's history, where a force-push that none of these
timelines recorded replaced it: one made while the branch was not the
target, before a pull request was opened from it or on a branch none was
opened from. The block can then print a base below that commit and exit
`0`.

**A clean change belongs in the set too**, so that a change which only
makes the reviewer raise more shows as false findings. PR
btclib-org/ai-agents-process#522 is one (*Cases*). A finding a run makes
on one is re-measured: where it holds, the case moves to the defects,
and where it does not, it is a false finding. A pull request becomes a
clean case where, on the head it landed on, the three reviewers of
`/btclib-pr`'s *The reviews on GitHub* read `ack`, both reads below
print `0`, two fresh reviewers, briefed as for a run, each clear it, and
no review names a defect in it that holds: a false sentence is one,
wording that could only be better is not.

```shell
repo=<owner>/<repo>
n=<n>
gh api graphql -F owner="${repo%%/*}" -F repo="${repo#*/}" -F n="${n:?}" \
  -f query='query($owner: String!, $repo: String!, $n: Int!) {
    repository(owner: $owner, name: $repo) { pullRequest(number: $n) {
      reviewThreads { totalCount } } } }' \
  --jq .data.repository.pullRequest.reviewThreads.totalCount ||
  echo read-failed
{ gh api --paginate "repos/${repo:?}/pulls/${n:?}/reviews?per_page=100" \
    --jq '.[] | select(.user.login == "coderabbitai[bot]") | .body' ||
    echo read-failed
} | grep -c -E \
  'read-failed|cr-comment:v1|Additional comments|Actionable comments|Nitpick'
```

The first read counts every review thread, any author, resolved or not.
The second is a first screen: it counts the lines of CodeRabbit's
review bodies, on every head, that carry one of its terms, so a count
above `0` rules the pull request out, and `0` does not show it free of
findings. A failed pre-merge check under *Prompt to fix all issues*, as
on PR btclib-org/btclib-node#2531, carries none of the terms. So a
clean case also has every CodeRabbit review body read as `/btclib-pr`'s
*What was raised* reads them, with none holding a finding. A failed
read prints `read-failed` or counts it, and any answer other than `0` is
not clean.

## How a run is scored

**A hit names the defect's mechanism and its consequence** well enough
to fix it, as *The findings record* in `orchestration.md` matches two
findings. A defect a run names only in a non-blocking finding is a miss.
The orchestrator scores each verdict against the case's sentence, and
the human scores where it cannot tell. The cases are chosen, not drawn
at random, so a run says how a configuration did on them and not how
often it finds a defect.

**One factor at a time.** A run changes one thing from the baseline, the
brief, the model, the effort or the tools, and is compared with the
baseline's run on the same cases. One configuration can answer
differently on two runs, so a case that alone decides the comparison is
run again first. A run that changes the brief is compared with a
baseline at the candidate's merge base with the branch it targets,
`main` or a stacked branch's parent. That is the target's commit the
candidate's branch last merged or, with no merge, the parent of the
branch's first commit, so that `git diff <baseline> <candidate> --
process agents skills REVIEWING.md` shows that change alone. The
baseline's entry names that sha.

## Runs

Each run is an entry: the date, the `$PROCESS` sha, the factor changed
and its value, the client, the model and the effort, a hit or a miss for
each defect, or why its case was left out (*A case's tree can hold this
file*) or recorded as unable to evaluate the change (*The expected
finding is kept out of the reviewer's input* and *A reviewer carries
more than its brief*), each false finding on any case apart, and the
notes outside the brief that *A reviewer carries more than its brief*
has it name.

**An entry whose `$PROCESS` sha is not on `main` also records the tree
the copy is built from**, which `git rev-parse '<sha>:process'` prints.
Such a sha is a commit of a branch, which the squash does not land and
an amend or a rebase can replace: after `git fetch origin`,
`git merge-base --is-ancestor <sha> origin/main` exits `1` for it. In a
clone that holds the tree, `git ls-tree -r <tree>` lists its files and
`git cat-file -p '<tree>:<file>'` prints one. A clone that lacks it
fetches it with `git fetch origin <tree>` where a commit pushed to
`origin` holds it, even once no ref there reaches that commit. A tree
that no pushed commit holds fails that fetch with `not our ref`, and is
read only where its objects are, as in the clone the run was made in.

- **Baseline**, 2026-11-15: `$PROCESS` `2ef0de4`, no factor changed;
  Claude Code, the `reviewer` agent, Opus, effort `high`. PR
  btclib-org/ai-agents-process#317: miss. PR
  btclib-org/btclib-secp256k1#1331: miss. PR btclib-org/ecc#484: hit.
  PR btclib-org/ai-agents-process#444, clean when run: one finding,
  which holds and moved the case to the defects.
- **Candidate**, 2026-11-15: `$PROCESS` `466d803`, tree
  `ae2991e8a0a7037091e9dd03fd2e04e93145474f`, the factor changed being
  the brief: `local-review.md`'s *Local review*'s round rules of ISS
  btclib-org/ai-agents-process#461 and ISS
  btclib-org/ai-agents-process#464. The same client, model and effort.
  The same four results: miss, miss, hit, and the same finding on the
  last. The change neither loses a hit nor adds a false finding on these
  cases.

Both runs withheld nothing: the reviewer read the head's own
`REVIEWING.md`, which does not describe the defect of PR
btclib-org/ai-agents-process#317, and the change under test changes
no `REVIEWING.md`. Each brief had the reviewer read the prose at the
head, run no suite and use no forge, and no verdict's coverage list
named this file. On PR btclib-org/ai-agents-process#317 both also
raised, as blocking, that "tied to the account" is wider than "does not
clear within the session": a finding that holds, outside the case's
defect, and that the pull request fixed in `d5dee25` before it landed.

- **Baseline**, 2026-11-15: `$PROCESS` `aa5dcdc`, no factor changed;
  Claude Code, the `reviewer` agent, Opus, effort `high`, the brief
  having the reviewer read `every-session.md` and `btclib-common.md`
  whole. PR btclib-org/ai-agents-process#317: miss. PR
  btclib-org/btclib-secp256k1#1331: miss, then miss on a repeat. PR
  btclib-org/ecc#484: hit. PR btclib-org/ai-agents-process#444: hit.
- **Candidate**, 2026-11-15: `$PROCESS` `1ddae0d`, tree
  `7ee14c3c7929570af22e0554910f0ef7627818f6`, the factor changed being
  the brief's files of ISS btclib-org/ai-agents-process#447: the
  reviewer reads `every-session.md`, `every-role.md`, `local-review.md`
  and the sections of `writing.md` the map names, in place of
  `btclib-common.md` whole. The same client, model and effort. PR
  btclib-org/ai-agents-process#317: miss. PR
  btclib-org/btclib-secp256k1#1331: miss, named as non-blocking in a
  `CLEARED`: a call recorded as `reported` passes on any Valgrind error,
  whatever caused the exit `42`; then miss on a repeat. PR
  btclib-org/ecc#484: hit. PR btclib-org/ai-agents-process#444: hit.
- **Candidate**, 2026-11-15: `$PROCESS` `2166200`, tree
  `0c74e2feb51248cf3c388b10bbf66006a9c6f0cd`, whose process files,
  `agents/` and `REVIEWING.md` are those of `1ddae0d`, the factor
  changed being the whole brief of ISS btclib-org/ai-agents-process#447:
  the split process files, the change's `agents/reviewer.md`, and for
  this repository's cases the change's `REVIEWING.md`. Claude Code,
  Opus, effort `high`, with a general-purpose agent briefed to read the
  change's `agents/reviewer.md` whole and act as it, since the installed
  `reviewer` agent is `main`'s: the agent type, with its wider tools, is
  another difference from the baseline. PR
  btclib-org/ai-agents-process#317: miss; the verdict notes, outside its
  findings, that the rewritten exception now reaches the new sentence,
  and judges it without effect. PR btclib-org/btclib-secp256k1#1331:
  miss. PR btclib-org/ecc#484: hit. PR btclib-org/ai-agents-process#444:
  hit.

Neither the run at `aa5dcdc` nor the run at `1ddae0d`, their repeats
included, made a false finding. Outside a case's defect, on PR
btclib-org/ai-agents-process#317 both raised again the finding that the
runs at `2ef0de4` and `466d803` raised, which holds, and the repeat at
`1ddae0d` on PR btclib-org/btclib-secp256k1#1331 raised, as blocking,
that `SECURITY.md`'s reasons for `zkp.rangeproof.sign` leave out the
blinding factor and the message, which holds on `main` (ISS
btclib-org/btclib-secp256k1#1403). Each brief had the reviewer read the
prose at the head, run no suite and use no forge, and no verdict's
coverage list named this file.

The run at `2166200` withheld from PR btclib-org/ai-agents-process#317
and PR btclib-org/ai-agents-process#444 the sentence of the change's
`REVIEWING.md` that states the defect of PR
btclib-org/ai-agents-process#317, from "In [PR ai-agents-process#317]"
to "exempted that run from the hold too.": their reviewers read that
file in place of the head's. The reviewers of the other cases read their
own tree's `REVIEWING.md`. No verdict's coverage list named this file,
and the verdict on PR btclib-org/ai-agents-process#317 says it is absent
at that head. Outside the cases' defects, that run raised on PR
btclib-org/ai-agents-process#317 the finding the runs at `2ef0de4` and
`466d803` raised, which holds; on PR btclib-org/ecc#484, as blocking,
that the phrase is split across string literals and that a required copy
is read as a finding, both of which `main`'s later version of that
paragraph answers; and on PR btclib-org/btclib-secp256k1#1331, as
non-blocking, that the workflow's outcome list and the harness's call
table are copies kept by hand, which the orchestrator did not
re-measure. No false finding was found.

The run at `1ddae0d` tested the process files alone: each reviewer read
them at that sha, the case's own `REVIEWING.md` at the case's head, and
the installed `reviewer` agent, which is `main`'s `agents/reviewer.md`.
It left out the change's edit to this tree's `REVIEWING.md`, which
retargets its pointers to `btclib-common.md` to the new files. It also
left out the edit to `agents/reviewer.md`, which retargets its citations
of `btclib-common.md` and adds a sentence naming what the reviewer
reads. The run at `2166200` tested both edits. The `REVIEWING.md` edit
rewrites the paragraph that states the defect of PR
btclib-org/ai-agents-process#317, and that run withheld the sentence, so
that case cannot evaluate the edit. The run at `1ddae0d` loses no hit
and gains none. With the whole brief under test, the run at `2166200`
matches the baseline at `aa5dcdc` on every case, so the change loses no
hit on these cases and shows no gain.

- **Baseline**, 2026-11-15: `$PROCESS` `53b7a57`, no factor changed;
  Claude Code, the `reviewer` agent, Opus, effort `high`, one first run
  per case. PR btclib-org/ai-agents-process#317: miss. PR
  btclib-org/ai-agents-process#444: hit. PR
  btclib-org/btclib-secp256k1#1331: miss, and miss on each repeat but
  one, which is void: its reviewer read the subject of the fix commit on
  a local branch. PR btclib-org/ecc#484: hit.
- **Candidate**, 2026-11-15: `$PROCESS` `853aa9c`, tree
  `facb7eaf1e0ae989359a0f610f142e16102dd88e`, the factor changed being
  the reviewer's map entry of ISS btclib-org/ai-agents-process#483: it
  gives `writing.md`'s *Writing work* whole, in place of the checklist,
  *A rule stated more than once*, *What the prose that lands may say*,
  *Citations and closing keywords* and *Signed and signed off*, and adds
  the sections of the skill the brief names. `agents/reviewer.md` and
  `REVIEWING.md` are `main`'s. The same client, model, effort and
  briefs, one run per case. PR btclib-org/ai-agents-process#317: miss,
  the defect named only in a non-blocking finding judged as already on
  the base (*How a run is scored*). PR btclib-org/ai-agents-process#444:
  hit. PR btclib-org/btclib-secp256k1#1331: miss. PR btclib-org/ecc#484:
  hit.

Neither run made a false finding. Each brief had the reviewer read the
process from a copy of its files at the run's sha without this file,
read the prose at the head, run no suite and use no forge. The reviewers
read their own tree's `REVIEWING.md` at the head, and no verdict's
coverage list named this file. On one run per case the candidate loses
no hit and gains none. What it adds to the reviewer's reading,
`writing.md`'s *The gates*, *Sourcery and CodeRabbit before a push* and
*Committing and rebasing*, bears on checks no case of the set exercises.

- **Candidate**, 2026-11-15: `$PROCESS` `86cc1ec`, tree
  `bb669fe1f9761677f194399770c630f802f3a980`, the factor changed being
  the brief: the item of ISS btclib-org/ai-agents-process#462 in
  `local-review.md`'s *The verdict*, that each blocking finding names
  its trigger, its mechanism, its consequence and, where one is known,
  one correction that suffices. It is compared with the baseline at
  `53b7a57` above. The same client, model and effort. PR
  btclib-org/ai-agents-process#317: miss. PR
  btclib-org/ai-agents-process#444: hit. PR
  btclib-org/btclib-secp256k1#1331: miss on each run. PR
  btclib-org/ecc#484: hit.
- **Baseline and candidate**, 2026-11-15: `$PROCESS` `53b7a57` and
  `86cc1ec`, tree `bb669fe1f9761677f194399770c630f802f3a980`, as above,
  one run each on the cases PR btclib-org/ai-agents-process#503 added.
  PR btclib-org/.github#2288, the clean case: `CLEARED` in both, each
  with a non-blocking wording finding that is not a defect. PR
  btclib-org/btclib-node#2516: miss in both; the baseline names the
  defect only in a non-blocking finding, and the candidate names the
  same overstatement only in the commit message. PR btclib-org/ecc#580:
  hit in both.

PR btclib-org/btclib-secp256k1#1331, the one case where a gain was
plausible, ran four more times in each configuration, and the baseline's
repeats are those of the entry above. The candidate's reviewers read the
process as the baseline's did, and no brief named the configuration. No
verdict's coverage list named this file. On PR
btclib-org/ai-agents-process#317 the candidate named the exemption and
its consequence only in a non-blocking finding, as the baseline did.

Outside the cases' defects, on PR btclib-org/btclib-secp256k1#1331 two
baseline runs and one candidate run asked for changes on findings that
hold: that `SECURITY.md`'s reasons for `zkp.rangeproof.sign` leave out
the blinding factor (ISS btclib-org/btclib-secp256k1#1403), and that the
step's list is kept equal to `SECURITY.md` by hand, which other runs
raised as non-blocking. The baseline run on PR btclib-org/ecc#484
blocked on two more findings that hold.

The scoring was not wholly blind: a candidate verdict shows the format,
and one candidate verdict on PR btclib-org/btclib-secp256k1#1331 was
scored after the key was read. The briefs of the further runs were
handed as a file to read, where the first ones were inline. Each case's
tree was a worktree of its repository's primary checkout, which *What a
case holds* rules out. Only the void baseline repeat read a fix there,
but five of the six runs on the added cases noted that the local
`origin/main` already holds the landed change, and two compared the head
with it: the baseline on PR btclib-org/.github#2288, the clean case,
where that may favour a `CLEARED`, and the candidate on PR
btclib-org/btclib-node#2516. Neither hit on PR btclib-org/ecc#580 rests
on such a comparison. On PR btclib-org/ecc#580, whose briefs said to run
no suite, both runs ran the branch's tests as inputs to measure their
finding, the baseline one test on the missing methods and the candidate
whole test modules; neither ran the suite as a gate.

Neither configuration made a false finding, and the candidate gains no
hit and loses none. By the rule recorded on ISS
btclib-org/ai-agents-process#462 the result is inconclusive, and the
item is not adopted.

- **Candidate**, 2026-11-15: `$PROCESS` `cab9c97`, tree
  `39a87f84c7133c05199cda4b8d25bb8141f984ff`, the factor changed being
  the brief's prose rules of ISS btclib-org/ai-agents-process#415,
  `local-review.md`'s *Local review*'s new *A text to be posted* among
  them. Claude Code, the `reviewer` agent, Opus, effort `high`, one run
  per case. It is compared with the baseline at `53b7a57` above on all
  seven cases: the candidate's base, `e029de3`, differs from `53b7a57`
  only in `process/orchestration.md`, which no brief of this run had the
  reviewer read. PR btclib-org/ai-agents-process#317: miss. PR
  btclib-org/ai-agents-process#444: hit. PR
  btclib-org/btclib-secp256k1#1331: miss. PR btclib-org/ecc#484: hit. PR
  btclib-org/.github#2288, the clean case: `CLEARED` with no finding. PR
  btclib-org/btclib-node#2516: miss (*How a run is scored*). PR
  btclib-org/ecc#580: hit. The last three ran after the first four, once
  PR btclib-org/ai-agents-process#503 had added them to the set.

On the seven cases the candidate has the baseline's hits and misses, and
it made no false finding. On PR btclib-org/ecc#484 it also gave as
blocking a second finding, which earlier runs did not give as blocking:
the new bullet restates a rule the review workflow's prompt holds. The
orchestrator did not measure it false. On PR
btclib-org/ai-agents-process#317 it raised again the finding the earlier
runs raised, which holds. Each brief had the reviewer read the process
from a copy of `process/` at `cab9c97` without this file, read the prose
at the head, run no suite and use no forge; the change's hunk in
`/btclib-pr` is outside what the reviewer's map gives it. No verdict's
coverage list named this file.

Each case's tree was a worktree of its repository's primary checkout,
which *What a case holds* rules out. Three runs noted that the local
`origin/main` already holds the landed change: the one on PR
btclib-org/.github#2288, the clean case, which did not read it; the one
on PR btclib-org/btclib-node#2516, which compared the head with it and
found the touched files unchanged; and the one on PR btclib-org/ecc#580,
which read the merge with it and found the prose unchanged, its hit
resting on a walk of the head. The run on PR
btclib-org/ai-agents-process#317 tried the merge with the local
`origin/main`, which conflicted, and read the head alone. No run read a
fix. The runs on PR btclib-org/btclib-node#2516 and PR
btclib-org/ecc#580 ran tests of the branch as inputs to measure a
finding; neither ran the suite as a gate.

- **Baseline and candidate**, 2026-11-15: `$PROCESS` `e91f4c3` and
  `9c5ada8`, tree `caf3c0374e5fe127aa7d28ec68b324a33bb3cc60`, the factor
  changed being the brief: the changelog bullet of `writing.md`'s *What
  the prose that lands may say*, which PR
  btclib-org/ai-agents-process#502 rewrites, and which alone `git diff
  e91f4c3 9c5ada8` changes. Claude Code, the `reviewer` agent, Opus,
  effort `high`, one run per case, and a second on PR
  btclib-org/.github#2288, then the clean case, since its first two runs
  differed. In both: PR btclib-org/ai-agents-process#317: miss. PR
  btclib-org/ai-agents-process#444: hit. PR
  btclib-org/btclib-secp256k1#1331: miss. PR btclib-org/ecc#484: hit. PR
  btclib-org/btclib-node#2516: miss (*How a run is scored*). PR
  btclib-org/ecc#580: hit. PR btclib-org/.github#2288, scored as a
  defect: the baseline hit, then miss on the repeat; the candidate miss,
  then hit.

On PR btclib-org/.github#2288 all four runs raise the same finding,
which holds, and which moved the case to the defects (*What a case
holds*). Two runs weigh it blocking and two non-blocking, one of each in
each configuration. On PR btclib-org/ai-agents-process#317 both block on
"tied to the account", which holds, and the candidate names the
exemption only as non-blocking. On PR btclib-org/ecc#484 the candidate
also blocks on the rule being stated a second time in the review
workflow's prompt, as the run at `cab9c97` did, which was not measured
false. No finding of either configuration was measured false.

Each reviewer read the process from a copy of `process/` at its sha
without this file, and the case from a repository holding only the head
and its ancestors (*What a case holds*). The brief forbade the network,
the forge, any suite and any other checkout of the case's repository,
and every reviewer reports that it ran no gate. On PR
btclib-org/btclib-secp256k1#1331 the baseline's reviewer ran its harness
under Valgrind in a local container with no network, reading the zkp pin
from a local upstream clone, and the candidate's built it against a
stand-in memcheck header. On PR btclib-org/btclib-node#2516 both loaded
btclib, read-only, from outside the tree. The labels were random, and
the scores were written before the key was read.

The candidate has the baseline's hits and misses on the other six cases,
and on PR btclib-org/.github#2288 each configuration hits once in two
runs. The run shows no loss from the bullet, and cannot show a gain: no
case's defect concerns a changelog entry.

- **Baseline and candidate**, 2026-11-16: `$PROCESS` `9dd351e` and
  `bd66221`, tree `217ea4c4d2a9aff74cc8f95e07caad5c9079487c`, the factor
  changed being the brief: the sentence the change for ISS
  btclib-org/ai-agents-process#486 adds to `writing.md`'s bullet on an
  issue owed by several trees, which excepts a port of the standard from
  the switch to a closing keyword, and which alone `git diff 9dd351e
  bd66221 -- process` changes. Claude Code, the `reviewer` agent, Opus,
  effort `high`, one run per case, and a second on PR
  btclib-org/ai-agents-process#317, since its first two runs differed.
  In both: PR btclib-org/ai-agents-process#444: hit. PR
  btclib-org/ecc#484: hit. PR btclib-org/btclib-secp256k1#1331: miss. PR
  btclib-org/.github#2288: miss. PR btclib-org/btclib-node#2516: miss.
  PR btclib-org/ecc#580: miss. PR btclib-org/ai-agents-process#317: the
  baseline hit, then miss on the repeat; the candidate miss, then miss.

On PR btclib-org/ai-agents-process#317 all four runs block on "tied to
the account", which holds. The baseline's first run also blocks on the
exemption of the resumed run; the other three read the same wait as
already in the base's text and put it as collateral or as no finding.
On PR btclib-org/.github#2288 both runs raise the lookbehind's single
space as a non-blocking finding, the candidate's on the commit message
alone, which is a miss (*How a run is scored*). On PR btclib-org/ecc#580
neither names the comment over `_AFF_CALLS`. No finding of either
configuration was measured false.

Each reviewer read the process from a copy of `process/` at its sha
without this file, and the case from a repository holding only the head
and its ancestors (*What a case holds*). The brief forbade the network,
the forge, any suite and any other checkout of the case's repository,
and every reviewer reports that it ran no gate. On PR
btclib-org/btclib-secp256k1#1331 the baseline's reviewer ran the harness
under Valgrind in a local container with no network, reading the zkp pin
from a local upstream clone, and the candidate's built it against a
stand-in memcheck header. On PR btclib-org/ai-agents-process#444 the
baseline's reviewer read the standard at the port's sha from the local
clone of btclib-org/.github. On PR btclib-org/btclib-node#2516 the
baseline's loaded btclib, read-only, from the uv cache. The baseline's
first reviewer of PR btclib-org/ai-agents-process#317 reports that the
process copy states the case's bullet in a later form, which answers its
findings, and that it derived them from the head's text. The candidate's
reviewer of PR btclib-org/ecc#580 wrote no verdict file, holding its
definition over the brief, and its hand-back is the verdict. No
verdict's coverage list named this file. The labels were random.

The candidate has the baseline's hits and misses on six cases. On PR
btclib-org/ai-agents-process#317 the baseline hits once in two runs and
the candidate in neither, and the defect there does not concern a
citation. The run shows no loss it can tie to the sentence, and cannot
show a gain: no case's defect concerns how a port's issue closes.

- **Baseline and candidate**, 2026-11-16: `$PROCESS` `2854831` and
  `8990d03`, tree `cc159c93aae1249432875cf0b844206277de6121`, the factor
  changed being the brief: the sentences the change for ISS
  btclib-org/ai-agents-process#495 moves, which alone `git diff 2854831
  8990d03 -- process` changes. In `local-review.md`, *Every reviewer
  tries to break the change* points to `writing.md`'s *Writing work* for
  what the fix of a blocking finding adds, and the item of *The verdict*
  on a new major version asks for the notes, each named, and whether
  anything in them breaks the tree, and says what a major move is. In
  `writing.md`'s *Writing work*, a new item has the fix of a blocking
  finding that rests on an input add that input as a test. Claude Code,
  the `reviewer` agent, Opus, effort `high`, one run per case. In both:
  PR btclib-org/ai-agents-process#317: miss. PR
  btclib-org/ai-agents-process#444: hit. PR
  btclib-org/btclib-secp256k1#1331: miss. PR btclib-org/ecc#484: hit. PR
  btclib-org/.github#2288: miss. PR btclib-org/btclib-node#2516: miss.
  PR btclib-org/ecc#580: hit.

On PR btclib-org/ai-agents-process#317 both block on "tied to the
account", which holds, and put the exemption of the resumed run as
collateral. On PR btclib-org/btclib-secp256k1#1331 the baseline names
the hold to exit code `42` as a non-blocking finding, and the candidate
raises none on it. On PR btclib-org/.github#2288 the baseline raises the
lookbehind's single space as a non-blocking finding, and the candidate
lists the other spacings only among the claims it tried. On PR
btclib-org/btclib-node#2516 both name "`i` sums the length fields" as
non-blocking wording. On PR btclib-org/ecc#484 the baseline also blocks
on the rule being stated a second time in the review workflow's prompt,
as the candidates at `cab9c97` and `9c5ada8` did, which was not measured
false.

Each reviewer read the process from a copy of `process/` at its sha
without this file, and the case from a repository holding only the head
and its ancestors (*What a case holds*). A first candidate copy, built
at `f5d2025`, before the change's fixes, was discarded before any
reviewer read it. The brief forbade the network, the forge, any suite
and any other checkout of the case's repository, and every reviewer
reports that it ran no gate. On PR btclib-org/btclib-secp256k1#1331 the
baseline's reviewer could not read the zkp source and left its coverage
claim as a question, and the candidate's read local clones of
secp256k1-zkp and secp256k1 with `git show`, `git ls-tree` and `git
archive`, and built the harness against a stand-in memcheck header. On
PR btclib-org/btclib-node#2516 the baseline's loaded btclib 2026.11.10
from another repository's environment, not the lock's 2026.11.12, and
the candidate's loaded the lock's version in an environment it built
offline from the uv cache in its scratch directory. No verdict names
this file. The order of the runs and their labels were random.

The candidate has the baseline's hits and misses on all seven cases, so
no case decides the comparison alone and none was run again (*One factor
at a time*). The run shows no loss from the change, and cannot show a
gain: no case's defect concerns the test a fix adds or a major version.

- **Baseline and candidate**, 2026-11-16: `$PROCESS` `aa06777` and
  `25e8949`, tree `e2902b7f3615976e92dbf2d79f24cc6739e4bb53`, the factor
  changed being the brief: the move of ISS
  btclib-org/ai-agents-process#492, which
  `git diff aa06777 25e8949 -- process` makes, of the text only the
  orchestrator acts on from the reviewer's files to `orchestration.md`,
  which the reviewer's map does not give it. Out of `every-role.md` go
  starting and resuming an agent, how the session starts and prepares
  the reviewer in the other client, the Codex escalation measurements,
  undoing an accident in the primary checkout, where a session's memory
  puts each fact, and closing collateral. Out of `local-review.md` go
  the convergence check, a session restart, the classes carried forward,
  the findings record, the other client being unavailable, the Codex
  pass, the port check, and a rebase and the clearance. The reviewer
  keeps what its sandbox lets it write, run and read, the human's answer
  standing in for an input's result, how a finding quotes its lines, now
  in `local-review.md`'s *The verdict*, and the merge of `main` that
  resolved nothing, now *A merge of `main` and the clearance*; its
  pointers to the moved text name `orchestration.md`. Claude Code, the
  `reviewer` agent, Opus, effort `high`, one run per case, and a second
  in each configuration on PR btclib-org/.github#2288 and PR
  btclib-org/ecc#580, where the first runs differed. In both: PR
  btclib-org/ai-agents-process#317: miss. PR
  btclib-org/ai-agents-process#444: hit. PR
  btclib-org/btclib-secp256k1#1331: miss. PR btclib-org/ecc#484: hit. PR
  btclib-org/btclib-node#2516: miss. PR btclib-org/.github#2288: the
  baseline miss, then miss; the candidate hit, then hit. PR
  btclib-org/ecc#580: the baseline hit, then hit; the candidate miss,
  then hit.

On PR btclib-org/ai-agents-process#317 both block on "tied to the
account", which holds; the baseline names the exemption of the resumed
run only in a non-blocking finding and the candidate puts it as
collateral, both reading it as already in the base's text. On PR
btclib-org/btclib-secp256k1#1331 the baseline blocks on another finding,
that the step holds each call to a list in the workflow where the tree
says it holds it to `SECURITY.md`'s record, and the candidate clears it;
neither says that exit `42` answers for every memcheck error. On PR
btclib-org/.github#2288 the baseline's first run lists the other
spacings among the claims it tried as holding, and its repeat names the
single-space limit only as a non-blocking refinement (*How a run is
scored*). On PR btclib-org/ecc#580 the candidate's first run lists
`add_var`, `require_on_curve` and `is_on_curve` in its own walk of the
class and raises no finding on the comment over `_AFF_CALLS`. Outside
the cases' defects, the baseline's first run on PR btclib-org/ecc#580
also blocks on a tuple subclass whose length overstates its items, the
candidate's on PR btclib-org/ecc#484 on the sentence describing the
pattern, which it calls false for wrapped `#:` comment lines the tree
holds, and the baseline's first on PR btclib-org/.github#2288 on the
test's docstring, which it calls false for the row the branch adds. No
finding of either configuration was measured false.

Each reviewer read the process from a copy of `process/` at its sha
without this file, built with this file's `git archive` command, and the
case from a repository holding only the head and its ancestors (*What a
case holds*). The reviewer's map is unchanged, so the candidate's
reviewer read `every-session.md`, `every-role.md`, `local-review.md` and
the sections of `writing.md` the map names, at `25e8949`, and not
`orchestration.md`. The installed `reviewer` agent is `main`'s
`agents/reviewer.md`, so the run left out the change's pointer edit
there, and no brief named a skill, so it left out the change's pointer
edits in `/btclib-pr` too. The brief forbade the network, the forge, any
suite and any other checkout of the case's repository, and every
reviewer reports that it ran no gate. A case's briefs differ only in the
copy's path and the run's label, and none names a configuration. On PR
btclib-org/btclib-secp256k1#1331 the baseline's reviewer ran the harness
under Valgrind on aarch64 in a local container with no network, reading
local clones of secp256k1-zkp and secp256k1 with `git archive`, and the
candidate's read a local secp256k1-zkp clone with `git show` and
`git archive` and built the pin in its scratch directory against a
stand-in memcheck header. On PR btclib-org/btclib-node#2516 the
baseline's reviewer loaded the lock's btclib from the uv cache, and the
candidate's used a stand-in for btclib in its scratch directory. On PR
btclib-org/.github#2288 both of the baseline's reviewers and the
candidate's second ran the head's own `check_sign_off.py` with `GIT_DIR`
set to the case's repository. On PR btclib-org/ecc#580 the candidate's
first reviewer replaced `typing_extensions` with a stub and its second
ran the test's body under a pytest stub; the removal of its exports was
refused to the baseline's second, and they stay in its scratch
directory. No verdict names this file. The runs went in a shuffled
order, the repeats last.

The candidate has the baseline's hits and misses on five cases. On the
first runs each configuration hits on three cases, the candidate on PR
btclib-org/.github#2288 and the baseline on PR btclib-org/ecc#580, so
neither case alone decides the comparison, and *One factor at a time*
asks for a repeat only where one does; both ran again all the same. Over
two runs PR btclib-org/.github#2288 is a hit in neither for the baseline
and in both for the candidate, and PR btclib-org/ecc#580 in both for the
baseline and in one for the candidate. Each case has gone both ways
before under configurations that differ in nothing it concerns: PR
btclib-org/.github#2288 hit once in two runs in each configuration at
`e91f4c3` and `9c5ada8`, and PR btclib-org/ecc#580 missed at `9dd351e`
and `bd66221` and hit in every other run above. The run shows no loss it
can tie to the move, and cannot show a gain: no case's defect concerns
the text that moved.

- **Baseline and candidate**, 2026-11-16: `$PROCESS` `9f70ee0` and
  `e49e295`, tree `8df46d6761dca32187e364bdb0820a5969a7a6bd`, the factor
  changed being the brief: the change of ISS
  btclib-org/ai-agents-process#548, which `git diff 9f70ee0 e49e295 --
  process` makes. In `writing.md`'s *The gates*, an outside
  contributor's gates run in a new worktree detached at the commit they
  gate, never in the branch's worktree, each followed by a sandboxed
  `git status` and a check from outside for a repository the gate left
  there, and no git runs outside the sandbox in that worktree but its
  removal; `every-role.md`'s *Clients* points the Codex reviewer's
  inputs to that worktree's `.venv`. Claude Code, the `reviewer` agent,
  Opus, effort `high`, one run per case, and a second in each
  configuration on PR btclib-org/ecc#580, which alone decided the first
  runs. In both: PR btclib-org/ai-agents-process#317: miss. PR
  btclib-org/ai-agents-process#444: hit. PR
  btclib-org/btclib-secp256k1#1331: miss. PR btclib-org/ecc#484: hit. PR
  btclib-org/.github#2288: miss. PR btclib-org/btclib-node#2516: miss.
  PR btclib-org/ai-agents-process#526: miss. PR
  btclib-org/ai-agents-process#522, the clean case: `CLEARED`, with no
  false finding. PR btclib-org/ecc#580: the baseline miss, then hit; the
  candidate hit, then miss.

On PR btclib-org/ai-agents-process#317 both block on "tied to the
account", which holds. On PR btclib-org/ecc#484 the baseline also blocks
on the rule being stated a second time in the review workflow's prompt,
as earlier runs did, which was not measured false. On PR
btclib-org/.github#2288 each names the single-space limit only as
non-blocking, and on PR btclib-org/btclib-node#2516 both name "`i` sums
the length fields" only as non-blocking wording (*How a run is scored*).
On PR btclib-org/ai-agents-process#526 the baseline raises a nested
bullet folded with no error, and the candidate a dash item after a
paragraph that is never compared, each only as a question. On PR
btclib-org/ecc#580 the baseline's first run blocks on a tuple subclass
whose length overstates its items, outside the defect, and the
candidate's repeat clears the head; neither names the comment over
`_AFF_CALLS`. On PR btclib-org/ai-agents-process#522 each verdict says,
as non-blocking, that "The skill" in `process/night-mode.md` names no
file, and asks a question; neither is a defect. No finding of either
configuration was measured false.

Each reviewer read the process from a copy of `process/` at its sha
without this file, and the case from a repository holding only the head
and its ancestors (*What a case holds*). The brief forbade the network,
the forge, any suite and any other checkout of the case's repository,
and every reviewer reports that it ran no gate. A network outage failed
six runs, which ran again on copies and case trees built again with this
file's commands, from the same trees and heads. The reviewers of PR
btclib-org/ai-agents-process#522 read the case tree's own copy of this
file, for which the check of *A case's tree can hold this file* prints
`unnamed`, and no verdict names another copy. Nothing was withheld: the
change edits no `REVIEWING.md` and nothing in `agents/`. No brief named
a skill, so the run left out the change's sentence in `/btclib-pr`'s
*Landing*, and the change's edits to `orchestration.md` are outside the
reviewer's map. A case's briefs differ only in the copy's path, the
run's label and, for the runs made after the outage, the directory
holding their inputs, and none names a configuration. The runs went in a
shuffled order, the repeats last. After the run the branch merged `main`
at `6445b63` in `f17978c`, which brought to the reviewer's files a wider
definition of a major move in `local-review.md`, the sweep of a piece of
work's directory in `every-role.md`, and in `writing.md` the removal of
the Sign-off control's clone, which that sweep refuses. The change's own
lines are unchanged: with `-- process agents skills REVIEWING.md`, `git
diff 6445b63 f17978c` adds and removes the lines `git diff 9f70ee0
659524d` does.

The candidate has the baseline's hits and misses on eight cases. On the
first runs PR btclib-org/ecc#580 alone decided the comparison, a hit for
the candidate only, so it ran again in both (*One factor at a time*),
and over two runs each configuration hits once. The run shows no loss it
can tie to the change, and cannot show a gain: no case's defect concerns
where an outside contributor's gates run.

- **Baseline and candidate**, 2026-11-19: `$PROCESS` `fbd575b` and
  `2a9ba3a6058a88ddda691a1b69085b111fa53a25`, tree
  `a7b691b6f82969b4c76cbb7e7c876fade1df85c1`, the factor changed being
  the brief: the change of ISS btclib-org/ai-agents-process#587, which
  `git diff fbd575b 2a9ba3a6058a88ddda691a1b69085b111fa53a25 -- process`
  makes. In `local-review.md`'s *A pull request's rounds*, every local
  reviewer's brief carries the `path_instructions` of the sha's
  `.coderabbit.yaml`, the text each links to, and classes CodeRabbit's
  review on GitHub found, each for the reviewer to try first; a reply to
  a bot's finding is read in the branch's rounds before it is posted;
  and the fresh reviewer of a text to be posted runs in the writer's
  client where the rounds review that text on its own. In `writing.md`'s
  *Sourcery and CodeRabbit before a push*, the CLI runs with `--deep`,
  and its read is not CodeRabbit's review on GitHub. In
  `orchestration.md`'s *Running the rounds*, the list the briefs carry
  is one place the report may propose for a class that review found.
  Claude Code, the `reviewer` agent, Opus, effort `high`, one run per
  case, and a second in each configuration on PR btclib-org/ecc#580, PR
  btclib-org/ai-agents-process#526 and PR
  btclib-org/ai-agents-process#522, the clean case, where the first runs
  differed. In both: PR btclib-org/ai-agents-process#444: hit. PR
  btclib-org/ecc#484: hit. PR btclib-org/ai-agents-process#317: miss. PR
  btclib-org/btclib-secp256k1#1331: miss. PR btclib-org/.github#2288:
  miss. PR btclib-org/btclib-node#2516: miss. PR btclib-org/ecc#580: the
  baseline miss, then hit; the candidate hit, then miss. PR
  btclib-org/ai-agents-process#526: the baseline miss, then miss; the
  candidate hit, then miss. PR btclib-org/ai-agents-process#522: the
  baseline `CLEARED`, then `CLEARED`; the candidate blocked on a false
  finding, then `CLEARED`.

On PR btclib-org/ai-agents-process#317 both runs block on "tied to the
account", which holds, and neither names the exemption of the resumed
run as the defect. On PR btclib-org/btclib-secp256k1#1331 the baseline's
run also blocks on a point outside the defect, "SECURITY.md never read",
which was not measured. On PR btclib-org/btclib-node#2516 both
configurations clear the head, with "`i` sums the length fields" only as
non-blocking wording (*How a run is scored*). On PR btclib-org/ecc#580
each hit blocks on the comment over `_AFF_CALLS`, which leaves out
`add_var`, `is_on_curve` and `require_on_curve`. On PR
btclib-org/ai-agents-process#526 the candidate's hit blocks on an item
indented two or three spaces after a closing paragraph: it is folded in
as a continuation and never compared, and the check exits `0`. The
baseline's first run names that mechanism only as non-blocking, and both
repeats name only the nested-item variant, as non-blocking.

On PR btclib-org/ai-agents-process#522 the candidate's first run blocks
on "The skill" at `process/night-mode.md:10` naming no file, and its
repeat clears the head with that point as non-blocking wording. The
baseline's two runs do not raise it. The sentence is true, since the
skill says what `/night-mode` does with each word and with none, so a
block on it is a false finding (*What a case holds*). The other findings
outside the cases' defects were not measured.

Each reviewer read the process from a copy of `process/` at its sha
without this file, and the case from a repository holding only the head
and its ancestors (*What a case holds*), for which its check prints
`isolated` and the check of *A case's tree can hold this file* prints
`unnamed`. Every run had the same brief, which named only the case's
tree, its base, the process copy and the limits. It carried no case's
`path_instructions`, no text they link to and no list of classes, so the
run tries the change's rules as a reviewer reads them in
`local-review.md`, and not what those rules have a brief carry. The
brief forbade the network, the forge, any suite, any gate and any other
checkout, and every reviewer reports that it ran no gate.

The candidate's reviewer of PR btclib-org/ai-agents-process#522 read
lines 1 to 60 of the case tree's own copy of this file, for which the
check prints `unnamed`. The candidate's reviewer of PR
btclib-org/ai-agents-process#317 read the copy's `orchestration.md`,
which words the rule the case changes as it later landed, not the case's
defect, and left one file outside its scratch directory, which it
removed. Nothing was withheld: the change edits no `REVIEWING.md` and
nothing in `agents/`. No brief named a skill, so the run left out the
change's sentence in `/btclib-pr`'s *Answering it*, and the change's
edit to `orchestration.md` is outside the reviewer's map. No reviewer
wrote a verdict file; each gave its verdict in its output only, as its
agent definition says. The labels were random, and each verdict was
scored as it arrived, against the case's defect sentence.

The candidate has the baseline's hits and misses on six cases. On PR
btclib-org/ecc#580 each configuration hits once in two runs. On PR
btclib-org/ai-agents-process#526 the candidate hits once in two and the
baseline in neither, which is too few to call a gain. On the clean case
the candidate made one false finding in two runs. The run shows no loss
of hits, and cannot show a gain, least of all from what the change has a
brief carry, which no brief of the run held.

- **Baseline and candidate**, 2026-11-19: `$PROCESS` `460205a` and
  `d5b52538e06e53b2635dcc427f78fa214d844b0b`, tree
  `ef50694b9a4dc1c9a68b92a7320fd8fc85edab5a`, the factor changed being
  the brief: the change of ISS btclib-org/ai-agents-process#585, which
  `git diff 460205a d5b52538e06e53b2635dcc427f78fa214d844b0b -- process`
  makes in `writing.md` alone, all of it in *Writing work*, which the
  reviewer's map gives whole. Its checklist asks the hooks to pass on
  the tip's tree, staged or committed, and the suite and the docs build
  on the tip itself, and reads `git status --porcelain` once the commit
  is made and the last gate has run. In `writing.md`'s *The gates*, the
  hooks and the checks that decide the suite and the docs build read the
  staged tree's diff from the merge base; a run of the hooks carries
  over to a commit of the same tree on the same merge base, which the
  log's `TREE=` lines name; the writer runs the fixers before the commit
  and signs one commit at hand-over; and in the gate lock the hooks run
  first and a failure stops the block. In `writing.md`'s *Committing and
  rebasing*, a push waits on those gates. Claude Code, the `reviewer`
  agent, Opus, effort `high`, one run per case, and a second in each
  configuration on PR btclib-org/ecc#580, where the first runs differed.
  In both: PR btclib-org/ai-agents-process#444: hit. PR
  btclib-org/ecc#484: hit. PR btclib-org/ai-agents-process#317: miss. PR
  btclib-org/btclib-secp256k1#1331: miss. PR btclib-org/.github#2288:
  miss. PR btclib-org/btclib-node#2516: miss. PR
  btclib-org/ai-agents-process#526: miss. PR
  btclib-org/ai-agents-process#522, the clean case: `CLEARED`, with no
  false finding. PR btclib-org/ecc#580: the baseline hit, then hit; the
  candidate miss, then miss.

On PR btclib-org/ai-agents-process#317 both runs block on "tied to the
account", and neither names the exemption of the resumed run as the
defect. On PR btclib-org/.github#2288 both name the lookbehind's single
space, and on PR btclib-org/btclib-node#2516 both name the wording on
`i`, only as non-blocking (*How a run is scored*). The baseline's run on
PR btclib-org/btclib-node#2516 asks for changes only because no gate run
is on record, and names no defect, so it is a miss and not a false
finding. On PR btclib-org/ai-agents-process#526 the baseline names the
item after a paragraph and the candidate only the nested item, each as
non-blocking. On PR btclib-org/ecc#580 each of the baseline's runs
blocks on the comment over `_AFF_CALLS`, which leaves out `add_var`,
`is_on_curve` and `require_on_curve`, and each of the candidate's clears
the head without naming that comment. The findings outside the cases'
defects were not measured.

Each reviewer read the process from a copy of `process/` at its sha
without this file, and the case from a repository holding only the head
and its ancestors (*What a case holds*), for which its check prints
`isolated` and the check of *A case's tree can hold this file* prints
`unnamed`. Every brief followed one template, which named only the
case's tree, its base, the process copy and the limits, and every
reviewer reports that it ran no gate. Both reviewers of PR
btclib-org/ai-agents-process#317 read the copy's `orchestration.md`,
which words the rule the case changes as it later landed. Both
reviewers of PR btclib-org/ai-agents-process#526 read the case tree's
own copy of this file, the candidate's lines 1 to 80 and the baseline's
lines 1 to 60. The baseline's reviewer of PR
btclib-org/ai-agents-process#317 opened one command with `cd`. The
change edits no `REVIEWING.md`, and neither `agents/reviewer.md` nor its
`.toml`. Its edits to `agents/writer.md`, `agents/writer.toml` and
`scripts/gate-lock.sh` are outside the reviewer's map, so the run did
not exercise them. No reviewer wrote a verdict file. The labels were
random, and each verdict was scored as it arrived, against the case's
defect sentence.

The candidate has the baseline's results on eight cases. On PR
btclib-org/ecc#580 the baseline hits in both runs and the candidate in
neither: a loss on that case, over two runs each. Under `process/` the
change touches only the gating text, the checklist's line on the gates
and its line on `git status` among it, all in `writing.md`'s *Writing
work*. The run cannot tell whether that wording moves a reviewer's
attention, or whether the difference is the variation between runs this
case has shown: in the run at `9f70ee0` and `e49e295` each configuration
hits it once in two runs, and in the run at `9dd351e` and `bd66221`
neither hits it.

- **Baseline and candidate**, 2026-11-19: `$PROCESS` `460205a` and
  `acfa6d32c9210b7aa1461d0c8b2cee508d055013`, tree
  `0f73cc704177d24a897b87ec0cef1ae8ee3fc377`, the factor changed being
  the brief: the change of ISS btclib-org/ai-agents-process#589, which
  `git diff 460205a acfa6d32c9210b7aa1461d0c8b2cee508d055013 -- process`
  makes. In `local-review.md`'s *The rounds*, from the third round of a
  branch's local review, in place of the sixth, a finding on a shape
  that is not reachable, or whose worst outcome is on the safe side, is
  filed as an issue and does not block. A refusal, a crash and a false
  sentence on a reachable shape block at any round. The verdict marks
  such a finding `filed`, with its ground and the issue's body, and the
  orchestrator files it. Claude Code, the `reviewer` agent, Opus, effort
  `high`, one run per case, and a second in each configuration on PR
  btclib-org/ecc#580, which alone decided the first runs. In both: PR
  btclib-org/ai-agents-process#444: hit. PR btclib-org/ecc#484: hit. PR
  btclib-org/ai-agents-process#522, the clean case: `CLEARED`, with no
  false finding. PR btclib-org/ai-agents-process#317: miss. PR
  btclib-org/btclib-secp256k1#1331: miss. PR btclib-org/.github#2288:
  miss. PR btclib-org/btclib-node#2516: miss. PR
  btclib-org/ai-agents-process#526: miss. PR btclib-org/ecc#580: the
  baseline miss, then miss; the candidate hit, then hit.

On PR btclib-org/ai-agents-process#444 both block on the skills that
still arm with `--auto` and cite `CONTRIBUTING.md`'s *Landing it*. On PR
btclib-org/ecc#484 both block on the perl two-argument `open` on file
names, and the candidate's reviewer holds it blocking at the third round
because an outside contributor's branch supplies the names. On PR
btclib-org/ecc#580 the candidate's runs block on the comment over
`_AFF_CALLS`, whose "each" leaves out `add_var`, `is_on_curve` and
`require_on_curve`, and the baseline's do not name it. On PR
btclib-org/btclib-node#2516 both name the `i` wording only as
non-blocking, and on PR btclib-org/btclib-secp256k1#1331 neither names
as blocking that the exit `42` refusal accepts any error.

On PR btclib-org/ai-agents-process#317, PR btclib-org/.github#2288 and
PR btclib-org/ai-agents-process#526 the candidate's reviewer finds the
defect, and the third round's rule files it in place of blocking. On PR
btclib-org/ai-agents-process#317 it names the wait of the resumed run
with its mechanism and files it as on the safe side, where the
baseline's names it only as collateral. On PR btclib-org/.github#2288 it
names the single-space lookbehind and files it as on the safe side,
where the baseline's names it only as non-blocking. On PR
btclib-org/ai-agents-process#526 it names exactly the item indented two
spaces after a prose paragraph and files it as a constructed shape,
where the baseline's does not name it. The baseline misses these three
cases anyway, so the comparison does not move. But the rule turns into
issues defects that the cases record, which a run scores as a hit only
where it blocks (*How a run is scored*).

The findings outside the cases' defects were not measured, among them
the filed finding on prose lines that look like list markers on PR
btclib-org/ai-agents-process#526, the overstated `__len__` on PR
btclib-org/ecc#580, the `#:` and `//` comment lines on PR
btclib-org/ecc#484, and both runs on PR btclib-org/ai-agents-process#317
blocking on "tied to the account".

Each reviewer read the process from a copy of `process/` at its sha
without this file, and the case from a repository holding only the head
and its ancestors, at the head and base *Cases* names. Every brief said
that this was the branch's third local round (`local-review.md`'s *The
rounds*) and gave no earlier round's verdict. Each reviewer was fresh,
at fresh context, read the case only from its tree and the process only
from the copy, used no network, no forge and no gate, and gave its
verdict in its output only. The runs went in a shuffled order. The
copies hold `process/` alone, so the run left out the change's edit to
`/btclib-iss`'s *Opening the pull request*. Nothing was withheld: the
change edits no `REVIEWING.md` and nothing in `agents/`. The account's
API limit stopped five runs, which resumed where they stopped once it
reset. A first launch of the baseline's run on PR
btclib-org/btclib-secp256k1#1331 went out with a cut-off brief, was
stopped about three seconds in after listing the primary checkout's
`process/` and the cases directory, and was relaunched with the full
brief. The baseline's reviewer of PR btclib-org/btclib-node#2516 ran
none of its own inputs, since memory pressure stayed at level 2 for the
whole run.

After the run the branch merged `main` twice: at `bcbd810` in `ed608ae`,
which brought to the reviewer's files the change of ISS
btclib-org/ai-agents-process#587 that the run at `fbd575b` and
`2a9ba3a6058a88ddda691a1b69085b111fa53a25` tried and the sign-off
closing's exemption in `every-role.md`; and at `d2da963` in `6de8585`,
which brought the change of ISS btclib-org/ai-agents-process#585 to
`writing.md`'s *Writing work*, tried in the entry above. The change's
own lines are unchanged: with `-- process agents skills REVIEWING.md`,
neither merge changes the lines `git diff 460205a acfa6d3` adds and
removes.

The candidate has the baseline's hits and misses on eight cases, and
loses none. Over the defects the baseline hits on two cases and the
candidate on three, and neither makes a false finding on the clean case.
The difference is PR btclib-org/ecc#580, whose defect is a false
sentence, which blocks at any round in both configurations. That case
has gone both ways before under configurations that differ in nothing
it concerns (the runs above), so the run cannot tie the gain to the
change.

- **Baseline and candidate**, 2026-11-19: `$PROCESS` `ebd995a` and
  `f7b7ce4a5b4e7b75494899bcab9d6f56b03c0a15`, tree
  `fcfa4f0f017fbbe7ca4db53bcb7a05ad3c78057a`, the factor changed being
  the brief: the change of ISS btclib-org/ai-agents-process#624, which
  `git diff ebd995a f7b7ce4a5b4e7b75494899bcab9d6f56b03c0a15 -- process`
  makes in `local-review.md`'s *The rounds* alone. From the third round,
  a reviewer that cannot run the search showing a finding's shape is not
  reachable, as one that needs the forge, gives the command and names it
  as not run. The orchestrator runs it before filing. The finding blocks
  where what it printed shows a tree or a caller holding the shape, or
  where the orchestrator cannot run it either. Claude Code, the
  `reviewer` agent, Opus, effort `high`, one run per case, and a second
  in each configuration on PR btclib-org/ecc#580, which alone decided
  the first runs. In both: PR btclib-org/ecc#484: hit. PR
  btclib-org/ai-agents-process#444: hit. PR
  btclib-org/ai-agents-process#317: miss. PR
  btclib-org/btclib-secp256k1#1331: miss. PR btclib-org/.github#2288:
  miss. PR btclib-org/btclib-node#2516: miss. PR
  btclib-org/ai-agents-process#526: miss. PR
  btclib-org/ai-agents-process#522, the clean case: `CLEARED`, with no
  false finding. PR btclib-org/ecc#580: the baseline miss, then hit; the
  candidate hit, then hit.

On PR btclib-org/ecc#484 both block on perl `-n` opening hostile file
names, and on PR btclib-org/ai-agents-process#444 both block on the
skills that still arm with `--auto`. On PR btclib-org/ecc#580 both of
the candidate's runs and the baseline's second block on the comment over
`_AFF_CALLS`, which leaves out `add_var`, `is_on_curve` and
`require_on_curve`, and the baseline's first clears the head without
naming it. On PR btclib-org/ai-agents-process#317 both block on the hold
covering limits that reset, and the candidate names the wait of the
resumed run only as `filed`. On PR btclib-org/btclib-secp256k1#1331 both
clear the head, and neither names the exit `42`. The candidate clears it
while naming as not run the inputs that bear on the case, the zkp source
at the pin and Valgrind. On PR btclib-org/.github#2288 both clear the
head: that no test pins the lookbehind is non-blocking in the candidate
and `filed` in the baseline. On PR btclib-org/btclib-node#2516 both
clear the head, and the candidate names "`i` sums the length fields"
only as non-blocking (*How a run is scored*).

On PR btclib-org/ai-agents-process#526 the candidate's verdict takes the
route the change adds. It files the defect, the item indented after a
prose paragraph that is never compared while the check exits `0`, and
names as not run the forge search that decides whether a tree holds that
shape. The run scores the verdict as given, so the defect is `filed` and
a miss. The baseline blocks on a numbered prose line the item pattern
refuses, outside the defect, and names the indented item only as
collateral. The findings outside the cases' defects were not measured.

Each reviewer read the process from a copy of `process/` at its sha
without this file, for which its check prints `copied`, and the case
from a repository holding only the head and its ancestors (*What a case
holds*), for which its check prints `isolated` and the check of *A
case's tree can hold this file* prints `unnamed`. `diff -r` of the two
copies shows only the change's paragraph. Every brief said that this was
the branch's third local round, gave no earlier round's verdict, and
forbade the network, the forge, any suite and any gate. The briefs were
given inline. Both reviewers of PR btclib-org/ai-agents-process#522 list
the case tree's own copy of this file as read. Nothing was withheld: the
change edits no `REVIEWING.md`, no skill and nothing in `agents/`.

The candidate has the baseline's hits and misses on eight cases, and
loses none. On the first runs the baseline hits on two cases and the
candidate on three, and neither makes a false finding on the clean case.
PR btclib-org/ecc#580 alone decided the first runs, so it ran again in
both (*One factor at a time*), and over two runs the baseline hits it
once and the candidate twice. That case has gone both ways before under
configurations that differ in nothing it concerns (the runs above), so
the run shows no gain from the change.

- **Baseline and candidate**, 2026-11-20: `$PROCESS` `80b7f26` and
  `341cc33e60e89ee9c74fd536fe84a4d1359b8ddf`, tree
  `6ac4631eee6d6252ebdc1e38332f2bd15b254ec2`, the factor changed being
  the brief: the change of ISS btclib-org/ai-agents-process#612 and ISS
  btclib-org/ai-agents-process#614, which `git diff 80b7f26
  341cc33e60e89ee9c74fd536fe84a4d1359b8ddf -- process` makes in
  `local-review.md`: in its *The rounds*, and in the sentence of its *A
  pull request's rounds* on a reply that declines a finding. A file
  name, a text or a file's content is reachable where an outside
  contributor's branch can put it where the code or a command of the
  process reads it, a branch to another repository only where a command
  of the process reads it before it lands. A reviewer's own test input
  that reaches the code only through a call it writes is constructed.
  From the third round on the forge, a finding the local rule files is
  filed, not fixed. A reply that declines a false sentence the branch
  adds, which the forge keeps off the branch, is a finding. Claude Code,
  the `reviewer` agent, Opus, effort `high`, one run per case, and a
  second in each configuration on PR btclib-org/ecc#484, which alone
  decided the first runs. In both: PR btclib-org/ai-agents-process#444:
  hit. PR btclib-org/ai-agents-process#317: miss. PR
  btclib-org/btclib-secp256k1#1331: miss. PR btclib-org/.github#2288:
  miss. PR btclib-org/btclib-node#2516: miss. PR
  btclib-org/ai-agents-process#526: miss. PR btclib-org/ecc#580: miss.
  PR btclib-org/ai-agents-process#522, the clean case: `CLEARED`, with
  no blocking finding. PR btclib-org/ecc#484: the baseline miss, then
  hit; the candidate hit, then hit.

On PR btclib-org/ecc#484 the candidate's runs block on perl's `<>`
opening hostile file names, as `cmd|` runs and `-i` truncates, which an
outside contributor's branch can supply. The baseline's first run names
it only as `filed`, and its second blocks on it. On PR
btclib-org/ai-agents-process#444 both block on the skills that still arm
with `--auto`. On PR btclib-org/ai-agents-process#526 the candidate
blocks on another finding, outside the defect: the item pattern refuses
a wrapped prose line opening with `14.` and exits `2`. It does not name
the item indented after a paragraph, which the baseline names only as
`filed`. On PR btclib-org/ai-agents-process#317 the baseline blocks on
the hold covering limits that reset, as in the runs above, and the
candidate clears the head with non-blocking findings only. On PR
btclib-org/.github#2288 both name whitespace other than one space only
as `filed`. On PR btclib-org/btclib-secp256k1#1331 the baseline names
only as `filed` that any exit `42` reads as a secret reaching a branch,
and the candidate does not name it. On PR btclib-org/btclib-node#2516
both name "`i` sums the length fields" only as non-blocking, and on PR
btclib-org/ecc#580 neither names what the comment over `_AFF_CALLS`
leaves out. The findings outside the cases' defects were not measured.

Both of the baseline's verdicts on PR btclib-org/ecc#484 cite the
session's auto-memory note of the maintainer's answer on ISS
btclib-org/ai-agents-process#614, which states the candidate's rule, and
the second's hit blocks on it. The note reached the reviewer from
neither the copy nor the case's tree. ISS
btclib-org/ai-agents-process#677 is filed for it.

Each reviewer read the process from a copy of `process/` at its sha
without this file, for which its check prints `copied`, and the case
from a repository holding only the head and its ancestors, for which its
check prints `isolated` and the check of *A case's tree can hold this
file* prints `unnamed`. Each read its brief from a file in the run's
directory, not inline. The copies hold `process/` alone, so the run left
out the change's edit to `/btclib-pr`'s *Answering it*. Nothing was
withheld: the change edits no `REVIEWING.md` and nothing in `agents/`. A
baseline reviewer of PR btclib-org/ai-agents-process#522 read its case
tree's own copy of this file down to line 60, which is the head's own
(*A case's tree can hold this file*), so its verdict stands.

The candidate has the baseline's hits and misses on eight cases, and
loses none, and neither blocks on the clean case. PR btclib-org/ecc#484
alone decided the first runs, so it ran again in both (*One factor at a
time*), and over two runs the baseline hits it once and the candidate
twice. The memory note confounds that difference, so the run cannot tie
it to the change.

- **Candidate**, 2026-11-20, for ISS btclib-org/ai-agents-process#588:
  `$PROCESS` `80b7f26`, the factor changed being the effort: `medium`,
  against the baseline at `80b7f26` above, at `high`. Claude Code, the
  `reviewer` agent, Opus, one run per case. PR
  btclib-org/ai-agents-process#444: hit. PR btclib-org/ecc#484: hit. PR
  btclib-org/ai-agents-process#317: miss. PR
  btclib-org/btclib-secp256k1#1331: miss. PR btclib-org/.github#2288:
  miss. PR btclib-org/btclib-node#2516: miss. PR
  btclib-org/ai-agents-process#526: miss. PR btclib-org/ecc#580: miss.
  PR btclib-org/ai-agents-process#522, the clean case: `CLEARED`, with
  no blocking finding.

Its reviewers read the process from the baseline's copy above, for which
the check prints `copied`, the cases from the same trees, and each its
brief from a file. The hit on PR btclib-org/ecc#484 rests on the same
memory note as the baseline's second run (above). Effort `medium` has
the baseline's hits and misses on eight cases, and loses none, and on PR
btclib-org/ecc#484 it hits, as the baseline's second run does. Its
findings outside the cases' defects were not measured either.

- **Candidate**, 2026-11-20, for ISS btclib-org/ai-agents-process#620:
  `$PROCESS` `3e291f3e9d03187113523cf9fa705400df72aa46`, tree
  `1adc27f256ca9de6d8957c4fe1316a00ebff6b80`, the factor changed being
  the brief: the change of ISS btclib-org/ai-agents-process#620, ISS
  btclib-org/ai-agents-process#664 and ISS
  btclib-org/ai-agents-process#668, which `git diff d469992
  3e291f3e9d03187113523cf9fa705400df72aa46 -- process` makes in
  `writing.md` alone, all of it in *Writing work*, which the reviewer's
  map gives whole. Each `TREE=` line of a gate run names `HEAD`, and a
  run of the suite or the docs build counts only where both lines name,
  as `HEAD`, the commit the report names. The gate blocks write the file
  `mktemp` made with `>|`, and the gates that follow hooks whose run
  carries over run in a block of their own. The baseline is the run at
  `80b7f26` for ISS btclib-org/ai-agents-process#612 and ISS
  btclib-org/ai-agents-process#614, which PR
  btclib-org/ai-agents-process#673 records, its runs reused but its
  second on PR btclib-org/ecc#580, made in this run from a copy at
  `80b7f26`, since that case alone decided the first runs (*One factor
  at a time*): `git diff 80b7f26 d469992 -- process agents skills
  REVIEWING.md`, from it to the candidate's merge base, prints nothing.
  Claude Code, the `reviewer` agent, Opus, effort `high`, one run per
  case, and the baseline's two on PR btclib-org/ecc#484 and two on PR
  btclib-org/ecc#580. In both: PR btclib-org/ai-agents-process#444: hit.
  PR btclib-org/ai-agents-process#317: miss. PR
  btclib-org/btclib-secp256k1#1331: miss. PR btclib-org/.github#2288:
  miss. PR btclib-org/btclib-node#2516: miss. PR
  btclib-org/ai-agents-process#526: miss. PR
  btclib-org/ai-agents-process#522, the clean case: `CLEARED`, with no
  blocking finding. PR btclib-org/ecc#484 and PR btclib-org/ecc#580: the
  baseline miss, then hit; the candidate hit.

On PR btclib-org/ecc#484 the candidate blocks on perl's `<>` opening
hostile file names, as `-i` and `cmd|` show, which an outside
contributor's branch can supply. The baseline's first run names it only
as `filed`, and its second blocks on it. On PR btclib-org/ecc#580 the
candidate blocks on the comment over `_AFF_CALLS`, which leaves out
methods that take an affine point. The baseline's first run does not
name it, and its second blocks on it. On PR
btclib-org/ai-agents-process#444 both block on the skills that still arm
with `--auto`. On PR btclib-org/ai-agents-process#317 the baseline
blocks on the hold covering limits that reset, as in the runs above, and
the candidate clears the head without blocking on it. On PR
btclib-org/ai-agents-process#526 the baseline names the item indented
after a paragraph only as `filed`, and the candidate does not name it.
On PR btclib-org/.github#2288 the baseline names whitespace other than
one space only as `filed`, and the candidate only in a non-blocking
finding. On PR btclib-org/btclib-secp256k1#1331 the baseline names only
as `filed` that any exit `42` reads as reported, and the candidate does
not name it. On PR btclib-org/btclib-node#2516 the baseline names "`i`
sums the length fields" only as non-blocking, and the candidate measures
that `i` also counts the fixed-width fields and calls the sentence true.
The findings outside the cases' defects were not measured.

Both of the baseline's verdicts on PR btclib-org/ecc#484 cite the
session's auto-memory note of the maintainer's answer on ISS
btclib-org/ai-agents-process#614, for which ISS
btclib-org/ai-agents-process#677 is filed. The candidate's verdict on it
cites no memory note.

Each reviewer read the process from a copy of `process/` at its sha
without this file, for which its check prints `copied`, and the cases
from the same trees as the baseline. Each read its brief from a file.
The copies hold `process/` alone, and nothing was withheld: the change
edits no `REVIEWING.md`, no skill and nothing in `agents/`.

The candidate hits each case the baseline hits in either of its runs,
and loses none, and neither blocks on the clean case. On PR
btclib-org/ecc#580 the baseline's second run hits too, so the
candidate's hit is within the baseline's spread, not a gain. On PR
btclib-org/ecc#484 the memory note confounds the baseline, so the run
does not compare the two there.

- **Candidate**, 2026-11-20, for ISS btclib-org/ai-agents-process#634:
  `$PROCESS` `0cc65b8`, tree `e386a4605299cdc6545eba1d5e5cb7a57c1737a8`,
  the factor changed being the brief: the change of that issue, which
  `git diff 80b7f26 0cc65b8 -- process` makes in `writing.md` alone, all
  of it in *The gates*, under *Writing work*, which the reviewer's map
  gives whole. The bullet that leaves the suite to CI where no test of
  the tree reads a file of the diff goes, with its block, so the suite
  runs locally as the other rules of `writing.md`'s *The gates* say, and
  the hooks of a diff that changes only Markdown run outside the gate
  lock only where the tree's gates hold no suite. The baseline is its
  merge base, `80b7f26`: the runs at effort `high` made for ISS
  btclib-org/ai-agents-process#612 and ISS
  btclib-org/ai-agents-process#614 the same day, reused but for its
  second run on PR btclib-org/ecc#580. Claude Code, the `reviewer`
  agent, Opus, effort `high`, one run per case, a second in the baseline
  on PR btclib-org/ecc#484, and a second in each configuration on PR
  btclib-org/ecc#580, the baseline's made in this run. PR
  btclib-org/ai-agents-process#444: hit in both. PR btclib-org/ecc#484:
  the candidate hit; the baseline miss, then hit. PR
  btclib-org/ai-agents-process#317: miss in both. PR
  btclib-org/btclib-secp256k1#1331: miss in both. PR
  btclib-org/.github#2288: miss in both. PR btclib-org/btclib-node#2516:
  miss in both. PR btclib-org/ai-agents-process#526: miss in both. PR
  btclib-org/ai-agents-process#522, the clean case: `CLEARED` in both,
  with no blocking finding. PR btclib-org/ecc#580: the candidate hit,
  then hit; the baseline miss, then hit.

On PR btclib-org/ai-agents-process#444 both block on the skills that
still arm with `--auto`. On PR btclib-org/ecc#484 the candidate blocks
on perl's `<>` opening hostile file names, which the pull request's
author can supply. On PR btclib-org/ecc#580 the candidate's runs and the
baseline's second block on the comment over `_AFF_CALLS`, which leaves
out `add_var`, `require_on_curve` and `is_on_curve`, and the baseline's
first clears the head without naming it. On PR
btclib-org/ai-agents-process#317 both block on "tied to the account"
covering limits that reset, as in the runs above. On PR
btclib-org/.github#2288 both name whitespace other than one space only
as `filed`, and on PR btclib-org/ai-agents-process#526 both name the
item indented after a paragraph only as `filed`. On PR
btclib-org/btclib-secp256k1#1331 the baseline names only as `filed` that
any exit `42` reads as a secret reaching a branch, and the candidate
does not name it. On PR btclib-org/btclib-node#2516, where the baseline
of 2026-11-19 above asks for changes only because no gate run is on
record, both clear the head and name "`i` sums the length fields" only
as non-blocking. The findings outside the cases' defects were not
measured.

Both of the baseline's verdicts on PR btclib-org/ecc#484 cite the
session's auto-memory note of the maintainer's answer on ISS
btclib-org/ai-agents-process#614, which reached the reviewer from
neither the copy nor the case's tree (ISS
btclib-org/ai-agents-process#677), and the second's hit rests on it.

Each candidate reviewer read the process from a copy of `process/` at
its sha without this file, for which its check prints `copied`, the case
from the same tree as the baseline's reviewer, and its brief from a file
in the run's directory, not inline. Nothing was withheld: the change
edits no `REVIEWING.md` and nothing in `agents/` or `skills/`.

The candidate has the baseline's hits on PR
btclib-org/ai-agents-process#444 and PR btclib-org/ecc#484, loses none,
and blocks on nothing in the clean case. On PR btclib-org/ecc#580 it
hits twice where the baseline's first run misses, but the baseline's
second run hits too, so the difference is within the baseline's spread
and shows no gain from the change.

- **Baseline and candidate**, 2026-11-21: `$PROCESS` `4f8000a` and
  `43acfa66891d109417da8d4c7fd3b5edb2cb4eff`, tree
  `96cd75be81487e6596295f6cf763fc7dc41eac85`, the factor changed being
  the brief: the change of ISS btclib-org/ai-agents-process#694 and ISS
  btclib-org/ai-agents-process#695, which `git diff 4f8000a
  43acfa66891d109417da8d4c7fd3b5edb2cb4eff -- process agents skills
  REVIEWING.md` makes in `writing.md` alone, all of it in *The gates*,
  under *Writing work*, which the reviewer's map gives whole. On an
  outside contributor's branch both `TREE=` lines' `HEAD=` name the
  commit `<wt>` holds, and a run in `<gate wt>` counts for `<sha>` where
  `<gate wt>` was added at `<sha>` and both lines name `<sha>` as
  `HEAD`. The sandbox's status block and its `log stream` write their
  file with `>|`. The baseline is the candidate's merge base, the parent
  of `43acfa6`, run anew since the brief's files there differ from those
  of every run above. Claude Code, the `reviewer` agent as
  `agents/reviewer.md` defines it at both shas, Opus, effort `high`, one
  run per case. In both: PR btclib-org/ai-agents-process#444: hit. PR
  btclib-org/ecc#484: hit. PR btclib-org/ai-agents-process#317: miss. PR
  btclib-org/btclib-secp256k1#1331: miss. PR btclib-org/.github#2288:
  miss. PR btclib-org/btclib-node#2516: miss. PR btclib-org/ecc#580:
  miss. PR btclib-org/ai-agents-process#526: miss. PR
  btclib-org/ai-agents-process#522, the clean case: `CLEARED`, with no
  blocking finding.

On PR btclib-org/ecc#484 both block on perl's `<>` running or rewriting
hostile tracked names, which an outside contributor's branch can supply,
as `local-review.md`'s *The rounds* holds at both shas, which descend
from the landing of PR btclib-org/ai-agents-process#673. Neither rests
on a note outside the brief, unlike the hits at `80b7f26` above. On PR
btclib-org/ai-agents-process#444 both block on the skills that still arm
with `--auto`. On PR btclib-org/ai-agents-process#317 the baseline
blocks on "tied to the account" covering limits that reset, a finding
that holds, as in the runs above, and the candidate names it only as
non-blocking and clears the head. On PR btclib-org/btclib-secp256k1#1331
the baseline does not name that any exit `42` reads as reported, and the
candidate names it only as non-blocking. On PR btclib-org/.github#2288
both name whitespace other than one space only as `filed`, a constructed
shape whose search of the other trees needs the forge. On PR
btclib-org/btclib-node#2516 the baseline names "`i` sums the length
fields" only as non-blocking, and the candidate only in a non-blocking
finding on the commit message. On PR btclib-org/ecc#580 neither names
what the comment over `_AFF_CALLS` leaves out. On PR
btclib-org/ai-agents-process#526 the baseline does not name the item
indented after a paragraph, and the candidate names it as `filed` and in
a non-blocking finding. The searches the two `filed` findings name, of
the other trees' justifications and of section 14 of
btclib-org/.github's `README.md`, were run after the verdicts, in the
local review of this entry, and found no tree holding either shape, so
both findings stay filed. The other findings outside the cases' defects
were not measured.

Every verdict ends `Outside the brief: none`, the screen of *A reviewer
carries more than its brief* prints `unaided` for each, and none rests
on or quotes a note of an instruction file or of the memory index. The
orchestrator read the instruction files and the index before the first
reviewer and after the last verdict, and no note of either states the
change under test or a case's finding.

Each reviewer read the process from a copy of `process/` at its sha
without this file, for which its check prints `copied`, the case from
the tree of the 2026-11-20 runs above, at the same head, for which the
checks still print `isolated` and `unnamed`, and its brief from a file
in the run's directory. The brief was that of the runs above, with a
scratch directory of the reviewer's own, which the orchestrator made
with the `mkdir` that refuses a path that exists and removed once it
saved the verdict, and with the paragraph that makes neither an
instruction file nor the memory index a ground for a finding. The
candidate's reviewer of PR btclib-org/ai-agents-process#522 read its
case tree's own copy of this file down to line 60, the head's own, and
no case entry, so its verdict stands. No verdict lists or quotes another
copy. Nothing was withheld: the change edits no `REVIEWING.md` and
nothing in `agents/` or `skills/`.

The run departed from its plan. While the first reviewers ran, the
orchestrator appended to every brief file a line asking each reviewer to
also save its verdict to a file outside its scratch directory, and
removed it from all of them once a reviewer reported it. The reviewers
of PR btclib-org/ai-agents-process#317, PR
btclib-org/ai-agents-process#522 and PR btclib-org/ai-agents-process#526
started while it stood, and each declined it, citing the agent
definition's rule that the verdict goes in the output only. So did the
baseline's reviewer of PR btclib-org/ecc#580, which saw the brief change
while it ran. The verdicts on PR btclib-org/ai-agents-process#444 and PR
btclib-org/ecc#484, and the candidate's on PR btclib-org/ecc#580, do not
mention the line, so on PR btclib-org/ecc#580 only the baseline's
reviewer is shown to have read it. The reviewers of PR
btclib-org/.github#2288, PR btclib-org/btclib-node#2516 and PR
btclib-org/btclib-secp256k1#1331 had no such line. The line stood on
both sides of each case it reached, so no case compares a brief with it
against one without it.

Every reviewer named the conflict between the brief, which forbids the
gates, and `local-review.md`'s *The gates are the writer's*, which has a
reviewer run them where none is on the record, and ran none, as in the
runs above.

The candidate has the baseline's hits on PR
btclib-org/ai-agents-process#444 and PR btclib-org/ecc#484, loses none,
and blocks on nothing in the clean case. No case alone decides the
comparison, so none ran again. On PR btclib-org/ecc#580 one run per side
can show no difference, since that case has gone both ways at one
configuration in the runs above. No brief carried a gate run, and each
forbade the gates, so no reviewer had a gate run to judge by the change.
The run shows that the change costs no hit and adds no blocking finding
on these cases, not that it finds anything.

## Cases

### PR btclib-org/ai-agents-process#317

- base `8bd39f62775846b6cdd4f2bd822ae6a528aae088`
- head `ed94e501019cbe2d6b0d55e3081c4fe44629fef8`
- defect: the branch adds a session hold to `process/btclib-common.md`'s
  *A pull request's rounds* and rewrites the next sentence to "None of
  this applies to the resumed run of a fresh reviewer…", which exempts
  that run from the hold too.
- found by CodeRabbit on GitHub after the dedicated reviewer's
  `CLEARED`, in review comment `4498549481` on [the pull
  request](https://github.com/btclib-org/ai-agents-process/pull/317),
  and fixed in `a290019`. `REVIEWING.md` on `main` describes this
  defect, and the copy at the head does not (*What a case holds*).

### PR btclib-org/btclib-secp256k1#1331

- base `fe7b181be790dc2c57a48b7281bc9de1ecbc1d29`
- head `d6e660ec2c9e1841af00e29646359b60082871d4`
- defect: `.github/workflows/upstream-tests.yml` reads Valgrind's exit
  `42`, set by `--error-exitcode=42`, as a secret reaching a branch,
  where Valgrind gives that exit for every memcheck error, an invalid
  read included.
- found by CodeRabbit on GitHub after the dedicated reviewer's
  `CLEARED`, in review comment `4493105492` on [the pull
  request](https://github.com/btclib-org/btclib-secp256k1/pull/1331),
  and fixed in `49102ac`.

### PR btclib-org/ecc#484

- base `1a81844a361f2c60c55441c7c82589cbd14fb8f8`
- head `35f495ff1989dc7d0a7540ad2ab0fd370fb2369f`
- defect: the search `REVIEWING.md` adds,
  `git ls-files -z | xargs -0 perl -0777 -ne …`, opens each file name
  with perl's two-argument `open`, so a tracked name ending in `|` runs
  as a shell command and one starting with `-` is read as a switch.
- found by CodeRabbit on GitHub after the dedicated reviewer's
  `CLEARED`, in review comment `4503224613` on [the pull
  request](https://github.com/btclib-org/ecc/pull/484), and fixed in
  `2545806`.

### PR btclib-org/ai-agents-process#444

- base `d765a161be9100de22248de72f22d6c9cae17c19`
- head `709efef082c5f81d0fdf775633317699aa0fc1be`
- defect: the port makes `CONTRIBUTING.md` and `REPOSITORY.md` say
  auto-merge is off and no pull request can be armed, while
  `skills/btclib-pr/SKILL.md`, in its sections *Arming auto-merge* and
  *Landing*, `skills/btclib-iss/SKILL.md` and `process/btclib-common.md`
  at that head still tell a session to arm it, as
  `git grep -c -i -E 'auto-merge|--auto' 709efef -- skills process`
  shows in each of the three.
- found by the runs at `2ef0de4` and `466d803` (*Runs*), and fixed on
  `main` in `7f7de67`.

### PR btclib-org/.github#2288

- base `4e68136bb12ffdf1bdd21a86479b1c921668848b`
- head `dfcc9c4262bd9a94cb2bb4f9669052aacb7d1163`
- defect: the docstring the branch adds to
  `.github/scripts/bestpractices.py` says "draft" after "not a" is not
  listed, while `UNDATED`'s lookbehind is the literal "not a ", so a
  line break, a tab or a second space between the words still gets it
  listed.
- found by each run of the replay of 2026-11-15 at `e91f4c3` and
  `9c5ada8` (*Runs*), and measured again by the orchestrator; not fixed
  on `main` (ISS btclib-org/.github#2327).
- measured clean on 2026-11-15, before that run, as *What a case holds*
  asks: the forge's reviews of the head it landed on read no finding,
  and two fresh reviewers at `$PROCESS` `aa5dcdc` each cleared it. One
  of them raised two non-blocking findings and a nit, none a defect: the
  first asks whether ISS btclib-org/.github#2278 is fully answered, and
  it is, since that issue's *Done when* asks that `--stale` list no
  justification for "not a draft" alone; the rest is wording.

### PR btclib-org/btclib-node#2516

- base `aa973d9c6bb93858776350e25e7f19bd1e991da3`
- head `6415350199171c1cbe9ae4da00e22ba0bd289569`
- defect: the docstring the branch adds to `_assert_ends_at` in
  `src/btclib_node/p2p/raw_block.py` says "`i` sums the length fields
  the walk read", where `i` is the offset at which the walk ends, which
  also counts the header and the fixed-width fields.
- found on 2026-11-15 by one of two fresh reviewers reading it as a
  clean candidate, as a non-blocking finding in its `CLEARED`, after the
  local Codex reviewer's `CLEARED`, the review bot's `ACK`, Codex's
  state with no finding and CodeRabbit's passed check (ISS
  btclib-org/btclib-node#2526); not fixed on `main` at `ae099c4`.

### PR btclib-org/ecc#580

- base `d1ddc9b17aabcc64bbb6898748d81c61005662bc`
- head `186d8b6de3bc88944a3d4b1357c44d6a2542b396`
- defect: the comment the branch adds over `_AFF_CALLS` in
  `tests/curves/curve_group_test.py` says the list holds "each public
  method of CurveGroup taking an affine point", where it leaves out
  `add_var`, `require_on_curve` and `is_on_curve`.
- found on 2026-11-15 by one of two fresh reviewers reading it as a
  clean candidate, after the local Codex reviewer's `CLEARED`, the
  review bot's `ACK`, Codex's state with no finding and CodeRabbit's
  passed check (ISS btclib-org/ecc#583); not fixed on `main` at
  `5546cf0`.

### PR btclib-org/ai-agents-process#522

- base `dfa8ed07dfe568750d579bf92b136d34e6b2b4a2`
- head `c20a251ea8d041dd3fac65c222d837cf01513506`
- clean: the case is the head that landed, on which no review names a
  defect that holds.
- measured clean on 2026-11-16, as *What a case holds* asks: on that
  head the review bot, Codex and CodeRabbit read `ack`, both reads print
  `0`, and CodeRabbit's review body is empty. Fresh reviewers at
  `$PROCESS` `58a8649` each cleared it, with no finding a defect. Two
  were briefed as for a run and read the head's copy of this file, for
  which the check of *A case's tree can hold this file* prints
  `unnamed`; the briefs of the other two also named this file, to forbid
  reading it. Each says "The skill" in `process/night-mode.md` could
  name its file, and three find "in place of every rule" in the commit
  message hard to read. One also asks that the skill's sentence on a
  lost context say it covers only the command with no word, and whether
  a model may call the skill with no word.
- the local rounds of its branch made two findings, neither a defect of
  the head. The local Codex reviewer blocked on `21418e3`, an earlier
  commit never pushed, whose diff moved rules into the skill and left
  its pointer "The rules are all in `$PROCESS/process/night-mode.md`";
  it cleared the head, which rewrites the pointer. The CodeRabbit CLI
  found that `/night-mode --night` meets both `process/night-mode.md`'s
  `--night` clause and the skill's sentence on any other word. The pull
  request's body declined it, since the skill is the more specific text
  (`every-role.md`'s *Which file wins*), and the base's two files meet
  the same way.

### PR btclib-org/ai-agents-process#526

- base `dfa8ed07dfe568750d579bf92b136d34e6b2b4a2`
- head `062425cf6ddc1019a6ac8ef46ff5f7f405606a73`
- defect: `obligations()` in `scripts/port-check.py` joins each line
  that starts with two spaces to the bullet before it, so a list item
  indented two spaces after a paragraph that closes section 14's list is
  never compared, and the check can exit `0` on a tree that lacks that
  copy, though the docstring the branch adds says a list item that is
  not a dash bullet raises.
- found on 2026-11-16 by both fresh reviewers reading it as a clean
  candidate at `$PROCESS` `58a8649`, as the blocking finding of each
  `CHANGES REQUESTED`, after the local Codex reviewer's `CLEARED`, the
  CodeRabbit CLI's read with no finding, the review bot's `ACK`, Codex's
  state with no finding and CodeRabbit's approval (ISS
  btclib-org/ai-agents-process#535); not fixed on `main` at `3af75db`.
  Neither `REVIEWING.md`, at the head and on `main`, nor the reviewers'
  copy of `process/` describes this defect (*What a case holds*).
