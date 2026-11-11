# AGENTS.md — Instructions for AI Agents

This file tells an AI agent (Codex, Claude Code, or any other) how to
contribute to SLOP Source. If you received this repository link, start
here.

## What this project is

SLOP Source is an open-source project that independently analyzes and
reimplements SLOPCASH's public contracts and features. The model is
Hyperliquid-source: contributors submit research PRs, and the work is
filled in little by little. Verified implementations are eventually
integrated into the REALSLOP (RSLOP) platform.

This is an independent, unofficial project. It is not affiliated with,
endorsed by, or connected to SlopDotCash or slop.cash.

## How to contribute

1. **Read the docs.** Start with `README.md`, then
   `CONTRIBUTING.md`, then `research/scope.md` for the 14 research
   areas.
2. **Pick an Issue.** Open Issues list the research tasks. Issues labeled
   `good first issue` are suitable for a first contribution. Do not start
   work that duplicates an open Issue or an open PR.
3. **Do the research.** Use public materials only: the public SLOPCASH
   codebase (MIT licensed) and public on-chain data. Gather reproducible
   evidence for every claim.
4. **Submit a PR.** One PR, one target, one claim. Use the PR template.
   Every PR must have these four sections: Target, Claim, Evidence,
   Verification.

## Rules

- **No fabrication.** If the evidence does not show it, say so. An honest
  "not found" beats an invented finding.
- **No verbatim copying.** Reconstructions are independently authored. Do
  not paste source code from the original project.
- **Cite everything.** A behavioral claim without a source does not merge.
- **One packet, one claim.** A PR that tries to prove five things proves
  none of them.
- **Small and checkable.** A reviewer should be able to re-run your
  evidence in minutes.
- **Unverified is not complete.** Do not present unverified work as a
  finished feature.
- **Public materials only.** Do not attack real systems without
  authorization. Do not collect confidential information.
- **Do not disclose progress.** The overall completion rate and the
  internal integration progress are not published. Do not add them to
  any file, PR, or comment.
- **Do not merge.** The repository maintainer reviews and merges every PR
  personally. Never merge your own PR or anyone else's.

## PR format

Every PR body must contain these four sections:

- **Target:** the exact contract, function, or site feature studied.
- **Claim:** one sentence stating what the evidence shows.
- **Evidence:** the source for every claim — the public codebase, an
  on-chain transaction hash, block number, contract call, RPC output, or
  observed behavior. Link it or paste it.
- **Verification:** how the claim can be checked again, and what you
  actually checked.

## How PRs are evaluated

PRs are evaluated by technical value, originality, reproducible
evidence, and verification level — not by count. Duplicate PRs and
auto-generated low-quality PRs are not recognized for reward purposes.

## Where things go

- `research/` — research packets and evidence, organized by area.
- `src/` — independently authored reconstruction code.
- `tests/` — tests for the reconstruction code.
- `contributors.json` — contributor PR and verification records,
  updated by the maintainer on merge. Do not edit it in a research PR.
- `docs/airdrop-criteria.md` — the airdrop evaluation criteria policy.
  The criteria are not yet confirmed; do not invent them.
