# Selector 40c10f19 is mint(address,uint256)

## Target

SLOP token contract `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on
Robinhood Chain mainnet (chain ID 4663). The deployed bytecode is in
`research/slop-bytecode.hex`. This packet identifies one function
selector in that contract's dispatcher.

## Claim

The function selector `40c10f19` in the SLOP token dispatcher is
`mint(address,uint256)`.

## Evidence

1. **keccak256 of the signature.** The first four bytes of
   `keccak256("mint(address,uint256)")` are `40c10f19`:

   ```text
   keccak256("mint(address,uint256)")
     = 40c10f19c047ae7dfa66d6312b683d2ea3dfbcb4159e96b967c5f4b0a86f2842
   selector = 0x40c10f19
   ```

2. **The selector is in the deployed bytecode.** `40c10f19` appears
   exactly once in `research/slop-bytecode.hex`, at byte offset 105,
   in the dispatcher pattern `PUSH4` (`0x63`) + selector + `EQ`
   (`0x14`):

   ```text
   ... 63313ce5671461067b5780633f4ba83a1461061557806340c10f19146105445780635c975abb1461052257 ...
                                                     ^^^^^^^^^^
                                                     PUSH4 40c10f19, EQ
   ```

   The surrounding bytes show the dispatcher comparing the incoming
   call data against this selector, right after the `unpause`
   selector (`63 3f4ba83a`) and before the `paused` selector
   (`63 5c975abb`). The `decimals` selector (`63 313ce567`) is
   visible just before `unpause`.

3. **The contract is live.** At block 111,538,360 (2026-11-11),
   `totalSupply()` (selector `0x18160ddd`) returned
   `0x00000000000000000000000000000000000000000052b7d2dcc80cd2e4000000`
   = 100,000,000 SLOP, confirming the contract at this address is the
   live SLOP token.

## Verification

To re-check this claim:

1. Recompute the selector:
   `keccak256("mint(address,uint256)")` and take the
   first 4 bytes. Expected: `40c10f19`.
2. Search the deployed bytecode for `40c10f19`:
   `grep -o 40c10f19 research/slop-bytecode.hex` — expect exactly one
   match, preceded by `63` (PUSH4) and followed by `14` (EQ).
3. Run the repo checker:
   `python3 scripts/verify-selector.py --bytecode
   research/slop-bytecode.hex 'mint(address,uint256)'`
   — expect "found at byte offset 105".
4. Confirm the contract is live at
   `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on Robinhood Chain
   (public RPC `https://rpc.mainnet.chain.robinhood.com`):
   `eth_call` to `totalSupply()` (`0x18160ddd`) returns
   `100,000,000 * 10^18`.

## Notes

- `mint` is a state-changing function, so it cannot be called
  with `eth_call` to observe its behavior. This packet identifies the
  selector only; it does not claim anything about who can call
  `mint` or what it does when called.
- This packet covers one selector only. The other 10 functions are not
  covered here. `burn` (`9dc29fac`), `transfer` (`a9059cbb`),
  `supportsInterface` (`01ffc9a7`), `name` (`06fdde03`), `approve`
  (`095ea7b3`), `totalSupply` (`18160ddd`), and `transferFrom`
  (`23b872dd`) were verified in previous packets.
