"""Reproducible cross-asset ranking and allocation example.

The script downloads a small liquid crypto universe, ranks assets through pairwise
price-ratio momentum, and compares simple rank-derived weights with the long-only
maximum-Sharpe allocation used in the original research notebook.

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
from src.relative_strength import normalized_rank_weights, pairwise_scores, ratio_momentum_signal

TICKERS = ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD"]
LOOKBACK = 63
ALLOCATION_WINDOW = 252
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


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = download_prices()

    scores = pairwise_scores(
        prices,
        signal_fn=lambda ratio: ratio_momentum_signal(ratio, lookback=LOOKBACK),
    )
    rank_weights = normalized_rank_weights(scores, top_n=3).reindex(TICKERS, fill_value=0.0)

    allocation_prices = prices.tail(ALLOCATION_WINDOW)
    sharpe_weights = max_sharpe_weights(allocation_prices).reindex(TICKERS, fill_value=0.0)

    print("Pairwise relative-strength scores:")
    print(scores.to_string())
    print("\nTop-3 normalized rank weights:")
    print(rank_weights.sort_values(ascending=False).round(4).to_string())
    print("\nLong-only maximum-Sharpe weights:")
    print(sharpe_weights.sort_values(ascending=False).round(4).to_string())

    ranking = scores.sort_values()
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ranking.plot(kind="barh", ax=ax)
    ax.set_title(f"Pairwise relative-strength ranking ({LOOKBACK}-day ratio momentum)")
    ax.set_xlabel("Pairwise wins")
    ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "relative_strength_ranking.png", dpi=160)
    plt.close(fig)

    comparison = pd.DataFrame(
        {
            "Rank-derived": rank_weights,
            "Max-Sharpe": sharpe_weights,
        }
    )
    fig, ax = plt.subplots(figsize=(9, 4.8))
    comparison.plot(kind="bar", ax=ax)
    ax.set_title("Two allocation translations of the same asset universe")
    ax.set_ylabel("Portfolio weight")
    ax.set_xlabel("")
    ax.set_ylim(bottom=0)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "allocation_weights.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
