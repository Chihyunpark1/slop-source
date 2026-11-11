# Document the global score archive boundary

Refs #9

## Target

cycles behavior in the pinned upstream source. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/global-leaderboard.ts#L70-L154)

## Claim

An archived project-month supplies its recorded score while the live ledger and penalty rows contribute only for unarchived project-months.

## Evidence

The open-month helper builds keys from cycle index project and month pairs. It filters events before the project reward start and excludes rows whose project-month is already archived. The global aggregator adds recorded archive scores before adding open events and subtracting open deductions. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/global-leaderboard.ts#L70-L154)

## Verification

Trace one archived project-month and one adjacent open month. A new penalty in the archived month is filtered out of open deductions, while the open month remains eligible for deduction. The author checked the source statically. The example is a reviewer check.
