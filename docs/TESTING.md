# Testing Guide

This document explains how to run, write, and maintain tests for the Algorand AI Contract Creator.

## Quick Start

### Run Unit Tests Only (Default)

No API keys required. These tests use mocks and fixtures.

```bash
pytest tests/ -v
```

This runs all tests marked as NOT integration.

### Run Integration Tests (Optional)

Requires valid API keys in `.env` and environment variable set:

```bash
# Export for this session
export RUN_LIVE_TESTS=1
export PERPLEXITY_API_KEY=your-key-here  # or OPENAI_API_KEY=...

# Run all tests (unit + integration)
pytest tests/ -v
```

Or on Windows:

```bash
set RUN_LIVE_TESTS=1
set PERPLEXITY_API_KEY=your-key-here
pytest tests/ -v
```

### Run Specific Test Categories

```bash
# Unit tests only (default)
pytest tests/ -v -m "not integration"

# Integration tests only
pytest tests/ -v -m integration

# Specific test class
pytest tests/test_contracts.py::TestValidationLogic -v

# Specific test function
pytest tests/test_contracts.py::TestValidationLogic::test_validate_empty_code -v
```

## Test Organization

Tests are organized into layers:

### Unit Tests (always run by default)

These tests do NOT make external API calls:

- **TestValidationLogic** – Contract validation (empty code, missing functions, dangerous patterns, syntax)
- **TestResponseParsing** – LLM response parsing (code extraction, section parsing, markdown handling)
- **TestCompilation** – PyTeal compilation (with mocked algod client)
- **TestArtifactIntegrity** – Generated code completeness, truncation detection
- **TestLogging** – Logging configuration and behavior

**When to use unit tests:**
- ✅ Local development
- ✅ Pre-commit validation
- ✅ CI/CD pipelines
- ✅ Testing without secrets

### Integration Tests (marked with @pytest.mark.integration)

These tests call live LLM and Algorand APIs:

- **TestLiveGeneration** – Real contract generation using Perplexity/OpenAI
- **TestLiveCompilation** – Real compilation against Algorand node

**When to use integration tests:**
- ✅ Full end-to-end validation
- ✅ Nightly/weekly CI runs
- ✅ Before releases
- ✅ When you have valid API keys

**Do NOT use integration tests:**
- ❌ In local development without need
- ❌ In pull requests (wastes tokens, slow)
- ❌ Without valid API keys

## Writing New Tests

### 1. Add Unit Test (Recommended)

Unit tests use mocks and should not call external APIs:

```python
def test_my_validation_rule(generator):
    """Test a specific validation rule."""
    code = "some invalid pyteal"
    result = generator._validate_pyteal_syntax(code)
    assert result['valid'] is False
    assert "expected error" in result['error'].lower()
```

### 2. Use Fixtures

Fixtures provide common test data:

```python
def test_with_sample_code(generator, sample_pyteal_code):
    """Test using pre-defined sample code."""
    result = generator._validate_pyteal_syntax(sample_pyteal_code)
    assert result['valid'] is True
```

### 3. Mock External Services

Use `unittest.mock.patch()` for mocking algod or LLM APIs:

```python
from unittest.mock import patch, MagicMock

def test_compile_with_mock(deployer):
    """Test compilation with mocked algod client."""
    with patch('algorand_ai_contractor.core.algorand_utils.algod.AlgodClient') as mock_algod:
        mock_client = MagicMock()
        mock_client.compile.return_value = {'result': 'hex_result', 'hash': 'hash'}
        deployer.algod_client = mock_client
        
        result = deployer.compile_pyteal_to_teal("valid pyteal code")
        assert result['success'] is True
```

### 4. Add Integration Test (If Needed)

For testing against live APIs:

```python
@pytest.mark.integration
class TestLiveFeature:
    @pytest.mark.skipif(
        os.getenv('RUN_LIVE_TESTS') != '1' or not os.getenv('PERPLEXITY_API_KEY'),
        reason="Requires RUN_LIVE_TESTS=1 and PERPLEXITY_API_KEY"
    )
    def test_live_generation(self, generator):
        """Test with real LLM API."""
        result = generator.generate_pyteal_contract("simple description")
        assert result.get('success')
```

## CI/CD Integration

GitHub Actions runs tests automatically:

### Default (On Every Push/PR)
- ✅ Python 3.10 and 3.11
- ✅ Unit tests only
- ✅ Black formatting check
- ✅ Pylint linting (soft fail)
- ✅ Documentation validation
- ✅ Outputs directory structure validation

### On Main Branch (Post-Merge)
- ✅ Integration tests (if API keys available in secrets)
- ✅ Full end-to-end validation

See [.github/workflows/tests.yml](.github/workflows/tests.yml) for details.

## Common Test Patterns

### Testing Validation Rules

```python
def test_validation_rule(generator):
    # Test failure case
    invalid_code = "malformed code"
    result = generator._validate_pyteal_syntax(invalid_code)
    assert result['valid'] is False
    assert "expected error text" in result['error'].lower()
    
    # Test success case
    valid_code = "from pyteal import *\n\ndef approval_program():\n    return Approve()"
    result = generator._validate_pyteal_syntax(valid_code)
    assert result['valid'] is True
```

### Testing Response Parsing

```python
def test_parse_response(generator):
    response = "some LLM response with code blocks"
    result = generator._parse_ai_response(response)
    
    # Check structure
    assert 'code' in result
    assert 'explanation' in result
    
    # Check content
    assert result['code'] != "No code extracted"
    assert "from pyteal" in result['code'] or "import pyteal" in result['code']
```

### Testing with Mocks

```python
def test_with_mock(deployer):
    with patch('some.module.Class') as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        mock_instance.method.return_value = expected_result
        
        # Call function being tested
        result = deployer.do_something()
        
        # Verify
        assert result == expected_result
        mock_instance.method.assert_called_once()
```

## Debugging Tests

### Run with Verbose Output

```bash
pytest tests/ -vv --tb=long
```

### Run Single Test with Debugging

```bash
pytest tests/test_contracts.py::TestValidationLogic::test_validate_empty_code -vv --tb=long -s
```

The `-s` flag shows all `print()` output.

### Use pytest markers

```bash
# See all available markers
pytest --markers

# Run tests matching a pattern
pytest tests/ -k "validation" -v

# Run specific test by name
pytest tests/ -k "test_validate_empty_code" -v
```

## Troubleshooting

### Tests fail with "module not found"

**Solution:** Install in editable mode:
```bash
pip install -e ".[dev]"
```

### Integration tests skip or fail with API errors

**Solution:** Check environment variables:
```bash
echo $PERPLEXITY_API_KEY  # Should not be empty
echo $RUN_LIVE_TESTS      # Should be "1" for integration tests
```

### Tests pass locally but fail in CI

**Possible causes:**
- Python version mismatch (always test 3.10+)
- Missing environment variable in CI secrets
- File path issues on different OS (use `Path` from pathlib)

**Solution:**
```bash
# Test with same Python version as CI
python --version
# Ensure all dependencies are installed
pip install -e ".[dev]"
# Run exact same pytest command as CI
pytest tests/ -v -m "not integration"
```

### Mock not working as expected

**Solution:** Check patch target path:
```python
# ❌ WRONG - patches the wrong location
with patch('algorand_ai_contractor.core.algorand_utils.AlgodClient'):
    
# ✅ CORRECT - patches where it's used
with patch('algorand_ai_contractor.core.algorand_utils.algod.AlgodClient'):
```

## Performance & Coverage

### Run with coverage report

```bash
pytest tests/ --cov=src/algorand_ai_contractor --cov-report=html
# Opens htmlcov/index.html in browser
```

### Profile slow tests

```bash
pytest tests/ --durations=10  # Shows 10 slowest tests
```

## Best Practices

1. **Keep unit tests fast** – Target <1 second per test
2. **Use descriptive names** – `test_validate_empty_code` is better than `test_1`
3. **One assertion per test** – Easier to debug
4. **Mock external services** – Never call real APIs in unit tests
5. **Use fixtures** – Avoid duplicating test data
6. **Document non-obvious tests** – Use docstrings
7. **Clean up after tests** – Remove temp files if created
8. **Mark integration tests** – Use `@pytest.mark.integration`
9. **Test edge cases** – Empty inputs, None values, boundary conditions
10. **Keep tests independent** – Tests should pass in any order

## Questions?

- Review existing tests in [tests/test_contracts.py](../tests/test_contracts.py)
- Check pytest docs: https://docs.pytest.org/
- See Contributing guidelines: [CONTRIBUTING.md](../CONTRIBUTING.md)
