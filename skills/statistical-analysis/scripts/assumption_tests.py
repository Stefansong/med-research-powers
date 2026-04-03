"""
Statistical assumption tests and method selection for medical research.
Usage: from assumption_tests import check_normality, check_homogeneity, choose_test, full_check
"""

from scipy import stats
import numpy as np

def check_normality(data, alpha=0.05):
    """Test normality. Auto-selects Shapiro-Wilk (n<50) or D'Agostino-Pearson."""
    data = np.array(data)
    data = data[~np.isnan(data)]
    n = len(data)
    if n < 8:
        return {'method': 'too_few_samples', 'n': n, 'is_normal': None,
                'recommendation': 'Non-parametric (n<8, normality untestable)'}
    if n < 50:
        stat, p = stats.shapiro(data)
        method = 'Shapiro-Wilk'
    else:
        stat, p = stats.normaltest(data)
        method = "D'Agostino-Pearson"
    return {
        'method': method, 'statistic': round(stat, 4), 'p_value': round(p, 4),
        'n': n, 'is_normal': p > alpha,
        'recommendation': 'Parametric' if p > alpha else 'Non-parametric'
    }

def check_homogeneity(*groups, alpha=0.05):
    """Test homogeneity of variance using Levene's test."""
    clean = [np.array(g)[~np.isnan(g)] for g in groups]
    stat, p = stats.levene(*clean)
    return {
        'method': 'Levene', 'statistic': round(stat, 4), 'p_value': round(p, 4),
        'is_homogeneous': p > alpha,
        'note': 'Equal variances assumed' if p > alpha else 'Use Welch correction or non-parametric'
    }

def choose_test(n_groups, paired=False, all_normal=True, homogeneous=True):
    """Recommend statistical test based on data characteristics."""
    if n_groups == 2:
        if all_normal:
            if paired:
                return 'Paired t-test'
            return 'Independent t-test' if homogeneous else "Welch's t-test"
        else:
            return 'Wilcoxon signed-rank' if paired else 'Mann-Whitney U'
    else:  # >2 groups
        if all_normal and homogeneous:
            return 'Repeated-measures ANOVA' if paired else 'One-way ANOVA + Tukey HSD'
        elif all_normal and not homogeneous:
            return "Welch's ANOVA + Games-Howell" if not paired else 'Repeated-measures ANOVA'
        else:
            return 'Friedman + Nemenyi' if paired else 'Kruskal-Wallis + Dunn'

def full_check(*groups, paired=False, alpha=0.05):
    """Run all assumption tests and recommend method. Returns full report."""
    if paired and len(groups) == 2:
        # For paired data: test normality of differences, not individual groups
        diff = np.array(groups[0]) - np.array(groups[1])
        diff_normality = check_normality(diff, alpha)
        all_normal = diff_normality['is_normal'] if diff_normality['is_normal'] is not None else False
        recommended = choose_test(2, paired=True, all_normal=all_normal, homogeneous=True)
        return {
            'normality_tests': [diff_normality],
            'normality_note': 'Tested on paired differences (not individual groups)',
            'homogeneity_test': None,
            'homogeneity_note': 'Levene test not applicable for paired data',
            'all_normal': all_normal,
            'homogeneous': None,
            'recommended_test': recommended,
            'alpha': alpha
        }
    normality = [check_normality(g, alpha) for g in groups]
    all_normal = all(r['is_normal'] for r in normality if r['is_normal'] is not None)
    homogeneity = check_homogeneity(*groups, alpha=alpha) if len(groups) > 1 else None
    homogeneous = homogeneity['is_homogeneous'] if homogeneity else True
    recommended = choose_test(len(groups), paired, all_normal, homogeneous)
    return {
        'normality_tests': normality,
        'homogeneity_test': homogeneity,
        'all_normal': all_normal,
        'homogeneous': homogeneous,
        'recommended_test': recommended,
        'alpha': alpha
    }

def effect_size_cohens_d(group1, group2):
    """Calculate Cohen's d with 95% CI for two independent groups."""
    g1, g2 = np.array(group1), np.array(group2)
    n1, n2 = len(g1), len(g2)
    pooled_std = np.sqrt(((n1-1)*g1.std(ddof=1)**2 + (n2-1)*g2.std(ddof=1)**2) / (n1+n2-2))
    d = (g1.mean() - g2.mean()) / pooled_std
    se_d = np.sqrt((n1 + n2) / (n1 * n2) + d**2 / (2 * (n1 + n2 - 2)))
    ci_lower = d - 1.96 * se_d
    ci_upper = d + 1.96 * se_d
    magnitude = 'small' if abs(d)<0.5 else ('medium' if abs(d)<0.8 else 'large')
    return {
        'cohens_d': round(d, 3),
        'ci_95': [round(ci_lower, 3), round(ci_upper, 3)],
        'magnitude': magnitude
    }
