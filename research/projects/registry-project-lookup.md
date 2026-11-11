# Document project lookup across registry snapshots

Refs #1

## Target

Upstream projects behavior in [the primary source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/projects.mjs#L210-L237) at commit 7dc83b504627c70eb6d1f0d1950b40aad3006bf8.

## Claim

Project lookup separates current public identity from repository identity in the ingestion snapshot.

## Evidence

Public ID or slug lookup trims and lowercases its input, checks the ID map first, then scans slugs. Repository lookup lowercases a repository ID and uses the current registry map. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/projects.mjs#L210-L237)

The ingestion path uses a separate repository map built for the snapshot that collected the ledger. That map can include retired projects. This allows historical score events to resolve even if their project no longer appears in the current registry. [Supporting source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/projects.mjs#L1-L113)

## Verification

Compare the three exported lookup functions and their maps. Follow a repository ID present only in the ingestion map through both repository lookup functions and compare the returned values. This packet was verified by static source inspection. Upstream tests and live services were outside the verification.
