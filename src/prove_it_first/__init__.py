"""Prove It First: a tiny kit for testing trading ideas honestly (pre-registered rules, costs, block results, a sieve)."""
from .core import Criteria, Result, backtest_long_only, block_results, concentration, evaluate, finalist, max_drawdown, metrics

__all__ = ["Criteria", "Result", "backtest_long_only", "block_results", "concentration", "evaluate", "finalist", "max_drawdown", "metrics"]
