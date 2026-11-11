# Selector 18160ddd is totalSupply()

## Target

SLOP token contract `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on
Robinhood Chain mainnet (chain ID 4663). The deployed bytecode is in
`research/slop-bytecode.hex`. This packet identifies one function
selector in that contract's dispatcher.

## Claim

The function selector `18160ddd` in the SLOP token dispatcher is
`totalSupply()`.

## Evidence

1. **keccak256 of the signature.** The first four bytes of
   `keccak256("totalSupply()")` are `18160ddd`:

   ```text
   keccak256("totalSupply()")
     = 18160ddd7f15c72528c2f94fd8dfe3c8d5aa26e2c50c7d81f4bc7bee8d4b7932
   selector = 0x18160ddd
   ```

2. **The selector is in the deployed bytecode.** `18160ddd` appears
   exactly once in `research/slop-bytecode.hex`, at byte offset 61,
   in the dispatcher pattern `PUSH4` (`0x63`) + selector + `EQ`
   (`0x14`):

   ```text
   ... fdde0314610814578063095ea7b31461079257806318160ddd1461077557806323b872dd14610696578063313ce567146106 ...
                                                 ^^^^^^^^^^
                                                 PUSH4 18160ddd, EQ
   ```

   The surrounding bytes show the dispatcher comparing the incoming
   call data against this selector, right after the `approve` selector
   (`63 095ea7b3`) and before the `transferFrom` selector
   (`63 23b872dd`).

3. **The contract is live.** At block 111,538,360 (2026-11-11),
   `totalSupply()` (selector `0x18160ddd`) returned
   `0x00000000000000000000000000000000000000000052b7d2dcc80cd2e4000000`
   = 100,000,000 SLOP, confirming the contract at this address is the
   live SLOP token.

## Verification

To re-check this claim:

1. Recompute the selector:
   `keccak256("totalSupply()")` and take the first 4 bytes.
   Expected: `18160ddd`.
2. Search the deployed bytecode for `18160ddd`:
   `grep -o 18160ddd research/slop-bytecode.hex` — expect exactly one
   match, preceded by `63` (PUSH4) and followed by `14` (EQ).
3. Run the repo checker:
   `python3 scripts/verify-selector.py --bytecode
   research/slop-bytecode.hex 'totalSupply()'` — expect "found at
   byte offset 61".
4. Confirm the contract is live at
   `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on Robinhood Chain
   (public RPC `https://rpc.mainnet.chain.robinhood.com`):
   `eth_call` to `totalSupply()` (`0x18160ddd`) returns
   `100,000,000 * 10^18`.

## Notes

- `totalSupply` is a view function. This packet identifies the
  selector only; the live return value (100,000,000 SLOP at block
  111,538,360) is the contract-liveness evidence cited above.
- This packet covers one selector only. The other 12 functions are not
  covered here. `burn` (`9dc29fac`), `transfer` (`a9059cbb`),
  `supportsInterface` (`01ffc9a7`), `name` (`06fdde03`), and `approve`
  (`095ea7b3`) were verified in previous packets.
