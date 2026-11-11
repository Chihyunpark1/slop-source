# Document the closed-cycle evidence gate

Refs #9

## Target

Upstream cycles behavior in [the primary source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/reward-cycle.ts#L164-L200) at commit 7dc83b504627c70eb6d1f0d1950b40aad3006bf8.

## Claim

A reward proposal requires a closed calendar window backed by complete verification coverage.

## Evidence

The window starts at the later of the calendar start and the project's reward start and ends at the calendar boundary. The validator requires that exact view window, closed status and a generation timestamp at or after the boundary. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/reward-cycle.ts#L164-L200)

The snapshot's verification window must equal its declared window and its evidence status must be complete. The source digest field must contain 64 lowercase hexadecimal characters. The digest check here is a format check. [Supporting source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/reward-cycle.ts#L202-L234)

## Verification

Read ensureCompleteCycle and trace its caller. Compare a generation timestamp one millisecond before close with the timestamp exactly at close, keeping the other inputs valid. Only the latter clears the time check. This packet was verified by static source inspection. Upstream tests and live services were outside the verification.
