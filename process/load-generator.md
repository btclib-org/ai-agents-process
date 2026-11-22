# A load generator

A load generator is anything run to raise the load for a timing
measurement, such as `yes`. It takes every slot of the gate lock, since
other gates spoil the measurement: `gate_take_all <worktree>` instead of
`gate_take`, and `gate_release_all` instead of `gate_release`. One
generator runs at a time, as the comment above `gate_take_all` in
`$PROCESS/scripts/gate-lock.sh` says.

While `gate_take_all` waits for the rest of the slots, it holds those it
has. That wait is at least (`GATE_LOCK_SLOTS` − 1) × `GATE_LOCK_STAGGER`
seconds, 30 seconds by default, rising to (`GATE_LOCK_SLOTS` − 1) ×
`GATE_LOCK_SETTLE` seconds, 120 by default, while less than
`GATE_LOCK_FREE` plus `GATE_LOCK_MARGIN` percent of memory is free. Each
take queues with a fresh ticket, so gates that queue meanwhile take the
next free slots before it, and it may hold the slots it has for longer.

The session that runs it starts at most one single-threaded process per
free core: the cores times the idle fraction on the last line
`gate_take_all` printed, rounded down, minus the workers of the measured
run. The example counts the cores with `getconf _NPROCESSORS_ONLN`,
which Codex's `workspace-write` sandbox allows. The measured run goes in
the same shell call, inside that hold, with no `gate_take` of its own.
The session records the PIDs and stops the measured run as the example's
watchdog does: where the run is still going 900 seconds after its start,
SIGTERM at the watchdog's next 5-second poll, and SIGKILL where it is
still there a second later. Once the run ends, the session kills the
rest and checks with `kill -0` that they are gone before
`gate_release_all`:

```shell
scratch=<scratch>
workers=<n>
wt=<worktree>
set -- <the measured run>
```

```shell
. "${PROCESS:?}/scripts/gate-lock.sh"
out=${scratch:?}/gen.out pids=${scratch:?}/gen.pids
: "${workers:?}" && gate_take_all "${wt:?}" > "$out" 2>&1 && {
  idle=$(tail -n 1 "$out" | sed -n 's/.* at \([0-9][0-9]*\)% CPU idle.*/\1/p')
  idle=${idle:-0}
  free=$(( $(getconf _NPROCESSORS_ONLN) * idle / 100 - ${workers:?} ))
  : > "$pids"
  reaped=
  gen_gone() {
    case $(LC_ALL=C kill -0 "$1" 2>&1) in
      *[Nn]'o such process'*) ;;
      *) return 1 ;;
    esac
  }
  gen_add() {
    printf '%s\n' "$@" >> "$pids" && return
    kill -9 "$@"
    for pid; do until gen_gone "$pid"; do sleep 1; done; done
    exit 1
  }
  gen_stop() {
    trap '' HUP INT TERM
    while read -r pid; do
      [ "$pid" = "$reaped" ] || kill "$pid" 2>/dev/null
    done < "$pids"
    sleep 1
    while read -r pid; do
      [ "$pid" = "$reaped" ] || gen_gone "$pid" || kill -9 "$pid" 2>/dev/null
    done < "$pids"
    while read -r pid; do
      [ "$pid" = "$reaped" ] || until gen_gone "$pid"; do sleep 5; done
    done < "$pids"
  }
  trap gen_stop EXIT
  stop=
  trap 'stop=1' HUP INT TERM
  while [ "$free" -gt 0 ]; do
    yes > /dev/null & gen_add $!
    free=$(( free - 1 ))
  done
  "$@" & run=$!; gen_add "$run"
  sleep 900 & nap=$!
  ( until gen_gone "$nap"; do sleep 5; done
    kill "$run"; sleep 1; gen_gone "$run" || kill -9 "$run" ) 2>/dev/null &
  gen_add $! "$nap"
  trap 'exit 1' HUP INT TERM
  [ -z "$stop" ] || exit 1
  wait "$run"
  reaped=$run
  gen_stop
  trap - EXIT HUP INT TERM
  gate_release_all
}
```

The block holds no comment and no negated bracket such as `[!0-9]`, so
that it runs when pasted into an interactive zsh: one without
`interactive_comments` reads a `#` line as words, and one with history
expansion reads that `!` as an event. `sed` prints the digits of the
idle percentage or nothing, and nothing reads as 0.

`workers` is checked on the line of `gate_take_all`, chained to it: an
interactive shell that fails a `:?` goes on to the next line, so a check
on a line of its own would still take every slot.

`gen_gone` reads a PID as gone only where `kill -0` answers "No such
process": Codex's sandbox refuses `ps`, and `kill -0` also fails for
another user's process. `gen_add` records the PIDs it is given; where it
cannot, it kills them and exits the shell once they are gone.

A signal while the processes start sets `stop`, and the shell exits
once each is recorded. The measured run goes in the background so that
a signal reaches the trap while it runs.

`gen_stop` runs when the measured run ends, and from the trap when the
shell exits or receives SIGHUP, SIGINT or SIGTERM. It sends SIGTERM,
then SIGKILL to each process not gone a second later, skipping the
measured run once `wait` has reaped it, and returns only
once each is gone, ignoring those three signals meanwhile. So the shell
holds the slots until then: where a PID never reads as gone, as another
user's does, until the human sends the shell SIGKILL. A SIGKILL of the
shell leaves the processes, and the PID file is there to kill them by
hand.

The watchdog and `gen_stop` signal the PIDs recorded, each one a `$!`,
and no process those start. Of a pipeline `$!` names the last process:
zsh then goes on with the others still running, and sh, bash and dash
wait in `wait "$run"` until they end, with the generators running. Of a
list or a group it names one process of several, which one depending on
the shell. So the measured run is a single command, and a simple one:
`set -- <the measured run>` takes its words, and a redirection or a
pipeline written there applies to `set`, not to the run. An assignment
written before the command is read as its name, which no shell finds
(exit 127): `env NAME=value cmd` sets a variable for the run.

A recorded process that ends on its own before `gen_stop`, such as a
generator, the watchdog or its `sleep 900`, is reaped by the shell, and
`gen_stop` still signals its PID, which another process may hold by
then. That window runs from its end to `gen_stop`, which starts at most
900 seconds after the measured run does, plus the watchdog's poll and
its second. That bound fails where another process takes the nap's PID
before that poll: the watchdog then reads the nap as there, and neither
stops the run nor ends until that process does.

The watchdog can itself signal the reaped run. Where the run ends on its
own just as the watchdog reads the nap gone, `wait` may reap it before
the watchdog sends SIGTERM, which then goes to the reaped PID before
`gen_stop` ends the watchdog. The watchdog is recorded ahead of its nap,
so that `gen_stop` ends it first: this narrows the time it can signal a
reaped run.
