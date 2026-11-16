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
# identity, and a tag with git mktag: neither signs unless asked, and the
# stand-in gpg.program makes a fixture that ever asks fail instead of
# reaching a real key. Each commit message names its case, so that no two
# cases make the same commit. Stand-ins for git and id, first on the PATH
# of the cases that need them, move a branch or fail a step at a set
# moment, and make the caller another user: the test cannot make a
# directory that another user owns.
#
# The cases, each a <work> directory unless it says otherwise. Removed
# means removed, its worktrees deregistered and their branches deleted;
# refused means refused with its reason, nothing in it removed:
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
# - a clone whose commit only a lightweight or an annotated tag, refs/stash,
#   refs/wip/x or refs/notes/commits holds is refused; one whose commit
#   only a tag of origin holds is removed; one with a ref to a tree is
#   refused; a linked worktree whose commit only refs/worktree/keep holds
#   is refused;
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
# - a name with a newline inside, or a directory find cannot read, is
#   refused;
# - a clone with a modified file is refused;
# - a clone with an unpushed branch, and a bare repository with one, are
#   refused; a clean bare clone is one --check would remove;
# - a clone with a worktree outside the directory is refused, and so is
#   a bare repository whose worktree outside sits below a directory that
#   cannot be entered; an entry whose worktree, or the directory above
#   it, is gone is stale and swept. As uid 0, whom chmod 000 does not
#   stop, the unreadable directory and that hidden worktree are skipped;
# - a commit that only a branch of the repository holds is refused, in a
#   bare repository whose HEAD is a symbolic link, a clone whose .git is a
#   symbolic link, a clone whose .git file names a git directory inside
#   the work directory, and a clone inside an ignored directory of a clean
#   clone; a clone whose .git file names a git directory outside it is
#   refused too;
# - a work directory that is itself a worktree is refused and left clean;
#   so is one holding .sweep-unfinished as a file, a symbolic link, a
#   dangling one, whose target is not created, or a directory;
# - where origin has moved on to a commit the repository has not fetched,
#   a commit it reaches is refused, with fetch named, and removed once
#   origin is fetched;
# - a commit only a split repository holds is refused, its git directory
#   naming its store in commondir, inside the directory and at its top,
#   and so is a git directory whose worktree is outside, and a HEAD beside
#   a commondir file git does not open; a bare repository
#   with a linked worktree inside the directory is removed;
# - a directory with an empty .git, or a HEAD beside objects and refs that
#   git does not open, at its top is refused;
# - where the pull request's head on origin is a child of the worktree's
#   pushed commit, and its branch was squashed and deleted, the directory
#   is refused after a fetch of origin and removed after a fetch of the
#   head;
# - with the session's directory spelled Orchestrator, where the file
#   system ignores case, the name orchestrator is refused;
# - for each case a run decides, --check exits as the run does, except
#   where a stand-in fails a step only the run takes;
# - a .git that git cannot read, a worktree whose index git cannot read, a
#   .git directory or a bare repository's layout that git reads as part of
#   an enclosing clone, and a commit whose parent is missing, are refused;
# - a locked worktree is refused by --check and by a run, and the other
#   worktree of its directory stays registered;
# - a worktree moved by hand, which its repository does not list where it
#   is, is refused;
# - a branch whose tip moves before its deletion is kept and printed, and
#   the directory is removed;
# - where git worktree remove fails half-way, the directory is refused
#   and keeps .sweep-unfinished, and the next run refuses it;
# - where rm cannot remove a file, the directory is refused (with chflags
#   only, where it exists);
# - with GIT_DIR set to another repository, a clean directory is still
#   removed and that repository is left as it was;
# - an unknown mode, an unknown option and no directory exit 2 with the
#   usage;
# - after the cases, no repository holds a stale worktree entry;
# - under an interactive zsh, where present, the two lines of
#   process/every-role.md's *Debris goes when its work ends*, with a path
#   for <work>, remove its directory.

# a git variable the caller sets, as a hook run by git commit inherits,
# would send the fixtures' git writes to the caller's repository
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_COMMON_DIR CDPATH
unset GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_NAMESPACE
script=${1:-$(dirname "$0")/sweep.sh}
script=$(cd -P "$(dirname "$script")" && pwd -P)/${script##*/}
[ -f "$script" ] || { echo "FAIL: no script $script"; exit 1; }
tmp=$(mktemp -d) || exit 1
asroot=
[ "$(id -u)" != 0 ] || asroot=1
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

# The stand-in for git. Before `update-ref -d` it moves $SHIM_MOVE_REF of
# $SHIM_GIT_DIR to $SHIM_MOVE_TO; at `worktree remove` of $SHIM_FAIL, it
# removes that worktree's .git file and fails.
REAL_GIT=$(command -v git)
export REAL_GIT
mkdir "$tmp/git-shim" "$tmp/id-shim"
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
kept() { [ -e "$2" ] || fail "$1: $2 was removed"; }

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

# mkclone <name>: $sp/<name>/c, a clone of origin; sets $w and $cl
mkclone() {
  w=$sp/$1 cl=$sp/$1/c
  git clone -q "$o" "$cl" || fail "mkclone $1"
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

  for ref in refs/tags/v9 refs/tags/a9 refs/stash refs/wip/x \
    refs/notes/commits; do
    mkclone "clone-$(printf '%s' "${ref#refs/}" | tr / -)"
    newcommit "$cl" "$ref"
    if [ "$ref" = refs/tags/a9 ]; then
      c=$(printf 'object %s\ntype commit\ntag a9\ntagger %s\n\na9\n' "$c" \
        'Fixture <fixture@example.invalid> 0 +0000' | git -C "$cl" mktag)
    fi
    git -C "$cl" update-ref "$ref" "$c"
    run "$base" work "$w"
    expect "$ref" 1 "of $cl: no ref of origin"
    kept "$ref" "$cl/f.txt"
  done

  mkclone remote-tag
  newcommit "$cl" remote-tag
  git -C "$cl" update-ref refs/tags/rt "$c"
  git -C "$cl" push -q origin refs/tags/rt
  run "$base" work "$w"
  expect 'remote tag' 0 "removed: $w"

  mkclone tree-ref
  git -C "$cl" update-ref refs/tags/tree "$t"
  run "$base" work "$w"
  expect 'tree ref' 1 "ref refs/tags/tree of $cl holds no commit"

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
  expect newline 1 'holds a name with a newline'
  kept newline "$sp/newline"

  # chmod 000 hides nothing from uid 0
  if [ -z "$asroot" ]; then
    mkdir -p "$sp/unreadable-dir/d"
    chmod 000 "$sp/unreadable-dir/d"
    run "$base" work "$sp/unreadable-dir"
    chmod 755 "$sp/unreadable-dir/d"
    expect 'unreadable dir' 1 'find cannot read all of it'
    kept 'unreadable dir' "$sp/unreadable-dir/d"

    git clone -q --bare "$o" "$sp/hidden/b.git"
    mkdir -m 700 "$base/hid"
    git -C "$sp/hidden/b.git" worktree add -q --detach "$base/hid/wt" main \
      2> /dev/null
    chmod 000 "$base/hid"
    run "$base" work "$sp/hidden"
    chmod 700 "$base/hid"
    expect 'hidden worktree' 1 "worktree that cannot be resolved: $base/hid/wt"
    kept 'hidden worktree' "$sp/hidden/b.git/HEAD"
    git -C "$base/hid/wt" rev-parse -q --verify HEAD > /dev/null ||
      fail 'hidden worktree: git no longer reads it'
  fi
  for d in "$base/stale-wt" "$base/gone-parent/wt"; do
    rm -rf "$sp/bare-stale"
    git clone -q --bare "$o" "$sp/bare-stale/b.git"
    git -C "$sp/bare-stale/b.git" worktree add -q --detach "$d" main \
      2> /dev/null
    rm -rf "${d%/wt}"
    run "$base" work "$sp/bare-stale"
    expect "stale entry $d" 0 "removed: $sp/bare-stale"
  done

  mkclone clone
  git -C "$cl" branch -q side
  newcommit "$cl" clone
  git -C "$cl" update-ref refs/heads/side "$c"
  run "$base" work "$w"
  expect clone 1 "of $cl: no ref of origin"
  kept clone "$cl/f.txt"
  mkclone clone-modified
  echo more >> "$cl/f.txt"
  run "$base" work "$w"
  expect 'clone modified' 1 "uncommitted change or untracked file in $cl"
  kept 'clone modified' "$cl/f.txt"

  git clone -q --bare "$o" "$sp/bare/b.git"
  run "$base" work --check "$sp/bare"
  expect 'clean bare' 0 "would remove: $sp/bare"
  c=$(git -C "$sp/bare/b.git" commit-tree -p HEAD -m bare "$t" < /dev/null)
  git -C "$sp/bare/b.git" update-ref refs/heads/x "$c"
  run "$base" work "$sp/bare"
  expect bare 1 "of $sp/bare/b.git: no ref of origin"
  kept bare "$sp/bare/b.git/HEAD"
  git clone -q --bare "$o" "$sp/bare-link/b.git"
  c=$(git -C "$sp/bare-link/b.git" commit-tree -p HEAD -m bare-link "$t" \
    < /dev/null)
  git -C "$sp/bare-link/b.git" update-ref refs/heads/x "$c"
  rm "$sp/bare-link/b.git/HEAD"
  ln -s refs/heads/main "$sp/bare-link/b.git/HEAD"
  [ "$(git -C "$sp/bare-link/b.git" rev-parse --is-bare-repository)" = true ] ||
    fail 'bare with a linked HEAD: git does not read it'
  run "$base" work "$sp/bare-link"
  expect 'bare with a linked HEAD' 1 "of $sp/bare-link/b.git: no ref of origin"
  kept 'bare with a linked HEAD' "$sp/bare-link/b.git/objects"

  mkclone git-link
  mv "$cl/.git" "$w/gd"
  ln -s ../gd "$cl/.git"
  newcommit "$cl" git-link
  git -C "$cl" update-ref refs/heads/side "$c"
  run "$base" work "$w"
  expect '.git link' 1 "refused: $w: "
  kept '.git link' "$w/gd/HEAD"
  w=$sp/gitfile cl=$sp/gitfile/c
  git clone -q --separate-git-dir="$w/gd" "$o" "$cl"
  newcommit "$cl" gitfile
  git -C "$cl" update-ref refs/heads/side "$c"
  run "$base" work "$w"
  expect gitfile 1 "refused: $w: "
  kept gitfile "$w/gd/HEAD"
  w=$sp/gitfile-out cl=$sp/gitfile-out/c
  git clone -q --separate-git-dir="$base/gd-out" "$o" "$cl"
  newcommit "$cl" gitfile-out
  git -C "$cl" update-ref refs/heads/side "$c"
  run "$base" work "$w"
  expect 'gitfile out' 1 "refused: $w: "
  kept 'gitfile out' "$cl/f.txt"
  mkclone ignored-repo
  git clone -q "$o" "$cl/ignored/inner"
  newcommit "$cl/ignored/inner" ignored-repo
  git -C "$cl/ignored/inner" update-ref refs/heads/side "$c"
  [ -z "$(git -C "$cl" status --porcelain)" ] ||
    fail 'ignored repo: the outer clone is not clean'
  run "$base" work "$w"
  expect 'ignored repo' 1 "of $cl/ignored/inner: no ref of origin"
  kept 'ignored repo' "$cl/ignored/inner/f.txt"
  for d in "$sp/split" "$sp/split-top"; do
    git clone -q --bare "$o" "$d/store"
    c=$(git -C "$d/store" commit-tree -p HEAD -m split "$t" < /dev/null)
    git -C "$d/store" update-ref refs/heads/x "$c"
  done
  mkdir "$sp/split/repo"
  mv "$sp/split/store/HEAD" "$sp/split/repo/HEAD"
  echo ../store > "$sp/split/repo/commondir"
  mv "$sp/split-top/store/HEAD" "$sp/split-top/HEAD"
  echo store > "$sp/split-top/commondir"
  for g in "$sp/split/repo" "$sp/split-top"; do
    d=${g%/repo}
    [ -n "$(git --git-dir="$g" rev-parse -q --verify 'HEAD^{commit}')" ] ||
      fail "split $d: git does not read it"
    run "$base" work "$d"
    expect "split $d" 1 'is the git directory of a worktree of'
    kept "split $d" "$d/store/objects"
  done
  mkdir "$sp/sep"
  git clone -q --separate-git-dir="$sp/sep/gd" "$o" "$base/sep-wt"
  run "$base" work "$sp/sep"
  expect 'git directory, worktree out' 1 'whose worktree is not found'
  kept 'git directory, worktree out' "$sp/sep/gd/HEAD"
  mkdir -p "$sp/bad-commondir/g"
  echo 'ref: refs/heads/main' > "$sp/bad-commondir/g/HEAD"
  echo ../none > "$sp/bad-commondir/g/commondir"
  run "$base" work "$sp/bad-commondir"
  expect 'commondir git does not open' 1 "git cannot read $sp/bad-commondir/g"
  git clone -q --bare "$o" "$sp/bare-wt/b.git"
  git -C "$sp/bare-wt/b.git" worktree add -q --detach "$sp/bare-wt/wt" main \
    2> /dev/null
  run "$base" work "$sp/bare-wt"
  expect 'bare with a worktree' 0 "removed: $sp/bare-wt"

  mkclone wt-out
  git -C "$cl" worktree add -q -b out "$base/out" 2> /dev/null
  run "$base" work "$w"
  expect 'worktree outside' 1 "has a worktree outside it: $base/out"
  kept 'worktree outside' "$cl/f.txt"

  mkdir -p "$sp/broken/x"
  echo "gitdir: $base/nowhere" > "$sp/broken/x/.git"
  run "$base" work "$sp/broken"
  expect broken 1 "git cannot read $sp/broken/x"
  kept broken "$sp/broken/x/.git"

  mkwork "$m" bad-index
  echo garbage > "$(git -C "$wt" rev-parse --path-format=absolute \
    --git-path index)"
  run "$base" work "$w"
  expect 'bad index' 1 "git status fails in $wt"
  kept 'bad index' "$wt/f.txt"

  mkclone enclosed-git
  mkdir -p "$cl/ignored/x/.git"
  run "$base" work "$w"
  expect 'enclosed .git' 1 "git cannot read $cl/ignored/x"
  kept 'enclosed .git' "$cl/f.txt"
  mkclone enclosed-bare
  mkdir -p "$cl/ignored/x/objects" "$cl/ignored/x/refs"
  echo garbage > "$cl/ignored/x/HEAD"
  run "$base" work "$w"
  expect 'enclosed bare' 1 "git cannot read $cl/ignored/x"
  kept 'enclosed bare' "$cl/f.txt"

  mkclone missing-parent
  p=0000000000000000000000000000000000000001
  c=$(printf 'tree %s\nparent %s\nauthor %s\ncommitter %s\n\nx\n' "$t" "$p" \
    'Fixture <fixture@example.invalid> 0 +0000' \
    'Fixture <fixture@example.invalid> 0 +0000' |
    git -C "$cl" hash-object -t commit -w --stdin --literally)
  git -C "$cl" update-ref refs/heads/side "$c"
  run "$base" work "$w"
  expect 'missing parent' 1 "git cannot list the commits of $cl"
  kept 'missing parent' "$cl/f.txt"

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
  run "$base" work "$sp/mv-to"
  expect 'moved worktree' 1 "does not list the worktree $sp/mv-to/wt"
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

  mkwork "$m" half wt1
  wt1=$wt
  git -C "$m" worktree add -q -b "b-half2" "$w/wt2" origin/main 2> /dev/null
  spath=$tmp/git-shim:$PATH
  SHIM_FAIL=$w/wt2 nocheck=1
  export SHIM_FAIL
  run "$base" work "$w"
  unset SHIM_FAIL
  nocheck=
  spath=$PATH
  expect half 1 "git worktree remove $w/wt2 fails"
  [ -d "$w/.sweep-unfinished" ] || fail 'half: no .sweep-unfinished'
  kept half "$w/wt2/f.txt"
  echo new > "$w/wt2/new.txt"
  run "$base" work "$w"
  expect 'half again' 1 'holds .sweep-unfinished'
  kept 'half again' "$w/wt2/new.txt"
  git -C "$m" worktree prune

  git -C "$m" worktree add -q -b wt-direct "$sp/wt-direct" origin/main \
    2> /dev/null
  run "$base" work "$sp/wt-direct"
  expect 'work that is a worktree' 1 'a .git, or a HEAD beside objects'
  registered 'work that is a worktree' yes "$sp/wt-direct"
  [ -z "$(git -C "$sp/wt-direct" status --porcelain)" ] ||
    fail 'work that is a worktree: it was dirtied'
  echo x > "$base/marker-target"
  mkdir -p "$sp/top-git/.git" "$sp/top-head/objects" "$sp/top-head/refs"
  echo x > "$sp/top-head/HEAD"
  for d in "$sp/top-git" "$sp/top-head"; do
    run "$base" work "$d"
    expect "top $d" 1 'a .git, or a HEAD beside objects and refs, at its top'
  done
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
    chflags uchg "$sp/immutable/f"
    nocheck=1
    run "$base" work "$sp/immutable"
    nocheck=
    chflags nouchg "$sp/immutable/f"
    expect immutable 1 'rm -rf fails'
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
  git -C "$base/main3" fetch -q origin refs/pull/6/head
  run "$base" work "$w"
  expect 'pull head ahead, fetched' 0 "removed: $w"

  for r in "$m" "$base/main2" "$base/main3" "$sp/wt-out/c"; do
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
  shells="$shells zsh"
fi

[ -z "$asroot" ] ||
  echo 'as uid 0, the unreadable directory and hidden worktree are skipped'
[ "$status" = 0 ] && echo "sweep.sh answers as expected under:$shells"
exit "$status"
