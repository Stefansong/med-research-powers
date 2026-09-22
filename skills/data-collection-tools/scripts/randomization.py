#!/usr/bin/env python3
"""
Randomisation lists for RCTs: simple, permuted-block, and stratified (block within stratum).
Fixed seed -> reproducible; the allocation table is written to CSV plus a JSON summary.

Command line (from the project directory):
    python3 randomization.py --n 120 --arms Control,Treatment --method block --block-sizes 4,6 --seed 42 \
        --out tools/allocation.csv
    python3 randomization.py --method stratified --n-per-stratum 40 --strata site=A,B,C sex=M,F \
        --arms A,B --ratio 1:1 --block-sizes 4,6 --seed 42 --out tools/allocation.csv
    python3 randomization.py --n 60 --arms A,B,C --ratio 1:1:2 --method simple --seed 7

Allocation concealment: the generated list must be held by someone independent of
enrolment (e.g. sealed envelopes / central web system). Do NOT hand this file to the
person recruiting participants. Record the seed and block sizes in study-protocol.md
(CONSORT 2025 items on sequence generation, allocation concealment, implementation).

Library use:
    import os, sys
    sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT", "."),
                                    "skills", "data-collection-tools", "scripts"))
    from randomization import simple_randomization, block_randomization, stratified_randomization
"""

import argparse
import itertools
import json
import os

try:
    import numpy as np
    import pandas as pd
except ImportError:  # pragma: no cover - depends on the user's environment
    raise SystemExit("缺少 pandas / numpy：pip install pandas numpy")


# ─── helpers ────────────────────────────────────────────────────────────────

def _check_arms_ratio(arms, ratio):
    arms = list(arms)
    if len(arms) < 2:
        raise ValueError("至少需要 2 个组（arms）")
    if len(set(arms)) != len(arms):
        raise ValueError(f"组名重复：{arms}")
    if ratio is None:
        ratio = [1] * len(arms)
    ratio = [int(r) for r in ratio]
    if len(ratio) != len(arms) or any(r <= 0 for r in ratio):
        raise ValueError(f"ratio 必须与组数相同且均为正整数，收到 arms={arms}, ratio={ratio}")
    return arms, ratio


def _to_records(seq, blocks=None, stratum=None, prefix=''):
    rows = []
    for i, arm in enumerate(seq, start=1):
        rows.append({'allocation_id': f'{prefix}{i:04d}', 'stratum': stratum or 'all',
                     'sequence': i, 'block': blocks[i - 1] if blocks is not None else None, 'arm': arm})
    return rows


# ─── methods ────────────────────────────────────────────────────────────────

def simple_randomization(n, arms=('A', 'B'), ratio=None, seed=42):
    """Independent draws with probabilities proportional to ratio. Group sizes vary by chance."""
    arms, ratio = _check_arms_ratio(arms, ratio)
    if n < 1:
        raise ValueError("n 必须 >= 1")
    rng = np.random.default_rng(seed)
    probs = np.array(ratio, dtype=float) / sum(ratio)
    seq = rng.choice(arms, size=n, p=probs).tolist()
    return pd.DataFrame(_to_records(seq))


def block_randomization(n, arms=('A', 'B'), ratio=None, block_sizes=(4, 6), seed=42):
    """Random permuted blocks; block size drawn at random from block_sizes (each a multiple
    of sum(ratio)) so the next allocation cannot be predicted from the block boundary."""
    arms, ratio = _check_arms_ratio(arms, ratio)
    if n < 1:
        raise ValueError("n 必须 >= 1")
    unit = sum(ratio)
    block_sizes = [int(b) for b in block_sizes]
    bad = [b for b in block_sizes if b <= 0 or b % unit != 0]
    if bad:
        raise ValueError(f"区组大小 {bad} 不是分配比总和 {unit} 的倍数（ratio={ratio}）")
    rng = np.random.default_rng(seed)
    seq, blocks, b_id = [], [], 0
    while len(seq) < n:
        b_id += 1
        size = int(rng.choice(block_sizes))
        block = []
        for arm, r in zip(arms, ratio):
            block += [arm] * (r * size // unit)
        rng.shuffle(block)
        seq += block
        blocks += [b_id] * size
    return pd.DataFrame(_to_records(seq[:n], blocks[:n]))


def stratified_randomization(n_per_stratum, strata, arms=('A', 'B'), ratio=None,
                             block_sizes=(4, 6), seed=42):
    """Permuted-block list inside every stratum combination.

    strata: {'site': ['A', 'B'], 'sex': ['M', 'F']} -> 4 strata, each with its own list.
    n_per_stratum: int (same for all) or {stratum_label: n}.
    """
    if not strata:
        raise ValueError("分层随机需要至少一个分层因素，例如 {'site': ['A', 'B']}")
    factors = list(strata)
    combos = list(itertools.product(*[strata[f] for f in factors]))
    frames = []
    for i, combo in enumerate(combos):
        label = '|'.join(f'{f}={v}' for f, v in zip(factors, combo))
        n = n_per_stratum[label] if isinstance(n_per_stratum, dict) else int(n_per_stratum)
        df = block_randomization(n, arms, ratio, block_sizes, seed=seed + i)
        df['stratum'] = label
        df['allocation_id'] = [f'S{i + 1:02d}-{k:04d}' for k in df['sequence']]
        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    return out[['allocation_id', 'stratum', 'sequence', 'block', 'arm']]


def allocation_summary(table):
    """Counts per arm overall and per stratum."""
    overall = {str(k): int(v) for k, v in table['arm'].value_counts().sort_index().items()}
    per_stratum = {}
    for s, grp in table.groupby('stratum'):
        per_stratum[str(s)] = {str(k): int(v) for k, v in grp['arm'].value_counts().sort_index().items()}
    return {'n_total': int(len(table)), 'per_arm': overall, 'per_stratum': per_stratum}


# ─── CLI ────────────────────────────────────────────────────────────────────

def _parse_strata(items):
    strata = {}
    for item in items or []:
        try:
            name, levels = item.split('=')
        except ValueError:
            raise ValueError(f"--strata 格式应为 factor=level1,level2，收到 {item!r}")
        strata[name.strip()] = [x.strip() for x in levels.split(',') if x.strip()]
    return strata


def main(argv=None):
    p = argparse.ArgumentParser(description='Reproducible randomisation list (simple / block / stratified).')
    p.add_argument('--method', choices=['simple', 'block', 'stratified'], default='block')
    p.add_argument('--n', type=int, default=None, help='total sample size (simple / block)')
    p.add_argument('--n-per-stratum', type=int, default=None, help='sample size per stratum (stratified)')
    p.add_argument('--arms', default='A,B', help='comma-separated arm names')
    p.add_argument('--ratio', default=None, help='allocation ratio, e.g. 1:1 or 1:1:2')
    p.add_argument('--block-sizes', default='4,6', help='comma-separated permuted block sizes')
    p.add_argument('--strata', nargs='*', default=[], help='e.g. site=A,B,C sex=M,F')
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--out', default='allocation.csv')
    args = p.parse_args(argv)

    arms = [a.strip() for a in args.arms.split(',') if a.strip()]
    ratio = [int(x) for x in args.ratio.split(':')] if args.ratio else None
    block_sizes = [int(x) for x in args.block_sizes.split(',') if x.strip()]
    try:
        if args.method == 'stratified':
            if args.n_per_stratum is None:
                raise ValueError("分层随机需要 --n-per-stratum")
            table = stratified_randomization(args.n_per_stratum, _parse_strata(args.strata), arms, ratio,
                                             block_sizes, args.seed)
        else:
            if args.n is None:
                raise ValueError("需要 --n（总样本量）")
            if args.method == 'simple':
                table = simple_randomization(args.n, arms, ratio, args.seed)
            else:
                table = block_randomization(args.n, arms, ratio, block_sizes, args.seed)
    except ValueError as e:
        raise SystemExit(f"参数错误：{e}")

    out_dir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(out_dir, exist_ok=True)
    table.to_csv(args.out, index=False)
    summary = {'method': args.method, 'seed': args.seed, 'arms': arms, 'ratio': ratio or [1] * len(arms),
               'block_sizes': block_sizes if args.method != 'simple' else None,
               'strata': _parse_strata(args.strata) if args.method == 'stratified' else None,
               'allocation': allocation_summary(table),
               'concealment_note': '此分配表须由与入组无关的人员保管（信封/中央随机系统），不得交给招募者。'}
    with open(os.path.splitext(args.out)[0] + '_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"[Randomization] wrote {args.out} (+ _summary.json)")
    return table, summary


if __name__ == '__main__':
    main()
