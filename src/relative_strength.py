"""Cross-asset relative-strength ranking utilities.

The original notebook compared every asset pair through a directional signal on
their price ratio, then awarded one point to the stronger asset. This module
keeps that tournament-style ranking idea while making the ratio signal explicit
and replaceable.
"""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd

RatioSignal = Callable[[pd.Series], float]


def ratio_momentum_signal(ratio: pd.Series, lookback: int = 63) -> float:
    """Return +1 when the price ratio has risen over ``lookback`` bars, else -1.

    This transparent signal is used by the standalone example so the repository
    does not depend on the separate trend-ensemble project. The original research
    used the TPI trend ensemble to classify each ratio instead.
    """
    clean = ratio.dropna()
    if len(clean) <= lookback:
        raise ValueError(f"Need more than {lookback} observations for ratio momentum.")
    start = float(clean.iloc[-lookback - 1])
    end = float(clean.iloc[-1])
    if start <= 0 or end <= 0:
        raise ValueError("Price ratios require strictly positive prices.")
    return 1.0 if end / start > 1.0 else -1.0


def pairwise_scores(
    prices: pd.DataFrame,
    signal_fn: RatioSignal | None = None,
) -> pd.Series:
    """Rank assets by pairwise directional comparisons of their price ratios.

    For every unordered pair ``A, B``, the function forms ``A / B``. A positive
    ratio signal awards one point to ``A``; a negative signal awards one point to
    ``B``. The resulting score is therefore a simple tournament ranking.
    """
    if prices.shape[1] < 2:
        raise ValueError("At least two assets are required.")
    if signal_fn is None:
        signal_fn = ratio_momentum_signal

    clean = prices.astype(float).sort_index()
    scores = pd.Series(0.0, index=clean.columns, name="score")

    columns = list(clean.columns)
    for i, asset_a in enumerate(columns):
        for asset_b in columns[i + 1 :]:
            pair = clean[[asset_a, asset_b]].dropna()
            if pair.empty:
                continue
            ratio = pair[asset_a] / pair[asset_b]
            signal = float(signal_fn(ratio))
            if signal > 0:
                scores.loc[asset_a] += 1.0
            elif signal < 0:
                scores.loc[asset_b] += 1.0

    return scores.sort_values(ascending=False)


def pairwise_win_percent(scores: pd.Series) -> pd.Series:
    """Convert tournament scores into the percentage of peers each asset beats.

    With ``N`` assets, each asset is compared with ``N - 1`` peers. For example,
    in a six-asset universe, four pairwise wins correspond to an 80% win rate.
    """
    n_assets = len(scores)
    if n_assets < 2:
        raise ValueError("At least two assets are required.")
    return (scores.astype(float) / (n_assets - 1) * 100.0).rename("pairwise_win_percent")


def rank_history(
    prices: pd.DataFrame,
    lookback: int = 63,
    rebalance_every: int = 21,
) -> pd.DataFrame:
    """Compute tournament scores through time using only information available then."""
    prices = prices.astype(float).sort_index().dropna(how="all")
    if len(prices) <= lookback:
        raise ValueError("Not enough observations for the requested lookback.")

    rows: list[pd.Series] = []
    dates: list[pd.Timestamp] = []
    for end in range(lookback, len(prices), rebalance_every):
        window = prices.iloc[: end + 1]
        scores = pairwise_scores(
            window,
            signal_fn=lambda ratio, lb=lookback: ratio_momentum_signal(ratio, lb),
        )
        rows.append(scores.reindex(prices.columns))
        dates.append(prices.index[end])

    return pd.DataFrame(rows, index=pd.Index(dates, name="date"))


def normalized_rank_weights(scores: pd.Series, top_n: int | None = None) -> pd.Series:
    """Convert non-negative ranking scores into simple normalized allocation weights."""
    scores = scores.clip(lower=0).astype(float)
    if top_n is not None:
        keep = scores.nlargest(top_n).index
        scores = scores.where(scores.index.isin(keep), 0.0)
    if scores.sum() == 0:
        return pd.Series(1.0 / len(scores), index=scores.index, name="weight")
    return (scores / scores.sum()).rename("weight")
