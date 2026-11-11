# Selector 313ce567 is decimals()

## Target

SLOP token contract `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on
Robinhood Chain mainnet (chain ID 4663). The deployed bytecode is in
`research/slop-bytecode.hex`. This packet identifies one function
selector in that contract's dispatcher.

## Claim

The function selector `313ce567` in the SLOP token dispatcher is
`decimals()`.

## Evidence

1. **keccak256 of the signature.** The first four bytes of
   `keccak256("decimals()")` are `313ce567`:

   ```text
   keccak256("decimals()")
     = 313ce567add4d438edf58b94ff345d7d38c45b17dfc0f947988d7819dca364f9
   selector = 0x313ce567
   ```

2. **The selector is in the deployed bytecode.** `313ce567` appears
   exactly once in `research/slop-bytecode.hex`, at byte offset 83,
   in the dispatcher pattern `PUSH4` (`0x63`) + selector + `EQ`
   (`0x14`):

   ```text
   ... 095ea7b31461079257806318160ddd1461077557806323b872dd14610696578063313ce5671461067b5780633f4ba83a1461 ...
                                                                         ^^^^^^^^^^
                                                                         PUSH4 313ce567, EQ
   ```

   The surrounding bytes show the dispatcher comparing the incoming
   call data against this selector, right after the `transferFrom`
   selector (`63 23b872dd`) and before the `3f4ba83a` selector
   (`63 3f4ba83a`).

3. **The contract is live.** At block 111,538,360 (2026-11-11),
   `totalSupply()` (selector `0x18160ddd`) returned
   `0x00000000000000000000000000000000000000000052b7d2dcc80cd2e4000000`
   = 100,000,000 SLOP, confirming the contract at this address is the
   live SLOP token.

## Verification

To re-check this claim:

1. Recompute the selector:
   `keccak256("decimals()")` and take the
   first 4 bytes. Expected: `313ce567`.
2. Search the deployed bytecode for `313ce567`:
   `grep -o 313ce567 research/slop-bytecode.hex` — expect exactly one
   match, preceded by `63` (PUSH4) and followed by `14` (EQ).
3. Run the repo checker:
   `python3 scripts/verify-selector.py --bytecode
   research/slop-bytecode.hex 'decimals()'`
   — expect "found at byte offset 83".
4. Confirm the contract is live at
   `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on Robinhood Chain
   (public RPC `https://rpc.mainnet.chain.robinhood.com`):
   `eth_call` to `totalSupply()` (`0x18160ddd`) returns
   `100,000,000 * 10^18`.

## Notes

- `decimals()` is a view function (a read-only ERC-20 metadata
  getter), so unlike a state-changing function it can be observed
  with `eth_call`. This packet identifies the selector only; it does
  not claim a return value.
- This packet covers one selector only. The other 10 functions are not
  covered here. `burn` (`9dc29fac`), `transfer` (`a9059cbb`),
  `supportsInterface` (`01ffc9a7`), `name` (`06fdde03`), `approve`
  (`095ea7b3`), `totalSupply` (`18160ddd`), and `transferFrom`
  (`23b872dd`) were verified in previous packets.
