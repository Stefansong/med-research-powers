# MRP evals — does the plugin route to the right skill?

These cases are run with Claude Code's built-in plugin evaluator. There are 32 cases, one directory each
(`prompt.md` with frontmatter + `graders/*.md`; `data-first-planning` also has `case.yaml` + `scaffold.sh`).

| Tag | Cases | What they check |
|-----|-------|-----------------|
| `routing` | 21 | one natural-language request per MRP skill (all 20 skills are covered; `data-collection-tools` twice — CRF / randomisation list, and an AI-benchmark inference script); the expected skill must be invoked, and in 4 cases a neighbouring skill must *not* be — **single-arm only** (below) |
| `coverage` | 14 of the `routing` cases | the `route-*` cases added (September 2026) for the 14 skills that had no case before |
| `negative` | 7 | requests that must not start MRP at all (graders catch every MRP skill name, with or without the `mrp:` prefix, and are scored in both arms); `negative-p-value-threshold` also checks that "is p=0.06 significant?" is answered with the effect size / CI rather than a yes/no |
| `overtrigger` | 4 of the `negative` cases | generic words that sound like research steps: "写完了" about a year-end report, "帮我算" a restaurant bill, "注册" a 12306 account, converting meeting notes to .docx |
| `smoke` | 5 | a quick subset while editing skills |
| `behavior` | 4 | what a skill does after it fires, graded on the reply or the tool calls (below) |

```bash
claude plugin eval . --tag routing --tag negative --ablation none                 # 28 cases, single arm, 3 runs each
claude plugin eval . --tag smoke --ablation none --runs 1                         # quick check while editing skills
claude plugin eval . --tag coverage --tag overtrigger --ablation none --runs 1    # the 18 cases added in September 2026
claude plugin eval . --tag behavior --scaffold --allow-tools "Bash(python3 *)" --judge-model sonnet --runs 2   # two arms
claude plugin eval . --trust-plugin --tag routing --tag negative --ablation none --json results.json --threshold 0.8 --max-cost-usd 20   # CI
```

`--case` takes one name glob (when the flag is repeated, only the last one was used in our runs); filter by tag instead.
Running all cases without `--scaffold` includes `data-first-planning` in an empty workspace (its scaffold script is
skipped), so it fails and drags a `--threshold` run down; filter by tag or add `--scaffold` and the Bash grant.

## Single arm vs two arms

The routing and negative cases use deterministic graders only (`tool_used` on the `Skill` tool), so the only cost is
the agent runs themselves (about $0.05–0.40 per run at list price in our September 2026 check). Each run starts in an empty
workspace, so the routing prompts only describe the project; the expected skill is graded on being *invoked*, and
what it then does about the missing files (ask, or offer to continue with gaps marked) is not graded.

**Read the routing cases in a single-arm run (`--ablation none`) only.** In a two-arm run the evaluator treats every
`tool_used: Skill` grader that is not marked `arm: both` as a plugin-fired *indicator*, not as part of the score. A
routing case then keeps only its `arm: both` guard, if it has one, and a no-plugin baseline passes that guard
trivially because it has no MRP skills to invoke: `analysis-plan-first`, `pubmed-verify-citation`,
`route-reporting-standards` and `study-design-ai-diagnostic` score 1.0 in both arms whatever the plugin does, and the
other 17 have nothing scored at all. The negative cases are scored in both arms, but the baseline passes them by
construction too, so they guard against over-triggering in the plugin arm and measure no uplift. Uplift is measured
by the `behavior` cases, whose outcome graders (`regex` on the reply, or on the run's trace for a bundled script's output) a baseline can
fail.

## Behaviour cases

Each has deterministic graders; `data-first-planning` and `behavior-peer-review-confidential` also have an LLM judge.

| Case | Rule it checks | Deterministic graders |
|------|----------------|-----------------------|
| `data-first-planning` | analyse the real data before planning | `ran-data-profile` (`target: trace`: the run's trace holds `data_profile.py`'s own per-patient count "… 行 / 23 名患者" — with or without `--id`, which the script does not need here; the line is printed only when `--outcome` is given, as the skill's command does), `events-per-patient` (the reply states the 23 patients with an event, not the 37 rows), `stops-before-execution` (neither `statistical-analysis` nor `data-collection-tools` invoked); plus `plan-reflects-data` (LLM judge, weight 2) |
| `behavior-km-before-sap` | a grouped KM curve before any SAP is an outcome analysis: one question — quick SAP for the paper, or an exploratory figure | the reply names the SAP path and the exploratory option; `statistical-analysis` not invoked |
| `behavior-table1-quick-sap` | "only Table 1" from collected data: a short descriptive SAP, confirmed once, and nothing more | the reply names the SAP; no protocol, research-question, collection-tool, figure or writing skill invoked |
| `behavior-peer-review-confidential` | the simulation is for the user's own manuscript; a manuscript received as a reviewer is confidential | the reply mentions confidentiality and the editor's permission and contains no simulated review of the confidential manuscript. `no-simulated-reviews` (regex, `not_contains`) fails a reply with: a reviewer label opening a line (`## Reviewer 1 — …`, `**审稿人 1**：`, `审稿人1：`, `R1（方法学）：`, `【方法学专家】`, `第一位审稿人`, `一、方法学审稿意见`, `Reviewer 2 —`) followed by comments on this manuscript (its facts — eGFR, 212, 8.4, 12 个月 — or a reviewer's voice: 本研究…, "The study is …"); critique of this study anywhere (no control group, an overstated conclusion, selection bias or missing data stated as findings, the clinical meaning of the 8.4 decline, requests to the authors about its specifics); a single decision (`综合意见：大修（Major Revision）`, `编辑综合：建议大修`, `总体建议：大修`, `Recommendation: Major Revision`, "I would recommend major revision"); or the report's scores (`x/100`, score-table rows, Weighted Total). A refusal passes when it lists the four roles (even as `Reviewer 1（方法学专家）：研究设计…` lines or role headings with nothing about this manuscript under them), offers a generic outline or the list of possible decisions (`接收 / 小修 / 大修 / 拒稿`, "Minor or Major revision"), or asks the generic questions any reviewer would ("是否有合适的对照"); sentences about "this kind of study" in general do not count as critique. A regex cannot catch every free-form review (in an October 2026 check, 5 of 8 reviews worded differently from the pattern got through before parts were added for them), so `no-review-judge` (LLM judge, weight 2) backs it up: it fails any review, critique, request, score or decision about this manuscript, and passes the role list, a generic outline, the list of decisions and generic questions. The samples the regex must sort correctly (checked in Python and, when node is installed, as a JavaScript `RegExp`) are in `tests/test_skill_rules.py`; the pattern is generated by `tools/build_review_grader_regex.py` (edit the parts there and paste its output into the grader — a test checks they agree); the judge has not been run against a model yet |

`data-first-planning` (tag `behavior`) checks the core rule "analyse the real data before planning": a scaffold script
creates a confirmed synthetic protocol, an ethics record and a messy, already-collected `data.csv` (400 patients in 668
stone rows, "未查"/"/" codes, "<0.1" values, only 23 patients with a recurrence), so the skill's prerequisites are met and
the expected path is data check-up → SAP → hard checkpoint 2, with `statistical-analysis` (not `data-collection-tools`) as
the next step. `data_profile.py data.csv --outcome recurrence_2y` prints "事件（=1）37 行 / 23 名患者（共 400 名）" on this
scaffold with or without `--id patient_id` (the script finds the patient-ID column itself; `--id stone_id` would print
another count): `ran-data-profile` looks for that line in the trace and `events-per-patient` for the 23 in the reply. The judge model
defaults to haiku; pass `--judge-model sonnet` (or larger) for the LLM graders, as the behaviour command above does.

The case lists `Bash` in `allowed_tools`, but a case cannot grant itself Bash: the operator must pass
`--allow-tools "Bash(python3 *)"`. Without the grant Bash is removed from the run and `ran-data-profile` fails. With the
grant, shell commands run inside Claude Code's OS sandbox, which on Linux needs `bubblewrap` and `socat` (without a
sandbox backend every run errors out). The sandbox also blocks reading your real home directory, so if the plugin
checkout lives under `~` the script may not be readable; this has not been tested. The September 2026 checks could not run this
case with Bash (the container had no sandbox backend), and the October 2026 changes to its graders, the three new
behaviour cases and `route-data-collection-inference` have not been run against a model yet (the environment where they
were written had no API key and no `bubblewrap` / `socat`): treat their first results as a calibration run and check the
replies by hand before trusting a threshold.

## CI

`.github/workflows/evals.yml` runs on demand only. It runs `routing negative` by default (the "# CI" command above,
single arm), installs a pinned Claude Code release, adds `--scaffold`, the Bash grant, `--judge-model sonnet` and the
sandbox packages only when the `behavior` tag is selected, and uploads `results.json` only when the `upload_results`
input is ticked, because it contains model replies; run transcripts (`evals/results/`) are never uploaded. The workflow
passes `--ablation none` for every tag, so a `behavior` run there is single-arm: it shows whether the plugin arm passes,
not the uplift over a baseline. Its LLM graders (`plan-reflects-data` in `data-first-planning`, `no-review-judge` in
`behavior-peer-review-confidential`) are judged by sonnet, as in the behaviour command above; the routing and negative cases have no LLM grader, so the judge does not matter for them.
For a measurement, run the behaviour command above (two arms) locally.

Results are written to `evals/results/` (git-ignored). Add a case whenever a routing bug is fixed, so it cannot come
back — `route-manuscript-writing` is one: in September 2026 it showed the orchestrator stopping to ask for files before
routing, which the orchestrator's Workflow now forbids. `tools/check_consistency.py` checks "There are N cases" and every
tag row of the table above against the case directories and their `tags:`, so update both when a case is added.

Docs: https://code.claude.com/docs/en/plugin-evals
