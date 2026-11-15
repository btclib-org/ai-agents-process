---
name: night-mode
description: "night-mode — turn night mode on or off in any session, or toggle it with no word, or say whether it is on, since when and what it has deferred"
argument-hint: "[on|off|status]"
---

# Night mode

Do what the word after the skill's name says. The rules are all in
`$PROCESS/process/night-mode.md`, which the session reads whole whatever
the word. A session that has not read
`$PROCESS/process/every-session.md` whole reads it first. `$PROCESS` is
two directories above this skill's own.

- `on` starts the night as `night-mode.md`'s activation says.
- `off` ends it as `night-mode.md`'s paragraph on turning it off says.
- `status` answers as `night-mode.md`'s paragraph on status says.

With no word, the night toggles: where it is off, the session starts it
as `on` does, the whole activation included, and where it is on, ends it
as `off` does, and says which it did. Where the context no longer holds
whether the night is on, the session says so and changes nothing. With
any other word, name the three and change nothing.
