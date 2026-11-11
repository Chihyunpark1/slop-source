# Selector 5c975abb is paused()

## Target

SLOP token contract `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on
Robinhood Chain mainnet (chain ID 4663). The deployed bytecode is in
`research/slop-bytecode.hex`. This packet identifies one function
selector in that contract's dispatcher.

## Claim

The function selector `5c975abb` in the SLOP token dispatcher is
`paused()`.

## Evidence

1. **keccak256 of the signature.** The first four bytes of
   `keccak256("paused()")` are `5c975abb`:

   ```text
   keccak256("paused()")
     = 5c975abbf8c4d6efa68fc896e233763eb503f2318260b7bf59b19412913788b2
   selector = 0x5c975abb
   ```

2. **The selector is in the deployed bytecode.** `5c975abb` appears
   exactly once in `research/slop-bytecode.hex`, at byte offset 116,
   in the dispatcher pattern `PUSH4` (`0x63`) + selector + `EQ`
   (`0x14`):

   ```text
   ... 7b5780633f4ba83a1461061557806340c10f19146105445780635c975abb1461052257806370a08231146104eb578063715018a6146104 ...
                                                           ^^^^^^^^^^
                                                           PUSH4 5c975abb, EQ
   ```

   The surrounding bytes show the dispatcher comparing the incoming
   call data against this selector, right after the `40c10f19`
   selector (`63 40c10f19`) and before the `70a08231` selector
   (`63 70a08231`).

3. **The contract is live.** At block 111,538,360 (2026-11-11),
   `totalSupply()` (selector `0x18160ddd`) returned
   `0x00000000000000000000000000000000000000000052b7d2dcc80cd2e4000000`
   = 100,000,000 SLOP, confirming the contract at this address is the
   live SLOP token.

## Verification

To re-check this claim:

1. Recompute the selector:
   `keccak256("paused()")` and take the
   first 4 bytes. Expected: `5c975abb`.
2. Search the deployed bytecode for `5c975abb`:
   `grep -o 5c975abb research/slop-bytecode.hex` — expect exactly one
   match, preceded by `63` (PUSH4) and followed by `14` (EQ).
3. Run the repo checker:
   `python3 scripts/verify-selector.py --bytecode
   research/slop-bytecode.hex 'paused()'`
   — expect "found at byte offset 116".
4. Confirm the contract is live at
   `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on Robinhood Chain
   (public RPC `https://rpc.mainnet.chain.robinhood.com`):
   `eth_call` to `totalSupply()` (`0x18160ddd`) returns
   `100,000,000 * 10^18`.

## Notes

- `paused` is a view function, so it can be observed via `eth_call`
  in principle. This packet identifies the selector only; it does not
  claim anything about the contract's paused state or what `paused`
  returns when called.
- This packet covers one selector only. The other 10 functions are not
  covered here. `burn` (`9dc29fac`), `transfer` (`a9059cbb`),
  `supportsInterface` (`01ffc9a7`), `name` (`06fdde03`), `approve`
  (`095ea7b3`), `totalSupply` (`18160ddd`), and `transferFrom`
  (`23b872dd`) were verified in previous packets.
