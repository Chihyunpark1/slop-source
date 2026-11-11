# Contributing to SLOP Source

Every contribution is a research packet submitted as a pull request. One PR, one target, one claim, evidence attached.

## What a packet contains

- **Target**: the exact contract address, function, or behavior being studied.
- **Claim**: one sentence stating what the evidence shows.
- **Evidence**: the on-chain source for every claim — transaction hash, block number, contract call, or RPC output. Link it or paste it.
- **Files**: the reconstruction, notes, or tests your packet adds, under a clear path.

## Rules

1. **No fabrication.** If the chain does not show it, say so. An honest "not found" beats an invented finding.
2. **No verbatim copying.** Reconstructions are independently authored. Do not paste proprietary code.
3. **Cite everything.** A behavioral claim without an on-chain source does not merge.
4. **One packet, one claim.** A PR that tries to prove five things proves none of them.
5. **Small and checkable.** A reviewer should be able to re-run your evidence in minutes.

## How to submit

1. Fork the repo and create a branch named after your packet, e.g. `slop/claim-flow-001`.
2. Add your files and open a PR against `main`.
3. In the PR body, fill in: target, claim, evidence, and what you checked.
4. Wait for review. Address comments by updating the same PR, not by opening a new one.

## What does not merge

- Packets without evidence.
- Packets that copy code instead of reconstructing it.
- Packets that claim a finding the cited source does not support.
- Packets about anything other than the SLOP token target.
