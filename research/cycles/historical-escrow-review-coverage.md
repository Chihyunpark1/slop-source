# Document historical escrow review coverage

Refs #9

## Target

cycles behavior in the pinned upstream source. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/payments/escrow-review.ts#L42-L103)

## Claim

A historical decision file must identify the exact proposal digest and contain one valid decision per proposed recipient.

## Evidence

The validator checks schema, digest and row count, then rejects unknown or repeated actor IDs. Held and excluded rows must carry zero approved gross. Changes to proposed amounts need a reason, and the total approved amount cannot exceed the proposal cap. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/payments/escrow-review.ts#L42-L103)

## Verification

For a proposal with actors A and B, compare a two-row decision file for A and B with one for A twice. Equal row counts alone cannot satisfy coverage. The author checked the source statically. The example is a reviewer check.
