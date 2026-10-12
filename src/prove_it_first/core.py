"""Core of the sieve: a long-only backtest with costs and next-open execution, plus the pass/fail criteria.

Design rules (they are the point of the kit):
  * The signal function sees only data up to the decision candle t. The trade happens at the OPEN of t+1.
  * Every trade pays a cost on both sides; you must also run a doubled-cost replay. Fold slippage into `cost`.
  * Criteria are fixed in code BEFORE you look at results. Changing a threshold after seeing numbers is cheating yourself.
  * Inputs are validated: bad data raises ValueError instead of producing quiet nonsense.
No third-party dependencies. Educational software, not investment advice. No warranty: passing the sieve does not
show that an idea is profitable.
"""
from dataclasses import dataclass
import math

EPS = 1e-9


@dataclass(frozen=True)
class Criteria:
    """The conditions that must ALL hold. The defaults are illustrative: write your own down before you test.

    Note: `min_return` and the benchmark rule are both applied (return >= min_return AND return > exposure * benchmark return).
    """
    blocks_required: int = 8                      # how many equal time blocks must be positive (out of `blocks` in metrics())
    max_drawdown: float = -0.30                   # worst peak-to-trough, not worse than -30%
    max_concentration: float = 0.40               # no single asset gives more than 40% of the positive profit
    concentration_min_assets: int = 3             # concentration is only meaningful with at least this many assets
    min_return: float = 0.10                      # beat doing nothing by a margin
    min_exposure: float = 0.05                    # idea must actually be invested sometimes
    min_trades: int = 100                         # enough fills that it is not luck

    def __post_init__(self):
        if not (self.max_drawdown < 0 and 0 < self.max_concentration <= 1 and self.blocks_required >= 1 and self.min_trades >= 0):
            raise ValueError("invalid criteria")


@dataclass
class Result:
    equity: list      # equity at each close; the last point is marked AFTER liquidation costs so every number agrees
    invested: list
    pnl_by_asset: dict
    trades: int
    final: float
    capital: float


def _validate(opens, closes, capital, cost, start):
    if not isinstance(opens, dict) or not isinstance(closes, dict) or not closes:
        raise ValueError("opens and closes must be non-empty dicts {asset: [prices]}")
    if set(opens) != set(closes):
        raise ValueError("opens and closes must have the same assets")
    lengths = {len(v) for v in list(opens.values()) + list(closes.values())}
    if len(lengths) != 1:
        raise ValueError("all price lists must have the same length")
    n = lengths.pop()
    if n < start + 2:
        raise ValueError("need at least start + 2 candles")
    for series in list(opens.values()) + list(closes.values()):
        for v in series:
            if not (isinstance(v, (int, float)) and math.isfinite(v) and v > 0):
                raise ValueError("prices must be finite and positive")
    if not (capital > 0 and 0 <= cost < 1 and start >= 0):
        raise ValueError("capital must be > 0, 0 <= cost < 1, start >= 0")
    return n


def _check_weights(w):
    if not isinstance(w, dict):
        raise ValueError("weight_fn must return a dict {asset: weight}")
    total = 0.0
    for a, x in w.items():
        if not (isinstance(x, (int, float)) and math.isfinite(x) and 0.0 <= x <= 1.0 + EPS):
            raise ValueError(f"weight for {a} must be in [0, 1], got {x!r}")
        total += x
    if total > 1.0 + 1e-6:
        raise ValueError("weights must sum to at most 1 (long-only, no leverage)")


def backtest_long_only(opens, closes, weight_fn, capital=1000.0, cost=0.0015, start=1, band=0.0):
    """opens/closes: {asset: [price per candle]}, same length for every asset.

    weight_fn(t, history) -> {asset: target weight in [0, 1]} (sum <= 1), decided on the close of candle t.
    `history` is {asset: closes[0..t]}, so looking ahead is impossible by construction. The first decision is taken
    on candle `start`; candle 0 is only history.
    Execution at the open of t+1: sells first, then buys limited by cash. `cost` is a fraction per side (0.0015 = 0.15%;
    include slippage in it). `band` skips rebalancing trades smaller than that share of equity (full exits always trade),
    which keeps drift from creating fees and fake trade counts.
    """
    n = _validate(opens, closes, capital, cost, start)
    assets = sorted(closes)
    cash, qty = float(capital), {a: 0.0 for a in assets}
    flow = {a: 0.0 for a in assets}
    trades = 0
    equity, invested = [], []
    pending = None
    for t in range(start, n):
        if pending is not None:
            eq_open = cash + sum(qty[a] * opens[a][t] for a in assets)
            for a in assets:      # sells first
                target = pending.get(a, 0.0) * eq_open
                have = qty[a] * opens[a][t]
                if have > target + EPS and (target <= EPS or (have - target) >= band * eq_open):
                    sell = have - target
                    proceeds = sell * (1 - cost)
                    cash += proceeds; flow[a] += proceeds; qty[a] -= sell / opens[a][t]; trades += 1
            for a in assets:      # then buys
                target = pending.get(a, 0.0) * eq_open
                have = qty[a] * opens[a][t]
                if target > have + EPS and (target - have) >= band * eq_open:
                    buy = min(target - have, cash / (1 + cost))
                    if buy > EPS:
                        cash -= buy * (1 + cost); flow[a] -= buy * (1 + cost); qty[a] += buy / opens[a][t]; trades += 1
            pending = None
        value = sum(qty[a] * closes[a][t] for a in assets)
        equity.append(cash + value); invested.append(value)
        if t + 1 < n:
            pending = weight_fn(t, {a: closes[a][: t + 1] for a in assets})
            _check_weights(pending)
    last = n - 1
    pnl = {a: flow[a] + qty[a] * closes[a][last] * (1 - cost) for a in assets}
    final = cash + sum(qty[a] * closes[a][last] * (1 - cost) for a in assets)
    equity[-1] = final            # mark the last point after liquidation costs: drawdown, blocks and return then agree
    return Result(equity, invested, pnl, trades, final, float(capital))


def max_drawdown(equity, start_value):
    peak, worst = start_value, 0.0
    for v in equity:
        peak = max(peak, v)
        worst = min(worst, v / peak - 1)
    return worst


def block_results(equity, start_value, block, blocks):
    """List of True/False per equal block (did equity at the end of the block exceed equity at its start?).
    Blocks that the data is too short to fill are returned as False, so a short series cannot look better."""
    out, prev = [], start_value
    for k in range(1, blocks + 1):
        i = k * block - 1
        if i >= len(equity):
            out.append(False)
            continue
        out.append(equity[i] > prev)
        prev = equity[i]
    return out


def concentration(pnl_by_asset):
    """Share of the positive profit that comes from the single best asset; None if nothing is positive."""
    positives = [v for v in pnl_by_asset.values() if v > 0]
    total = sum(positives)
    return (max(positives) / total) if total > 0 else None


def metrics(res, block, blocks):
    if res.capital <= 0 or not res.equity or any(e <= 0 for e in res.equity):
        raise ValueError("equity and capital must stay positive")
    blocks_ok = block_results(res.equity, res.capital, block, blocks)
    exposure = sum(i / e for i, e in zip(res.invested, res.equity)) / len(res.equity)
    return dict(ret=(res.final - res.capital) / res.capital, net=res.final - res.capital, max_drawdown=max_drawdown(res.equity, res.capital),
                blocks_positive=sum(blocks_ok), blocks_total=blocks, concentration=concentration(res.pnl_by_asset),
                assets=len(res.pnl_by_asset), exposure=exposure, trades=res.trades)


def evaluate(normal, doubled, benchmarks=(), criteria=Criteria()):
    """All conditions. `normal`/`doubled` are metrics() dicts from the normal and the doubled-cost replay;
    `benchmarks` are metrics() dicts of simple holds (e.g. the main asset, an equal-weight basket): the idea must beat exposure * their return.
    Concentration is skipped (counted as passed) when fewer than `criteria.concentration_min_assets` assets were available."""
    e = normal["exposure"]
    bench_ok = all(normal["ret"] > max(0.0, e * b["ret"]) for b in benchmarks)
    conc = normal["concentration"]
    conc_applies = normal.get("assets", 99) >= criteria.concentration_min_assets
    c = dict(
        c1_profit_at_double_costs=bool(doubled["net"] > 0),
        c2_blocks=bool(normal["blocks_positive"] >= criteria.blocks_required),
        c3_drawdown=bool(normal["max_drawdown"] >= criteria.max_drawdown),
        c4_concentration=bool((not conc_applies) or (conc is not None and conc <= criteria.max_concentration)),
        c5_beats_benchmarks=bool(e >= criteria.min_exposure and normal["ret"] >= criteria.min_return and bench_ok),
        c6_enough_trades=bool(normal["trades"] >= criteria.min_trades),
    )
    c["passed"] = all(c.values())
    return c


def finalist(results):
    """results: {name: dict(normal=metrics, doubled=metrics, criteria=evaluate(...))}. At most one finalist: the best
    (profit at double costs / |max drawdown|) among those that passed; ties go to the lower name; a drawdown of 0 is not eligible."""
    ranked = []
    for name in sorted(results):
        r = results[name]
        dd = r["normal"]["max_drawdown"]
        if r["criteria"]["passed"] and dd < 0:
            ranked.append((-(r["doubled"]["net"] / abs(dd)), name))
    ranked.sort()
    return ranked[0][1] if ranked else None
