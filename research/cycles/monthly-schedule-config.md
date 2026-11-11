# Document automatic monthly schedule configuration

Refs #9

## Target

cycles behavior in the pinned upstream source. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/payments/monthly-allocation.ts#L29-L67)

## Claim

Automatic monthly scheduling is opt-in through a two-field configuration object with a positive integer offset.

## Evidence

An absent, null or empty value produces null. A supplied JSON string must have exactly firstPeriod and cutoffSecondsAfterPeriodEnd. The offset must be a positive safe integer and the first period must match the period pattern. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/payments/monthly-allocation.ts#L29-L67)

## Verification

Compare an empty string, the two-field configuration with offset 259200, and a configuration with offset zero. Expect null, a schedule, and an error. The author checked the source statically. The example is a reviewer check.
