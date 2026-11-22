# shellcheck shell=sh
# The gate lock, by default one per user, shared by every worker of every
# session that user runs. It has GATE_LOCK_SLOTS slots, 3 by default, so
# that many workers gate at once. POSIX sh, sourced in the same shell call
# that runs the gates, by sh, bash or zsh, in the main shell or in a
# `( ... ) &` subshell. writing.md's "The gates" (the gate lock) says in
# which shell gate_release runs, and where a timeout goes.
# GATE_LOCK_WORKERS, the `-n` of a suite run in a slot, is by default the
# cores divided by the slots (3 on 10 cores), and GATE_LOCK_LOAD, a
# ceiling, 3 times the cores (30 on 10). Sourcing sets each of them that
# is not already set:
#
#   . "${PROCESS:?}/scripts/gate-lock.sh"
#   gate_take [<worktree>] && {
#     gate_wait; rc=0
#     gate_peak hooks <worktree> <a gate> || rc=$?; echo "EXIT_hooks=$rc"
#     if [ "$rc" -eq 0 ]; then
#       gate_wait; rc=0
#       gate_peak <gate> <worktree> <a gate> || rc=$?; echo "EXIT_<gate>=$rc"
#     fi
#     gate_release
#   }
#
# A load generator takes every slot with gate_take_all and releases them with
# gate_release_all. One runs at a time.
#
# gate_peak runs a program and records its peak memory and its wall time. It
# takes no slot and admits nothing: it only records. Each gate in the block
# above runs through it, and so does a reviewer an orchestrator starts as a
# command, with `codex exec` or `claude -p`. A run not started through it is
# not recorded:
#
#   gate_peak <kind> <tree> <program> [<argument>...]
#   gate_peak suite /abs/wt timeout 1800 uv run pytest -n "$GATE_LOCK_WORKERS"
#   gate_peak codex /abs/work/reviewer env -i ... codex exec ...
#
# <program> is a program, not a shell function, since time runs it. It
# returns the program's exit code and appends one line to
# $GATE_LOCK_DIR/gate.peaks, tab-separated: the UTC time the program ended,
# <kind>, <tree>, the peak resident memory in KB (`?` where it could not be
# read), that exit code, and the wall time in whole seconds, the difference
# of `date +%s` before and after the program. A tab or a newline in <kind>
# or <tree> is written as a space. The peak is read with `/usr/bin/time -l`
# on macOS and GNU `/usr/bin/time -v` elsewhere, which run the program
# through sh, so that one a signal ends returns 128 plus its number, as 137
# for KILL: macOS's time alone returns 1 for it. time writes into a file
# beside the lock, which a later gate_peak removes where an interrupt left
# it. Where neither time runs, the peak is the largest VmHWM that /proc
# shows, once a second while the program runs, of the program and the
# processes /proc lists below it. The program then runs as a background job,
# which ignores SIGINT: TERM, as timeout sends, still stops it, and an
# interrupt that ends the calling shell leaves it running, outside the lock.
# Where none of the three can read the peak, the program runs alone and the
# peak is `?`, as in Codex's workspace-write sandbox, which refuses
# `time -l` a sysctl it reads.
#
# The peak is that of the largest single process, not the sum over the
# program's processes: of two processes of 200 MB at once it reads about
# 200 MB. A process still running when its parent ends, as a daemon, is not
# counted. /proc also misses what a process gains in its last second, and a
# process that starts and ends between two reads. So a line is a lower
# bound on what the run held at once. Read by time, it also bounds it from
# above: a run that held N processes at once, as a suite's workers and its
# controller, held at most N times its peak, daemons aside. An agent that
# runs inside the session's own client, as a Claude Code subagent does, has
# no process of its own to wrap, and is not recorded.
#
# The slots and the queue sit in $GATE_LOCK_DIR, by default
# /tmp/claude-<uid>/gate. The first slot is the directory gate.lock, the
# others gate.lock.2, gate.lock.3 and so on. A script that knows one lock
# only takes gate.lock, so its holder fills the first slot.
# `gate_take <scratchpad> <worktree>` and `gate_release <scratchpad>` take
# and release a slot as the one-argument forms do: the scratchpad is
# ignored.
#
# Waiters queue in arrival order. gate_take writes a ticket into
# $GATE_LOCK_DIR/gate.queue, named by its arrival time and PID, and waits
# until its ticket is the oldest one whose process is alive. Then it waits,
# as gate_wait does, and takes the first free slot, so that nobody holds a
# slot while only waiting, a load generator excepted. While a slot is held,
# it takes none within GATE_LOCK_STAGGER seconds of the last take recorded
# in gate.last, so that the idle reading shows the gate just started. While
# a slot is held, it also takes none within GATE_LOCK_SETTLE seconds (60) of
# that take, unless it read GATE_LOCK_FREE plus GATE_LOCK_MARGIN percent (30
# plus 15) of memory or more free: a gate reaches its peak memory after it
# starts, so gates taken seconds apart would each see the same free memory
# and together exceed it. A slot is held while its owner file names a live
# process, so that a stale slot does not hold the next take back. gate.last
# sits in $GATE_LOCK_DIR and is written aside and renamed. gate_wait waits
# until GATE_LOCK_IDLE percent or more of the CPU was idle over the last
# GATE_LOCK_POLL seconds, the 1-minute load is under GATE_LOCK_LOAD,
# GATE_LOCK_DISK GB or more of disk is free where $GATE_LOCK_DIR sits (/tmp
# when it is unset), and memory is admissible: a pressure level below 4
# (macOS answers 1 normal, 2 warn, 4 critical) with GATE_LOCK_FREE percent
# (30) of memory or more free. It adds no peak to that reading, since it is
# not told which gate follows. Where the level cannot be read, the
# percentage free decides alone. Where any other read fails, as off macOS,
# it does not wait on that read. It prints the idle percentage, the load,
# the level, the percentage free and the disk free, `?` for each read that
# failed, and then names those reads. The idle percentage is the gate; the
# load, which on macOS counts threads that use no CPU, is only a ceiling
# that catches a runaway. These waits have no bound, nor has the wait for
# gate.generator: holders that never finish keep every waiter waiting. This
# names them:
#
#   cat "${GATE_LOCK_DIR:-/tmp/claude-$(id -u)/gate}"/gate.lock*/owner
#   cat "${GATE_LOCK_DIR:-/tmp/claude-$(id -u)/gate}"/gate.generator/owner
#
# and this the waiters, each line of a ticket after its file name:
#
#   grep -r . "${GATE_LOCK_DIR:-/tmp/claude-$(id -u)/gate}"/gate.queue
#
# To check, from the repository root in a fresh sh, with a directory of
# your own so as not to wait on a real gate:
#
#   . scripts/gate-lock.sh
#   GATE_LOCK_DIR=$(mktemp -d); export GATE_LOCK_DIR
#   gate_take; echo $?
#   gate_release; echo $?
#   rm -r "$GATE_LOCK_DIR"
#
# A ticket holds its PID, that process's start time, read in UTC, and the
# worktree. A ticket whose process is gone, or whose PID now belongs to a
# process started at another time, is dead, and any waiter removes it.
# A start time, and whether a process is alive, are read through libproc's
# proc_pidinfo from /usr/bin/python3, which Codex's sandbox allows where it
# refuses ps, and through ps where libproc cannot answer, as off macOS.
# A process is gone only where one of them answers that no process has its
# PID. A process neither can read, as another user's under that sandbox,
# counts as alive: a live one releases as any holder does, and a gone one
# keeps its ticket or slot until the human removes it (a slot as below, a
# ticket from gate.queue). Such a slot is one slot fewer; such a ticket,
# once the oldest, holds every waiter behind it, and such a gate.generator
# every generator.
#
# Codex's workspace-write sandbox refuses sysctl and iostat. There the load
# is read through uptime, the percentage free through memory_pressure, and
# the idle percentage through Mach's host_statistics from /usr/bin/python3.
# The sandbox refuses the pressure level to sysctl, by name and by number.
#
# gate_take writes the holder's PID into the slot's owner file, so that
# only the holder releases it. A slot whose holder's process is gone is
# stale, and gate_take removes it.
#
# Reclaiming renames the owner file, which only one waiter wins (mv is
# atomic; the others find no file). The winner reads the PID in what it
# moved: only if that is the dead PID it judged stale does it remove the
# slot. Otherwise its read was out of date and it moved a live holder's
# file, which it puts back at once. While a slot has no owner file nobody
# reclaims it, and gate_release reads again for up to 5 seconds. A slot made
# by hand with mkdir, or left by a waiter killed while it held the owner file
# renamed to stale.<pid>, has no owner file. Nor is a gate.generator with
# no owner file reclaimed. The human removes either by its directory name,
# after checking that no gate runs in it:
#
#   rm -r "${GATE_LOCK_DIR:-/tmp/claude-$(id -u)/gate}"/<slot>

# The number of cores
_gl_ncpu() {
  sysctl -n hw.ncpu 2>/dev/null || getconf _NPROCESSORS_ONLN 2>/dev/null ||
    nproc 2>/dev/null || echo 1
}

# The load ceiling and the workers follow the cores, so that they hold on any machine
_gl_cpus=$(_gl_ncpu)
GATE_LOCK_SLOTS=${GATE_LOCK_SLOTS:-3}
[ "$GATE_LOCK_SLOTS" -ge 1 ] 2>/dev/null || GATE_LOCK_SLOTS=1
GATE_LOCK_LOAD=${GATE_LOCK_LOAD:-$((_gl_cpus * 3))}
GATE_LOCK_IDLE=${GATE_LOCK_IDLE:-30}
GATE_LOCK_WORKERS=${GATE_LOCK_WORKERS:-$((_gl_cpus / GATE_LOCK_SLOTS))}
[ "$GATE_LOCK_WORKERS" -ge 1 ] || GATE_LOCK_WORKERS=1
GATE_LOCK_FREE=${GATE_LOCK_FREE:-30}
GATE_LOCK_DISK=${GATE_LOCK_DISK:-20}
GATE_LOCK_STAGGER=${GATE_LOCK_STAGGER:-15}
GATE_LOCK_SETTLE=${GATE_LOCK_SETTLE:-60}
GATE_LOCK_MARGIN=${GATE_LOCK_MARGIN:-15}
GATE_LOCK_POLL=${GATE_LOCK_POLL:-5}

_gl_dir() {
  _gl_d=${GATE_LOCK_DIR:-/tmp/claude-$(id -u)/gate}
  [ -d "$_gl_d" ] || (umask 077 && mkdir -p "$_gl_d") || {
    echo "gate lock: cannot create '$_gl_d'"
    return 1
  }
}

# Sets _gl_me to the PID of the shell that calls it. `$$` is not that PID in
# a subshell: it stays the main shell's, which may be gone while a
# background `( ... ) &` still gates, and is shared by sibling subshells.
# A command run from this shell, with its output redirected and not
# substituted, has this shell as its parent. The file is outside
# $GATE_LOCK_DIR, which a waiter reads, and `>|` writes it under noclobber.
_gl_self() {
  _gl_sf=$(mktemp "${TMPDIR:-/tmp}/gate-lock.self.XXXXXX") || return 1
  sh -c 'echo $PPID' >| "$_gl_sf"
  _gl_me=""
  read -r _gl_me < "$_gl_sf"
  rm -f "$_gl_sf"
  [ -n "$_gl_me" ] || { echo "gate lock: cannot read this shell's PID"; return 1; }
}

# The directory of slot $1: gate.lock for the first, gate.lock.<n> after it
_gl_slot() {
  if [ "$1" -eq 1 ]; then _gl_s="$_gl_d/gate.lock"
  else _gl_s="$_gl_d/gate.lock.$1"; fi
}

# The start time of PID $1 read through libproc, as _gl_started prints it.
# Exits 3 where no process has that PID, and any other code but 0 where
# libproc cannot answer: off macOS, without /usr/bin/python3, or for
# another user's process.
_gl_libproc() {
  /usr/bin/python3 -I -c '
import ctypes, errno, struct, sys, time
try:
    proc_pidinfo = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True).proc_pidinfo
except (OSError, AttributeError):
    sys.exit(2)
pid = int(sys.argv[1])
# PROC_PIDTBSDINFO fills a struct proc_bsdinfo of 136 bytes, its pid at
# offset 12 and its start time in seconds at offset 120
info = ctypes.create_string_buffer(136)
if proc_pidinfo(pid, 3, ctypes.c_uint64(0), info, 136) != 136:
    sys.exit(3 if ctypes.get_errno() == errno.ESRCH else 2)
if struct.unpack_from("=I", info, 12)[0] != pid:
    sys.exit(2)
t = time.gmtime(struct.unpack_from("=Q", info, 120)[0])
print("%s %s %d %02d:%02d:%02d %d" % (
    "Mon Tue Wed Thu Fri Sat Sun".split()[t.tm_wday],
    "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()[t.tm_mon - 1],
    t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec, t.tm_year))
' "$1" 2>/dev/null
}

# Prints the start time of PID $1, in UTC, as `ps -o lstart=` prints it
# with its spaces squeezed. Fails with 1 where no process has that PID, and
# with 2 where neither libproc nor ps can tell. Tickets carry the time, so
# libproc and ps print the same text: a ticket written through one is read
# through the other. A zombie, which ps still lists, libproc reads as gone.
_gl_started() {
  _gl_libproc "$1" && return 0
  [ $? -eq 3 ] && return 1
  # ps exits 1 for a PID it does not find; the shell gives 126 or 127 where
  # ps is refused or absent
  _gl_ps=$(LC_ALL=C TZ=UTC0 ps -o lstart= -p "$1" 2>/dev/null)
  case $? in
    0) ;;
    1) return 1 ;;
    *) return 2 ;;
  esac
  [ -n "$_gl_ps" ] || return 2
  # ps pads the time with spaces, which `read` strips: squeeze them so that
  # the ticket and a fresh read compare equal
  echo "$_gl_ps" | tr -s ' ' | sed 's/^ //; s/ $//'
}

# Succeeds unless no process has PID $1
_gl_running() {
  _gl_started "$1" >/dev/null
  [ $? -ne 1 ]
}

_gl_alive() {
  # $1 is a ticket: "<pid>" on its first line, its start time on the second
  _gl_tpid="" _gl_tstart=""
  { { read -r _gl_tpid; read -r _gl_tstart; } < "$1"; } 2>/dev/null || return 1
  [ -n "$_gl_tpid" ] && [ -n "$_gl_tstart" ] || return 1
  _gl_tnow=$(_gl_started "$_gl_tpid")
  case $? in
    0) [ "$_gl_tnow" = "$_gl_tstart" ] ;;
    1) return 1 ;;
    *) return 0 ;;
  esac
}

# The 1-minute load, read under LC_ALL=C because some locales print a
# decimal comma. Where sysctl is refused, uptime reads it.
_gl_load() {
  if [ -r /proc/loadavg ]; then cut -d' ' -f1 /proc/loadavg; return; fi
  _gl_o=$(LC_ALL=C sysctl -n vm.loadavg 2>/dev/null | cut -d' ' -f2)
  [ -n "$_gl_o" ] ||
    _gl_o=$(LC_ALL=C uptime 2>/dev/null | sed -n 's/.*load averages*: *\([0-9.]*\).*/\1/p')
  [ -z "$_gl_o" ] || echo "$_gl_o"
}

# The percentage of CPU idle over the next $1 seconds, read through Mach's
# host_statistics from /usr/bin/python3. Exits 2 at once where it cannot
# read, and prints nothing after the wait where the second read fails.
_gl_ticks() {
  /usr/bin/python3 -I -c '
import ctypes, sys, time
try:
    lib = ctypes.CDLL("/usr/lib/libSystem.dylib")
    lib.mach_host_self.restype = ctypes.c_uint
    host = lib.mach_host_self()
except (OSError, AttributeError):
    sys.exit(2)
def ticks():
    # HOST_CPU_LOAD_INFO fills the user, system, idle and nice ticks
    t = (ctypes.c_uint * 4)()
    n = ctypes.c_uint(4)
    return list(t) if lib.host_statistics(host, 3, t, ctypes.byref(n)) == 0 else None
t0 = ticks()
if t0 is None:
    sys.exit(2)
time.sleep(float(sys.argv[1]))
t1 = ticks()
if t1 is not None:
    # the counters are 32 bits wide and wrap
    d = [(b - a) % 2**32 for a, b in zip(t0, t1)]
    if sum(d) > 0:
        print(d[2] * 100 // sum(d))
' "$1" 2>/dev/null
}

# The percentage of CPU idle over the next GATE_LOCK_POLL seconds, as an
# integer. The read is the wait of a poll, so that a poll costs the same
# time whether or not the read works. Linux reads /proc/stat twice; macOS
# reads the second line of `iostat -c 2`, the first being the average since
# boot, and where iostat is refused, _gl_ticks. Where all fail it prints
# nothing.
_gl_idle() {
  if [ -r /proc/stat ]; then
    { head -n 1 /proc/stat; sleep "$GATE_LOCK_POLL"; head -n 1 /proc/stat; } |
      awk '{ t = 0; for (i = 2; i <= NF; i++) t += $i
             if (NR == 1) { t0 = t; i0 = $5 }
             else if (t > t0) print int(($5 - i0) * 100 / (t - t0)) }'
  else
    _gl_o=$(LC_ALL=C iostat -c 2 -w "$GATE_LOCK_POLL" 2>/dev/null |
      awk 'END { if ($(NF-3) ~ /^[0-9]+$/) print $(NF-3) }')
    [ -n "$_gl_o" ] || _gl_o=$(_gl_ticks "$GATE_LOCK_POLL") || sleep "$GATE_LOCK_POLL"
    [ -z "$_gl_o" ] || echo "$_gl_o"
  fi
}

_gl_level() { sysctl -n kern.memorystatus_vm_pressure_level 2>/dev/null; }

# Where sysctl is refused, memory_pressure reads the same percentage
_gl_free() {
  sysctl -n kern.memorystatus_level 2>/dev/null ||
    memory_pressure -Q 2>/dev/null |
      sed -n 's/^System-wide memory free percentage: \([0-9]*\)%$/\1/p'
}

# GB available, in units of 1024^3 bytes as `df -g` counts them
_gl_disk() {
  LC_ALL=C df -Pk "${GATE_LOCK_DIR:-/tmp}" 2>/dev/null |
    awk 'NR == 2 { print int($4 / 1048576) }'
}

# Reads idle, load, level, free and disk into _gl_u, _gl_l, _gl_p, _gl_f and
# _gl_g; succeeds when all five admit a gate. An empty read admits.
_gl_admit() {
  _gl_u=$(_gl_idle 2>/dev/null) _gl_l=$(_gl_load 2>/dev/null)
  _gl_p=$(_gl_level) _gl_f=$(_gl_free) _gl_g=$(_gl_disk)
  [ -z "$_gl_u" ] || [ "$_gl_u" -ge "$GATE_LOCK_IDLE" ] || return 1
  [ -z "${_gl_l%.*}" ] || [ "${_gl_l%.*}" -lt "$GATE_LOCK_LOAD" ] || return 1
  [ -z "$_gl_g" ] || [ "$_gl_g" -ge "$GATE_LOCK_DISK" ] || return 1
  [ -z "$_gl_p" ] || [ "$_gl_p" -lt 4 ] || return 1
  [ -z "$_gl_f" ] || [ "$_gl_f" -ge "$GATE_LOCK_FREE" ]
}

# The readings, then the names of those that could not be read
_gl_status() {
  _gl_x=""
  [ -n "$_gl_u" ] || _gl_x="$_gl_x, CPU idle"
  [ -n "$_gl_l" ] || _gl_x="$_gl_x, load"
  [ -n "$_gl_p" ] || _gl_x="$_gl_x, memory pressure level"
  [ -n "$_gl_f" ] || _gl_x="$_gl_x, memory free"
  [ -n "$_gl_g" ] || _gl_x="$_gl_x, disk free"
  echo "${_gl_u:-?}% CPU idle, load ${_gl_l:-?}, memory pressure level ${_gl_p:-?}, ${_gl_f:-?}% free, ${_gl_g:-?} GB disk free${_gl_x:+; not read: ${_gl_x#, }}"
}

# Succeeds when $1 seconds or more have passed since the last take, or when
# the time of the last take is unreadable or in the future
_gl_spaced() {
  _gl_last=""
  [ -r "$_gl_d/gate.last" ] && read -r _gl_last < "$_gl_d/gate.last"
  case $_gl_last in
    "" | *[!0-9]* | 0?* | ???????????*) return 0 ;;
  esac
  _gl_gap=$(($(date +%s) - _gl_last))
  [ "$_gl_gap" -lt 0 ] || [ "$_gl_gap" -ge "$1" ]
}

# Succeeds when the last take has settled, or when the percentage free that
# _gl_admit read leaves the margin
_gl_settled() {
  _gl_spaced "$GATE_LOCK_SETTLE" || {
    [ -n "$_gl_f" ] && [ "$_gl_f" -ge $((GATE_LOCK_FREE + GATE_LOCK_MARGIN)) ]
  }
}

# Succeeds when the owner file of a slot names a live process
_gl_held() {
  _gl_hn=1
  # counted rather than globbed: zsh stops at a glob with no match
  while [ "$_gl_hn" -le "$GATE_LOCK_SLOTS" ]; do
    _gl_slot "$_gl_hn"
    _gl_hn=$((_gl_hn + 1))
    _gl_hpid=""
    [ -r "$_gl_s/owner" ] && read -r _gl_hpid _ < "$_gl_s/owner"
    [ -n "$_gl_hpid" ] && _gl_running "$_gl_hpid" && return 0
  done
  return 1
}

# Records now as the time of the last take. It is written before the ticket
# is removed, so that the next head reads it. The rename keeps a reader from
# a half written file.
_gl_stamp() {
  date +%s > "$_gl_d/.last.$_gl_me" && mv "$_gl_d/.last.$_gl_me" "$_gl_d/gate.last"
}

gate_wait() {
  until _gl_admit; do :; done
  echo "gate_wait: $(_gl_status)"
}

# Removes slot $_gl_s if its holder's process is gone; succeeds if it did
_gl_reclaim() {
  _gl_pid=""
  [ -r "$_gl_s/owner" ] && read -r _gl_pid _ < "$_gl_s/owner"
  [ -n "$_gl_pid" ] || return 1
  ! _gl_running "$_gl_pid" || return 1
  mv "$_gl_s/owner" "$_gl_s/stale.$_gl_me" 2>/dev/null || return 1
  _gl_now=""
  read -r _gl_now _ < "$_gl_s/stale.$_gl_me"
  if [ "$_gl_now" = "$_gl_pid" ]; then
    echo "${_gl_s##*/} of pid $_gl_pid is stale, its process gone: removed"
    rm -f "$_gl_s/stale.$_gl_me"
    rmdir "$_gl_s" 2>/dev/null
    return 0
  fi
  mv "$_gl_s/stale.$_gl_me" "$_gl_s/owner"
  return 1
}

gate_take() {
  _gl_dir && _gl_self || return 1
  _gl_wt=${2:-${1:-}}
  _gl_queue="$_gl_d/gate.queue"
  _gl_start=$(_gl_started "$_gl_me")
  [ -n "$_gl_start" ] || {
    echo "gate_take: cannot read the start time of pid $_gl_me"
    return 1
  }
  _gl_ticket="$_gl_queue/$(date +%s).$(printf '%010d' "$_gl_me")"
  while :; do
    # written aside and renamed, so that no waiter reads it half written,
    # and written again if a waiter removed it, so that it keeps its place
    [ -f "$_gl_ticket" ] || {
      mkdir -p "$_gl_queue" &&
      printf '%s\n%s\n%s\n' "$_gl_me" "$_gl_start" "$_gl_wt" > "$_gl_queue/.$_gl_me" &&
        mv "$_gl_queue/.$_gl_me" "$_gl_ticket" &&
        # long enough for a ticket written at the same moment to be seen
        # by the first scan, so that two new waiters do not both find
        # themselves at the head
        sleep 1
    }
    _gl_head=""
    # listed rather than globbed: zsh stops at a glob with no match. The
    # names are digits and a dot, so each line is one whole name.
    while read -r _gl_t; do
      _gl_t="$_gl_queue/$_gl_t"
      [ -f "$_gl_t" ] || continue
      if _gl_alive "$_gl_t"; then _gl_head=$_gl_t; break; fi
      rm -f "$_gl_t"
    done <<EOF
$(ls "$_gl_queue" 2>/dev/null)
EOF
    [ "$_gl_head" = "$_gl_ticket" ] || { sleep "$GATE_LOCK_POLL"; continue; }
    ! _gl_held || _gl_spaced "$GATE_LOCK_STAGGER" || { sleep "$GATE_LOCK_POLL"; continue; }
    _gl_admit || continue
    # no sleep here: the admit above waited a poll
    ! _gl_held || _gl_settled || continue
    _gl_i=1
    while [ "$_gl_i" -le "$GATE_LOCK_SLOTS" ]; do
      _gl_slot "$_gl_i"
      if mkdir "$_gl_s" 2>/dev/null; then
        echo "$_gl_me $(date +%s) $_gl_wt" > "$_gl_s/owner"
        _gl_stamp
        rm -f "$_gl_ticket"
        echo "${_gl_s##*/} taken by $_gl_me at $(_gl_status)"
        return 0
      fi
      _gl_reclaim
      _gl_i=$((_gl_i + 1))
    done
    # no sleep here: the admit above waited a poll
  done
}

gate_release() {
  _gl_dir && _gl_self || return 1
  _gl_i=0
  while [ "$_gl_i" -lt 5 ]; do
    # a slot with no owner file may be ours, its file renamed by a waiter
    # that is about to put it back
    _gl_unowned="" _gl_n=1
    # counted rather than globbed: zsh stops at a glob with no match
    while [ "$_gl_n" -le "$GATE_LOCK_SLOTS" ]; do
      _gl_slot "$_gl_n"
      _gl_n=$((_gl_n + 1))
      [ -d "$_gl_s" ] || continue
      _gl_pid=""
      [ -r "$_gl_s/owner" ] && read -r _gl_pid _ < "$_gl_s/owner"
      if [ "$_gl_pid" = "$_gl_me" ]; then
        rm -f "$_gl_s/owner"
        rmdir "$_gl_s" 2>/dev/null &&
          { echo "${_gl_s##*/} released by $_gl_me"; return 0; }
      elif [ -z "$_gl_pid" ]; then
        _gl_unowned=1
      fi
    done
    [ -n "$_gl_unowned" ] || break
    _gl_i=$((_gl_i + 1)); sleep 1
  done
  echo "no gate slot is held by $_gl_me: left alone"
  return 1
}

# A load generator takes every slot. Two generators that each took slots one
# by one would split them and wait on each other for ever, so the generator
# first takes gate.generator, a directory holding an owner file as a slot
# does, and removed as a stale slot is. Then it takes every slot. While it
# waits for the rest it holds the slots it has. process/load-generator.md
# says what that costs.
gate_take_all() {
  _gl_dir && _gl_self || return 1
  _gl_gwt=${2:-${1:-}}
  while :; do
    _gl_s="$_gl_d/gate.generator"
    if mkdir "$_gl_s" 2>/dev/null; then
      echo "$_gl_me $(date +%s) $_gl_gwt" > "$_gl_s/owner"
      break
    fi
    _gl_reclaim || sleep "$GATE_LOCK_POLL"
  done
  _gl_gi=0
  while [ "$_gl_gi" -lt "$GATE_LOCK_SLOTS" ]; do
    gate_take "$_gl_gwt" || { gate_release_all >/dev/null; return 1; }
    _gl_gi=$((_gl_gi + 1))
  done
}

# Releases every slot this shell holds, then gate.generator; fails if it
# released nothing
gate_release_all() {
  _gl_dir && _gl_self || return 1
  _gl_gi=0 _gl_gn=0
  while [ "$_gl_gi" -lt "$GATE_LOCK_SLOTS" ]; do
    gate_release || break
    _gl_gn=$((_gl_gn + 1))
    _gl_gi=$((_gl_gi + 1))
  done
  _gl_s="$_gl_d/gate.generator"
  _gl_pid=""
  [ -r "$_gl_s/owner" ] && read -r _gl_pid _ < "$_gl_s/owner"
  if [ "$_gl_pid" = "$_gl_me" ]; then
    rm -f "$_gl_s/owner"
    rmdir "$_gl_s" 2>/dev/null &&
      { echo "gate.generator released by $_gl_me"; _gl_gn=$((_gl_gn + 1)); }
  fi
  [ "$_gl_gn" -gt 0 ]
}

# Where _gl_hwm reads the processes; a test points it at a tree of its own
_gl_proc=/proc

# The peak in KB that the output of /usr/bin/time on stdin gives: GNU's -v
# names KB, macOS's -l gives bytes. Prints nothing where it gives none.
_gl_peak_kb() {
  awk 'tolower($0) ~ /maximum resident set size/ {
         if ($0 ~ /\(kbytes\)/) v = $NF; else if ($1 ~ /^[0-9]+$/) v = int($1 / 1024)
       }
       END { if (v ~ /^[0-9]+$/) print v }'
}

# The VmHWM in KB of PID $1, read under $_gl_proc
_gl_vmhwm() {
  sed -n 's/^VmHWM:[[:space:]]*\([0-9][0-9]*\) kB$/\1/p' "$_gl_proc/$1/status" 2>/dev/null
}

# Prints the children of PID $1 that /proc lists under each of its threads,
# each followed by a space
_gl_children() {
  # listed rather than globbed: zsh stops at a glob with no match. The
  # names are thread IDs, digits only, so each line is one whole name.
  while read -r _gl_ht; do
    [ -n "$_gl_ht" ] || continue
    # split on purpose: the file holds the PIDs, a space after each
    # shellcheck disable=SC2046
    printf '%s ' $(cat "$_gl_proc/$1/task/$_gl_ht/children" 2>/dev/null)
  done <<EOF
$(ls "$_gl_proc/$1/task" 2>/dev/null)
EOF
}

# Sets _gl_hm to the largest VmHWM in KB of PID $1 and the processes below
# it. Fails where PID $1 shows none, as once it has ended.
_gl_hwm() {
  _gl_hm=$(_gl_vmhwm "$1")
  [ -n "$_gl_hm" ] || return 1
  # the trailing space ends every PID, so that each step drops one
  _gl_hq="$(_gl_children "$1") "
  while [ -n "$_gl_hq" ]; do
    _gl_hp=${_gl_hq%% *}
    _gl_hq=${_gl_hq#* }
    [ -n "$_gl_hp" ] || continue
    _gl_hk=$(_gl_vmhwm "$_gl_hp")
    [ -z "$_gl_hk" ] || [ "$_gl_hk" -le "$_gl_hm" ] || _gl_hm=$_gl_hk
    _gl_hq="$_gl_hq$(_gl_children "$_gl_hp")"
  done
}

# Removes the files of time's output that gate_peak runs left behind, those
# whose shell is gone, as one interrupted before it removed its own
_gl_peak_sweep() {
  # listed rather than globbed: zsh stops at a glob with no match
  while read -r _gl_t; do
    case $_gl_t in peak.*) ;; *) continue ;; esac
    _gl_tp=${_gl_t#peak.}
    _gl_tp=${_gl_tp%%.*}
    case $_gl_tp in "" | *[!0-9]*) continue ;; esac
    _gl_running "$_gl_tp" || rm -f "$_gl_d/$_gl_t"
  done <<EOF
$(ls "$_gl_d" 2>/dev/null)
EOF
}

gate_peak() {
  [ "$#" -ge 3 ] || {
    echo "usage: gate_peak <kind> <tree> <program> [<argument>...]" >&2
    return 2
  }
  _gl_pkind=$1 _gl_ptree=$2
  shift 2
  _gl_prc=0 _gl_pkb="" _gl_pf=""
  # time's output goes beside the lock, named by this shell's PID, so that
  # a later run removes it where this one is interrupted
  if _gl_dir >&2 && _gl_self >&2; then
    _gl_peak_sweep
    _gl_pf=$(mktemp "$_gl_d/peak.$_gl_me.XXXXXX" 2>/dev/null) || _gl_pf=""
  fi
  _gl_pt0=$(date +%s)
  # each time is tried on `true` first: where it fails after the program
  # has run, it returns its own code in place of the program's. time runs
  # the program through sh, which returns 128 plus the number of a signal
  # that ends it, where macOS's time returns 1 for KILL.
  if [ -n "$_gl_pf" ] && [ "$(uname -s)" = Darwin ] &&
    /usr/bin/time -l -o "$_gl_pf" true > /dev/null 2>&1; then
    /usr/bin/time -l -o "$_gl_pf" sh -c '"$@"; exit $?' sh "$@" || _gl_prc=$?
    _gl_pkb=$(_gl_peak_kb < "$_gl_pf")
  elif [ -n "$_gl_pf" ] && /usr/bin/time -v -o "$_gl_pf" true > /dev/null 2>&1; then
    /usr/bin/time -v -o "$_gl_pf" sh -c '"$@"; exit $?' sh "$@" || _gl_prc=$?
    _gl_pkb=$(_gl_peak_kb < "$_gl_pf")
  elif [ -r "$_gl_proc/self/status" ]; then
    # stdin through fd 3: a command started with & reads /dev/null, which
    # dash puts in place before an explicit <&0
    { "$@" <&3 3<&- & } 3<&0
    _gl_ppid=$!
    while _gl_hwm "$_gl_ppid"; do
      [ -n "$_gl_pkb" ] && [ "$_gl_pkb" -ge "$_gl_hm" ] || _gl_pkb=$_gl_hm
      sleep 1
    done
    wait "$_gl_ppid" || _gl_prc=$?
  else
    "$@" || _gl_prc=$?
  fi
  _gl_psec=$(($(date +%s) - _gl_pt0))
  [ -z "$_gl_pf" ] || rm -f "$_gl_pf"
  if [ -n "$_gl_d" ] && [ -d "$_gl_d" ]; then
    # noclobber off in a subshell: zsh with it set refuses >> to a file
    # that does not exist, and the caller's setting stays as it was
    (
      set +C
      printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        "$(printf '%s' "$_gl_pkind" | tr '\t\n' '  ')" \
        "$(printf '%s' "$_gl_ptree" | tr '\t\n' '  ')" \
        "${_gl_pkb:-?}" "$_gl_prc" "$_gl_psec" >> "$_gl_d/gate.peaks"
    ) || echo "gate_peak: cannot append to $_gl_d/gate.peaks" >&2
  fi
  return "$_gl_prc"
}
