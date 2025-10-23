"""
Algorand AI Contract Creator
Production-grade AI-powered smart contract generator for Algorand blockchain

Main package initialization
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__description__ = "AI-powered Algorand smart contract generator with AlgoKit integration"

# Make key components available at package level
from tools.ai_engine import ContractGenerator, explain_contract
from tools.algorand_utils import AlgorandDeployer, create_simple_clear_program

__all__ = [
    "ContractGenerator",
    "explain_contract", 
    "AlgorandDeployer",
    "create_simple_clear_program",
]
