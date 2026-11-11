# Document exact display formatting for payment amounts

Refs #3

## Target

payouts behavior in the pinned upstream source. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/base-units.mjs#L1-L26)

## Claim

The base-unit formatter renders decimal text using integer division and remainder without rounding through floating point.

## Evidence

The input must be canonical unsigned integer text. Precision must be an integer between zero and 36. Fractional digits are left-padded to the declared precision and trailing zeros are removed. The whole part gets optional comma grouping. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/base-units.mjs#L1-L26)

## Verification

Format 1234500000 base units with six decimals. The expected default display is 1,234.5 and disabling grouping gives 1234.5. The author checked the source statically. The example is a reviewer check.
