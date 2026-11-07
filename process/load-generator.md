# A load generator

A load generator is anything run to raise the load for a timing
measurement, such as `yes`. It takes every slot of the gate lock, since
other gates spoil the measurement: `gate_take_all <worktree>` instead of
`gate_take`, and `gate_release_all` instead of `gate_release`. One
generator runs at a time, as the comment above `gate_take_all` in
`$PROCESS/scripts/gate-lock.sh` says.

While `gate_take_all` waits for the rest of the slots, it holds those it
has. That wait is at least (`GATE_LOCK_SLOTS` − 1) × `GATE_LOCK_STAGGER`
seconds, 30 seconds by default. Each take queues with a fresh ticket, so
gates that queue meanwhile take the next free slots before it, and it may
hold the slots it has for longer.

The session that runs it starts at most one single-threaded process per
free core: the cores times the idle fraction on the last line
`gate_take_all` printed, rounded down, minus the workers of the measured
run. The example counts the cores with `getconf _NPROCESSORS_ONLN`,
which Codex's `workspace-write` sandbox allows. The measured run goes in
the same shell call, inside that hold, with no `gate_take` of its own.
The session records the PIDs, kills them within 15 minutes of the start
of the measured run, as the example's watchdog does, and checks with
`kill -0` that they are gone before `gate_release_all`:

```shell
. "${PROCESS:?}/scripts/gate-lock.sh"
out=<scratchpad>/gen.out pids=<scratchpad>/gen.pids workers=<n>
gate_take_all <worktree> > "$out" 2>&1 && {
  idle=$(tail -n 1 "$out" | sed 's/.* at \([0-9]*\)% CPU idle.*/\1/')
  case $idle in ''|*[!0-9]*) idle=0 ;; esac
  free=$(( $(getconf _NPROCESSORS_ONLN) * idle / 100 - workers ))
  : > "$pids"
  # Codex's sandbox refuses ps, and kill -0 also fails for another user's
  # process: only "No such process" reads as gone
  gen_gone() {
    case $(LC_ALL=C kill -0 "$1" 2>&1) in
      *[Nn]'o such process'*) ;;
      *) return 1 ;;
    esac
  }
  # a PID that cannot be recorded is killed, and the shell exits once it
  # is gone
  gen_add() {
    echo "$1" >> "$pids" && return
    kill -9 "$1"
    until gen_gone "$1"; do sleep 1; done
    exit 1
  }
  gen_stop() {
    trap '' HUP INT TERM
    while read -r pid; do kill "$pid" 2>/dev/null; done < "$pids"
    sleep 1
    while read -r pid; do
      gen_gone "$pid" || kill -9 "$pid" 2>/dev/null
    done < "$pids"
    while read -r pid; do
      until gen_gone "$pid"; do sleep 5; done
    done < "$pids"
  }
  trap gen_stop EXIT
  # a signal while the processes start is acted on once each is recorded
  stop=
  trap 'stop=1' HUP INT TERM
  while [ "$free" -gt 0 ]; do
    yes > /dev/null & gen_add $!
    free=$(( free - 1 ))
  done
  # the measured run goes in the background so that a signal reaches
  # the trap, and the watchdog kills it after 15 minutes (900 seconds)
  <the measured run> & run=$!; gen_add "$run"
  sleep 900 & nap=$!; gen_add "$nap"
  ( until gen_gone "$nap"; do sleep 5; done
    kill "$run"; sleep 1; gen_gone "$run" || kill -9 "$run" ) 2>/dev/null &
  gen_add $!
  trap 'exit 1' HUP INT TERM
  [ -z "$stop" ] || exit 1
  wait "$run"
  gen_stop
  trap - EXIT HUP INT TERM
  gate_release_all
}
```

`gen_stop` runs when the measured run ends, and from the trap when the
shell exits or receives SIGHUP, SIGINT or SIGTERM. It sends SIGTERM,
then SIGKILL to each process not gone a second later, and returns only
once each is gone, ignoring those three signals meanwhile. So the shell
holds the slots until then: where a PID never reads as gone, as another
user's does, until the human sends the shell SIGKILL. A SIGKILL of the
shell leaves the processes, and the PID file is there to kill them by
hand.
