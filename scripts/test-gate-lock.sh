#!/bin/sh
# Sessions ask for the gate lock's slots while others hold them:
#
#   sh scripts/test-gate-lock.sh [<gate-lock.sh>]
#   TEST_GATE_LOCK_PS=1 sh scripts/test-gate-lock.sh [<gate-lock.sh>]
#
# The second form runs the sessions with libproc stubbed out, so that they
# read start times through ps, as they do off macOS.
# Each session is a `sh` of its own, since the holder is its PID. Load,
# memory and disk are stubbed, so that the test does not depend on the
# machine: a session redefines _gl_idle, _gl_load, _gl_level, _gl_free and
# _gl_disk after sourcing. Every wait for an event polls once a second, up to 30
# times. Past that, the test kills the sessions it started and their
# children, prints the events, and exits 1. The cases, in order:
#
# - One slot. Two sessions, each with a scratchpad of its own, call
#   `gate_take <scratchpad> <worktree>`, the second while the first holds
#   the slot for 3 seconds. gate-lock.sh ignores the scratchpad. The events
#   must read A asks, A taken, B asks, A released, B taken, B released, in
#   that order. A script that keeps one lock per scratchpad fails, unless
#   its gate_take for B is slow enough to return after A's hold: no order
#   of events tells that apart from a lock.
# - Three slots. Four sessions ask at once. Three take a slot, and the
#   fourth still has none 3 seconds later. One holder releases, and the
#   fourth takes the freed slot.
# - A holder killed with SIGKILL leaves its slot behind. A new session
#   finds the slot stale, removes it and takes it.
# - A gate.lock held by a live process that is not a session, as a script
#   that knows one lock only leaves it, fills one slot: of three sessions,
#   two take a slot and the third waits. Once that process is killed, the
#   third finds gate.lock stale and takes it.
# - A session takes a slot at a high idle, finds the CPU busy when it
#   calls gate_wait, and must return from it only after the test lowers
#   the idle.
# - Spacing. With GATE_LOCK_STAGGER at 4 seconds, two sessions ask at once
#   with a slot free for each. The first holds its slot while the second
#   waits. The stamps in gate.last that the two takes write are 4 seconds
#   or more apart.
# - No slot held. With GATE_LOCK_STAGGER at 60 seconds and gate.last just
#   written, a session asks while no slot is held, and takes one within
#   the 30 seconds of a wait. Then a session asks beside a gate.lock.3
#   whose holder is gone, and takes a slot within them too.
# - Settling. With GATE_LOCK_SETTLE at 4 seconds and 40% of memory free,
#   under the floor plus the margin, two sessions ask at once with a slot
#   free for each, and the takes are 4 seconds or more apart. With it at
#   60 seconds and 50% free, the second takes a slot within the 30
#   seconds of a wait.
# - Zsh. A zsh session takes the first slot with no other slot present, and
#   releases it. Skipped where there is no zsh.
# - A background subshell. Under each of sh, bash, zsh and dash, with
#   noclobber set, a shell starts `( ... ) &` that takes a slot, and
#   exits. The owner of the slot is the subshell, which is alive, and not
#   the shell that exited. The subshell releases it.
# - Load generators. Under each of sh, bash, zsh and dash, two sessions ask
#   at once for every slot with gate_take_all. Both finish, and their holds
#   do not overlap.
# - gate_release_all called by a shell that holds nothing fails, and leaves
#   the gate.generator and the slots of another shell as they were.
# - A generator killed with SIGKILL while it holds every slot. The next
#   generator reclaims gate.generator and the slots, and finishes.
# - Defaults. Sourced with no GATE_LOCK_LOAD, GATE_LOCK_SLOTS,
#   GATE_LOCK_WORKERS, GATE_LOCK_FREE, GATE_LOCK_SETTLE or GATE_LOCK_MARGIN
#   and a core count stubbed, the script sets the load ceiling to 3 times
#   the cores, the idle to 30, the workers to the cores divided by the
#   slots, at least 1, the free floor to 35, the settle to 60 and the
#   margin to 15.
# - The real _gl_idle prints an integer from 0 to 100.
# - On macOS, with sysctl and iostat refused as Codex's sandbox refuses
#   them, the real readers still print the idle percentage, the load and
#   the percentage free, and no level.
# - _gl_admit is called with each idle percentage, load, disk, level and
#   free percentage in the tables below, and _gl_settled with each age of
#   the last take and free percentage.
# - _gl_status names the reads that failed, and only those.
# - A process neither libproc nor ps can read is alive: its ticket is
#   alive and its slot is not reclaimed. Once ps answers that no process
#   has its PID, it is gone, and its slot is reclaimed.
# - Libproc and ps, where libproc reads this shell. Both print the same
#   start time for a live process and nothing for a dead one, and a ticket
#   written through either is alive to the other. Libproc reads an
#   unreaped zombie as gone. With ps refused, a dead PID and a zombie lose
#   their ticket and their slot on libproc's answer alone.
# - gate_peak. Under each of sh, bash, zsh and dash, it returns the exit
#   code of the program it runs and appends one well-formed line to
#   gate.peaks. A program holding 200 MB peaks between 200 and 300 MB,
#   skipped where neither time nor /proc reads a peak, as in Codex's
#   sandbox. A program killed with KILL returns 137. gate_peak removes
#   time's output file, and one a shell that is gone left, and keeps one
#   of a live shell. With no file for time's output, under each shell,
#   the program runs through a /proc of the test's and then alone, reads
#   the caller's stdin, and returns its code.
#   The output of GNU time and of macOS time are both read in KB.
# - /proc, in a tree the test writes: the largest VmHWM of a process and
#   the processes below it, a grandchild and a child of a thread other
#   than the main one included, and none once the process has ended.

# The stubs are called by the sourced script, and the script is a variable.
# The stubs are text a session evals, and they read $idle.
# shellcheck disable=SC1090,SC2329,SC2016,SC2034
script=${1:-$(dirname "$0")/gate-lock.sh}
tmp=$(mktemp -d "${TMPDIR:-/tmp}/test-gate-lock.XXXXXX") || exit 1
trap 'rm -r "$tmp"' EXIT
GATE_LOCK_DIR=$tmp/lock GATE_LOCK_POLL=1 GATE_LOCK_SLOTS=1
GATE_LOCK_LOAD=30 GATE_LOCK_IDLE=30 GATE_LOCK_FREE=35 GATE_LOCK_DISK=20 GATE_LOCK_STAGGER=0
GATE_LOCK_SETTLE=0 GATE_LOCK_MARGIN=15
export GATE_LOCK_DIR GATE_LOCK_POLL GATE_LOCK_SLOTS GATE_LOCK_STAGGER
export GATE_LOCK_SETTLE GATE_LOCK_MARGIN
export GATE_LOCK_LOAD GATE_LOCK_IDLE GATE_LOCK_FREE GATE_LOCK_DISK
echo 80 > "$tmp/idle"
mkdir "$tmp/scratchpad-A" "$tmp/scratchpad-B"
: > "$tmp/events"

# The stubs every session defines after sourcing the script
stubs='
  _gl_idle() { sleep 1; cat "$idle"; }
  _gl_load() { echo 5; }
  _gl_level() { echo 1; }
  _gl_free() { echo 50; }
  _gl_disk() { echo 100; }
'
[ -z "${TEST_GATE_LOCK_PS:-}" ] || stubs="$stubs _gl_libproc() { return 2; }"

session() { # <name> <scratchpad> <seconds held>
  exec sh -c '
    . "$1"
    idle=$6
    eval "$7"
    echo "$(date +%s) $2 asks" >> "$4"
    gate_take "$3" "wt-$2" >/dev/null || exit 1
    echo "$(date +%s) $2 taken" >> "$4"
    sleep "$5"
    echo "$(date +%s) $2 released" >> "$4"
    gate_release "$3" >/dev/null || exit 1
    echo "$(date +%s) $2 done" >> "$4"
  ' sh "$script" "$1" "$2" "$tmp/events" "$3" "$tmp/idle" "$stubs"
}

# <name>: writes its PID to $tmp/pid-<name> and what gate_take prints to
# $tmp/out-<name>, and holds its slot until the file $tmp/go-<name> exists
holder() {
  exec sh -c '
    . "$1"
    idle=$4/idle
    eval "$5"
    echo $$ > "$4/pid-$2"
    echo "$(date +%s) $2 asks" >> "$3"
    gate_take "wt-$2" > "$4/out-$2" || exit 1
    cp "$GATE_LOCK_DIR/gate.last" "$4/last-$2" 2>/dev/null
    echo "$(date +%s) $2 taken" >> "$3"
    until [ -f "$4/go-$2" ]; do sleep 1; done
    gate_release >/dev/null || exit 1
    echo "$(date +%s) $2 done" >> "$3"
  ' sh "$script" "$1" "$tmp/events" "$tmp" "$stubs"
}

pids=""
fail() { # <reason>: stop the sessions started and their children
  # one PID a line, since zsh does not split an unquoted $pids
  printf '%s\n' "$pids" | tr ' ' '\n' | while read -r pid; do
    [ -n "$pid" ] || continue
    # stopped first, so that it starts no child between the two kills
    kill -STOP "$pid" 2>/dev/null
    pkill -P "$pid" 2>/dev/null
    kill "$pid" 2>/dev/null
    kill -CONT "$pid" 2>/dev/null
  done
  wait
  cat "$tmp/events"
  echo "FAIL: $1"
  exit 1
}

# <pattern> <count> <reason>: wait up to 30 seconds for <count> events
await() {
  i=0
  until [ "$(grep -c "$1" "$tmp/events")" -ge "$2" ]; do
    i=$((i + 1))
    [ "$i" -le 30 ] || fail "$3"
    sleep 1
  done
}

# <name>: whether that session holds a slot it took
holds() { grep -q " $1 taken$" "$tmp/events" && ! grep -q " $1 done$" "$tmp/events"; }

session A "$tmp/scratchpad-A" 3 &
pids=$!
await 'A taken' 1 "A never took the slot"
session B "$tmp/scratchpad-B" 0 &
pids="$pids $!"
await ' done$' 2 "a session never finished"
wait

cat "$tmp/events"
order=$(grep -v ' done$' "$tmp/events" | cut -d' ' -f2- | tr '\n' ',')
[ "$order" = "A asks,A taken,B asks,A released,B taken,B released," ] || {
  echo "FAIL: the events are not in the order of one slot"
  exit 1
}
echo "ok: with one slot, B asked while A held it, and took it only after A released"

# Three slots, four sessions.
GATE_LOCK_SLOTS=3
: > "$tmp/events"
pids=""
for n in C D E F; do
  holder "$n" &
  pids="$pids $!"
done
await ' taken$' 3 "three sessions never held a slot each"
sleep 3
[ "$(grep -c ' taken$' "$tmp/events")" -eq 3 ] ||
  fail "a fourth session took a slot while three held one"
waiter=""
for n in C D E F; do holds "$n" || waiter=$n; done
first=$(grep ' taken$' "$tmp/events" | head -n 1 | cut -d' ' -f2)
touch "$tmp/go-$first"
await ' taken$' 4 "$waiter never took the slot $first released"
cat "$tmp/events"
echo "ok: three sessions held a slot each, and $waiter took one only after $first released"

# A killed holder.
victim=""
for n in C D E F; do [ "$n" = "$first" ] || ! holds "$n" || victim=$n; done
kill -KILL "$(cat "$tmp/pid-$victim")"
holder G &
pids="$pids $!"
await 'G taken' 1 "G never took the slot of the killed $victim"
grep -q 'stale' "$tmp/out-G" || fail "G took a slot without reclaiming $victim's"
cat "$tmp/out-G"
echo "ok: G took the slot of $victim, killed while it held it"
for n in C D E F G; do touch "$tmp/go-$n"; done
wait

# A gate.lock left by a process that is not a session.
: > "$tmp/events"
sleep 300 &
legacy=$!
pids="$legacy"
mkdir "$GATE_LOCK_DIR/gate.lock"
echo "$legacy $(date +%s) wt-legacy" > "$GATE_LOCK_DIR/gate.lock/owner"
for n in H I J; do
  holder "$n" &
  pids="$pids $!"
done
await ' taken$' 2 "two sessions never held a slot each beside gate.lock"
sleep 3
[ "$(grep -c ' taken$' "$tmp/events")" -eq 2 ] ||
  fail "a third session took a slot while gate.lock and two slots were held"
kill "$legacy"
await ' taken$' 3 "the third session never took gate.lock once its holder was gone"
cat "$tmp/events"
cat "$tmp"/out-[HIJ]
grep -q 'gate.lock of pid' "$tmp"/out-[HIJ] ||
  fail "no session reclaimed gate.lock"
echo "ok: a live gate.lock filled a slot, and was reclaimed once its holder was gone"
for n in H I J; do touch "$tmp/go-$n"; done
wait

# Spacing: two sessions ask at once, and the second waits for the stagger.
GATE_LOCK_STAGGER=4
rm -f "$GATE_LOCK_DIR/gate.last"
: > "$tmp/events"
pids=""
for n in K L; do
  holder "$n" &
  pids="$pids $!"
done
await ' taken$' 1 "no session took a slot"
sleep 1
[ "$(grep -c ' taken$' "$tmp/events")" -eq 1 ] ||
  fail "a second session took a slot within the stagger of the first"
await ' taken$' 2 "the second session never took a slot"
# the times the takes were stamped, which gate_take returns after
t1=$(cat "$tmp/last-K")
t2=$(cat "$tmp/last-L")
[ "$t1" -le "$t2" ] || { t=$t1; t1=$t2; t2=$t; }
[ $((t2 - t1)) -ge "$GATE_LOCK_STAGGER" ] ||
  fail "the takes were $((t2 - t1)) seconds apart, under the stagger of $GATE_LOCK_STAGGER"
echo "ok: the second take came $((t2 - t1)) seconds after the first, the stagger being $GATE_LOCK_STAGGER"
for n in K L; do touch "$tmp/go-$n"; done
wait

# No slot held: a recent take does not hold the next one back for the
# stagger, nor does a slot whose holder is gone.
GATE_LOCK_STAGGER=60
date +%s > "$GATE_LOCK_DIR/gate.last"
: > "$tmp/events"
holder M &
pids=$!
await 'M taken' 1 "with no slot held, M was held for the stagger"
touch "$tmp/go-M"
await 'M done' 1 "M never released its slot"
wait
# a process that ends by itself: one killed at once may still be a copy of
# this shell, which runs the trap that removes $tmp
sh -c : &
dead=$!
wait "$dead"
mkdir "$GATE_LOCK_DIR/gate.lock.3"
echo "$dead $(date +%s) wt-dead" > "$GATE_LOCK_DIR/gate.lock.3/owner"
holder N &
pids=$!
await 'N taken' 1 "beside a stale gate.lock.3, N was held for the stagger"
touch "$tmp/go-N"
await 'N done' 1 "N never released its slot"
wait
cat "$tmp/events"
echo "ok: with no slot held, or only a stale one, a take came within the stagger of $GATE_LOCK_STAGGER"
rm -r "${GATE_LOCK_DIR:?}/gate.lock.3"
GATE_LOCK_STAGGER=0

# Settling: two sessions ask at once with a slot free for each, at 40% of
# memory free, which admits a gate but lacks the margin. The second waits
# for the settle. At 50% free, the margin, it does not.
# Each stub goes on a line of its own, after the libproc stub of the
# second form.
saved=$stubs
stubs="$saved
  _gl_free() { echo 40; }
"
GATE_LOCK_SETTLE=4
rm -f "$GATE_LOCK_DIR/gate.last"
: > "$tmp/events"
pids=""
for n in S T; do
  holder "$n" &
  pids="$pids $!"
done
await ' taken$' 1 "no session took a slot at 40% free"
sleep 1
[ "$(grep -c ' taken$' "$tmp/events")" -eq 1 ] ||
  fail "a second session took a slot within the settle at 40% free"
await ' taken$' 2 "the second session never took a slot at 40% free"
t1=$(cat "$tmp/last-S")
t2=$(cat "$tmp/last-T")
[ "$t1" -le "$t2" ] || { t=$t1; t1=$t2; t2=$t; }
[ $((t2 - t1)) -ge "$GATE_LOCK_SETTLE" ] ||
  fail "at 40% free the takes were $((t2 - t1)) seconds apart, under the settle of $GATE_LOCK_SETTLE"
echo "ok: at 40% free the second take came $((t2 - t1)) seconds after the first, the settle being $GATE_LOCK_SETTLE"
for n in S T; do touch "$tmp/go-$n"; done
wait
stubs="$saved
  _gl_free() { echo 50; }
"
GATE_LOCK_SETTLE=60
rm -f "$GATE_LOCK_DIR/gate.last"
: > "$tmp/events"
pids=""
for n in U V; do
  holder "$n" &
  pids="$pids $!"
done
await ' taken$' 2 "at 50% free, the second session was held for the settle"
cat "$tmp/events"
echo "ok: at 50% free the second take came within the settle of $GATE_LOCK_SETTLE"
for n in U V; do touch "$tmp/go-$n"; done
wait
stubs=$saved
GATE_LOCK_SETTLE=0

# Under zsh, which stops at a glob with no match, a session takes the first
# slot, with no gate.lock.2 or gate.lock.3 beside it, and releases it.
if command -v zsh > /dev/null; then
  rm -rf "${GATE_LOCK_DIR:?}"
  zsh -c '
    . "$1"
    idle=$3
    eval "$4"
    gate_take wt-Z > /dev/null || exit 1
    gate_release
  ' zsh "$script" "$tmp" "$tmp/idle" "$stubs" > "$tmp/out-Z" 2>&1 ||
    { cat "$tmp/out-Z"; fail "a zsh session did not release its slot"; }
  grep -q 'gate.lock released by' "$tmp/out-Z" || { cat "$tmp/out-Z"; fail "zsh printed no release"; }
  [ ! -e "$GATE_LOCK_DIR/gate.lock" ] || fail "gate.lock is still there after a zsh release"
  cat "$tmp/out-Z"
  echo "ok: under zsh, a session released gate.lock with no other slot present"
else
  echo "skipped: no zsh to run the release case under"
fi

# A background subshell. A shell sources the script, starts `( ... ) &`
# that takes a slot and holds it until $tmp/go-bg exists, and exits at once.
# The slot's owner is the subshell, which is alive, and not the shell that
# exited, whose `$$` the subshell shares. Run under each shell of the kind
# named, those not installed skipped.
for shell in sh bash zsh dash; do
  command -v "$shell" > /dev/null || { echo "skipped: no $shell to run the subshell case under"; continue; }
  rm -rf "${GATE_LOCK_DIR:?}" "$tmp/go-bg" "$tmp/out-bg" "$tmp/main-bg" "$tmp/sub-bg"
  idle=$tmp/idle
  "$shell" -c '
    . "$1"
    idle=$2
    eval "$3"
    set -C
    echo $$ > "$4/main-bg"
    (
      sh -c '"'"'echo $PPID'"'"' >| "$4/sub-bg"
      gate_take wt-bg > "$4/out-bg" || exit 1
      until [ -f "$4/go-bg" ]; do sleep 1; done
      gate_release >> "$4/out-bg"
    ) &
  ' "$shell" "$script" "$tmp/idle" "$stubs" "$tmp" || fail "$shell could not start the subshell"
  # the subshell is in $pids from its first line, so that fail kills it
  i=0
  until [ -s "$tmp/sub-bg" ]; do
    i=$((i + 1))
    [ "$i" -le 30 ] || fail "the subshell of $shell did not start"
    sleep 1
  done
  read -r pids < "$tmp/sub-bg"
  # the owner file exists before its content is written: wait for the PID
  owner="" i=0
  until [ -n "$owner" ]; do
    i=$((i + 1))
    [ "$i" -le 30 ] || { cat "$tmp/out-bg" 2>/dev/null; fail "a subshell of $shell took no slot after its shell exited"; }
    sleep 1
    read -r owner _ 2>/dev/null < "$GATE_LOCK_DIR/gate.lock/owner"
  done
  read -r main < "$tmp/main-bg"
  [ "$owner" != "$main" ] || { touch "$tmp/go-bg"; fail "$shell: the owner of the slot is the shell that exited, not the subshell"; }
  kill -0 "$owner" 2>/dev/null || { touch "$tmp/go-bg"; fail "$shell: the owner of the slot is not alive"; }
  touch "$tmp/go-bg"
  i=0
  while [ -e "$GATE_LOCK_DIR/gate.lock" ]; do
    i=$((i + 1))
    [ "$i" -le 30 ] || fail "the subshell of $shell did not release its slot"
    sleep 1
  done
  grep -q 'gate.lock released by' "$tmp/out-bg" || { cat "$tmp/out-bg"; fail "the subshell of $shell printed no release"; }
  pids=""
  echo "ok: under $shell, with noclobber set, a background subshell held gate.lock after its shell exited, and released it"
done
rm -rf "${GATE_LOCK_DIR:?}"

# Load generators. Two generators ask at once for every slot, each in a shell
# of the kind named. Both finish, one after the other: a generator holds
# every slot, as its own owner file says, so the two do not split them and
# wait for ever.
generator() { # <shell> <name>
  exec "$1" -c '
    . "$1"
    idle=$4/idle
    eval "$5"
    echo "$(date +%s) $2 asks" >> "$3"
    gate_take_all "wt-$2" > /dev/null || exit 1
    # every slot has this shell as its owner
    for slot in gate.lock gate.lock.2 gate.lock.3; do
      owner=""
      read -r owner _ 2>/dev/null < "$GATE_LOCK_DIR/$slot/owner"
      [ "$owner" = "$$" ] || { echo "$2 does not hold $slot" >> "$3"; exit 1; }
    done
    echo "$(date +%s) $2 taken" >> "$3"
    sleep 2
    echo "$(date +%s) $2 released" >> "$3"
    gate_release_all > /dev/null || exit 1
    echo "$(date +%s) $2 done" >> "$3"
  ' "$1" "$script" "$2" "$tmp/events" "$tmp" "$stubs"
}
GATE_LOCK_SLOTS=3
for shell in sh bash zsh dash; do
  command -v "$shell" > /dev/null || { echo "skipped: no $shell for the generators"; continue; }
  rm -rf "${GATE_LOCK_DIR:?}"
  : > "$tmp/events"
  pids=""
  for n in P Q; do
    generator "$shell" "$n" &
    pids="$pids $!"
  done
  await ' done$' 2 "under $shell, the two generators did not both finish"
  wait
  order=$(grep -v -e ' asks$' -e ' done$' "$tmp/events" | cut -d' ' -f2- | tr '\n' ',')
  case $order in
    "P taken,P released,Q taken,Q released," | "Q taken,Q released,P taken,P released,") ;;
    *) cat "$tmp/events"; fail "under $shell, the generators overlapped: $order" ;;
  esac
  [ ! -e "$GATE_LOCK_DIR/gate.generator" ] && [ ! -e "$GATE_LOCK_DIR/gate.lock" ] &&
    [ ! -e "$GATE_LOCK_DIR/gate.lock.2" ] && [ ! -e "$GATE_LOCK_DIR/gate.lock.3" ] ||
    fail "under $shell, a slot or gate.generator is left after the release"
  "$shell" -c '. "$1"; gate_release_all > /dev/null' "$shell" "$script" &&
    fail "under $shell, gate_release_all released nothing and succeeded"
  echo "ok: under $shell, two generators took every slot one after the other"
done

# gate_release_all releases only what its own shell holds: called by another
# shell while a generator holds gate.generator and the slots, it fails and
# leaves all of them, and the owner file, as they were.
rm -rf "${GATE_LOCK_DIR:?}"
sh -c '
  . "$1"
  idle=$3
  eval "$4"
  gate_take_all wt-H > /dev/null || exit 1
  : > "$2/held-H"
  exec sleep 300
' sh "$script" "$tmp" "$tmp/idle" "$stubs" &
pids=$!
i=0
until [ -f "$tmp/held-H" ]; do
  i=$((i + 1))
  [ "$i" -le 30 ] || fail "the generator H never held every slot"
  sleep 1
done
before=$(cat "$GATE_LOCK_DIR/gate.generator/owner")
sh -c '. "$1"; gate_release_all' sh "$script" > /dev/null 2>&1 &&
  fail "gate_release_all succeeded in a shell that held nothing"
[ "$(cat "$GATE_LOCK_DIR/gate.generator/owner" 2>/dev/null)" = "$before" ] ||
  fail "another shell's gate_release_all changed gate.generator"
[ -d "$GATE_LOCK_DIR/gate.lock" ] || fail "another shell's gate_release_all released gate.lock"
kill "$pids"
wait "$pids" 2>/dev/null
echo "ok: gate_release_all left the gate.generator of another shell alone"

# A generator killed with SIGKILL while it holds gate.generator and every slot
# leaves them behind. The next generator finds all of them stale, removes
# them and finishes.
rm -rf "${GATE_LOCK_DIR:?}"
: > "$tmp/events"
sh -c '
  . "$1"
  idle=$3
  eval "$4"
  gate_take_all wt-X > /dev/null || exit 1
  : > "$2/held-X"
  exec sleep 300
' sh "$script" "$tmp" "$tmp/idle" "$stubs" &
pids=$!
i=0
until [ -f "$tmp/held-X" ]; do
  i=$((i + 1))
  [ "$i" -le 30 ] || fail "the generator X never held every slot"
  sleep 1
done
kill -KILL "$pids"
wait "$pids" 2>/dev/null
sh -c '
  . "$1"
  idle=$3
  eval "$4"
  gate_take_all wt-R || exit 1
  gate_release_all
' sh "$script" "$tmp" "$tmp/idle" "$stubs" > "$tmp/out-R" 2>&1 &
pids=$!
await_pid() { # <pid> <reason>: wait up to 30 seconds for the process to end
  i=0
  while kill -0 "$1" 2>/dev/null; do
    i=$((i + 1))
    [ "$i" -le 30 ] || fail "$2"
    sleep 1
  done
}
await_pid "$pids" "a generator never took the leftovers of the killed one"
wait "$pids" || fail "the generator R failed"
cat "$tmp/out-R"
grep -q 'gate.generator of pid .* is stale' "$tmp/out-R" ||
  fail "the generator did not reclaim the stale gate.generator"
[ ! -e "$GATE_LOCK_DIR/gate.generator" ] && [ ! -e "$GATE_LOCK_DIR/gate.lock" ] &&
  [ ! -e "$GATE_LOCK_DIR/gate.lock.2" ] && [ ! -e "$GATE_LOCK_DIR/gate.lock.3" ] ||
  fail "gate.generator or a slot is left after the release"
echo "ok: a generator reclaimed the gate.generator and the slots of one killed while it held them"
GATE_LOCK_SLOTS=1

# Defaults: the core count is stubbed, once by sysctl and once by getconf.
# The values are printed by a subshell that has none of the settings.
defaults() { # <ncpu> <sysctl or getconf>
  (
    unset GATE_LOCK_LOAD GATE_LOCK_IDLE GATE_LOCK_SLOTS GATE_LOCK_WORKERS
    unset GATE_LOCK_FREE GATE_LOCK_SETTLE GATE_LOCK_MARGIN
    n=$1
    if [ "$2" = sysctl ]; then sysctl() { echo "$n"; }
    else
      sysctl() { return 1; }
      getconf() { echo "$n"; }
    fi
    . "$script"
    echo "$GATE_LOCK_LOAD $GATE_LOCK_IDLE $GATE_LOCK_SLOTS $GATE_LOCK_WORKERS" \
      "$GATE_LOCK_FREE $GATE_LOCK_SETTLE $GATE_LOCK_MARGIN"
  )
}
bad=0
while read -r ncpu via want; do
  got=$(defaults "$ncpu" "$via")
  [ "$got" = "$want" ] || { echo "FAIL: $ncpu cores by $via: '$got', want '$want'"; bad=1; }
done <<'CASES'
10 sysctl 30 30 3 3 35 60 15
10 getconf 30 30 3 3 35 60 15
8 sysctl 24 30 3 2 35 60 15
2 getconf 6 30 3 1 35 60 15
CASES
[ "$bad" -eq 0 ] || exit 1
echo "ok: the load ceiling is 3 times the cores, idle 30, workers the cores divided by the slots, at least 1, free 35, settle 60, margin 15"

# A gate that finds the CPU busy after the slot is taken waits for it.
: > "$tmp/events"
(
  . "$script"
  idle=$tmp/idle
  eval "$stubs"
  gate_take "$tmp/scratchpad-A" wt-W > /dev/null || exit 1
  echo 10 > "$tmp/idle"
  echo "$(date +%s) W waits" >> "$tmp/events"
  gate_wait > /dev/null
  echo "$(date +%s) W returned" >> "$tmp/events"
  gate_release "$tmp/scratchpad-A" > /dev/null
) &
pids=$!
await 'W waits' 1 "W never reached gate_wait"
sleep 3
grep -q 'W returned' "$tmp/events" && fail "gate_wait returned at an idle under GATE_LOCK_IDLE"
echo 80 > "$tmp/idle"
await 'W returned' 1 "gate_wait did not return once the CPU was idle"
wait
echo "ok: gate_wait waited for idle CPU after the slot was taken"

# The real reader, not stubbed
(
  . "$script"
  GATE_LOCK_POLL=2
  t0=$(date +%s)
  u=$(_gl_idle)
  [ $(($(date +%s) - t0)) -ge 2 ] || { echo "FAIL: _gl_idle took under the poll"; exit 1; }
  case $u in "" | *[!0-9]*) echo "FAIL: _gl_idle printed '$u'"; exit 1 ;; esac
  [ "$u" -le 100 ] || { echo "FAIL: _gl_idle printed '$u'"; exit 1; }
) || exit 1
echo "ok: _gl_idle printed a percentage, over the poll interval"

# The real readers where sysctl and iostat are refused, on macOS only: off
# it, /proc answers the idle and the load, and nothing the free.
if [ "$(uname -s)" = Darwin ]; then
  (
    . "$script"
    GATE_LOCK_POLL=2
    sysctl() { echo "sysctl: refused" >&2; return 1; }
    iostat() { echo "iostat: refused" >&2; return 1; }
    t0=$(date +%s)
    u=$(_gl_idle) l=$(_gl_load) p=$(_gl_level) f=$(_gl_free)
    [ $(($(date +%s) - t0)) -ge 2 ] || { echo "FAIL: _gl_idle took under the poll"; exit 1; }
    case $u in "" | *[!0-9]*) echo "FAIL: _gl_idle printed '$u'"; exit 1 ;; esac
    [ "$u" -le 100 ] || { echo "FAIL: _gl_idle printed '$u'"; exit 1; }
    case $l in [0-9]*.[0-9]*) ;; *) echo "FAIL: _gl_load printed '$l'"; exit 1 ;; esac
    case $f in "" | *[!0-9]*) echo "FAIL: _gl_free printed '$f'"; exit 1 ;; esac
    [ "$f" -le 100 ] || { echo "FAIL: _gl_free printed '$f'"; exit 1; }
    [ -z "$p" ] || { echo "FAIL: _gl_level printed '$p' with sysctl refused"; exit 1; }
    echo "ok: with sysctl and iostat refused, idle $u%, load $l and $f% free were read, and no level"
  ) || exit 1
else
  echo "skipped: not macOS, so no sysctl or iostat to refuse"
fi

# Idle: percentage idle, expected admission ("-" is a failed read).
(
  . "$script"
  _gl_load() { echo 5; }
  _gl_level() { echo 1; }
  _gl_free() { echo 50; }
  _gl_disk() { echo 100; }
  bad=0
  while read -r u want; do
    _gl_idle() { [ "$u" = - ] || echo "$u"; }
    _gl_admit && got=admit || got="wait"
    [ "$got" = "$want" ] || { echo "FAIL: idle $u: $got, want $want"; bad=1; }
  done <<'CASES'
30 admit
29 wait
100 admit
0 wait
- admit
CASES
  exit "$bad"
) || exit 1
echo "ok: a gate is admitted with 30% of the CPU idle, not with 29%"

# Load and disk: load, GB free, expected admission ("-" is a failed read).
(
  . "$script"
  _gl_idle() { echo 80; }
  _gl_level() { echo 1; }
  _gl_free() { echo 50; }
  bad=0
  while read -r l g want; do
    _gl_load() { [ "$l" = - ] || echo "$l"; }
    _gl_disk() { [ "$g" = - ] || echo "$g"; }
    _gl_admit && got=admit || got="wait"
    [ "$got" = "$want" ] || { echo "FAIL: load $l disk $g: $got, want $want"; bad=1; }
  done <<'CASES'
29.99 100 admit
30.00 100 wait
23.20 100 admit
5.00 20 admit
5.00 19 wait
5.00 - admit
- 100 admit
CASES
  exit "$bad"
) || exit 1
echo "ok: a gate is admitted under load 30, and with 20 GB of disk free"

# Memory: level, free percentage, expected admission ("-" is a failed read).
(
  . "$script"
  _gl_idle() { echo 80; }
  _gl_load() { echo 5; }
  _gl_disk() { echo 100; }
  bad=0
  while read -r level free want; do
    _gl_level() { [ "$level" = - ] || echo "$level"; }
    _gl_free() { [ "$free" = - ] || echo "$free"; }
    _gl_admit && got=admit || got="wait"
    [ "$got" = "$want" ] || { echo "FAIL: level $level free $free: $got, want $want"; bad=1; }
  done <<'CASES'
1 35 admit
1 90 admit
1 34 wait
1 5 wait
1 - admit
2 90 wait
2 - wait
4 90 wait
- 35 admit
- 34 wait
- - admit
CASES
  exit "$bad"
) || exit 1
echo "ok: memory is admissible at level 1 or an unread level with 35% free, never at level 2 or 4"

# Settling: seconds since the last take, free percentage, expected take
# ("-" is no gate.last, or a failed read of the free percentage).
(
  . "$script"
  _gl_d=$tmp/settle
  mkdir -p "$_gl_d"
  GATE_LOCK_SETTLE=60
  bad=0
  while read -r age free want; do
    if [ "$age" = - ]; then rm -f "$_gl_d/gate.last"
    else echo $(($(date +%s) - age)) > "$_gl_d/gate.last"; fi
    _gl_f=$free
    [ "$free" != - ] || _gl_f=""
    _gl_settled && got=take || got="wait"
    [ "$got" = "$want" ] || { echo "FAIL: age $age free $free: $got, want $want"; bad=1; }
  done <<'CASES'
0 50 take
0 49 wait
50 49 wait
0 - wait
60 35 take
60 - take
- 35 take
CASES
  exit "$bad"
) || exit 1
echo "ok: within the settle a take needs 50% free, and after it the free floor alone"

# The status names the reads that failed ("-"), in the order it prints them.
(
  . "$script"
  read_as() { [ "$1" = - ] || echo "$1"; }
  bad=0
  while read -r u l p f g want; do
    _gl_u=$(read_as "$u") _gl_l=$(read_as "$l") _gl_p=$(read_as "$p")
    _gl_f=$(read_as "$f") _gl_g=$(read_as "$g")
    got=$(_gl_status)
    case $want in
      -) case $got in *"not read"*) echo "FAIL: '$got', want all read"; bad=1 ;; esac ;;
      *) case $got in *"; not read: $want") ;; *) echo "FAIL: '$got', want '$want' not read"; bad=1 ;; esac ;;
    esac
  done <<'CASES'
80 5.00 1 50 100 -
80 5.00 - 50 100 memory pressure level
- - - - - CPU idle, load, memory pressure level, memory free, disk free
80 - 2 - 100 load, memory free
CASES
  exit "$bad"
) || exit 1
echo "ok: the status names the reads that failed, and none where all were read"

# A process that cannot be read, then one ps answers is gone.
(
  . "$script"
  _gl_libproc() { return 2; }
  ps() { return 126; }
  sh -c : &
  dead=$!
  wait "$dead"
  _gl_d=$tmp/unread _gl_me=$$
  _gl_s=$_gl_d/gate.lock
  mkdir -p "$_gl_s"
  echo "$dead 0 wt" > "$_gl_s/owner"
  printf '%s\n%s\n%s\n' "$dead" "Mon Nov 2 00:00:00 2026" wt > "$tmp/ticket-unread"
  _gl_running "$dead" || { echo "FAIL: a process ps cannot read is not running"; exit 1; }
  _gl_alive "$tmp/ticket-unread" || { echo "FAIL: the ticket of a process ps cannot read is dead"; exit 1; }
  ! _gl_reclaim > /dev/null && [ -f "$_gl_s/owner" ] ||
    { echo "FAIL: the slot of a process ps cannot read was reclaimed"; exit 1; }
  unset -f ps
  ! _gl_running "$dead" || { echo "FAIL: a PID ps does not find is running"; exit 1; }
  ! _gl_alive "$tmp/ticket-unread" || { echo "FAIL: the ticket of a PID ps does not find is alive"; exit 1; }
  _gl_reclaim > /dev/null && [ ! -d "$_gl_s" ] ||
    { echo "FAIL: the slot of a PID ps does not find was not reclaimed"; exit 1; }
) || exit 1
echo "ok: a process that cannot be read holds its slot, and one ps does not find loses it"

# Libproc and ps. A ticket is written by gate_take as "<pid>", its start
# time and the worktree, one a line.
(
  . "$script"
  _gl_libproc "$$" > /dev/null || { echo "skipped: libproc does not read this shell"; exit 0; }
  sleep 30 &
  live=$!
  sh -c : &
  dead=$!
  wait "$dead"
  lp=$(_gl_started "$live") lpdead=$(_gl_started "$dead")
  printf '%s\n%s\n%s\n' "$live" "$lp" wt > "$tmp/ticket-libproc"
  _gl_libproc() { return 2; }
  ps=$(_gl_started "$live") psdead=$(_gl_started "$dead")
  printf '%s\n%s\n%s\n' "$live" "$ps" wt > "$tmp/ticket-ps"
  _gl_alive "$tmp/ticket-libproc" || { echo "FAIL: ps reads a ticket written through libproc as dead"; kill "$live"; exit 1; }
  . "$script"
  _gl_alive "$tmp/ticket-ps" || { echo "FAIL: libproc reads a ticket written through ps as dead"; kill "$live"; exit 1; }
  kill "$live"
  [ -n "$lp" ] && [ "$lp" = "$ps" ] || { echo "FAIL: libproc '$lp', ps '$ps'"; exit 1; }
  [ -z "$lpdead" ] && [ -z "$psdead" ] || { echo "FAIL: dead pid: libproc '$lpdead', ps '$psdead'"; exit 1; }
  echo "ok: libproc and ps both read '$lp' for a live process and nothing for a dead one"
  # a zombie: the shell that exec's sleep never waits for its child
  sh -c 'sleep 0 & echo $! > "$1"; exec sleep 30' sh "$tmp/zombie" &
  parent=$!
  i=0
  until [ -s "$tmp/zombie" ] && read -r zombie < "$tmp/zombie" &&
    case $(ps -o stat= -p "$zombie") in Z*) true ;; *) false ;; esac; do
    i=$((i + 1))
    [ "$i" -le 30 ] || { echo "FAIL: no zombie to read"; kill "$parent"; exit 1; }
    sleep 1
  done
  _gl_libproc "$zombie" > /dev/null
  rc=$?
  # with ps refused, libproc alone says that both are gone
  ps() { return 126; }
  _gl_d=$tmp/refused _gl_me=$$
  _gl_s=$_gl_d/gate.lock
  for pid in "$dead" "$zombie"; do
    mkdir -p "$_gl_s"
    echo "$pid 0 wt" > "$_gl_s/owner"
    printf '%s\n%s\n%s\n' "$pid" "Mon Nov 2 00:00:00 2026" wt > "$tmp/ticket-refused"
    ! _gl_running "$pid" && ! _gl_alive "$tmp/ticket-refused" &&
      _gl_reclaim > /dev/null && [ ! -d "$_gl_s" ] || {
      echo "FAIL: with ps refused, PID $pid, gone to libproc, kept its ticket or slot"
      kill "$parent"
      exit 1
    }
  done
  unset -f ps
  kill "$parent"
  [ "$rc" -eq 3 ] || { echo "FAIL: libproc read the zombie $zombie with exit $rc, not 3"; exit 1; }
  echo "ok: libproc reads a zombie, which ps lists, as gone"
  echo "ok: with ps refused, a dead PID and a zombie lost their ticket and slot"
) || exit 1

# gate_peak, under each shell: a program that exits 7 returns 7, and one
# line is appended, five fields of the forms the header gives, a tab in the
# kind written as a space.
pids=""
for shell in sh bash zsh dash; do
  command -v "$shell" > /dev/null || { echo "skipped: no $shell for gate_peak"; continue; }
  rm -rf "${GATE_LOCK_DIR:?}"
  rc=0
  "$shell" -c '. "$1"; gate_peak "$2" /abs/wt sh -c "exit 7"' "$shell" "$script" "$(printf 'a\tb')" ||
    rc=$?
  [ "$rc" -eq 7 ] || fail "under $shell, gate_peak returned $rc, not the program's 7"
  [ "$(wc -l < "$GATE_LOCK_DIR/gate.peaks")" -eq 1 ] ||
    fail "under $shell, gate.peaks does not hold one line"
  awk -F '\t' 'NF != 5 || $1 !~ /^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$/ ||
    $2 != "a b" || $3 != "/abs/wt" || $4 !~ /^([0-9]+|[?])$/ || $5 != 7 { exit 1 }' \
    "$GATE_LOCK_DIR/gate.peaks" ||
    { cat "$GATE_LOCK_DIR/gate.peaks"; fail "under $shell, the line of gate.peaks is not well formed"; }
  echo "ok: under $shell, gate_peak returned 7 and appended: $(cat "$GATE_LOCK_DIR/gate.peaks")"
done

# A program a signal ends returns 128 plus its number, as the shell gives
# it: 137 for KILL, which macOS's time alone turns into 1.
rm -rf "${GATE_LOCK_DIR:?}"
rc=0
sh -c '. "$1"; gate_peak killed /abs/wt sh -c "kill -KILL \$\$"' sh "$script" || rc=$?
[ "$rc" -eq 137 ] || fail "a program killed with KILL returned $rc through gate_peak, not 137"
[ "$(cut -f 5 "$GATE_LOCK_DIR/gate.peaks")" = 137 ] ||
  fail "gate.peaks does not record 137 for a program killed with KILL"
echo "ok: a program killed with KILL returned 137, and gate.peaks records it"

# Time's output file: gate_peak removes its own, and one left by a shell
# that is gone, and keeps one whose shell is alive.
rm -rf "${GATE_LOCK_DIR:?}"
mkdir -p "$GATE_LOCK_DIR"
sh -c : &
dead=$!
wait "$dead"
: > "$GATE_LOCK_DIR/peak.$dead.left"
: > "$GATE_LOCK_DIR/peak.$$.live"
sh -c '. "$1"; gate_peak k /abs/wt true' sh "$script" || fail "gate_peak failed on true"
[ ! -e "$GATE_LOCK_DIR/peak.$dead.left" ] || fail "gate_peak kept the file of a shell that is gone"
[ -e "$GATE_LOCK_DIR/peak.$$.live" ] || fail "gate_peak removed the file of a live shell"
rm -f "$GATE_LOCK_DIR/peak.$$.live"
left=""
for f in "$GATE_LOCK_DIR"/peak.*; do [ ! -e "$f" ] || left="$left ${f##*/}"; done
[ -z "$left" ] || fail "gate_peak left $left"
echo "ok: gate_peak removed its own file and one of a shell that is gone, and kept a live shell's"

# Where neither time can run, as with no file for its output, gate_peak runs
# the program through /proc, here a tree of the test's holding only
# self/status, or else alone. Under each shell, the program reads the
# caller's stdin and its exit code comes back.
mkdir -p "$tmp/fakeproc/self"
: > "$tmp/fakeproc/self/status"
for shell in sh bash zsh dash; do
  command -v "$shell" > /dev/null || { echo "skipped: no $shell for the fallbacks"; continue; }
  for proc in "$tmp/fakeproc" "$tmp/noproc"; do
    rm -rf "${GATE_LOCK_DIR:?}"
    got=$(printf 'brief\n' | "$shell" -c '
      . "$1"
      mktemp() { return 1; }
      _gl_proc=$2
      gate_peak k /abs/wt cat
      gate_peak k /abs/wt sh -c "exit 7" < /dev/null
      echo "rc=$?"' "$shell" "$script" "$proc")
    [ "$got" = "$(printf 'brief\nrc=7')" ] ||
      fail "under $shell, with _gl_proc at ${proc##*/}, the fallback printed '$got'"
    [ "$(cut -f 4,5 "$GATE_LOCK_DIR/gate.peaks" | tr '\t\n' ' ,')" = "? 0,? 7," ] ||
      fail "under $shell, with _gl_proc at ${proc##*/}, gate.peaks holds $(cat "$GATE_LOCK_DIR/gate.peaks")"
  done
  echo "ok: under $shell, through /proc and alone, the program read stdin and returned its code"
done
rm -rf "${GATE_LOCK_DIR:?}"

# The peak of a known allocation: a program holding 200 MB reads between
# 200 and 300 MB, in KB.
if command -v python3 > /dev/null; then
  rm -rf "${GATE_LOCK_DIR:?}"
  sh -c '. "$1"; gate_peak alloc /abs/wt python3 -c "import time; b = bytearray(200 * 2**20); time.sleep(2)"' \
    sh "$script" || fail "gate_peak failed on the allocation"
  kb=$(cut -f 4 "$GATE_LOCK_DIR/gate.peaks")
  # no reader of the peak, as in Codex's sandbox, which refuses time -l
  if [ "$kb" = "?" ] && ! /usr/bin/time -l true > /dev/null 2>&1 &&
    ! /usr/bin/time -v true > /dev/null 2>&1 && [ ! -r /proc/self/status ]; then
    echo "skipped: no time or /proc reads a peak here"
  else
    case $kb in "" | *[!0-9]*) fail "the peak of the allocation is '$kb'" ;; esac
    [ "$kb" -ge 204800 ] && [ "$kb" -le 307200 ] ||
      fail "the peak of 200 MB held is $kb KB, outside 204800 to 307200"
    echo "ok: a program holding 200 MB peaked at $kb KB"
  fi
else
  echo "skipped: no python3 to allocate 200 MB"
fi
rm -rf "${GATE_LOCK_DIR:?}"

# The output of each time, GNU's -v in KB and macOS's -l in bytes, read as
# KB, and an output with neither as nothing.
(
  . "$script"
  bad=0
  got=$(printf '\tCommand being timed: "x"\n\tMaximum resident set size (kbytes): 215032\n\tExit status: 0\n' | _gl_peak_kb)
  [ "$got" = 215032 ] || { echo "FAIL: GNU time read as '$got', want 215032"; bad=1; }
  got=$(printf '        0,06 real         0,02 user\n           223166464  maximum resident set size\n           215581272  peak memory footprint\n' | _gl_peak_kb)
  [ "$got" = 217936 ] || { echo "FAIL: macOS time read as '$got', want 217936"; bad=1; }
  got=$(printf 'time: command terminated abnormally\n' | _gl_peak_kb)
  [ -z "$got" ] || { echo "FAIL: an output with no peak read as '$got'"; bad=1; }
  exit "$bad"
) || exit 1
echo "ok: the peak is read in KB from GNU time and from macOS time"

# /proc, in a tree of the test's: the largest VmHWM of a process and those
# below it, and a failure once the process shows none, as a zombie.
(
  . "$script"
  _gl_proc=$tmp/proc
  hwm() { # <pid> <KB or -> <children>
    mkdir -p "$_gl_proc/$1/task/$1"
    if [ "$2" = - ]; then printf 'Name:\tx\nState:\tZ (zombie)\n'
    else printf 'Name:\tx\nVmPeak:\t 99999999 kB\nVmHWM:\t %s kB\n' "$2"; fi > "$_gl_proc/$1/status"
    # shellcheck disable=SC2086
    [ -z "$3" ] || printf '%s ' $3 > "$_gl_proc/$1/task/$1/children"
  }
  hwm 100 1000 "200 300"
  hwm 200 3000 "400"
  hwm 300 2000 ""
  hwm 400 5000 ""
  hwm 500 - ""
  hwm 600 6000 ""
  _gl_hwm 100 || { echo "FAIL: _gl_hwm failed on a live process"; exit 1; }
  # _gl_hwm, of the sourced script, sets _gl_hm
  # shellcheck disable=SC2154
  [ "$_gl_hm" = 5000 ] || { echo "FAIL: _gl_hwm read $_gl_hm, want the grandchild's 5000"; exit 1; }
  # a child that a thread other than the main one started
  mkdir -p "$_gl_proc/100/task/101"
  printf '600 ' > "$_gl_proc/100/task/101/children"
  _gl_hwm 100 && [ "$_gl_hm" = 6000 ] ||
    { echo "FAIL: _gl_hwm read $_gl_hm, want the thread's child's 6000"; exit 1; }
  ! _gl_hwm 500 || { echo "FAIL: _gl_hwm read a zombie as live"; exit 1; }
  ! _gl_hwm 700 || { echo "FAIL: _gl_hwm read a missing process as live"; exit 1; }
) || exit 1
echo "ok: /proc gives the largest VmHWM of a process and those below it, and none once it has ended"
