#!/usr/bin/env python3
"""
Data cleaning helpers for statistical-analysis Step 2: missing-data overview,
outlier detection (Z-score / IQR / clinical range), type checks, and an auditable
data-cleaning-log.md (format: references/output-templates.md section 1).

Default behaviour is NON-destructive: without cleaning flags the script only reports,
writes data_clean.csv identical in rows to the input, and logs everything. Cleaning
actions (complete-case drop, winsorizing, recoding, dropping columns) run only when
requested — they must be pre-specified in analysis-plan.md Section 2.

Command line:
    python3 data_cleaning.py data.csv --out data_clean.csv --log data-cleaning-log.md \
        --continuous age,bmi,psa --categorical sex,stage --dates visit_date \
        --range age=0:120 bmi=10:80 --complete-case outcome --winsorize psa \
        --recode sex=Male:0,Female:1 --drop-cols free_text_notes

Library use (run from the user's project directory):
    import os, sys
    sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT", "."),
                                    "skills", "statistical-analysis", "scripts"))
    from data_cleaning import missing_summary, detect_outliers, check_types, apply_cleaning, write_cleaning_log
"""

import argparse
import datetime as _dt
import json
import os

try:
    import numpy as np
    import pandas as pd
except ImportError:  # pragma: no cover - depends on the user's environment
    raise SystemExit("缺少 pandas / numpy：pip install pandas numpy")


# ─── missing data ───────────────────────────────────────────────────────────

def suggest_missing_strategy(pct):
    """Map % missing of one variable to the default strategy (see SKILL.md Step 2.1)."""
    if pct == 0:
        return 'none'
    if pct < 5:
        return 'complete case (justify) or MI'
    if pct <= 20:
        return 'multiple imputation (m>=20, Rubin)'
    if pct <= 40:
        return 'multiple imputation + MNAR sensitivity analysis'
    return 'discuss whether to keep the variable (>40% missing)'


def missing_summary(df):
    """Per-variable missing count / % / suggested strategy. Rows with 0 missing are kept."""
    n = len(df)
    n_missing = df.isnull().sum()
    pct = (n_missing / n * 100).round(1) if n else n_missing.astype(float)
    out = pd.DataFrame({
        'variable': df.columns,
        'n_missing': n_missing.to_numpy().astype(int),
        'pct_missing': pct.to_numpy().astype(float),
    })
    out['suggested_strategy'] = [suggest_missing_strategy(p) for p in out['pct_missing']]
    return out.reset_index(drop=True)


# ─── outliers ───────────────────────────────────────────────────────────────

def parse_ranges(items):
    """['age=0:120', 'bmi=10:80'] -> {'age': (0.0, 120.0), 'bmi': (10.0, 80.0)}"""
    ranges = {}
    for item in items or []:
        try:
            col, bounds = item.split('=')
            lo, hi = bounds.split(':')
            ranges[col.strip()] = (float(lo), float(hi))
        except ValueError:
            raise ValueError(f"--range 格式应为 col=low:high，收到 {item!r}")
    return ranges


def detect_outliers(df, cols=None, z_thresh=3.0, iqr_k=1.5, clinical_ranges=None):
    """Count outliers per numeric column by Z-score, IQR and (optional) clinical range.

    Returns a DataFrame; nothing is modified. NaN are ignored in every rule.
    """
    clinical_ranges = clinical_ranges or {}
    if cols is None:
        cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    rows = []
    for col in cols:
        x = pd.to_numeric(df[col], errors='coerce').dropna().to_numpy(dtype=float)
        if len(x) == 0:
            rows.append({'variable': col, 'n': 0, 'n_z': 0, 'n_iqr': 0,
                         'iqr_low': np.nan, 'iqr_high': np.nan,
                         'n_out_of_range': 0, 'range': None})
            continue
        sd = x.std(ddof=1) if len(x) > 1 else 0.0
        n_z = int((np.abs((x - x.mean()) / sd) > z_thresh).sum()) if sd > 0 else 0
        q1, q3 = np.percentile(x, [25, 75])
        iqr = q3 - q1
        low, high = q1 - iqr_k * iqr, q3 + iqr_k * iqr
        n_iqr = int(((x < low) | (x > high)).sum())
        rng = clinical_ranges.get(col)
        n_range = int(((x < rng[0]) | (x > rng[1])).sum()) if rng else 0
        rows.append({'variable': col, 'n': int(len(x)), 'n_z': n_z, 'n_iqr': n_iqr,
                     'iqr_low': round(float(low), 3), 'iqr_high': round(float(high), 3),
                     'n_out_of_range': n_range,
                     'range': f"{rng[0]}-{rng[1]}" if rng else None})
    return pd.DataFrame(rows)


# ─── types ──────────────────────────────────────────────────────────────────

def check_types(df, continuous=None, categorical=None, dates=None, max_levels=20):
    """Return a list of type issues (dicts). Empty list = no problems found."""
    issues = []
    for col in continuous or []:
        if col not in df.columns:
            issues.append({'variable': col, 'issue': 'missing column', 'detail': '声明为连续变量但数据中不存在'})
            continue
        if not pd.api.types.is_numeric_dtype(df[col]):
            coerced = pd.to_numeric(df[col], errors='coerce')
            bad = df[col].notna() & coerced.isna()
            issues.append({'variable': col, 'issue': 'non-numeric continuous',
                           'detail': f"dtype={df[col].dtype}, {int(bad.sum())} 个值无法转为数字"
                                     f"（例：{df.loc[bad, col].astype(str).unique()[:5].tolist()}）"})
    for col in categorical or []:
        if col not in df.columns:
            issues.append({'variable': col, 'issue': 'missing column', 'detail': '声明为分类变量但数据中不存在'})
            continue
        levels = df[col].dropna().astype(str)
        n_levels = levels.nunique()
        if n_levels > max_levels:
            issues.append({'variable': col, 'issue': 'too many levels',
                           'detail': f'{n_levels} 个水平（>{max_levels}），确认是否真是分类变量'})
        stripped = levels.str.strip().str.lower()
        if stripped.nunique() != n_levels:
            issues.append({'variable': col, 'issue': 'inconsistent coding',
                           'detail': f'大小写/空格不一致：{sorted(levels.unique().tolist())[:10]}'})
    for col in dates or []:
        if col not in df.columns:
            issues.append({'variable': col, 'issue': 'missing column', 'detail': '声明为日期变量但数据中不存在'})
            continue
        parsed = pd.to_datetime(df[col], errors='coerce')
        bad = df[col].notna() & parsed.isna()
        if bad.any():
            issues.append({'variable': col, 'issue': 'unparseable dates',
                           'detail': f"{int(bad.sum())} 个值无法解析为日期"
                                     f"（例：{df.loc[bad, col].astype(str).unique()[:5].tolist()}）"})
    return issues


# ─── cleaning actions ───────────────────────────────────────────────────────

def parse_recode(items):
    """['sex=Male:0,Female:1'] -> {'sex': {'Male': '0', 'Female': '1'}}"""
    recode = {}
    for item in items or []:
        try:
            col, mapping = item.split('=', 1)
            pairs = [kv.split(':') for kv in mapping.split(',')]
            recode[col.strip()] = {k.strip(): v.strip() for k, v in pairs}
        except ValueError:
            raise ValueError(f"--recode 格式应为 col=old1:new1,old2:new2，收到 {item!r}")
    return recode


def apply_cleaning(df, complete_case=None, winsorize=None, drop_cols=None, recode=None,
                   dates=None, continuous=None, clinical_ranges=None, drop_out_of_range=False,
                   winsor_limits=(0.01, 0.99)):
    """Apply pre-specified cleaning steps; returns (df_clean, actions).

    actions is a list of dicts describing exactly what changed (for the log).
    """
    out = df.copy()
    actions = []
    for col in continuous or []:
        if col in out.columns and not pd.api.types.is_numeric_dtype(out[col]):
            before = out[col].notna().sum()
            out[col] = pd.to_numeric(out[col], errors='coerce')
            lost = int(before - out[col].notna().sum())
            actions.append({'step': 'type', 'variable': col, 'from': str(df[col].dtype),
                            'to': 'float64', 'note': f'非数字条目置为缺失 (N={lost})'})
    for col in dates or []:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors='coerce')
            actions.append({'step': 'type', 'variable': col, 'from': str(df[col].dtype),
                            'to': 'datetime64', 'note': '无法解析的日期置为缺失'})
    for col, mapping in (recode or {}).items():
        if col in out.columns:
            unmapped = set(out[col].dropna().astype(str).unique()) - set(mapping)
            out[col] = out[col].astype(str).where(out[col].notna()).map(mapping)
            actions.append({'step': 'recode', 'variable': col, 'from': json.dumps(list(mapping), ensure_ascii=False),
                            'to': json.dumps(list(mapping.values()), ensure_ascii=False),
                            'note': f'未在映射表中的值置为缺失：{sorted(unmapped)}' if unmapped else ''})
    for col in drop_cols or []:
        if col in out.columns:
            out = out.drop(columns=[col])
            actions.append({'step': 'drop_column', 'variable': col, 'from': '', 'to': '', 'note': '按 SAP 移除该变量'})
    if drop_out_of_range and clinical_ranges:
        for col, (lo, hi) in clinical_ranges.items():
            if col in out.columns:
                x = pd.to_numeric(out[col], errors='coerce')
                mask = (x < lo) | (x > hi)
                n_bad = int(mask.sum())
                out = out[~mask]
                actions.append({'step': 'drop_rows', 'variable': col, 'from': f'{lo}-{hi}', 'to': '',
                                'note': f'移除超出临床合理范围的记录 (N={n_bad})；须在敏感性分析中比较移除前后'})
    for col in winsorize or []:
        if col in out.columns:
            x = pd.to_numeric(out[col], errors='coerce')
            lo, hi = x.quantile(winsor_limits[0]), x.quantile(winsor_limits[1])
            n_changed = int(((x < lo) | (x > hi)).sum())
            out[col] = x.clip(lower=lo, upper=hi)
            actions.append({'step': 'winsorize', 'variable': col,
                            'from': f'P{int(winsor_limits[0]*100)}={lo:.4g}', 'to': f'P{int(winsor_limits[1]*100)}={hi:.4g}',
                            'note': f'截尾 {n_changed} 个值'})
    if complete_case:
        cols = [c for c in complete_case if c in out.columns]
        before = len(out)
        out = out.dropna(subset=cols)
        actions.append({'step': 'complete_case', 'variable': ','.join(cols), 'from': str(before), 'to': str(len(out)),
                        'note': f'完整病例分析：删除 {before - len(out)} 行（须在 SAP 中说明理由）'})
    return out.reset_index(drop=True), actions


# ─── log ────────────────────────────────────────────────────────────────────

def _md_table(headers, rows):
    lines = ['| ' + ' | '.join(headers) + ' |', '|' + '|'.join(['---'] * len(headers)) + '|']
    for r in rows:
        lines.append('| ' + ' | '.join('' if v is None else str(v) for v in r) + ' |')
    return '\n'.join(lines)


def write_cleaning_log(path, input_name, output_name, df_raw, df_clean, missing_df,
                       outlier_df, type_issues, actions, date=None):
    """Write data-cleaning-log.md following references/output-templates.md section 1."""
    date = date or _dt.date.today().isoformat()
    n0, n1 = len(df_raw), len(df_clean)
    removed = n0 - n1
    pct_removed = round(removed / n0 * 100, 1) if n0 else 0.0
    cc0 = int(df_raw.dropna().shape[0])
    cc1 = int(df_clean.dropna().shape[0])

    miss_rows = [(r.variable, r.n_missing, f'{r.pct_missing}%', r.suggested_strategy, '[填写理由]')
                 for r in missing_df.itertuples() if r.n_missing > 0]
    out_rows = []
    for r in outlier_df.itertuples():
        if not (r.n_z or r.n_iqr or r.n_out_of_range):
            continue
        has_range = isinstance(r.range, str)
        out_rows.append((r.variable,
                         f'Z>3: {r.n_z}; IQR: {r.n_iqr}' + (f'; range: {r.n_out_of_range}' if has_range else ''),
                         'Z / IQR' + (f' / clinical {r.range}' if has_range else ''),
                         'Retained (flagged)', '[填写理由]'))
    type_rows = [(a['variable'], a['from'], a['to'], a['note']) for a in actions if a['step'] == 'type']
    type_rows += [(i['variable'], i['issue'], '', i['detail']) for i in type_issues]
    recode_rows = [(a['variable'], a['from'], a['to'], a['note']) for a in actions if a['step'] == 'recode']
    other_rows = [(a['step'], a['variable'], a['from'], a['to'], a['note'])
                  for a in actions if a['step'] not in ('type', 'recode')]

    parts = [
        '# Data Cleaning Log', '',
        f'**Date:** {date}',
        f'**Input:** {input_name} (N={n0}, vars={df_raw.shape[1]})',
        f'**Output:** {output_name} (N={n1}, vars={df_clean.shape[1]})',
        f'**Records removed:** {removed} ({pct_removed}%)', '',
        '## Missing Data', '',
        _md_table(['Variable', 'N Missing', '% Missing', 'Strategy', 'Justification'], miss_rows)
        if miss_rows else '_No missing values._', '',
        '## Outliers', '',
        _md_table(['Variable', 'N Outliers', 'Method', 'Action', 'Justification'], out_rows)
        if out_rows else '_No outliers flagged by Z-score / IQR / clinical range._', '',
        '## Data Type Corrections', '',
        _md_table(['Variable', 'Original Type', 'Corrected Type', 'Notes'], type_rows)
        if type_rows else '_No type corrections._', '',
        '## Recoding', '',
        _md_table(['Variable', 'Original Coding', 'New Coding', 'Reason'], recode_rows)
        if recode_rows else '_No recoding._', '',
        '## Other Cleaning Actions', '',
        _md_table(['Step', 'Variable', 'From', 'To', 'Notes'], other_rows)
        if other_rows else '_No rows removed or values altered (non-destructive run)._', '',
        '## Before vs After Summary', '',
        _md_table(['Metric', 'Before', 'After'], [
            ('Total N', n0, n1),
            ('Complete cases', f'{cc0} ({round(cc0 / n0 * 100, 1) if n0 else 0}%)',
             f'{cc1} ({round(cc1 / n1 * 100, 1) if n1 else 0}%)'),
            ('Variables', df_raw.shape[1], df_clean.shape[1]),
        ]), '',
        '_Generated by data_cleaning.py — fill in the [Justification] cells; every action above '
        'must correspond to analysis-plan.md Section 2._', '',
    ]
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(parts))
    return path


# ─── CLI ────────────────────────────────────────────────────────────────────

def _split(s):
    return [x.strip() for x in s.split(',') if x.strip()] if s else []


def main(argv=None):
    p = argparse.ArgumentParser(description='Missing / outlier / type report + auditable cleaning log.')
    p.add_argument('csv', help='raw data file (never modified)')
    p.add_argument('--out', default='data_clean.csv')
    p.add_argument('--log', default='data-cleaning-log.md')
    p.add_argument('--continuous', default='', help='comma-separated continuous columns')
    p.add_argument('--categorical', default='', help='comma-separated categorical columns')
    p.add_argument('--dates', default='', help='comma-separated date columns')
    p.add_argument('--range', nargs='*', default=[], help='clinical ranges, e.g. age=0:120 bmi=10:80')
    p.add_argument('--z', type=float, default=3.0, help='Z-score threshold')
    p.add_argument('--iqr', type=float, default=1.5, help='IQR multiplier')
    p.add_argument('--complete-case', default='', help='drop rows missing any of these columns')
    p.add_argument('--winsorize', default='', help='winsorize these columns to P1/P99')
    p.add_argument('--drop-cols', default='', help='drop these columns')
    p.add_argument('--drop-out-of-range', action='store_true', help='drop rows outside --range')
    p.add_argument('--recode', nargs='*', default=[], help='e.g. sex=Male:0,Female:1')
    p.add_argument('--sep', default=',')
    args = p.parse_args(argv)

    if not os.path.exists(args.csv):
        raise SystemExit(f"找不到数据文件 {args.csv}（当前目录 {os.getcwd()}）")
    if os.path.abspath(args.csv) == os.path.abspath(args.out):
        raise SystemExit("输出文件不能覆盖原始数据文件：原始 data.csv 必须保留，清洗结果另存")
    df = pd.read_csv(args.csv, sep=args.sep)
    try:
        ranges = parse_ranges(args.range)
        recode = parse_recode(args.recode)
    except ValueError as e:
        raise SystemExit(f"参数错误：{e}")
    continuous, categorical, dates = _split(args.continuous), _split(args.categorical), _split(args.dates)

    missing_df = missing_summary(df)
    type_issues = check_types(df, continuous, categorical, dates)
    df_clean, actions = apply_cleaning(
        df, complete_case=_split(args.complete_case), winsorize=_split(args.winsorize),
        drop_cols=_split(args.drop_cols), recode=recode, dates=dates, continuous=continuous,
        clinical_ranges=ranges, drop_out_of_range=args.drop_out_of_range)
    outlier_df = detect_outliers(df_clean, cols=continuous or None, z_thresh=args.z, iqr_k=args.iqr,
                                 clinical_ranges=ranges)
    df_clean.to_csv(args.out, index=False)
    write_cleaning_log(args.log, os.path.basename(args.csv), os.path.basename(args.out),
                       df, df_clean, missing_df, outlier_df, type_issues, actions)

    print(f"[Cleaning] Original N={len(df)}, Clean N={len(df_clean)}, Removed={len(df) - len(df_clean)}")
    flagged = missing_df[missing_df.n_missing > 0]
    if len(flagged):
        print("[Cleaning] Missing data summary:")
        print(flagged.to_string(index=False))
    out_flag = outlier_df[(outlier_df.n_z > 0) | (outlier_df.n_iqr > 0) | (outlier_df.n_out_of_range > 0)]
    if len(out_flag):
        print("[Cleaning] Outliers flagged (retained unless an action was requested):")
        print(out_flag.to_string(index=False))
    for issue in type_issues:
        print(f"[Cleaning] TYPE ISSUE {issue['variable']}: {issue['issue']} — {issue['detail']}")
    print(f"[Cleaning] Wrote {args.out} and {args.log}")
    return df_clean


if __name__ == '__main__':
    main()
