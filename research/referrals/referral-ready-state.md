# Document ready-state requirements in referral responses

Refs #4

## Target

referrals behavior in the pinned upstream source. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/referral-claims.ts#L61-L124)

## Claim

The referral response parser requires program data, timestamps and all three balance figures before accepting a ready account.

## Evidence

The disabled result returns an enabled false marker. Enabled payloads must have a recognized status and valid scalar fields. The additional ready-state check requires the program, observation and finalized times, and non-null claimed, claimable and pending balances. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/referral-claims.ts#L61-L124)

## Verification

Start with a valid ready fixture and replace claimedBase with null. The ready-state condition should reject it even though the earlier scalar check allows null. The author checked the source statically. The example is a reviewer check.
