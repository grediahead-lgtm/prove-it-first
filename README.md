# Prove It First

A tiny, dependency-free kit for testing trading ideas **honestly**: write the rules first, count every attempt, pay costs on every trade, and let the idea pass or fail by criteria you fixed in advance.

> Education only. Not investment advice. Past results do not predict future results. You can lose money.

## Why
Most beautiful backtests are accidents: luck from many tries, peeking at the future, survivor-only lists, forgotten costs, one lucky period. This kit makes the cheap fixes the default.

## What is inside
| Path | What |
|---|---|
| `src/prove_it_first/core.py` | Long-only backtest (decide on close of t, trade at open of t+1, costs both sides), drawdown, equal time blocks, concentration, the six sieve criteria, finalist rule. No dependencies. |
| `templates/PREREGISTRATION_TEMPLATE.md` | The document you write BEFORE running anything. |
| `templates/HYPOTHESIS_LEDGER_TEMPLATE.md` | Count of every attempt on a dataset. |
| `templates/REVIEW_PROMPTS.md` | Prompts for an independent AI reviewer of your rules and code. |
| `docs/CHECKLIST.md`, `docs/LESSONS.md` | One-page checklist and the five ways a backtest lies. |
| `examples/demo_synthetic.py` | Two checks on synthetic data: random strategies should fail, a real trend-follower on a trending market should pass. |
| `tests/` | Unit tests (`python3 -m unittest discover -s tests`). |

## Quick start
```bash
python3 -m unittest discover -s tests
python3 examples/demo_synthetic.py
```
```python
from prove_it_first import backtest_long_only, evaluate, metrics
# opens/closes: {asset: [prices]}, same length for every asset; use 3+ assets so the concentration rule means something
normal  = backtest_long_only(opens, closes, my_signal, cost=0.0015, band=0.05)
doubled = backtest_long_only(opens, closes, my_signal, cost=0.003, band=0.05)   # always replay at double cost
hold    = backtest_long_only(opens, closes, lambda t, h: {a: 1 / len(h) for a in h}, cost=0.0015, band=0.05)
m = lambda r: metrics(r, block=200, blocks=11)
print(evaluate(m(normal), m(doubled), [m(hold)]))
```
`my_signal(t, history)` sees only closes up to candle `t` and returns target weights; the trade happens at the open of `t+1`, so looking ahead is impossible by construction.

Notes: `cost` is per side and should include slippage. `band` skips rebalances smaller than that share of equity (so drift does not create fake trades). The first decision is taken on candle `start` (default 1); every asset must have the same number of candles. The last equity point is marked after liquidation costs. Bad input (NaN, non-positive prices, weights outside [0, 1] or summing above 1) raises `ValueError`.

## Limitations (read this)
- Long-only, no leverage, no shorting, no funding or borrow costs, no partial fills, no order-book model. Slippage is whatever you put into `cost`.
- Synthetic demos prove the machinery, not any real edge. Passing the sieve means "worth a forward test on new data", never "profitable".
- Concentration is checked only with at least 3 assets. With fewer, that criterion is skipped and you must say so in your pre-registration.
- The default thresholds are illustrative. Choose your own and write them down before looking at results.
- No warranty. See LICENSE.

## Rules of the game
1. Write the pre-registration first, date it, never edit it after the run.
2. One attempt per idea. Log every look in the ledger.
3. The criteria are fixed before the run. A pass only means "admitted to a forward test on new data", never "signal found".
4. Keep a sealed final window you open once.

## License
MIT. Author: Dmytro Grechyshchev.

---

# Prove It First (українською)

Мінімальний набір без залежностей для чесної перевірки торгових ідей: спочатку записати правила, рахувати кожну спробу, платити комісії за кожну угоду і приймати рішення за критеріями, які зафіксовані заздалегідь.

> Тільки для навчання. Це не інвестиційна порада. Минулі результати не гарантують майбутніх. Ви можете втратити гроші.

**Що всередині:** ядро (`src/prove_it_first/core.py`), шаблони (передреєстрація правил, журнал гіпотез, запити для незалежного перегляду ШІ), чек-лист і п’ять способів, як бектест вводить в оману, демо на синтетичних даних і тести.

**Швидкий старт:** `python3 -m unittest discover -s tests`, потім `python3 examples/demo_synthetic.py`.

**Головне:** рішення на закритій свічці, угода на відкритті наступної; подвійний прогін із подвоєними комісіями; критерії не змінюються після перегляду результату; прохід відсіву означає лише допуск до перевірки на нових даних.
