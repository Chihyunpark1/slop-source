# Selector 095ea7b3 is approve(address,uint256)

## Target

SLOP token contract `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on
Robinhood Chain mainnet (chain ID 4663). The deployed bytecode is in
`research/slop-bytecode.hex`. This packet identifies one function
selector in that contract's dispatcher.

## Claim

The function selector `095ea7b3` in the SLOP token dispatcher is
`approve(address,uint256)`.

## Evidence

1. **keccak256 of the signature.** The first four bytes of
   `keccak256("approve(address,uint256)")` are `095ea7b3`:

   ```text
   keccak256("approve(address,uint256)")
     = 095ea7b334ae44009aa867bfb386f5c3b4b443ac6f0ee573fa91c4608fbadfba
   selector = 0x095ea7b3
   ```

2. **The selector is in the deployed bytecode.** `095ea7b3` appears
   exactly once in `research/slop-bytecode.hex`, at byte offset 50,
   in the dispatcher pattern `PUSH4` (`0x63`) + selector + `EQ`
   (`0x14`):

   ```text
   ... a7146108e65750806306fdde0314610814578063095ea7b31461079257806318160ddd1461077557806323b872dd14610696 ...
                                               ^^^^^^^^^^
                                               PUSH4 095ea7b3, EQ
   ```

   The surrounding bytes show the dispatcher comparing the incoming
   call data against this selector, right after the `name` selector
   (`63 06fdde03`) and before the `totalSupply` selector
   (`63 18160ddd`).

3. **The contract is live.** At block 111,538,360 (2026-11-11),
   `totalSupply()` (selector `0x18160ddd`) returned
   `0x00000000000000000000000000000000000000000052b7d2dcc80cd2e4000000`
   = 100,000,000 SLOP, confirming the contract at this address is the
   live SLOP token.

## Verification

To re-check this claim:

1. Recompute the selector:
   `keccak256("approve(address,uint256)")` and take the first 4 bytes.
   Expected: `095ea7b3`.
2. Search the deployed bytecode for `095ea7b3`:
   `grep -o 095ea7b3 research/slop-bytecode.hex` — expect exactly one
   match, preceded by `63` (PUSH4) and followed by `14` (EQ).
3. Run the repo checker:
   `python3 scripts/verify-selector.py --bytecode
   research/slop-bytecode.hex 'approve(address,uint256)'` — expect
   "found at byte offset 50".
4. Confirm the contract is live at
   `0xfeb4E36FA4a2A494FF25ae4a63491e4c584A67AE` on Robinhood Chain
   (public RPC `https://rpc.mainnet.chain.robinhood.com`):
   `eth_call` to `totalSupply()` (`0x18160ddd`) returns
   `100,000,000 * 10^18`.

## Notes

- `approve` is a state-changing function, so it cannot be called with
  `eth_call` to observe its behavior. This packet identifies the
  selector only; it does not claim anything about who can call
  `approve` or what it does when called.
- This packet covers one selector only. The other 13 functions are not
  covered here. `burn` (`9dc29fac`), `transfer` (`a9059cbb`),
  `supportsInterface` (`01ffc9a7`), and `name` (`06fdde03`) were
  verified in previous packets.
