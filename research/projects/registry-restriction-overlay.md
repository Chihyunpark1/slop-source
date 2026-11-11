# Document the browser registry restriction overlay

Refs #1

## Target

projects behavior in the pinned upstream source. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/project-registry-boot.ts#L28-L71)

## Claim

The live registry loader displays a project named in the restriction list as paused and retired before its matching revision arrives.

## Evidence

The loader checks the response schema and requires arrays for projects and restrictions, treating absent restrictions as empty for compatibility. It builds a set of project IDs from restriction rows. Matching project records are copied with paused status and retired listing tier. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/project-registry-boot.ts#L28-L71)

## Verification

Trace a registry with two active projects and a single restriction matching one ID. Only that returned record should have the overridden state. The author checked the source statically. The example is a reviewer check.
