"""Regression tests for the data-analysis-planning methods content.

The decision tree, the SAP extension and the method cards are advice, not code, so most checks pin the
advice that was wrong before (n-based data split, pre-test gating, %-based missing-data grid, LLM GLMM
without the question x model term, ...). The Python recipes printed in the cards are extracted from the
markdown and run on simulated data, so a broken recipe fails here, not in a user's project.
"""

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
DAP = ROOT / "skills" / "data-analysis-planning"
REFS = DAP / "references"
CARDS = REFS / "method-cards"


def _read(path):
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def tree():
    return yaml.safe_load(_read(REFS / "stat-method-decision-tree.yaml"))


def _python_block(text, marker):
    """Return the ```python block that contains `marker`."""
    for block in re.findall(r"```python\n(.*?)```", text, flags=re.S):
        if marker in block:
            return block
    raise AssertionError(f"no python block containing {marker!r}")


# ── MA-1 / D3: validation split by model type and events, not by total n ─────────────────────

def test_data_split_is_not_an_n_table(tree):
    split = tree["deep_learning_training"]["data_split"]
    assert isinstance(split, dict), "data_split must be the D3 rule, not the old list of n tiers"
    text = yaml.safe_dump(split, allow_unicode=True)
    assert not re.search(r"n\s*[<>]=?\s*\d", text), "no tier may be chosen by total patient n"
    assert "60/20/20" not in text
    assert "EFFECTIVE" in split["principle"] and "events" in split["principle"]
    reg = split["regression_or_classical_model"]["method"]
    assert "ALL available data" in reg and "bootstrap" in reg and "No random hold-out" in reg
    tuned = split["tuned_ml_or_dl_model"]
    assert "Nested cross-validation" in tuned["method"] and "enough events" in tuned["method"]
    assert "10.1002/sim.9025" in tuned["split_condition"]          # Riley external-validation size
    assert "REQUIRED" in split["external_or_temporal_validation"]
    rules = " ".join(tree["deep_learning_training"]["data_split_rules"])
    assert "patient ID" in rules and "Stratify" in rules and "events" in rules


def test_sap_texts_follow_d3():
    skill = _read(DAP / "SKILL.md")
    ext = _read(REFS / "ai-ml-sap-extension.md")
    for text in (skill, ext):
        assert "档位" not in text and "落在哪一档" not in text and "按样本量分档" not in text
        assert "bootstrap" in text and "嵌套交叉验证" in text
    assert "n < 50" not in ext
    assert "60/20/20" in skill and "不按总人数分档" in skill                 # named only as the mistake
    reg = _read(CARDS / "regression-and-prediction-models.md")
    assert "Steyerberg 2001" in reg and "10.1016/S0895-4356(01)00341-9" in reg


# ── MA-2: no pre-test gating left in the tree ─────────────────────────────────────────────────

def test_no_pretest_gating(tree):
    corr = tree["association"]["continuous_vs_continuous"]
    assert "normal" not in corr and "non_normal" not in corr
    two = tree["longitudinal"]["two_timepoints"]
    assert "differences_normal" not in two and "differences_non_normal" not in two
    assert "not chosen by a normality pre-test" in two["rank_based"]
    rm = tree["longitudinal"]["multiple_timepoints"]["continuous"]["balanced_complete"]
    assert "Greenhouse-Geisser correction prespecified" in rm
    sph = tree["assumptions"]["sphericity"]
    assert "if violated" not in sph and "Prespecify the Greenhouse-Geisser" in sph
    skill = _read(DAP / "SKILL.md")
    assert "配对看差值" not in skill


# ── MA-3: missing data chosen by mechanism, not by % ──────────────────────────────────────────

def test_missing_data_not_by_proportion(tree):
    md = tree["missing_data"]
    assert "by_proportion" not in md
    text = yaml.safe_dump(md, allow_unicode=True)
    assert not re.search(r"(less|more)_than_\d+_percent|\d+_to_\d+_percent", text)
    dec = md["decision"]
    assert "outcome" in dec["complete_case_unbiased_when"] and "MNAR" in dec["complete_case_unbiased_when"]
    # MNAR not related to the outcome -> complete cases, not "MI + sensitivity" (the old grid cell)
    assert "complete cases" in dec["covariate_mnar_not_outcome_related"]
    assert "No %-cut-off" in dec["large_proportion"]
    raw = _read(REFS / "stat-method-decision-tree.yaml")
    assert "10.1016/j.jclinepi.2019.02.016" in raw and "10.1093/ije/dyz032" in raw
    card = _read(CARDS / "missing-data.md")
    assert "比例 × 机制" not in card and "选哪一格" not in card
    # the card's complete-case rule must not reintroduce "only when little is missing" (round 2)
    cc = next(line for line in card.splitlines() if line.startswith("- **完整病例分析什么时候可以接受**"))
    assert "缺失很少" not in cc and "与缺失比例多少无关" in cc
    # the logistic-regression exception the yaml states must be in the card too (exposure OR unbiased when
    # completeness depends on the outcome but not on the exposure)
    assert "For logistic regression the exposure OR also stays unbiased" in dec["complete_case_unbiased_when"]
    assert re.search(r"logistic 回归[^。]*与暴露无关时，暴露的 OR 仍不偏[^。]*同时取决于结局和暴露时才有偏", cc), cc
    assert "主要结果（多重插补）" not in card
    skill = _read(DAP / "SKILL.md")
    assert "比例 × 机制" not in skill and "比例 + 机制" not in skill and "缺失超过 20%" not in skill


# ── MA-4 / MA-12: mediation, causal and survival branches ─────────────────────────────────────

def test_mediation_counterfactual(tree):
    med = tree["mediation"]
    assert "traditional" not in med
    assert "Counterfactual" in med["method"] and "Baron-Kenny" not in med["method"]
    assert "Baron-Kenny" in med["historical_only"]


def test_causal_and_survival_branches(tree):
    ps = tree["causal_inference"]["propensity_score"]
    steps = " ".join(ps["steps"])
    for word in ("ATE", "ATT", "ATO", "AIPW", "TMLE", "bootstrap"):
        assert word in steps, word
    assert "overlap_weights" in ps["methods"] and "doubly_robust" in ps["methods"]
    assert "truncation" in ps["methods"]["iptw"]
    ph = tree["survival_extended"]["single_event"]["if_ph_violated"]
    assert "RMST" in ph["main_exposure"] and "prespecified tau" in ph["main_exposure"]
    cr = tree["survival_extended"]["competing_risks"]["model"]
    assert "Cause-specific" in cr["aetiology"] and "Fine-Gray" in cr["absolute_risk_or_prognosis"]
    assert "landmark" in tree["survival_extended"]["immortal_time"]["method"]


# ── MA-5 / MA-6 / MA-7: regression and missing-data recipes ───────────────────────────────────

def test_pmvalsampsize_scope():
    card = _read(CARDS / "regression-and-prediction-models.md")
    row = next(line for line in card.splitlines() if line.startswith("| 外部验证样本量"))
    assert "都只支持二分类结局" in row and "Archer 2021" in row and "Riley 2022" in row
    for doi in ("10.1002/sim.9025", "10.1002/sim.8766", "10.1002/sim.9275"):
        assert doi in card


def test_l1_back_transform_recipe_runs():
    np = pytest.importorskip("numpy")
    pytest.importorskip("sklearn")
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    code = _python_block(_read(CARDS / "regression-and-prediction-models.md"), "scaler.mean_")
    rng = np.random.default_rng(3)
    X = np.column_stack([rng.normal(60, 10, 400), rng.normal(25, 4, 400), rng.normal(1, 0.3, 400)])
    y = rng.binomial(1, 1 / (1 + np.exp(-(-8 + 0.08 * X[:, 0] + 0.1 * X[:, 1] + 0.5 * X[:, 2]))))
    pipe = make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=2000)).fit(X, y)
    ns = {"pipe": pipe}
    exec(code, ns)                                                     # the card's recipe
    lp = ns["intercept"] + X @ ns["coef"]
    assert np.allclose(lp, pipe.decision_function(X))


def test_recode_missing_recipe_runs():
    pd = pytest.importorskip("pandas")
    import io

    code = _python_block(_read(CARDS / "missing-data.md"), "def recode_missing")
    ns = {}
    exec(code.split("\ndf = recode_missing")[0], ns)                  # define the helper only
    recode = ns["recode_missing"]
    df = pd.read_csv(io.StringIO("plt\n210\n999\n/\n未查\n180\n"))   # text column: object (pandas 2) / str (pandas 3)
    out = recode(df.copy(), "plt", ["/", "未查"], [999])
    assert out["plt"].isna().sum() == 3 and out["plt"].dropna().tolist() == [210, 180]
    num = pd.DataFrame({"plt": [210.0, 999.0, None]})
    assert recode(num.copy(), "plt", ["/"], [999])["plt"].isna().sum() == 2
    with pytest.raises((ValueError, TypeError)):                      # unlisted spelling is not silently dropped
        recode(pd.read_csv(io.StringIO("plt\n210\n不详\n")), "plt", ["/", "未查"], [999])
    card = _read(CARDS / "missing-data.md")
    assert "from sklearn.experimental import enable_iterative_imputer" in card


# ── MB-1 / MB-9 / LLM-1: LLM card ─────────────────────────────────────────────────────────────

def test_llm_glmm_has_question_by_model_term():
    card = _read(CARDS / "llm-vlm-evaluation.md")
    glmer = [line for line in card.splitlines() if "glmer(correct ~ model" in line]
    assert glmer, "the repeated-run GLMM formula must still be given"
    for line in glmer:
        assert "(1 | question_id:model)" in line, line


def test_llm_paired_recipe_runs():
    np = pytest.importorskip("numpy")
    pd = pytest.importorskip("pandas")
    pytest.importorskip("scipy")
    pytest.importorskip("statsmodels")
    code = _python_block(_read(CARDS / "llm-vlm-evaluation.md"), "pivot_table")
    rng = np.random.default_rng(9)
    rows = [{"question_id": q, "model": m, "correct": int(rng.random() < 0.6 + 0.1 * (m == "B"))}
            for q in range(40) for m in ("A", "B") for _ in range(3)]
    ns = {"d": pd.DataFrame(rows), "print": lambda *a, **k: None}
    exec(code, ns)
    assert 0 <= ns["res"].pvalue <= 1 and ns["tab"].shape == (2, 2)


def test_run_agreement_consistent_with_agreement_card():
    llm = _read(CARDS / "llm-vlm-evaluation.md")
    agree = _read(CARDS / "agreement-and-reliability.md")
    assert "评分者不固定" in llm and "可以互换" in llm
    assert "可以互换" in agree and "身份固定的评分者" in agree


def test_reporting_guideline_citations():
    diag = _read(CARDS / "diagnostic-accuracy-and-ai-evaluation.md")
    ext = _read(REFS / "ai-ml-sap-extension.md")
    llm = _read(CARDS / "llm-vlm-evaluation.md")
    assert "STARD-AI 是主要报告规范" in diag and "10.1038/s41591-025-03953-8" in diag
    assert "以 STARD-AI 为主要报告规范" in ext and "10.1038/s41591-025-03953-8" in ext
    assert "CHART" in ext and "10.1136/bmjmed-2025-001632" in ext
    assert "10.1136/bmjmed-2025-001632" in llm
    # modified STARD-AI items replace the STARD 2015 wording; stard-2015.yaml alone is not enough (round 2)
    assert "STARD 2015 的条目照常逐条满足" not in diag and "同时逐条满足 STARD 2015" not in ext
    for text in (diag, ext):
        assert "以 STARD-AI 的措辞为准" in text and "STARD-AI 官方清单" in text
    assert "`stard-ai`" in llm
    clustered = _read(CARDS / "clustered-and-repeated-data.md").split("## 6. 对应报告规范")[1].split("## 参考")[0]
    assert re.search(r"AI 诊断准确性研究以 `stard-ai`[^；。]*为主、与 `stard` 合用", clustered)
    for text in (diag, ext, llm):                                       # index membership is another package's job
        assert "也不在规范索引里" not in text and "仓库索引无条目" not in text


# ── MB-6 / MB-7 / MB-10: meta-analysis card ───────────────────────────────────────────────────

def test_meta_card():
    card = _read(CARDS / "meta-analysis.md")
    assert "只有 2 项研究时怎么办也要预先写：这时 HKSJ" not in card
    assert "12.71" in card and "10.1186/s12874-015-0091-1" in card
    assert 'method_re="dl"' in card and "不把负的 τ² 截断为 0" in card
    sec1 = card.split("## 1.")[1].split("## 2.")[0]
    assert "提取结果数据之前" in sec1
    assert "零事件研究有几项" not in sec1.split("计划前能用的只有")[1].split("结果数据里才能看到")[0]


def test_statsmodels_dl_claim_still_true():
    """The card warns that statsmodels' DL tau^2 is not truncated; keep the warning honest."""
    np = pytest.importorskip("numpy")
    pytest.importorskip("statsmodels")
    from statsmodels.stats.meta_analysis import combine_effects

    res = combine_effects(np.array([0.10, 0.12, 0.11, 0.09, 0.105]),
                          np.array([0.04, 0.05, 0.03, 0.06, 0.045]), method_re="dl")
    if res.tau2 >= 0:
        pytest.skip("installed statsmodels truncates DL tau^2; the card's warning names the versions it was checked on")
    assert "不把负的 τ² 截断为 0" in _read(CARDS / "meta-analysis.md")


# ── MB-8: mixedlm reports z-tests ─────────────────────────────────────────────────────────────

def test_mixedlm_z_warning_and_bootstrap_recipe():
    card = _read(CARDS / "clustered-and-repeated-data.md")
    row = next(line for line in card.splitlines() if line.startswith("| 线性混合模型"))
    assert "z 检验" in row and "pbkrtest" in row
    np = pytest.importorskip("numpy")
    pd = pytest.importorskip("pandas")
    pytest.importorskip("statsmodels")
    code = _python_block(card, "boot_id").replace("range(2000)", "range(15)")
    rng = np.random.default_rng(4)
    g = np.repeat(np.arange(12), 6)
    x = rng.integers(0, 2, g.size)
    df = pd.DataFrame({"y": 1 + 0.5 * x + rng.normal(0, 0.7, 12)[g] + rng.normal(0, 1, g.size),
                       "x": x, "surgeon_id": g})
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ns = {"df": df}
        exec(code, ns)
    assert len(ns["boot"]) == 15 and ns["ci"][0] <= ns["ci"][1]


# ── CG-11: omics reference matches the tree ───────────────────────────────────────────────────

def test_omics_reference(tree):
    omics = _read(REFS / "omics-methods.md")
    assert "n=200" not in omics and "≥1000 次" in omics
    assert "limma / t-test" not in omics and "moderated t-test" in omics
    assert "pseudobulk" in omics and "10.1038/s41467-021-25960-2" in omics
    assert "Pseudobulk" in tree["omics"]["differential_analysis"]["single_cell"]
    assert ">=1000 permutations" in tree["omics"]["dimensionality_reduction"]["supervised"]


# ── SKILL.md residuals (penalised regression as a fix; Cochran-Armitage "only") ───────────────

def test_skill_md_residuals():
    skill = _read(DAP / "SKILL.md")
    assert "改用惩罚回归" not in skill
    assert "才用 Cochran-Armitage" not in skill


def test_markdown_tables_keep_their_columns():
    """An unescaped | inside a table cell (e.g. `P>|z|`) silently adds a column."""
    files = [DAP / "SKILL.md", REFS / "ai-ml-sap-extension.md", REFS / "omics-methods.md",
             *sorted(CARDS.glob("*.md"))]
    for path in files:
        width = None
        for n, line in enumerate(_read(path).splitlines(), 1):
            if not line.startswith("|"):
                width = None
                continue
            cells = len(re.findall(r"(?<!\\)\|", line))
            if width is None:
                width = cells
            assert cells == width, f"{path.name}:{n} has {cells} pipes, header has {width}"
