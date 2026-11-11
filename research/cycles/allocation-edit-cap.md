# Document the monthly allocation edit cap

Refs #9

## Target

cycles behavior in the pinned upstream source. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/payments/monthly-allocation.ts#L139-L177)

## Claim

The allocation edit validator checks the total after replacing the target recipient's amount with the proposed amount.

## Evidence

The change must identify an existing recipient and supply canonical base units. The editor cannot change their own allocation. An excluded recipient may be assigned zero but no positive amount. The validator sums the proposed replacement and every other current amount and rejects totals above the cap. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/payments/monthly-allocation.ts#L139-L177)

## Verification

For allocations of 60 and 40 and a cap of 100, propose changing the second to 41 and then to 39. With an otherwise permitted editor, the first fails and the second passes. The author checked the source statically. The example is a reviewer check.
