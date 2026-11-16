# shellcheck shell=sh
# Removes the directories of pieces of work that have ended.
# process/every-role.md's *Debris goes when its work ends* says when the
# orchestrator runs it. POSIX sh, with `test -ef`, which dash, bash and zsh
# have: two names are the same directory where the file system says so,
# whatever their letter case or Unicode form. Run it as:
#
#   sh "${PROCESS:?}/scripts/sweep.sh" work [--check] [--] <work>...
#
# `work` removes each <work> directory named. With --check it runs every
# check, prints what it would remove, and writes nothing in what it
# checks. It refuses a directory, prints why, and goes on to the next,
# where:
#
# - the path has a . or .. component, or, less its trailing slashes, is a
#   symbolic link, or is not a directory. A path through a symbolic link
#   further up names the link's target, as it does to rm;
# - resolved, it is not <root>/<project>/<session>/scratchpad/<work>,
#   <root> being $SWEEP_ROOT resolved, a directory the caller owns:
#   /tmp/claude-<uid> by default, which scripts/test-sweep.sh sets to its
#   fixtures;
# - it is its scratchpad's `orchestrator`, which holds the session's own
#   files;
# - it is the caller's current directory or holds it;
# - it holds a repository that is not a linked worktree of the session's
#   (below);
# - it holds a findings record, findings-*.md, anywhere below it, which
#   process/every-role.md's *Debris goes when its work ends* moves first;
# - it holds .sweep-unfinished, of any kind, which a failed
#   `git worktree remove` leaves (below);
# - find cannot read all of it, or it holds a name with a newline or
#   \001, or its own path holds one;
# - git cannot read one of its worktrees, or its git directory holds
#   modules, or it holds a commit and its repository has no remote named
#   origin, or its HEAD is a symbolic ref to anything but a branch,
#   refs/heads/*, which the removal would delete;
# - it holds a worktree with an uncommitted change, an untracked file that
#   is not ignored, or a file marked assume-unchanged or skip-worktree,
#   whose change git status does not show;
# - it holds a commit that no ref `git ls-remote origin` prints reaches,
#   among the refs whose objects the repository holds, or origin cannot be
#   read while it holds a commit at all. A ref whose commit the repository
#   does not hold proves nothing, as where origin moved on to a commit
#   made elsewhere, and a remote-tracking ref proves nothing, since it
#   outlives the branch. The commits read are each worktree's HEAD and its
#   own refs, refs/worktree, refs/bisect and refs/rewritten, the others
#   being its repository's, outside. A commit that only a reflog or a
#   pseudo-ref such as ORIG_HEAD holds is not read;
# - one of those refs holds an object that is not a commit or a tag of one;
# - one of its linked worktrees is locked, or its repository does not list
#   it.
#
# git runs only in a linked worktree of the session's: git reads a
# repository's config and runs its hooks, and a gate's code, or a
# reviewer's inputs, can write a repository anywhere below <work> but in
# a worktree's own .git file. So, before any git command, find lists
# each name below <work> that is .git in any letter case, and each other
# directory not below such a name, and plain file reads decide. A linked
# worktree of the session's is a directory directly in <work>,
# <work>/<e>, whose .git, spelled so, is a regular file with one link,
# not a symbolic link, whose first line is gitdir: naming a directory
# outside <work>; that directory is worktrees/<id> of a repository
# outside, as its commondir file says, and its gitdir file names that
# .git back. Every other .git, and every directory holding a HEAD beside
# objects and refs or beside commondir, is a repository the script
# cannot tell is the session's: it refuses the directory, names that
# repository, and runs no git at all. HEAD, objects, refs and commondir
# are tested through the file system, so that they fold as they fold for
# git. A HEAD with neither beside it is not one git opens, and is passed
# over.
#
# Nothing is removed before every check of the directory has passed. Then
# the script makes the directory <work>/.sweep-unfinished with mkdir,
# which follows no symbolic link; <work> being no worktree, no worktree
# it removes holds it. It removes each linked worktree with its
# repository's `git worktree remove`, so that the repository keeps no
# entry for it. Once every one is removed, it deletes their branches with
# `git update-ref -d` at the tip that was checked, deleting once a branch
# that two of them had checked out, and removes the directory. A branch
# that a worktree outside the directory has checked out, or one inside
# whose .git file is gone, as `git worktree list --porcelain -z` shows at
# the check, is kept, even where a directory named later removes that
# worktree: the run prints it as `kept branch:`, and --check as
# `would keep branch:`, with ? for each newline in that worktree's path.
# The run has removed the worktrees of a directory named earlier before
# that check, and --check counts them as removed where it would remove
# that directory. A branch whose tip moved meanwhile, or that git cannot
# delete, is kept too, and printed as `kept branch:`. The directory still
# goes. Where `git worktree remove` fails, the branches of the worktrees
# already deregistered stay, and the refusal names them; the directory is
# refused and keeps .sweep-unfinished, so that every later run refuses it
# until a person has read it and removed .sweep-unfinished. Where rm -rf
# fails, the directory is refused, and what it left had passed every
# check. A worktree whose .git file is gone is not found, and its
# repository keeps an entry for it, which `git worktree prune` clears.
#
# Exit 0 where each directory named was removed, or would be under
# --check, or does not exist; 1 where any was refused; 2, after the usage,
# on any other invocation, an unknown mode or option included.
#
# shellcheck disable=SC3013

usage() {
  echo 'usage: sh sweep.sh work [--check] [--] <work>...' >&2
  exit 2
}

case ${1-} in
  work) shift ;;
  *) usage ;;
esac
check=
case ${1-} in
  --check) check=1; shift ;;
esac
case ${1-} in
  --) shift ;;
  -*) usage ;;
esac
[ $# -gt 0 ] || usage

# the caller's git variables would point every call below at one
# repository; GIT_OPTIONAL_LOCKS=0 keeps git status from writing the index
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_COMMON_DIR CDPATH
unset GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_NAMESPACE
GIT_TERMINAL_PROMPT=0 GIT_OPTIONAL_LOCKS=0
export GIT_TERMINAL_PROMPT GIT_OPTIONAL_LOCKS

# real <dir>: its path, every symbolic link resolved, each name spelled as
# the file system holds it; the shells' own pwd prints the case as typed
real() { (cd -P -- "$1" 2> /dev/null && env pwd -P); }
# there <path>: something, a dangling link included, is at <path>
there() { [ -e "$1" ] || [ -L "$1" ]; }
# line <file>: its first line, read as text, in $line
line() { line=; { IFS= read -r line || [ -n "$line" ]; } < "$1"; }
# from <dir> <path>: <path> resolved, in $u, a relative one read from
# <dir>, as git reads it; fails where it does not resolve
from() {
  case $2 in
    /*) u=$2 ;;
    *) u=$1/$2 ;;
  esac
  u=$(real "$u")
}

root=${SWEEP_ROOT:-/tmp/claude-$(id -u)}
# resolved, and owned by the caller: find prints it only then
if ! rroot=$(real "$root") ||
  [ -z "$(find "$rroot" -prune -user "$(id -u)")" ]; then
  rroot=
fi
here=$(env pwd -P)
# a template under $TMPDIR: macOS's mktemp without one ignores it
list=$(mktemp "${TMPDIR:-/tmp}/sweep.XXXXXX") || exit 2
todo=$(mktemp "${TMPDIR:-/tmp}/sweep.XXXXXX") || exit 2
owns=$(mktemp "${TMPDIR:-/tmp}/sweep.XXXXXX") || exit 2
dirs=$(mktemp "${TMPDIR:-/tmp}/sweep.XXXXXX") || exit 2
wls=$(mktemp "${TMPDIR:-/tmp}/sweep.XXXXXX") || exit 2
gone=$(mktemp "${TMPDIR:-/tmp}/sweep.XXXXXX") || exit 2
trap 'rm -f "${list:?}" "${todo:?}" "${owns:?}" "${dirs:?}" "${wls:?}" \
  "${gone:?}"' EXIT
trap 'exit 1' INT TERM
nl='
'
soh=$(printf '\001')
# a ref's commit, or the commit its tag points at, then its type and name
fmt='%(if)%(*objectname)%(then)%(*objectname) %(*objecttype)'
fmt="$fmt%(else)%(objectname) %(objecttype)%(end) %(refname)"
rc=0

refuse() {
  printf 'refused: %s: %s\n' "$name" "$1" >&2
  rc=1
}

# layout <path below the root>: whether it is
# <project>/<session>/scratchpad/<work>
layout() {
  l=$1
  for want in any any scratchpad; do
    case $l in
      */*) part=${l%%/*} l=${l#*/} ;;
      *) return 1 ;;
    esac
    [ -n "$part" ] || return 1
    [ "$want" = any ] || [ "$part" = "$want" ] || return 1
  done
  case $l in
    '' | */*) return 1 ;;
  esac
}

# pushed <repo> <commit>...: refuses where one of the commits is on no ref
# that `git ls-remote origin` prints
pushed() {
  o=$1
  shift
  [ $# -gt 0 ] || return 0
  # with no remote named origin, ls-remote would read a path origin
  if [ -z "$(git -C "$o" config --get remote.origin.url)" ]; then
    refuse "$o has no remote named origin"
    return 1
  fi
  if ! heads=$(git -C "$o" ls-remote origin < /dev/null 2> /dev/null); then
    refuse "the origin of $o cannot be read"
    return 1
  fi
  # the objects origin's refs name that this repository holds
  if ! known=$(printf '%s\n' "$heads" | awk 'NF { print $1 }' |
    git -C "$o" cat-file --batch-check='%(objectname) %(objecttype)'); then
    refuse "git cannot read the objects of $o"
    return 1
  fi
  if ! out=$({
    printf '%s\n' "$@"
    printf '%s\n' "$known" |
      awk '$2 == "commit" || $2 == "tag" { print "^" $1 }'
  } | git -C "$o" rev-list --stdin -n 1); then
    refuse "git cannot list the commits of $o"
    return 1
  fi
  if [ -n "$out" ]; then
    why='no ref of origin that this repository holds reaches it'
    how="fetch origin and the pull request's head, and run again"
    refuse "commit $out of $o: $why; $how"
    return 1
  fi
}

# held <repo> <ref pattern>...: sets $tips to HEAD's commit and those of
# the refs, remote-tracking ones left out; refuses on another object
held() {
  o=$1
  shift
  if ! refs=$(git -C "$o" for-each-ref --format="$fmt" "$@"); then
    refuse "git cannot read the refs of $o"
    return 1
  fi
  refs=$(printf '%s\n' "$refs" | awk 'NF && $3 !~ /^refs\/remotes\//')
  bad=$(printf '%s\n' "$refs" | awk 'NF && $2 != "commit" { print $3; exit }')
  if [ -n "$bad" ]; then
    refuse "ref $bad of $o holds no commit"
    return 1
  fi
  tips=$(printf '%s\n' "$refs" | awk 'NF { print $1 }')
  h=$(git -C "$o" rev-parse -q --verify 'HEAD^{commit}') || h=
  tips="$h $tips"
}

# ours <path>: one of the worktrees the run removes: those the scan
# listed in $owns, and under --check, in $gone, those of the directories
# named earlier, which the run will have removed
ours() {
  for f in "$owns" "$gone"; do
    while IFS= read -r y <&4; do
      if [ "$1" -ef "$y" ]; then return 0; fi
    done 4< "$f"
  done
  return 1
}

# tree <dir>: the checks of the linked worktree <dir>, which the scan
# found to be the session's; it goes in $todo, to be removed with git
# worktree remove
tree() {
  t=$1
  if ! top=$(git -C "$t" rev-parse --show-toplevel 2> /dev/null) ||
    [ ! "$top" -ef "$t" ] ||
    ! gd=$(git -C "$t" rev-parse --path-format=absolute --git-dir) ||
    ! cd_=$(git -C "$t" rev-parse --path-format=absolute --git-common-dir)
  then
    refuse "git cannot read $t"
    return 1
  fi
  # git worktree remove refuses a worktree whose git directory holds
  # modules, and one whose submodules git status, reading them, fails
  # on; the scan has refused every .git inside
  if there "$gd/modules"; then
    refuse "$gd holds modules, which git worktree remove refuses"
    return 1
  fi
  if ! s=$(git -C "$t" status --porcelain --untracked-files=normal \
    --ignore-submodules=none); then
    refuse "git status fails in $t"
    return 1
  fi
  if [ -n "$s" ]; then
    refuse "uncommitted change or untracked file in $t"
    return 1
  fi
  # ls-files -v tags a file assume-unchanged in lower case, skip-worktree S
  if ! v=$(git -C "$t" ls-files -v); then
    refuse "git cannot list the files of $t"
    return 1
  fi
  if printf '%s\n' "$v" | awk '/^([a-z]|S) / { f = 1; exit } END { exit !f }'
  then
    refuse "a file marked assume-unchanged or skip-worktree in $t"
    return 1
  fi
  if [ "$gd" -ef "$cd_" ]; then
    refuse "git reads $t as no linked worktree"
    return 1
  fi
  # without -z, a newline in a worktree's path would start a line of its
  # own; tr makes each field a line, and such a newline \001
  if ! git --git-dir="$cd_" worktree list --porcelain -z > "$wls"; then
    refuse "git cannot read $cd_"
    return 1
  fi
  wl=$(tr '\n\000' '\001\n' < "$wls")
  b=$(git -C "$t" symbolic-ref -q HEAD) || b=
  # k: a worktree the run does not remove that has the branch checked out,
  # which keeps it
  listed='' locked='' cur='' at='' k='' nlp=''
  while IFS= read -r l; do
    case $l in
      'worktree '*)
        cur='' at=${l#worktree } nlp=''
        # a path holding \001, which stands for a newline here, is no
        # worktree the run removes: the scan refuses a <work> whose path
        # or names hold either
        case $at in
          *"$soh"*) nlp=1 ;;
          *) if [ "$at" -ef "$t" ]; then cur=1 listed=1; fi ;;
        esac
        ;;
      locked*) [ -z "$cur" ] || locked=1 ;;
      "branch $b")
        [ -n "$k" ] || { [ -z "$nlp" ] && ours "$at"; } ||
          k=$(printf '%s\n' "$at" | tr '\001' '?')
        ;;
    esac
  done << EOF
$wl
EOF
  if [ -z "$listed" ]; then
    refuse "$cd_ does not list the worktree $t"
    return 1
  fi
  if [ -n "$locked" ]; then
    refuse "worktree $t is locked"
    return 1
  fi
  held "$t" refs/worktree refs/bisect refs/rewritten || return 1
  # shellcheck disable=SC2086
  pushed "$t" $tips || return 1
  # what HEAD names is deleted with the worktree, so it must be a branch
  case $b in
    '' | refs/heads/*) ;;
    *)
      refuse "the HEAD of $t names $b, which is not a branch"
      return 1
      ;;
  esac
  printf '%s\n%s\n%s\n%s\n%s\n' "$t" "$cd_" "$b" "$h" "$k" >> "$todo"
}

# foreign <path> <why>: the refusal of a repository the scan cannot tell
# is the session's
foreign() {
  [ -z "$alien" ] || return 0
  alien="$1: $2; the script reads no repository it cannot tell is a"
  alien="$alien linked worktree of the session's"
}

# scan: the decision, by file reads alone, of each .git find listed in
# any letter case, and of each directory; the session's worktrees go in
# $owns, the first other repository in $alien, and the scan reads both
# lists whole either way
scan() {
  alien=
  : > "$owns"
  while IFS= read -r p <&3; do
    if [ "${p##*/}" != .git ]; then
      foreign "$p" 'a .git spelled in another case'
      continue
    fi
    e=${p%/.git}
    case ${e#"$r"/} in
      "$e" | */*) foreign "$p" 'a .git not at <work>/<e>'; continue ;;
    esac
    if [ -L "$p" ]; then foreign "$p" 'a symbolic link'; continue; fi
    if [ ! -f "$p" ]; then foreign "$p" 'not a regular file'; continue; fi
    if [ -n "$(find "$p" -prune -links +1)" ]; then
      foreign "$p" 'a .git with more than one link'
      continue
    fi
    if ! line "$p" || [ "${line#gitdir: }" = "$line" ]; then
      foreign "$p" 'no gitdir: line'
      continue
    fi
    if ! from "$e" "${line#gitdir: }"; then
      foreign "$p" "its gitdir does not resolve"
      continue
    fi
    g=$u
    case $g/ in
      "$r"/*) foreign "$p" "its gitdir $g is inside <work>"; continue ;;
    esac
    case ${g%/*} in
      */worktrees) ;;
      *)
        foreign "$p" "its gitdir $g is in no worktrees directory"
        continue
        ;;
    esac
    if [ -L "$g/commondir" ] || [ ! -f "$g/commondir" ] ||
      ! line "$g/commondir" || ! from "$g" "$line" ||
      [ ! "$u/worktrees/${g##*/}" -ef "$g" ]; then
      foreign "$p" "$g/commondir does not name the repository of $g"
      continue
    fi
    case $u/ in
      "$r"/*) foreign "$p" "its repository $u is inside <work>"; continue ;;
    esac
    if [ -L "$g/gitdir" ] || [ ! -f "$g/gitdir" ] || ! line "$g/gitdir" ||
      ! { case $line in /*) [ "$line" -ef "$p" ] ;;
        *) [ "$g/$line" -ef "$p" ] ;; esac; }; then
      foreign "$p" "$g/gitdir does not name it"
      continue
    fi
    printf '%s\n' "$e" >> "$owns"
  done 3< "$list"
  # objects, refs and commondir are tested through the file system, which
  # folds their names as it folds them for git
  while IFS= read -r d <&3; do
    if there "$d/HEAD" &&
      { { there "$d/objects" && there "$d/refs"; } || there "$d/commondir"; }
    then
      foreign "$d" "a git directory's layout"
    fi
  done 3< "$dirs"
}

# record: the next record of $todo, read from descriptor 3
record() {
  IFS= read -r t <&3 && IFS= read -r cd_ <&3 && IFS= read -r b <&3 &&
    IFS= read -r h <&3 && IFS= read -r k <&3
}

# once: whether the record names a branch that no earlier record of the
# loop named, $seen holding those
once() {
  [ -n "$b" ] && [ -n "$h" ] || return 1
  case $nl$seen in
    *"$nl$cd_ $b$nl"*) return 1 ;;
  esac
  seen="$seen$cd_ $b$nl"
}

# remove: the removal of $r, once its checks have passed
remove() {
  if ! mkdir "$r/.sweep-unfinished"; then
    refuse 'cannot write .sweep-unfinished'
    return
  fi
  # left: the branches of the worktrees deregistered so far, n of them
  seen='' left='' n=0
  while record; do
    if ! git --git-dir="$cd_" worktree remove "$t"; then
      why="git worktree remove $t fails; .sweep-unfinished stays"
      case $n in
        0) ;;
        1) why="$why; so does the branch $left" ;;
        *) why="$why; so do the branches $left" ;;
      esac
      refuse "$why"
      return
    fi
    printf 'deregistered: %s\n' "$t"
    if once; then left="$left${left:+, }$b of $cd_" n=$((n + 1)); fi
  done 3< "$todo"
  # the branches go once every worktree is deregistered, so that none is
  # left on a deleted branch
  seen=
  while record; do
    once || continue
    if [ -n "$k" ]; then
      printf 'kept branch: %s of %s, checked out in %s\n' "$b" "$cd_" "$k"
    elif git --git-dir="$cd_" update-ref -d "$b" "$h" 2> /dev/null; then
      git --git-dir="$cd_" config --remove-section "branch.${b#refs/heads/}" \
        2> /dev/null
      printf 'deleted branch: %s of %s\n' "$b" "$cd_"
    else
      printf 'kept branch: %s of %s, its tip moved or git cannot delete it\n' \
        "$b" "$cd_"
    fi
  done 3< "$todo"
  # a read-only directory inside is made writable, and rm tried again
  if rm -rf "${r:?}" 2> /dev/null ||
    { chmod -R u+w "${r:?}" 2> /dev/null; rm -rf "${r:?}"; }; then
    printf 'removed: %s\n' "$r"
  else
    refuse 'rm -rf fails'
  fi
}

sweep() {
  w=$name
  case /$w/ in
    */./* | */../*) refuse 'a . or .. component'; return ;;
  esac
  while [ "${#w}" -gt 1 ] && [ "${w%/}" != "$w" ]; do w=${w%/}; done
  if [ -L "$w" ]; then refuse 'a symbolic link'; return; fi
  if [ ! -e "$w" ]; then printf 'absent: %s\n' "$name"; return; fi
  if [ ! -d "$w" ]; then refuse 'not a directory'; return; fi
  if ! r=$(real "$w"); then refuse 'cannot be resolved'; return; fi
  case $r in
    *"$nl"* | *"$soh"*)
      refuse 'its path holds a newline or \001'
      return
      ;;
  esac
  if [ -z "$rroot" ]; then
    refuse "$root is not a directory the caller owns"
    return
  fi
  # outside the root, r keeps its leading slash, which layout refuses
  if ! layout "${r#"$rroot"/}"; then
    refuse "not <root>/<project>/<session>/scratchpad/<work>, <root>: $rroot"
    return
  fi
  if [ "$r" -ef "${r%/*}/orchestrator" ]; then
    refuse "the session's own files"
    return
  fi
  a=$here
  until [ "$a" -ef "$r" ]; do
    case $a in
      / | '') a=; break ;;
    esac
    a=${a%/*}
    [ -n "$a" ] || a=/
  done
  if [ -n "$a" ]; then refuse 'the current directory, or holds it'; return; fi
  if [ -e "$r/.sweep-unfinished" ] || [ -L "$r/.sweep-unfinished" ]; then
    refuse 'holds .sweep-unfinished, left by a removal that stopped'
    return
  fi
  # each name that is .git in any letter case, then each other directory
  # not below one, which the scan asks the file system about, as git asks
  if ! odd=$(find "$r" \( -name "*$nl*" -o -name "*$soh*" \) -print) ||
    ! kept=$(find "$r" -name 'findings-*.md' -print) ||
    ! find "$r" -iname .git -print -prune > "$list" ||
    ! find "$r" \( -iname .git -prune \) -o -type d -print > "$dirs"; then
    refuse 'find cannot read all of it'
    return
  fi
  if [ -n "$odd" ]; then
    refuse 'holds a name with a newline or \001'
    return
  fi
  if [ -n "$kept" ]; then
    refuse "holds the findings record ${kept%%"$nl"*}, kept elsewhere first"
    return
  fi
  scan
  if [ -n "$alien" ]; then
    refuse "$alien"
    return
  fi
  : > "$todo"
  while IFS= read -r e <&3; do
    tree "$e" || return
  done 3< "$owns"
  if [ -z "$check" ]; then
    remove
    return
  fi
  while record; do
    printf 'would deregister: %s\n' "$t"
  done 3< "$todo"
  seen=
  while record; do
    once || continue
    if [ -n "$k" ]; then
      printf 'would keep branch: %s of %s, checked out in %s\n' "$b" "$cd_" "$k"
    else
      printf 'would delete branch: %s of %s\n' "$b" "$cd_"
    fi
  done 3< "$todo"
  printf 'would remove: %s\n' "$r"
  cat "$owns" >> "$gone"
}

for name in "$@"; do
  sweep
done
exit "$rc"
