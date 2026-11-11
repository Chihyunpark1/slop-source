# Document allocation revision folding

Refs #9

## Target

cycles behavior in the pinned upstream source. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/payments/monthly-allocation.ts#L110-L133)

## Claim

Monthly allocation folding preserves the original proposed gross value while the highest applied sequence supplies the effective gross value.

## Evidence

Base rows are copied into a map keyed by GitHub user ID. Changes are sorted by sequence and update the current gross amount. A change for an unknown recipient throws. The final rows are ordered by GitHub user ID. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/payments/monthly-allocation.ts#L110-L133)

## Verification

Start with gross 100 and supply sequence 2 at 80 before sequence 1 at 90. The result should report proposed gross 100 and current gross 80. The author checked the source statically. The example is a reviewer check.
