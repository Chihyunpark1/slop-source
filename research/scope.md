# SLOP Source — Scope Definition

The denominator for progress measurement. Established 2026-11-11 from live
on-chain data and the public slop.cash codebase
(`SlopDotCash/slopdotcash`, MIT).

## Target: the site's features

The reverse-engineering target is the slop.cash site's features — what the
platform does, end to end — not only the SLOP token. The token is one
component of the site.

## Feature areas (the denominator)

14 areas, grouped by domain from the public codebase.

| # | Area | What it covers |
|---|---|---|
| 1 | Projects | Proposals, leaderboard, setup, risk flags |
| 2 | Points | Points rules, disputes, earnings |
| 3 | Payouts & bounties | Direct, Solana, escrow, funding, monthly payments |
| 4 | Referrals | Referral claims and accrual |
| 5 | Security | Bounty program, private reports, vetting |
| 6 | Admin & operations | Admin pages, enforcement, operations |
| 7 | Identity & profiles | Accounts, profiles, inbox |
| 8 | Vaults & owner | Owner vault, reserve release, commitment, awards |
| 9 | Cycles & standings | Cycle pages, home standings |
| 10 | Contracts — EVM | EVM adapters, monthly reserve, native cost |
| 11 | Contracts — Solana | Anchor programs, commitment, funding, token extensions |
| 12 | Token (SLOP) | The SLOP token contract |
| 13 | Workers | 13 background workers (payments, vetting, notify, slopbot, …) |
| 14 | Notifications | Notification delivery |

The denominator is 14 areas. Current progress is tracked by the
maintainer and is not published.

## Component: SLOP token contract

Analyzed live on Robinhood Chain mainnet (chain ID 4663, public RPC
`https://rpc.mainnet.chain.robinhood.com`).

| Field | Value |
|---|---|
| Address | `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` |
| Name | Slop Cash |
| Symbol | SLOP |
| Decimals | 18 |
| Total supply | 100,000,000 SLOP (on-chain `totalSupply()`) |
| Owner | `0x96028de971a9d37404f5030f6284b40640e2d1a2` |
| Paused | false |
| Deployed bytecode | 2,732 bytes |
| Bytecode SHA-256 | `59e56b971f2b6a53b7a469aadf32ff5f48fc1330674fa872757c45518ff9e19e` |

### Source verification

Verified (partial match) on Blockscout, Nov 3, 2026. Contract name
`VentureToken`, compiler v0.8.26, EVM version cancun, optimization enabled
(200 runs), file `src/tokens/VentureToken.sol`.

### Function scope: 18 functions, all identified

`supportsInterface`, `name`, `approve`, `totalSupply`, `transferFrom`,
`decimals`, `unpause`, `mint`, `paused`, `balanceOf`, `renounceOwnership`,
`pause`, `owner`, `symbol`, `burn(address,uint256)`, `transfer`,
`allowance`, `transferOwnership`.

No claim or registration function exists in this contract — the
contributor claim/registration flow lives elsewhere (separate contract or
off-chain), and mapping it is a follow-on task.

## Evidence

- Bytecode: `research/slop-bytecode.hex` (fetched via `eth_getCode`, 2026-11-11)
- Chain ID confirmed `0x1237` (4663) before reading
- `totalSupply()`, `name()`, `symbol()`, `decimals()`, `owner()`,
  `paused()` read live via `eth_call`
- Verification status read from the Blockscout explorer page, 2026-11-11
- Site inventory from the public SLOPCASH codebase (MIT licensed)
