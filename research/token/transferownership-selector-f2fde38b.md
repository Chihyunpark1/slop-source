# Selector f2fde38b is transferOwnership(address)

## Target

SLOP token contract `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on
Robinhood Chain mainnet (chain ID 4663). The deployed bytecode is in
`research/slop-bytecode.hex`. This packet identifies one function
selector in that contract's dispatcher.

## Claim

The function selector `f2fde38b` in the SLOP token dispatcher is
`transferOwnership(address)`.

## Evidence

1. **keccak256 of the signature.** The first four bytes of
   `keccak256("transferOwnership(address)")` are `f2fde38b`:

   ```text
   keccak256("transferOwnership(address)")
     = f2fde38b092330466c661fc723d5289b90272a3e580e3187d1d7ef788506c557
   selector = 0xf2fde38b
   ```

2. **The selector is in the deployed bytecode.** `f2fde38b` appears
   exactly once in `research/slop-bytecode.hex`, at byte offset 214,
   in the dispatcher pattern `PUSH4` (`0x63`) + selector + `EQ`
   (`0x14`):

   ```text
   ... 63a9059cbb146101cf578063dd62ed3e1461017f5763f2fde38b146100e2575f80fd5b3461017b ...
                                                   ^^^^^^^^^^
                                                   PUSH4 f2fde38b, EQ
   ```

   The surrounding bytes show the dispatcher comparing the incoming
   call data against this selector, right after the `allowance`
   selector (`63 dd62ed3e`). It is the last entry in the dispatcher:
   after its `EQ` + `JUMPI` (`6100e2`) the fallback bytes
   `5f 80 fd 5b` follow, and no further `PUSH4` selector appears in
   the bytecode.

3. **The contract is live.** At block 111,538,360 (2026-11-11),
   `totalSupply()` (selector `0x18160ddd`) returned
   `0x00000000000000000000000000000000000000000052b7d2dcc80cd2e4000000`
   = 100,000,000 SLOP, confirming the contract at this address is the
   live SLOP token.

## Verification

To re-check this claim:

1. Recompute the selector:
   `keccak256("transferOwnership(address)")` and take the
   first 4 bytes. Expected: `f2fde38b`.
2. Search the deployed bytecode for `f2fde38b`:
   `grep -o f2fde38b research/slop-bytecode.hex` — expect exactly one
   match, preceded by `63` (PUSH4) and followed by `14` (EQ).
3. Run the repo checker:
   `python3 scripts/verify-selector.py --bytecode
   research/slop-bytecode.hex 'transferOwnership(address)'`
   — expect "found at byte offset 214".
4. Confirm the contract is live at
   `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on Robinhood Chain
   (public RPC `https://rpc.mainnet.chain.robinhood.com`):
   `eth_call` to `totalSupply()` (`0x18160ddd`) returns
   `100,000,000 * 10^18`.

## Notes

- `transferOwnership` is a state-changing function, so it cannot be called
  with `eth_call` to observe its behavior. This packet identifies the
  selector only; it does not claim anything about who can call
  `transferOwnership` or what it does when called.
- This packet covers one selector only. The other 10 functions are not
  covered here. `burn` (`9dc29fac`), `transfer` (`a9059cbb`),
  `supportsInterface` (`01ffc9a7`), `name` (`06fdde03`), `approve`
  (`095ea7b3`), `totalSupply` (`18160ddd`), and `transferFrom`
  (`23b872dd`) were verified in previous packets.
