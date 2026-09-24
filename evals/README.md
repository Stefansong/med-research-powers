# MRP evals — does the plugin route to the right skill?

These cases are run with Claude Code's built-in plugin evaluator:

```bash
claude plugin eval . --tag routing --tag negative         # routing + negative cases, with/without-plugin arms, 3 runs each
claude plugin eval . --tag smoke --ablation none --runs 1   # quick check while editing skills
claude plugin eval . --trust-plugin --tag routing --tag negative --json results.json --threshold 0.8 --max-cost-usd 10   # CI
claude plugin eval . --scaffold                           # everything, including the behaviour case below
```

Running all cases without `--scaffold` includes `data-first-planning` in an empty workspace (its scaffold script is
skipped), so it fails and drags a `--threshold` run down; filter by tag or add `--scaffold`.

The routing cases use deterministic graders only (`tool_used` on the `Skill` tool), so the only cost is the agent runs themselves.

`data-first-planning` (tag `behavior`) checks the core rule "analyse the real data before planning": a scaffold script
creates a confirmed synthetic protocol, an ethics record and a messy, already-collected `data.csv` (400 patients in 668
stone rows, "未查"/"/" codes, "<0.1" values, only 23 patients with a recurrence), so the skill's prerequisites are met and
the expected path is data check-up → SAP → hard checkpoint 2, with `statistical-analysis` (not `data-collection-tools`) as
the next step. An LLM judge checks that the plan is built from those features instead of a generic template. The case
grants no Bash, so `data_profile.py` itself is not exercised. The Read and judge graders can also be passed by a
no-plugin baseline, so compare the arms (drop `--ablation none`) before reading a pass as plugin value. It needs `--scaffold`:

```bash
claude plugin eval . --tag behavior --scaffold --ablation none --runs 2
```

A routing case passes when the expected MRP skill is invoked (and, where it matters, a neighbouring skill is *not*).
The two `negative-*` cases are scored in both arms: an unrelated coding question and a one-line statistics
question must not start the MRP pipeline at all (their graders catch MRP skill names with or without the `mrp:` prefix).

Results are written to `evals/results/` (git-ignored). Add a case whenever a routing bug is fixed, so it cannot come back.

Docs: https://code.claude.com/docs/en/plugin-evals
