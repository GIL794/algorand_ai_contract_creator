"""
Smart Contract Configuration
Defines schemas and settings for contract deployment
"""

import os
from pathlib import Path
from algosdk.transaction import StateSchema

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
GENERATED_CONTRACTS_PATH = PROJECT_ROOT / "smart_contracts" / "ai_generated"
ARTIFACTS_PATH = PROJECT_ROOT / "smart_contracts" / "artifacts"

# Ensure directories exist
GENERATED_CONTRACTS_PATH.mkdir(parents=True, exist_ok=True)
ARTIFACTS_PATH.mkdir(parents=True, exist_ok=True)

# Default state schemas for AI-generated contracts
DEFAULT_GLOBAL_SCHEMA = StateSchema(num_uints=4, num_byte_slices=4)
DEFAULT_LOCAL_SCHEMA = StateSchema(num_uints=2, num_byte_slices=2)

# Extended schemas for complex contracts
EXTENDED_GLOBAL_SCHEMA = StateSchema(num_uints=8, num_byte_slices=8)
EXTENDED_LOCAL_SCHEMA = StateSchema(num_uints=4, num_byte_slices=4)

# Network configurations
TESTNET_ALGOD_ADDRESS = os.getenv('ALGOD_ADDRESS', 'https://testnet-api.algonode.cloud')
TESTNET_ALGOD_TOKEN = os.getenv('ALGOD_TOKEN', 'a' * 64)

MAINNET_ALGOD_ADDRESS = 'https://mainnet-api.algonode.cloud'
MAINNET_ALGOD_TOKEN = 'a' * 64

# Contract deployment settings
DEFAULT_FEE = 1000  # microAlgos
MIN_BALANCE_REQUIREMENT = 100000  # microAlgos (0.1 ALGO)

# AI generation settings
AI_PROVIDER = os.getenv('AI_PROVIDER', 'perplexity')  # 'perplexity' or 'openai'
DEFAULT_MODEL = os.getenv('AI_MODEL', 'sonar')  # Use 'sonar' - latest default
GENERATION_TEMPERATURE = 0.2
MAX_GENERATION_RETRIES = 3
