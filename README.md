# SLOP Source

A private reverse-engineering research project. Not published.

The purpose is to receive research PRs and measure the overall
reconstruction progress: how much of the slop.cash site's features have
been mapped, as a percentage.

## Target: the site's features

The target is what the slop.cash site does — its features, end to end.
The SLOP token contract is one component of it, not the whole target.

**Progress: 0/14 areas mapped (0%).** See
[research/scope.md](research/scope.md) for the scope definition.

| Area | Status |
|---|---|
| Projects | unmapped |
| Points | unmapped |
| Payouts & bounties | unmapped |
| Referrals | unmapped |
| Security | unmapped |
| Admin & operations | unmapped |
| Identity & profiles | unmapped |
| Vaults & owner | unmapped |
| Cycles & standings | unmapped |
| Contracts — EVM | unmapped |
| Contracts — Solana | unmapped |
| Token (SLOP) | scope identified |
| Workers | unmapped |
| Notifications | unmapped |

A feature counts as mapped only when a research packet documents its
behavior with evidence and is merged. The token's scope is identified
(18 functions, verified contract `VentureToken`); its behavior is not
yet mapped in depth.

## How this stays legally safe

- **Document behavior, not code.** We write down what each feature does,
  from observable behavior and the public codebase. We do not copy source
  code verbatim.
- **Independent reconstructions.** Anything we rebuild is written by us,
  in our own words and code.
- **Public sources only.** The platform code is MIT-licensed and public;
  the token bytecode is public on-chain. We use them as references.
- **Private.** Nothing here is published or shown to the public. This
  repository exists to collect PRs and track progress.

## Contribution and evidence requirements

See [CONTRIBUTING.md](CONTRIBUTING.md). In short:

- Every PR is a research packet: one target, one claim, evidence attached.
- No fabricated findings. If the evidence does not show it, say so.
- No verbatim copying of code. Reconstructions are independently authored.
- Every behavioral claim cites its source: the public codebase, an
  on-chain transaction, or observed behavior.
- The maintainer reviews and merges each PR personally. Merged packets
  move the progress percentage.

## REALSLOP (RSLOP)

This project exists because of REALSLOP's story.

### Origin

The contributor behind this project shipped hundreds of pull requests to the slop.cash ecosystem — bug fixes, research packets, and reviews across eliza, slopdotcash, pumpfun-source, and hyperliquid-source. When the SLOP contributor allocation list was published (PR #2488: 214 recipients, 2,000,000 SLOP total), his name was not on it.

So he shipped his own slop: **REALSLOP (RSLOP)**, a parody memecoin on Solana.

> "The contributor airdrop forgot. The top slop shipper, left off the 214-person list — so he shipped his own. Not affiliated with slop.cash. This is the real slop."

### Token

| | |
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

### Allocation

| Bucket | Share | Amount |
|---|---|---|
| Airdrop | 30% | 300,000,000 |
| Liquidity pool (PumpSwap) | 70% | 700,000,000 |
| Team / dev | 0% | 0 |

The airdrop wallet is `BKyNuXaWNdkg3XwZubdcLtXfzVPtT6dBBcnMcHKy1xMM`. The 30% airdrop goes to people who contribute by writing PRs. There is no private owner allocation — the team/dev share is 0%. The supply is earned by contributing, not held by an owner.

The liquidity pool is on PumpSwap: `5Fv54bu57GUJ47zqPBwyah3btKwpzFAytVrfnpMEVCu8` (RSLOP ~696.5M + WSOL ~0.0653 SOL). LP tokens (213.307) are held 100% by the creator wallet.

### Links

- Repository: https://github.com/Chihyunpark1/realslop
- Token: https://solscan.io/token/5hyubHsUEyAYBeD2AeUL34L9JKTvMPpSaxJY6w1hEvex
- Not affiliated with SlopDotCash or slop.cash.

## Get started

This is a private repository. Collaborators clone it, pick a task from
the scope, gather evidence, and open a PR.

New project work is MIT licensed; imported materials retain their original terms.

---

*Not affiliated with SlopDotCash or slop.cash. This is an independent, private research project.*
