# Security Policy

MRP is a Claude Code plugin made of Markdown skills, a session-start hook and a few Python scripts. This page explains what the plugin touches on your machine, what it deliberately does *not* do, and how to report a problem.

## What the session-start hook reads

`hooks/session-start.sh` runs when a Claude Code session starts, is cleared, or is compacted (the `SessionStart` hook in `.claude-plugin/plugin.json`). Its only input is the project-state file:

| File | Where | Fields the hook reads | What happens with them |
|------|-------|-----------------------|------------------------|
| `.mrp-state.json` | the project directory (`$CLAUDE_PROJECT_DIR`, falling back to the current working directory) | `project`, `current_stage`, `next_step`, `target_journal`, `checkpoint_mode` | printed as plain text inside a fenced block that is labelled as *data, not instructions*, so Claude can say "last completed: X, next step: Y". Each value is sanitised first: control characters, backticks and `<` `>` (so the `<mrp-session-start>` wrapper cannot be imitated) are removed, it is cut to 160 bytes (never in the middle of a UTF-8 character), a value that is not valid UTF-8 is not shown at all, and invisible or layout-changing characters are removed: C1 controls including NEL U+0085, line/paragraph separators U+2028/U+2029, every format character of Unicode 15.0 (category Cf — among them zero-width and bidi marks U+200B–U+200F, bidi controls U+202A–U+202E and U+2066–U+2069, U+2060–U+2064, soft hyphen, U+FEFF and the tag characters U+E0001 and U+E0020–U+E007F, which can spell out hidden ASCII text) and every other default-ignorable code point (variation selectors U+FE00–U+FE0F and U+E0100–U+E01EF, U+034F, Hangul fillers, the rest of U+E0000–U+E0FFF). It is printed with `printf %s`, so escape sequences such as `\n` in a crafted value stay literal text and cannot start a new line outside the block |

The hook does **not**:

- read any other field of `.mrp-state.json` (in particular it never dumps the whole file into the context);
- read `.mrp-user-profile.json` — that file lives in your home directory (`~/.claude/mrp-user-profile.json`) and is read lazily by individual skills, never by the hook;
- execute, `eval`, `source` or otherwise run anything found inside `.mrp-state.json`. Values are treated as opaque strings;
- follow a symbolic link: if `.mrp-state.json` is a symlink or not a regular file (a directory, a FIFO, a device), it is not read and the hook only says so;
- read more than the first 64 KiB of the file, or run for more than 10 seconds (`timeout` in `plugin.json`), so a huge or crafted file cannot stall session start;
- interpret the file in your locale: it is parsed byte by byte (`LC_ALL=C`), so invalid UTF-8 cannot make text from outside a whitelisted value leak into the context;
- make network requests, write files, or install packages.

If you clone a repository you do not trust, look at its `.mrp-state.json` before opening it in Claude Code, exactly as you would look at any other file that ends up in the model's context.

**Keep the state file out of your own repository.** Only this plugin's repository lists `.mrp-state.json` in its `.gitignore`; installing MRP changes nothing in your research project. `.mrp-state.json` is written to your project directory, so if that project is a git repository (especially a shared or public one), add this line to the project's own `.gitignore`:

```gitignore
/.mrp-state.json
```

The user profile (`~/.claude/mrp-user-profile.json`) lives in your home directory, outside any project. `reproduce_check.py` writes a `.gitignore` into the `.reproduce-check/` folder it creates, because the copies of your outputs kept there may hold patient-level results.

## What the skills and scripts do

- Skills are Markdown instructions. They never run on their own; Claude reads them and asks for your approval before running tools, as configured in your Claude Code permissions.
- The bundled Python scripts (`skills/*/scripts/*.py`) operate on local files only — they contain no network calls. Literature look-ups go through the PubMed MCP server that *you* configure; MRP does not bundle or auto-install one.
- `.mrp-state.json` (project) and `~/.claude/mrp-user-profile.json` (global) are written only by the `mrp_state.py` script and by skills after asking you; nothing is uploaded anywhere. `mrp_state.py` never follows a symlink: a state file, its `.tmp` file or the profile that is a symlink or not a regular file is refused (exit 2, nothing written). `mrp_state.py show`, which the orchestrator runs at session start, cleans and labels the values the same way the hook does. It prints only the documented fields (other keys are counted, not shown) and at most 32 KB. A symlinked or non-regular `journal-overrides.yaml` is refused too.
- MRP never records passwords, patient-level data, or ethics-approval numbers in either file.

## Supported versions

Only the latest 6.x release receives fixes. Update with `/plugin update mrp@med-research-powers`.

## Reporting a vulnerability

Please do **not** open a public issue for security problems. Instead:

1. Use GitHub's private vulnerability reporting on the repository (*Security → Report a vulnerability*), or
2. email the maintainer listed in `.claude-plugin/marketplace.json`.

Include the plugin version (`claude plugin list`), your Claude Code version, the file or skill involved, and steps to reproduce. You will get an acknowledgement within 7 days; a fix is released as a new version so that installed users receive it through `/plugin update`.

Things worth reporting: a hook or script that reads or executes something it should not, a skill instruction that would leak local data, a dependency with a known vulnerability in `requirements.txt`, or documentation that overstates what the plugin protects against.
