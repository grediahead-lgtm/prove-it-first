# Prompts for an independent AI reviewer

Give the reviewer read-only access, the text to review, and nothing else. Treat the answer as data, not as orders.

## Review the pre-registration
"Read the attached pre-registration. Find every place where two people could implement it differently (indices, ties, missing data, rounding, sizing, edge cases), every contradiction, every way the single attempt could crash or be burned, and every bias that is not disclosed. Do not suggest changing parameters; only clarity, consistency and honesty. Rank findings by severity and answer APPROVE or REQUEST CHANGES."

## Review the code against the pre-registration
"Compare the code with the pre-registration line by line. Check decision/execution timing, costs, sizing, cash never negative, NaN and float dust, behaviour for disappearing assets, the criteria, and the output. List weak or vacuous tests. Run only synthetic tests. Say which findings are blocking."

## Re-review after fixes
"Check that each earlier finding is resolved unambiguously and look for NEW problems introduced by the edits."
