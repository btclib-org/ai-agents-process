# The replay set

The pull requests a change to the local reviewer is tried on before it
lands: those where the local rounds cleared a defect that a later review
found, and clean ones, where no review found any.

**A change to the reviewer's brief, its model or its effort is run on
every case here first**, and its pull request adds the run to *Runs* and
names it in `## Evidence`. The brief's part this repository holds is
`local-review.md`'s *Local review*, `agents/reviewer.md` with its
generated `.toml`, and this tree's `REVIEWING.md`; another tree's
`REVIEWING.md` and the review bot's prompt, which the brief also
carries, change in their own trees. The model and the effort are those
`orchestration.md`'s *Models* gives. Without the run, such a change is
judged on the next pull requests, whose defects nobody knows in advance.

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
after the head, since both state the defect. A run whose verdict's
coverage list names this file is discarded and run again. The process it
is briefed with is the configuration under test, at the `$PROCESS` sha
the run records. The reviewer reads the prose at the head itself, not on
the merge with `origin/main` that *A pull request's rounds* asks for,
since `main` has moved past the case, a defect's fix included. Where the
run changes this tree's `REVIEWING.md`, a reviewer of this repository's
cases reads the changed file in place of the head's, without the
sentences that describe a case's defect, such as PR
btclib-org/ai-agents-process#317's in its *This repository in
particular*. The run records what it withheld. Where the change under
test rewrites such a sentence, its case is recorded as unable to
evaluate the change, beside a case that tests the instruction without
stating its answer, where one is needed.

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
makes the reviewer raise more shows as false findings. A finding a run
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
The second counts the lines of CodeRabbit's review bodies that mark a
finding, which *The reviews on GitHub* does not read while ISS
btclib-org/ai-agents-process#489 is open; it goes once that section
reads them. A failed read prints `read-failed` or counts it, and any
answer other than `0` is not clean.

## How a run is scored

**A hit names the defect's mechanism and its consequence** well enough
to fix it, as *The findings record* in `local-review.md` matches two
findings. The orchestrator scores each verdict against the case's
sentence, and the human scores where it cannot tell. The cases are
chosen, not drawn at random, so a run says how a configuration did on
them and not how often it finds a defect.

**One factor at a time.** A run changes one thing from the baseline,
the brief, the model or the effort, and is compared with the
baseline's run on the same cases. One configuration can answer
differently on two runs, so a case that alone decides the comparison is
run again first. A run that changes the brief is compared with a
baseline at the commit before the change under test's first commit, so
that only that change differs, and the baseline's entry names that sha.

## Runs

Each run is an entry: the date, the `$PROCESS` sha, the factor changed
and its value, the client, the model and the effort, a hit or a miss for
each defect, and each false finding on any case apart.

- **Baseline**, 2026-11-15: `$PROCESS` `2ef0de4`, no factor changed;
  Claude Code, the `reviewer` agent, Opus, effort `high`. PR
  btclib-org/ai-agents-process#317: miss. PR
  btclib-org/btclib-secp256k1#1331: miss. PR btclib-org/ecc#484: hit.
  PR btclib-org/ai-agents-process#444, clean when run: one finding,
  which holds and moved the case to the defects.
- **Candidate**, 2026-11-15: `$PROCESS` `466d803`, the factor changed
  being the brief: *Local review*'s round rules of ISS
  btclib-org/ai-agents-process#461 and ISS
  btclib-org/ai-agents-process#464. The same client, model and effort.
  The same four results: miss, miss, hit, and the same finding on the
  last. The change neither loses a hit nor adds a false finding on
  these cases.

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
  btclib-org/btclib-secp256k1#1331: miss, then miss on the repeat *How a
  run is scored* asks for. PR btclib-org/ecc#484: hit. PR
  btclib-org/ai-agents-process#444: hit.
- **Candidate**, 2026-11-15: `$PROCESS` `1ddae0d`, the factor changed
  being the brief's files of ISS btclib-org/ai-agents-process#447: the
  reviewer reads `every-session.md`, `every-role.md`, `local-review.md`
  and the sections of `writing.md` the map names, in place of
  `btclib-common.md` whole. The same client, model and effort. PR
  btclib-org/ai-agents-process#317: miss. PR
  btclib-org/btclib-secp256k1#1331: hit, named as non-blocking in a
  `CLEARED`: a call recorded as `reported` passes on any Valgrind error,
  whatever caused the exit `42`; then miss on the repeat *How a run is
  scored* asks for. PR btclib-org/ecc#484: hit. PR
  btclib-org/ai-agents-process#444: hit.
- **Candidate**, 2026-11-15: `$PROCESS` `2166200`, whose process files,
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
that case cannot evaluate the edit. The run at `1ddae0d` loses no hit,
and its hit on PR btclib-org/btclib-secp256k1#1331 did not repeat. With
the whole brief under test, the run at `2166200` matches the baseline at
`aa5dcdc` on every case, so the change loses no hit on these cases and
shows no gain.

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
- clean, as *What a case holds* measures it, on 2026-11-15: the forge's
  reviews of the head it landed on read no finding, and two fresh
  reviewers at `$PROCESS` `aa5dcdc` each cleared it. One of them raised
  two non-blocking findings and a nit, none a defect: the first asks
  whether ISS btclib-org/.github#2278 is fully answered, and it is,
  since that issue's *Done when* asks that `--stale` list no
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
