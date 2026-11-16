#!/bin/sh
# What git outside the sandbox reads once an outside contributor's gate
# has written a repository under a gitlink's directory, and what the gate
# can do to the clean-tree check:
#
#   sh scripts/test-gate-sandbox.sh [<writing.md>]
#
# It runs on macOS, where sandbox-exec is, and needs uv, as the gates do.
# Where sandbox-exec is not on the PATH, as on Linux, it prints `skip:`
# and exits 0.
# From <writing.md>, by default process/writing.md beside this script,
# it takes the shell blocks of *The gates* that gate a commit, where they
# are: the one that reads `<gate wt>`'s git directories, the one that
# runs sandbox-exec, the one that starts `"$@" uv sync --locked`, the
# one that runs `git status --porcelain`, and the `find` check. Their
# placeholders become paths of a fixture, and the gate command, `uv sync
# --locked`, a script of the test's. The fixture is a repository whose
# commit holds the gitlink `sub`, with `<wt>` detached at it, and for
# each case a new `<gate wt>`, added from `<wt>`, and `<sbx>`. git reads
# no global or system configuration, and no config written here runs a
# program: a probe is an inert key, or a line with a syntax error, which
# git fails on loudly where it parses the file. A stand-in git, first on
# the PATH, records each call outside the sandbox, and whether it printed
# `bad config`. The blocks' `env -i` drops the variable it records under,
# so it records no call inside the sandbox. The cases, in order:
#
# - fixer: the gate writes a file. The status file holds `?? fixed`,
#   then `EXIT_status=0`.
# - forged: the gate tries to overwrite `.git`, makes `sub/.git` a
#   repository whose config holds the syntax error, prints
#   `EXIT_status=0`, and leaves a process that waits for the status
#   file, tries to write `EXIT_status=0` there, empties the gate's log
#   and writes `EXIT_status=0` in it, then writes `late` in the tree.
#   The status file holds an `EXIT_status=` other than 0, the log the
#   forged line, and `late` exists. `.git` is what `git worktree add`
#   wrote. Control: `git status --porcelain` outside the sandbox, in the
#   tree the gate wrote, prints `bad config`. Then `git status
#   --porcelain` and `git diff --name-only HEAD` run in `<wt>`, and `git
#   -C <wt> worktree remove --force <gate wt>`: no recorded call printed
#   `bad config`, and `<gate wt>` is gone.
# - nested: `sub/.git` is a repository with an inert config. The status
#   file holds `EXIT_status=0` and a `nested:` line.
# - filled: `sub` holds a file and no `.git`. The status file holds
#   `EXIT_status=0` and a `gitlink:` line.
# - without find: nested and filled again, with the `find` check left
#   out. Each status file is the one line `EXIT_status=0`, so the check is
#   what refuses them.
# - hidden, crlf, attributes, ignore, ident: the gate writes a new file
#   beside a `.gitignore` of its own that ignores everything; turns the
#   tracked `file` from LF to CRLF; does that again with `* text` in
#   `$HOME/.config/git/attributes`; writes `x` with `x` in
#   `$HOME/.config/git/ignore`; and, in a `<gate wt>` checked out with
#   `* ident`, gives the expanded `$Id$` of `id` another hash of the same
#   length, with `* ident` in `$HOME/.config/git/attributes`, which git
#   would collapse back. Each status file lists the change, as
#   `!! hidden/`, ` M file`, `?? x` or ` M id`.
# - octopus: `<gate wt>` merges two heads with `--no-commit`, which
#   stages a change to `file` and a new file `new`, and the status block
#   runs before the gate into a base file. With a gate that writes
#   nothing, the base file lists both, and the status file holds no line
#   the base file lacks. With a gate that writes `new`, the status file
#   holds `AM new`, which the base file lacks.
# - include: the repository's configuration includes `~/inc`, which is
#   `<sbx>/home/inc` inside the sandbox, and the gate writes an inert
#   key there. The status file holds `EXIT_status=0` and an `include:`
#   line. With a line with a syntax error there instead, it holds an
#   `EXIT_status=` other than 0: git status read the included file.
#
# Where it runs the checks, each line it prints starts `ok` or `FAIL`,
# and it exits 1 where a check failed.
command -v sandbox-exec > /dev/null ||
  { echo "skip: no sandbox-exec on the PATH, so nothing is tested"; exit 0; }
here=$(dirname "$0")
doc=${1:-$here/../process/writing.md}
proc=$(cd "$(dirname "$doc")/.." && pwd -P) || exit 1
real=$(command -v git) || { echo "FAIL: no git on the PATH"; exit 1; }
tmp=$(mktemp -d) || exit 1
trap 'rm -rf "${tmp:?}"' EXIT
tmp=$(cd "$tmp" && pwd -P) || exit 1
fail=0
ok() { echo "ok: $1"; }
no() { echo "FAIL: $*"; fail=1; }

GIT_CONFIG_GLOBAL=$tmp/gitconfig GIT_CONFIG_NOSYSTEM=1
GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@example.invalid
GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@example.invalid
XDG_CONFIG_HOME=$tmp/xdg
export GIT_CONFIG_GLOBAL GIT_CONFIG_NOSYSTEM GIT_AUTHOR_NAME \
  GIT_AUTHOR_EMAIL GIT_COMMITTER_NAME GIT_COMMITTER_EMAIL XDG_CONFIG_HOME
: > "$GIT_CONFIG_GLOBAL"
mkdir -p "$XDG_CONFIG_HOME/git" || exit 1

repo=$tmp/repo wt=$tmp/wt gwt=$tmp/gate sbx=$tmp/sbx st=$tmp/gate-status
"$real" init -q -b main "$repo" || exit 1
base=$("$real" -C "$repo" commit-tree \
  "$("$real" -C "$repo" hash-object -t tree -w /dev/null)" -m base) &&
  blob=$(printf 'a\nb\n' | "$real" -C "$repo" hash-object -w --stdin) &&
  id=$(printf '\044Id\044\n' | "$real" -C "$repo" hash-object -w --stdin) &&
  tree=$({ printf '100644 blob %s\t%s\n' "$blob" file "$id" id
    printf '160000 commit %s\tsub\n' "$base"; } | "$real" -C "$repo" mktree) &&
  sha=$("$real" -C "$repo" commit-tree "$tree" -p "$base" -m gitlink) &&
  "$real" -C "$repo" update-ref refs/heads/gated "$sha" &&
  "$real" -C "$repo" worktree add -q --detach "$wt" "$sha" &&
  cp "$wt/.git" "$tmp/dotgit-wt" || exit 1

mkdir "$tmp/bin" || exit 1
cat > "$tmp/bin/git" <<EOF
#!/bin/sh
[ -n "\${STANDIN_LOG:-}" ] || exec "$real" "\$@"
err=\$(mktemp) || exit 1
"$real" "\$@" 2> "\$err"
rc=\$?
cat "\$err" >&2
r=-
grep -q 'bad config' "\$err" && r=READ
printf '%s git %s\n' "\$r" "\$*" >> "\$STANDIN_LOG"
rm -f "\$err"
exit "\$rc"
EOF
chmod +x "$tmp/bin/git" || exit 1
PATH=$tmp/bin:$PATH
STANDIN_LOG=$tmp/outside.log
export PATH STANDIN_LOG
: > "$STANDIN_LOG"

# The shell fence whose lines match $1, its two-space indent removed, and
# its placeholders filled.
block() {
  awk -v re="$1" '/^ *```shell$/ { b = ""; on = 1; next }
    on && /^ *```$/ { if (b ~ re) { printf "%s", b; exit }
      on = 0; next }
    on { sub(/^  /, ""); b = b $0 "\n" }' "$doc" |
    sed -e "s|<gate wt>|$gwt|g" -e "s|<wt>|$wt|g" -e "s|<sbx>|$sbx|g" \
      -e "s|<scratch>/<name>-|$tmp/gate-|g" -e "s|\${PROCESS:?}|$proc|g" \
      -e "s|uv sync --locked\$|sh $tmp/gate.sh|"
}
block '--git-common-dir >' > "$tmp/prep.sh"
{ block 'sandbox-exec -f'; block '^"[$]@" uv sync --locked'
  block 'porcelain'; } > "$tmp/gate-only.sh"
block '^gwt=.*\nst=' > "$tmp/find.sh"
{ block 'sandbox-exec -f'
  block 'porcelain' | sed "s|$tmp/gate-status|$tmp/gate-base|g"; } \
  > "$tmp/base.sh"
cat "$tmp/gate-only.sh" "$tmp/find.sh" > "$tmp/block.sh"
grep -q "sh $tmp/gate.sh" "$tmp/block.sh" ||
  { no "no gate block in $doc"; exit 1; }

# A new <gate wt>, its git directories read as the blocks read them.
fresh() {
  [ -e "$gwt" ] && "$real" -C "$wt" worktree remove --force "$gwt"
  rm -f "$st" "$tmp/gate-git-dirs" "$tmp/gate-gitlinks"
  rm -rf "${sbx:?}/home/.config"
  "$real" -C "$wt" worktree add -q --detach "$gwt" "$sha" &&
    cp "$gwt/.git" "$tmp/dotgit-gate" && mkdir -p "$sbx/home" "$sbx/tmp" &&
    if [ -s "$tmp/prep.sh" ]; then sh "$tmp/prep.sh"; else
      "$real" -C "$gwt" rev-parse --path-format=absolute --git-dir \
        --git-common-dir > "$tmp/gate-git-dirs"; fi || exit 1
}
# Runs script $1 on a new <gate wt> with gate $2, its log in $3.
run() { fresh; printf '%s\n' "$2" > "$tmp/gate.sh"; sh "$1" > "$3" 2>&1; }
plant='mkdir -p sub/.git/objects sub/.git/refs &&
  echo "ref: refs/heads/main" > sub/.git/HEAD'

run "$tmp/block.sh" ': > fixed' "$tmp/fixer.log"
if [ "$(cat "$st" 2>/dev/null)" = "$(printf '?? fixed\nEXIT_status=0')" ]
then ok "fixer: the status file lists the file, then EXIT_status=0"
else no "fixer: the status file does not list the fixer's file"; fi

run "$tmp/block.sh" "printf 'gitdir: /nowhere\n' > .git 2> /dev/null
$plant && printf '[broken\n' > sub/.git/config
echo 'EXIT_status=0'
(
  i=0
  while [ ! -s '$st' ] && [ \"\$i\" -lt 10 ]; do i=\$((i + 1)); sleep 1; done
  printf 'EXIT_status=0\n' > '$st' 2> /dev/null
  perl -e 'truncate(STDOUT, 0)'
  echo 'EXIT_status=0'
  : > late
) &" "$tmp/plant.log"
i=0
while [ ! -e "$gwt/late" ] && [ ! -e "$wt/late" ] && [ "$i" -lt 15 ]; do
  i=$((i + 1)); sleep 1
done
if grep -q '^EXIT_status=[1-9]' "$st" 2>/dev/null; then
  ok "forged: the status file refuses the tree: $(grep '^EXIT_status=' "$st")"
else
  no "forged: the status file holds no failing exit"
fi
if tr -d '\000' < "$tmp/plant.log" | grep -qx 'EXIT_status=0'; then
  ok "forged: the gate's log holds EXIT_status=0, which does not count"
else
  no "forged: the gate's log lost the forgery, so the test did not try it"
fi
if [ -e "$gwt/late" ] || [ -e "$wt/late" ]; then
  ok "forged: the process the gate left wrote in the tree after the check"
else
  no "forged: the process the gate left wrote nothing"
fi
for d in gate wt; do
  [ "$d" = gate ] && t=$gwt || t=$wt
  [ -d "$t/sub/.git" ] || continue
  if cmp -s "$tmp/dotgit-$d" "$t/.git"; then ok "forged: .git is unchanged"
  else no "forged: the gate wrote .git"; fi
done

git -C "$wt" status --porcelain > /dev/null 2>&1
git -C "$wt" diff --name-only HEAD > /dev/null 2>&1

planted=
for d in "$gwt" "$wt"; do [ -d "$d/sub/.git" ] && planted=$d && break; done
if [ -z "$planted" ]; then
  no "forged: the gate wrote no sub/.git"
elif STANDIN_LOG='' git -C "$planted" status --porcelain 2>&1 |
  grep -q 'bad config'; then
  ok "control: git status outside the sandbox parses it where the gate ran"
else
  no "control: git status outside the sandbox does not parse it"
fi

git -C "$wt" worktree remove --force "$gwt" > /dev/null 2>&1

if grep -q '^READ' "$STANDIN_LOG"; then
  no "git outside the sandbox parsed the planted config:"
  sed -n 's/^READ /  /p' "$STANDIN_LOG" | sed "s|$tmp|<tmp>|g"
else
  ok "no git outside the sandbox parsed it, of $(wc -l < "$STANDIN_LOG" |
    tr -d ' ') calls"
fi
if [ -e "$gwt" ]; then no "the removal left <gate wt>"; else
  ok "the removal removed <gate wt>"; fi
# What the removal could not remove, the forged case's checkout of
# <wt> included, goes before the next case.
rm -rf "${wt:?}/sub/.git" "${wt:?}/late"

for c in nested filled; do
  case $c in
    nested) want='^nested: '
      g="$plant && printf '[probe]\n\tmarker = planted\n' > sub/.git/config" ;;
    filled) want='^gitlink: sub$' g=': > sub/file' ;;
  esac
  run "$tmp/block.sh" "$g" "$tmp/$c.log"
  if grep -qx 'EXIT_status=0' "$st" 2>/dev/null && grep -q "$want" "$st"
  then ok "$c: git status reads clean, and the find check refuses the tree"
  else no "$c: the status file is not EXIT_status=0 with a find line:" \
    "$(tr "\n" " " 2>/dev/null < "$st")"; fi
  run "$tmp/gate-only.sh" "$g" "$tmp/$c-nofind.log"
  if [ "$(cat "$st" 2>/dev/null)" = EXIT_status=0 ]; then
    ok "without find, $c reads clean: the find check is what refuses it"
  else no "without find, $c does not read clean"; fi
done

xdg="mkdir -p \"\$HOME/.config/git\" && printf"
crlf="printf 'a\r\nb\r\n' > file"
for c in hidden crlf attributes ignore ident; do
  rm -f "$XDG_CONFIG_HOME/git/attributes"
  case $c in
    hidden) want='!! hidden/'
      g="mkdir hidden && printf '*\n' > hidden/.gitignore && : > hidden/new" ;;
    crlf) want=' M file' g=$crlf ;;
    attributes) want=' M file'
      g="$xdg '* text\n' > \"\$HOME/.config/git/attributes\" && $crlf" ;;
    ignore) want='?? x'
      g="$xdg 'x\n' > \"\$HOME/.config/git/ignore\" && : > x" ;;
    ident) want=' M id'
      printf '* ident\n' > "$XDG_CONFIG_HOME/git/attributes"
      g="$xdg '* ident\n' > \"\$HOME/.config/git/attributes\" &&
        printf '\$Id: %s \$\n' 1111111111111111111111111111111111111111 > id" ;;
  esac
  run "$tmp/block.sh" "$g" "$tmp/$c.log"
  if grep -qxF "$want" "$st" 2>/dev/null; then
    ok "$c: the status file lists '$want'"
  else no "$c: the status file does not list '$want':" \
    "$(tr "\n" " " 2>/dev/null < "$st")"; fi
done

# Two heads on the gated commit: one changes file, one adds new.
mk() {
  printf '%s\n' "$2" > "$tmp/blob" &&
    b=$("$real" -C "$repo" hash-object -w "$tmp/blob") &&
    t=$({ "$real" -C "$repo" ls-tree "$sha" | awk -F '\t' -v p="$1" '$2 != p'
      printf '100644 blob %s\t%s\n' "$b" "$1"; } |
      "$real" -C "$repo" mktree) &&
    "$real" -C "$repo" commit-tree "$t" -p "$sha" -m "$1"
}
h1=$(mk file c) && h2=$(mk new n) || exit 1
rm -f "$XDG_CONFIG_HOME/git/attributes"
for c in quiet writer; do
  case $c in
    quiet) g=: ;;
    writer) g="printf 'x\n' > new" ;;
  esac
  fresh
  "$real" -C "$gwt" -c core.hooksPath=/dev/null \
    merge -q --no-ff --no-commit "$h1" "$h2" > /dev/null 2>&1 ||
    { no "octopus: the merge failed"; continue; }
  rm -f "$tmp/gate-base"
  sh "$tmp/base.sh" > "$tmp/octopus-base.log" 2>&1
  printf '%s\n' "$g" > "$tmp/gate.sh"
  sh "$tmp/block.sh" > "$tmp/octopus-$c.log" 2>&1
  extra=$(grep -vxF -f "$tmp/gate-base" "$st" 2> /dev/null)
  if ! grep -qxF 'M  file' "$tmp/gate-base" 2>/dev/null ||
    ! grep -qxF 'A  new' "$tmp/gate-base"; then
    no "octopus: the base file does not list the staged files:" \
      "$(tr "\n" " " 2>/dev/null < "$tmp/gate-base")"
  elif [ "$c" = quiet ] && [ -z "$extra" ] && [ -s "$st" ]; then
    ok "octopus: a gate that writes nothing adds no line to the base file's"
  elif [ "$c" = writer ] && [ "$extra" = 'AM new' ]; then
    ok "octopus: a gate that writes a staged file adds '$extra'"
  else no "octopus, $c: the lines the base file lacks are not as expected:" \
    "$(printf '%s' "$extra" | tr "\n" " ")"; fi
done

inc=$(printf '%s/inc' '~')
"$real" -C "$repo" config include.path "$inc" || exit 1
run "$tmp/block.sh" "printf '[probe]\n\tmarker = planted\n' > \"\$HOME/inc\"" \
  "$tmp/include.log"
if grep -qx 'EXIT_status=0' "$st" 2>/dev/null &&
  grep -q '^include: local' "$st"; then
  ok "include: git status reads clean, and the include line refuses the tree"
else no "include: the status file holds no include line:" \
  "$(tr "\n" " " 2>/dev/null < "$st")"; fi
run "$tmp/block.sh" "printf '[broken\n' > \"\$HOME/inc\"" "$tmp/include2.log"
if grep -q '^EXIT_status=[1-9]' "$st" 2>/dev/null; then
  ok "include: git status in the sandbox read the included file"
else no "include: git status did not read the included file"; fi
"$real" -C "$repo" config --unset include.path
exit "$fail"
