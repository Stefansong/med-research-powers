---
name: route-manuscript-export
tags: [routing, coverage]
runs: 3
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---

投稿前的六道门检查已经全部通过了。把 manuscript/ 里的 Markdown 稿件导出成符合 European Urology 格式的 Word 文档。
