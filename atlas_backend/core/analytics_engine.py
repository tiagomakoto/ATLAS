import numpy as np
from scipy import stats

def compute_returns(prices):
    prices = np.array(prices)
    return np.diff(prices) / prices[:-1]

def compute_walk_forward(ir_series, window_size=12):
    results = []
    for i in range(window_size, len(ir_series) + 1):
        window = ir_series[i - window_size:i]
        mean_ir = float(np.mean(window))
        boot = [
            float(np.mean(np.random.choice(window, len(window), replace=True)))
            for _ in range(1000)
        ]
        results.append({
            "window_end": i,
            "ir_mean": mean_ir,
            "ci_lower": float(np.percentile(boot, 2.5)),
            "ci_upper": float(np.percentile(boot, 97.5)),
            "n": len(window)
        })
    return {
        "type": "walk_forward",
        "series": results,
        "total_n": len(ir_series)
    }

def compute_distribution(returns):
    returns = np.array(returns)
    hist, bins = np.histogram(returns, bins=30)
    return {
        "type": "distribution",
        "histogram": hist.tolist(),
        "bins": bins.tolist(),
        "boxplot": {
            "q1": float(np.percentile(returns, 25)),
            "median": float(np.median(returns)),
            "q3": float(np.percentile(returns, 75)),
            "min": float(np.min(returns)),
            "max": float(np.max(returns))
        },
        "n": len(returns)
    }

def compute_acf(returns, lags=30):
    returns = np.array(returns)
    n = len(returns)
    confidence_band = float(1.96 / np.sqrt(n)) if n > 0 else 0.0
    acf_values = []
    for lag in range(1, lags + 1):
        if lag < n:
            corr = float(np.corrcoef(returns[:-lag], returns[lag:])[0, 1])
        else:
            corr = 0.0
        acf_values.append(corr)
    return {
        "type": "acf",
        "lags": list(range(1, lags + 1)),
        "values": acf_values,
        "confidence_band": confidence_band,
        "n": n
    }

def compute_tail_metrics(returns):
    returns = np.array(returns)
    skew_val = float(stats.skew(returns)) if len(returns) > 2 else 0.0
    return {
        "type": "fat_tails",
        "mean": float(np.mean(returns)),
        "std": float(np.std(returns)),
        "skew": skew_val,
        "kurtosis": float(stats.kurtosis(returns)),
        "p1": float(np.percentile(returns, 1)),
        "p99": float(np.percentile(returns, 99))
    }