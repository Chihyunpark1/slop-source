# Token contract routes exactly the 18 identified functions; live state confirmed

## Target

SLOP token contract `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on
Robinhood Chain mainnet (chain ID 4663), public RPC
`https://rpc.mainnet.chain.robinhood.com`. This packet covers the whole
contract for Issue #12: the full function set in its dispatcher and its
read-only on-chain state. The deployed bytecode copy is in
`research/slop-bytecode.hex`.

## Claim

The live SLOP token contract routes exactly the 18 functions identified
in `research/scope.md` — no more, no fewer — and at block 111,669,550
its state read: name "Slop Cash", symbol SLOP, 18 decimals, total
supply 100,000,000 SLOP, owner
`0x96028de971a9d37404f5030f6284b40640e2d1a2`, not paused.

## Evidence

All on-chain values below were read directly from the public RPC on
2026-11-11 with `scripts/verify-token-state.py` (added by this packet);
the run printed `ALL CHECKS PASSED` at block 111,669,550.

1. **The live bytecode is the repo copy.** `eth_getCode` at block
   111,669,550 returned 2,732 bytes, byte-identical to
   `research/slop-bytecode.hex`, SHA-256
   `59e56b971f2b6a53b7a469aadf32ff5f48fc1330674fa872757c45518ff9e19e`.
   Chain ID was confirmed first: `eth_chainId` returned `0x1237`
   (4663).

2. **The dispatcher routes exactly 18 selectors.** Scanning the whole
   bytecode for the dispatcher pattern (`PUSH4` `0x63` + selector +
   `EQ` `0x14`, the same pattern `scripts/verify-selector.py` checks)
   finds exactly 18 entries, and each one is the keccak256 selector of
   an identified function:

   | Byte offset | Selector | Function |
   |---|---|---|
   | 26 | `0x01ffc9a7` | `supportsInterface(bytes4)` |
   | 38 | `0x06fdde03` | `name()` |
   | 49 | `0x095ea7b3` | `approve(address,uint256)` |
   | 60 | `0x18160ddd` | `totalSupply()` |
   | 71 | `0x23b872dd` | `transferFrom(address,address,uint256)` |
   | 82 | `0x313ce567` | `decimals()` |
   | 93 | `0x3f4ba83a` | `unpause()` |
   | 104 | `0x40c10f19` | `mint(address,uint256)` |
   | 115 | `0x5c975abb` | `paused()` |
   | 126 | `0x70a08231` | `balanceOf(address)` |
   | 137 | `0x715018a6` | `renounceOwnership()` |
   | 148 | `0x8456cb59` | `pause()` |
   | 159 | `0x8da5cb5b` | `owner()` |
   | 170 | `0x95d89b41` | `symbol()` |
   | 181 | `0x9dc29fac` | `burn(address,uint256)` |
   | 192 | `0xa9059cbb` | `transfer(address,uint256)` |
   | 203 | `0xdd62ed3e` | `allowance(address,address)` |
   | 213 | `0xf2fde38b` | `transferOwnership(address)` |

   There is no 19th routed selector anywhere in the bytecode.

3. **On-chain state (`eth_call`, block 111,669,550).**

   | Getter | Raw result (trimmed) | Decoded |
   |---|---|---|
   | `name()` | `…0009` + `536c6f702043617368` ("Slop Cash") | Slop Cash |
   | `symbol()` | `…0004` + `534c4f50` ("SLOP") | SLOP |
   | `decimals()` | `0x…12` | 18 |
   | `totalSupply()` | `0x00000000000000000000000000000000000000000052b7d2dcc80cd2e4000000` | 100,000,000 SLOP |
   | `owner()` | `0x00000000000000000000000096028de971a9d37404f5030f6284b40640e2d1a2` | `0x96028de971a9d37404f5030f6284b40640e2d1a2` |
   | `paused()` | `0x…00` | false |

4. **Read-function behavior probes (`eth_call`, same run).**
   `balanceOf(owner)` returned
   `0x00000000000000000000000000000000000000000012330266de195e76848b60`
   = 22,001,549.749567755 SLOP. `allowance(owner, owner)` returned 0.
   `supportsInterface(0x01ffc9a7)` returned true and
   `supportsInterface(0xffffffff)` returned false, as ERC-165 requires.

5. **No claim or registration function exists in this contract.**
   Because the dispatcher enumeration in (2) is complete — 18 routed
   selectors, all accounted for — there is no routed `claim` or
   `register` function. As a cross-check, the checker also computes the
   selectors of 11 claim/registration candidate signatures (`claim()`,
   `claim(address)`, `claim(uint256)`, `claimTokens()`,
   `claimAllocation()`, `claimReward()`, `claimRewards()`,
   `register()`, `register(address)`, `registerContributor()`,
   `registration()`) and confirms none of them is routed.
   `research/scope.md` records where the flow lives instead: "the
   contributor claim/registration flow lives elsewhere (separate
   contract or off-chain), and mapping it is a follow-on task."

6. **Source verification status.** Per the maintainer's record in
   `research/scope.md`: verified (partial match) on Blockscout,
   contract name `VentureToken`, compiler v0.8.26, EVM version cancun,
   optimization enabled (200 runs), file `src/tokens/VentureToken.sol`.
   This packet did not independently re-read that status: automated
   access to the explorer was answered with a bot check (HTTP 403)
   from this environment on 2026-11-11, so the status is carried from
   the repo's record, not freshly confirmed. The explorer page for the
   address is
   https://robinhoodchain.blockscout.com/address/0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE

## Verification

1. Full live check (bytecode set + state), a few minutes:
   `python3 scripts/verify-token-state.py`
   Expected: 18 `[ok]` selector lines, "no dispatcher selectors beyond
   the 18", "no claim/registration candidate selector is routed",
   chainId 4663, live bytecode identical to the repo copy, the six
   state values from Evidence (3), and `ALL CHECKS PASSED`. Observed
   exactly that at block 111,669,550 on 2026-11-11 (block and
   `balanceOf` move over time; the other values change only if the
   owner acts).
2. Offline check (no RPC):
   `python3 scripts/verify-token-state.py --offline`
   Expected: the same selector results against
   `research/slop-bytecode.hex` and `ALL CHECKS PASSED`.
3. Tests: `tests/test_verify_token_state.py` — 4 tests over the
   offline mode (exact-18 set, spot-check selectors, no
   claim/registration selector, bytecode SHA-256). All 4 passed when
   run for this packet, and the existing `tests/test_verify_selector.py`
   still passes (4/4). Run with `python3 -m pytest tests/` where
   pytest is available (the PR checks workflow installs it).
4. Spot check without the script: `eth_call` to `totalSupply()`
   (`0x18160ddd`) at the address above on the public RPC returns
   `100,000,000 * 10^18`.

## Notes

- State-changing functions (`transfer`, `approve`, `transferFrom`,
  `mint`, `burn`, `pause`, `unpause`, `transferOwnership`,
  `renounceOwnership`) were identified by selector and dispatcher
  routing, not executed; only read-only functions were called.
- Two selectors already have dedicated single-selector packets: `burn`
  (merged) and `transfer` (open PR #21). This packet does not repeat
  their per-selector analysis; it verifies the complete set and the
  live state for Issue #12.
- A holder-distribution listing is not included: enumerating holders
  needs an indexer or the explorer, and the explorer API was not
  reachable from this environment (see Evidence 6). The only balance
  figure claimed is the `balanceOf(owner)` probe in Evidence (4),
  read directly from the RPC.
- State values are a snapshot at block 111,669,550 (2026-11-11).
  `totalSupply` can change through `mint`/`burn`, and `paused`/`owner`
  through the owner's calls; re-run the checker to refresh them.
