#!/bin/sh
# What two blocks of *The gates* that run outside the sandbox do with
# the trees and shells they meet:
#
#   sh scripts/test-gate-blocks.sh [<writing.md>]
#
# From <writing.md>, by default process/writing.md beside this script,
# it takes the block that defines gated_tree, and the hooks block of
# *The hooks run on the changed files* with the block before it, which
# empties `peak`. Their placeholders become paths of a fixture: a
# repository whose `main` holds `file` and `other`, with `HEAD` a commit
# on it that changes `file`. pre-commit is a script of the test's, which
# records its directory and arguments. gated_tree runs under each of
# sh, bash, zsh and dash on the PATH, and the hooks block, which needs
# arrays, under bash, `/bin/bash`, which on macOS is bash 3.2, and zsh.
# A shell that is missing is skipped, and its line says so. The cases,
# in order:
#
# - gated_tree, clean: it prints `HEAD`'s tree and the merge base.
# - gated_tree, unstaged, assume-unchanged, skip-worktree: `other`
#   holds a change git diff shows, then the same change with each bit
#   set on `other`. It prints nothing, and exits other than 0.
# - gated_tree, signal: a cp of the test's, first on the PATH, sends
#   TERM to the shell that runs it, once the directory exists. It prints
#   nothing.
# - after each gated_tree case, its $TMPDIR is empty.
# - hooks, set -u: the hooks block runs under `set -u`, with `peak`
#   empty, then with `peak` a script of the test's, which records that
#   it ran and runs the rest. Each exits 0, pre-commit runs in the
#   worktree with `--files ./file`, and only the second runs the script.
#
# Each line it prints starts `ok`, `skip` or `FAIL`, and it exits 1 where
# a check failed.
here=$(dirname "$0")
doc=${1:-$here/../process/writing.md}
real_cp=$(command -v cp) || { echo "FAIL: no cp on the PATH"; exit 1; }
tmp=$(mktemp -d "${TMPDIR:-/tmp}/test-gate-blocks.XXXXXX") || exit 1
trap 'rm -rf "${tmp:?}"' EXIT
trap 'exit 1' HUP INT TERM
tmp=$(cd "$tmp" && pwd -P) || exit 1
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
  git -C "$wt" add file other && git -C "$wt" commit -q -m base &&
  base=$(git -C "$wt" rev-parse HEAD) &&
  printf 'b\n' > "$wt/file" && git -C "$wt" commit -q -am change &&
  tree=$(git -C "$wt" rev-parse 'HEAD^{tree}') || exit 1

# The shell fence whose lines match $1, its two-space indent removed, and
# its placeholders filled.
block() {
  awk -v re="$1" '/^ *```shell$/ { b = ""; on = 1; next }
    on && /^ *```$/ { if (b ~ re) { printf "%s", b; exit }
      on = 0; next }
    on { sub(/^  /, ""); b = b $0 "\n" }' "$doc" |
    sed -e "s|<wt>|$wt|g" -e "s|<base>|$base|g" \
      -e "s|uvx pre-commit run|sh $tmp/pre-commit.sh|"
}
block 'gated_tree[(][)]' > "$tmp/gated.sh"
{ cat "$tmp/gated.sh"; echo gated_tree; } > "$tmp/gated-run.sh"
grep -q 'gated_tree()' "$tmp/gated.sh" ||
  { no "no block in $doc defines gated_tree"; exit 1; }
block '^peak=[(][)]\n$' > "$tmp/empty.sh"
grep -qx 'peak=()' "$tmp/empty.sh" ||
  { no "no block in $doc empties peak"; exit 1; }
block 'uvx pre-commit run' > "$tmp/hooks.sh"
grep -q "sh $tmp/pre-commit.sh" "$tmp/hooks.sh" ||
  { no "no hooks block in $doc"; exit 1; }

mkdir "$tmp/bin" "$tmp/t" || exit 1
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
chmod +x "$tmp/bin/cp" || exit 1

# Runs gated_tree under shell $1 with PATH $2; sets out and rc.
gated() {
  rm -rf "${tmp:?}/t" && mkdir "$tmp/t" || exit 1
  out=$(PATH=$2 TMPDIR=$tmp/t "$1" "$tmp/gated-run.sh" 2> /dev/null)
  rc=$?
}
# Checks that $TMPDIR of the gated_tree case $1 is empty.
emptied() {
  left=$(find "$tmp/t" -mindepth 1 -maxdepth 1 -exec basename {} \;)
  if [ -z "$left" ]; then ok "$1: \$TMPDIR is empty"
  else no "$1: \$TMPDIR holds $(printf '%s' "$left" | tr '\n' ' ')"; fi
}

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
  for c in unstaged assume-unchanged skip-worktree; do
    printf 'x\n' > "$wt/other"
    [ "$c" = unstaged ] || git -C "$wt" update-index "--$c" other || exit 1
    gated "$s" "$PATH"
    if [ "$rc" -ne 0 ] && [ -z "$out" ]; then
      ok "$s, $c: gated_tree prints nothing and exits $rc"
    else no "$s, $c: exit $rc, gated_tree prints '$out'"; fi
    emptied "$s, $c"
    [ "$c" = unstaged ] ||
      git -C "$wt" update-index "--no-$c" other || exit 1
    git -C "$wt" checkout -q -- other || exit 1
  done
  gated "$s" "$tmp/bin:$PATH"
  if [ -z "$out" ]; then ok "$s, signal: gated_tree prints nothing and exits $rc"
  else no "$s, signal: exit $rc, gated_tree prints '$out'"; fi
  emptied "$s, signal"
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
    "$s" "$tmp/hooks-$n-$c.sh" > "$tmp/hooks-$n-$c.log" 2>&1
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
exit "$fail"
