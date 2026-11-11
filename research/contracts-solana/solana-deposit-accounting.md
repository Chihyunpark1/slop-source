# Document Solana escrow deposit accounting

Refs #11

## Target

Upstream contracts-solana behavior in [the primary source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/contracts/solana/programs/slop-escrow/src/lib.rs#L254-L276) at commit 7dc83b504627c70eb6d1f0d1950b40aad3006bf8.

## Claim

Both Solana deposit instructions increment the same cumulative deposited counter after a successful transfer and emit the same event type.

## Evidence

The token instruction rejects zero, uses a checked transfer with the mint's decimals, and adds the transferred amount to project.deposited. It emits a Deposited event with the project, depositor and amount. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/contracts/solana/programs/slop-escrow/src/lib.rs#L254-L276)

The native instruction also rejects zero, checks the vault including its rent reserve, and uses a system-program lamport transfer. The subsequent counter update and event fields match the token instruction. [Supporting source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/contracts/solana/programs/slop-escrow/src/lib.rs#L277-L298)

## Verification

Compared instruction order, counter targets and event payloads in the two source ranges. Each transfer precedes the counter update. No transaction was sent. Full upstream test suites and live services were outside the verification.
