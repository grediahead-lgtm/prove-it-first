# Pre-registration: <idea name>

Write this BEFORE you look at any result. Date it. Never edit it after the run; add a dated amendment instead.

## 1. Idea and mechanism
One paragraph: why should this work, and who is on the other side of the trade?

## 2. Data
- Instruments and how the list is chosen (as of the START date, not today's ranking: avoids survivor bias).
- Period used for sieving. Period kept sealed for one final exam (do not look at it).
- Time zone (use one, e.g. UTC) and what counts as a missing candle.

## 3. Rules (exact numbers, no "about")
- Decision: on the close of candle t. Execution: at the open of t+1.
- Entry rule, exit rule, position size, rebalancing band, how ties are broken.
- What happens when an instrument disappears (e.g. assume the position is sold at the last available close minus 10%; write your own number).

## 4. Costs
- Fee and slippage per side. A second full replay at DOUBLE costs is mandatory.

## 5. Success criteria (all must hold)
1. Profit still positive at double costs.
2. At least __ of __ equal time blocks positive.
3. Max drawdown not worse than __%.
4. No single asset gives more than __% of the positive profit.
5. Return at least __% and beats simple holds scaled by time invested.
6. At least __ trades.
Finalist rule: the best (profit at double costs / |max drawdown|); a drawdown of 0 is not eligible.

## 6. Attempts
How many runs are allowed (normally ONE). A crash after the marker (a small file you create right before the run, so everyone can see that the one allowed run has started) counts as used unless a documented implementation defect is found before looking at results.

## 7. Disclosures
What may bias this test (survivor list, ideas chosen after seeing history, thresholds not calibrated against a null model, ...).
