---
name: night-mode
description: "night-mode — turn night mode on or off in any session, or say whether it is on, since when and what it has deferred"
argument-hint: "on|off|status"
---

# Night mode

Do what `$ARGUMENTS` names. The rules are all in
`$PROCESS/process/night-mode.md`, which the session reads whole whatever
the word. A session that has not read `$PROCESS/process/every-session.md`
whole reads it first. `$PROCESS` is two directories above this skill's
own.

- `on` starts the night as `night-mode.md`'s activation says.
- `off` ends it as `night-mode.md`'s paragraph on turning it off says.
- `status` answers as `night-mode.md`'s paragraph on status says.

With no word, or any other, name the three and change nothing.
