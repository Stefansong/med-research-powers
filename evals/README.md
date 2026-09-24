# MRP evals — does the plugin route to the right skill?

These cases are run with Claude Code's built-in plugin evaluator. There are 27 cases, one directory each
(`prompt.md` with frontmatter + `graders/*.md`; `data-first-planning` also has `case.yaml` + `scaffold.sh`).

| Tag | Cases | What they check |
|-----|-------|-----------------|
| `routing` | 20 | one natural-language request per MRP skill (all 20 skills are covered); the expected skill must be invoked, and in 4 cases a neighbouring skill must *not* be |
| `coverage` | 14 of the `routing` cases | the `route-*` cases added in 6.4.1 for the 14 skills that had no case before |
| `negative` | 6 | requests that must not start MRP at all (graders catch every MRP skill name, with or without the `mrp:` prefix, and are scored in both arms) |
| `overtrigger` | 4 of the `negative` cases | generic words that sound like research steps: "写完了" about a year-end report, "帮我算" a restaurant bill, "注册" a 12306 account, converting meeting notes to .docx |
| `smoke` | 5 | a quick subset while editing skills |
| `behavior` | 1 (`data-first-planning`) | the "analyse the real data before planning" rule; needs `--scaffold` and a Bash grant (below) |

```bash
claude plugin eval . --tag routing --tag negative                            # 26 cases, with/without-plugin arms, 3 runs each
claude plugin eval . --tag smoke --ablation none --runs 1                    # quick check while editing skills
claude plugin eval . --tag coverage --tag overtrigger --ablation none --runs 1   # the 18 cases added in 6.4.1
claude plugin eval . --trust-plugin --tag routing --tag negative --json results.json --threshold 0.8 --max-cost-usd 20   # CI
claude plugin eval . --tag behavior --scaffold --allow-tools "Bash(python3 *)" --ablation none --runs 2
```

`--case` takes one name glob (when the flag is repeated, only the last one was used in our runs); filter by tag instead.
Running all cases without `--scaffold` includes `data-first-planning` in an empty workspace (its scaffold script is
skipped), so it fails and drags a `--threshold` run down; filter by tag or add `--scaffold` and the Bash grant.

The routing and negative cases use deterministic graders only (`tool_used` on the `Skill` tool), so the only cost is
the agent runs themselves (about $0.05–0.40 per run at list price in our 6.4.1 check). Each run starts in an empty
workspace, so the routing prompts only describe the project; the expected skill is graded on being *invoked*, and
what it then does about the missing files (ask, or offer to continue with gaps marked) is not graded.

`data-first-planning` (tag `behavior`) checks the core rule "analyse the real data before planning": a scaffold script
creates a confirmed synthetic protocol, an ethics record and a messy, already-collected `data.csv` (400 patients in 668
stone rows, "未查"/"/" codes, "<0.1" values, only 23 patients with a recurrence), so the skill's prerequisites are met and
the expected path is data check-up → SAP → hard checkpoint 2, with `statistical-analysis` (not `data-collection-tools`) as
the next step. Graders: the skill fired (indicator only in a two-arm run); `ran-data-profile` — a Bash call that runs the
bundled `data_profile.py`, which a no-plugin baseline cannot know, so this grader separates the arms; and an LLM judge
(weight 2) that checks the plan is built from the data's features instead of a generic template.

The case lists `Bash` in `allowed_tools`, but a case cannot grant itself Bash: the operator must pass
`--allow-tools "Bash(python3 *)"`. Without the grant Bash is removed from the run and `ran-data-profile` fails. With the
grant, shell commands run inside Claude Code's OS sandbox, which on Linux needs `bubblewrap` and `socat` (without a
sandbox backend every run errors out). The sandbox also blocks reading your real home directory, so if the plugin
checkout lives under `~` the script may not be readable; this has not been tested. The 6.4.1 checks could not run this
case with Bash (the container had no sandbox backend).

A two-arm run (drop `--ablation none`) is needed before reading a pass as plugin value: under `--ablation none` nothing is
excluded from the score. Results are written to `evals/results/` (git-ignored). Add a case whenever a routing bug is
fixed, so it cannot come back — `route-manuscript-writing` is one: in 6.4.1 it showed the orchestrator stopping to ask
for files before routing, which the orchestrator's Workflow now forbids.

Docs: https://code.claude.com/docs/en/plugin-evals
