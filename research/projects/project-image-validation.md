# Document project image validation

Refs #1

## Target

projects behavior in the pinned upstream source. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/project-image.mjs#L1-L25)

## Claim

A project image must be a bounded inline WebP or JPEG data URL with matching byte markers.

## Evidence

The validator checks the media type, Base64 spelling and 16384-character limit before decoding. It checks RIFF and WEBP markers for WebP and the starting and ending markers for JPEG. These are byte-marker checks, so they do not establish that a full image decoder can read the payload. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/project-image.mjs#L1-L25)

## Verification

Compare a Base64 string containing the expected JPEG markers with the same payload declared as WebP. Trace both through the marker branches. The author checked the source statically. The example is a reviewer check.
