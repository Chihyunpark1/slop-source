# Document home and community listing eligibility

Refs #1

## Target

projects behavior in the pinned upstream source. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/home-projects.ts#L1-L28)

## Claim

The discovery helpers filter projects by placement, active status and, for bounty-only projects, an open bounty.

## Evidence

Both lists require active status. The home helper selects featured projects while the community helper selects community projects. A bounty-only overview requires an open bounty. Other bounty modes do not add this discovery restriction. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/home-projects.ts#L1-L28)

## Verification

Trace a featured, active project with a closed bounty through both reward modes. Only the bounty-only mode causes the open-project check to reject it. The author checked the source statically. The example is a reviewer check.
