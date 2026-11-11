# Document published registry snapshot validation

Refs #1

## Target

projects behavior in the pinned upstream source. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/project-registry-boot.ts#L73-L107)

## Claim

The browser accepts a published registry snapshot only with schema version 1, a parseable sync timestamp and a nonempty project array.

## Evidence

The published snapshot reader fetches the build snapshot path and reads bounded JSON. It rejects unsuccessful HTTP status and invalid metadata, then returns the project array and sync timestamp together. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/project-registry-boot.ts#L73-L107)

## Verification

Compare two otherwise identical responses with one project and with an empty project array. Only the nonempty response meets the published snapshot check. The author checked the source statically. The example is a reviewer check.
