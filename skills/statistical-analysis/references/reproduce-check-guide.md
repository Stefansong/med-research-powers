# reproduce_check.py 的用法与报告解读

`statistical-analysis` Step 5 第 1 项用它做重跑检查；判定是否通过的规矩写在 SKILL.md，这里是细则（行为以脚本的 docstring 和 `--help` 为准）。

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/reproduce_check.py" \
  --cmd "python3 analysis_script.py" --outputs results/ --compare-stdout --report reproduce-check.md
```

退出码：0 一致 / 1 不一致 / 2 运行失败或参数有误。

## 参数

- `--cmd`：从原始数据开始的整个分析。R 脚本用 `--cmd "Rscript analysis_script.R"`。清洗写在单独脚本里时，把两步串起来一起重跑，并把清洗后的数据也列进 `--outputs`（如 `--cmd "python3 clean_data.py && python3 analysis_script.py" --outputs results/ data_clean.csv`），否则清洗那一步没有被重跑。
- `--outputs`：只放分析写出的东西。输入文件（数据、配置、上一步的结果）不要放在 `--outputs` 里：检查前这些路径里的文件会被移走。AI 模型的推理输出 / 预测也是输入：放 `data/model_outputs/`（data-collection-tools 的项目目录），不放 `results/`。
- `--compare-stdout`：必须加。屏幕上打印的结果也要一致（不加时屏幕差异只警告、不算失败）。
- `--compare-stderr`：结果用 R 的 `message()` 或 Python 的 `logging` 输出时再加。不加时报告里「错误输出（stderr）」一行写着"未计入结论"是正常的（包的启动信息常写在 stderr）；「屏幕输出（stdout）」一行不能有"未计入结论"（Gate 2 查这一点）。

## 读报告

- 每次运行前只清空 `--outputs`：报告"需要留意"里列出的 `--outputs` 之外新建或改动的文件（缓存、中间结果，如 `cache/`、`_targets/`）要么加进 `--outputs`，要么关掉缓存后重查，否则"一致"不代表能从头复现。检查前就有、名字像缓存的文件（`cache/`、`*_cache/`、`_targets/`、`_freeze/`、`*.pkl` 等）也列在这里——各次运行读的是同一份；名字不像缓存的旧缓存认不出来，分析用了缓存就把缓存目录加进 `--outputs`。`--cwd` 里文件超过 100000 个时不逐个比较运行前后的文件，报告会写明，这时要自己确认没有缓存。输出里的运行日期 / 钟点、运行留下的后台进程也列在这里。
- 不一致时按报告里的提示修改（多半是没固定种子，或输出里写了时间），改完再跑。
- DOCX/PPTX/XLSX 已按内容比较，不必为保存时间排除。

## `--exclude`

只用于已确认除内嵌时间外完全相同的文件，并在 `analysis-log.md` 写明。模式是 shell 通配符：`*` 不跨目录，跨目录用 `**/`（如 `results/**/*.pdf`）；只写文件名如 `'*.pdf'` 则匹配所有目录里的同名文件。

## 副本与 `--keep-last`

各次副本在 `.reproduce-check/`（自动 git 忽略，可能含患者级结果）。`--keep-last 1` 只留最近一次：只删本工具建的检查文件夹，而且只在其中 pre-existing/ 的每个文件要么是较早一次检查运行生成的结果（检查开始时和那次检查最后一次运行的副本相同，记在检查文件夹的状态文件里），要么在原处或留下的检查副本里还有内容相同的一份时才删（按内容比较，不按文件名）；手工做的、改过的或在检查之外运行得到的版本不会被删，不删的会在报告里写明原因。每个检查文件夹的状态文件记下各次运行副本（run<k>/、logs/、pre-existing/）的内容清单：之后被改过或新放进去的文件会让这个文件夹保留；记录不完整（检查被中断、状态文件写不进去）时，那次检查不做清理。从旧版本升级后，旧检查文件夹没有内容清单，`--keep-last` 会保留它们并写明原因，确认后手工删一次即可。检查前就在 `--outputs` 里、没有哪次运行重新生成的文件（如手工整理的表）检查后会放回原处；较早的运行生成过、最后一次没有生成的文件不放回（以免旧版本混进这次的结果），报告里写明，检查前的版本留在 pre-existing/。运行重新生成了、但内容和检查前不同的文件（如手工改过的表），报告会提醒，检查前的版本在 pre-existing/ 里。
