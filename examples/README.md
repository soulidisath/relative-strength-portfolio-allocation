# Examples

`cross_asset_demo.py` is a standalone demonstration of the two ideas preserved from the original notebooks:

1. **Pairwise relative-strength ranking** — compare every market pair through the trend of their price ratio and award one point to the stronger market.
2. **Long-only portfolio allocation** — solve a fully invested maximum-Sharpe problem with SLSQP using historical mean returns and the covariance matrix.

The original relative-strength notebook used the separate TPI trend ensemble to classify each pairwise ratio. To keep this repository independent and easy to reproduce, the example uses a transparent 63-day price-ratio momentum signal instead. The ranking mechanism itself is unchanged.

The example universe is Gold, Silver, Copper, WTI crude oil, Natural Gas, and Corn futures proxies from Yahoo Finance.

Run from the repository root:

```bash
python examples/cross_asset_demo.py
```

The script generates four diagnostics:

- `output/commodity_price_performance.png` — the six commodity series rebased to 100 over the ranking window.
- `output/relative_strength_win_rate.png` — current ranking expressed as the percentage of peers beaten.
- `output/relative_strength_history.png` — the same percentage ranking recalculated through time.
- `output/allocation_weights.png` — percentage portfolio weights from the rank-derived and long-only maximum-Sharpe approaches.

With six commodities, every market has five pairwise comparisons. A relative-strength reading of 80% therefore means that market beat four of its five peers over the selected lookback.

These are research diagnostics only. Yahoo Finance futures series can include roll effects, and the example does not establish predictive performance or portfolio profitability.
