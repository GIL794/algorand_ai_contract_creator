# Recommended Algorand MCP Tools (Top 80)

Based on your AI contract creator project, here are the **most essential tools** you should keep enabled:

## 🔴 **CRITICAL - Must Keep (25 tools)**

### Account Management (8 tools)
- `create_account` - Create new Algorand accounts
- `rekey_account` - Rekey accounts for security
- `validate_address` - Validate Algorand addresses
- `encode_address` / `decode_address` - Address encoding/decoding
- `mnemonic_to_secret_key` / `secret_key_to_mnemonic` - Key management
- `get_application_address` - Get smart contract addresses

### Core Transactions (7 tools)
- `make_payment_txn` - Send ALGO payments
- `make_app_create_txn` - Deploy smart contracts
- `make_app_update_txn` - Update contracts
- `make_app_call_txn` - Call contract methods
- `make_app_optin_txn` - Opt into contracts
- `sign_transaction` - Sign transactions
- `assign_group_id` - Atomic transaction groups

### Essential Utilities (10 tools)
- `ping` - Test connectivity
- `bytes_to_bigint` / `bigint_to_bytes` - Data conversion
- `encode_uint64` / `decode_uint64` - Number encoding
- `sign_bytes` / `verify_bytes` - Cryptographic operations
- `encode_obj` / `decode_obj` - MessagePack encoding
- `compile_teal` - Compile TEAL code
- `disassemble_teal` - Disassemble TEAL

## 🟡 **HIGH PRIORITY - Smart Contract Development (20 tools)**

### Application Transactions (7 tools)
- `make_app_delete_txn` - Delete applications
- `make_app_closeout_txn` - Close out from apps
- `make_app_clear_txn` - Clear state

### Algod API - Account & Application (8 tools)
- `api_algod_get_account_info` - Get account balance/assets
- `api_algod_get_account_application_info` - Get app state
- `api_algod_get_account_asset_info` - Get asset holdings
- `api_algod_get_application_by_id` - Get app details
- `api_algod_get_application_box` / `api_algod_get_application_boxes` - Box storage
- `api_algod_get_transaction_params` - Get suggested params
- `api_algod_get_node_status` - Check node status

### Indexer API - Querying (5 tools)
- `api_indexer_lookup_account_by_id` - Lookup accounts
- `api_indexer_lookup_transaction_by_id` - Lookup transactions
- `api_indexer_lookup_application_by_id` - Lookup applications
- `api_indexer_search_for_transactions` - Search transactions
- `api_indexer_lookup_account_transactions` - Account history

## 🟢 **MEDIUM PRIORITY - Asset Management (15 tools)**

### Asset Transactions (5 tools)
- `make_asset_create_txn` - Create ASAs (tokens)
- `make_asset_config_txn` - Configure assets
- `make_asset_transfer_txn` - Transfer tokens
- `make_asset_freeze_txn` - Freeze/unfreeze assets
- `make_asset_destroy_txn` - Destroy assets

### Asset APIs (10 tools)
- `api_algod_get_asset_by_id` - Get asset info
- `api_indexer_lookup_asset_by_id` - Lookup assets
- `api_indexer_lookup_asset_balances` - Asset holders
- `api_indexer_lookup_asset_transactions` - Asset transactions
- `api_indexer_search_for_assets` - Search assets
- `api_indexer_lookup_account_assets` - Account's assets

## 🔵 **LOW PRIORITY - Advanced Features (20 tools)**

### Knowledge & Documentation (1 tool)
- `get_knowledge_doc` - Access Algorand documentation

### ARC-26 (1 tool)
- `generate_algorand_uri` - Generate payment URIs

### Simulation & Testing (2 tools)
- `simulate_transactions` - Simulate before sending
- `simulate_raw_transactions` - Raw simulation

### Additional Indexer (8 tools)
- `api_indexer_lookup_account_app_local_states` - Local state
- `api_indexer_lookup_application_logs` - App logs
- `api_indexer_lookup_application_boxes` - App boxes
- `api_indexer_search_for_applications` - Search apps
- `api_indexer_search_for_accounts` - Search accounts

### NFD (Domain Names) (3 tools)
- `api_nfd_get_nfd` - Get NFD info
- `api_nfd_get_nfds_for_addresses` - Addresses to NFDs
- `api_nfd_search_nfds` - Search NFDs

### Transaction Management (5 tools)
- `api_algod_get_pending_transaction` - Check pending
- `api_algod_get_pending_transactions` - List pending
- `api_algod_get_node_status_after_block` - Block status

## ❌ **DISABLE - DeFi/Specialized (44 tools)**

These are less critical for contract development:

### Tinyman DEX (8 tools) - Disable if not using
- All `api_tinyman_*` tools

### Ultrade Exchange (20 tools) - Disable if not using
- All `api_ultrade_*` tools

### Vestige DeFi (16 tools) - Disable if not using
- All `api_vestige_*` tools

## 📊 Summary

**Keep (80 tools):**
- Critical: 25 tools
- High Priority: 20 tools
- Medium Priority: 15 tools
- Low Priority: 20 tools

**Disable (4 tools):**
- Tinyman, Ultrade, Vestige APIs (unless you specifically need DeFi features)

## 🎯 Quick Action Plan

1. In Cursor MCP settings, expand the `algorand-mcp` server
2. **Disable** all tools starting with:
   - `api_tinyman_*` (8 tools)
   - `api_ultrade_*` (20 tools)  
   - `api_vestige_*` (16 tools)
3. This will reduce from 84 to **40 essential tools** (well under your 80 limit)
4. You can always re-enable specific tools later if needed

