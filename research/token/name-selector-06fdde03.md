# Selector 06fdde03 is name()

## Target

SLOP token contract `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on
Robinhood Chain mainnet (chain ID 4663). The deployed bytecode is in
`research/slop-bytecode.hex`. This packet identifies one function
selector in that contract's dispatcher.

## Claim

The function selector `06fdde03` in the SLOP token dispatcher is
`name()`.

## Evidence

1. **keccak256 of the signature.** The first four bytes of
   `keccak256("name()")` are `06fdde03`:

   ```text
   keccak256("name()")
     = 06fdde0383f15d582d1a74511486c9ddf862a882fb7904b3d9fe9b8b8e58a796
   selector = 0x06fdde03
   ```

2. **The selector is in the deployed bytecode.** `06fdde03` appears
   exactly once in `research/slop-bytecode.hex`, at byte offset 39,
   in the dispatcher pattern `PUSH4` (`0x63`) + selector + `EQ`
   (`0x14`):

   ```text
   ... 3560e01c90816301ffc9a7146108e65750806306fdde0314610814578063095ea7b31461079257806318160ddd1461077557 ...
                                             ^^^^^^^^^^
                                             PUSH4 06fdde03, EQ
   ```

   The surrounding bytes show the dispatcher comparing the incoming
   call data against this selector, right after the `supportsInterface`
   selector (`63 01ffc9a7`) and before the `approve` selector
   (`63 095ea7b3`).

3. **The contract is live.** At block 111,538,360 (2026-11-11),
   `totalSupply()` (selector `0x18160ddd`) returned
   `0x00000000000000000000000000000000000000000052b7d2dcc80cd2e4000000`
   = 100,000,000 SLOP, confirming the contract at this address is the
   live SLOP token.

## Verification

To re-check this claim:

1. Recompute the selector:
   `keccak256("name()")` and take the first 4 bytes.
   Expected: `06fdde03`.
2. Search the deployed bytecode for `06fdde03`:
   `grep -o 06fdde03 research/slop-bytecode.hex` — expect exactly one
   match, preceded by `63` (PUSH4) and followed by `14` (EQ).
3. Run the repo checker:
   `python3 scripts/verify-selector.py --bytecode
   research/slop-bytecode.hex 'name()'` — expect "found at byte
   offset 39".
4. Confirm the contract is live at
   `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on Robinhood Chain
   (public RPC `https://rpc.mainnet.chain.robinhood.com`):
   `eth_call` to `totalSupply()` (`0x18160ddd`) returns
   `100,000,000 * 10^18`.

## Notes

- `name` is a view function. This packet identifies the selector
  only; it does not claim a specific return value. (The token name
  "Slop Cash" was confirmed separately from the contract's public
  state.)
- This packet covers one selector only. The other 14 functions are not
  covered here. `burn` (`9dc29fac`), `transfer` (`a9059cbb`), and
  `supportsInterface` (`01ffc9a7`) were verified in previous packets.
