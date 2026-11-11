# Document referral accrual period selection

Refs #4

## Target

Upstream referrals behavior in [the primary source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/referral-accrual/core.ts#L147-L174) at commit 7dc83b504627c70eb6d1f0d1950b40aad3006bf8.

## Claim

The referral worker enumerates closed UTC months in chronological order from the first configured month or the month after the last filing.

## Evidence

The period helpers calculate the start and end as UTC midnight on the first day of the relevant months. pendingPeriods begins with the configured first period for an empty filing list or advances from the last entry of a nonempty list. It includes a month once its end timestamp is at or before the current instant. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/referral-accrual/core.ts#L147-L174)

The accrual runner passes the stored filing list into that helper and processes candidates for each returned period in order. The helper uses the last array entry as a cursor, so its input represents a chronological filing sequence. [Supporting source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/workers/referral-accrual/core.ts#L540-L557)

## Verification

Executed the three extracted upstream calendar helpers against a December rollover. With December 2026 configured and no filings, January 1 at 00:00 UTC includes December. One millisecond earlier yields no periods. With December already filed, the same instant yields no pending period. Full upstream test suites and live services were outside the verification.
