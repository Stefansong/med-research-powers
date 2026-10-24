#!/usr/bin/env python3
"""
Randomisation lists for RCTs: simple, permuted-block, and stratified (block within stratum).
The allocation table is written to CSV plus a JSON summary that records the seed, so the same
list can be regenerated later.

Who runs it, and where (allocation concealment)
    The person responsible for allocation -- an independent statistician or the trial office,
    nobody who recruits, treats or assesses participants -- runs this script and writes the list
    into a folder that only they control, OUTSIDE the shared project folder (not tools/, not any
    folder below one that holds .mrp-state.json, study-protocol.md or analysis-plan.md: the
    script refuses such a path -- a new project may not have .mrp-state.json yet). Recruiters and
    data collectors get only the allocation mechanism (sequentially numbered opaque sealed
    envelopes, or a central telephone / web system), never the list, its summary JSON (seed, block
    sizes) or the command that made it -- so the command does not go into tools/README.md or CRF
    guides either. Do NOT write the seed or the block sizes into study-protocol.md, which the
    recruiting team reads: the protocol states only the method (e.g. "permuted blocks of varying
    size, stratified by centre") and who holds the list (SPIRIT 2025 / CONSORT 2025 items on
    sequence generation and allocation concealment).

Command line (run by the allocation holder; --out is required and lies outside the project):
    python3 randomization.py --n 120 --arms Control,Treatment --method block --block-sizes 4,6 \
        --out ~/trial-allocation/allocation.csv
    python3 randomization.py --method stratified --n-per-stratum 40 --strata site=A,B,C sex=M,F \
        --arms A,B --ratio 1:1 --block-sizes 4,6 --out ~/trial-allocation/allocation.csv
    python3 randomization.py --n 60 --arms A,B,C --ratio 1:1:2 --method simple \
        --out ~/trial-allocation/simple.csv

What it writes
    <out>                allocation_id, stratum, sequence, block, arm
    <out>_summary.json   seed (as a number and as the string seed_str), method, arms, ratio, block
                         sizes, strata, counts per arm and stratum, warnings, Python / numpy /
                         pandas versions, sha256 of this script, the command that regenerates the list
    Both files are created with owner-only permissions (0600, where the OS supports it). An
    existing list or summary is never replaced unless --force is given. --strata and
    --n-per-stratum only go with --method stratified, --n and --block-sizes only with the methods
    that use them; a factor named twice, an empty --ratio or --block-sizes, and a '|' in a factor
    or level name are errors. Exit status 0 = written; 2 = invalid arguments, a refused output
    path or a write error (one line on stderr, no traceback).

Seed: leave --seed out. The script then draws an unpredictable seed (Python `secrets`) and
records it in the summary JSON. A memorable seed (42, 123, the study date) lets anyone who
guesses it rebuild the list. Pass --seed only to regenerate an existing list.

Regenerating a list
    Take `seed_str` from the summary, not the number `seed`: JavaScript, jq and spreadsheets read
    JSON numbers as doubles and lose digits of a 63-bit seed. Use the same arguments (the
    summary's `regenerate` field holds the command), the same script (`script_sha256`) and the
    same numpy version (`software`): numpy does not promise the same Generator stream in every
    release (NEP 19), so keep a copy of this script with the list.
    What changes a list: every stratum has its own random stream, keyed by its factor=level
    pairs (not by its position, and not by the order of the factors). The stratum label lists
    the factors in alphabetical order of their names ("sex=M|site=A" whatever the order given
    in --strata), so reordering the factors changes nothing at all. Adding a level (a new
    centre) or reordering the levels leaves the stratum labels and arms of the existing strata
    unchanged; only the allocation_id numbers S01, S02 ... follow the order of the strata, so
    compare old and new lists by stratum + sequence, not by allocation_id. Adding a new factor
    creates new strata, so every list changes.
    Changing a stratum's n, the block sizes, the ratio or the arms changes that stratum's whole
    list, not just its end: to extend a list already in use, generate an additional list for the
    extra participants with a new seed instead of regenerating the old one. Stratified lists made
    with an earlier version of this script (streams keyed by stratum position, no script_sha256 in
    the summary) can only be regenerated with that earlier script.

Library use (code never imports this from the plugin install path): copy the file first into
the folder of the code that imports it -- the allocation holder's own folder outside the project,
like the list itself; it reads nothing else from the plugin, and the copy is also the copy of the
script to keep with the list:
    cp "$CLAUDE_PLUGIN_ROOT/skills/data-collection-tools/scripts/randomization.py" ~/trial-allocation/
    # in a script in ~/trial-allocation/:
    from randomization import simple_randomization, block_randomization, stratified_randomization
"""

import argparse
import hashlib
import itertools
import json
import os
import platform
import secrets
import shlex
import sys

try:
    import numpy as np
    import pandas as pd
except ImportError:  # pragma: no cover - depends on the user's environment
    print("缺少 pandas / numpy：pip install pandas numpy", file=sys.stderr)
    raise SystemExit(2)


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


def new_seed():
    """An unpredictable seed (not guessable like 42) -- record it in the concealed summary."""
    return secrets.randbits(63)


def _rng(seed):
    if seed is None:
        raise ValueError("需要 seed：用 new_seed() 生成一个不可预测的种子，并与分配表一起保密保存")
    if isinstance(seed, (int, np.integer)) and seed < 0:
        raise ValueError(f"seed 必须是非负整数，收到 {seed}")
    return np.random.default_rng(seed)


def _fillable(n, block_sizes):
    """fillable[r]: r allocations can be made of whole blocks of the given sizes."""
    fillable = [True] + [False] * n
    for r in range(1, n + 1):
        fillable[r] = any(b <= r and fillable[r - b] for b in block_sizes)
    return fillable


def _stratum_key(factors, combo):
    """Random-stream key of one stratum: a hash of its factor=level pairs in factor-name order, so
    neither its position nor the order of the factors matters (adding a centre or reordering the
    factors leaves the other strata's lists as they were). Used as the SeedSequence spawn_key,
    the same mechanism as SeedSequence.spawn(), so the streams stay independent."""
    pairs = sorted([str(f), str(v)] for f, v in zip(factors, combo))
    digest = hashlib.sha256(json.dumps(pairs, ensure_ascii=False).encode('utf-8')).digest()
    return tuple(int.from_bytes(digest[i:i + 4], 'big') for i in range(0, 16, 4))


def _to_records(seq, blocks=None, stratum=None, prefix=''):
    rows = []
    for i, arm in enumerate(seq, start=1):
        rows.append({'allocation_id': f'{prefix}{i:04d}', 'stratum': stratum or 'all',
                     'sequence': i, 'block': blocks[i - 1] if blocks is not None else None, 'arm': arm})
    return rows


# ─── methods ────────────────────────────────────────────────────────────────

def simple_randomization(n, arms=('A', 'B'), ratio=None, seed=None):
    """Independent draws with probabilities proportional to ratio. Group sizes vary by chance."""
    arms, ratio = _check_arms_ratio(arms, ratio)
    if n < 1:
        raise ValueError("n 必须 >= 1")
    rng = _rng(seed)
    probs = np.array(ratio, dtype=float) / sum(ratio)
    seq = rng.choice(arms, size=n, p=probs).tolist()
    return pd.DataFrame(_to_records(seq))


def block_randomization(n, arms=('A', 'B'), ratio=None, block_sizes=(4, 6), seed=None):
    """Random permuted blocks; block size drawn at random from block_sizes (each a multiple
    of sum(ratio)) so the next allocation cannot be predicted from the block boundary."""
    arms, ratio = _check_arms_ratio(arms, ratio)
    if n < 1:
        raise ValueError("n 必须 >= 1")
    unit = sum(ratio)
    block_sizes = [int(b) for b in block_sizes]
    if not block_sizes:
        raise ValueError("至少需要一个区组大小，如 4,6")
    bad = [b for b in block_sizes if b <= 0 or b % unit != 0]
    if bad:
        raise ValueError(f"区组大小 {bad} 不是分配比总和 {unit} 的倍数（ratio={ratio}）")
    rng = _rng(seed)
    # Block sizes are drawn only among those that keep the rest fillable, so the list ends on a
    # complete block (exact balance) whenever n allows it; otherwise the last block is cut and the
    # imbalance is at most one block.
    fillable = _fillable(n, block_sizes)
    seq, blocks, b_id = [], [], 0
    while len(seq) < n:
        b_id += 1
        rest = n - len(seq)
        fits = [b for b in block_sizes if b <= rest and fillable[rest - b]]
        size = int(rng.choice(fits if (fits and fillable[rest]) else block_sizes))
        block = []
        for arm, r in zip(arms, ratio):
            block += [arm] * (r * size // unit)
        rng.shuffle(block)
        seq += block
        blocks += [b_id] * size
    return pd.DataFrame(_to_records(seq[:n], blocks[:n]))


def stratified_randomization(n_per_stratum, strata, arms=('A', 'B'), ratio=None,
                             block_sizes=(4, 6), seed=None):
    """Permuted-block list inside every stratum combination.

    strata: {'site': ['A', 'B'], 'sex': ['M', 'F']} -> 4 strata, each with its own list, labelled
    with the factors in alphabetical order of their names ('sex=M|site=A').
    n_per_stratum: int (same for all) or {stratum_label: n} (factors in the label in any order).
    Every stratum gets an independent random stream derived from the one seed (not seed + i,
    which made stratum 2 of seed 42 identical to stratum 1 of seed 43), keyed by the stratum's
    factor=level pairs rather than its position: adding a level or reordering the factors does
    not change the lists of the strata that were already there.
    """
    if not strata:
        raise ValueError("分层随机需要至少一个分层因素，例如 {'site': ['A', 'B']}")
    for f, levels in strata.items():
        if not levels:
            raise ValueError(f"分层因素 {f!r} 没有水平")
        if len(set(levels)) != len(levels):
            raise ValueError(f"分层因素 {f!r} 的水平有重复：{levels}")
        bad = [str(x) for x in [f, *levels] if '|' in str(x)] + ([str(f)] if '=' in str(f) else [])
        if bad:
            raise ValueError(f"分层因素名和水平里不能有 '|'，因素名里不能有 '='（分层标签用它们分隔）：{bad}")
    _rng(seed)                                       # same seed checks as the other methods
    factors = sorted(strata, key=str)                # labels and order do not depend on the factor order given
    combos = list(itertools.product(*[strata[f] for f in factors]))
    labels = ['|'.join(f'{f}={v}' for f, v in zip(factors, combo)) for combo in combos]
    if isinstance(n_per_stratum, dict):
        given = {frozenset(str(k).split('|')): v for k, v in n_per_stratum.items()}
        missing = [lab for lab in labels if frozenset(lab.split('|')) not in given]
        if missing:
            raise ValueError(f"n_per_stratum 缺少这些分层的样本量：{missing}")
    frames = []
    for i, (combo, label) in enumerate(zip(combos, labels)):
        n = given[frozenset(label.split('|'))] if isinstance(n_per_stratum, dict) else int(n_per_stratum)
        stream = np.random.SeedSequence(seed, spawn_key=_stratum_key(factors, combo))
        df = block_randomization(n, arms, ratio, block_sizes, seed=stream)
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

CONCEALMENT_REMINDER = ('[Randomization] Allocation concealment: keep the list and its summary outside the shared '
                        'project folder, held by someone independent of enrolment; recruiters get only sealed '
                        'envelopes / the central system, never the list, the seed, the block sizes or this command.')


def _fail(msg):
    """CLI error: one line on stderr, exit status 2 (never a traceback)."""
    print(str(msg).replace('\r', ' ').replace('\n', ' '), file=sys.stderr)
    raise SystemExit(2)


class _Parser(argparse.ArgumentParser):
    def error(self, message):            # one line on stderr, exit 2 (argparse prints a usage block)
        _fail(f"参数错误：{message}（用 --help 查看用法）")


def _parse_strata(items):
    strata = {}
    for item in items or []:
        name, sep, levels = item.partition('=')
        name = name.strip()
        if not sep or not name or '=' in levels:
            raise ValueError(f"--strata 格式应为 factor=level1,level2，收到 {item!r}")
        if name in strata:
            raise ValueError(f"分层因素 {name!r} 在 --strata 里出现了两次；同一因素的水平写在一起，如 {name}=A,B,C")
        strata[name] = [x.strip() for x in levels.split(',') if x.strip()]
    return strata


# Files that mark an MRP project folder. .mrp-state.json alone is not enough: a project whose skills
# were called directly may not have it yet when the tools are made (data-collection-tools Step 4),
# but study-protocol.md and analysis-plan.md are its prerequisites.
PROJECT_MARKERS = ('.mrp-state.json', 'study-protocol.md', 'analysis-plan.md')


def _project_folder(path):
    """(folder, marker file) of the MRP project folder that contains `path`, or (None, None)."""
    d = os.path.dirname(os.path.realpath(path))
    while True:
        for marker in PROJECT_MARKERS:
            if os.path.lexists(os.path.join(d, marker)):
                return d, marker
        parent = os.path.dirname(d)
        if parent == d:
            return None, None
        d = parent


def _check_out(out, force):
    """Refuse an output path inside the shared project folder, a directory, a symlink, or (without
    --force) an existing list or summary. Returns the summary path."""
    summary_path = os.path.splitext(out)[0] + '_summary.json'
    project, marker = _project_folder(out)
    if project is not None:
        _fail(f"--out {out} 在项目文件夹 {project} 里（那里有 {marker}，研究团队都能看到）：分配表和种子"
              "要由负责分配的人（独立统计师 / 试验办公室）保存在项目文件夹以外、只有他能访问的位置")
    if os.path.isdir(out):
        _fail(f"--out {out} 是一个目录；请给分配表的文件名，如 {os.path.join(out, 'allocation.csv')}")
    links = [x for x in (out, summary_path) if os.path.islink(x)]
    if links:
        _fail(f"{' 和 '.join(links)} 是符号链接：为免把分配表写到别处，不跟随符号链接；请给一个普通文件路径")
    existing = [x for x in (out, summary_path) if os.path.lexists(x)]
    if existing and not force:
        _fail(f"{' 和 '.join(existing)} 已存在：为免覆盖已有的分配表和唯一的种子记录，请换一个 --out；"
              "确认要替换时加 --force")
    return summary_path


def _write_private(path, text, force):
    """Create `path` with owner-only permissions (0600 where the OS supports it). Without force an
    existing file is never replaced (O_EXCL); a symlink is never followed (O_NOFOLLOW)."""
    flags = os.O_WRONLY | os.O_CREAT | (os.O_TRUNC if force else os.O_EXCL) | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
        f.write(text)
    try:
        os.chmod(path, 0o600)                        # a replaced file (--force) keeps its old mode otherwise
    except OSError:                                  # pragma: no cover - file systems without modes
        pass


def _script_sha256():
    with open(os.path.abspath(__file__), 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def _regenerate_command(args, arms, ratio, block_sizes, strata, seed):
    cmd = ['python3', 'randomization.py', '--method', args.method]
    if args.method == 'stratified':
        cmd += ['--n-per-stratum', str(args.n_per_stratum), '--strata']
        cmd += [f"{f}={','.join(levels)}" for f, levels in strata.items()]
    else:
        cmd += ['--n', str(args.n)]
    cmd += ['--arms', ','.join(arms)]
    if ratio:
        cmd += ['--ratio', ':'.join(str(r) for r in ratio)]
    if args.method != 'simple':
        cmd += ['--block-sizes', ','.join(str(b) for b in block_sizes)]
    return shlex.join(cmd + ['--seed', str(seed), '--out', 'regenerated.csv'])


def main(argv=None):
    p = _Parser(description='Reproducible randomisation list (simple / block / stratified). Run by the person '
                            'responsible for allocation; --out must lie outside the shared project folder.')
    p.add_argument('--method', choices=['simple', 'block', 'stratified'], default='block')
    p.add_argument('--n', type=int, default=None, help='total sample size (simple / block)')
    p.add_argument('--n-per-stratum', type=int, default=None, help='sample size per stratum (stratified only)')
    p.add_argument('--arms', default='A,B', help='comma-separated arm names')
    p.add_argument('--ratio', default=None, help='allocation ratio, e.g. 1:1 or 1:1:2')
    p.add_argument('--block-sizes', default=None,
                   help='comma-separated permuted block sizes (block / stratified; default 4,6)')
    p.add_argument('--strata', nargs='*', default=None,
                   help='stratified only, e.g. site=A,B,C sex=M,F (stratum labels list the factors alphabetically)')
    p.add_argument('--seed', type=int, default=None,
                   help='only to regenerate an existing list (use seed_str from its summary); by default an '
                        'unpredictable seed is drawn and recorded in the (concealed) summary JSON')
    p.add_argument('--out', required=True,
                   help='allocation CSV, in a folder only the allocation holder can read, outside the project '
                        'folder; <out>_summary.json is written next to it')
    p.add_argument('--force', action='store_true', help='replace an existing list and its summary')
    args = p.parse_args(argv)

    arms = [a.strip() for a in args.arms.split(',') if a.strip()]
    stratified = args.method == 'stratified'
    try:
        try:                                         # an empty --ratio "" is an error, not the default
            ratio = [int(x) for x in args.ratio.split(':')] if args.ratio is not None else None
        except ValueError:
            raise ValueError(f"--ratio 应为整数比，如 1:1 或 1:2，收到 {args.ratio!r}")
        if args.method == 'simple' and args.block_sizes is not None:
            raise ValueError("--block-sizes 只用于 --method block / stratified；简单随机没有区组")
        try:
            block_sizes = [int(x) for x in (args.block_sizes if args.block_sizes is not None else '4,6').split(',')
                           if x.strip()]
        except ValueError:
            raise ValueError(f"--block-sizes 应为逗号分隔的整数，如 4,6，收到 {args.block_sizes!r}")
        if not block_sizes:
            raise ValueError(f"--block-sizes 至少要有一个区组大小，如 4,6，收到 {args.block_sizes!r}")
        if not stratified and (args.strata is not None or args.n_per_stratum is not None):
            raise ValueError(f"--strata / --n-per-stratum 只用于 --method stratified（现在是 {args.method}）；"
                             "要分层随机请加 --method stratified")
        if stratified:
            if args.n is not None:
                raise ValueError("--method stratified 用 --n-per-stratum（每层例数），不用 --n")
            if args.n_per_stratum is None:
                raise ValueError("分层随机需要 --n-per-stratum")
            strata = _parse_strata(args.strata)
        else:
            if args.n is None:
                raise ValueError("需要 --n（总样本量）")
            strata = None
        if args.seed is not None and args.seed < 0:
            raise ValueError(f"--seed 必须是非负整数，收到 {args.seed}")
    except ValueError as e:
        _fail(f"参数错误：{e}")
    summary_path = _check_out(args.out, args.force)

    seed = args.seed if args.seed is not None else new_seed()
    try:
        if stratified:
            table = stratified_randomization(args.n_per_stratum, strata, arms, ratio, block_sizes, seed)
        elif args.method == 'simple':
            table = simple_randomization(args.n, arms, ratio, seed)
        else:
            table = block_randomization(args.n, arms, ratio, block_sizes, seed)
    except ValueError as e:
        _fail(f"参数错误：{e}")

    warnings = []
    n_each = args.n_per_stratum if stratified else args.n
    if args.method != 'simple' and not _fillable(n_each, block_sizes)[n_each]:
        warnings.append(f"{'每层 ' if stratified else ''}{n_each} 例不能由所给的区组大小正好拼成：最后一个区组被截断，"
                        "各组人数可能略偏离分配比（见 allocation）")
    summary = {'method': args.method, 'seed': seed, 'seed_str': str(seed),
               'seed_source': 'given with --seed' if args.seed is not None else 'drawn with secrets (unpredictable)',
               'arms': arms, 'ratio': ratio or [1] * len(arms),
               'block_sizes': block_sizes if args.method != 'simple' else None,
               'strata': strata,
               'allocation': allocation_summary(table),
               'warnings': warnings,
               'software': {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__,
                            'script_sha256': _script_sha256()},
               'regenerate': _regenerate_command(args, arms, ratio, block_sizes, strata, seed),
               'regenerate_note': '重新生成时用 seed_str（JavaScript / jq / 表格软件按双精度读数字，seed 会丢位数）、'
                                  'regenerate 里的参数、同一份脚本（script_sha256）和同一 numpy 版本。'
                                  '分层标签按因素名的字母顺序写，调换 --strata 里因素的顺序什么都不变；新增某因素的水平（如新中心）'
                                  '或调换水平顺序不改变已有各层的标签和分配（allocation_id 编号可能变，按 stratum + sequence '
                                  '对照，不按 allocation_id）；改某层的例数、区组大小、分配比或组别会改变该层的整张表——'
                                  '扩大正在使用的表时另用新种子生成追加的表，不要重新生成旧表。',
               'concealment_note': '此分配表和本文件（含种子、区组大小）须由与入组无关的人员（独立统计师 / 试验办公室）'
                                   '保存在项目文件夹以外、只有他能访问的位置；招募者只拿到分配机制（按序编号的不透明密封信封 / '
                                   '中央随机系统），拿不到分配表、种子、区组大小和生成命令。生成命令不写进 tools/README.md 或 '
                                   'CRF 指南，种子和区组大小也不要写进 study-protocol.md；方案里只写方法（如"按中心分层、'
                                   '大小可变的置换区组"）和由谁保管。'}

    out_dir = os.path.dirname(os.path.abspath(args.out))
    try:
        os.makedirs(out_dir, mode=0o700, exist_ok=True)
        _write_private(args.out, table.to_csv(index=False), args.force)
    except OSError as e:
        _fail(f"无法写入 {args.out}：{e.strerror or e}")
    try:
        _write_private(summary_path, json.dumps(summary, ensure_ascii=False, indent=2) + '\n', args.force)
    except OSError as e:
        try:
            os.remove(args.out)                      # never leave a list without its seed record
        except OSError:
            pass
        _fail(f"无法写入 {summary_path}：{e.strerror or e}（分配表也没有保留）")
    for w in warnings:
        print(f"[Randomization] 警告：{w}", file=sys.stderr)
    print(f"[Randomization] {len(table)} allocations written to {args.out} + {os.path.basename(summary_path)} "
          f"(seed inside; owner-only permissions).")
    print(CONCEALMENT_REMINDER)
    return table, summary


if __name__ == '__main__':
    main()
