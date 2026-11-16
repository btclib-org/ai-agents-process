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
# - it has a .git, or a HEAD beside objects and refs, at its top, as a
#   worktree or a repository would: a piece of work's repositories sit
#   inside it;
# - it holds .sweep-unfinished, of any kind, which a failed
#   `git worktree remove` leaves (below);
# - find cannot read all of it, or it holds a name with a newline;
# - it holds a git repository that git cannot read as one;
# - it holds a worktree with an uncommitted change, an untracked file that
#   is not ignored, or a file marked assume-unchanged or skip-worktree,
#   whose change git status does not show;
# - it holds a commit that no ref `git ls-remote origin` prints reaches,
#   among the refs whose objects the repository holds, or origin cannot be
#   read while it holds a commit at all. A ref whose commit the repository
#   does not hold proves nothing, as where origin moved on to a commit
#   made elsewhere, and a remote-tracking ref proves nothing, since it
#   outlives the branch. The commits read are, for a clone or a bare
#   repository, HEAD and every ref but the remote-tracking ones; for a
#   linked worktree, HEAD and its own refs, refs/worktree, refs/bisect and
#   refs/rewritten, the others being its repository's. A commit that only
#   a reflog or a pseudo-ref such as ORIG_HEAD holds is not read;
# - one of those refs holds an object that is not a commit or a tag of one;
# - it holds a repository with a worktree outside the directory;
# - it holds a git directory that is neither named .git nor bare, as a
#   clone's made with --separate-git-dir, whose worktree the script does
#   not look for, or a linked worktree's git directory that is not in the
#   worktrees directory of a bare repository it holds;
# - one of its linked worktrees is locked, or its repository does not list
#   it.
#
# The repositories read are found by each .git, of any kind, and each
# HEAD, of any kind, that `git --git-dir` opens as a git directory. A
# HEAD git does not open is passed over, unless objects and refs, or a
# commondir file, sit beside it.
#
# Nothing is removed before every check of the directory has passed. Then
# the script makes the directory <work>/.sweep-unfinished with mkdir,
# which follows no symbolic link; <work> being no worktree, no worktree
# it removes holds it. It removes each linked worktree with its
# repository's `git worktree remove`, so that the repository keeps no
# entry for it, deletes the worktree's branch with `git update-ref -d` at
# the tip that was checked, and removes the directory. A branch whose tip
# moved meanwhile, or that git cannot delete, is kept and printed as
# `kept branch:`, and the directory still goes. Where
# `git worktree remove` fails, the directory is refused and keeps
# .sweep-unfinished, so that every later run refuses it until a person
# has read it and removed .sweep-unfinished. Where rm -rf fails, the
# directory is refused, and what it left had passed every check. A
# worktree whose .git file is gone is not found, and its repository keeps
# an entry for it, which `git worktree prune` clears.
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

root=${SWEEP_ROOT:-/tmp/claude-$(id -u)}
# resolved, and owned by the caller: find prints it only then
if ! rroot=$(real "$root") ||
  [ -z "$(find "$rroot" -prune -user "$(id -u)")" ]; then
  rroot=
fi
here=$(env pwd -P)
list=$(mktemp) || exit 2
todo=$(mktemp) || exit 2
trap 'rm -f "${list:?}" "${todo:?}"' EXIT
trap 'exit 1' INT TERM
nl='
'
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

# own <repo>: the checks of a repository that is not a linked worktree
own() {
  o=$1
  if ! wl=$(git -C "$o" worktree list --porcelain); then
    refuse "git cannot read $o"
    return 1
  fi
  while IFS= read -r l; do
    case $l in
      'worktree '*) p=${l#worktree } ;;
      *) continue ;;
    esac
    # a worktree whose directory is gone leaves only a stale entry
    rp=$(real "$p") || continue
    case $rp/ in
      "$r"/*) ;;
      *) refuse "$o has a worktree outside it: $rp"; return 1 ;;
    esac
  done << EOF
$wl
EOF
  held "$o" || return 1
  # word splitting of $tips is meant: one commit per word
  # shellcheck disable=SC2086
  pushed "$o" $tips
}

# tree <dir>: the checks of the worktree that <dir>/.git makes <dir>; a
# linked one goes in $todo, to be removed with git worktree remove
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
    own "$t"
    return
  fi
  if ! wl=$(git --git-dir="$cd_" worktree list --porcelain); then
    refuse "git cannot read $cd_"
    return 1
  fi
  listed='' locked='' cur=''
  while IFS= read -r l; do
    case $l in
      'worktree '*)
        cur=
        if [ "${l#worktree }" -ef "$t" ]; then cur=1 listed=1; fi
        ;;
      locked*) [ -z "$cur" ] || locked=1 ;;
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
  b=$(git -C "$t" symbolic-ref -q HEAD) || b=
  printf '%s\n%s\n%s\n%s\n' "$t" "$cd_" "$b" "$h" >> "$todo"
}

# remove: the removal of $r, once its checks have passed
remove() {
  if ! mkdir "$r/.sweep-unfinished"; then
    refuse 'cannot write .sweep-unfinished'
    return
  fi
  while IFS= read -r t <&3 && IFS= read -r cd_ <&3 &&
    IFS= read -r b <&3 && IFS= read -r h <&3; do
    if ! git --git-dir="$cd_" worktree remove "$t"; then
      refuse "git worktree remove $t fails; .sweep-unfinished stays"
      return
    fi
    printf 'deregistered: %s\n' "$t"
    [ -n "$b" ] && [ -n "$h" ] || continue
    if git --git-dir="$cd_" update-ref -d "$b" "$h" 2> /dev/null; then
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
  if ! find "$r" \( -name .git -print -prune \) -o \
    \( -name HEAD -print \) -o \( -name "*$nl*" -print \) > "$list"
  then
    refuse 'find cannot read all of it'
    return
  fi
  # a name with a newline prints a line that ends in neither /.git nor /HEAD
  while IFS= read -r p <&3; do
    case $p in
      */.git | */HEAD) ;;
      *) refuse 'holds a name with a newline'; return ;;
    esac
  done 3< "$list"
  : > "$todo"
  while IFS= read -r p <&3; do
    case $p in
      "$r/.git" | "$r/HEAD")
        if [ "$p" = "$r/.git" ] || { [ -d "$r/objects" ] && [ -d "$r/refs" ]; }
        then
          refuse 'a .git, or a HEAD beside objects and refs, at its top'
          return
        fi
        ;;
    esac
    case $p in
      */.git) tree "${p%/.git}" || return ;;
      */HEAD)
        d=${p%/HEAD}
        # a git directory outside any .git, which find pruned above
        if ! g=$(git --git-dir="$d" rev-parse --absolute-git-dir \
          2> /dev/null); then
          if [ -d "$d/objects" ] && [ -d "$d/refs" ] ||
            [ -e "$d/commondir" ]; then
            refuse "git cannot read $d"
            return
          fi
          continue
        fi
        if [ ! "$g" -ef "$d" ] || ! c=$(git --git-dir="$d" rev-parse \
          --path-format=absolute --git-common-dir) || ! bare=$(git \
          --git-dir="$d" rev-parse --is-bare-repository); then
          refuse "git cannot read $d"
          return
        fi
        if [ ! "$c" -ef "$d" ]; then
          # covered where its repository, bare and held here, is read
          case ${d%/worktrees/*}/ in
            "$r"/*) [ "${d%/worktrees/*}" -ef "$c" ] && [ -e "$c/HEAD" ] &&
              continue ;;
          esac
          refuse "$d is the git directory of a worktree of $c"
          return
        fi
        if [ "$bare" != true ]; then
          refuse "$d is a git directory whose worktree is not found"
          return
        fi
        own "$d" || return
        ;;
    esac
  done 3< "$list"
  if [ -z "$check" ]; then
    remove
    return
  fi
  while IFS= read -r t <&3 && IFS= read -r cd_ <&3 &&
    IFS= read -r b <&3 && IFS= read -r h <&3; do
    printf 'would deregister: %s\n' "$t"
    [ -z "$b" ] || printf 'would delete branch: %s of %s\n' "$b" "$cd_"
  done 3< "$todo"
  printf 'would remove: %s\n' "$r"
}

for name in "$@"; do
  sweep
done
exit "$rc"
