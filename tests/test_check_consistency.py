"""Tests for tools/check_consistency.py (the repository consistency guard).

Each test copies the repository to a temp dir, breaks the copy in ONE way and runs
the copied guard on it. The test passes when the guard reports a new error of the
expected kind. Errors already present in the untouched copy are subtracted, so the
tests do not depend on the working tree being consistent at the moment they run.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
GUARD = Path("tools") / "check_consistency.py"
IGNORE = shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "node_modules", "*.pyc",
                                ".reproduce-check", "results")


def run_guard(repo):
    proc = subprocess.run([sys.executable, str(repo / GUARD)], capture_output=True, text=True,
                          encoding="utf-8", timeout=120)
    assert proc.returncode in (0, 1), proc.stdout + proc.stderr
    errors = {line.strip()[2:] for line in proc.stdout.splitlines() if line.strip().startswith("- ")}
    assert (proc.returncode == 1) == bool(errors), proc.stdout
    return errors


@pytest.fixture(scope="module")
def pristine(tmp_path_factory):
    repo = tmp_path_factory.mktemp("pristine") / "repo"
    shutil.copytree(ROOT, repo, ignore=IGNORE, symlinks=True)
    return repo, run_guard(repo)


@pytest.fixture
def repo(pristine, tmp_path):
    src, _ = pristine
    dst = tmp_path / "repo"
    shutil.copytree(src, dst, symlinks=True)
    return dst


def new_errors(pristine, repo):
    _, baseline = pristine
    return run_guard(repo) - baseline


def assert_caught(pristine, repo, pattern):
    found = new_errors(pristine, repo)
    assert any(re.search(pattern, e) for e in found), f"guard did not report {pattern!r}; new errors: {found}"


def append(repo, rel, text):
    p = repo / rel
    p.write_text(p.read_text(encoding="utf-8") + "\n" + text + "\n", encoding="utf-8")


def real_counts():
    journals = yaml.safe_load((ROOT / "skills/manuscript-writing/references/journal-templates.yaml")
                              .read_text(encoding="utf-8"))["templates"]
    standards = yaml.safe_load((ROOT / "skills/reporting-standards/references/checklists/standards-index.yaml")
                               .read_text(encoding="utf-8"))["standards"]

    def has(j, k):
        return isinstance(j, dict) and j.get(k) is not None and str(j.get(k)).strip() != ""

    return {
        "skills": sum((d / "SKILL.md").is_file() for d in (ROOT / "skills").iterdir()),
        "commands": len(list((ROOT / "commands").glob("*.md"))),
        "journals": len(journals),
        "standards": len(standards),
        "scripts": len(list((ROOT / "skills").glob("*/scripts/*.py"))),
        "if_year": sum(has(j, "IF_year") for j in journals),
        "guidelines_checked": sum(has(j, "guidelines_checked") for j in journals),
        "checklists": sum(has(s, "file") for s in standards),
    }


# ── sanity ──────────────────────────────────────────────────────────────────

def test_untouched_copy_reports_the_same_as_the_repo(pristine):
    _, baseline = pristine
    proc = subprocess.run([sys.executable, str(ROOT / GUARD)], capture_output=True, text=True, encoding="utf-8")
    real = {line.strip()[2:] for line in proc.stdout.splitlines() if line.strip().startswith("- ")}
    assert real == baseline


def test_guard_without_findings_exits_0_and_prints_one_summary_line(pristine, repo):
    _, baseline = pristine
    if baseline:
        pytest.skip("the working tree currently has consistency errors")
    proc = subprocess.run([sys.executable, str(repo / GUARD)], capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0 and proc.stdout.startswith("✅")


# ── (b) documented counts ───────────────────────────────────────────────────

WRONG_CLAIMS = [
    pytest.param("README.md", "MRP has 99 skills.", r"README\.md:\d+ claims 99 skills", id="skills-en"),
    pytest.param("README_CN.md", "共 99 个 skill。", r"README_CN\.md:\d+ claims 99 skills", id="skills-cn"),
    pytest.param("docs/USER-MANUAL.md", "一共 99 个斜杠命令。", r"claims 99 commands", id="commands-cn"),
    pytest.param("README.md", "There are 99 slash commands.", r"claims 99 commands", id="commands-en"),
    pytest.param("README.md", "It ships 99 journal templates.", r"claims 99 journals", id="journals-en"),
    pytest.param("README_CN.md", "收录 99 本期刊。", r"claims 99 journals", id="journals-cn"),
    pytest.param("README.md", "No software equivalent; 99 domain-specific compliance standards.",
                 r"claims 99 standards", id="standards-alternative-phrasing"),
    pytest.param("docs/USER-MANUAL.md", "99 项报告规范。", r"claims 99 standards", id="standards-cn"),
    pytest.param("README.md", "## Reporting Standards (99)", r"claims 99 standards", id="standards-heading"),
    pytest.param("README.md", "It bundles 99 Python scripts.", r"claims 99 scripts", id="scripts-en"),
    pytest.param("docs/USER-MANUAL.md", "99 个内置脚本。", r"claims 99 scripts", id="scripts-cn"),
    pytest.param("README.md", "99 frequently targeted journals have `IF_year`/`IF_source` fields.",
                 r"claims 99 journals with IF_year", id="if-year-en"),
    pytest.param("README_CN.md", "99 本常投期刊有 `IF_year`/`IF_source` 字段。",
                 r"claims 99 journals with IF_year", id="if-year-cn"),
    pytest.param("README.md", "99 journals carry `guidelines_checked`.",
                 r"claims 99 journals with guidelines_checked", id="guidelines-checked-en"),
    pytest.param("README.md", "99 journals were re-checked against their official author guidelines.",
                 r"claims 99 journals with guidelines_checked", id="guidelines-checked-phrase"),
    pytest.param("CONTRIBUTING.md", "the 99-skill framework", r"CONTRIBUTING\.md:\d+ claims 99 skills",
                 id="outside-the-six-files"),
    pytest.param("hooks/session-start.sh", "# a framework of 99 skills", r"session-start\.sh:\d+ claims 99 skills",
                 id="hook"),
    pytest.param("skills/manuscript-writing/SKILL.md", "模板库共 99 个期刊。", r"SKILL\.md:\d+ claims 99 journals",
                 id="skill-md-library-total"),
    # "到 / 至 / -" before a number is a range only when another number comes first
    pytest.param("README_CN.md", "报告规范已扩展到 99 项报告规范。", r"README_CN\.md:\d+ claims 99 standards",
                 id="cn-extended-to"),
    pytest.param("docs/USER-MANUAL.md", "期刊库增加到 99 本期刊。", r"USER-MANUAL\.md:\d+ claims 99 journals",
                 id="cn-increased-to"),
    pytest.param("README.md", "Framework - 99 skills.", r"claims 99 skills", id="hyphen-before-number"),
    pytest.param("README.md", "Framework – 99 skills.", r"claims 99 skills", id="en-dash-before-number"),
    pytest.param("README.md", "MRP covers 99 reporting guidelines.", r"claims 99 standards", id="reporting-guidelines"),
    pytest.param("README_CN.md", "收录 99 个报告指南。", r"claims 99 standards", id="reporting-guidelines-cn"),
    pytest.param("README.md", "It ships 99 checklists.", r"claims 99 item-by-item checklists", id="checklists"),
    pytest.param("docs/architecture.md", "99 with a local checklist", r"claims 99 item-by-item checklists",
                 id="checklists-with-a"),
    pytest.param("README.md", "It ships 99 templates.", r"claims 99 journals", id="bare-templates"),
    pytest.param("README.md", "It ships 1,240 journals.", r"claims 1240 journals", id="thousands-separator"),
    pytest.param("README.md", "Of the 240 journals, 99 have `IF_year`.", r"claims 99 journals with IF_year",
                 id="if-year-subset-after-total"),
    pytest.param("README.md", "The 240 journals include 99 with `IF_year`.", r"claims 99 journals with IF_year",
                 id="if-year-include"),
    pytest.param("skills/journal-selection/SKILL.md", "覆盖 99 个报告规范。", r"SKILL\.md:\d+ claims 99 standards",
                 id="skill-md-standards-total"),
    # two stale counts J3 fixed by hand (README "from 47 options", the architecture mind-map root)
    pytest.param("docs/architecture.md", '  root(("99 Reporting<br/>Standards"))',
                 r"architecture\.md:\d+ claims 99 standards", id="standards-mermaid-br"),
    pytest.param("README.md", "| Ignores reporting standards | Matches study type to the correct standard from 99 options |",
                 r"README\.md:\d+ claims 99 standards", id="standards-from-n-options"),
    pytest.param("README.md", "Claude picks from 99 options: the reporting standards of the index.",
                 r"README\.md:\d+ claims 99 standards", id="standards-from-n-options-before"),
    # "from A to B" after a change verb is a change, not a range: B is the new total
    pytest.param("README.md", "Standards went from 47 to 99 standards.", r"README\.md:\d+ claims 99 standards",
                 id="went-from-to"),
    # a list right after the count exempts it only when it names exactly that many items
    pytest.param("README.md", "MRP ships 99 reporting standards (CONSORT, STROBE and PRISMA).",
                 r"README\.md:\d+ claims 99 standards", id="list-of-another-size"),
    pytest.param("README.md", "It ships 99 templates for journals.", r"claims 99 journals", id="templates-for-journals"),
    # reference files: wording that states the size of the library
    pytest.param("skills/data-analysis-planning/references/omics-methods.md", "The library holds 99 standards.",
                 r"omics-methods\.md:\d+ claims 99 standards", id="reference-library-holds"),
    pytest.param("skills/data-analysis-planning/references/omics-methods.md", "Check all 99 reporting standards.",
                 r"omics-methods\.md:\d+ claims 99 standards", id="reference-all-n"),
    pytest.param("skills/data-analysis-planning/references/omics-methods.md", "规范库共 99 项规范。",
                 r"omics-methods\.md:\d+ claims 99 standards", id="reference-cn-total"),
    pytest.param("skills/data-analysis-planning/references/omics-methods.md", "There are 999 journals in total.",
                 r"omics-methods\.md:\d+ claims 999 journals", id="reference-journals-in-total"),
]


@pytest.mark.parametrize("rel, line, pattern", WRONG_CLAIMS)
def test_wrong_count_claim_is_caught(pristine, repo, rel, line, pattern):
    append(repo, rel, line)
    assert_caught(pristine, repo, pattern)


def test_correct_claims_and_subsets_are_not_flagged(pristine, repo):
    c = real_counts()
    append(repo, "README.md", "\n".join([
        f"MRP has {c['skills']} skills, {c['commands']} slash commands and {c['scripts']} bundled Python scripts.",
        f"It ships {c['journals']} journal templates and {c['standards']} reporting standards.",
        f"{c['if_year']} frequently targeted journals have `IF_year` fields; the rest hold JCR 2022 values.",
        f"{c['guidelines_checked']} of the {c['journals']} journals carry `guidelines_checked`.",
    ]))
    append(repo, "README_CN.md", f"{c['journals']} 本期刊中有 {c['guidelines_checked']} 本带 `guidelines_checked`。")
    append(repo, "skills/journal-selection/SKILL.md", "每个梯队 1–2 个期刊，共 3 个候选期刊；出现在 4 个 skill 里。")
    assert new_errors(pristine, repo) == set()


def test_totals_ranges_and_selections_are_told_apart(pristine, repo):
    c = real_counts()
    version = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
    append(repo, "README.md", "\n".join([
        f"Of the {c['journals']} journals, {c['if_year']} have `IF_year`.",
        f"The {c['journals']} journals include {c['if_year']} with `IF_year`.",
        f"Among the {c['journals']} journals, {c['if_year']} carry `IF_year` values from JCR 2024.",
        f"{c['checklists']} of the {c['standards']} standards ship with an item-by-item checklist.",
        "The skill proposes 3 target journals and 2 backup journals.",
        "Pick from the top-5 journals; a study uses 1-2 reporting standards and 2 to 4 skills.",
        "Choose the figure style from 3 options.",                    # "options" without a standard is no total
        f"Release {version} – {c['skills']} skills.",           # the current version, not a count
    ]))
    append(repo, "README_CN.md", "每个梯队 1 到 2 本期刊；一次调用 20-30 个 skill；推荐 3 个目标期刊；10 个脚本的清单。")
    assert new_errors(pristine, repo) == set()


# Ordinary small numbers that are not the library: a named short list, the singular, "templates for"
# something else, "options" beside "standard deviation" — and, in reference files, anything that does
# not state the size of the library.
ORDINARY_COUNTS = {
    "README.md": [
        "STARD has 2 checklists: one for the abstract and one for the full text.",
        "Choose from 6 templates for the article types.",
        "A diagnostic AI study usually follows 2 reporting guidelines (STARD and CLAIM).",
        "The skill picks the standard from 2 options when the design is mixed.",
        "It uses only the Python standard library; pick the layout from 3 options.",
    ],
    "docs/USER-MANUAL.md": [
        "每篇稿件提交前填写 1 份核查清单。",
        "Pick the summary statistic from 3 options and report the standard deviation alongside the mean.",
    ],
    "skills/data-analysis-planning/references/omics-methods.md": [
        "Report against 2 standards: MIAME and MINSEQE.",
        "需同时满足 2 项规范。",
        "STARD has 2 checklists: one for the abstract and one for the full text.",
        "每篇稿件提交前填写 1 份核查清单。",
        "Choose from 6 templates for the article types.",
        "A diagnostic AI study usually follows 2 reporting guidelines (STARD and CLAIM).",
        "Pick the summary statistic from 3 options and report the standard deviation alongside the mean.",
        "Most designs need 2 standards; pick 3 journals.",
        "Use 2 standards in all mixed designs.",
        "## Diagnostic AI (2 standards)",
    ],
    "skills/reporting-standards/references/checklists/standards-index.yaml": [
        "# pair it with 2 reporting standards when the design is mixed",
    ],
    "skills/manuscript-writing/references/journal-templates.yaml": [
        "# All 3 journals in this family share one template.",
    ],
}


def test_ordinary_small_numbers_are_not_library_totals(pristine, repo):
    for rel, lines in ORDINARY_COUNTS.items():
        append(repo, rel, "\n".join(lines))
    assert new_errors(pristine, repo) == set()


@pytest.mark.parametrize("rel, old, new, pattern", [
    pytest.param("skills/reporting-standards/references/checklists/standards-index.yaml",
                 "Master Index ({standards} standards)", "Master Index (99 standards)",
                 r"standards-index\.yaml:1 claims 99 standards", id="index-title"),
    pytest.param("skills/reporting-standards/references/checklists/standards-index.yaml",
                 "({checklists} of {standards}:", "({checklists_plus} of {standards}:",
                 r"standards-index\.yaml header says '\(\d+ of \d+: \.\.\.\)'", id="index-checklist-list"),
    pytest.param("skills/manuscript-writing/references/journal-templates.yaml",
                 "({journals} journals total", "(999 journals total",
                 r"journal-templates\.yaml:\d+ claims 999 journals", id="journal-library-summary"),
])
def test_totals_in_reference_and_data_files_are_checked(pristine, repo, rel, old, new, pattern):
    c = real_counts()
    c["checklists_plus"] = c["checklists"] + 1
    p = repo / rel
    text = p.read_text(encoding="utf-8")
    old, new = old.format(**c), new.format(**c)
    if old not in text:
        pytest.skip(f"{rel} no longer states {old!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")
    assert_caught(pristine, repo, pattern)


def test_per_specialty_counts_in_the_journal_library_are_not_totals(pristine, repo):
    append(repo, "skills/manuscript-writing/references/journal-templates.yaml", "# Urology:   3 journals")
    assert new_errors(pristine, repo) == set()


def test_adding_a_checklist_entry_makes_the_stated_checklist_counts_wrong(pristine, repo):
    p = repo / "skills/reporting-standards/references/checklists/standards-index.yaml"
    text = p.read_text(encoding="utf-8")
    p.write_text(text.replace("standards:\n", "standards:\n  - id: zz-test\n    name: ZZ\n    file: zz-test.yaml\n", 1),
                 encoding="utf-8")
    real = real_counts()["checklists"]
    assert_caught(pristine, repo, rf"claims {real} item-by-item checklists \(repo has {real + 1}\)")
    assert_caught(pristine, repo, r"standards-index\.yaml header says .* not listed: \['zz-test'\]")


def test_adding_a_journal_makes_every_stated_journal_count_wrong(pristine, repo):
    p = repo / "skills/manuscript-writing/references/journal-templates.yaml"
    text = p.read_text(encoding="utf-8")
    entry = "templates:\n  - id: zz-test-journal\n    journal: ZZ Test Journal\n"
    p.write_text(text.replace("templates:\n", entry, 1), encoding="utf-8")
    real = real_counts()["journals"] + 1
    assert_caught(pristine, repo, rf"claims {real - 1} journals \(repo has {real}\)")


def test_adding_a_standard_makes_every_stated_standards_count_wrong(pristine, repo):
    p = repo / "skills/reporting-standards/references/checklists/standards-index.yaml"
    text = p.read_text(encoding="utf-8")
    p.write_text(text.replace("standards:\n", "standards:\n  - id: zz-test\n    name: ZZ\n", 1), encoding="utf-8")
    real = real_counts()["standards"] + 1
    assert_caught(pristine, repo, rf"claims {real - 1} standards \(repo has {real}\)")


def test_journal_with_if_year_changes_the_if_year_count(pristine, repo):
    p = repo / "skills/manuscript-writing/references/journal-templates.yaml"
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    n = real_counts()["if_year"]
    append(repo, "README.md", f"{n} journals have `IF_year` fields.")
    assert new_errors(pristine, repo) == set()
    victim = next(j for j in data["templates"] if j.get("IF_year"))
    text = p.read_text(encoding="utf-8")
    text = re.sub(rf"(- id: {re.escape(victim['id'])}\n(?:    .*\n)*?)    IF_year: .*\n", r"\1", text, count=1)
    p.write_text(text, encoding="utf-8")
    assert_caught(pristine, repo, rf"README\.md:\d+ claims {n} journals with IF_year \(repo has {n - 1}\)")


def test_removing_a_command_is_caught(pristine, repo):
    name = sorted((repo / "commands").glob("*.md"))[0]
    name.unlink()
    assert_caught(pristine, repo, r"claims \d+ commands \(repo has \d+\)")


# ── (j) eval coverage ───────────────────────────────────────────────────────

def test_new_skill_without_an_eval_case_is_caught(pristine, repo):
    d = repo / "skills" / "zz-new-skill"
    d.mkdir()
    (d / "SKILL.md").write_text("---\nname: zz-new-skill\ndescription: Use when testing the guard.\n---\n\n# x\n",
                                encoding="utf-8")
    assert_caught(pristine, repo, r"\(j\) skill 'zz-new-skill' has no eval case")


def _cases_expecting(repo, skill):
    out = []
    for g in (repo / "evals").glob("*/graders/*.md"):
        text = g.read_text(encoding="utf-8")
        if re.search(rf"input_match:.*{re.escape(skill)}", text) and "max: 0" not in text:
            out.append(g.parent.parent)
    return out


def test_skill_whose_eval_cases_are_removed_is_caught(pristine, repo):
    cases = _cases_expecting(repo, "figure-generation")
    assert cases
    for c in cases:
        shutil.rmtree(c)
    assert_caught(pristine, repo, r"\(j\) skill 'figure-generation' has no eval case")


def test_a_must_not_invoke_grader_does_not_count_as_coverage(pristine, repo):
    for c in _cases_expecting(repo, "figure-generation"):
        for g in (c / "graders").glob("*.md"):
            text = g.read_text(encoding="utf-8")
            g.write_text(text.replace("min: 1", "min: 0\nmax: 0"), encoding="utf-8")
    assert_caught(pristine, repo, r"\(j\) skill 'figure-generation' has no eval case")


def test_wrong_eval_case_total_and_tag_count_are_caught(pristine, repo):
    p = repo / "evals" / "README.md"
    text = p.read_text(encoding="utf-8")
    if not re.search(r"There are \d+ cases", text):
        pytest.skip("evals/README.md states no case total")
    p.write_text(re.sub(r"There are \d+ cases", "There are 999 cases", text, count=1), encoding="utf-8")
    append(repo, "evals/README.md", "| `smoke` | 999 | wrong |")
    found = new_errors(pristine, repo)
    assert any("says 999 eval cases" in e for e in found), found
    assert any("tag 'smoke' has 999 cases" in e for e in found), found


# ── (h) links and anchors ───────────────────────────────────────────────────

def test_broken_anchor_is_caught(pristine, repo):
    append(repo, "README.md", "See [nowhere](#no-such-heading-here).")
    assert_caught(pristine, repo, r"README\.md:\d+ links to #no-such-heading-here")


def test_anchor_into_another_file_follows_its_headings(pristine, repo):
    append(repo, "docs/USER-MANUAL.md", "[ok](../SECURITY.md#reporting-a-vulnerability) "
                                        "[bad](../SECURITY.md#reporting-a-vulnerability-now)")
    found = new_errors(pristine, repo)
    assert any("#reporting-a-vulnerability-now" in e for e in found), found
    assert not any(e.endswith("anchor #reporting-a-vulnerability") for e in found), found


def test_renamed_heading_breaks_links_to_it(pristine, repo):
    p = repo / "SECURITY.md"
    p.write_text(p.read_text(encoding="utf-8").replace("## Reporting a vulnerability", "## How to report"),
                 encoding="utf-8")
    append(repo, "CONTRIBUTING.md", "[report](SECURITY.md#reporting-a-vulnerability)")
    assert_caught(pristine, repo, r"CONTRIBUTING\.md:\d+ links to SECURITY\.md#reporting-a-vulnerability")


def test_missing_link_target_is_caught(pristine, repo):
    append(repo, "SECURITY.md", "[gone](docs/no-such-file.md)")
    assert_caught(pristine, repo, r"SECURITY\.md:\d+ links to docs/no-such-file\.md, which does not exist")


# ── (a) versions, (f) frontmatter, (+) hook ─────────────────────────────────

def test_version_mismatch_is_caught(pristine, repo):
    p = repo / "install.sh"
    p.write_text(re.sub(r'MRP_VERSION="[^"]*"', 'MRP_VERSION="' + ".".join(["0"] * 3) + '"',
                        p.read_text(encoding="utf-8")), encoding="utf-8")
    assert_caught(pristine, repo, r"\(a\) version mismatch in install\.sh")


def test_stray_version_is_caught(pristine, repo):
    append(repo, "docs/architecture.md", "Released as " + ".".join(["9"] * 3) + ".")
    assert_caught(pristine, repo, r"\(a\) stray version '9\.9\.9' in docs/architecture\.md")


def test_tool_versions_are_not_stray(pristine, repo):
    append(repo, "docs/architecture.md", "Tested with numpy " + ".".join(["9"] * 3) + ".")
    assert not any("stray version" in e for e in new_errors(pristine, repo))


def test_pinned_actions_and_packages_are_not_stray_versions(pristine, repo):
    v = ".".join(["9"] * 3)
    append(repo, ".github/workflows/ci.yml", "\n".join([
        f"      - uses: actions/checkout@{'a' * 40}  # v{v}",
        f"        run: npm install --global @anthropic-ai/claude-code@{v}",
        f"        run: python -m pip install ruff=={v}",
    ]))
    assert not any("stray version" in e for e in new_errors(pristine, repo))


def test_version_in_a_comment_without_a_pinned_sha_is_stray(pristine, repo):
    append(repo, ".github/workflows/ci.yml", "      - uses: actions/checkout@main  # v" + ".".join(["9"] * 3))
    assert_caught(pristine, repo, r"\(a\) stray version '9\.9\.9' in \.github/workflows/ci\.yml")


# ── (k) workflows ───────────────────────────────────────────────────────────

def test_unpinned_actions_job_secrets_and_soft_failures_are_caught(pristine, repo):
    wf = repo / ".github" / "workflows" / "zz-test.yml"
    wf.write_text("""name: t
on: workflow_dispatch
jobs:
  a:
    runs-on: ubuntu-latest
    continue-on-error: true
    env:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    steps:
      - uses: actions/checkout@v7
      - run: npm install -g @anthropic-ai/claude-code
""", encoding="utf-8")
    found = new_errors(pristine, repo)
    for pattern in (r"'actions/checkout@v7' is not pinned to a commit SHA", r"a secret is in the job env",
                    r"job 'a' has continue-on-error", r"install @anthropic-ai/claude-code at an exact version"):
        assert any(re.search(pattern, e) for e in found), (pattern, found)


def test_evals_workflow_defaults_to_the_documented_tags():
    flow = yaml.safe_load((ROOT / ".github/workflows/evals.yml").read_text(encoding="utf-8"))
    inputs = flow[True]["workflow_dispatch"]["inputs"]       # YAML 1.1 reads the key `on` as True
    assert inputs["tag"]["default"].split() == ["routing", "negative"]
    assert inputs["upload_results"]["default"] is False
    readme = (ROOT / "evals" / "README.md").read_text(encoding="utf-8")
    ci_lines = [line for line in readme.splitlines() if "claude plugin eval" in line and "# CI" in line]
    assert ci_lines, "evals/README.md has no `claude plugin eval ... # CI` command line"
    assert all("--tag routing --tag negative" in line for line in ci_lines), ci_lines


# ── (+) requirements.txt ────────────────────────────────────────────────────

def test_requirement_without_a_lower_bound_is_caught(pristine, repo):
    append(repo, "requirements.txt", "seaborn")
    assert_caught(pristine, repo, r"requirements\.txt:\d+ 'seaborn' needs a lower bound")


def test_requirement_with_an_environment_marker_is_accepted(pristine, repo):
    append(repo, "requirements.txt", "tomli>=2.0; python_version < '3.11'\nnumpy>=1.23,<3 ; sys_platform != 'win32'")
    assert not any("requirements.txt" in e for e in new_errors(pristine, repo))


def test_ci_minimum_versions_step_keeps_environment_markers(tmp_path):
    """tests-minimum-versions turns each `name>=X` into `name==X`; a marker must survive."""
    flow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    run = next(str(s["run"]) for s in flow["jobs"]["tests-minimum-versions"]["steps"]
               if "minimum.txt" in str(s.get("run", "")))
    cmd = re.search(r"^\s*(sed\b.*?requirements\.txt)\s*>", run, re.S | re.M).group(1)
    (tmp_path / "requirements.txt").write_text(
        "# comment\nscipy>=1.11  # why; because\nnumpy>=1.23,<3\ntomli>=2.0; python_version < '3.11'\n",
        encoding="utf-8")
    out = subprocess.run(["sh", "-c", cmd], cwd=tmp_path, capture_output=True, text=True, check=True).stdout
    assert out.splitlines() == ["scipy==1.11", "numpy==1.23", "tomli==2.0; python_version < '3.11'"]


def _lower_bounds():
    out = {}
    for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([A-Za-z0-9_.-]+)>=([\d.]+)", line.split("#", 1)[0].strip())
        if m:
            out[m.group(1).lower()] = tuple(int(x) for x in m.group(2).split("."))
    return out


def test_requirements_lower_bounds_cover_what_the_code_needs():
    bounds = _lower_bounds()
    assert set(bounds) >= {"scipy", "statsmodels", "matplotlib", "pandas", "numpy", "python-docx", "openpyxl",
                           "pyyaml"}
    # pub_style.save_figure needs matplotlib 3.6 (layout engines, draw_without_rendering)
    pub_style = (ROOT / "skills/figure-generation/scripts/pub_style.py").read_text(encoding="utf-8")
    m = re.search(r"MIN_MATPLOTLIB\s*=\s*\((\d+),\s*(\d+)\)", pub_style)
    assert bounds["matplotlib"] >= ((int(m.group(1)), int(m.group(2))) if m else (3, 6))
    # the method-card recipes call .confidence_interval() on ttest_ind results (SciPy 1.11)
    assert bounds["scipy"] >= (1, 11)


def test_skill_description_rules_are_enforced(pristine, repo):
    p = repo / "skills" / "figure-generation" / "SKILL.md"
    text = p.read_text(encoding="utf-8")
    p.write_text(re.sub(r"^description: Use when", "description: Helps with", text, count=1, flags=re.M),
                 encoding="utf-8")
    assert_caught(pristine, repo, r"\(f\) skills/figure-generation/SKILL\.md description must start with 'Use when'")


def test_non_executable_hook_is_caught(pristine, repo):
    hook = repo / "hooks" / "session-start.sh"
    hook.chmod(0o644)
    assert_caught(pristine, repo, r"hooks/session-start\.sh is not executable")
