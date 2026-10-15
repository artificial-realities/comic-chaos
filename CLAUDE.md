# CLAUDE.md

**Read [AGENTS.md](AGENTS.md) first.** It is the source of truth for this
project: setup and test commands, secrets handling, the rules on paid OpenAI
calls and network exposure, code style, and the definition of done. This file
only adds Claude Code workflow preferences on top of it.

## Workflow

- **Plan first** for non-trivial work (3+ steps or an architectural decision).
  Share the plan and check in before implementing, unless told to go ahead. If
  something goes sideways, stop and re-plan instead of pushing on.
- **Verify before calling it done.** Run `ruff check .` and `python -m pytest`,
  compare behaviour with `main` when relevant, and ask "would a staff engineer
  approve this?". Never start or submit a real comic to verify something: that's
  a paid API call and needs the owner's explicit go-ahead.
- **Simplicity and root causes.** Make the smallest change that fixes the real
  problem; no temporary hacks. For non-trivial changes, pause and look for a more
  elegant approach, but don't over-engineer simple fixes.
- **Subagents** are fine for broad research or exploration that would flood the
  main context. Give each one a single focused task.

## Local notes (optional)

`tasks/` is git-ignored and stays on your machine:

- `tasks/todo.md`: the plan as a checklist, ticked off as you go, with a short
  review section at the end.
- `tasks/lessons.md`: after any correction from the owner, record the pattern
  and a rule that prevents it. Review it at the start of a session.
