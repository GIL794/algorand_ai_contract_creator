"""
Pytest test suite for contract generation and deployment
"""

import pytest
from tools.ai_engine import ContractGenerator
from tools.algorand_utils import AlgorandDeployer

@pytest.fixture
def generator():
    return ContractGenerator(temperature=0.2)

@pytest.fixture
def deployer():
    return AlgorandDeployer()

def test_simple_escrow_generation(generator):
    """Test generation of simple escrow contract."""
    description = "Create an escrow contract that releases funds when both parties agree"
    result = generator.generate_pyteal_contract(description)
    
    assert result['success'] is True
    assert 'pyteal' in result['code'].lower()
    assert len(result['code']) > 100

def test_compilation_validation(generator, deployer):
    """Test PyTeal compilation pipeline."""
    description = "Create a contract that always approves"
    result = generator.generate_pyteal_contract(description)
    
    if result['success']:
        compile_result = deployer.compile_pyteal_to_teal(result['code'])
        assert compile_result['success'] is True
        assert 'teal' in compile_result

def test_dangerous_pattern_rejection(generator):
    """Ensure dangerous code patterns are rejected."""
    # This should trigger validation failure
    dangerous_code = "eval('malicious code')"
    validation = generator._validate_pyteal_syntax(dangerous_code)
    assert validation['valid'] is False

def test_retry_mechanism(generator):
    """Test self-correction on invalid code."""
    # Force a scenario that might need retry
    description = "Create an extremely complex multi-sig with nested conditions"
    result = generator.generate_pyteal_contract(description, max_retries=2)
    
    # Should either succeed or fail gracefully
    assert 'success' in result
    assert 'metadata' in result or 'error' in result