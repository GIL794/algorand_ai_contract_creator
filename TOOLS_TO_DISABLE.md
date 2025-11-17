# Tools to Disable in Cursor MCP Settings

**Total: 60 tools to disable** (reduces from 84 to 24 essential tools)

## 🔴 TINYMAN DEX Tools (9 tools) - DISABLE ALL

1. `api_tinyman_get_asset_optin_quote`
2. `api_tinyman_get_liquidity_quote`
3. `api_tinyman_get_pool`
4. `api_tinyman_get_pool_analytics`
5. `api_tinyman_get_pool_creation_quote`
6. `api_tinyman_get_remove_liquidity_quote`
7. `api_tinyman_get_swap_quote`
8. `api_tinyman_get_validator_optin_quote`
9. `api_tinyman_get_validator_optout_quote`

## 🔴 ULTRADE EXCHANGE Tools (25 tools) - DISABLE ALL

### Market Tools (21 tools)
1. `api_ultrade_market_assets`
2. `api_ultrade_market_balances`
3. `api_ultrade_market_cancel_order`
4. `api_ultrade_market_cancel_orders`
5. `api_ultrade_market_chains`
6. `api_ultrade_market_create_order`
7. `api_ultrade_market_create_orders`
8. `api_ultrade_market_depth`
9. `api_ultrade_market_details`
10. `api_ultrade_market_fee_rates`
11. `api_ultrade_market_history`
12. `api_ultrade_market_last_trades`
13. `api_ultrade_market_markets`
14. `api_ultrade_market_open_orders`
15. `api_ultrade_market_operation_details`
16. `api_ultrade_market_order_by_id`
17. `api_ultrade_market_order_message`
18. `api_ultrade_market_orders`
19. `api_ultrade_market_price`
20. `api_ultrade_market_settings`
21. `api_ultrade_market_symbols`
22. `api_ultrade_market_withdrawal_fee`

### Wallet Tools (10 tools)
23. `api_ultrade_wallet_add_key`
24. `api_ultrade_wallet_key_message`
25. `api_ultrade_wallet_keys`
26. `api_ultrade_wallet_revoke_key`
27. `api_ultrade_wallet_signin`
28. `api_ultrade_wallet_signin_message`
29. `api_ultrade_wallet_trades`
30. `api_ultrade_wallet_transactions`
31. `api_ultrade_wallet_withdraw`
32. `api_ultrade_wallet_withdraw_message`

### System Tools (3 tools)
33. `api_ultrade_system_maintenance`
34. `api_ultrade_system_time`
35. `api_ultrade_system_version`

## 🔴 VESTIGE DEFI Tools (26 tools) - DISABLE ALL

### Asset Tools (8 tools)
1. `api_vestige_view_asset_candles`
2. `api_vestige_view_asset_composition`
3. `api_vestige_view_asset_history`
4. `api_vestige_view_asset_notes_count`
5. `api_vestige_view_asset_price`
6. `api_vestige_view_assets`
7. `api_vestige_view_assets_list`
8. `api_vestige_view_assets_search`

### Swap Tools (6 tools)
9. `api_vestige_get_aggregator_stats`
10. `api_vestige_get_best_v4_swap_data`
11. `api_vestige_get_v4_swap_data_transactions`
12. `api_vestige_get_v4_swap_discount`
13. `api_vestige_view_swaps`

### Protocol Tools (3 tools)
14. `api_vestige_view_protocol_by_id`
15. `api_vestige_view_protocol_volumes`
16. `api_vestige_view_protocols`

### Network Tools (2 tools)
17. `api_vestige_view_network_by_id`
18. `api_vestige_view_networks`

### Other Tools (7 tools)
19. `api_vestige_view_balances`
20. `api_vestige_view_first_asset_notes`
21. `api_vestige_view_notes`
22. `api_vestige_view_pools`
23. `api_vestige_view_vaults`

---

## ✅ KEEP THESE (24 essential tools)

These are the core tools you need for Algorand smart contract development:

### Account Management (8 tools)
- `create_account`
- `rekey_account`
- `validate_address`
- `encode_address`
- `decode_address`
- `mnemonic_to_secret_key`
- `secret_key_to_mnemonic`
- `get_application_address`

### Smart Contract Transactions (7 tools)
- `make_payment_txn`
- `make_app_create_txn`
- `make_app_update_txn`
- `make_app_call_txn`
- `make_app_optin_txn`
- `sign_transaction`
- `assign_group_id`

### Essential Utilities (9 tools)
- `ping`
- `bytes_to_bigint`
- `bigint_to_bytes`
- `encode_uint64`
- `decode_uint64`
- `sign_bytes`
- `verify_bytes`
- `encode_obj`
- `decode_obj`

---

## 📝 How to Disable in Cursor

1. Open Cursor Settings → MCP Servers
2. Expand `algorand-mcp` (the working one with green dot)
3. Scroll through the tools list
4. **Uncheck** all tools starting with:
   - `api_tinyman_*` (9 tools)
   - `api_ultrade_*` (25 tools)
   - `api_vestige_*` (26 tools)
5. This will reduce from 84 to **24 essential tools** ✅

