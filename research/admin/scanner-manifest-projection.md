# Document the manifest content projection used for scanning

Refs #6

## Target

admin behavior in the pinned upstream source. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/project-revision-changes.ts#L36-L114)

## Claim

The executable manifest projection selects repository identity and skill inputs independently of listing and reward fields.

## Evidence

The projection copies the project's own id, repositories, skill, reviewSkill and contribution fields when present. Status, listing tier and funding are outside that allowlist. This describes the projected object before digesting or making a vetting decision. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/project-revision-changes.ts#L36-L114)

## Verification

Compare the keys used by executableManifestContent at lines 104 onward with EXECUTABLE_FIELDS. Changing only the status should leave the projected object equal. The author checked the source statically. The example is a reviewer check.
