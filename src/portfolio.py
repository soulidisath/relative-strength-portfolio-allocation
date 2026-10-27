"""Long-only portfolio allocation utilities used in the research experiments."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize


def simple_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Calculate aligned simple returns from a wide price table."""
    returns = prices.astype(float).sort_index().pct_change(fill_method=None)
    return returns.dropna(how="any")


def portfolio_statistics(weights: np.ndarray, returns: pd.DataFrame) -> tuple[float, float, float]:
    """Return mean period return, volatility and zero-rate Sharpe ratio."""
    mean_returns = returns.mean().to_numpy(dtype=float)
    covariance = returns.cov().to_numpy(dtype=float)
    expected_return = float(weights @ mean_returns)
    volatility = float(np.sqrt(weights.T @ covariance @ weights))
    sharpe = expected_return / volatility if volatility > 0 else float("nan")
    return expected_return, volatility, sharpe


def max_sharpe_weights(prices: pd.DataFrame) -> pd.Series:
    """Solve the notebook's long-only, fully-invested maximum-Sharpe allocation.

    This mirrors the original SLSQP experiment: weights are bounded to [0, 1],
    sum to one, and the objective maximizes mean return divided by volatility.
    No risk-free rate, turnover penalty or transaction cost is included.
    """
    returns = simple_returns(prices)
    if returns.shape[1] < 2:
        raise ValueError("At least two assets are required for portfolio optimization.")

    mean_returns = returns.mean().to_numpy(dtype=float)
    covariance = returns.cov().to_numpy(dtype=float)
    n_assets = len(mean_returns)

    def negative_sharpe(weights: np.ndarray) -> float:
        portfolio_return = float(weights @ mean_returns)
        variance = float(weights.T @ covariance @ weights)
        if variance <= 0:
            return 1e9
        return -(portfolio_return / np.sqrt(variance))

    constraints = ({"type": "eq", "fun": lambda weights: np.sum(weights) - 1.0},)
    bounds = tuple((0.0, 1.0) for _ in range(n_assets))
    initial = np.full(n_assets, 1.0 / n_assets)

    result = minimize(
        negative_sharpe,
        initial,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
    )
    if not result.success:
        raise RuntimeError(f"SLSQP optimization failed: {result.message}")

    weights = pd.Series(result.x, index=returns.columns, name="weight")
    weights[weights.abs() < 1e-10] = 0.0
    return weights / weights.sum()


def equal_weights(columns: pd.Index | list[str]) -> pd.Series:
    """Return an equal-weight allocation for comparison."""
    columns = list(columns)
    return pd.Series(1.0 / len(columns), index=columns, name="weight")
