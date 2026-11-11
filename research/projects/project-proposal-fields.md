# Document the project proposal form and its validation

Refs #16

## Target

The public Add a project wizard at upstream commit 7dc83b504627c70eb6d1f0d1950b40aad3006bf8.

## Claim

The wizard requires repository identity and four listing fields for a points-only proposal, then adds validation according to the chosen funding and saved legal terms.

## Evidence

| Label or field | Requirement and validation |
| --- | --- |
| GitHub repository | Required. Expects owner/repository and a successful lookup of repository and steward identifiers. If license metadata is present, the SPDX identifier, commit SHA and file digest must all be valid. |
| Integration branch | Required. Selected from discovered branches and checked as a Git branch name. Private bounty mode also requires a verified source commit. |
| Project image | Optional. The image control receives the steward login and the draft image. |
| Project name | Required. 2–80 characters. |
| Short description | Required. 8–120 characters. |
| Goal | Required. 24–600 characters. |
| Acceptance criteria | Required. 6–2,000 characters, with a minimum of 12 trimmed characters for a private bounty. |
| Tests and additional contribution rules | Optional. Blank entries defer to the repository. Nonblank entries accept up to 2,000 characters. Private bounty testing text, if supplied, needs at least 12 trimmed characters. |
| Allow Slopbot to close Slop-skill PRs | Optional checkbox. Hidden in private bounty mode. |
| Reward type | Points only, Monthly rewards or Private bounty. Points only needs no funding details. |
| Network, asset and amount | Required in either paid mode. The network must be supported and the amount must pass the asset-aware amount parser. Custom tokens require a valid address and symbol. The non-custom-token bounty amount must be divisible by four in minor units. |
| Copyright model and exact legal copyright holder | The holder is required for sponsor-owned copyright and must be 2–240 characters. The validator disallows sponsor-owned copyright for a DAO steward. |
| Inbound contribution terms | A mode other than unknown requires a repository-matching immutable GitHub blob URL, 40-character commit SHA, 64-character SHA-256, version of 1–80 characters and acceptance mechanism of 1–240 characters. |
| Assignment assignee, signed instrument URL, instrument SHA-256, instrument version, signed at | Required for sponsor-owned copyright or assignment mode. Assignee is 2–240 characters, URL must be HTTPS, digest is 64 characters, version is 1–80 characters and the signing date/time must be present. |

[Validation function](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/ProjectProposalPage.tsx#L211-L341) · [Reward controls](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/ProjectProposalPage.tsx#L638-L744) · [Wizard and legal controls](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/ProjectProposalPage.tsx#L1440-L1685) · [Shared field components](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/ProjectFormFields.tsx)

## Verification

At the pinned commit, compare the rendered controls with the branches of proposalErrors. Check the repository lookup and the funding and legal conditionals before treating a field as universally required. Verified by static source inspection. No proposal was submitted.
