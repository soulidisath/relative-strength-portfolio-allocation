"""Reproducible commodity relative-strength and allocation example.

The script downloads a small diversified commodity-futures universe, ranks the
contracts through pairwise price-ratio momentum, expresses strength as the
percentage of peers beaten, and compares a simple rank-derived allocation with
the long-only maximum-Sharpe allocation used in the original research notebook.

The figures are descriptive research diagnostics, not performance claims.
"""

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.portfolio import max_sharpe_weights
from src.relative_strength import (
    normalized_rank_weights,
    pairwise_scores,
    pairwise_win_percent,
    rank_history,
    ratio_momentum_signal,
)

TICKERS = ["GC=F", "SI=F", "HG=F", "CL=F", "NG=F", "ZC=F"]
NAMES = {
    "GC=F": "Gold",
    "SI=F": "Silver",
    "HG=F": "Copper",
    "CL=F": "WTI crude",
    "NG=F": "Natural gas",
    "ZC=F": "Corn",
}
LOOKBACK = 63
ALLOCATION_WINDOW = 252
HISTORY_STEP = 21
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def download_prices() -> pd.DataFrame:
    raw = yf.download(
        TICKERS,
        period="3y",
        interval="1d",
        auto_adjust=True,
        progress=False,
        group_by="column",
    )

    if isinstance(raw.columns, pd.MultiIndex):
        if "Close" in raw.columns.get_level_values(0):
            prices = raw["Close"]
        elif "Close" in raw.columns.get_level_values(1):
            prices = raw.xs("Close", axis=1, level=1)
        else:
            raise RuntimeError("Could not locate Close prices in yfinance output.")
    else:
        if "Close" not in raw.columns:
            raise RuntimeError("Could not locate Close prices in yfinance output.")
        prices = raw[["Close"]].rename(columns={"Close": TICKERS[0]})

    prices = prices.reindex(columns=TICKERS).dropna(how="any")
    if len(prices) <= max(LOOKBACK, ALLOCATION_WINDOW):
        raise RuntimeError("Downloaded history is too short for the example windows.")
    return prices


def add_bar_labels(ax, suffix="") -> None:
    for container in ax.containers:
        ax.bar_label(container, fmt=lambda value: f"{value:.0f}{suffix}", padding=3, fontsize=8)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = download_prices()

    scores = pairwise_scores(
        prices,
        signal_fn=lambda ratio: ratio_momentum_signal(ratio, lookback=LOOKBACK),
    )
    win_pct = pairwise_win_percent(scores)
    rank_weights = normalized_rank_weights(scores, top_n=3).reindex(TICKERS, fill_value=0.0)

    allocation_prices = prices.tail(ALLOCATION_WINDOW)
    sharpe_weights = max_sharpe_weights(allocation_prices).reindex(TICKERS, fill_value=0.0)

    print("Pairwise relative-strength win percentages:")
    print(win_pct.rename(index=NAMES).round(1).to_string())
    print("\nTop-3 normalized rank weights (%):")
    print((rank_weights.rename(index=NAMES) * 100).sort_values(ascending=False).round(1).to_string())
    print("\nLong-only maximum-Sharpe weights (%):")
    print((sharpe_weights.rename(index=NAMES) * 100).sort_values(ascending=False).round(1).to_string())

    # 1) Show the actual price moves used by the final 63-day ranking.
    recent = prices.tail(LOOKBACK + 1).rename(columns=NAMES)
    normalized = recent.div(recent.iloc[0]).mul(100)
    fig, ax = plt.subplots(figsize=(10, 5.4))
    normalized.plot(ax=ax)
    ax.axhline(100, linewidth=1)
    ax.set_title(f"Commodity price performance over the {LOOKBACK}-day ranking window")
    ax.set_ylabel("Indexed price (start = 100)")
    ax.set_xlabel("")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "commodity_price_performance.png", dpi=160)
    plt.close(fig)

    # 2) Express the tournament score as an intuitive percentage of peers beaten.
    ranking = win_pct.rename(index=NAMES).sort_values()
    fig, ax = plt.subplots(figsize=(9, 5.0))
    ranking.plot(kind="barh", ax=ax)
    ax.set_title("Relative strength: percentage of commodity peers beaten")
    ax.set_xlabel("Pairwise win rate")
    ax.set_ylabel("")
    ax.set_xlim(0, 105)
    ax.set_xticks([0, 20, 40, 60, 80, 100], labels=["0%", "20%", "40%", "60%", "80%", "100%"])
    add_bar_labels(ax, "%")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "relative_strength_win_rate.png", dpi=160)
    plt.close(fig)

    # 3) Show how leadership changed through time, not just the latest snapshot.
    history_scores = rank_history(prices, lookback=LOOKBACK, rebalance_every=HISTORY_STEP)
    history_pct = history_scores.div(len(TICKERS) - 1).mul(100).rename(columns=NAMES)
    history_pct = history_pct.tail(18)
    fig, ax = plt.subplots(figsize=(10, 5.4))
    history_pct.plot(ax=ax, marker="o", markersize=3)
    ax.set_title("Relative-strength leadership through time")
    ax.set_ylabel("Peers beaten")
    ax.set_xlabel("")
    ax.set_ylim(-5, 105)
    ax.set_yticks([0, 20, 40, 60, 80, 100], labels=["0%", "20%", "40%", "60%", "80%", "100%"])
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "relative_strength_history.png", dpi=160)
    plt.close(fig)

    # 4) Keep allocation secondary and label it directly in percentages.
    comparison = pd.DataFrame(
        {
            "Rank-derived": rank_weights,
            "Max-Sharpe": sharpe_weights,
        }
    ).rename(index=NAMES).mul(100)
    fig, ax = plt.subplots(figsize=(10, 5.0))
    comparison.plot(kind="bar", ax=ax)
    ax.set_title("Illustrative portfolio weights from two different allocation rules")
    ax.set_ylabel("Portfolio weight")
    ax.set_xlabel("")
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(lambda value, pos: f"{value:.0f}%")
    add_bar_labels(ax, "%")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "allocation_weights.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
