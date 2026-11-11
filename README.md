# SLOP Source

100% focused on the SLOP token — an independent, open-source reverse-engineering reconstruction.

Progress · Target · Source availability · Get started · Task queue

The goal is a public, evidence-backed reconstruction of the SLOP token's on-chain behavior: what the deployed contract does, how claims and registration work, and how the contributor allocation is actually enforced. The platform's own code is already open source; this project maps what the chain says.

## Progress

SLOP token progress: work starting.

- **0 research work items** registered so far. The scope below is the starting point, not a result.
- **0 components** mapped, **0** reconstructed, **0** gates accepted.

These counts are honest starting points. They grow only when a PR lands with evidence.

### Target contract

| | |
|---|---|
| Token | SLOP |
| Address | `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` |
| Chain | robinhood-mainnet |
| Decimals | 18 |
| Contributor allocation | 2,000,000 SLOP across 214 recipients |
| Registration closes | 2027-02-08 |

The deployed bytecode is public. The first research task is to establish its identity: bytecode hash, whether verified source exists, and which functions the token actually exposes.

## Target: the SLOP token

The SLOP token contract is the only reconstruction target. All active research, implementations, tests and PRs must advance this artifact.

- **Token behavior**: transfer, approval, and any non-standard functions the deployed bytecode contains.
- **Claim and registration**: how a contributor registers, what the contract checks, and when a claim can be made.
- **Allocation enforcement**: how the 2,000,000 SLOP contributor allocation is held and released, and what stops it from being spent another way.
- **Platform surface**: the on-chain calls the slop.cash platform makes, and what they prove about the token.

100% focus does not mean 100% completion. A full behavioral map, an independently authored reconstruction, and whole-contract identity remain open acceptance requirements.

## Public source and private changes

The platform is public. The deployed contract is a separate question.

- **Reuse public code**: the slop.cash platform is open source under the MIT license. Match its exact revision and license terms instead of reinventing it.
- **Recover deployed behavior**: the token bytecode is public on-chain. Its contents establish behavior, not intent. Public upstream code alone does not establish what the deployed contract does.
- **Reconstruct contract logic**: claim, registration, and allocation behavior need independently authored implementations and documentation. New implementation must be independently authored or reused under an applicable source license; inferred unlicensed code cannot be copied.

That is why deployed-bytecode findings are reported separately from component completion. They validate observed behavior; they do not finish the reconstruction.

## Next delivery milestones

1. Establish the deployed contract's exact bytecode identity and source availability.
2. Map the claim and registration flow end to end, with on-chain evidence for each step.
3. Document the allocation logic: who can move the 2,000,000 SLOP, when, and under what checks.
4. Deliver an independently authored reconstruction of the token's core behavior, with tests against observed on-chain data.

## Contribution and evidence requirements

See [CONTRIBUTING.md](CONTRIBUTING.md). In short:

- Every PR is a research packet: one target, one claim, evidence attached.
- No fabricated findings. If the chain does not show it, say so.
- No verbatim copying of proprietary code. Reconstructions are independently authored.
- Every behavioral claim cites its on-chain source: transaction, block, or contract call.

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

The airdrop wallet is `BKyNuXaWNdkg3XwZubdcLtXfzVPtT6dBBcnMcHKy1xMM` — recipients are selected by the creator.

The liquidity pool is on PumpSwap: `5Fv54bu57GUJ47zqPBwyah3btKwpzFAytVrfnpMEVCu8` (RSLOP ~696.5M + WSOL ~0.0653 SOL). LP tokens (213.307) are held 100% by the creator wallet.

### Links

- Repository: https://github.com/Chihyunpark1/realslop
- Token: https://solscan.io/token/5hyubHsUEyAYBeD2AeUL34L9JKTvMPpSaxJY6w1hEvex
- Not affiliated with SlopDotCash or slop.cash.

## Get started

Prerequisites: Git, Python 3.10+, and a way to read the chain (a public RPC endpoint for robinhood-mainnet).

```sh
git clone https://github.com/Chihyunpark1/slop-source.git
cd slop-source
```

Then pick an open task from the task queue, gather the evidence, and open a PR.

New project work is MIT licensed; imported materials retain their original terms.

---

*Not affiliated with SlopDotCash or slop.cash. This is an independent research project.*
