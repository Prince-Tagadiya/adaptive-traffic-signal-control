"""
compute_final_statistical_analysis.py

Phase 10: Final Statistical Analysis of Blind Test Set
Generates:
- results/statistical_primary_waiting_time.csv
- results/statistical_secondary_metrics.csv
- results/effect_size_summary.csv

Strict protocol:
- Matched pairs design on simulation realizations (scenario, seed) with N=5.
- Primary metric: mean_waiting_time_s.
- Corrections: Holm-Bonferroni and Benjamini-Hochberg FDR across 21 primary tests.
- Secondary metrics: exploratory only, separated from primary family.
"""

import os
import numpy as np
import pandas as pd
from scipy import stats

def holm_bonferroni(p_vals):
    p_vals = np.asarray(p_vals, dtype=float)
    n = len(p_vals)
    order = np.argsort(p_vals)
    p_sorted = p_vals[order]
    adj_sorted = np.zeros(n)
    running_max = 0.0
    for i in range(n):
        val = (n - i) * p_sorted[i]
        running_max = max(running_max, val)
        adj_sorted[i] = min(1.0, running_max)
    adj = np.zeros(n)
    adj[order] = adj_sorted
    return adj

def benjamini_hochberg(p_vals):
    p_vals = np.asarray(p_vals, dtype=float)
    n = len(p_vals)
    order = np.argsort(p_vals)
    p_sorted = p_vals[order]
    q_sorted = np.zeros(n)
    running_min = 1.0
    for i in range(n - 1, -1, -1):
        rank = i + 1
        val = (n / rank) * p_sorted[i]
        running_min = min(running_min, val)
        q_sorted[i] = min(1.0, running_min)
    q = np.zeros(n)
    q[order] = q_sorted
    return q

def classify_result(mean_diff, p_adj, alpha=0.05, threshold=1e-6):
    if abs(mean_diff) < threshold:
        return "no statistically detectable difference"
    if p_adj < alpha:
        if mean_diff < 0:
            return "statistically supported improvement"
        else:
            return "statistically supported degradation"
    else:
        if mean_diff < 0:
            return "statistically unsupported improvement"
        else:
            return "statistically unsupported degradation"

def run_analysis():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    results_dir = os.path.join(base_dir, "results")
    input_file = os.path.join(results_dir, "final_test_results_per_seed.csv")
    
    df = pd.read_csv(input_file)
    
    scenarios = ['low', 'medium', 'high', 'oversaturated', 'asym_ns', 'asym_ew', 'dynamic']
    primary_comparators = [
        ('C0_Original_FixedTime', 'C0', 'Original Fixed-Time'),
        ('C1_Webster_FixedTime', 'C1', 'Webster-Calibrated Fixed-Time'),
        ('C2_Basic_Queue', 'C2', 'Basic Queue')
    ]
    
    demand_regimes = {
        'low': 'symmetric',
        'medium': 'symmetric',
        'high': 'symmetric',
        'oversaturated': 'oversaturated',
        'asym_ns': 'asymmetric',
        'asym_ew': 'asymmetric',
        'dynamic': 'dynamic'
    }
    
    # ---------------------------------------------------------
    # 1. Primary Analysis: mean_waiting_time_s
    # ---------------------------------------------------------
    primary_records = []
    
    for sc in scenarios:
        df_sc = df[df['scenario'] == sc]
        c3_df = df_sc[df_sc['controller_id'] == 'C3_Proposed_Adaptive'].sort_values('seed')
        c3_vals = c3_df['mean_waiting_time_s'].values
        seeds_c3 = c3_df['seed'].values
        
        for comp_id, comp_short, comp_name in primary_comparators:
            comp_df = df_sc[df_sc['controller_id'] == comp_id].sort_values('seed')
            comp_vals = comp_df['mean_waiting_time_s'].values
            seeds_comp = comp_df['seed'].values
            assert np.array_equal(seeds_c3, seeds_comp), f"Seed mismatch: {sc} {comp_id}"
            
            diff = c3_vals - comp_vals
            N = len(diff)
            df_deg = N - 1
            
            mean_c3 = float(np.mean(c3_vals))
            sd_c3 = float(np.std(c3_vals, ddof=1))
            mean_comp = float(np.mean(comp_vals))
            sd_comp = float(np.std(comp_vals, ddof=1))
            
            mean_diff = float(np.mean(diff))
            sd_diff = float(np.std(diff, ddof=1))
            se_diff = sd_diff / np.sqrt(N)
            
            t_crit = float(stats.t.ppf(0.975, df=df_deg))
            ci_low = mean_diff - t_crit * se_diff
            ci_high = mean_diff + t_crit * se_diff
            
            # Paired t-test
            if sd_diff > 1e-12:
                t_stat = mean_diff / se_diff
                raw_p_ttest = float(2.0 * (1.0 - stats.t.cdf(abs(t_stat), df=df_deg)))
                cohen_dz = mean_diff / sd_diff
            else:
                t_stat = 0.0
                raw_p_ttest = 1.0
                cohen_dz = 0.0
                
            # Wilcoxon signed-rank test (exact two-sided)
            # Check if all diffs are zero
            if np.all(diff == 0):
                w_stat = 0.0
                raw_p_wilcox = 1.0
            else:
                try:
                    w_res = stats.wilcoxon(c3_vals, comp_vals, alternative='two-sided', method='exact')
                    w_stat = float(w_res.statistic)
                    raw_p_wilcox = float(w_res.pvalue)
                except Exception:
                    w_stat = np.nan
                    raw_p_wilcox = np.nan
                    
            pct_change = float(100.0 * mean_diff / mean_comp) if mean_comp != 0 else 0.0
            
            primary_records.append({
                'scenario': sc,
                'demand_regime': demand_regimes[sc],
                'comparator_id': comp_id,
                'comparator_short': comp_short,
                'comparator_name': comp_name,
                'sample_size_N': N,
                'df': df_deg,
                'c3_mean': mean_c3,
                'c3_sd': sd_c3,
                'comparator_mean': mean_comp,
                'comparator_sd': sd_comp,
                'mean_difference_s': mean_diff,
                'sd_difference_s': sd_diff,
                'se_difference_s': se_diff,
                'ci_95_lower_s': ci_low,
                'ci_95_upper_s': ci_high,
                'pct_change': pct_change,
                't_stat': t_stat,
                'raw_p_ttest': raw_p_ttest,
                'wilcoxon_stat': w_stat,
                'raw_p_wilcoxon': raw_p_wilcox,
                'cohen_dz': cohen_dz
            })
            
    df_primary = pd.DataFrame(primary_records)
    
    # Apply multiple-comparison corrections across all 21 tests
    df_primary['p_holm_bonferroni'] = holm_bonferroni(df_primary['raw_p_ttest'].values)
    df_primary['p_benjamini_hochberg'] = benjamini_hochberg(df_primary['raw_p_ttest'].values)
    
    # Classifications
    # Using Holm (conservative FWER) and BH (FDR)
    df_primary['classification_holm'] = [
        classify_result(row['mean_difference_s'], row['p_holm_bonferroni'])
        for _, row in df_primary.iterrows()
    ]
    df_primary['classification_bh'] = [
        classify_result(row['mean_difference_s'], row['p_benjamini_hochberg'])
        for _, row in df_primary.iterrows()
    ]
    df_primary['classification_raw'] = [
        classify_result(row['mean_difference_s'], row['raw_p_ttest'])
        for _, row in df_primary.iterrows()
    ]
    
    # Save primary waiting time results
    out_primary_path = os.path.join(results_dir, "statistical_primary_waiting_time.csv")
    df_primary.to_csv(out_primary_path, index=False)
    print(f"Saved: {out_primary_path}")
    
    # ---------------------------------------------------------
    # 2. Effect Size Summary (Table for Report)
    # ---------------------------------------------------------
    effect_summary = []
    for _, row in df_primary.iterrows():
        ci_str = f"[{row['ci_95_lower_s']:.2f}, {row['ci_95_upper_s']:.2f}]"
        effect_summary.append({
            'scenario': row['scenario'],
            'demand_regime': row['demand_regime'],
            'comparator': row['comparator_short'],
            'c3_mean': round(row['c3_mean'], 2),
            'comparator_mean': round(row['comparator_mean'], 2),
            'mean_difference_s': round(row['mean_difference_s'], 2),
            'pct_change': round(row['pct_change'], 2),
            'ci_95': ci_str,
            'raw_p': row['raw_p_ttest'],
            'holm_p': row['p_holm_bonferroni'],
            'bh_q': row['p_benjamini_hochberg'],
            'wilcoxon_p': row['raw_p_wilcoxon'],
            'cohen_dz': round(row['cohen_dz'], 3),
            'classification_holm': row['classification_holm'],
            'classification_bh': row['classification_bh']
        })
    df_effect = pd.DataFrame(effect_summary)
    out_effect_path = os.path.join(results_dir, "effect_size_summary.csv")
    df_effect.to_csv(out_effect_path, index=False)
    print(f"Saved: {out_effect_path}")
    
    # ---------------------------------------------------------
    # 3. Secondary Metrics: C3 vs C1 and C3 vs C2 (Exploratory)
    # ---------------------------------------------------------
    sec_metrics = [
        ('mean_travel_time_s', 'Mean Travel Time (s)'),
        ('mean_delay_s', 'Mean Delay (s)'),
        ('mean_queue_veh', 'Mean Queue (veh)'),
        ('throughput_cohort_a', 'Cohort A Throughput (veh)'),
        ('phase_switch_count', 'Phase Switch Count')
    ]
    sec_comparators = [
        ('C1_Webster_FixedTime', 'C1', 'Webster-Calibrated Fixed-Time'),
        ('C2_Basic_Queue', 'C2', 'Basic Queue')
    ]
    
    secondary_records = []
    for m_col, m_name in sec_metrics:
        for sc in scenarios:
            df_sc = df[df['scenario'] == sc]
            c3_df = df_sc[df_sc['controller_id'] == 'C3_Proposed_Adaptive'].sort_values('seed')
            c3_vals = c3_df[m_col].values
            seeds_c3 = c3_df['seed'].values
            
            for comp_id, comp_short, comp_name in sec_comparators:
                comp_df = df_sc[df_sc['controller_id'] == comp_id].sort_values('seed')
                comp_vals = comp_df[m_col].values
                seeds_comp = comp_df['seed'].values
                assert np.array_equal(seeds_c3, seeds_comp)
                
                diff = c3_vals - comp_vals
                N = len(diff)
                df_deg = N - 1
                
                mean_c3 = float(np.mean(c3_vals))
                sd_c3 = float(np.std(c3_vals, ddof=1))
                mean_comp = float(np.mean(comp_vals))
                sd_comp = float(np.std(comp_vals, ddof=1))
                
                mean_diff = float(np.mean(diff))
                sd_diff = float(np.std(diff, ddof=1))
                se_diff = sd_diff / np.sqrt(N)
                
                t_crit = float(stats.t.ppf(0.975, df=df_deg))
                ci_low = mean_diff - t_crit * se_diff
                ci_high = mean_diff + t_crit * se_diff
                
                if sd_diff > 1e-12:
                    t_stat = mean_diff / se_diff
                    raw_p_ttest = float(2.0 * (1.0 - stats.t.cdf(abs(t_stat), df=df_deg)))
                    cohen_dz = mean_diff / sd_diff
                else:
                    t_stat = 0.0
                    raw_p_ttest = 1.0 if mean_diff == 0 else 0.0
                    cohen_dz = 0.0
                    
                if np.all(diff == 0):
                    w_stat = 0.0
                    raw_p_wilcox = 1.0
                else:
                    try:
                        w_res = stats.wilcoxon(c3_vals, comp_vals, alternative='two-sided', method='exact')
                        w_stat = float(w_res.statistic)
                        raw_p_wilcox = float(w_res.pvalue)
                    except Exception:
                        w_stat = np.nan
                        raw_p_wilcox = np.nan
                        
                pct_change = float(100.0 * mean_diff / mean_comp) if mean_comp != 0 else 0.0
                
                secondary_records.append({
                    'status': 'Exploratory/Secondary',
                    'metric': m_col,
                    'metric_name': m_name,
                    'scenario': sc,
                    'demand_regime': demand_regimes[sc],
                    'comparator_id': comp_id,
                    'comparator_short': comp_short,
                    'comparator_name': comp_name,
                    'sample_size_N': N,
                    'df': df_deg,
                    'c3_mean': mean_c3,
                    'c3_sd': sd_c3,
                    'comparator_mean': mean_comp,
                    'comparator_sd': sd_comp,
                    'mean_difference': mean_diff,
                    'sd_difference': sd_diff,
                    'se_difference': se_diff,
                    'ci_95_lower': ci_low,
                    'ci_95_upper': ci_high,
                    'pct_change': pct_change,
                    't_stat': t_stat,
                    'raw_p_ttest': raw_p_ttest,
                    'wilcoxon_stat': w_stat,
                    'raw_p_wilcoxon': raw_p_wilcox,
                    'cohen_dz': cohen_dz
                })
                
    df_secondary = pd.DataFrame(secondary_records)
    out_secondary_path = os.path.join(results_dir, "statistical_secondary_metrics.csv")
    df_secondary.to_csv(out_secondary_path, index=False)
    print(f"Saved: {out_secondary_path}")
    
    return df_primary, df_secondary, df_effect

if __name__ == '__main__':
    run_analysis()
