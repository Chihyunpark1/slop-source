# Selector 8da5cb5b is owner()

## Target

SLOP token contract `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on
Robinhood Chain mainnet (chain ID 4663). The deployed bytecode is in
`research/slop-bytecode.hex`. This packet identifies one function
selector in that contract's dispatcher.

## Claim

The function selector `8da5cb5b` in the SLOP token dispatcher is
`owner()`.

## Evidence

1. **keccak256 of the signature.** The first four bytes of
   `keccak256("owner()")` are `8da5cb5b`:

   ```text
   keccak256("owner()")
     = 8da5cb5b36e7f68c1d2e56001220cdbdd3ba2616072f718acfda4a06441a807d
   selector = 0x8da5cb5b
   ```

2. **The selector is in the deployed bytecode.** `8da5cb5b` appears
   exactly once in `research/slop-bytecode.hex`, at byte offset 160,
   in the dispatcher pattern `PUSH4` (`0x63`) + selector + `EQ`
   (`0x14`):

   ```text
   ... 63715018a61461048c5780638456cb59146104325780638da5cb5b1461040657806395d89b41146102eb5780639dc29fac14610200578063a9059cbb1461 ...
                                                     ^^^^^^^^^^
                                                     PUSH4 8da5cb5b, EQ
   ```

   The surrounding bytes show the dispatcher comparing the incoming
   call data against this selector, right after the `pause`
   selector (`63 8456cb59`) and before the `symbol` selector
   (`63 95d89b41`).

3. **The contract is live.** At block 111,538,360 (2026-11-11),
   `totalSupply()` (selector `0x18160ddd`) returned
   `0x00000000000000000000000000000000000000000052b7d2dcc80cd2e4000000`
   = 100,000,000 SLOP, confirming the contract at this address is the
   live SLOP token.

## Verification

To re-check this claim:

1. Recompute the selector:
   `keccak256("owner()")` and take the
   first 4 bytes. Expected: `8da5cb5b`.
2. Search the deployed bytecode for `8da5cb5b`:
   `grep -o 8da5cb5b research/slop-bytecode.hex` — expect exactly one
   match, preceded by `63` (PUSH4) and followed by `14` (EQ).
3. Run the repo checker:
   `python3 scripts/verify-selector.py --bytecode
   research/slop-bytecode.hex 'owner()'`
   — expect "found at byte offset 160".
4. Confirm the contract is live at
   `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on Robinhood Chain
   (public RPC `https://rpc.mainnet.chain.robinhood.com`):
   `eth_call` to `totalSupply()` (`0x18160ddd`) returns
   `100,000,000 * 10^18`.

## Notes

- `owner()` is a view function, so it can be observed via `eth_call`
  in principle. This packet identifies the selector only; it does not
  claim anything about who the owner is or what the owner can do.
- This packet covers one selector only. The other 10 functions are not
  covered here. `burn` (`9dc29fac`), `transfer` (`a9059cbb`),
  `supportsInterface` (`01ffc9a7`), `name` (`06fdde03`), `approve`
  (`095ea7b3`), `totalSupply` (`18160ddd`), and `transferFrom`
  (`23b872dd`) were verified in previous packets.
