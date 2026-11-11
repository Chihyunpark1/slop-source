# Document the referral accrual cutoff

Refs #4

## Target

Upstream referrals behavior in [the primary source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/referral-accrual/core.ts#L176-L190) at commit 7dc83b504627c70eb6d1f0d1950b40aad3006bf8.

## Claim

The referral accrual window ends at the same UTC time of day a configured number of calendar months after the first payout, clamping the day to the last day of the destination month when needed.

## Evidence

The helper advances the UTC calendar month while preserving the time of day. If the original day does not exist in the destination month, it uses that month's last day. January 31, 2027 at 10:00 UTC plus one month becomes February 28 at 10:00 UTC. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/referral-accrual/core.ts#L176-L190)

The accrual loop uses the earlier of the stored first-paid timestamp and the candidate timestamp to compute the cutoff. A candidate observed exactly at the cutoff gets the same window_closed outcome as a later candidate. [Supporting source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/referral-accrual/core.ts#L347-L367)

## Verification

Checked the month-end example and the February 29, 2028 plus 12 months example against the extracted upstream helper. Compare the caller's greater-than-or-equal check with the exact boundary. Full upstream test suites and live services were outside the verification.
