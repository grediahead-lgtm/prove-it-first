"""Two experiments on synthetic markets (no real data, no network):
  1. 30 coin-flip "strategies" on random-walk prices  -> almost none should pass the sieve.
  2. A trend-follower on a market that really trends  -> it should pass (a sieve nothing can pass is useless).
Run:  python3 examples/demo_synthetic.py
"""
import os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tests"))
from prove_it_first import backtest_long_only, evaluate, metrics
from test_core import trending, walk

N, BLOCK, BLOCKS, ASSETS = 2200, 200, 11, 4
m = lambda r: metrics(r, BLOCK, BLOCKS)


def run(opens, closes, signal, hold):
    n = backtest_long_only(opens, closes, signal, cost=0.0015, band=0.05)
    d = backtest_long_only(opens, closes, signal, cost=0.003, band=0.05)
    b = backtest_long_only(opens, closes, hold, cost=0.0015, band=0.05)
    return evaluate(m(n), m(d), [m(b)]), m(n)


hold = lambda t, h: {a: 1.0 / len(h) for a in h}
passed = 0
for k in range(30):
    rng = random.Random(k)
    data = [walk(N, 100 * k + a) for a in range(ASSETS)]
    opens = {f"A{a}": d[0] for a, d in enumerate(data)}
    closes = {f"A{a}": d[1] for a, d in enumerate(data)}
    flips = [[rng.random() < 0.5 for _ in range(N)] for _ in range(ASSETS)]
    signal = lambda t, h: {a: 1.0 / ASSETS for i, a in enumerate(sorted(h)) if flips[i][t]}
    passed += run(opens, closes, signal, hold)[0]["passed"]
print(f"1. {passed} of 30 random strategies passed. Luck rarely survives all six conditions plus doubled costs.")

o, c = trending(2400, 2)
def above_average(t, h):
    up = [a for a in h if len(h[a]) >= 50 and h[a][-1] > sum(h[a][-50:]) / 50]
    return {a: 1.0 / len(h) for a in up}
verdict, stats = run(o, c, above_average, hold)
print(f"2. Trend-follower on a trending market: passed={verdict['passed']}, return {stats['ret']:.0%}, worst drawdown {stats['max_drawdown']:.0%}, {stats['trades']} trades.")
print("   (Synthetic data. A pass here says the machinery works, not that any real idea is profitable.)")
