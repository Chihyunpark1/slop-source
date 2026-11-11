# Document capability handling for funded paused projects

Refs #1

## Target

projects behavior in the pinned upstream source. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/project-capabilities.mjs#L24-L72)

## Claim

A registered, paused project can retain the project-level ability to execute approved payments if its vault is funded.

## Evidence

The evaluator rejects contributor work when project status differs from active. The payment branch checks registration and funding independently. Its result is a project-level flag and individual payment approval and destination checks remain separate. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/project-capabilities.mjs#L24-L72)

## Verification

Evaluate registered true, paused status, clear restrictions and funded funding. The contributor-work flag should be false and the approved-payment flag true. The author checked the source statically. The example is a reviewer check.
