# The replay set

The pull requests a change to the local reviewer is tried on before it
lands: those where the local rounds cleared a defect that a later review
found. A clean one, where no review found any, belongs there too (*What
a case holds*).

**A change to the reviewer's model, its effort or its tools, or a
change to the files of its brief that adds, alters or removes a rule it
applies in judging a branch, is run on every case here first**, and its
pull request adds the run to *Runs* and names it in `## Evidence`. The
model and the effort are those `orchestration.md`'s *Models* gives. The
tools are those the `tools` key of `agents/reviewer.md`'s frontmatter
gives a Claude Code reviewer; the generated `.toml` carries no such key.
The brief's part this repository holds is the files and sections
`every-role.md`'s map gives the reviewer under *Everybody* and
*The reviewer*, the reviewer's sections of the skill the brief names,
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
it was added from, and one of those may hold the fix. A run whose
verdict's coverage list names this file is discarded and run again. The
process it is briefed with is the configuration under test, at the
`$PROCESS` sha the run records. The reviewer reads that process from a
copy that leaves this file out, so the discard of a run whose coverage
list names this file is the backstop, not the only guard. The reviewer
reads the prose at the head itself, not on the merge with `origin/main`
that *A pull request's rounds* asks for, since `main` has moved past the
case, a defect's fix included. Where the run changes this tree's
`REVIEWING.md`, a reviewer of this repository's cases reads the changed
file in place of the head's, without the sentences that describe a
case's defect, such as PR btclib-org/ai-agents-process#317's in its
*This repository in particular*. The run records what it withheld. Where
the change under test rewrites such a sentence, its case is recorded as
unable to evaluate the change, beside a case that tests the instruction
without stating its answer, where one is needed.

The case's tree is built at a new path from a checkout that holds the
head, named by its path, so that the fetch needs no network and the
tree keeps no remote. The first command refuses a path that exists,
since `git init` keeps the objects of a repository already there, and a
refusal there stops the build. The fetch runs in the tree, so it makes
the checkout's path absolute first: a relative one would be read from
the tree. The three values are set first:

```shell
tree=<tree>
checkout=<checkout>
head=<head>
```

```shell
[ ! -e "${tree:?}" ] && git init "$tree"
```

```shell
src=$(realpath "${checkout:?}") &&
  git -C "${tree:?}" fetch "$src" "${head:?}"
```

```shell
git -C "${tree:?}" checkout --detach FETCH_HEAD
```

This prints `isolated` only where each read succeeds, the tree has no
remote, it has a `HEAD`, and every commit its refs reach is the head or
one of its ancestors:

```shell
remotes=$(git -C "${tree:?}" remote) &&
  all=$(git -C "$tree" rev-list --all) &&
  ancestry=$(git -C "$tree" rev-list HEAD) &&
  [ -z "$remotes" ] && [ -n "$ancestry" ] && [ "$all" = "$ancestry" ] &&
  echo isolated
```

The tree goes once the run is recorded in *Runs*, since the sweep of
`every-role.md`'s *Debris goes when its work ends* reads no repository it
cannot tell is a linked worktree of the session's:

```shell
tree=<tree>
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

A forge finding gives a case its head, the commit its thread names, and
the head gives its base, the merge base with `main`:

```shell
gh api repos/<owner>/<repo>/pulls/comments/<comment id> \
  --jq .original_commit_id
```

```shell
gh api repos/<owner>/<repo>/compare/main...<head> \
  --jq .merge_base_commit.sha
```

**A clean change belongs in the set too**, so that a change which only
makes the reviewer raise more shows as false findings. The set holds
none while ISS btclib-org/ai-agents-process#516 is open. A finding a run
makes on one is re-measured: where it holds, the case moves to the
defects, and where it does not, it is a false finding. A pull request
becomes a clean case where, on the head it landed on, the three
reviewers of `/btclib-pr`'s *The reviews on GitHub* read `ack`, both
reads below print `0`, two fresh reviewers, briefed as for a run, each
clear it, and no review names a defect in it that holds: a false
sentence is one, wording that could only be better is not.

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
to fix it, as *The findings record* in `local-review.md` matches two
findings. A defect a run names only in a non-blocking finding is a miss.
The orchestrator scores each verdict against the case's sentence, and
the human scores where it cannot tell. The cases are chosen, not drawn
at random, so a run says how a configuration did on them and not how
often it finds a defect.

**One factor at a time.** A run changes one thing from the baseline,
the brief, the model, the effort or the tools, and is compared with the
baseline's run on the same cases. One configuration can answer
differently on two runs, so a case that alone decides the comparison is
run again first. A run that changes the brief is compared with a
baseline at the commit before the change under test's first commit, so
that only that change differs, and the baseline's entry names that sha.

## Runs

Each run is an entry: the date, the `$PROCESS` sha, the factor changed
and its value, the client, the model and the effort, a hit or a miss for
each defect, and each false finding on any case apart.

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
  the brief: *Local review*'s round rules of ISS
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
no hit and gains none. What it adds to the reviewer's reading, *The
gates*, *Sourcery and CodeRabbit before a push* and *Committing and
rebasing*, bears on checks no case of the set exercises.

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
  *Local review*'s new *A text to be posted* among them. Claude Code,
  the `reviewer` agent, Opus, effort `high`, one run per case. It is
  compared with the baseline at `53b7a57` above on all seven cases: the
  candidate's base, `e029de3`, differs from `53b7a57` only in
  `process/orchestration.md`, which no brief of this run had the
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

## Cases

### PR btclib-org/ai-agents-process#317

- base `8bd39f62775846b6cdd4f2bd822ae6a528aae088`
- head `ed94e501019cbe2d6b0d55e3081c4fe44629fef8`
- defect: the branch adds a session hold to `process/btclib-common.md`'s
  *A pull request's rounds* and rewrites the next sentence to "None of
  this applies to the resumed run of a fresh reviewer…", which exempts
  that run from the hold too.
- found by CodeRabbit on GitHub after the dedicated reviewer's `CLEARED`
  ([thread](https://github.com/btclib-org/ai-agents-process/pull/317#discussion_r4498549481)),
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
  `CLEARED`
  ([thread](https://github.com/btclib-org/btclib-secp256k1/pull/1331#discussion_r4493105492)),
  and fixed in `49102ac`.

### PR btclib-org/ecc#484

- base `1a81844a361f2c60c55441c7c82589cbd14fb8f8`
- head `35f495ff1989dc7d0a7540ad2ab0fd370fb2369f`
- defect: the search `REVIEWING.md` adds,
  `git ls-files -z | xargs -0 perl -0777 -ne …`, opens each file name
  with perl's two-argument `open`, so a tracked name ending in `|` runs
  as a shell command and one starting with `-` is read as a switch.
- found by CodeRabbit on GitHub after the dedicated reviewer's
  `CLEARED`
  ([thread](https://github.com/btclib-org/ecc/pull/484#discussion_r4503224613)),
  and fixed in `2545806`.

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
