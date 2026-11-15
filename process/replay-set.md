# The replay set

The pull requests a change to the local reviewer is tried on before it
lands: those where the local rounds cleared a defect that a later review
found, and clean ones, where no review found any.

**A change to the reviewer's brief, its model or its effort is run on
every case here first**, and its pull request adds the run to *Runs* and
names it in `## Evidence`. The brief's part this repository holds is
`btclib-common.md`'s *Local review*, `agents/reviewer.md` with its
generated `.toml`, and this tree's `REVIEWING.md`; another tree's
`REVIEWING.md` and the review bot's prompt, which the brief also
carries, change in their own trees. The model and the effort are those
`btclib-common.md`'s *Models* gives. Without the run, such a change is
judged on the next pull requests, whose defects nobody knows in advance.

## What a case holds

- the repository, and the base and head shas of the commit the miss was
  made on, frozen before the fix;
- for a defect, the defect in one sentence, and where it was found
  later;
- for a clean change, how it was measured clean.

**The expected finding is kept out of the reviewer's input.** The run
briefs a fresh reviewer of the head, as `btclib-common.md`'s *A pull
request's rounds* says, with the head's commit message standing for the
pull request. Its brief names neither this file nor anything posted
after the head, since both state the defect. A run whose verdict's
coverage list names this file is discarded and run again. The process it
is briefed with is the configuration under test, at the `$PROCESS` sha
the run records. The reviewer reads the prose at the head itself, not on
the merge with `origin/main` that *A pull request's rounds* asks for,
since `main` has moved past the case, a defect's fix included.

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
defects, and where it does not, it is a false finding.

## How a run is scored

**A hit names the defect's mechanism and its consequence** well enough
to fix it, as *The findings record* in `btclib-common.md` matches two
findings. The orchestrator scores each verdict against the case's
sentence, and the human scores where it cannot tell. The cases are
chosen, not drawn at random, so a run says how a configuration did on
them and not how often it finds a defect.

**One factor at a time.** A run changes one thing from the baseline,
the brief, the model or the effort, and is compared with the
baseline's run on the same cases. One configuration can answer
differently on two runs, so a case that alone decides the comparison is
run again first.

## Runs

Each run is an entry: the date, the `$PROCESS` sha, the factor changed
and its value, the client, the model and the effort, a hit or a miss for
each defect, and each false finding on any case apart.

The change that creates this set records no run. Its baseline is
[ISS ai-agents-process#456](https://github.com/btclib-org/ai-agents-process/issues/456),
and the rule above binds from the next change to the brief, the model
or the effort.

## Cases

### PR btclib-org/ai-agents-process#317

- base `8bd39f62775846b6cdd4f2bd822ae6a528aae088`
- head `ed94e501019cbe2d6b0d55e3081c4fe44629fef8`
- defect: the branch adds a session hold to `process/btclib-common.md`'s
  *A pull request's rounds* and rewrites the next sentence to "None of
  this applies to the resumed run of a fresh reviewer…", which exempts
  that run from the hold too.
- found by CodeRabbit on GitHub after the dedicated reviewer's
  `CLEARED`
  ([thread](https://github.com/btclib-org/ai-agents-process/pull/317#discussion_r4498549481)),
  and fixed in `a290019`. `REVIEWING.md` on `main` cites the case, so the
  run reads that file at the case's head.

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

### PR btclib-org/ai-agents-process#444, clean

- base `d765a161be9100de22248de72f22d6c9cae17c19`
- head `709efef082c5f81d0fdf775633317699aa0fc1be`
- clean: it landed on that head, where the review bot's `ACK` names it,
  Codex's state reads no finding, and CodeRabbit's check passed with no
  thread, each read as `/btclib-pr`'s *The reviews on GitHub* reads
  them.
