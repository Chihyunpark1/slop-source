# Selector 95d89b41 is symbol()

## Target

SLOP token contract `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on
Robinhood Chain mainnet (chain ID 4663). The deployed bytecode is in
`research/slop-bytecode.hex`. This packet identifies one function
selector in that contract's dispatcher.

## Claim

The function selector `95d89b41` in the SLOP token dispatcher is
`symbol()`.

## Evidence

1. **keccak256 of the signature.** The first four bytes of
   `keccak256("symbol()")` are `95d89b41`:

   ```text
   keccak256("symbol()")
     = 95d89b41e2f5f391a79ec54e9d87c79d6e777c63e32c28da95b4e9e4a79250ec
   selector = 0x95d89b41
   ```

2. **The selector is in the deployed bytecode.** `95d89b41` appears
   exactly once in `research/slop-bytecode.hex`, at byte offset 171,
   in the dispatcher pattern `PUSH4` (`0x63`) + selector + `EQ`
   (`0x14`):

   ```text
   ... 61048c5780638456cb59146104325780638da5cb5b1461040657806395d89b41146102eb5780639dc29fac14610200578063a9059cbb146101cf5780 ...
                                                               ^^^^^^^^^^
                                                               PUSH4 95d89b41, EQ
   ```

   The surrounding bytes show the dispatcher comparing the incoming
   call data against this selector, right after the `8da5cb5b`
   selector (`63 8da5cb5b`) and before the `burn` selector
   (`63 9dc29fac`).

3. **The contract is live.** At block 111,538,360 (2026-11-11),
   `totalSupply()` (selector `0x18160ddd`) returned
   `0x00000000000000000000000000000000000000000052b7d2dcc80cd2e4000000`
   = 100,000,000 SLOP, confirming the contract at this address is the
   live SLOP token.

## Verification

To re-check this claim:

1. Recompute the selector:
   `keccak256("symbol()")` and take the first 4 bytes.
   Expected: `95d89b41`.
2. Search the deployed bytecode for `95d89b41`:
   `grep -o 95d89b41 research/slop-bytecode.hex` — expect exactly one
   match, preceded by `63` (PUSH4) and followed by `14` (EQ).
3. Run the repo checker:
   `python3 scripts/verify-selector.py --bytecode
   research/slop-bytecode.hex 'symbol()'` — expect "found at byte
   offset 171".
4. Confirm the contract is live at
   `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on Robinhood Chain
   (public RPC `https://rpc.mainnet.chain.robinhood.com`):
   `eth_call` to `totalSupply()` (`0x18160ddd`) returns
   `100,000,000 * 10^18`.

## Notes

- `symbol` is a view function, so it can be observed via `eth_call`
  in principle. This packet identifies the selector only; it does not
  claim a specific return value.
- This packet covers one selector only. The other functions are not
  covered here. `burn` (`9dc29fac`), `transfer` (`a9059cbb`),
  `supportsInterface` (`01ffc9a7`), `name` (`06fdde03`), `approve`
  (`095ea7b3`), `totalSupply` (`18160ddd`), and `transferFrom`
  (`23b872dd`) were verified in previous packets.
