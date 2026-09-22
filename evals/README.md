# MRP evals — does the plugin route to the right skill?

These cases are run with Claude Code's built-in plugin evaluator:

```bash
claude plugin eval .                       # all cases, with/without-plugin arms, 3 runs each
claude plugin eval . --tag smoke --ablation none --runs 1   # quick check while editing skills
claude plugin eval . --trust-plugin --json results.json --threshold 0.8 --max-cost-usd 10   # CI
```

Every grader here is deterministic (`tool_used` on the `Skill` tool), so the only cost is the agent runs themselves.
A case passes when the expected MRP skill is invoked (and, where it matters, a neighbouring skill is *not*).
The two `negative-*` cases are scored in both arms: an unrelated coding question and a one-line statistics
question must not start the MRP pipeline at all.

Results are written to `evals/results/` (git-ignored). Add a case whenever a routing bug is fixed, so it cannot come back.

Docs: https://code.claude.com/docs/en/plugin-evals
