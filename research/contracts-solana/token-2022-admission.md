# Document Solana escrow token admission

Refs #11

## Target

Upstream contracts-solana behavior in [the primary source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/contracts/solana/programs/slop-escrow/src/token_policy.rs#L13-L75) at commit 7dc83b504627c70eb6d1f0d1950b40aad3006bf8.

## Claim

The Solana escrow helpers apply explicit extension and authority checks to Token-2022 mints and accounts.

## Evidence

The mint helper accepts the classic SPL owner through its legacy branch. For Token-2022 it parses the mint, requires absent mint and freeze authorities and permits only metadata pointer and token metadata extensions without duplicates. Embedded token metadata must name the same mint. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/contracts/solana/programs/slop-escrow/src/token_policy.rs#L13-L75)

The account helper also has a classic SPL owner branch. A Token-2022 account must be initialized and can carry at most one extension, ImmutableOwner. These are the helper-level conditions. Instruction account constraints are outside the packet. [Supporting source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/contracts/solana/programs/slop-escrow/src/token_policy.rs#L77-L164)

## Verification

Read the mint and account branches independently. Compare a metadata-only Token-2022 mint with the fixture that restores an active authority, and inspect the separate account extension allowlist. This packet was verified by static source inspection. Upstream tests and live services were outside the verification.
