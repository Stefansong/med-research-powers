# Security Policy

MRP is a Claude Code plugin made of Markdown skills, a session-start hook and a few Python scripts. This page explains what the plugin touches on your machine, what it deliberately does *not* do, and how to report a problem.

## What the session-start hook reads

`hooks/session-start.sh` runs when a Claude Code session starts, is cleared, or is compacted (the `SessionStart` hook in `.claude-plugin/plugin.json`). Its only input is the project-state file:

| File | Where | Fields the hook reads | What happens with them |
|------|-------|-----------------------|------------------------|
| `.mrp-state.json` | the project directory (`$CLAUDE_PROJECT_DIR`, falling back to the current working directory) | `project`, `current_stage`, `next_step`, `target_journal`, `checkpoint_mode` | printed as plain text inside a fenced block that is labelled as *data, not instructions*, each value truncated to a short length, so Claude can say "last completed: X, next step: Y" |

The hook does **not**:

- read any other field of `.mrp-state.json` (in particular it never dumps the whole file into the context);
- read `.mrp-user-profile.json` — that file lives in your home directory (`~/.claude/mrp-user-profile.json`) and is read lazily by individual skills, never by the hook;
- execute, `eval`, `source` or otherwise run anything found inside `.mrp-state.json`. Values are treated as opaque strings;
- make network requests, write files, or install packages.

If you clone a repository you do not trust, look at its `.mrp-state.json` before opening it in Claude Code, exactly as you would look at any other file that ends up in the model's context. Both state files are listed in `.gitignore`, so they are not committed by default.

## What the skills and scripts do

- Skills are Markdown instructions. They never run on their own; Claude reads them and asks for your approval before running tools, as configured in your Claude Code permissions.
- The bundled Python scripts (`skills/*/scripts/*.py`) operate on local files only — they contain no network calls. Literature look-ups go through the PubMed MCP server that *you* configure; MRP does not bundle or auto-install one.
- `.mrp-state.json` (project) and `~/.claude/mrp-user-profile.json` (global) are written only by the `mrp_state.py` script and by skills after asking you; nothing is uploaded anywhere.
- MRP never records passwords, patient-level data, or ethics-approval numbers in either file.

## Supported versions

Only the latest 6.x release receives fixes. Update with `/plugin update mrp@med-research-powers`.

## Reporting a vulnerability

Please do **not** open a public issue for security problems. Instead:

1. Use GitHub's private vulnerability reporting on the repository (*Security → Report a vulnerability*), or
2. email the maintainer listed in `.claude-plugin/marketplace.json`.

Include the plugin version (`claude plugin list`), your Claude Code version, the file or skill involved, and steps to reproduce. You will get an acknowledgement within 7 days; a fix is released as a new version so that installed users receive it through `/plugin update`.

Things worth reporting: a hook or script that reads or executes something it should not, a skill instruction that would leak local data, a dependency with a known vulnerability in `requirements.txt`, or documentation that overstates what the plugin protects against.
