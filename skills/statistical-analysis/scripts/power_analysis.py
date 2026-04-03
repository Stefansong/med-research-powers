"""
Sample size calculation for common medical research designs.
Usage: from power_analysis import two_groups, diagnostic, survival, proportion
"""

import math
from scipy import stats as st

def two_groups(effect_size, alpha=0.05, power=0.80, ratio=1.0, dropout=0.1):
    """Two-group continuous outcome (t-test). effect_size = Cohen's d."""
    from statsmodels.stats.power import TTestIndPower
    analysis = TTestIndPower()
    n = analysis.solve_power(effect_size=effect_size, alpha=alpha, power=power, ratio=ratio)
    n_control = math.ceil(n)
    n_treatment = math.ceil(n * ratio)
    n_control_adj = math.ceil(n_control / (1 - dropout))
    n_treatment_adj = math.ceil(n_treatment / (1 - dropout))
    return {
        'n_per_group': n_control,
        'n_treatment': n_treatment,
        'n_control_adjusted': n_control_adj,
        'n_treatment_adjusted': n_treatment_adj,
        'total': n_control_adj + n_treatment_adj,
        'params': {'effect_size': effect_size, 'alpha': alpha, 'power': power, 'ratio': ratio, 'dropout': dropout}
    }

def proportion(p1, p2, alpha=0.05, power=0.80, ratio=1.0, dropout=0.1):
    """Two-group proportion comparison (chi-square)."""
    from statsmodels.stats.power import NormalIndPower
    es = 2 * (math.asin(math.sqrt(p1)) - math.asin(math.sqrt(p2)))  # Cohen's h
    analysis = NormalIndPower()
    n = analysis.solve_power(effect_size=abs(es), alpha=alpha, power=power, ratio=ratio)
    n_adj = math.ceil(n / (1 - dropout))
    return {
        'n_per_group': math.ceil(n),
        'n_adjusted': n_adj,
        'effect_size_h': round(es, 3),
        'params': {'p1': p1, 'p2': p2, 'alpha': alpha, 'power': power}
    }

def diagnostic(sensitivity, prevalence, precision=0.05, confidence=0.95):
    """Diagnostic accuracy study sample size based on target precision."""
    z = st.norm.ppf(1 - (1 - confidence) / 2)
    n_diseased = math.ceil((z**2 * sensitivity * (1 - sensitivity)) / precision**2)
    n_total = math.ceil(n_diseased / prevalence)
    return {
        'n_diseased': n_diseased,
        'n_total': n_total,
        'params': {'sensitivity': sensitivity, 'prevalence': prevalence, 'precision': precision}
    }

def survival(hazard_ratio, alpha=0.05, power=0.80, ratio=1.0, event_rate=0.5, dropout=0.1):
    """Survival analysis (log-rank test) sample size."""
    z_alpha = st.norm.ppf(1 - alpha / 2)
    z_beta = st.norm.ppf(power)
    d = ((z_alpha + z_beta)**2) / (math.log(hazard_ratio)**2 * ratio / (1 + ratio)**2)
    d = math.ceil(d) * (1 + ratio)
    n = math.ceil(d / event_rate / (1 - dropout))
    return {
        'events_needed': math.ceil(d),
        'n_total': n,
        'params': {'hazard_ratio': hazard_ratio, 'event_rate': event_rate, 'alpha': alpha, 'power': power}
    }

def correlation(r_expected, alpha=0.05, power=0.80):
    """Sample size for detecting a correlation."""
    z_alpha = st.norm.ppf(1 - alpha / 2)
    z_beta = st.norm.ppf(power)
    z_r = 0.5 * math.log((1 + r_expected) / (1 - r_expected))
    n = math.ceil(((z_alpha + z_beta) / z_r)**2 + 3)
    return {'n': n, 'params': {'r_expected': r_expected, 'alpha': alpha, 'power': power}}
