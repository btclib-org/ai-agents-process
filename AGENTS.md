# Repository instructions

Follow [CONTRIBUTING.md](./CONTRIBUTING.md) for issues, pull requests,
and local gates. Use [README.md](./README.md) for the
repository and setup, and [REPOSITORY.md](./REPOSITORY.md) before
changing workflows or settings.
For vulnerability reporting, see
[btclib-org/.github's SECURITY.md][security].

[security]: https://github.com/btclib-org/.github/blob/main/SECURITY.md

When an agent works here, a separate worktree per task keeps your own
checkout clean: hooks and agents change files where they run. For
example, `git worktree add ../<name> origin/main -b <branch>`, and
`git worktree remove ../<name>` when done.

Choose the least capable model that can reliably complete the task: use
a fast model for straightforward execution, a reasoning-focused model
for multi-step work, and the most capable available model for difficult
or ambiguous problems. Increase capability if progress stalls.

This repository holds the maintainers' process: `process/btclib-common.md`
contains shared rules, `skills/btclib-iss/SKILL.md` and
`skills/btclib-pr/SKILL.md` guide issue and pull-request work, and
`agents/` defines the writer and reviewer roles.

## Code Review Rules

Review against [REVIEWING.md](./REVIEWING.md). Its *The verdict* says
which review opens with a verdict line and what every other review
posts.

The heading is the one Codex's GitHub review asks for
([Customize what Codex reviews](https://learn.chatgpt.com/docs/third-party/github#customize-what-codex-reviews)).
