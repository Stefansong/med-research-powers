# Example project — AI bladder-cancer detection on CT (synthetic)

A small, **entirely made-up** example of what an MRP project directory looks like after the first
three main-line skills have run. Numbers, centres and results are invented for illustration; do not cite them.

```
ai-bladder-ct/
├── .mrp-state.json        ← written by mrp_state.py after each skill (hook reads 5 fields of it)
├── research-question.md   ← research-question-formulation
├── study-protocol.md      ← study-design (type: ai-ml), hard checkpoint 1 confirmed
└── README.md
```

What the next steps would produce (not included): `ethics-statement.md` (research-ethics),
`journal-selection-report.md` (journal-selection, provisional), `analysis-plan.md` (data-analysis-planning,
hard checkpoint 2), `tools/` (data-collection-tools), `results-summary.md` + `analysis-log.md`
(statistical-analysis), `figures/` (figure-generation), `manuscript/*.md` (manuscript-writing), and so on.

To start your own project the same way, open Claude Code in an empty folder and say, for example:

> 我想研究用深度学习在 CT 上检测膀胱癌，比较模型和放射科医生的准确性。

The `using-med-research-powers` skill routes to `research-question-formulation`, and every skill ends by
updating `.mrp-state.json`, so a later session can resume with "上次完成到 …，下一步是 …".
