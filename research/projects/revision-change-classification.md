# Document owner revision change classification

Refs #1

## Target

projects behavior in the pinned upstream source. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/project-revision-changes.ts#L18-L102)

## Claim

The revision classifier labels changed top-level fields according to their role and flags owner-fixed fields as restricted.

## Evidence

The classifier compares canonical JSON and visits the union of field names in sorted order. A headline change is presentation, a contribution change is executable and a funding change is financial. Repository identity is executable content but belongs to the owner-fixed set and is reported as restricted. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/project-revision-changes.ts#L18-L102)

## Verification

Compare two manifest-shaped objects that change headline, funding and repositories. The corresponding lists should contain headline, funding and repositories. The author checked the source statically. The example is a reviewer check.
