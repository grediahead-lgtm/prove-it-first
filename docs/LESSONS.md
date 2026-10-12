# Five ways a backtest lies (and the cheap fix for each)

1. **Luck from many tries (overfitting).** Give a hundred people a coin to flip ten times: one of them will look like a genius. Limit attempts, never change rules after seeing results.
2. **Peeking at the future.** A candle's close is known only after it closes. Decide on the closed candle, trade on the next open.
3. **Survivors only.** Today's top list hides the dead projects. Build the list as of the start date and book delistings honestly.
4. **Costs.** Fee plus slippage compound over hundreds of trades. Always run a doubled-cost replay.
5. **One period, one market.** A strategy that "sat out" one crash looks brilliant. Check several assets and periods, then confirm on new data.

Our own story: five ideas were run once each on three years of hourly data with pre-registered rules; none passed. That is a successful test, not a failed project: nothing was lost and we learned what does not work.
