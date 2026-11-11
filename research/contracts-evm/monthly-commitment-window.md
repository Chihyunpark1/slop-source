# Document the EVM monthly commitment window

Refs #10

## Target

Upstream contracts-evm behavior in [the primary source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/contracts/evm/src/ProjectEscrow.sol#L390-L412) at commit 7dc83b504627c70eb6d1f0d1950b40aad3006bf8.

## Claim

The EVM escrow accepts monthly commitment and reservation creation in a half-open UTC window from the fourth of the next month to the fourth of the month after that.

## Evidence

The calendar helper splits a YYYYMM value, validates year and month, and advances across December explicitly. Both endpoints are midnight UTC on the relevant first day plus 72 hours. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/contracts/evm/src/ProjectEscrow.sol#L390-L412)

The commitment and reservation entry points reject timestamps before the opening and at or after the closing time. For the period 202612, the time gate therefore admits January 4, 2027 at 00:00 UTC and rejects February 4 at 00:00 UTC. Other entry-point checks still apply. [Supporting source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/contracts/evm/test/MonthlyCommitment.t.sol#L165-L183)

## Verification

Compare the December fixture with the calendar helper, then compare the time predicates at lines 528–529 and 571–572 of ProjectEscrow.sol. This packet was verified by static source inspection. Upstream tests and live services were outside the verification.
