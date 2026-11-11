# Document vault amount parsing

Refs #8

## Target

vaults behavior in the pinned upstream source. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/payments/vault-amount.ts#L1-L19)

## Claim

The vault amount parser accepts positive decimal text only when it converts exactly to a positive uint128 amount.

## Evidence

It accepts an unsigned whole number with an optional fraction. The declared precision must be an integer from zero to 36, and a fraction longer than that precision is rejected. The conversion pads the fraction and uses integer arithmetic. Zero and amounts at or above 2^128 are rejected. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/payments/vault-amount.ts#L1-L19)

## Verification

With six decimals, compare 1.25, 0, and 0.0000001. The expected results are 1250000 base units and two rejections. The author checked the source statically. The example is a reviewer check.
