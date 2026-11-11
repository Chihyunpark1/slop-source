# Document escrow policy matching for archived proposals

Refs #8

## Target

vaults behavior in the pinned upstream source. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/payments/escrow-review.ts#L105-L128)

## Claim

The historical escrow financial-policy check requires the current and archived records to agree on five selected escrow fields.

## Evidence

Both project definitions must contain escrow settings. The comparison covers chain, effective cycle, fee mode, payout fee basis points and withdrawal fee basis points. The helper throws when any selected field differs. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/payments/escrow-review.ts#L105-L128)

## Verification

Compare identical escrow objects and then change only withdrawalFeeBasisPoints in the current record. The changed case should throw. The author checked the source statically. The example is a reviewer check.
