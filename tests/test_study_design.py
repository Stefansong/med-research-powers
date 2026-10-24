"""Regression tests for the study-design methods content and the bundled example project.

The protocol templates, modules and experiment templates are advice, not code, so most checks pin the
advice that was wrong before (a clinical template missing SPIRIT 2025 items, the crossover carry-over
pre-test, Delphi routed to a survey guideline, class weights without recalibration, the n-based data
split, ...). Item lists are read from the local SPIRIT 2025 / STARD 2015 / ARRIVE 2.0 checklists, and the
example protocol's precision numbers are recomputed here, so a template or example that drifts from the
checklist or from its own arithmetic fails.
"""

import json
import math
import re
import subprocess
import sys
from pathlib import Path
from statistics import NormalDist

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
SD = ROOT / "skills" / "study-design"
REFS = SD / "references"
MODULES = REFS / "modules"
EXPT = REFS / "experiment-templates"
CHECKLISTS = ROOT / "skills" / "reporting-standards" / "references" / "checklists"
EXAMPLE = ROOT / "examples" / "ai-bladder-ct"
POWER = ROOT / "skills" / "statistical-analysis" / "scripts" / "power_analysis.py"


def _read(path):
    return path.read_text(encoding="utf-8")


def _checklist_ids(name):
    data = yaml.safe_load(_read(CHECKLISTS / name))
    return [item["id"] for section in data["sections"] for item in section["items"]]


def _section(text, start, end=None):
    """Text from the line that starts with `start` up to the next line that starts with `end`."""
    i = text.index(start)
    j = text.index(end, i + len(start)) if end else len(text)
    return text[i:j]


def _expand(token, all_ids):
    """'6' -> ['6'], '10a' -> ['10a'], '6–9' -> 6,7,8,9 (with their sub-items), '21' -> ['21a', '21b']."""
    token = token.strip()
    m = re.fullmatch(r"(\d+)([a-d]?)\s*[–-]\s*(\d+)([a-d]?)", token)
    if m:
        lo, hi = int(m.group(1)), int(m.group(3))
        return [i for i in all_ids if lo <= int(re.match(r"\d+", i).group()) <= hi]
    if token in all_ids:
        return [token]
    return [i for i in all_ids if re.fullmatch(token + r"[a-d]", i)]


NEGATION = r"(?:不是|并非|不必|无需|无须|不需要|不用|不要|未必|不一定|可以不|不|非|无|未|勿)"


def _affirms(text, phrase):
    """`phrase` is stated and nowhere negated right before it, so "是上限" → "不是上限" or "必须有" → "不是必须有"
    (edits that keep the substring but reverse the meaning) fail."""
    return phrase in text and not re.search(NEGATION + r"\s*" + re.escape(phrase), text)


def _only_inside(text, pattern, container):
    """Every match of `pattern` lies inside one match of `container` (e.g. the description of a forbidden
    procedure), and there is at least one."""
    spans = [m.span() for m in re.finditer(container, text)]
    hits = [m.start() for m in re.finditer(pattern, text)]
    return bool(hits) and all(any(a <= h < b for a, b in spans) for h in hits)


# ── MA-8: the clinical protocol template covers every SPIRIT 2025 item ───────────────────────

def test_clinical_template_covers_all_spirit_2025_items():
    ids = _checklist_ids("spirit-2025.yaml")
    assert len(ids) == 53
    clinical = _section(_read(REFS / "protocol-templates.md"), "## A. Clinical", "## B. Basic Science")
    tagged = set()
    for group in re.findall(r"SPIRIT ((?:\d{1,2}[a-d]?)(?:/\d{1,2}[a-d]?)*)(?![\d/])", clinical):
        tagged.update(group.split("/"))
    missing = [i for i in ids if i not in tagged]
    assert not missing, f"SPIRIT 2025 items without a place in template A: {missing}"
    assert not tagged - set(ids), f"tags that are not SPIRIT 2025 items: {sorted(tagged - set(ids))}"
    ppi = next(line for line in clinical.splitlines() if "SPIRIT 11" in line)
    assert "患者与公众参与" in ppi and '没有就写"没有"并说明理由' in ppi   # say so explicitly when there is none
    assert "SPIRIT 2025 只针对随机试验" in clinical                    # observational studies: not applicable + reason


# ── MA-9: crossover, cluster design effect, PROBAST+AI ────────────────────────────────────────

def test_clinical_module_crossover_cluster_probast():
    text = _read(MODULES / "clinical.md")
    rows = {line.split("|")[1].strip(): line for line in text.splitlines() if line.startswith("| **")}
    cross = rows["**交叉试验**"]
    assert "序列效应检验" not in cross
    # the wording carries the advice: no two-stage pre-test (it inflates type I error), rely on wash-out
    assert "**不做两阶段分析**" in cross and "I 类错误明显膨胀" in cross
    assert "残留效应靠设计排除" in cross and "洗脱期" in cross and "或只用每一期末段的测量" in cross
    # "use only the first period" appears only as the description of the forbidden two-stage procedure
    first_period = r"(?:只|仅)(?:用|分析|保留)第\s*[一1]\s*期"
    assert _only_inside(cross, first_period, r"\*\*不做两阶段分析\*\*（[^）]*）"), cross
    assert "10.1002/sim.4780081202" in text and "10.1136/bmj.l4378" in text     # Freeman 1989; CONSORT crossover
    cluster = rows["**群随机试验**"]
    assert "群大小不等时用 1 + ((CV² + 1)·m̄ − 1)·ICC" in cluster and "10.1093/ije/dyl129" in text
    assert "| 个体样本量 × 设计效应 |" in cluster                    # the sample-size column applies it
    assert not re.search(r"设计效应\s*(?:可|可以)?(?:忽略|不计|省略)|直接用\s*`?power_analysis", cluster), cluster
    assert not re.search(NEGATION + r"[^；。|]{0,4}设计效应", cluster), cluster
    assert "PROBAST+AI" in text and "10.1136/bmj-2024-082505" in text
    ai = _read(MODULES / "ai-ml.md")
    assert "PROBAST+AI" in ai and "QUADAS-2 / PROBAST）" not in ai


# ── MA-10: Delphi -> ACCORD, CROSS only for surveys ───────────────────────────────────────────

def test_delphi_uses_accord_not_cross():
    module = _read(MODULES / "survey-delphi.md")
    delphi = next(line for line in module.splitlines() if "Delphi Study" in line)
    assert "ACCORD" in delphi and "CROSS" not in delphi
    assert "10.1371/journal.pmed.1004326" in module
    survey = _section(_read(REFS / "protocol-templates.md"), "## E. Survey")
    assert "ACCORD" in survey
    skill = _read(SD / "SKILL.md")
    assert "ACCORD" in skill
    ref = _read(REFS / "survey-reference.yaml")
    assert "ACCORD" in yaml.safe_load(ref)["delphi"]["reporting"]


# ── MA-11: class weighting needs recalibration; calibration = CITL + slope + curve ───────────

def test_ai_module_class_weighting_and_calibration():
    text = _read(MODULES / "ai-ml.md")
    lines = text.splitlines()
    # every imbalance correction carries its own recalibration obligation (pinned as full phrases, so an
    # edit that keeps the word "重新校准" elsewhere in the row but drops the obligation still fails)
    loss_row = next(line for line in lines if line.startswith("  | 损失函数"))
    assert "破坏校准" in loss_row and "输出风险概率前必须在未加权的数据上重新校准" in loss_row
    oversample = next(line for line in lines if line.startswith("  | 数据层面"))
    assert "校准变差" in oversample and "需在未重采样的数据上重新校准" in oversample
    batch = next(line for line in lines if line.startswith("  | 采样策略"))
    assert "概率输出要重新校准" in batch
    methods = next(line for line in lines if line.startswith("- 必须在 Methods 中报告采用的策略和理由"))
    assert "输出的概率就不再是真实风险" in methods and "做了纠正就必须重新校准" in methods
    assert "10.1093/jamia/ocac093" in methods
    risk = next(line for line in text.splitlines() if line.startswith("风险预测类必须同时报告"))
    for word in ("calibration-in-the-large", "校准斜率", "校准曲线"):
        assert word in risk, word
    template_c = _section(_read(REFS / "protocol-templates.md"), "## C. AI/ML", "## D. Qualitative")
    imbalance = next(line for line in template_c.splitlines() if "Class imbalance handling" in line)
    assert "预测概率偏离真实风险" in imbalance and "必须在未重采样、未加权的数据上重新校准" in imbalance


# ── D3 (MA-1): validation split by model type and events, never by total n ───────────────────

N_TIER = re.compile(r"n\s*[<>≤≥]=?\s*\d|\d+\s*≤\s*n|按样本量分档|按 n 分档|分档边界")
SIZE_TIER = re.compile(r"[<>≤≥]\s*\d[\d,]{2,}\s*(?:例|人|名|patients|cases)?\s*(?:→|->|时|：|:)")   # ">1000 → …"
SPLIT_RATIO = re.compile(r"\b\d{2}\s*/\s*\d{2}\s*/\s*\d{2}\b|\b\d\s*:\s*\d\s*:\s*\d\b")      # 70/15/15, 8:1:1


@pytest.mark.parametrize("path", [MODULES / "ai-ml.md", REFS / "protocol-templates.md"])
def test_d3_split_rule(path):
    text = _read(path)
    assert not N_TIER.search(text), N_TIER.search(text).group()
    assert not SIZE_TIER.search(text), SIZE_TIER.search(text).group()
    for line in text.splitlines():                  # a fixed split ratio only as the myth of a Common-Mistakes row
        if SPLIT_RATIO.search(line):
            assert line.startswith('| "') and SPLIT_RATIO.search(line.split("|")[1]), line
    assert re.search(r"有效样本量\*{0,2}（?是?按患者计的事件数", text) and re.search(r"不[看是]总人数", text)
    lines = text.splitlines()
    regression = next(line for line in lines if "回归类及其他经典临床预测模型" in line)
    assert _affirms(regression, "用全部数据建模") and _affirms(regression, "bootstrap 乐观校正")
    assert re.search(r"不做随机 hold-out", regression)
    ml = next(line for line in lines if "要调超参数的 ML / 深度学习模型" in line)
    # nested CV first; a patient-level train / validation / test split only when every set has enough events
    assert re.search(r"ML / 深度学习模型\**\s*[：→]\s*嵌套交叉验证", ml), ml
    assert re.search(r"只有每个集合的事件数都够时，?才用按患者的训练 / 验证 / 测试划分", ml), ml
    assert not re.search(NEGATION + r"\s*(?:用|做)?\s*嵌套交叉验证", ml), ml
    external = next(line for line in lines if "外部 / 时间验证" in line and "优于任何随机划分" in line)
    assert re.search(r"声称模型可推广[^；。]*必须有", external) and _affirms(external, "必须有"), external
    assert "患者 ID" in text and "按结局分层" in text


# ── SS-5: power_analysis.py is not the tool for every sample size ─────────────────────────────

def test_skill_scopes_power_analysis():
    skill = _read(SD / "SKILL.md")
    assert "样本量脚本统一用" not in skill
    step3 = _section(skill, "### Step 3", "### Step 4")
    assert "power_analysis.py --help" in step3
    assert re.search(r"power_analysis\.py` 只覆盖", step3) and "脚本不覆盖的用专门方法" in step3
    for word in ("pmsampsize", "MRMC", "群随机", "设计效应"):
        assert word in step3, word
    # cluster trials: the individual sample size times the design effect, never power_analysis.py as it is
    assert "群随机试验和整群抽样 → 个体样本量 × 设计效应（ICC 写出处" in step3
    assert not re.search(r"设计效应\s*(?:可|可以)?(?:忽略|不计|省略)|直接用\s*`?\$?\{?[^`]*power_analysis", step3)


# ── CG-8: qPCR / Western blot analysis scale, reference genes, MIQE ───────────────────────────

def test_qpcr_template():
    text = _read(EXPT / "qpcr.md")
    assert "ΔCt" in text
    assert "**统计在 log 尺度上做**" in text and "不在 2^(-ΔΔCq) 倍数上做" in text
    assert "内参基因：**至少 2 个**，先在本实验的样本和处理条件下验证稳定性" in text
    assert "效率不同就用效率校正模型" in text
    assert "10.1186/gb-2002-3-7-research0034" in text                              # Vandesompele 2002
    assert "10.1373/clinchem.2008.112797" in text and "10.1093/clinchem/hvaf043" in text  # MIQE, MIQE 2.0
    assert "10.1093/nar/29.9.e45" in text                                            # Pfaffl efficiency model
    assert "相差 >5%" not in text and "Ct 值 >35 视为不可靠" not in text


def test_western_blot_template():
    text = _read(EXPT / "western-blot.md")
    assert "统计：在 log 尺度上分析" in text and "不要把对照组设成 1 后对比值直接做 t 检验" in text
    assert "单一内参要先证明它不随处理变化" in text and "过曝（饱和）的条带不能定量" in text
    assert "总蛋白染色" in text
    assert "10.1016/j.jneumeth.2008.05.003" in text and "10.1016/j.ab.2020.113608" in text
    assert "方法：目标蛋白灰度值 / 内参灰度值" not in text


# ── CG-9: animal study — experimental unit, cage effects, ARRIVE Essential 10 ────────────────

def test_animal_template():
    text = _read(EXPT / "animal-study.md")
    assert "实验单位 = 能被独立随机分配到不同处理的最小单位，n 按实验单位数计" in text
    assert "10.1371/journal.pbio.2005282" in text
    assert "实验单位是笼时，样本量按笼数算" in text
    assert "每笼混合分组（避免笼效应）" not in text
    assert "笼位安排：按实验单位定，没有统一做法" in text and "**不能**混笼" in text
    # which unit: feed / water / whole-cage treatment → cage; dam-level treatment → litter; slices are not n
    assert re.search(r"处理加在饲料 / 饮水 / 笼内环境里，或整笼一起处理 → \*\*笼\*\*（[^）]*不是独立的 n）", text)
    assert re.search(r"处理施加在孕鼠 / 母鼠身上、看子代 → \*\*窝\*\*", text)
    assert "多张切片 → 不是独立的 n，按动物汇总或用混合模型" in text
    assert not re.search(r"切片[^。；\n]{0,12}(?:各|都|分别)?(?:算|计|记)(?:作|为|成)?\s*(?:一个|独立的)?\s*n", text)
    assert "Essential 10" in text
    arrive = yaml.safe_load(_read(CHECKLISTS / "arrive-2.yaml"))
    essential = arrive["sections"][0]
    topics = []
    for item in essential["items"]:
        if item["topic"] not in topics:
            topics.append(item["topic"])
    assert len(topics) == 10
    for topic in topics:
        assert topic in text, topic


def test_basic_template_animal_section_counts_experimental_units():
    """A protocol written from template B must define the unit before counting animals (ARRIVE 2.0 1b)."""
    basic = _section(_read(REFS / "protocol-templates.md"), "## B. Basic Science", "## C. AI/ML")
    animal = _section(basic, "## 3. 动物实验", "## 4.")
    lines = animal.splitlines()
    unit = next(line for line in lines if line.startswith("- Experimental unit"))
    assert "ARRIVE 2.0 第 1b 条" in unit and "单只动物 / 笼 / 窝" in unit
    assert "处理逐只给、同笼动物可分到不同组 → 单只动物；" in unit
    assert "处理加在饲料 / 饮水 / 笼内环境或整笼处理 → 笼；" in unit
    assert re.search(r"处理给孕鼠 / 母鼠、看子代 → 窝\]$", unit), unit
    cage = next(line for line in lines if line.startswith("- Housing & cage allocation"))
    assert "处理可能经笼互相影响时不能混笼" in cage and "随机效应 / 区组" in cage
    # ARRIVE 2.0 Recommended Set item 15 (housing and husbandry) has a place in the slot
    assert "ARRIVE 2.0 第 15 条" in cage and "饲养条件" in cage and "环境丰富化" in cage
    size = next(line for line in lines if line.startswith("- Sample size"))
    assert "每组实验单位数（笼为单位时是笼数）" in size and "每组 n]" not in size
    rand = next(line for line in lines if line.startswith("- Randomization & blinding"))
    assert "随机分配的对象是实验单位" in rand
    module = _read(MODULES / "basic-science.md")
    assert "样本量按实验单位数算（笼为单位时是笼数）" in module
    assert "处理整笼给（饲料、饮水）时是笼，处理给孕鼠时是窝，处理逐只给时是单只动物" in module
    assert "同一只动物的多张切片、多个细胞只是观察单位，不增加 n" in module
    assert "实验单位已定义（动物实验：单只 / 笼 / 窝）" in module
    router = next(line for line in _read(SD / "SKILL.md").splitlines() if line.startswith("| Basic Science"))
    assert "n 按实验单位数计" in router


# ── CG-10: survey design effect and COSMIN criteria ───────────────────────────────────────────

def test_survey_reference():
    raw = _read(REFS / "survey-reference.yaml")
    ref = yaml.safe_load(raw)
    cs = ref["sample_size"]["cross_sectional"]
    deff = cs["corrections"]["design_effect"]
    assert "ICC" in deff and "(CV^2 + 1)" in deff and "10.1093/ije/dyl129" in raw
    order = cs["corrections"]["order"]
    assert order.index("finite_population") < order.index("design_effect") < order.index("response_rate")
    attrs = {a["attribute"].split()[0]: a for a in ref["psychometric_properties"]["attributes"]}
    structural = attrs["结构效度"]["criterion"]
    assert "0.95" in structural and "0.06" in structural and "0.08" in structural
    assert "CFI > 0.90" not in raw and "RMSEA < 0.08" not in raw
    assert "10.1007/s11136-018-1798-3" in raw                                       # COSMIN, Prinsen 2018
    assert "单维" in attrs["内部一致性"]["criterion"]
    module = _read(MODULES / "survey-delphi.md")
    assert "CFA 至少 200 人" not in module


# ── R17 / N3: the example protocol ───────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def protocol():
    return _read(EXAMPLE / "study-protocol.md")


def test_example_has_real_conditions_section(protocol):
    headings = [line for line in protocol.splitlines() if line.startswith("## ")]
    assert headings[0] == "## 0. 真实条件与设计理由"
    sec0 = _section(protocol, "## 0.", "## 1.")
    for word in ("真实条件", "未知项", "设计选择", "理由"):
        assert word in sec0, word


def test_example_centre_b_counts_are_pre_exclusion_upper_bound(protocol):
    """§0 lists centre B's image-quality exclusion as unknown, so the 400 / 95 used for every §2 precision
    figure cannot be called post-exclusion: they are pre-exclusion counts and the precision is an upper bound."""
    sec0 = _section(protocol, "## 0.", "## 1.")
    cases = next(line for line in sec0.splitlines() if line.startswith("  - 病例数与事件数"))
    assert "（排除后）" not in cases
    centre_b = cases[cases.index("中心 B"):]
    assert "尚未按图像质量排除" in centre_b
    unknown = next(line for line in sec0.splitlines() if "按图像质量排除后的可评估例数" in line)
    assert _affirms(unknown, "是上限") and "重算" in unknown
    sec2 = _section(protocol, "## 2.", "## 3.")
    size = next(line for line in sec2.splitlines() if line.startswith("- Sample size — 外部测试集"))
    assert "图像质量排除前" in size and _affirms(size, "下面的精度都是上限")
    volume = next(line for line in sec2.splitlines() if line.startswith("- Data volume"))
    assert "图像质量排除前" in volume[volume.index("中心 B"):]
    mrmc = next(line for line in sec2.splitlines() if "读片者研究（MRMC）" in line)
    assert "全部 400 例" not in mrmc and "全部可评估病例（至多 400 例" in mrmc


def test_example_split_follows_d3(protocol):
    assert not re.search(r"60/20/20|8:1:1|n > 1000|hold-out 档", protocol)
    assert not SPLIT_RATIO.search(protocol) and not re.search(r"[>≥]\s*1,?000", protocol)
    split = _section(protocol, "## 3.", "## 4.")
    assert "嵌套交叉验证" in split and "患者" in split and "事件" in split and "按结局" in split
    rule = next(line for line in split.splitlines() if line.startswith("- Rule:"))
    assert "本模型是要调超参数的 3D CNN → 嵌套交叉验证；" in rule
    assert next(line for line in split.splitlines() if line.startswith("- Strategy:")).startswith(
        "- Strategy: 中心 A 内嵌套交叉验证")
    assert not re.search(NEGATION + r"\s*(?:用|做)?\s*嵌套交叉验证", split)
    assert "中心 A 内不做随机 hold-out" in split and "中心 B 整体作为外部测试集，不参与任何调参" in split


def test_example_states_riley_precision(protocol):
    """The C-statistic CI width quoted for the external test set is the Riley 2021 closed form."""
    assert "10.1002/sim.9025" in protocol
    m = re.search(r"中心 B 共 (\d+) 例（癌 (\d+)", protocol)
    n, events = int(m.group(1)), int(m.group(2))
    c = float(re.search(r"预期 C 统计量 (0\.\d+)", protocol).group(1))
    phi = events / n
    se = math.sqrt(c * (1 - c) * (1 + (n / 2 - 1) * (1 - c) / (2 - c) + (n / 2 - 1) * c / (1 + c))
                   / (n ** 2 * phi * (1 - phi)))
    assert f"C 统计量 95% CI 宽约 {2 * 1.959964 * se:.2f}" in protocol
    lnoe = math.sqrt((1 - phi) / (n * phi))
    assert f"O/E 95% CI 约 {math.exp(-1.959964 * lnoe):.2f}–{math.exp(1.959964 * lnoe):.2f}" in protocol
    # calibration slope: Riley 2024 fallback — linear predictor normal in events and non-events with a
    # common variance, calibrated (slope 1, intercept 0); SE from the logistic-regression Fisher information
    assert "10.1136/bmj-2023-074821" in protocol
    nd = NormalDist()
    delta = 2 * nd.inv_cdf(c) ** 2
    sd, mu0 = math.sqrt(delta), math.log(phi / (1 - phi)) - delta / 2
    mu1 = mu0 + delta
    grid = [mu0 - 12 * sd + i * (mu1 - mu0 + 24 * sd) / 20000 for i in range(20001)]
    dens = [(1 - phi) * NormalDist(mu0, sd).pdf(x) + phi * NormalDist(mu1, sd).pdf(x) for x in grid]
    tot = sum(dens)
    info = [0.0, 0.0, 0.0]
    for x, d in zip(grid, dens):
        p = 1 / (1 + math.exp(-x))
        v = d / tot * p * (1 - p)
        info = [info[0] + v, info[1] + v * x, info[2] + v * x * x]
    var_slope = info[0] / (n * (info[0] * info[2] - info[1] ** 2))
    assert f"校准斜率 95% CI 宽约 {2 * 1.959964 * math.sqrt(var_slope):.2f}" in protocol


def test_example_buderer_numbers_match_power_analysis(protocol):
    pytest.importorskip("scipy")
    m = re.search(r"`power_analysis\.py (diagnostic [^`]+)`：需癌 (\d+) 例、非癌 (\d+) 例，按患病率 [\d.]+% 约 (\d+) 例",
                  protocol)
    assert m, "Buderer command and its result not found"
    out = subprocess.run([sys.executable, str(POWER)] + m.group(1).split(), capture_output=True, text=True,
                         check=True).stdout
    res = json.loads(out)
    assert (res["n_diseased"], res["n_non_diseased"], res["n_total"]) == tuple(int(m.group(i)) for i in (2, 3, 4))
    # the cancer count that must survive the image-quality exclusion is the same Buderer number
    assert f"图像质量排除后癌仍须 ≥ {res['n_diseased']} 例" in protocol
    assert f"癌少于 {res['n_diseased']} 例时灵敏度 CI 半宽达不到" in protocol


def test_example_reader_study_is_mrmc(protocol):
    assert "MRMC" in protocol and "RJafroc" in protocol
    for line in protocol.splitlines():
        if "DeLong" in line:
            assert "不对每位医生分别做 DeLong" in line or "两个模型之间" in line, line
    rq = _read(EXAMPLE / "research-question.md")
    assert "MRMC" in rq


def test_example_stard_mapping_covers_every_item(protocol):
    ids = _checklist_ids("stard-2015.yaml")
    line = next(line for line in protocol.splitlines() if line.startswith("- STARD 2015"))
    mapped = set()
    for group in re.findall(r"(?:^|[；：])\s*([\d–a-d、]+)（", line.split("：", 1)[1]):
        for token in group.split("、"):
            mapped.update(_expand(token, ids))
    missing = [i for i in ids if i not in mapped]
    assert not missing, f"STARD 2015 items not mapped: {missing}"
    assert "18（样本量）→ §2" in line and "5（前瞻/回顾设计）→ §1" in line


def test_example_state_matches_protocol(protocol):
    state = json.loads(_read(EXAMPLE / ".mrp-state.json"))
    assert state["hard_checkpoints"]["protocol"].endswith(re.search(r"status: confirmed \(hard checkpoint 1, ([\d-]+)\)",
                                                                    protocol).group(1))
    note = next(n["note"] for n in state["notes"] if n["skill"] == "study-design")
    seed = re.search(r"Split seed: (\d+)", protocol).group(1)
    assert seed in note and "nested CV" in note and "MRMC" in note
    assert "60/20/20" not in note
