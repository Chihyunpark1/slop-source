# EVM escrow contracts — structure, deployment, and live on-chain state

## Target

Issue #10: the EVM escrow system in the public SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT) at development commit
`ced75d782d5836f60d84f46d50604f75a5852438` — the Solidity contracts in
`contracts/evm/src/ProjectEscrow.sol`, the TypeScript counterpart layer
(`contracts/evm/adapter.ts`, `monthly-reserve.ts`, `native-cost.ts`,
`factories.ts`), the Foundry deployment scripts in
`contracts/evm/script/`, and the deployment record in
`contracts/DEPLOY-MAINNET.md`. The on-chain side is checked live on
Base (8453), Ethereum (1), and Robinhood Chain (4663).

## Claim

The documented EVM escrow system is live at the same addresses with
byte-identical runtime code on all three mainnets — a UUPS factory
proxy whose ERC-1967 slot selects the recorded factory implementation,
which in turn selects the recorded vault implementation at monthly
reserve version 2 — and the adapter, monthly-reserve, and native-cost
modules are its off-chain counterpart: they verify deployments against
the recorded digests, build unsigned calldata, and account for native
fees, and never sign or submit anything.

## Evidence

### The on-chain contracts (one source file, two UUPS contracts)

`contracts/evm/src/ProjectEscrow.sol` (Solidity, Cancun target per
`contracts/evm/foundry.toml`) holds both contracts; both are
`Initializable` + `UUPSUpgradeable`, and upgrades are authorized only
by a dedicated upgrade authority (`_authorizeUpgrade`,
ProjectEscrow.sol:226 and :891).

- **EscrowFactory** (ProjectEscrow.sol:842) creates one vault per
  (owner, projectId, token, purpose): `vaultKey` is
  `keccak256(abi.encode(owner, projectId, token, purpose))`
  (ProjectEscrow.sol:955) and is reused as the CREATE2 salt, so a
  vault's address is deterministic — `_create` deploys
  `new ERC1967Proxy{salt: key}(vaultImplementation, initialization)`
  (ProjectEscrow.sol:993). The factory's selected vault implementation
  can be replaced only by the upgrade authority
  (`setVaultImplementation`, ProjectEscrow.sol:939); the registrar
  rotates the identity authority (ProjectEscrow.sol:1000-1031).
  Purpose is `Ordinary` (0) or `Bounty` (1) (ProjectEscrow.sol:25).
- **ProjectEscrow** (the vault, ProjectEscrow.sol:44) holds one
  project's funds for one token (the zero token address means native
  ETH, per `contracts/evm/README.md` "Native ETH"). Entry points, by
  role: `deposit(uint128)` (permissionless; native deposits must carry
  exactly the amount as value), owner-only `commitAward` /
  `commitBountyAward` for individual awards, `pay` against a signed
  destination binding (`bindDestination` / `payableBinding`),
  `withdrawUnused` (owner), and `claimFees` (permissionless, pays the
  configured fee recipient). Both fees are the same pure function:
  `payoutFee` is 2% of gross rounded up once — `gross / 50` plus one
  when there is a remainder (ProjectEscrow.sol:434-438) — and
  `withdrawalFee` returns `payoutFee` (ProjectEscrow.sol:440-443).

### The monthly reserve (inside the vault contract)

The monthly reserve is not a separate contract; it is the vault's
second commitment path (ProjectEscrow.sol:509-664), at version 2 —
`monthlyReserveVersion()` is a pure function returning the literal 2
(ProjectEscrow.sol:323-326). The owner sets a per-month cap and an
on/off switch (`setMonthlyCommitment(uint128,bool)`,
ProjectEscrow.sol:509). For a period (a UTC month as `YYYYMM`), anyone
can then commit the month's allocation inside its window:
`commitMonthly` rebuilds the allocation Merkle sum tree
(`allocationRoot`, ProjectEscrow.sol:369) and requires the identity
authority's EIP-712 attestation over `monthlyDigest(period, root)`
under the vault's `SlopProjectEscrow` / version `5` domain.
`reserveMonthly` records a reservation against a
`monthlyReserveDigest`, `commitMonthlyLeaf` commits individual leaves,
and `releaseMonthlyReserve` settles a reserve, including a
wrong-sum fault release path keyed by `monthlyReleaseDigest`.

### The off-chain counterpart (TypeScript, unsigned by design)

- **Adapter** (`contracts/evm/adapter.ts`): adapts finalized chain
  state to the platform. `verifyEvmFactory` (adapter.ts:329) and
  `verifyEvmDeployment` (adapter.ts:495) recompute runtime code
  SHA-256 digests and read the ERC-1967 implementation slot — the slot
  constant is written out at adapter.ts:356-357,
  `0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc`.
  Its calldata builders are explicitly "Unsigned call data only.
  Never selects signers or submits a transaction." (adapter.ts:840).
- **Monthly reserve module** (`contracts/evm/monthly-reserve.ts`):
  builds the same ordered sum tree off-chain (`evmMonthlySumTree`,
  monthly-reserve.ts:109), computes the reserve digest
  (monthly-reserve.ts:177), builds reserve/leaf calldata, reads a
  period's reserve state at a finalized block
  (`readEvmMonthlyReserve`, monthly-reserve.ts:254), and prepares
  reservations and wrong-sum releases (`prepareEvmMonthlyReservation`,
  monthly-reserve.ts:472) — again as unsigned plans only.
- **Native cost** (`contracts/evm/native-cost.ts`):
  `evmReceiptNativeCost` (native-cost.ts:18) computes the actual
  native fee of a finalized receipt, kept separate from payment
  principal: execution gas (`gasUsed × effectiveGasPrice`), plus blob
  gas for EIP-4844 receipts, plus — on Base only — the receipt's
  witnessed L1 data fee (the raw receipt's `l1Fee`, accepted only when
  the raw receipt's transaction and block hashes match) and the
  operator fee read from the Base gas-price oracle predeploy
  `0x420000000000000000000000000000000000000f` with selector
  `0x275aedd2` and the receipt's `gasUsed` as argument, at the
  receipt's block (native-cost.ts:53-54). The parts are summed by
  `nativeFeeTotal` from `src/lib/verified-money`.
- **Reviewed factory table** (`contracts/evm/factories.ts`):
  `REVIEWED_EVM_FACTORIES` (factories.ts:43) pins the three mainnets
  to one source commit, `7fdedd3507c3f79217ccc896ace0e0b7472ca092`
  (factories.ts:28), with the addresses and digests in the table
  below. Its header comment states that project deployments are kept
  exclusively in D1 and appended only after finalized owner creation —
  the table is network infrastructure, not a project vault inventory.

### Deployment record

Deployment is by per-network Foundry scripts sharing
`script/DeployEscrowFactory.sol` (`DeployBase.s.sol` runs it for chain
8453, likewise `DeployEthereum.s.sol` and `DeployRobinhood.s.sol`,
plus Sepolia/testnet variants and `DeployUpgradeImplementations.s.sol`
for upgrades). `contracts/DEPLOY-MAINNET.md` records: the initial
deployment from source `bce5b0df`; a Base-only upgrade from `208fbf5b`;
and the bundled monthly reserve V2 upgrade from `7fdedd35`, finalized
26 October 2026 on all three EVM networks, after which every network
selects the same implementations. The current record is:

| Role | Address | Runtime SHA-256 |
| --- | --- | --- |
| Factory proxy | `0xe51AbF8c6Dbb3Ca6E9AD09F2dc6EF141d7364aAb` | `afb62459ccdd87d344b8bfa367c8dc49586323316bb8a51f1dfbe753336c0509` |
| Factory implementation | `0x9f27aec70559D8f4CA1A62398e673A25B1cE3e2f` | `976208154ce5e58f59d826e58273d917adc226109bf95ab4894b9cf144e4a1dd` |
| Vault implementation | `0x90C46e3E5be35B1048cD69403d1402Feed1240D8` | `155c7ea2fdeeaeccfd6daac64b6105e968c1927092f8761f34090a8b42e15bfc` |

Recorded roles, the same on all three networks: registrar
`0xd64F35aC87D9a1FB8eBD44e745c24436B606cF60`, identity authority
`0x31B87d13f9091bC3b8A5cb6F45C8b3cB99Ed6d70`, fee recipient
`0x8f77C37D8650776bFe73c9b12B15209eE15D9b86`, upgrade authority and
deployer `0x2Ad20Afa352Ec70E43A6d0E7794cf305c9Cbe35D`, binding delay 0.
The slop.cash registry record for the Slop project
(`https://slop.cash/api/v1/projects/slopdotcash`, `escrow.deployments`)
carries one deployment entry, base-mainnet, whose factory and
`evmUpgrade` fields match the table above exactly; the Ethereum and
Robinhood records live in `factories.ts` and `DEPLOY-MAINNET.md`, not
in that registry array.

### Live on-chain verification (2026-11-11, read-only)

`scripts/verify-evm-deployments.py` (added by this PR) replays the
adapter's own checks from public RPC endpoints. All 57 checks passed
(Base block 56044250, Ethereum block 26391608, Robinhood block
111691250):

- Chain ids confirmed first (8453 / 1 / 4663).
- `eth_getCode` runtime SHA-256 of all three roles matches the
  recorded digest on every network; code sizes are identical across
  networks (proxy 122 bytes, factory implementation 6,879 bytes,
  vault implementation 22,752 bytes).
- The factory proxy's ERC-1967 implementation slot reads
  `0x9f27aec70559d8f4ca1a62398e673a25b1ce3e2f` on every network.
- `eth_call` on the factory proxy returns the recorded state on every
  network: `vaultImplementation()` = the vault implementation above,
  `registrar()`, `feeRecipient()`, `identityAuthority()`,
  `upgradeAuthority()` = the recorded role addresses, and
  `bindingDelay()` = 0.
- `monthlyReserveVersion()` read from the vault implementation
  returns 2 on every network.
- Dispatcher check, using the keccak and PUSH4+selector+EQ scan of
  `scripts/verify-selector.py`: the factory implementation routes
  `vaultImplementation()` (0xbba48a90),
  `create(bytes32,address,uint8)` (0x9a668156), and
  `upgradeToAndCall(address,bytes)` (0x4f1ef286); the vault
  implementation routes `monthlyReserveVersion()` (0xa763e864),
  `deposit(uint128)` (0x54469aea), `pay(bytes32,uint64)`
  (0xcbcf057d), and `setMonthlyCommitment(uint128,bool)`
  (0x37c4075c).

## Verification

- `python3 scripts/verify-evm-deployments.py` — full live check
  against the three public RPC endpoints; observed
  `result: ALL CHECKS PASSED` on 2026-11-11 (block numbers move over
  time; the digests, slot, and role reads should not).
- `python3 scripts/verify-evm-deployments.py --network base-mainnet`
  — single-network variant.
- `python3 -m pytest tests/` — 6 new offline tests in
  `tests/test_verify_evm_deployments.py` pin the slot constant, the
  selector computations, and the word decoding used by the checker;
  the existing `tests/test_verify_selector.py` still passes.
- Source citations are file:line in `SlopDotCash/slopdotcash` at
  `ced75d782d5836f60d84f46d50604f75a5852438`; every line range quoted
  above was read at that commit.

## Notes

- Boundaries with other packets: the monthly commitment *window*
  (the half-open time gate around `commitMonthly` / `reserveMonthly`)
  is covered by the open packet in
  `research/contracts-evm/monthly-commitment-window.md` and is only
  cited here. How an owner sets up, registers, and withdraws from a
  vault is Issue #8's procedure layer; this packet covers the
  contracts themselves. The SLOP token contract is Issue #12.
  `contracts/evm/src/ReferralDistributor.sol` belongs to the
  referrals area and is out of scope here.
- What is on-chain versus off-chain: the factory, vault
  implementations, and every vault proxy are on-chain; the adapter,
  monthly-reserve, and native-cost modules, the sum-tree building,
  and all fee accounting from receipts are off-chain TypeScript that
  only reads finalized state and prepares unsigned calls.
- Limits: individual project vaults are not inventoried here — per
  `factories.ts`, project deployments are kept in D1, so their
  existence is not verifiable from the public sources used.
  State-changing functions were identified by source, selector
  routing, and the recorded deployment history, not executed.
  Explorer verification status of the replacement implementations is
  not claimed: `DEPLOY-MAINNET.md` records a Sourcify full match for
  the initial contracts only and states that it does not cover the
  replacement implementations.
