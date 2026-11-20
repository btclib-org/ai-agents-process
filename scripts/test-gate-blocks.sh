#!/bin/sh
# What the blocks of *The gates* named below, which run outside the
# sandbox, do with the trees and shells they meet:
#
#   sh scripts/test-gate-blocks.sh [<writing.md>]
#
# From <writing.md>, by default process/writing.md beside this script,
# it takes the fence that defines gated_tree; from *The hooks run on the
# changed files* the fence that empties `peak` and the hooks block, the
# fence that runs pre-commit; the docs build's check; the sandbox's
# hooks gate; the gate lock's fence; and the one for hooks whose run
# carries over. Each comes with the fence just above it where that one
# holds only assignments. Their placeholders become paths of a fixture:
# a repository whose `main` holds `file`, `other`, `-i`, `!`,
# `docs/page.md`, which names `file`, and a gitlink `sub`, whose
# directory holds `inner`, with `HEAD` a commit on it that changes
# `file`, and a larger one, whose `git ls-files -v` fills a pipe's
# buffer. The docs source is `docs`, and the sandbox's command is empty.
# pre-commit is a script of the test's, which records its directory and
# arguments. gated_tree runs under each of sh, bash, zsh and dash on the
# PATH, and the other blocks under bash, `/bin/bash`, which on macOS is
# bash 3.2, and zsh. The noclobber cases also run under sh and dash,
# each where it has arrays, which the hooks block and the sandbox's
# hooks gate use.
# A shell that is missing is skipped, and its line says so. The cases,
# in order:
#
# - gated_tree, clean: it prints `HEAD`'s tree and the merge base.
# - gated_tree, unstaged, untracked, assume-unchanged, skip-worktree:
#   `other` holds a change git diff shows; then a new file `new` is
#   untracked; then `other` holds the change with each bit set on it.
#   It prints nothing, and exits other than 0.
# - gated_tree, awk fails: an awk of the test's, first on the PATH, exits
#   2 in the clean repository. It prints nothing, and exits other than 0.
# - gated_tree, tmp set by its caller: the script that calls it sets
#   `tmp` to a directory, and `other` holds a change git diff shows. It
#   prints nothing, exits other than 0, and the directory is still there.
# - gated_tree, mark: given a file made before, with `cache`, which
#   `.git/info/exclude` names, and `sub/inner` written after it, it
#   prints the tree.
#   Then `file` is written and restored with `cp -p`, which keeps its
#   bytes and its modification time: without the file gated_tree still
#   prints the tree; given the file, it prints nothing, and exits other
#   than 0.
# - gated_tree, pipefail: under `set -o pipefail`, in the larger
#   repository, whose first entry is marked assume-unchanged and
#   changed. It prints nothing, and exits other than 0. Skipped in a
#   shell with no pipefail, as dash.
# - gated_tree, signal: a cp of the test's, first on the PATH, sends
#   TERM to the shell that runs it, once the directory exists. It prints
#   nothing, and exits other than 0.
# - gated_tree, signal in mktemp: a mktemp of the test's makes the
#   directory, prints its name, and sends TERM to its process group,
#   which perl starts for the case. The script that calls gated_tree
#   survives the TERM with `trap : TERM`, so its exit is gated_tree's. It
#   prints nothing, and exits other than 0. Skipped under zsh, which runs
#   the trap before it assigns the name, and where perl is missing.
# - after each gated_tree case, its $TMPDIR is empty.
# - hooks, set -u: the hooks block runs twice under `set -u`, each time
#   with a $TMPDIR of the test's: first with `peak` empty, then with
#   `peak` a script of the test's, which records that it ran and runs the
#   rest. Each exits 0, pre-commit runs in the worktree with
#   `--files ./file`, and only the second runs the script.
# - gate lock: the gate lock's block under `set -u`, its functions a
#   stand-in's, as process/every-role.md's *A rehearsal of a block that
#   takes the gate lock* says, and its next gate a script of the test's.
#   The two `…` lines that stand for the hooks block are replaced by it,
#   and the test fails where they are not there exactly, in order, or
#   where any `…` is left in what it runs.
#   Where pre-commit writes `file` again with the same bytes through a
#   new file, and the next gate writes nothing, both `TREE=` lines name
#   `HEAD`'s tree and the merge base. Where pre-commit writes nothing,
#   and the next gate writes `file` and restores it with `cp -p`, the
#   second `TREE=` line is empty. Each `TREE=` line ends `HEAD=` and
#   `HEAD`'s commit.
# - noclobber: the hooks block, the docs build's check and the sandbox's
#   hooks gate, each run as is and then after `set -C`. Each exits 0
#   both times, prints the same, runs pre-commit with the same
#   arguments, and leaves $TMPDIR empty.
# - carried over: the block for hooks whose run carries over, under
#   `set -u`, with a stand-in that records the slot taken, the gate run
#   and the slot released, and a next gate that exits 0, then 3. It
#   exits 0 and prints two `TREE=` lines naming `HEAD`'s tree, the merge
#   base and `HEAD`, around `EXIT_next=` and the gate's exit.
# - staged, then committed: `file` changed and staged, the carried-over
#   block runs; the change committed, it runs again. Both runs name the
#   same tree and merge base, the first `HEAD` as the parent and the
#   second as the new commit. This commit is the fixture's last.
#
# Each line it prints starts `ok`, `skip` or `FAIL`, and it exits 1 where
# a check failed.
here=$(dirname "$0")
doc=${1:-$here/../process/writing.md}
real_cp=$(command -v cp) || { echo "FAIL: no cp on the PATH"; exit 1; }
tmp=
trap '[ -z "$tmp" ] || rm -rf "$tmp"' EXIT
trap 'exit 1' HUP INT TERM
tmp=$(mktemp -d "${TMPDIR:-/tmp}/test-gate-blocks.XXXXXX") || exit 1
d=$(cd "$tmp" && pwd -P) || exit 1
tmp=$d
fail=0
ok() { echo "ok: $*"; }
no() { echo "FAIL: $*"; fail=1; }

GIT_CONFIG_GLOBAL=$tmp/gitconfig GIT_CONFIG_NOSYSTEM=1
GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@example.invalid
GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@example.invalid
export GIT_CONFIG_GLOBAL GIT_CONFIG_NOSYSTEM GIT_AUTHOR_NAME \
  GIT_AUTHOR_EMAIL GIT_COMMITTER_NAME GIT_COMMITTER_EMAIL
: > "$GIT_CONFIG_GLOBAL"

wt=$tmp/wt
git init -q -b main "$wt" &&
  printf 'a\n' > "$wt/file" && printf 'o\n' > "$wt/other" &&
  printf 'h\n' > "$wt/-i" && printf 'h\n' > "$wt/!" &&
  mkdir "$wt/sub" "$wt/docs" && printf 's\n' > "$wt/sub/inner" &&
  printf 'see file\n' > "$wt/docs/page.md" &&
  git -C "$wt" add file other ./-i ./! docs/page.md &&
  git -C "$wt" update-index --add --cacheinfo \
    160000,0123456789012345678901234567890123456789,sub &&
  git -C "$wt" commit -q -m base &&
  base=$(git -C "$wt" rev-parse HEAD) &&
  printf 'b\n' > "$wt/file" && git -C "$wt" commit -q -am change &&
  tree=$(git -C "$wt" rev-parse 'HEAD^{tree}') &&
  head=$(git -C "$wt" rev-parse HEAD) &&
  mkdir -p "$wt/.git/info" && printf 'cache\n' >> "$wt/.git/info/exclude" ||
  exit 1
# A larger index, whose `git ls-files -v` fills a pipe's buffer, its
# first entry marked assume-unchanged and changed
big=$tmp/big
git init -q -b main "$big" &&
  awk 'BEGIN { for (i = 0; i < 6000; i++) printf "f%04d-of-a-larger-index\n", i }' |
  (cd "$big" && xargs touch) && git -C "$big" add -A &&
  git -C "$big" commit -q -m big && printf 'x\n' > "$big/f0000-of-a-larger-index" &&
  git -C "$big" update-index --assume-unchanged f0000-of-a-larger-index || exit 1

# The shell fence that, with the fence just above it where that one holds
# only assignments, matches $1: the two, their two-space indent removed,
# and their placeholders filled.
block() {
  awk -v re="$1" '/^ *```shell$/ { b = ""; on = 1; only = 1; next }
    on && /^ *```$/ { if ((a b) ~ re) { printf "%s", a b; exit }
      a = only ? b : ""; on = 0; next }
    on { sub(/^  /, ""); b = b $0 "\n"
      if ($0 !~ /^([A-Za-z_][A-Za-z0-9_]*=|set -- )/) only = 0; next }
    /[^ ]/ { a = "" }' "$doc" |
    sed -e "s|<wt>|$wt|g" -e "s|<base>|$base|g" -e "s|<sha>|$head|g" \
      -e "s|<docs source>|docs|g" \
      -e "s|uvx pre-commit run|sh $tmp/pre-commit.sh|" \
      -e "s|uv run pre-commit run|sh $tmp/pre-commit.sh|"
}
block 'gated_tree[(][)]' > "$tmp/gated.sh"
{ cat "$tmp/gated.sh"; echo gated_tree; } > "$tmp/gated-run.sh"
{ cat "$tmp/gated.sh"; printf "gated_tree '%s'\n" "$tmp/mark"; } \
  > "$tmp/gated-mark.sh"
{ cat "$tmp/gated.sh"; printf "tmp='%s'\ngated_tree\n" "$tmp/keep"; } \
  > "$tmp/gated-tmp.sh"
{ cat "$tmp/gated.sh"; printf 'trap : TERM\ngated_tree\n'; } > "$tmp/gated-sig.sh"
grep -q 'gated_tree()' "$tmp/gated.sh" ||
  { no "no block in $doc defines gated_tree"; exit 1; }
block '^peak=[(][)]\n$' > "$tmp/empty.sh"
grep -qx 'peak=()' "$tmp/empty.sh" ||
  { no "no block in $doc empties peak"; exit 1; }
block 'uvx pre-commit run' > "$tmp/hooks.sh"
grep -q "sh $tmp/pre-commit.sh" "$tmp/hooks.sh" ||
  { no "no hooks block in $doc"; exit 1; }
block 'ls-files --error-unmatch' > "$tmp/docs.sh"
grep -qx 'src=docs' "$tmp/docs.sh" ||
  { no "no docs build's check in $doc"; exit 1; }
block 'uv run pre-commit run "[$][{]files' > "$tmp/sbx-hooks.sh"
grep -q "sh $tmp/pre-commit.sh" "$tmp/sbx-hooks.sh" ||
  { no "no sandbox's hooks gate in $doc"; exit 1; }
# Where it is missing, its cases are left out, and the test fails
block 'HEAD[)]"\n *mark=[$]' > "$tmp/carried.sh"
grep -q 'gate_take' "$tmp/carried.sh" ||
  no "no block in $doc for hooks whose run carries over"
block 'gate_take ' > "$tmp/lock.sh"
grep -q 'gate_take' "$tmp/lock.sh" ||
  { no "no gate lock block in $doc"; exit 1; }
# The check of *A rehearsal of a block that takes the gate lock*, whose
# control is each block as extracted
[ "$(grep -cw -e gate-lock -e PROCESS "$tmp/lock.sh")" -ne 0 ] ||
  { no "the gate lock's block names neither gate-lock nor PROCESS"; exit 1; }
if grep -q 'gate_take' "$tmp/carried.sh" &&
  [ "$(grep -cw -e gate-lock -e PROCESS "$tmp/carried.sh")" -eq 0 ]; then
  no "the carried-over block names neither gate-lock nor PROCESS"; exit 1
fi

mkdir "$tmp/bin" "$tmp/bin-mktemp" "$tmp/bin-awk" "$tmp/t" || exit 1
printf '#!/bin/sh\nexit 2\n' > "$tmp/bin-awk/awk"
cat > "$tmp/bin/cp" <<EOF
#!/bin/sh
kill -TERM "\$PPID"
exec "$real_cp" "\$@"
EOF
# shellcheck disable=SC2016
printf '{ pwd -P; printf "%%s\\n" "$@"; } > %s/pre-commit-args\n' \
  "$tmp" > "$tmp/pre-commit.sh"
# shellcheck disable=SC2016
printf ': > %s/peak-ran\nexec "$@"\n' "$tmp" > "$tmp/peak.sh"
real_mktemp=$(command -v mktemp) || { echo "FAIL: no mktemp"; exit 1; }
cat > "$tmp/bin-mktemp/mktemp" <<EOF
#!/bin/sh
"$real_mktemp" "\$@" || exit 1
kill -TERM 0
EOF
chmod +x "$tmp/bin/cp" "$tmp/bin-mktemp/mktemp" "$tmp/bin-awk/awk" || exit 1

# Runs gated_tree under shell $1 with PATH $2, from script $3 where
# given, after the command words that follow; sets out and rc.
gated() {
  _s=$1 _p=$2 _r=${3:-$tmp/gated-run.sh}
  shift 2
  [ "$#" -eq 0 ] || shift
  rm -rf "${tmp:?}/t" && mkdir "$tmp/t" || exit 1
  out=$(PATH=$_p TMPDIR=$tmp/t "$@" "$_s" "$_r" 2> /dev/null)
  rc=$?
}
# Checks that $TMPDIR of the gated_tree case $1 is empty.
emptied() {
  left=$(find "$tmp/t" -mindepth 1 -maxdepth 1 -exec basename {} \;)
  if [ -z "$left" ]; then ok "$1: \$TMPDIR is empty"
  else no "$1: \$TMPDIR holds $(printf '%s' "$left" | tr '\n' ' ')"; fi
}

# Reads the TREE= lines of $1: sets nl, their count, t1 and t2, what
# gated_tree printed in each, and h1 and h2, the HEAD each names.
lines() {
  _l=$(printf '%s\n' "$1" | grep '^TREE=')
  nl=$(printf '%s\n' "$1" | grep -c '^TREE=')
  t1=$(printf '%s\n' "$_l" | sed -n '1s/^TREE=\(.*\) HEAD=.*$/\1/p')
  t2=$(printf '%s\n' "$_l" | sed -n '2s/^TREE=\(.*\) HEAD=.*$/\1/p')
  h1=$(printf '%s\n' "$_l" | sed -n '1s/^TREE=.* HEAD=//p')
  h2=$(printf '%s\n' "$_l" | sed -n '2s/^TREE=.* HEAD=//p')
}

perl=$(command -v perl)
for s in sh bash zsh dash; do
  if ! command -v "$s" > /dev/null; then
    echo "skip: gated_tree under $s, which is missing"
    continue
  fi
  gated "$s" "$PATH"
  if [ "$rc" -eq 0 ] && [ "$out" = "$tree $base" ]; then
    ok "$s, clean: gated_tree prints HEAD's tree and the merge base"
  else no "$s, clean: exit $rc, gated_tree prints '$out'"; fi
  emptied "$s, clean"
  for c in unstaged untracked assume-unchanged skip-worktree; do
    if [ "$c" = untracked ]; then : > "$wt/new"
    else printf 'x\n' > "$wt/other"; fi
    case $c in unstaged | untracked) ;; *)
      git -C "$wt" update-index "--$c" other || exit 1 ;; esac
    gated "$s" "$PATH"
    if [ "$rc" -ne 0 ] && [ -z "$out" ]; then
      ok "$s, $c: gated_tree prints nothing and exits $rc"
    else no "$s, $c: exit $rc, gated_tree prints '$out'"; fi
    emptied "$s, $c"
    case $c in unstaged | untracked) ;; *)
      git -C "$wt" update-index "--no-$c" other || exit 1 ;; esac
    rm -f "$wt/new" && git -C "$wt" checkout -q -- other || exit 1
  done
  gated "$s" "$tmp/bin-awk:$PATH"
  if [ "$rc" -ne 0 ] && [ -z "$out" ]; then
    ok "$s, awk fails: gated_tree prints nothing and exits $rc"
  else no "$s, awk fails: exit $rc, gated_tree prints '$out'"; fi
  emptied "$s, awk fails"
  mkdir -p "$tmp/keep" && printf 'x\n' > "$wt/other" || exit 1
  gated "$s" "$PATH" "$tmp/gated-tmp.sh"
  if [ "$rc" -ne 0 ] && [ -z "$out" ] && [ -d "$tmp/keep" ]; then
    ok "$s, tmp set by its caller: gated_tree prints nothing, exits $rc" \
      "and leaves the caller's directory"
  else no "$s, tmp set by its caller: exit $rc, gated_tree prints '$out'," \
    "the caller's directory is $([ -d "$tmp/keep" ] || printf 'not ')there"; fi
  emptied "$s, tmp set by its caller"
  git -C "$wt" checkout -q -- other || exit 1
  # The sleep makes each write after the mark newer than it, where the
  # file system counts whole seconds.
  : > "$tmp/mark" && sleep 1 && : > "$wt/cache" &&
    printf 's\n' >> "$wt/sub/inner" || exit 1
  gated "$s" "$PATH" "$tmp/gated-mark.sh"
  if [ "$rc" -eq 0 ] && [ "$out" = "$tree $base" ]; then
    ok "$s, mark, ignored file and sub/inner written: gated_tree prints" \
      "the tree"
  else no "$s, mark, ignored file and sub/inner written: exit $rc," \
    "prints '$out'"; fi
  emptied "$s, mark, ignored file and sub/inner written"
  "$real_cp" -p "$wt/file" "$tmp/saved" && printf 'x\n' > "$wt/file" &&
    "$real_cp" -p "$tmp/saved" "$wt/file" || exit 1
  gated "$s" "$PATH"
  if [ "$rc" -eq 0 ] && [ "$out" = "$tree $base" ]; then
    ok "$s, written and restored, no mark: gated_tree prints the tree"
  else no "$s, written and restored, no mark: exit $rc, prints '$out'"; fi
  emptied "$s, written and restored, no mark"
  gated "$s" "$PATH" "$tmp/gated-mark.sh"
  if [ "$rc" -ne 0 ] && [ -z "$out" ]; then
    ok "$s, written and restored, mark: gated_tree prints nothing," \
      "exits $rc"
  else no "$s, written and restored, mark: exit $rc, prints '$out'"; fi
  emptied "$s, written and restored, mark"
  rm -f "$wt/cache" "$tmp/mark" "$tmp/saved" || exit 1
  if "$s" -c 'set -o pipefail' 2> /dev/null; then
    { cat "$tmp/gated.sh"
      printf 'wt=%s base=HEAD\nset -o pipefail\ngated_tree\n' "$big"; } \
      > "$tmp/gated-big.sh"
    gated "$s" "$PATH" "$tmp/gated-big.sh"
    if [ "$rc" -ne 0 ] && [ -z "$out" ]; then
      ok "$s, pipefail: gated_tree prints nothing and exits $rc"
    else no "$s, pipefail: exit $rc, gated_tree prints '$out'"; fi
    emptied "$s, pipefail"
  else echo "skip: $s, pipefail: $s has no pipefail"; fi
  gated "$s" "$tmp/bin:$PATH"
  if [ "$rc" -ne 0 ] && [ -z "$out" ]; then
    ok "$s, signal: gated_tree prints nothing and exits $rc"
  else no "$s, signal: exit $rc, gated_tree prints '$out'"; fi
  emptied "$s, signal"
  if [ "$s" = zsh ]; then
    echo "skip: zsh, signal in mktemp: zsh runs the trap before it" \
      "assigns the name, as process/writing.md says"
  elif [ -z "$perl" ]; then
    echo "skip: $s, signal in mktemp: no perl to start a process group"
  else
    gated "$s" "$tmp/bin-mktemp:$PATH" "$tmp/gated-sig.sh" "$perl" -e \
      'setpgrp(0, 0); exec @ARGV or die'
    if [ "$rc" -ne 0 ] && [ -z "$out" ]; then
      ok "$s, signal in mktemp: gated_tree prints nothing and exits $rc"
    else no "$s, signal in mktemp: exit $rc, gated_tree prints '$out'"; fi
    emptied "$s, signal in mktemp"
  fi
done

for s in bash /bin/bash zsh; do
  if ! command -v "$s" > /dev/null; then
    echo "skip: the hooks block under $s, which is missing"
    continue
  fi
  n=$(printf '%s' "$s" | tr / _)
  for c in empty set; do
    rm -f "$tmp/pre-commit-args" "$tmp/peak-ran"
    { echo 'set -u'; cat "$tmp/empty.sh"
      [ "$c" = empty ] || echo "peak=(sh $tmp/peak.sh)"
      cat "$tmp/hooks.sh"; } > "$tmp/hooks-$n-$c.sh"
    TMPDIR=$tmp/t "$s" "$tmp/hooks-$n-$c.sh" > "$tmp/hooks-$n-$c.log" 2>&1
    rc=$?
    got=$(cat "$tmp/pre-commit-args" 2> /dev/null)
    if [ "$c" = set ]; then want=yes; else want=no; fi
    if [ -e "$tmp/peak-ran" ]; then ran=yes; else ran=no; fi
    if [ "$rc" -eq 0 ] && [ "$got" = "$(printf '%s\n' "$wt" --files ./file)" ] &&
      [ "$ran" = "$want" ]; then
      ok "$s, set -u, peak $c: pre-commit ran with --files ./file," \
        "the peak script ran: $ran"
    else no "$s, set -u, peak $c: exit $rc, the peak script ran: $ran," \
      "pre-commit ran with: $(printf '%s' "$got" | tr '\n' ' ')" \
      "$(tr '\n' ' ' < "$tmp/hooks-$n-$c.log")"; fi
  done
done

# The gate lock's stand-in, and the hooks and the next gate of each case:
# `rewrite` writes `file` again through a new file, and `restore`, a
# second after the mark, writes it and restores it
# shellcheck disable=SC2016
printf '%s\n' 'gate_take() { :; }' 'gate_wait() { :; }' \
  'gate_release() { :; }' \
  'gate_peak() { shift 2; [ "$1" != timeout ] || shift 4; "$@"; }' \
  > "$tmp/slots.sh"
printf 'cat file > .file.new && mv .file.new file\n' > "$tmp/rewrite.sh"
: > "$tmp/next-rewrite.sh"
printf "sleep 1 && cp -p '%s' '%s' && echo x > '%s' && cp -p '%s' '%s'\\n" \
  "$wt/file" "$tmp/saved" "$wt/file" "$tmp/saved" "$wt/file" \
  > "$tmp/next-restore.sh"
for c in rewrite restore; do
  if [ "$c" = rewrite ]; then h=rewrite.sh; else h=pre-commit.sh; fi
  sed "s|sh $tmp/pre-commit.sh|sh $tmp/$h|" "$tmp/hooks.sh" \
    > "$tmp/hooks-lock-$c.sh"
  # the two lines that stand for the hooks block, exactly and in order;
  # $tmp/lacks-$c is written where they are not
  awk -v h="$tmp/hooks-lock-$c.sh" -v bad="$tmp/lacks-$c" \
    -v a='  … *The hooks run on the changed files*: its fence of values, and …' \
    -v b='  … its fence that runs pre-commit, which sets rc …' '
    $0 == a && !s { while ((getline l < h) > 0) print l; s = 1; next }
    s == 1 { s = $0 == b ? 2 : 3; if (s == 2) next }
    { print }
    END { if (s != 2) print s > bad }' "$tmp/lock.sh" |
    sed -e "s|^\. .*/scripts/gate-lock\.sh\"\$|. $tmp/slots.sh|" \
      -e 's|^secs=<seconds>$|secs=60|' -e 's|^gate=<next gate>$|gate=next|' \
      -e "s|[^ ]* the next gate [^ ]*|sh $tmp/next-$c.sh|" \
      > "$tmp/lock-$c.sh"
  if [ -e "$tmp/lacks-$c" ]; then
    no "gate lock, $c: the lock fence lacks the hooks block's two lines"
    exit 1
  fi
  if grep -q '…' "$tmp/lock-$c.sh"; then
    no "gate lock, $c: a line of $doc's gate lock fence still holds …"; exit 1
  fi
  if [ "$(grep -cw -e gate-lock -e PROCESS "$tmp/lock-$c.sh")" -ne 0 ] ||
    ! grep -q "sh $tmp/next-$c.sh" "$tmp/lock-$c.sh" ||
    ! grep -q "sh $tmp/$h" "$tmp/lock-$c.sh"; then
    no "gate lock, $c: the stand-in block is not the one built"; exit 1
  fi
  { echo 'set -u'; cat "$tmp/gated.sh" "$tmp/lock-$c.sh"; } \
    > "$tmp/lock-run-$c.sh"
done
for s in bash /bin/bash zsh; do
  if ! command -v "$s" > /dev/null; then
    echo "skip: the gate lock's block under $s, which is missing"
    continue
  fi
  for c in rewrite restore; do
    i=$(ls -i "$wt/file") || exit 1
    gated "$s" "$PATH" "$tmp/lock-run-$c.sh"
    lines "$out"
    if [ "$c" = rewrite ]; then
      if [ "$(ls -i "$wt/file")" != "$i" ] && [ "$nl" -eq 2 ] &&
        [ "$t1" = "$tree $base" ] && [ "$t2" = "$tree $base" ] &&
        [ "$h1" = "$head" ] && [ "$h2" = "$head" ] &&
        printf '%s\n' "$out" | grep -qx 'EXIT_next=0'; then
        ok "$s, gate lock, hooks write file with the same bytes:" \
          "both TREE= lines name the tree and HEAD"
      else no "$s, gate lock, hooks write file with the same bytes:" \
        "exit $rc, prints $(printf '%s' "$out" | tr '\n' ' ')"; fi
    elif [ "$nl" -eq 2 ] && [ "$t1" = "$tree $base" ] && [ -z "$t2" ] &&
      [ "$h1" = "$head" ] && [ "$h2" = "$head" ] &&
      printf '%s\n' "$out" | grep -qx 'EXIT_next=0'; then
      ok "$s, gate lock, next gate writes and restores file:" \
        "the second TREE= line is empty, both name HEAD"
    else no "$s, gate lock, next gate writes and restores file:" \
      "exit $rc, prints $(printf '%s' "$out" | tr '\n' ' ')"; fi
    emptied "$s, gate lock, $c"
  done
done

for s in sh bash /bin/bash zsh dash; do
  if ! command -v "$s" > /dev/null; then
    echo "skip: noclobber under $s, which is missing"
    continue
  elif ! "$s" -c 'a=()' 2> /dev/null; then
    echo "skip: noclobber under $s, which has no arrays"
    continue
  fi
  n=$(printf '%s' "$s" | tr / _)
  for b in hooks docs sbx-hooks; do
    for c in plain noclobber; do
      { [ "$c" = plain ] || echo 'set -C'
        [ "$b" = docs ] || cat "$tmp/empty.sh"
        cat "$tmp/$b.sh"; } > "$tmp/nc-$n-$b-$c.sh"
      rm -f "$tmp/pre-commit-args"
      gated "$s" "$PATH" "$tmp/nc-$n-$b-$c.sh"
      got="exit $rc, prints '$out', pre-commit ran with:"
      got="$got '$(cat "$tmp/pre-commit-args" 2> /dev/null)'"
      [ "$c" = noclobber ] || { want=$got; want_rc=$rc; }
      emptied "$s, $b, $c"
    done
    if [ "$want_rc" -eq 0 ] && [ "$got" = "$want" ]; then
      ok "$s, $b, noclobber: exit 0, as without it, the same output"
    else no "$s, $b: without noclobber $(printf '%s' "$want" | tr '\n' ' ')," \
      "with it $(printf '%s' "$got" | tr '\n' ' ')"; fi
  done
done

# The carried-over block, where the test found it: its stand-in records
# the slot and the gate, and its next gate exits 0 or 3
# shellcheck disable=SC2016
printf '%s\n' "gate_take() { echo take >> '$tmp/slot-log'; }" \
  'gate_wait() { :; }' "gate_release() { echo release >> '$tmp/slot-log'; }" \
  "gate_peak() { echo \"peak \$1\" >> '$tmp/slot-log'; shift 2" \
  '  [ "$1" != timeout ] || shift 4; "$@"; }' > "$tmp/slots-log.sh"
for c in 0 3; do
  printf 'exit %s\n' "$c" > "$tmp/next-$c.sh"
  { echo 'set -u'; cat "$tmp/gated.sh"
    sed -e "s|^\. .*/scripts/gate-lock\.sh\"\$|. $tmp/slots-log.sh|" \
      -e 's|^secs=<seconds>$|secs=60|' -e 's|^gate=<next gate>$|gate=next|' \
      -e "s|[^ ]* the next gate [^ ]*|sh $tmp/next-$c.sh|" "$tmp/carried.sh"
  } > "$tmp/carried-$c.sh"
done
# Runs the carried-over block whose gate exits $2 under shell $1; sets
# out, rc and slot
carried() {
  rm -f "$tmp/slot-log"
  gated "$1" "$PATH" "$tmp/carried-$2.sh"
  slot=$(cat "$tmp/slot-log" 2> /dev/null)
}
if grep -q 'gate_take' "$tmp/carried.sh"; then
  if [ "$(grep -cw -e gate-lock -e PROCESS "$tmp/carried-0.sh")" -ne 0 ] ||
    ! grep -q "sh $tmp/next-0.sh" "$tmp/carried-0.sh"; then
    no "carried over: the stand-in block is not the one built"; exit 1
  fi
  for s in bash /bin/bash zsh; do
    if ! command -v "$s" > /dev/null; then
      echo "skip: the carried-over block under $s, which is missing"
      continue
    fi
    for c in 0 3; do
      carried "$s" "$c"
      if [ "$rc" -eq 0 ] && [ "$out" = "$(printf '%s\n' \
        "TREE=$tree $base HEAD=$head" "EXIT_next=$c" \
        "TREE=$tree $base HEAD=$head")" ] &&
        [ "$slot" = "$(printf '%s\n' take 'peak next' release)" ]; then
        ok "$s, carried over, next gate exits $c: EXIT_next=$c between" \
          "two TREE= lines naming the tree and HEAD, in a slot released"
      else no "$s, carried over, next gate exits $c: exit $rc, prints" \
        "$(printf '%s' "$out" | tr '\n' ' '), the slot:" \
        "$(printf '%s' "$slot" | tr '\n' ' ')"; fi
      emptied "$s, carried over, next gate exits $c"
    done
  done

  printf 'c\n' > "$wt/file" && git -C "$wt" add file || exit 1
  for s in bash /bin/bash zsh; do
    command -v "$s" > /dev/null || continue
    n=$(printf '%s' "$s" | tr / _)
    carried "$s" 0
    printf '%s\n' "$out" > "$tmp/staged-$n"
  done
  git -C "$wt" commit -q -m staged && new=$(git -C "$wt" rev-parse HEAD) ||
    exit 1
  for s in bash /bin/bash zsh; do
    if ! command -v "$s" > /dev/null; then
      echo "skip: staged, then committed, under $s, which is missing"
      continue
    fi
    n=$(printf '%s' "$s" | tr / _)
    lines "$(cat "$tmp/staged-$n")"
    st1=$t1 st2=$t2 sh1=$h1 sh2=$h2
    carried "$s" 0
    lines "$out"
    if [ -n "$st1" ] && [ "$st1" = "$st2" ] && [ "$t1" = "$st1" ] &&
      [ "$t2" = "$st1" ] && [ "$sh1" = "$head" ] && [ "$sh2" = "$head" ] &&
      [ "$h1" = "$new" ] && [ "$h2" = "$new" ]; then
      ok "$s, staged, then committed: the same tree and merge base," \
        "HEAD the parent, then the commit"
    else no "$s, staged, then committed: staged run prints" \
      "$(tr '\n' ' ' < "$tmp/staged-$n"), committed run prints" \
      "$(printf '%s' "$out" | tr '\n' ' ')"; fi
  done
fi
exit "$fail"
