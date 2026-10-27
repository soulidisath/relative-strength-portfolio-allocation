# Examples

`cross_asset_demo.py` is a standalone demonstration of the two ideas preserved from the original notebooks:

1. **Pairwise relative-strength ranking** — compare every asset pair through the trend of their price ratio and award one point to the stronger asset.
2. **Long-only portfolio allocation** — solve a fully invested maximum-Sharpe problem with SLSQP using historical mean returns and the covariance matrix.

The original relative-strength notebook used the separate TPI trend ensemble to classify each pairwise ratio. To keep this repository independent and easy to reproduce, the example uses a transparent 63-day price-ratio momentum signal instead. The ranking mechanism itself is unchanged.

Run from the repository root:

```bash
python examples/cross_asset_demo.py
```

The script downloads daily prices for a small crypto universe and generates:

- `output/relative_strength_ranking.png` — current pairwise tournament scores.
- `output/allocation_weights.png` — comparison of top-ranked normalized weights with the long-only maximum-Sharpe allocation.

These are research diagnostics only. The example does not establish predictive performance or portfolio profitability.
