# Selector 23b872dd is transferFrom(address,address,uint256)

## Target

SLOP token contract `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on
Robinhood Chain mainnet (chain ID 4663). The deployed bytecode is in
`research/slop-bytecode.hex`. This packet identifies one function
selector in that contract's dispatcher.

## Claim

The function selector `23b872dd` in the SLOP token dispatcher is
`transferFrom(address,address,uint256)`.

## Evidence

1. **keccak256 of the signature.** The first four bytes of
   `keccak256("transferFrom(address,address,uint256)")` are `23b872dd`:

   ```text
   keccak256("transferFrom(address,address,uint256)")
     = 23b872dd7302113369cda2901243429419bec145408fa8b352b3dd92b66c680b
   selector = 0x23b872dd
   ```

2. **The selector is in the deployed bytecode.** `23b872dd` appears
   exactly once in `research/slop-bytecode.hex`, at byte offset 72,
   in the dispatcher pattern `PUSH4` (`0x63`) + selector + `EQ`
   (`0x14`):

   ```text
   ... 095ea7b31461079257806318160ddd1461077557806323b872dd14610696578063313ce5671461067b5780633f4ba83a1461 ...
                                                   ^^^^^^^^^^
                                                   PUSH4 23b872dd, EQ
   ```

   The surrounding bytes show the dispatcher comparing the incoming
   call data against this selector, right after the `totalSupply`
   selector (`63 18160ddd`) and before the `decimals` selector
   (`63 313ce567`).

3. **The contract is live.** At block 111,538,360 (2026-11-11),
   `totalSupply()` (selector `0x18160ddd`) returned
   `0x00000000000000000000000000000000000000000052b7d2dcc80cd2e4000000`
   = 100,000,000 SLOP, confirming the contract at this address is the
   live SLOP token.

## Verification

To re-check this claim:

1. Recompute the selector:
   `keccak256("transferFrom(address,address,uint256)")` and take the
   first 4 bytes. Expected: `23b872dd`.
2. Search the deployed bytecode for `23b872dd`:
   `grep -o 23b872dd research/slop-bytecode.hex` — expect exactly one
   match, preceded by `63` (PUSH4) and followed by `14` (EQ).
3. Run the repo checker:
   `python3 scripts/verify-selector.py --bytecode
   research/slop-bytecode.hex 'transferFrom(address,address,uint256)'`
   — expect "found at byte offset 72".
4. Confirm the contract is live at
   `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on Robinhood Chain
   (public RPC `https://rpc.mainnet.chain.robinhood.com`):
   `eth_call` to `totalSupply()` (`0x18160ddd`) returns
   `100,000,000 * 10^18`.

## Notes

- `transferFrom` is a state-changing function, so it cannot be called
  with `eth_call` to observe its behavior. This packet identifies the
  selector only; it does not claim anything about who can call
  `transferFrom` or what it does when called.
- This packet covers one selector only. The other 11 functions are not
  covered here. `burn` (`9dc29fac`), `transfer` (`a9059cbb`),
  `supportsInterface` (`01ffc9a7`), `name` (`06fdde03`), `approve`
  (`095ea7b3`), and `totalSupply` (`18160ddd`) were verified in
  previous packets.
