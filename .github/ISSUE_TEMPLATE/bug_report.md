---
name: Bug report / 问题反馈
about: A skill gave wrong guidance, a script failed, or the plugin did not install
labels: bug
---

> ⚠️ **Issues are public. Do not paste patient data / 不要贴任何患者数据。**
> Before you paste anything below, remove or replace with made-up values:
> - rows, columns or summaries of a real dataset (names, IDs, medical record numbers, dates of birth, addresses, phone numbers, free-text notes, rare diagnoses or small subgroups that could identify someone);
> - prompts or Claude replies that contain any of the above, or the name of a patient, hospital ward or unpublished study;
> - script errors and tracebacks that print data values (a pandas/numpy error message often quotes the offending cell, a column header or a file path) — keep the error type and the line in the script, replace the quoted values with `<value>`;
> - attached files: share a small synthetic file that reproduces the problem instead of the real one.
>
> 公开 issue 任何人都能看到。贴出提示词、Claude 的回复或脚本报错之前，先删掉或换成虚构值：真实数据的行/列/汇总、姓名、ID、病历号、出生日期、地址、电话、自由文本备注，以及报错信息里引用的单元格内容和文件路径。需要数据复现时，请提供能复现问题的小份模拟数据。

**MRP version** (`claude plugin list`): 
**Claude Code version** (`claude --version`): 
**Skill / script / command involved**: 

**What happened** (the prompt and the relevant part of Claude's reply or the script's error — with every data value removed, see above):

**What should have happened**:

**Checks** (tick what you ran):
- [ ] I removed patient data, identifiers and data values quoted in error messages from everything above
- [ ] `python3 tools/check_consistency.py` passes on main
- [ ] `python3 -m pytest tests -q` passes
- [ ] The wrong fact/number is quoted with its source (paper, guideline page) so it can be fixed, not guessed
