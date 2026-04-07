"""
Test suite for AI-assisted Algorand contract generation and deployment.

Tests are organized into two layers:
- Unit Tests (default): Use mocks and fixtures; no external API calls
- Integration Tests (optional): Call live LLM and Algorand APIs; requires RUN_LIVE_TESTS=1

Run with: pytest tests/ -v
Integration tests require environment variables: PERPLEXITY_API_KEY or OPENAI_API_KEY
"""

import pytest
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import modules to test
from algorand_ai_contractor.core.ai_engine import ContractGenerator
from algorand_ai_contractor.core.algorand_utils import AlgorandDeployer


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def generator():
    """Create a ContractGenerator instance for testing."""
    return ContractGenerator(temperature=0.2)


@pytest.fixture
def deployer():
    """Create an AlgorandDeployer instance (without connection verification)."""
    return AlgorandDeployer(verify_connection=False)


@pytest.fixture
def sample_pyteal_code():
    """Sample valid PyTeal code for testing."""
    return """
from pyteal import *

def approval_program():
    return Approve()

def clear_program():
    return Approve()
"""


@pytest.fixture
def sample_pyteal_with_logic():
    """Sample PyTeal with more logic for testing."""
    return """
from pyteal import *

def approval_program():
    return If(
        Txn.application_id() == Int(0),
        Approve(),
        Reject()
    )

def clear_program():
    return Approve()
"""


@pytest.fixture
def execution_context():
    """Mark whether we're running integration tests."""
    return {
        'run_integration': os.getenv('RUN_LIVE_TESTS', '0') == '1',
        'has_api_key': any([
            os.getenv('PERPLEXITY_API_KEY'),
            os.getenv('OPENAI_API_KEY')
        ])
    }


# ==============================================================================
# UNIT TESTS - Validation Logic
# ==============================================================================

class TestValidationLogic:
    """Unit tests for contract validation (no external API calls)."""
    
    def test_validate_empty_code(self, generator):
        """Empty code should fail validation."""
        result = generator._validate_pyteal_syntax("")
        assert result['valid'] is False
        assert "empty" in result['error'].lower()
    
    def test_validate_missing_approval_program(self, generator):
        """Code without approval_program should fail."""
        code = "def some_other_function():\n    pass"
        result = generator._validate_pyteal_syntax(code)
        assert result['valid'] is False
        assert "approval_program" in result['error'].lower()
    
    def test_validate_missing_pyteal_imports(self, generator):
        """Code without PyTeal imports should fail."""
        code = "def approval_program():\n    return 1"
        result = generator._validate_pyteal_syntax(code)
        assert result['valid'] is False
        assert "import" in result['error'].lower()
    
    def test_validate_dangerous_eval_pattern(self, generator):
        """Code with eval() should be rejected."""
        code = """
from pyteal import *

def approval_program():
    eval('dangerous')
    return Approve()
"""
        result = generator._validate_pyteal_syntax(code)
        assert result['valid'] is False
        assert "eval" in result['error'].lower() or "dangerous" in result['error'].lower()
    
    def test_validate_dangerous_import_pattern(self, generator):
        """Code with __import__() should be rejected."""
        code = """
from pyteal import *

def approval_program():
    __import__('os')
    return Approve()
"""
        result = generator._validate_pyteal_syntax(code)
        assert result['valid'] is False
        assert "__import__" in result['error'].lower() or "dangerous" in result['error'].lower()
    
    def test_validate_assignment_operator_error(self, generator):
        """Code using = instead of == in conditions should fail."""
        code = """
from pyteal import *

def approval_program():
    if x = 5:
        return Approve()
    return Reject()
"""
        result = generator._validate_pyteal_syntax(code)
        assert result['valid'] is False
    
    def test_validate_valid_code(self, generator, sample_pyteal_code):
        """Valid PyTeal code should pass validation."""
        result = generator._validate_pyteal_syntax(sample_pyteal_code)
        assert result['valid'] is True
    
    def test_validate_valid_code_with_logic(self, generator, sample_pyteal_with_logic):
        """Valid PyTeal with If/Else logic should pass validation."""
        result = generator._validate_pyteal_syntax(sample_pyteal_with_logic)
        assert result['valid'] is True


# ==============================================================================
# UNIT TESTS - LLM Response Parsing
# ==============================================================================

class TestResponseParsing:
    """Unit tests for parsing LLM responses (no external API calls)."""
    
    def test_parse_basic_code_block(self, generator):
        """Parse code from markdown code block."""
        response = """
Here's your contract:

```python
from pyteal import *

def approval_program():
    return Approve()

def clear_program():
    return Approve()
```

This is a simple contract.
"""
        result = generator._parse_ai_response(response)
        assert "approval_program" in result['code']
        assert "from pyteal import" in result['code']
    
    def test_parse_code_with_sections(self, generator):
        """Parse code and extract sections."""
        response = """
```python
from pyteal import *

def approval_program():
    return Approve()

def clear_program():
    return Approve()
```

### Contract Purpose
This approves all transactions.

### Security Audit
No special security notes.
"""
        result = generator._parse_ai_response(response)
        assert "approval_program" in result['code']
        assert result['explanation'] != ""
    
    def test_parse_code_with_markdown_headers(self, generator):
        """Parse code when surrounded by markdown headers."""
        response = """
## Generated Contract

```python
from pyteal import *

def approval_program():
    return Approve()
```

## How It Works
Approves everything.
"""
        result = generator._parse_ai_response(response)
        assert "approval_program" in result['code']
        assert "Generated Contract" not in result['code']  # Headers removed


# ==============================================================================
# UNIT TESTS - Compilation
# ==============================================================================

class TestCompilation:
    """Unit tests for PyTeal compilation (mocked algod)."""
    
    def test_compile_rejects_invalid_syntax(self, deployer):
        """Invalid Python syntax should fail compilation."""
        invalid_code = """
from pyteal import *

def approval_program():
    this is not valid python!!
"""
        result = deployer.compile_pyteal_to_teal(invalid_code)
        assert result['success'] is False
        assert 'error' in result


# ==============================================================================
# UNIT TESTS - Artifact Integrity
# ==============================================================================

class TestArtifactIntegrity:
    """Unit tests for generated artifact handling."""
    
    def test_generated_code_not_empty(self, generator):
        """Generated code should not be empty."""
        code = """
from pyteal import *

def approval_program():
    return Approve()

def clear_program():
    return Approve()
"""
        result = generator._parse_ai_response(code)
        assert result['code'] != "" and result['code'] != "No code extracted"
    
    def test_validation_prevents_incomplete_functions(self, generator):
        """Validation should catch incomplete function definitions."""
        incomplete_code = """
from pyteal import *

def approval_program():
    return If(
        Txn.application_id() == Int(0),
"""
        result = generator._validate_pyteal_syntax(incomplete_code)
        assert result['valid'] is False


# ==============================================================================
# INTEGRATION TESTS - Live API Calls (Optional)
# ==============================================================================

@pytest.mark.integration
class TestLiveGeneration:
    """Integration tests that call live LLM APIs (optional)."""
    
    @pytest.mark.skipif(
        os.getenv('RUN_LIVE_TESTS') != '1' or not any([os.getenv('PERPLEXITY_API_KEY'), os.getenv('OPENAI_API_KEY')]),
        reason="Requires RUN_LIVE_TESTS=1 and valid API key"
    )
    def test_simple_contract_generation(self, generator):
        """Generate a simple contract using live API."""
        description = "Create a contract that returns approve"
        result = generator.generate_pyteal_contract(description, max_retries=1)
        
        assert 'success' in result
        if result.get('success'):
            assert 'code' in result
            assert 'approval_program' in result['code']


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires API keys)"
    )