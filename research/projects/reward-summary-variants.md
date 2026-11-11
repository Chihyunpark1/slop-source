# Document reward summary display variants

Refs #1

## Target

projects behavior in the pinned upstream source. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/project-reward-summary.ts#L44-L104)

## Claim

The reward summary combines an eligible primary reward badge with a bounty badge when present, and falls back to points-only when neither applies.

## Evidence

External prizes use the advertised display amount. Otherwise a positive monthly cap yields a monthly badge unless the bounty is bounty-only. A bounty contributes its own amount, status and eligibility. The result is a display summary derived from the manifest. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/project-reward-summary.ts#L44-L104)

## Verification

Trace points-only, monthly plus bounty, and bounty-only fixtures through the branches. Compare the ordered kinds returned in each case. The author checked the source statically. The example is a reviewer check.
