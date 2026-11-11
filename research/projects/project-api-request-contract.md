# Document project API request and failure handling

Refs #1

## Target

projects behavior in the pinned upstream source. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/project-api.ts#L65-L95)

## Claim

The project API client sends same-origin JSON requests and converts transport failures into a structured project API error.

## Evidence

The request uses an explicit method, no-store caching and a same-origin credential policy. It attaches a JSON content type only when a body is supplied and an expected actor header only when the option is supplied. Transport failures use status zero and the network_error code, with timeout-specific text for abort or timeout errors. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/project-api.ts#L65-L95)

## Verification

Inspect request options for a GET without a body and a POST with a body. Compare the timeout and general failure branches in the catch block. The author checked the source statically. The example is a reviewer check.
