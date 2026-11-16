#!/bin/sh
# What scripts/sweep.sh removes and refuses, on fixture directories:
#
#   sh scripts/test-sweep.sh [<sweep.sh>]
#
# TEST_SWEEP_SHELLS, sh dash bash by default, names the shells to run the
# cases under, zsh aside.
#
# The fixtures sit in a temporary directory the test removes, one tree for
# each of sh, dash and bash that is on the PATH, and each case runs the
# script under that shell. A tree holds a directory that stands for
# /tmp/claude-<uid> (SWEEP_ROOT), a scratchpad in it, a bare repository
# as origin, and a clone of it whose worktrees sit in the scratchpad's
# <work> directories. A commit is made with git commit-tree on a stand-in
# identity, which does not sign unless asked, and the stand-in
# gpg.program makes a fixture that ever asks fail instead of
# reaching a real key. Each commit message names its case, so that no two
# cases make the same commit. Stand-ins for git and id, first on the PATH
# of the cases that need them, move a branch or fail a step at a set
# moment, log each git call, and make the caller another user: the test
# cannot make a directory that another user owns. No fixture holds a git
# config, hook or attribute that runs a program.
#
# The cases, each a <work> directory unless it says otherwise. Removed
# means removed, its worktrees deregistered and their branches deleted,
# but for a branch the case says is kept; refused means refused with its
# reason, nothing in it removed:
#
# - a clean worktree whose commit is on origin is removed;
# - with --check, the same is printed and nothing is written, the index of
#   a worktree whose file's time changed included;
# - a worktree with a modified file, an untracked file that is not
#   ignored, or a modified file marked assume-unchanged or skip-worktree,
#   is refused; one with an ignored file is removed;
# - a worktree with an unpushed commit is refused, and its branch kept;
# - one whose commit only a branch head, a pull request head or a tag of
#   origin holds, and no remote-tracking ref reaches, is removed;
# - one whose commit only a remote-tracking ref reaches, the branch being
#   gone from origin, is refused; so is one whose origin cannot be read;
# - a worktree with a ref to a tree is refused, and so is one whose commit
#   only refs/worktree/keep holds;
# - a directory not directly under <root>/<project>/<session>/scratchpad,
#   deeper or shallower, a scratchpad outside SWEEP_ROOT, and the
#   scratchpad itself are refused;
# - a symbolic link to a directory in another scratchpad is refused,
#   written with a trailing slash too, and a path with a . or ..
#   component is refused; so is a directory reached through a scratchpad
#   that is a link to one outside; one reached through a link to
#   SWEEP_ROOT is removed;
# - where SWEEP_ROOT does not exist, or another user owns it, a directory
#   is refused;
# - a regular file is refused as no directory;
# - after a refused directory, the next one named is still removed;
# - the caller's current directory, and a directory holding it, are
#   refused, and so is the scratchpad's orchestrator; where the file system
#   ignores letter case, or Unicode normalization, the same directories
#   named in another case or form are refused too, and a work directory
#   named through SCRATCHPAD is removed;
# - a name with a space is removed, and so is a work directory holding a
#   read-only directory;
# - a path that does not exist is absent, and exits 0;
# - a name with a newline or \001 inside, a worktree's included, under
#   --check and in the run, a directory whose path above it holds \001,
#   and a directory find cannot read are refused; where find still reads
#   a directory of mode 000, as for uid 0, the unreadable directory case
#   is skipped and the test says so;
# - a directory holding a repository that is not a linked worktree of the
#   session's is refused, left as it was, and no git runs, under --check
#   or in the run: a clone, a .git deeper than <work>/<e>, a clone inside
#   an ignored directory of a worktree, a submodule's .git file there, a
#   bare repository, one whose HEAD is a symbolic link, a HEAD beside a
#   commondir file, a clone whose .git file names a git directory inside
#   the directory or one outside that is no worktrees entry, a worktree's
#   .git that is a symbolic link, a .git whose gitdir does not resolve,
#   one whose git directory's commondir names another repository, a
#   worktree moved by hand, which its repository does not name, a work
#   directory that is itself a worktree, and one whose top holds an empty
#   .git, or a HEAD beside objects and refs; so are a .git file with a
#   second hard link and a .git that is a FIFO; where the file system
#   ignores letter case, so are a clone in a worktree whose .git and HEAD
#   are spelled .GIT and Head, a gitlink's .GIT file naming a git
#   directory whose HEAD is spelled head, and a bare repository whose
#   HEAD is spelled Head, and a file system that keeps case skips them
#   and says so;
# - a directory holding a lone file named HEAD, notes alone, or a
#   reviewer's directory without a repository is removed, and no git
#   runs; one holding two worktrees is removed with both;
# - a work directory holding .sweep-unfinished as a file, a symbolic
#   link, a dangling one, whose target is not created, or a directory, is
#   refused;
# - where origin has moved on to a commit the repository has not fetched,
#   a commit it reaches is refused, with fetch named, and removed once
#   origin is fetched;
# - where the pull request's head on origin is a child of the worktree's
#   pushed commit, and its branch was squashed and deleted, the directory
#   is refused after a fetch of origin and removed after a fetch of the
#   head;
# - with the session's directory spelled Orchestrator, where the file
#   system ignores case, the name orchestrator is refused;
# - for each case a run decides, --check exits as the run does, except
#   where a stand-in fails a step only the run takes;
# - a directory holding a findings record, findings-*.md, at its top or
#   below, is refused; once the lines of process/every-role.md that move
#   the records have run, given <work> with a trailing slash, it is removed
#   and the record kept in the orchestrator's directory; where a record of
#   that name is there already, both are kept and the directory is refused;
#   an orphan worktree with no commit, in a repository with no remote named
#   origin, is removed, and --check names no branch to delete (where git
#   worktree add --orphan works; otherwise the test says it skipped it); a
#   worktree whose git directory holds modules is refused by --check and by
#   the run, and so is one whose repository has no remote named origin,
#   where a bundle named origin in the worktree lists its commit;
# - a detached worktree whose commit is on origin is removed, no branch
#   is deleted, and neither --check nor the run names a branch;
# - a worktree whose HEAD is a symbolic ref to a tag is refused, and the
#   tag kept;
# - a worktree whose gitlink path is a symbolic link is refused by
#   --check and by the run, as git worktree remove would refuse it,
#   whether git status fails on it or reports a change, which it does
#   on git 2.43, and leaves no .sweep-unfinished; where the file system
#   ignores letter case, a worktree its repository lists under .GIT is
#   refused;
# - a worktree whose index or HEAD git cannot read, and one whose
#   commit's parent is missing, are refused;
# - a locked worktree is refused by --check and by a run, and the other
#   worktree of its directory stays registered;
# - a branch whose tip moves before its deletion is kept and printed, and
#   the directory is removed;
# - where a worktree is switched with --ignore-other-worktrees to main,
#   which the repository's own checkout has checked out, main is kept and
#   printed as kept, --check prints what the run does, line for line, and
#   the directory is removed;
# - where two worktrees of the directory have one branch checked out, the
#   branch is deleted once, --check prints what the run does, line for
#   line, and the directory is removed;
# - where a worktree outside the directory has the branch checked out, and
#   its path holds a newline followed by a line naming the removed
#   worktree, the branch is kept and printed with ? for the newline,
#   --check prints what the run does, line for line, and the directory is
#   removed;
# - where a worktree outside the directory has the branch checked out at
#   a path holding a newline, and a symbolic link at that path with \001
#   for the newline leads to the removed worktree, the branch is kept,
#   --check prints what the run does, line for line, and the directory is
#   removed;
# - where a second worktree of the directory, whose .git file is gone,
#   has the branch checked out, the branch is kept and printed naming it,
#   --check prints what the run does, line for line, and the directory is
#   removed;
# - where two directories named in one run each hold a worktree on one
#   branch, the first keeps the branch, the second deletes it, and
#   --check prints what the run does, line for line;
# - where git worktree remove fails on the third worktree of the
#   directory, the branches of the first two stay and the refusal names
#   them, the directory is refused and keeps .sweep-unfinished, and the
#   next run refuses it;
# - where rm cannot remove a file, the directory is refused (only where
#   chflags exists and sets uchg; where it refuses, the case is skipped
#   and the test says so);
# - with GIT_DIR set to another repository, a clean directory is still
#   removed and that repository is left as it was;
# - an unknown mode, an unknown option and no directory exit 2 with the
#   usage;
# - after the cases, no repository holds a stale worktree entry;
# - under an interactive zsh, where present, the two lines of
#   process/every-role.md's *Debris goes when its work ends*, with a path
#   for <work>, remove its directory;
# - under each shell, the lines of that section that look up a worktree's
#   pull requests, run with a stand-in for gh, ask for the branch
#   topic;>MARKER by that name and write nothing, and run no gh for a
#   detached worktree.

# a git variable the caller sets, as a hook run by git commit inherits,
# would send the fixtures' git writes to the caller's repository
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_COMMON_DIR CDPATH
unset GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_NAMESPACE
script=${1:-$(dirname "$0")/sweep.sh}
script=$(cd -P "$(dirname "$script")" && pwd -P)/${script##*/}
[ -f "$script" ] || { echo "FAIL: no script $script"; exit 1; }
tmp=$(mktemp -d "${TMPDIR:-/tmp}/test-sweep.XXXXXX") || exit 1
readable='' noflag='' noorphan='' casefold=1
# the fixtures include an unreadable directory and, with chflags, an
# immutable file, which a plain rm -rf cannot remove; the EXIT trap calls
# it
# shellcheck disable=SC2329
cleanup() {
  command -v chflags > /dev/null && chflags -R nouchg "${tmp:?}" 2> /dev/null
  chmod -R u+rwx "${tmp:?}" 2> /dev/null
  rm -rf "${tmp:?}"
}
trap cleanup EXIT
trap 'exit 1' INT TERM
tmp=$(cd -P "$tmp" && pwd -P)
printf '#!/bin/sh\nexit 1\n' > "$tmp/gpg"
chmod +x "$tmp/gpg"
GIT_AUTHOR_NAME=Fixture GIT_AUTHOR_EMAIL=fixture@example.invalid
GIT_COMMITTER_NAME=Fixture GIT_COMMITTER_EMAIL=fixture@example.invalid
GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=gpg.program GIT_CONFIG_VALUE_0=$tmp/gpg
export GIT_AUTHOR_NAME GIT_AUTHOR_EMAIL GIT_COMMITTER_NAME GIT_COMMITTER_EMAIL
export GIT_CONFIG_COUNT GIT_CONFIG_KEY_0 GIT_CONFIG_VALUE_0
status=0

# the lines of process/every-role.md's *Debris goes when its work ends*
# that move the findings records, run after work=$1, with <work> as their
# first argument; the $1 in quotes is the text those lines get
prose=$(cd -P "$(dirname "$0")/.." && pwd -P)/process/every-role.md
# shellcheck disable=SC2016
movecmd='work=$1
'$(awk '
  /^  ```shell$/ { b = ""; on = 1; next }
  /^  ```$/ { if (on && b ~ /findings-/) printf "%s", b; on = 0; next }
  on { sub(/^  /, ""); b = b $0 "\n" }' "$prose")
# and the line that fetches a pull request's head, with <checkout> and
# <n> as its first and second arguments
# shellcheck disable=SC2016
pullcmd=$(awk '
  /^  ```shell$/ { b = ""; on = 1; next }
  /^  ```$/ { if (on && b ~ /refs\/pull\//) printf "%s", b; on = 0; next }
  on { sub(/^  /, ""); b = b $0 "\n" }' "$prose" |
  sed 's/<checkout>/"$1"/; s/<n>/$2/')
# shellcheck disable=SC2016
case $pullcmd in
  *'"$1"'*'$2'*) ;;
  *)
    echo "FAIL: no line that fetches a pull request's head in $prose"
    exit 1
    ;;
esac
# and the lines that look up a worktree's pull requests, with <wt> and
# <owner>/<repo> as their first and second arguments
# shellcheck disable=SC2016
lookcmd=$(awk '
  /^  ```shell$/ { b = ""; on = 1; next }
  /^  ```$/ {
    if (on && (b ~ /^wt=<wt>/ || b ~ /gh pr list/)) printf "%s", b
    on = 0
    next
  }
  on { sub(/^  /, ""); b = b $0 "\n" }' "$prose" |
  sed 's/^wt=<wt>$/wt=$1/; s|^repo=<owner>/<repo>$|repo=$2|')
# shellcheck disable=SC2016
case $lookcmd in
  'wt=$1'*'repo=$2'*'gh pr list'*) ;;
  *)
    echo "FAIL: no lines that look up a worktree's pull requests in $prose"
    exit 1
    ;;
esac
case $movecmd in
  *'findings-'*) ;;
  *) echo "FAIL: no lines that move the findings records in $prose"; exit 1 ;;
esac

# The stand-in for git. Before `update-ref -d` it moves $SHIM_MOVE_REF of
# $SHIM_GIT_DIR to $SHIM_MOVE_TO; at `worktree remove` of $SHIM_FAIL, it
# removes that worktree's .git file and fails.
REAL_GIT=$(command -v git)
export REAL_GIT
mkdir "$tmp/git-shim" "$tmp/id-shim" "$tmp/gh-shim"
# the stand-in for gh writes its arguments to $GHLOG, one per line
cat > "$tmp/gh-shim/gh" << 'EOF'
#!/bin/sh
printf '%s\n' "$@" > "$GHLOG"
EOF
chmod +x "$tmp/gh-shim/gh"
cat > "$tmp/git-shim/git" << 'EOF'
#!/bin/sh
case " $* " in
  *" update-ref -d "*)
    if [ -n "${SHIM_MOVE_REF:-}" ]; then
      "$REAL_GIT" --git-dir="$SHIM_GIT_DIR" update-ref "$SHIM_MOVE_REF" \
        "$SHIM_MOVE_TO"
    fi
    ;;
  *" worktree remove "*)
    for a; do last=$a; done
    if [ -n "${SHIM_FAIL:-}" ] && [ "$last" = "$SHIM_FAIL" ]; then
      rm -f "$last/.git"
      echo 'shim: worktree remove fails' >&2
      exit 1
    fi
    ;;
esac
exec "$REAL_GIT" "$@"
EOF
# The stand-in for git that logs each call, its working directory and its
# arguments, to $GITLOG, and runs git.
mkdir "$tmp/log-shim"
GITLOG=$tmp/git.log
export GITLOG
cat > "$tmp/log-shim/git" << 'EOF'
#!/bin/sh
printf '%s | %s\n' "$PWD" "$*" >> "$GITLOG"
exec "$REAL_GIT" "$@"
EOF
chmod +x "$tmp/log-shim/git"
# The stand-in for id, a caller that is another user.
cat > "$tmp/id-shim/id" << 'EOF'
#!/bin/sh
case $* in
  -u) echo 99999 ;;
  -un) echo other ;;
  *) exit 1 ;;
esac
EOF
chmod +x "$tmp/git-shim/git" "$tmp/id-shim/id"

fail() {
  printf 'FAIL (%s): %s\n' "$sh" "$*"
  status=1
}

# run <dir> <argument>...: the script, run by $sh from <dir> with
# SWEEP_ROOT=$sroot and PATH=$spath; its output in $out, its exit code in
# $rc. A run of `work` with directories is first made with --check, whose
# exit must be the run's, unless $nocheck is set, where a stand-in fails
# a step only the run takes.
run() {
  rdir=$1
  shift
  rcc=
  if [ "$1" = work ] && [ $# -gt 1 ] && [ "$2" != --check ] &&
    [ -z "${nocheck:-}" ]; then
    shift
    rcc=0
    outc=$(cd "$rdir" && SWEEP_ROOT=$sroot PATH=$spath \
      "$sh" "$script" work --check "$@" 2>&1) || rcc=$?
    set -- work "$@"
  fi
  rc=0
  out=$(cd "$rdir" && SWEEP_ROOT=$sroot PATH=$spath \
    "$sh" "$script" "$@" 2>&1) || rc=$?
  if [ -n "$rcc" ] && [ "$rcc" != "$rc" ]; then
    fail "$*: --check exits $rcc, the run $rc: $outc / $out"
  fi
}

# expect <case> <exit code> <text the output holds>
expect() {
  [ "$rc" = "$2" ] || fail "$1: exit $rc, not $2: $out"
  case $out in
    *"$3"*) ;;
    *) fail "$1: no '$3' in: $out" ;;
  esac
}

gone() { [ ! -e "$2" ] && [ ! -L "$2" ] || fail "$1: $2 is still there"; }

# foreign <case> <dir> <text>: <dir> is refused, with <text>, as holding a
# repository the script cannot tell is the session's; it is left as it
# was, and git ran nowhere, under --check or in the run
foreign() {
  : > "$GITLOG"
  names=$(find "$2" | sort | cksum)
  spath=$tmp/log-shim:$PATH
  run "$base" work "$2"
  spath=$PATH
  expect "$1" 1 "$3"
  expect "$1" 1 'the script reads no repository it cannot tell is a'
  [ "$(find "$2" | sort | cksum)" = "$names" ] || fail "$1: $2 changed"
  [ ! -s "$GITLOG" ] || fail "$1: git ran: $(cat "$GITLOG")"
}
kept() { [ -e "$2" ] || fail "$1: $2 was removed"; }

# same <case>: --check printed, line for line, what the run did
same() {
  want=$(printf '%s\n' "$out" | sed -e 's/^deregistered:/would deregister:/' \
    -e 's/^deleted branch:/would delete branch:/' \
    -e 's/^kept branch:/would keep branch:/' -e 's/^removed:/would remove:/')
  [ "$want" = "$outc" ] || fail "$1: --check printed: $outc / the run: $out"
}

# registered <case> yes|no <worktree>
registered() {
  if git -C "$m" worktree list --porcelain | grep -qxF "worktree $3"; then
    [ "$2" = yes ] || fail "$1: $3 is still a worktree of main"
  else
    [ "$2" = no ] || fail "$1: $3 is no worktree of main"
  fi
}

# branch <case> yes|no <branch>
branch() {
  if git -C "$m" rev-parse -q --verify "refs/heads/$3" > /dev/null; then
    [ "$2" = yes ] || fail "$1: branch $3 is still there"
  else
    [ "$2" = no ] || fail "$1: branch $3 was deleted"
  fi
}

# mkwork <repo> <name> [<worktree name>]: $sp/<name>, holding a note in
# writer/ and a worktree of <repo> on a new branch at origin/main; sets
# $w, $wt and $br
mkwork() {
  n=$((n + 1))
  w=$sp/$2 wt=$sp/$2/${3:-wt} br=b$n
  mkdir -p "$w/writer"
  echo note > "$w/writer/msg.txt"
  git -C "$1" worktree add -q -b "$br" "$wt" origin/main 2> /dev/null ||
    fail "mkwork $2"
}

# newcommit <dir> <message>: in $c, a commit on the HEAD of <dir>, with its
# tree; commit <dir> <message> moves HEAD to it
newcommit() {
  c=$(git -C "$1" commit-tree -p HEAD -m "$2" "$(git -C "$1" rev-parse \
    'HEAD^{tree}')" < /dev/null) || fail "commit $2"
}
commit() {
  newcommit "$@"
  git -C "$1" update-ref HEAD "$c" || fail "commit $2"
}

# lookup <case> <wt>: runs the lines that look up <wt>'s pull requests,
# under $sh, in an empty directory, with the stand-in for gh
lookup() {
  ldir=$tmp/lookup-dir
  rm -rf "$ldir" "$tmp/gh.log"
  mkdir "$ldir"
  rc=0
  if [ "$sh" = zsh ]; then
    (cd "$ldir" && PATH=$tmp/gh-shim:$PATH GHLOG=$tmp/gh.log \
      zsh -f -i -c "$lookcmd" zsh "$2" own/repo < /dev/null > /dev/null \
      2>&1) || rc=$?
  else
    (cd "$ldir" && PATH=$tmp/gh-shim:$PATH GHLOG=$tmp/gh.log \
      "$sh" -c "$lookcmd" sh "$2" own/repo > /dev/null 2>&1) || rc=$?
  fi
  [ "$rc" = 0 ] || fail "$1: the lookup exits $rc"
  [ -z "$(ls -A "$ldir")" ] || fail "$1: the lookup wrote $(ls -A "$ldir")"
  rm -rf "$ldir"
}

# lookups: a worktree on the branch topic;>MARKER is looked up by that
# name and nothing is written; a detached worktree is not looked up
lookups() {
  lw=$tmp/lookup-$sh
  git -C "$m" worktree add -q -b 'topic;>MARKER' "$lw/named" origin/main \
    2> /dev/null || fail 'lookup: no worktree'
  lookup 'lookup named' "$lw/named"
  [ "$(awk 'p { print; exit } $0 == "--head" { p = 1 }' "$tmp/gh.log" \
    2> /dev/null)" = 'topic;>MARKER' ] ||
    fail "lookup named ($sh): gh was not asked for the branch topic;>MARKER"
  [ "$(awk 'p { print; exit } $0 == "--repo" { p = 1 }' "$tmp/gh.log" \
    2> /dev/null)" = own/repo ] ||
    fail "lookup named ($sh): gh was not asked for own/repo"
  git -C "$m" worktree add -q --detach "$lw/detached" origin/main \
    2> /dev/null || fail 'lookup: no detached worktree'
  lookup 'lookup detached' "$lw/detached"
  [ ! -e "$tmp/gh.log" ] ||
    fail "lookup detached ($sh): gh was run for a worktree with no branch"
  git -C "$m" worktree remove "$lw/named"
  git -C "$m" worktree remove "$lw/detached"
  git -C "$m" branch -q -D 'topic;>MARKER'
  rm -rf "$lw" "$tmp/gh.log"
}

cases() {
  base=$tmp/$sh root=$base/root sp=$base/root/proj/sess/scratchpad n=0
  sroot=$root spath=$PATH
  mkdir -p "$sp" "$base/outside/scratchpad/w"
  o=$base/origin.git
  git init -q --bare -b main "$o"
  a=$(printf 'ignored.txt\nignored/\n' | git -C "$o" hash-object -w --stdin)
  f=$(printf 'text\n' | git -C "$o" hash-object -w --stdin)
  t=$(printf '100644 blob %s\t.gitignore\n100644 blob %s\tf.txt\n' "$a" "$f" |
    git -C "$o" mktree)
  c=$(git -C "$o" commit-tree -m init "$t" < /dev/null)
  git -C "$o" update-ref refs/heads/main "$c"
  git clone -q "$o" "$base/main"
  m=$base/main

  mkwork "$m" clean
  commit "$wt" clean
  git -C "$wt" push -q origin HEAD
  run "$base" work "$w"
  expect clean 0 "removed: $w"
  gone clean "$w"
  registered clean no "$wt"
  branch clean no "$br"

  mkwork "$m" check
  commit "$wt" check
  git -C "$wt" push -q origin HEAD
  touch -t 203001010000 "$wt/f.txt"
  index=$(git -C "$wt" rev-parse --path-format=absolute --git-path index)
  before=$(cksum < "$index")
  run "$base" work --check "$w"
  expect check 0 "would remove: $w"
  expect check 0 "would deregister: $wt"
  expect check 0 "would delete branch: refs/heads/$br"
  kept check "$wt/f.txt"
  registered check yes "$wt"
  branch check yes "$br"
  [ "$(cksum < "$index")" = "$before" ] || fail 'check: the index was written'
  gone check "$w/.sweep-unfinished"

  mkwork "$m" modified
  echo more >> "$wt/f.txt"
  run "$base" work "$w"
  expect modified 1 "uncommitted change or untracked file in $wt"
  kept modified "$wt/f.txt"
  registered modified yes "$wt"

  mkwork "$m" untracked
  echo new > "$wt/new.txt"
  run "$base" work "$w"
  expect untracked 1 "uncommitted change or untracked file in $wt"
  kept untracked "$wt/new.txt"

  for flag in assume-unchanged skip-worktree; do
    mkwork "$m" "$flag"
    git -C "$wt" update-index "--$flag" f.txt
    echo more >> "$wt/f.txt"
    [ -z "$(git -C "$wt" status --porcelain)" ] ||
      fail "$flag: git status shows the change"
    run "$base" work "$w"
    expect "$flag" 1 "a file marked assume-unchanged or skip-worktree in $wt"
    kept "$flag" "$wt/f.txt"
  done

  mkwork "$m" ignored
  echo new > "$wt/ignored.txt"
  run "$base" work "$w"
  expect ignored 0 "removed: $w"
  gone ignored "$w"
  registered ignored no "$wt"

  mkwork "$m" unpushed
  commit "$wt" unpushed
  unpushed=$w
  run "$base" work "$w"
  expect unpushed 1 "no ref of origin that this repository holds"
  kept unpushed "$wt/f.txt"
  registered unpushed yes "$wt"
  branch unpushed yes "$br"

  for ref in refs/heads/elsewhere refs/pull/7/head refs/tags/t; do
    mkwork "$m" "ref-${ref##*/}"
    commit "$wt" "$ref"
    # origin takes the ref by a fetch, and stale drops its branch in origin:
    # after a push to origin's path both setup checks failed on the forge's
    # runner, and Apple Git 2.54.0 leaves the clone's remote-tracking refs
    # untouched, so neither case depends on what that push does to them
    git -C "$o" fetch -q "$wt" "HEAD:$ref"
    [ -n "$(git -C "$wt" rev-list -n 1 HEAD --not --remotes)" ] ||
      fail "$ref: a remote-tracking ref reaches the commit"
    run "$base" work "$w"
    expect "$ref" 0 "removed: $w"
    gone "$ref" "$w"
    registered "$ref" no "$wt"
  done

  mkwork "$m" stale
  commit "$wt" stale
  git -C "$wt" push -q origin HEAD
  git -C "$o" update-ref -d "refs/heads/$br"
  git -C "$m" rev-parse -q --verify "refs/remotes/origin/$br" > /dev/null ||
    fail 'stale: no remote-tracking ref'
  run "$base" work "$w"
  expect stale 1 "no ref of origin that this repository holds"
  kept stale "$wt/f.txt"

  git clone -q "$o" "$base/main2"
  git -C "$base/main2" remote set-url origin "$base/missing.git"
  mkwork "$base/main2" unreadable
  commit "$wt" unreadable
  git -C "$wt" push -q "$o" HEAD:refs/heads/unreadable
  git -C "$base/main2" update-ref refs/remotes/origin/unreadable "$c"
  run "$base" work "$w"
  expect unreadable 1 "cannot be read"
  kept unreadable "$wt/f.txt"

  mkwork "$m" tree-ref
  git -C "$wt" update-ref refs/worktree/tree "$t"
  run "$base" work "$w"
  expect 'tree ref' 1 "ref refs/worktree/tree of $wt holds no commit"

  mkwork "$m" worktree-ref
  newcommit "$wt" worktree-ref
  git -C "$wt" update-ref refs/worktree/keep "$c"
  run "$base" work "$w"
  expect 'worktree ref' 1 "of $wt: no ref of origin"
  registered 'worktree ref' yes "$wt"

  mkdir -p "$root/proj/sess/notes/w" "$root/scratchpad/w"
  mkwork "$m" deep
  mkdir -p "$wt/scratchpad/x"
  for d in "$root/proj/sess/notes/w" "$base/outside/scratchpad/w" "$sp" \
    "$root/scratchpad/w" "$wt/scratchpad/x"; do
    run "$base" work "$d"
    expect "outside $d" 1 'not <root>/<project>/<session>/scratchpad/<work>'
    kept "outside $d" "$d"
  done

  mkdir -p "$root/proj/other/scratchpad/w"
  ln -s "$root/proj/other/scratchpad/w" "$sp/link"
  for d in "$sp/link" "$sp/link/" "$sp/link//"; do
    run "$base" work "$d"
    expect "link $d" 1 'a symbolic link'
    kept "link $d" "$root/proj/other/scratchpad/w"
  done
  mkdir "$sp/via-dot"
  for d in "$sp/link/." "$sp/link/./" "$sp/via-dot/../link"; do
    run "$base" work "$d"
    expect "dot $d" 1 'a . or .. component'
    kept "dot $d" "$root/proj/other/scratchpad/w"
  done
  mkdir -p "$root/proj/sess2"
  ln -s "$base/outside/scratchpad" "$root/proj/sess2/scratchpad"
  run "$base" work "$root/proj/sess2/scratchpad/w"
  expect 'linked scratchpad' 1 'not <root>/<project>/<session>/scratchpad'
  kept 'linked scratchpad' "$base/outside/scratchpad/w"
  mkdir "$sp/via-root"
  ln -s "$root" "$base/root-link"
  sroot=$base/root-link
  run "$base" work "$base/root-link/proj/sess/scratchpad/via-root"
  sroot=$root
  expect 'linked root' 0 "removed: $sp/via-root"
  gone 'linked root' "$sp/via-root"

  mkdir "$sp/no-root"
  sroot=$base/no-root
  run "$base" work "$sp/no-root"
  sroot=$root
  expect 'no root' 1 "$base/no-root is not a directory the caller owns"
  kept 'no root' "$sp/no-root"
  mkdir "$sp/other-user"
  spath=$tmp/id-shim:$PATH
  run "$base" work "$sp/other-user"
  spath=$PATH
  expect 'other user' 1 "$root is not a directory the caller owns"
  kept 'other user' "$sp/other-user"

  echo text > "$sp/file"
  run "$base" work "$sp/file"
  expect file 1 'not a directory'
  kept file "$sp/file"

  mkwork "$m" next
  run "$base" work "$unpushed" "$w"
  expect next 1 "refused: $unpushed"
  expect next 1 "removed: $w"
  gone next "$w"

  mkwork "$m" cwd
  for d in "$w/writer" "$w"; do
    run "$d" work "$w"
    expect "cwd $d" 1 'the current directory, or holds it'
    kept "cwd $d" "$wt/f.txt"
  done

  mkdir "$sp/orchestrator"
  run "$base" work "$sp/orchestrator"
  expect orchestrator 1 "the session's own files"
  kept orchestrator "$sp/orchestrator"

  mkdir "$tmp/Case-$sh"
  if [ -d "$tmp/case-$sh" ]; then
    run "$base" work "$sp/Orchestrator"
    expect 'Orchestrator' 1 "the session's own files"
    kept 'Orchestrator' "$sp/orchestrator"
    mkdir -p "$sp/here/writer"
    run "$sp/here/writer" work "$sp/HERE"
    expect 'cwd HERE' 1 'the current directory, or holds it'
    kept 'cwd HERE' "$sp/here/writer"
    mkdir "$sp/case-x"
    run "$base" work "$root/proj/sess/SCRATCHPAD/case-x"
    expect 'SCRATCHPAD' 0 "removed: $sp/case-x"
    mkdir -p "$root/proj/sess3/scratchpad/Orchestrator"
    run "$base" work "$root/proj/sess3/scratchpad/orchestrator"
    expect 'orchestrator on disk' 1 "the session's own files"
    kept 'orchestrator on disk' "$root/proj/sess3/scratchpad/Orchestrator"
  fi
  nfc=$(printf 'dir-\303\251') nfd=$(printf 'dir-e\314\201')
  mkdir "$tmp/$nfc-$sh"
  if [ -d "$tmp/$nfd-$sh" ]; then
    mkdir -p "$sp/$nfc/writer"
    run "$sp/$nfc/writer" work "$sp/$nfd"
    expect "cwd $nfd" 1 'the current directory, or holds it'
    kept "cwd $nfd" "$sp/$nfc/writer"
  fi

  mkwork "$m" 'aap 518 x' 'wt a b'
  mkdir -p "$w/read-only/d"
  echo x > "$w/read-only/d/f"
  chmod 555 "$w/read-only/d"
  run "$base" work "$w"
  expect space 0 "removed: $w"
  gone space "$w"
  registered space no "$wt"
  case $out in
    *denied* | *'not empty'*) fail "space: rm's errors printed: $out" ;;
  esac

  run "$base" work "$sp/never"
  expect absent 0 "absent: $sp/never"

  mkdir -p "$sp/newline/a
b"
  run "$base" work "$sp/newline"
  expect newline 1 'holds a name with a newline or \001'
  kept newline "$sp/newline"

  soh=$(printf '\001')
  mkwork "$m" soh-name "a${soh}b"
  run "$base" work "$w"
  expect 'soh name' 1 'holds a name with a newline or \001'
  case $outc in
    *'holds a name with a newline or \001'*) ;;
    *) fail "soh name: --check does not refuse it: $outc" ;;
  esac
  registered 'soh name' yes "$wt"
  git -C "$m" worktree remove "$wt"
  git -C "$m" branch -q -D "$br"
  mkdir -p "$root/p${soh}q/sess/scratchpad/w"
  run "$base" work "$root/p${soh}q/sess/scratchpad/w"
  expect 'soh path' 1 'its path holds a newline or \001'
  kept 'soh path' "$root/p${soh}q/sess/scratchpad/w"

  # chmod 000 hides nothing from uid 0, or from an account that may read
  # past permissions
  mkdir -p "$sp/unreadable-dir/d"
  chmod 000 "$sp/unreadable-dir/d"
  if find "$sp/unreadable-dir" > /dev/null 2>&1; then
    readable=1
    chmod 755 "$sp/unreadable-dir/d"
    rm -rf "$sp/unreadable-dir"
  else
    run "$base" work "$sp/unreadable-dir"
    chmod 755 "$sp/unreadable-dir/d"
    expect 'unreadable dir' 1 'find cannot read all of it'
    kept 'unreadable dir' "$sp/unreadable-dir/d"
  fi
  mkdir -p "$sp/broken/x"
  echo "gitdir: $base/nowhere" > "$sp/broken/x/.git"
  foreign broken "$sp/broken" 'its gitdir does not resolve'
  expect broken 1 "$sp/broken/x/.git: its gitdir does not resolve"
  kept broken "$sp/broken/x/.git"

  mkwork "$m" bad-index
  echo garbage > "$(git -C "$wt" rev-parse --path-format=absolute \
    --git-path index)"
  run "$base" work "$w"
  expect 'bad index' 1 "git status fails in $wt"
  kept 'bad index' "$wt/f.txt"

  git clone -q "$o" "$sp/f-clone/c"
  foreign 'clone' "$sp/f-clone" "$sp/f-clone/c/.git: not a regular file"
  git init -q "$sp/f-deep/x/y"
  foreign 'deeper .git' "$sp/f-deep" "$sp/f-deep/x/y/.git: a .git not at"
  mkwork "$m" f-nested
  git clone -q "$o" "$wt/ignored/inner"
  [ -z "$(git -C "$wt" status --porcelain)" ] ||
    fail 'nested: the worktree is not clean'
  foreign 'nested' "$w" "$wt/ignored/inner/.git: a .git not at"
  registered 'nested' yes "$wt"
  mkwork "$m" f-sub
  mkdir -p "$wt/ignored/sub"
  echo "gitdir: $m/.git/modules/sub" > "$wt/ignored/sub/.git"
  foreign 'submodule' "$w" "$wt/ignored/sub/.git: a .git not at"
  git clone -q --bare "$o" "$sp/f-bare/b.git"
  foreign 'bare' "$sp/f-bare" "$sp/f-bare/b.git: a git directory's layout"
  git clone -q --bare "$o" "$sp/f-bare-link/b.git"
  rm "$sp/f-bare-link/b.git/HEAD"
  ln -s refs/heads/main "$sp/f-bare-link/b.git/HEAD"
  foreign 'bare, linked HEAD' "$sp/f-bare-link" \
    "$sp/f-bare-link/b.git: a git directory's layout"
  mkdir -p "$sp/f-split/g"
  echo 'ref: refs/heads/main' > "$sp/f-split/g/HEAD"
  echo "$m/.git" > "$sp/f-split/g/commondir"
  foreign 'commondir' "$sp/f-split" "$sp/f-split/g: a git directory's layout"
  git clone -q --separate-git-dir="$sp/f-gitfile/gd" "$o" "$sp/f-gitfile/c"
  foreign 'gitfile inside' "$sp/f-gitfile" "$sp/f-gitfile/"
  git clone -q --separate-git-dir="$base/gd-out" "$o" "$sp/f-gitfile-out/c"
  foreign 'gitfile out' "$sp/f-gitfile-out" 'is in no worktrees directory'
  mkwork "$m" f-link c
  mv "$wt/.git" "$base/f-link-gitfile"
  ln -s "$base/f-link-gitfile" "$wt/.git"
  foreign '.git link' "$w" "$wt/.git: a symbolic link"
  rm "$wt/.git"
  mv "$base/f-link-gitfile" "$wt/.git"

  mkwork "$m" f-hard
  mkdir "$w/e2"
  ln "$wt/.git" "$w/e2/.git"
  foreign 'hard link' "$w" 'a .git with more than one link'
  rm "$w/e2/.git"
  mkdir -p "$sp/f-fifo/e"
  mkfifo "$sp/f-fifo/e/.git"
  foreign 'fifo' "$sp/f-fifo" "$sp/f-fifo/e/.git: not a regular file"
  if [ -d "$tmp/case-$sh" ]; then
    mkwork "$m" f-case
    git clone -q "$o" "$wt/ignored/inner"
    newcommit "$wt/ignored/inner" f-case
    git -C "$wt/ignored/inner" update-ref refs/heads/side "$c"
    mv "$wt/ignored/inner/.git" "$wt/ignored/inner/.GIT"
    mv "$wt/ignored/inner/.GIT/HEAD" "$wt/ignored/inner/.GIT/Head"
    [ "$(git -C "$wt/ignored/inner" rev-parse -q --verify refs/heads/side)" \
      = "$c" ] || fail 'case nested: git does not read it'
    foreign 'case nested' "$w" "$wt/ignored/inner/.GIT: a .git spelled in"
    kept 'case nested' "$wt/ignored/inner/.GIT/Head"
    mkwork "$m" f-case-sub
    git -C "$wt" update-index --add --cacheinfo "160000,$c,sub"
    c=$(git -C "$wt" commit-tree -p HEAD -m f-case-sub \
      "$(git -C "$wt" write-tree)" < /dev/null)
    git -C "$wt" update-ref HEAD "$c"
    git -C "$wt" push -q origin HEAD
    mkdir -p "$wt/sub" "$w/evil/objects" "$w/evil/refs"
    echo 'ref: refs/heads/main' > "$w/evil/head"
    echo '[[[' > "$w/evil/config"
    echo "gitdir: $w/evil" > "$wt/sub/.GIT"
    foreign 'case gitlink' "$w" "$wt/sub/.GIT: a .git spelled in"
    mkwork "$m" listed-case
    admin=$(git -C "$wt" rev-parse --path-format=absolute --git-dir)
    cp "$admin/gitdir" "$base/gitdir-copy"
    echo "$wt/.GIT" > "$admin/gitdir"
    run "$base" work "$w"
    cp "$base/gitdir-copy" "$admin/gitdir"
    expect 'listed under another case' 1 "does not list the worktree $wt"
    registered 'listed under another case' yes "$wt"
    git clone -q --bare "$o" "$sp/f-head-case/b.git"
    mv "$sp/f-head-case/b.git/HEAD" "$sp/f-head-case/b.git/Head"
    foreign 'case HEAD' "$sp/f-head-case" \
      "$sp/f-head-case/b.git: a git directory's layout"
  else
    casefold=
  fi
  mkdir -p "$base/fake/worktrees/x" "$sp/f-fake/e"
  echo 'ref: refs/heads/main' > "$base/fake/worktrees/x/HEAD"
  echo "$m/.git" > "$base/fake/worktrees/x/commondir"
  echo "$sp/f-fake/e/.git" > "$base/fake/worktrees/x/gitdir"
  echo "gitdir: $base/fake/worktrees/x" > "$sp/f-fake/e/.git"
  foreign 'commondir elsewhere' "$sp/f-fake" \
    "$base/fake/worktrees/x/commondir does not name the repository"
  mkwork "$m" unreadable-head
  head=$(git -C "$wt" rev-parse --path-format=absolute --git-dir)/HEAD
  cp "$head" "$base/head-copy"
  echo garbage > "$head"
  run "$base" work "$w"
  cp "$base/head-copy" "$head"
  expect 'unreadable HEAD' 1 "git cannot read $wt"
  kept 'unreadable HEAD' "$wt/f.txt"

  mkdir -p "$sp/lone-head/notes" "$sp/notes-only/writer" "$sp/rev/codex-1"
  echo 'ref: refs/heads/main' > "$sp/lone-head/notes/HEAD"
  echo note > "$sp/notes-only/writer/msg.txt"
  echo report > "$sp/rev/codex-1/report.md"
  for d in "$sp/lone-head" "$sp/notes-only" "$sp/rev"; do
    : > "$GITLOG"
    spath=$tmp/log-shim:$PATH
    run "$base" work "$d"
    spath=$PATH
    expect "no repository $d" 0 "removed: $d"
    [ ! -s "$GITLOG" ] || fail "no repository $d: git ran: $(cat "$GITLOG")"
  done
  mkwork "$m" several wt1
  wt1=$wt br1=$br
  git -C "$m" worktree add -q -b b-several2 "$w/wt2" origin/main 2> /dev/null
  : > "$GITLOG"
  spath=$tmp/log-shim:$PATH
  run "$base" work "$w"
  spath=$PATH
  expect several 0 "removed: $w"
  registered several no "$wt1"
  registered several no "$w/wt2"
  [ -s "$GITLOG" ] || fail 'several: the logging stand-in logged nothing'

  mkwork "$m" gitlink-link
  git -C "$wt" update-index --add --cacheinfo "160000,$t,sub"
  c=$(git -C "$wt" commit-tree -p HEAD -m gitlink-link \
    "$(git -C "$wt" write-tree)" < /dev/null)
  git -C "$wt" update-ref HEAD "$c"
  git -C "$wt" push -q origin HEAD
  rm -rf "$wt/sub"
  ln -s ../f.txt "$wt/sub"
  run "$base" work "$w"
  # git 2.54 fails status here and git 2.43 reports a change: both refuse
  [ "$rc" = 1 ] || fail "gitlink link: exit $rc, not 1: $out"
  case $out in
    *"git status fails in $wt"*) ;;
    *"uncommitted change or untracked file in $wt"*) ;;
    *) fail "gitlink link: no refusal of $wt in: $out" ;;
  esac
  kept 'gitlink link' "$wt/f.txt"
  gone 'gitlink link' "$w/.sweep-unfinished"

  mkwork "$m" tag-head
  x=$(git -C "$m" rev-parse origin/main)
  git -C "$m" update-ref refs/tags/valuable "$x"
  git -C "$wt" symbolic-ref HEAD refs/tags/valuable
  run "$base" work "$w"
  expect 'tag head' 1 \
    "the HEAD of $wt names refs/tags/valuable, which is not a branch"
  kept 'tag head' "$wt/f.txt"
  [ "$(git -C "$m" rev-parse -q --verify refs/tags/valuable)" = "$x" ] ||
    fail 'tag head: the tag refs/tags/valuable is gone'

  mkwork "$m" findings
  echo record > "$w/findings-$br.md"
  run "$base" work "$w"
  expect findings 1 "holds the findings record $w/findings-$br.md"
  "$sh" -c "$movecmd" sh "$w/" || fail 'findings: the move fails'
  run "$base" work "$w"
  expect 'findings moved' 0 "removed: $w"
  [ "$(cat "$sp/orchestrator/findings/findings-$br.md")" = record ] ||
    fail 'findings moved: the record is not in the orchestrator directory'
  mkwork "$m" collide
  mkdir -p "$sp/orchestrator/collide"
  echo old > "$sp/orchestrator/collide/findings-x.md"
  echo new > "$w/findings-x.md"
  "$sh" -c "$movecmd" sh "$w" || fail 'collide: the move fails'
  run "$base" work "$w"
  expect collide 1 "holds the findings record $w/findings-x.md"
  [ "$(cat "$sp/orchestrator/collide/findings-x.md")" = old ] &&
    [ "$(cat "$w/findings-x.md")" = new ] || fail 'collide: a record was lost'
  mkwork "$m" findings-below
  echo record > "$w/writer/findings-y.md"
  run "$base" work "$w"
  expect 'findings below' 1 "holds the findings record $w/writer/findings-y.md"

  mkwork "$m" modules
  gd=$(git -C "$wt" rev-parse --path-format=absolute --git-dir)
  mkdir "$gd/modules"
  run "$base" work "$w"
  rmdir "$gd/modules"
  expect modules 1 "$gd holds modules, which git worktree remove refuses"
  kept modules "$wt/f.txt"
  gone modules "$w/.sweep-unfinished"

  git clone -q "$o" "$base/main4"
  mkwork "$base/main4" no-origin
  commit "$wt" no-origin
  echo origin >> "$base/main4/.git/info/exclude"
  git -C "$base/main4" remote rename origin upstream
  git -C "$wt" bundle create -q "$wt/origin" "$br" 2> /dev/null
  [ -n "$(git -C "$wt" ls-remote origin 2> /dev/null)" ] ||
    fail 'no origin: the bundle lists nothing'
  run "$base" work "$w"
  expect 'no origin' 1 "$wt has no remote named origin"
  kept 'no origin' "$wt/f.txt"
  [ "$(git -C "$base/main4" rev-parse -q --verify "refs/heads/$br")" = "$c" ] ||
    fail "no origin: branch $br is not at $c"

  # git worktree add --orphan is git 2.42's
  if git -C "$base/main4" worktree add -q --orphan -b orphan \
    "$sp/orphan/wt" 2> /dev/null; then
    run "$base" work "$sp/orphan"
    expect 'orphan, no origin' 0 "removed: $sp/orphan"
    case $outc in
      *"would deregister: $sp/orphan/wt"*) ;;
      *) fail "orphan, no origin: --check names no worktree: $outc" ;;
    esac
    case $outc in
      *'would delete branch:'*)
        fail "orphan, no origin: --check would delete a branch: $outc"
        ;;
    esac
  else
    noorphan=1
  fi

  # a detached worktree has a commit at HEAD and no branch
  w=$sp/detached wt=$sp/detached/wt
  mkdir -p "$w/writer"
  echo note > "$w/writer/msg.txt"
  git -C "$m" worktree add -q --detach "$wt" origin/main 2> /dev/null ||
    fail 'detached: no worktree'
  heads=$(git -C "$m" for-each-ref refs/heads)
  run "$base" work "$w"
  expect detached 0 "removed: $w"
  registered detached no "$wt"
  case $outc in
    *"would deregister: $wt"*) ;;
    *) fail "detached: --check names no worktree: $outc" ;;
  esac
  case $outc in
    *'would delete branch:'*) fail "detached: --check names a branch: $outc" ;;
  esac
  case $out in
    *'branch:'*) fail "detached: the run names a branch: $out" ;;
  esac
  [ "$(git -C "$m" for-each-ref refs/heads)" = "$heads" ] ||
    fail 'detached: a branch was deleted'

  mkwork "$m" missing-parent
  p=0000000000000000000000000000000000000001
  c=$(printf 'tree %s\nparent %s\nauthor %s\ncommitter %s\n\nx\n' "$t" "$p" \
    'Fixture <fixture@example.invalid> 0 +0000' \
    'Fixture <fixture@example.invalid> 0 +0000' |
    git -C "$wt" hash-object -t commit -w --stdin --literally)
  git -C "$wt" update-ref refs/worktree/side "$c"
  run "$base" work "$w"
  expect 'missing parent' 1 "git cannot list the commits of $wt"
  kept 'missing parent' "$wt/f.txt"

  mkwork "$m" locked wt1
  wt1=$wt br1=$br
  git -C "$m" worktree add -q -b "b-locked2" "$w/wt2" origin/main 2> /dev/null
  git -C "$m" worktree lock "$w/wt2"
  run "$base" work --check "$w"
  expect 'locked check' 1 "worktree $w/wt2 is locked"
  run "$base" work "$w"
  expect locked 1 "worktree $w/wt2 is locked"
  registered locked yes "$wt1"
  branch locked yes "$br1"
  kept locked "$w/wt2/f.txt"
  git -C "$m" worktree unlock "$w/wt2"

  mkwork "$m" mv-from
  mkdir "$sp/mv-to"
  mv "$wt" "$sp/mv-to/wt"
  foreign 'moved worktree' "$sp/mv-to" 'gitdir does not name it'
  expect 'moved worktree' 1 "$sp/mv-to/wt/.git: "
  kept 'moved worktree' "$sp/mv-to/wt/f.txt"
  gone 'moved worktree' "$sp/mv-to/.sweep-unfinished"
  git -C "$m" worktree prune

  mkwork "$m" moved
  newcommit "$wt" moved
  spath=$tmp/git-shim:$PATH
  SHIM_GIT_DIR=$m/.git SHIM_MOVE_REF=refs/heads/$br SHIM_MOVE_TO=$c
  export SHIM_GIT_DIR SHIM_MOVE_REF SHIM_MOVE_TO
  run "$base" work "$w"
  unset SHIM_GIT_DIR SHIM_MOVE_REF SHIM_MOVE_TO
  spath=$PATH
  expect moved 0 "kept branch: refs/heads/$br"
  expect moved 0 "removed: $w"
  [ "$(git -C "$m" rev-parse -q --verify "refs/heads/$br")" = "$c" ] ||
    fail "moved: branch $br is not at $c"

  mkwork "$m" checked-out
  git -C "$wt" checkout -q --ignore-other-worktrees main
  x=$(git -C "$m" rev-parse refs/heads/main)
  run "$base" work "$w"
  expect 'checked out' 0 "kept branch: refs/heads/main of $m/.git, checked out"
  expect 'checked out' 0 "removed: $w"
  case $outc in
    *"would keep branch: refs/heads/main of $m/.git, checked out in $m"*) ;;
    *) fail "checked out: --check does not keep main: $outc" ;;
  esac
  case $outc$out in
    *'delete branch'* | *'deleted branch'*)
      fail "checked out: a branch is deleted: $outc / $out"
      ;;
  esac
  [ "$(git -C "$m" rev-parse -q --verify refs/heads/main)" = "$x" ] ||
    fail 'checked out: branch main is not where it was'
  registered 'checked out' no "$wt"
  same 'checked out'

  mkwork "$m" shared wt1
  wt1=$wt br1=$br
  git -C "$m" worktree add -q -f "$w/wt2" "$br1" 2> /dev/null ||
    fail 'shared: no second worktree'
  run "$base" work "$w"
  expect shared 0 "deleted branch: refs/heads/$br1 of $m/.git"
  expect shared 0 "removed: $w"
  same shared
  branch shared no "$br1"
  registered shared no "$wt1"
  registered shared no "$w/wt2"

  mkwork "$m" far-newline
  nl='
'
  far="$base/o${nl}worktree $wt"
  git -C "$m" worktree add -q -f "$far" "$br" 2> /dev/null ||
    fail 'far newline: no worktree'
  run "$base" work "$w"
  expect 'far newline' 0 "kept branch: refs/heads/$br of $m/.git, checked out"
  expect 'far newline' 0 "checked out in $base/o?worktree $wt$nl"
  expect 'far newline' 0 "removed: $w"
  same 'far newline'
  branch 'far newline' yes "$br"
  git -C "$far" rev-parse -q --verify HEAD > /dev/null ||
    fail 'far newline: the HEAD of the worktree outside does not resolve'
  git -C "$m" worktree remove "$far"
  git -C "$m" branch -q -D "$br" 2> /dev/null

  mkwork "$m" soh-link
  far="$base/s${nl}y"
  git -C "$m" worktree add -q -f "$far" "$br" 2> /dev/null ||
    fail 'soh link: no worktree'
  ln -s "$wt" "$base/s${soh}y"
  run "$base" work "$w"
  expect 'soh link' 0 "kept branch: refs/heads/$br of $m/.git, checked out"
  expect 'soh link' 0 "checked out in $base/s?y$nl"
  expect 'soh link' 0 "removed: $w"
  same 'soh link'
  branch 'soh link' yes "$br"
  git -C "$m" worktree remove "$far"
  git -C "$m" branch -q -D "$br" 2> /dev/null

  mkwork "$m" gone-git wa
  brg=$br
  git -C "$m" worktree add -q -f "$w/wb" "$brg" 2> /dev/null ||
    fail 'gone .git: no second worktree'
  rm "$w/wb/.git"
  run "$base" work "$w"
  expect 'gone .git' 0 "kept branch: refs/heads/$brg of $m/.git, checked out"
  expect 'gone .git' 0 "checked out in $w/wb$nl"
  expect 'gone .git' 0 "removed: $w"
  same 'gone .git'
  branch 'gone .git' yes "$brg"
  git -C "$m" worktree prune
  git -C "$m" branch -q -D "$brg" 2> /dev/null

  mkwork "$m" pair-a
  wa=$w bra=$br
  git -C "$m" worktree add -q -f "$sp/pair-b/wt" "$bra" 2> /dev/null ||
    fail 'pair: no second worktree'
  run "$base" work "$wa" "$sp/pair-b"
  expect pair 0 "kept branch: refs/heads/$bra of $m/.git, checked out in"
  expect pair 0 "checked out in $sp/pair-b/wt$nl"
  expect pair 0 "deleted branch: refs/heads/$bra of $m/.git"
  expect pair 0 "removed: $sp/pair-b"
  same pair
  branch pair no "$bra"

  mkwork "$m" half wt1
  git -C "$m" worktree add -q -b "b-half2" "$w/wt2" origin/main 2> /dev/null
  git -C "$m" worktree add -q -b "b-half3" "$w/wt3" origin/main 2> /dev/null
  # the removal fails on the worktree removed third, in the order the
  # script finds them
  run "$base" work --check "$w"
  ws=$(printf '%s\n' "$out" | sed -n 's/^would deregister: //p')
  first=$(printf '%s\n' "$ws" | sed -n 1p)
  second=$(printf '%s\n' "$ws" | sed -n 2p)
  third=$(printf '%s\n' "$ws" | sed -n 3p)
  fb1=$(git -C "$first" symbolic-ref -q HEAD) || fail 'half: no branch'
  fb2=$(git -C "$second" symbolic-ref -q HEAD) || fail 'half: no branch'
  spath=$tmp/git-shim:$PATH
  SHIM_FAIL=$third nocheck=1
  export SHIM_FAIL
  run "$base" work "$w"
  unset SHIM_FAIL
  nocheck=
  spath=$PATH
  expect half 1 "git worktree remove $third fails"
  expect half 1 "so do the branches $fb1 of $m/.git, $fb2 of $m/.git"
  for fb in "$fb1" "$fb2"; do
    git -C "$m" rev-parse -q --verify "$fb" > /dev/null ||
      fail "half: branch $fb was deleted"
  done
  [ -d "$w/.sweep-unfinished" ] || fail 'half: no .sweep-unfinished'
  kept half "$third/f.txt"
  echo new > "$third/new.txt"
  run "$base" work "$w"
  expect 'half again' 1 'holds .sweep-unfinished'
  kept 'half again' "$third/new.txt"
  git -C "$m" worktree prune

  git -C "$m" worktree add -q -b wt-direct "$sp/wt-direct" origin/main \
    2> /dev/null
  foreign 'work that is a worktree' "$sp/wt-direct" 'a .git not at <work>/<e>'
  registered 'work that is a worktree' yes "$sp/wt-direct"
  [ -z "$(git -C "$sp/wt-direct" status --porcelain)" ] ||
    fail 'work that is a worktree: it was dirtied'
  echo x > "$base/marker-target"
  mkdir -p "$sp/top-git/.git" "$sp/top-head/objects" "$sp/top-head/refs"
  echo x > "$sp/top-head/HEAD"
  foreign 'top .git' "$sp/top-git" 'a .git not at <work>/<e>'
  foreign 'top HEAD' "$sp/top-head" "$sp/top-head: a git directory's layout"
  for kind in file link dangling directory; do
    mkwork "$m" "marker-$kind"
    mk=$w/.sweep-unfinished
    case $kind in
      file) : > "$mk" ;;
      link) ln -s "$base/marker-target" "$mk" ;;
      dangling) ln -s "$base/marker-dangling" "$mk" ;;
      directory) mkdir "$mk" ;;
    esac
    run "$base" work "$w"
    expect "marker $kind" 1 'holds .sweep-unfinished'
    kept "marker $kind" "$wt/f.txt"
  done
  gone 'marker dangling' "$base/marker-dangling"

  if command -v chflags > /dev/null; then
    mkdir -p "$sp/immutable"
    echo x > "$sp/immutable/f"
    if chflags uchg "$sp/immutable/f" 2> /dev/null; then
      nocheck=1
      run "$base" work "$sp/immutable"
      nocheck=
      chflags nouchg "$sp/immutable/f"
      expect immutable 1 'rm -rf fails'
    else
      noflag=1
      rm -rf "$sp/immutable"
    fi
  fi

  mkwork "$m" git-dir
  rc=0
  out=$(cd "$base" && GIT_DIR=$o SWEEP_ROOT=$root "$sh" "$script" work "$w" \
    2>&1) || rc=$?
  expect 'GIT_DIR' 0 "removed: $w"
  [ "$(git -C "$o" worktree list --porcelain | grep -c '^worktree ')" = 1 ] ||
    fail 'GIT_DIR: origin holds a worktree entry'

  run "$base" sweep "$sp/never"
  expect 'unknown mode' 2 'usage: sh sweep.sh work'
  run "$base" work -x "$sp/never"
  expect 'unknown option' 2 'usage: sh sweep.sh work'
  run "$base" work
  expect 'no directory' 2 'usage: sh sweep.sh work'

  o3=$base/origin3.git
  git init -q --bare -b main "$o3"
  git --git-dir="$o" push -q "$o3" refs/heads/main
  git clone -q "$o3" "$base/main3"
  mkwork "$base/main3" moved-on
  c=$(git -C "$o3" commit-tree -p main -m moved-on "$t" < /dev/null)
  git -C "$o3" update-ref refs/heads/main "$c"
  run "$base" work "$w"
  expect 'origin moved on' 1 \
    'no ref of origin that this repository holds reaches it; fetch origin'
  kept 'origin moved on' "$wt/f.txt"
  git -C "$base/main3" fetch -q origin
  run "$base" work "$w"
  expect 'origin moved on, fetched' 0 "removed: $w"
  mkwork "$base/main3" pull-ahead
  commit "$wt" pushed
  x=$c
  git -C "$wt" push -q origin "$br" 2> /dev/null
  c=$(git -C "$o3" commit-tree -p "$x" -m update-branch "$t" < /dev/null)
  git -C "$o3" update-ref refs/pull/6/head "$c"
  c=$(git -C "$o3" commit-tree -p main -m squash "$t" < /dev/null)
  git -C "$o3" update-ref refs/heads/main "$c"
  git -C "$o3" update-ref -d "refs/heads/$br"
  git -C "$base/main3" fetch -q origin
  run "$base" work "$w"
  expect 'pull head ahead' 1 'fetch origin'
  "$sh" -c "$pullcmd" sh "$base/main3" 6 2> /dev/null ||
    fail 'pull head ahead: the fetch fails'
  run "$base" work "$w"
  expect 'pull head ahead, fetched' 0 "removed: $w"
  lookups

  for r in "$m" "$base/main2" "$base/main3" "$base/main4"; do
    s=$(git -C "$r" worktree prune -n -v 2>&1)
    [ -z "$s" ] || fail "stale worktree entries in $r: $s"
  done
}

shells=
for sh in ${TEST_SWEEP_SHELLS:-sh dash bash}; do
  command -v "$sh" > /dev/null || continue
  cases
  shells="$shells $sh"
done

if command -v zsh > /dev/null; then
  sh=zsh base=$tmp/sh sp=$tmp/sh/root/proj/sess/scratchpad
  mkdir -p "$tmp/process/scripts" "$sp/zsh paste"
  cp "$script" "$tmp/process/scripts/sweep.sh"
  rc=0
  out=$(cd "$tmp" && PROCESS=$tmp/process SWEEP_ROOT=$tmp/sh/root \
    zsh -f -i -c 'work=$1
sh "${PROCESS:?}/scripts/sweep.sh" work "${work:?}"' zsh "$sp/zsh paste" \
    < /dev/null 2>&1) || rc=$?
  expect 'zsh paste' 0 "removed: $sp/zsh paste"
  gone 'zsh paste' "$sp/zsh paste"
  lookups
  shells="$shells zsh"
fi

[ -n "$casefold" ] ||
  echo 'the file system keeps letter case: the case-folding cases are skipped'
[ -z "$readable" ] ||
  echo 'find reads a directory of mode 000: the unreadable case is skipped'
[ -z "$noflag" ] ||
  echo 'chflags uchg was refused: the immutable file case is skipped'
[ -z "$noorphan" ] ||
  echo 'git worktree add --orphan fails: the orphan case is skipped'
[ "$status" = 0 ] && echo "sweep.sh answers as expected under:$shells"
exit "$status"
