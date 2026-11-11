# Selector 3f4ba83a is unpause()

## Target

SLOP token contract `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on
Robinhood Chain mainnet (chain ID 4663). The deployed bytecode is in
`research/slop-bytecode.hex`. This packet identifies one function
selector in that contract's dispatcher.

## Claim

The function selector `3f4ba83a` in the SLOP token dispatcher is
`unpause()`.

## Evidence

1. **keccak256 of the signature.** The first four bytes of
   `keccak256("unpause()")` are `3f4ba83a`:

   ```text
   keccak256("unpause()")
     = 3f4ba83af89dc9793996d9e56b8abe6dc88cd97c9c2bb23027806e9c1ffd54dc
   selector = 0x3f4ba83a
   ```

2. **The selector is in the deployed bytecode.** `3f4ba83a` appears
   exactly once in `research/slop-bytecode.hex`, at byte offset 94,
   in the dispatcher pattern `PUSH4` (`0x63`) + selector + `EQ`
   (`0x14`):

   ```text
   ... 095ea7b31461079257806318160ddd1461077557806323b872dd14610696578063313ce5671461067b5780633f4ba83a1461061557806340c10f19146105445780635c ...
                                                                                               ^^^^^^^^^^
                                                                                               PUSH4 3f4ba83a, EQ
   ```

   The surrounding bytes show the dispatcher comparing the incoming
   call data against this selector, right after the `decimals`
   selector (`63 313ce567`) and before the `mint(address,uint256)`
   selector (`63 40c10f19`).

3. **The contract is live.** At block 111,538,360 (2026-11-11),
   `totalSupply()` (selector `0x18160ddd`) returned
   `0x00000000000000000000000000000000000000000052b7d2dcc80cd2e4000000`
   = 100,000,000 SLOP, confirming the contract at this address is the
   live SLOP token.

## Verification

To re-check this claim:

1. Recompute the selector:
   `keccak256("unpause()")` and take the
   first 4 bytes. Expected: `3f4ba83a`.
2. Search the deployed bytecode for `3f4ba83a`:
   `grep -o 3f4ba83a research/slop-bytecode.hex` — expect exactly one
   match, preceded by `63` (PUSH4) and followed by `14` (EQ).
3. Run the repo checker:
   `python3 scripts/verify-selector.py --bytecode
   research/slop-bytecode.hex 'unpause()'`
   — expect "found at byte offset 94".
4. Confirm the contract is live at
   `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on Robinhood Chain
   (public RPC `https://rpc.mainnet.chain.robinhood.com`):
   `eth_call` to `totalSupply()` (`0x18160ddd`) returns
   `100,000,000 * 10^18`.

## Notes

- `unpause` is a state-changing function, so it cannot be called
  with `eth_call` to observe its behavior. This packet identifies the
  selector only; it does not claim anything about who can call
  `unpause` or what it does when called.
- This packet covers one selector only. The other 10 functions are not
  covered here. `burn` (`9dc29fac`), `transfer` (`a9059cbb`),
  `supportsInterface` (`01ffc9a7`), `name` (`06fdde03`), `approve`
  (`095ea7b3`), `totalSupply` (`18160ddd`), and `transferFrom`
  (`23b872dd`) were verified in previous packets.
