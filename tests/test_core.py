import random
import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from prove_it_first import Criteria, backtest_long_only, block_results, concentration, evaluate, finalist, max_drawdown, metrics


def walk(n, seed, drift=0.0, vol=0.01):
    rng = random.Random(seed)
    price, opens, closes = 100.0, [], []
    for _ in range(n):
        o = price * (1 + rng.gauss(0, vol / 3))
        price = o * (1 + rng.gauss(drift, vol))
        opens.append(o); closes.append(price)
    return opens, closes


def trending(n, seed, assets=5):
    """Synthetic market with slow shared up/down regimes plus noise: a trend-follower has a genuine edge here."""
    rng = random.Random(seed)
    regime, r = [], 0.0
    for t in range(n):
        if t % 300 == 0:
            r = rng.choice([0.0025, -0.0015, 0.003, -0.001])
        regime.append(r)
    opens, closes = {}, {}
    for a in range(assets):
        p, o, c = 100.0, [], []
        for t in range(n):
            op = p * (1 + rng.gauss(0, 0.002)); p = op * (1 + regime[t] + rng.gauss(0, 0.008)); o.append(op); c.append(p)
        opens[f"A{a}"], closes[f"A{a}"] = o, c
    return opens, closes


class Core(unittest.TestCase):
    def test_executes_at_next_open_not_at_signal_close(self):
        opens = {"A": [100.0, 100.0, 120.0, 120.0]}
        closes = {"A": [100.0, 100.0, 100.0, 130.0]}
        res = backtest_long_only(opens, closes, lambda t, h: {"A": 1.0}, capital=1000, cost=0.0, start=1)
        # signal at close of t=1 (price 100) executes at open of t=2 (120): 1000/120 units, worth 1083.33 at close 130
        self.assertAlmostEqual(res.final, 1000 / 120 * 130, places=6)

    def test_signal_sees_only_past(self):
        seen = []
        opens, closes = {"A": list(range(1, 11))}, {"A": list(range(1, 11))}
        backtest_long_only(opens, closes, lambda t, h: seen.append(len(h["A"])) or {}, capital=100, cost=0.0, start=1)
        self.assertEqual(seen, [2, 3, 4, 5, 6, 7, 8, 9])  # history length is always t+1

    def test_costs_hurt_and_doubled_is_worse(self):
        o, c = walk(400, 1, drift=0.001)
        weight = lambda t, h: {"A": 1.0 if t % 2 == 0 else 0.0}
        a = backtest_long_only({"A": o}, {"A": c}, weight, cost=0.0015)
        b = backtest_long_only({"A": o}, {"A": c}, weight, cost=0.003)
        z = backtest_long_only({"A": o}, {"A": c}, weight, cost=0.0)
        self.assertGreater(z.final, a.final); self.assertGreater(a.final, b.final)

    def test_cash_never_negative_and_pnl_adds_up(self):
        o, c = walk(300, 2)
        o2, c2 = walk(300, 3)
        res = backtest_long_only({"A": o, "B": o2}, {"A": c, "B": c2}, lambda t, h: {"A": 0.5, "B": 0.5}, cost=0.002)
        self.assertTrue(all(v > 0 for v in res.equity))
        self.assertTrue(all(i <= e + 1e-9 for i, e in zip(res.invested[:-1], res.equity[:-1])))
        self.assertAlmostEqual(res.final - res.capital, sum(res.pnl_by_asset.values()), places=6)

    def test_drawdown_blocks_concentration(self):
        self.assertAlmostEqual(max_drawdown([100, 120, 60, 90], 100), -0.5)
        self.assertEqual(block_results([101, 102, 99, 98, 120, 130], 100, 2, 3), [True, False, True])
        self.assertAlmostEqual(concentration({"A": 30, "B": 10, "C": -20}), 0.75)
        self.assertIsNone(concentration({"A": -1}))

    def test_criteria_all_required_and_thresholds_fixed(self):
        good = dict(ret=0.5, net=500.0, max_drawdown=-0.1, blocks_positive=9, blocks_total=11, concentration=0.2, assets=5, exposure=0.6, trades=150)
        dbl = dict(good, net=100.0)
        bench = dict(ret=0.1)
        self.assertTrue(evaluate(good, dbl, [bench])["passed"])
        for field, value in (("blocks_positive", 5), ("max_drawdown", -0.4), ("concentration", 0.9), ("trades", 10), ("ret", 0.05), ("exposure", 0.01)):
            bad = dict(good, **{field: value})
            self.assertFalse(evaluate(bad, dbl, [bench])["passed"], field)
        self.assertFalse(evaluate(good, dict(dbl, net=-1.0), [bench])["passed"])
        self.assertFalse(evaluate(good, dbl, [dict(ret=2.0)])["passed"])   # loses to a simple hold

    def test_concentration_skipped_for_few_assets_but_enforced_with_many(self):
        good = dict(ret=0.5, net=500.0, max_drawdown=-0.1, blocks_positive=9, blocks_total=11, concentration=1.0, assets=1, exposure=0.6, trades=150)
        self.assertTrue(evaluate(good, good, [])["c4_concentration"])
        self.assertFalse(evaluate(dict(good, assets=5), good, [])["c4_concentration"])

    def test_rejects_bad_inputs(self):
        o = {"A": [1.0, 1.0, 1.0, 1.0]}
        ok = lambda t, h: {"A": 0.5}
        for bad in (
            lambda: backtest_long_only({"A": [1.0, float("nan"), 1.0, 1.0]}, o, ok),
            lambda: backtest_long_only({"A": [1.0, 0.0, 1.0, 1.0]}, o, ok),
            lambda: backtest_long_only(o, {"A": [1.0, 1.0, 1.0]}, ok),
            lambda: backtest_long_only(o, {"B": [1.0] * 4}, ok),
            lambda: backtest_long_only(o, o, ok, capital=0),
            lambda: backtest_long_only(o, o, ok, cost=1.5),
            lambda: backtest_long_only(o, o, lambda t, h: {"A": float("nan")}),
            lambda: backtest_long_only(o, o, lambda t, h: {"A": 1.5}),
            lambda: backtest_long_only(o, o, lambda t, h: {"A": -0.1}),
            lambda: backtest_long_only(o, o, lambda t, h: [1]),
            lambda: Criteria(max_drawdown=0.1),
        ):
            with self.assertRaises(ValueError):
                bad()

    def test_weights_summing_over_one_rejected(self):
        o = {"A": [1.0] * 5, "B": [1.0] * 5}
        with self.assertRaises(ValueError):
            backtest_long_only(o, o, lambda t, h: {"A": 0.7, "B": 0.7})

    def test_last_equity_point_is_after_liquidation_costs(self):
        o = {"A": [100.0] * 6}
        res = backtest_long_only(o, o, lambda t, h: {"A": 1.0}, capital=1000, cost=0.01)
        self.assertAlmostEqual(res.equity[-1], res.final, places=9)
        self.assertAlmostEqual(res.final - 1000, sum(res.pnl_by_asset.values()), places=9)

    def test_full_exit_leaves_no_dust(self):
        o = {"A": [100.0, 103.0, 97.0, 101.0, 99.0, 100.0, 102.0]}
        res = backtest_long_only(o, o, lambda t, h: {"A": 1.0 if t % 2 else 0.0}, cost=0.001)
        self.assertTrue(all(i >= 0 for i in res.invested))

    def test_band_reduces_tiny_rebalances(self):
        o, c = walk(300, 5)
        fn = lambda t, h: {"A": 0.5}
        free = backtest_long_only({"A": o}, {"A": c}, fn, cost=0.001)
        banded = backtest_long_only({"A": o}, {"A": c}, fn, cost=0.001, band=0.05)
        self.assertLess(banded.trades, free.trades)

    def test_short_series_cannot_pass_block_rule(self):
        self.assertEqual(block_results([101, 102], 100, 2, 3), [True, False, False])

    def test_finalist_prefers_better_ratio_and_ties_to_name_order(self):
        base = dict(normal=dict(max_drawdown=-0.1), doubled=dict(net=10.0), criteria=dict(passed=True))
        self.assertEqual(finalist({"b": base, "a": base}), "a")
        self.assertIsNone(finalist({"x": dict(base, criteria=dict(passed=False))}))
        self.assertIsNone(finalist({"x": dict(base, normal=dict(max_drawdown=0.0))}))

    def test_random_strategies_rarely_pass_the_sieve(self):
        passes = 0
        for k in range(30):
            rng = random.Random(k)
            data = [walk(2200, 100 * k + a) for a in range(4)]
            opens = {f"A{a}": d[0] for a, d in enumerate(data)}
            closes = {f"A{a}": d[1] for a, d in enumerate(data)}
            flips = [[rng.random() < 0.5 for _ in range(2200)] for _ in range(4)]
            fn = lambda t, h: {a: 0.25 for i, a in enumerate(sorted(h)) if flips[i][t]}
            hold = lambda t, h: {a: 0.25 for a in h}
            n = backtest_long_only(opens, closes, fn, cost=0.0015)
            d = backtest_long_only(opens, closes, fn, cost=0.003)
            b = backtest_long_only(opens, closes, hold, cost=0.0015)
            m = lambda r: metrics(r, 200, 11)
            if evaluate(m(n), m(d), [m(b)])["passed"]:
                passes += 1
        self.assertLessEqual(passes, 1)

    def test_positive_control_a_real_effect_can_pass(self):
        """A sieve that nothing can pass is useless: an idea that follows a genuine trend must pass on a trending market."""
        o, c = trending(2400, 2)
        def sig(t, h):
            up = [a for a in h if len(h[a]) >= 50 and h[a][-1] > sum(h[a][-50:]) / 50]
            return {a: 1.0 / len(h) for a in up}
        hold = lambda t, h: {a: 1.0 / len(h) for a in h}
        n = backtest_long_only(o, c, sig, cost=0.0015, band=0.05)
        d = backtest_long_only(o, c, sig, cost=0.003, band=0.05)
        b = backtest_long_only(o, c, hold, cost=0.0015, band=0.05)
        m = lambda r: metrics(r, 200, 11)
        self.assertTrue(evaluate(m(n), m(d), [m(b)])["passed"])


if __name__ == "__main__":
    unittest.main()
