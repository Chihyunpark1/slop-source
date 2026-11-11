# SLOP Source

An open-source project for independently analyzing and reimplementing
SLOPCASH's public contracts and features — the way Hyperliquid-source
does it for Hyperliquid: anyone can submit a PR, and the work is filled
in little by little.

Verified implementations from this project are eventually integrated
into the REALSLOP (RSLOP) platform.

This is an independent, unofficial project. It is not affiliated with,
endorsed by, or connected to SlopDotCash or slop.cash, and it is not
the original SLOPCASH project.

## For AI Agents

AI agents (Codex, Claude Code, and others) can contribute. Read
[AGENTS.md](AGENTS.md), pick an open Issue, do the research with
evidence, and submit a PR.

Copy and paste this prompt to start:

```text
You are contributing to SLOP Source (https://github.com/Chihyunpark1/slop-source),
an open-source project that independently analyzes and reimplements
SLOPCASH's public contracts and features.

1. Read AGENTS.md in the repository.
2. Pick an open Issue from the 14 research areas.
3. Do the research using public materials only, with reproducible evidence.
4. Submit a PR with these sections: Target, Claim, Evidence, Verification.

Rules: do not copy source code verbatim. Do not fabricate findings.
Do not attack real systems. Do not collect confidential information.
Do not disclose the overall completion rate. The maintainer reviews and
merges every PR personally.
```

## Scope

The research scope covers all 14 feature areas of the SLOPCASH
platform — not only the SLOP token. See
[research/scope.md](research/scope.md) for the scope definition.

The following work is explicitly permitted in this project:

1. Public contract function and selector analysis.
2. On-chain data verification.
3. Platform architecture and behavior analysis.
4. Independently authored reimplementations based on public code.
5. Reproducible technical research reports.
6. Corrections and verification of existing research results.

A research-only PR does not need a bug reproduction, a defect fix, or
an unrelated code change. One target, one claim, and reproducible
evidence is enough. Every research PR must include Target, Claim,
Evidence, and Verification. See [CONTRIBUTING.md](CONTRIBUTING.md)
and [AGENTS.md](AGENTS.md) for the full instructions.

| Area | What it covers |
|---|---|
| Projects | Proposals, leaderboard, setup, risk flags |
| Points | Points rules, disputes, earnings |
| Payouts & bounties | Direct, Solana, escrow, funding, monthly payments |
| Referrals | Referral claims and accrual |
| Security | Bounty program, private reports, vetting |
| Admin & operations | Admin pages, enforcement, operations |
| Identity & profiles | Accounts, profiles, inbox |
| Vaults & owner | Owner vault, reserve release, commitment, awards |
| Cycles & standings | Cycle pages, home standings |
| Contracts — EVM | EVM adapters, monthly reserve, native cost |
| Contracts — Solana | Anchor programs, commitment, funding, token extensions |
| Token (SLOP) | The SLOP token contract |
| Workers | Background workers (payments, vetting, notify, slopbot, …) |
| Notifications | Notification delivery |

The SLOP token contract has been analyzed live: 18 functions
identified, contract `VentureToken` (verified, partial match),
total supply 100,000,000 SLOP. See
[research/scope.md](research/scope.md) for the evidence.

## What is public

- GitHub Issues, pull requests, commits, and merge history
- Contributor list and contribution history
- Analysis materials and independently written source code
- CONTRIBUTING.md and the PR writing guide
- Verification results for individual tasks

## What stays private

- Overall project completion rate (%)
- Per-feature integration progress inside the project
- The private development roadmap
- The REALSLOP platform's actual integration status
- Internal testing and deployment readiness

This README does not calculate or display an overall completion rate.
Note: anything that can be verified from the public PRs and code alone
cannot be hidden — the private items above are the ones that are not
published.

## How PRs are evaluated

PRs are evaluated by technical value, originality, reproducible
evidence, and verification level — not by count. A single deep,
well-evidenced packet counts more than many shallow ones.

Duplicate PRs and auto-generated low-quality PRs are not recognized for
reward purposes.

## How PRs work

Anyone can open an Issue and submit a PR. Every PR is reviewed and
merged personally by the repository administrator. There is no automatic
merging. See [CONTRIBUTING.md](CONTRIBUTING.md) for the submission and
review procedure.

Contribution records are transparent on GitHub: Issues, PRs, commits,
and merge history are all public.

## How this stays legally safe

- **Document behavior, not code.** We write down what each feature does,
  from observable behavior and the public codebase. We do not copy source
  code verbatim.
- **Independent reconstructions.** Anything we rebuild is written by us,
  in our own words and code. The code is not identical to the original.
- **Public sources only.** The platform code is MIT-licensed and public;
  the token bytecode is public on-chain. We use them as references.
- **Verified only.** An implementation is not called complete until it is
  verified. Unverified work is not presented as a finished feature.
- **No attacks, no confidential data.** Only legal analysis using public
  materials is allowed. Unauthorized attacks on real systems and the
  collection of confidential information are prohibited.

## REALSLOP (RSLOP)

This project exists because of REALSLOP's story.

### Origin

The contributor behind this project shipped hundreds of pull requests to the slop.cash ecosystem — bug fixes, research packets, and reviews across eliza, slopdotcash, pumpfun-source, and hyperliquid-source. When the SLOP contributor allocation list was published (PR #2488: 214 recipients, 2,000,000 SLOP total), his name was not on it.

So he shipped his own slop: **REALSLOP (RSLOP)**, a parody memecoin on Solana.

> "The contributor airdrop forgot. The top slop shipper, left off the 214-person list — so he shipped his own. Not affiliated with slop.cash. This is the real slop."

### Token

| Field | Value |
|---|---|
| Name | Real Slop |
| Ticker | RSLOP |
| Mint | `5hyubHsUEyAYBeD2AeUL34L9JKTvMPpSaxJY6w1hEvex` |
| Chain | Solana |
| Total supply | 1,000,000,000 |
| Decimals | 6 |
| Mint authority | Revoked |
| Freeze authority | Revoked |
| Metadata update authority | Creator wallet |
| Status | Live and tradeable |

The logo is the creator's own handwritten image — "걸어서 코인속으로" ("walking into crypto") — stored on Arweave via Irys. Metadata: https://gateway.irys.xyz/Es6R9Sy9F4sMc7HuVxgFPRXzULvtWue7k5xcCsBD3zg6

### Tokenomics

| Bucket | Share | Amount |
|---|---|---|
| Contributor airdrop | 30% | 300,000,000 |
| Liquidity pool (PumpSwap) | 70% | 700,000,000 |
| Developer pre-allocation | 0% | 0 |

There is no private owner allocation — the team/dev share is 0%. The
supply is earned by contributing, not held by an owner.

The airdrop wallet is `BKyNuXaWNdkg3XwZubdcLtXfzVPtT6dBBcnMcHKy1xMM`.

### Airdrop policy

The evaluation criteria are managed in a separate document:
[docs/airdrop-criteria.md](docs/airdrop-criteria.md).

- **Evaluation criteria:** contributor rewards are selected based on
  verified PRs and contribution history. The specific criteria are
  **not yet confirmed**.
- **Payment procedure:** not yet confirmed.
- **Selection results:** disclosed only when confirmed.

Nothing in this section is final until it is confirmed. Unconfirmed
items are marked as such and are not invented.

The liquidity pool is on PumpSwap: `5Fv54bu57GUJ47zqPBwyah3btKwpzFAytVrfnpMEVCu8` (RSLOP ~696.5M + WSOL ~0.0653 SOL). LP tokens (213.307) are held 100% by the creator wallet.

### Links

- Repository: https://github.com/Chihyunpark1/realslop
- Token: https://solscan.io/token/5hyubHsUEyAYBeD2AeUL34L9JKTvMPpSaxJY6w1hEvex
- Not affiliated with SlopDotCash or slop.cash.

## Get started

Clone it, pick a task from the scope, gather evidence, and open a PR.

New project work is MIT licensed; imported materials retain their original terms.

---

*Not affiliated with SlopDotCash or slop.cash. This is an independent, unofficial research project.*
