# Document review budget rounding

Refs #9

## Target

Upstream cycles behavior in [the primary source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/reward-cycle.ts#L83-L136) at commit 7dc83b504627c70eb6d1f0d1950b40aad3006bf8.

## Claim

The review budget allocator distributes a positive budget among positive weights in whole minor units using largest remainder and actor ID as the tie-breaker.

## Evidence

The allocator validates nonnegative safe-integer weights, unique nonempty actor IDs and a nonnegative budget. It filters out zero weights and uses bigint multiplication, division and remainder to floor each proportional share. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/reward-cycle.ts#L83-L136)

It awards leftover units in descending remainder order, using the actor ID comparison for equal remainders. For a budget of five units and actors A and B with one weight each, the floor shares are two each and A receives the last unit. [Supporting source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/reward-cycle.ts#L83-L136)

## Verification

Ran the extracted upstream function with the five-unit tie in both input orders, and checked zero weights and duplicate actor IDs. The tie gave A three and B two units in both orders. Full upstream test suites and live services were outside the verification.
