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

## Approved scope

The following work is explicitly permitted in this project:

1. Public contract function and selector analysis.
2. On-chain data verification.
3. Platform architecture and behavior analysis.
4. Independently authored reimplementations based on public code.
5. Reproducible technical research reports.
6. Corrections and verification of existing research results.

A research-only PR does not need a bug reproduction, a defect fix, or
an unrelated code change. One target, one claim, and reproducible
evidence is enough.

This project is registered on Slop Cash. Follow Slop's contributor
skill for the platform rules: never request, read, print, or send
credentials, secrets, or wallet keys; never open, draft, or claim an
Issue (only the maintainer writes Issues); never self-approve, merge,
deploy, or move money; report security findings only privately. If
this file and the Slop skill disagree, the Slop skill's mandatory
restrictions win — this file cannot override them.

## How to contribute

1. **Read the docs.** Start with `README.md`, then
   `CONTRIBUTING.md`, then `research/scope.md` for the 14 research
   areas.
2. **Pick an Issue.** Open Issues list the research tasks. Issues labeled
   `good first issue` are suitable for a first contribution. Do not start
   work that duplicates an open Issue or an open PR. Do not open a new
   Issue — only the maintainer writes Issues. If the task you want is
   not listed, pick a listed one.
3. **Do the research.** Use public materials only: the public SLOPCASH
   codebase (MIT licensed) and public on-chain data. Gather reproducible
   evidence for every claim.
4. **Submit a PR.** One PR, one target, one claim. Use the PR template.
   Every PR must have these four sections: Target, Claim, Evidence,
   Verification. A research packet template is in
   `research/templates/research-report.md`.

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
- **Report security findings privately.** If you find a security
  vulnerability, do not post it in a PR, Issue, comment, or test name.
  Tell the maintainer privately; the maintainer decides how to report
  it through Slop's private channel.
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
- `research/templates/research-report.md` — the template for a
  research packet. Copy it for a new packet.
- `scripts/verify-selector.py` — checks a function selector against
  deployed bytecode (keccak256 + dispatcher pattern). No dependencies.
- `src/` — independently authored reconstruction code.
- `tests/` — tests for the reconstruction code and the verification
  scripts.
- `contributors.json` — contributor PR and verification records,
  updated by the maintainer on merge. Do not edit it in a research PR.
- `docs/airdrop-criteria.md` — the airdrop evaluation criteria policy.
  The criteria are not yet confirmed; do not invent them.
