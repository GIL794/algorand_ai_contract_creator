"""
AI Contract Generator with Multi-Layer Validation
Compliance: EU AI Act Tier 2, IEEE EAD
Supports: OpenAI GPT-4 and Perplexity AI
"""

from openai import OpenAI
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Optional

load_dotenv()

# Configure API keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
AI_PROVIDER = os.getenv('AI_PROVIDER', 'perplexity')

# Configure structured logging to canonical outputs/logs directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
LOG_DIR = PROJECT_ROOT / "outputs" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_DIR / 'ai_generations.log'),
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)


class ContractGenerator:
    """Deterministic PyTeal code generator with self-correction loop."""

    SYSTEM_PROMPT = """You are an expert Algorand blockchain developer specialized in PyTeal smart contracts.

YOU HAVE ACCESS TO REAL-TIME WEB SEARCH (if using Perplexity). If you need to verify PyTeal syntax or latest API changes, search for official documentation.

*CRITICAL REQUIREMENTS:*
1. Generate ONLY valid PyTeal code compatible with pyteal v0.24.0
2. **MUST** define both `approval_program()` and `clear_program()` functions
3. The `approval_program()` function MUST return a PyTeal expression (e.g., using Approve(), Reject(), Cond(), etc.)
4. The `clear_program()` function should typically return Approve() for simple contracts
5. Include comprehensive inline comments
6. Follow Algorand ASC1 security standards
7. Avoid:
   - Hardcoded addresses or keys
   - Unbounded loops
   - Reentrancy vulnerabilities
   - Unsafe global state manipulation
   - Integer overflow risks
8. Always include proper fee checks and transaction validation
9. Use defensive programming patterns
10. **CRITICAL**: Ensure ALL string literals are properly closed - no unterminated strings
11. **CRITICAL**: Generate COMPLETE code - do not truncate in the middle of functions, strings, or code blocks
12. **CRITICAL**: All functions must be complete with proper closing braces and return statements
13. **CRITICAL**: Use '==' for comparisons (NOT '=') - e.g., `if x == y:` NOT `if x = y:`
14. **CRITICAL**: Use ':=' (walrus operator) for assignment expressions if needed, but prefer regular assignments
15. **CRITICAL**: NEVER use '=' in if/while conditions - Python requires '==' for comparisons
16. **CRITICAL**: Use correct PyTeal comparison operators:
    - Ge (NOT Gte) for >= (greater than or equal)
    - Le (NOT Lte) for <= (less than or equal)
    - Gt for > (greater than)
    - Lt for < (less than)
    - Eq for == (equal)
    - Neq for != (not equal)
17. **CRITICAL**: Use Global.latest_timestamp() (NOT Global.latest_time) to get current timestamp

*TESTNET-SPECIFIC GUIDANCE:*
- This contract is for TESTNET use only - NOT for production/mainnet
- If testnet addresses are provided in the user description, USE THEM DIRECTLY in the contract code
- Replace any placeholder addresses with the actual testnet addresses provided
- Use proper PyTeal address handling: Addr("ACTUAL_TESTNET_ADDRESS_HERE")
- Add clear comments indicating these are testnet addresses: # TESTNET ADDRESS - Replace for mainnet
- If multiple addresses are provided, use them appropriately (e.g., for multi-sig, use all provided addresses)
- Always remind users this is TESTNET code and requires security audit before mainnet deployment

*OUTPUT STRUCTURE:*
1. Complete PyTeal source code with both approval_program() and clear_program() functions
2. Contract purpose summary (2-3 sentences)
3. Logic walkthrough (key conditions and branches)
4. Security considerations
5. Deployment parameters needed
6. Testnet address placeholders (if applicable)

*CODE STRUCTURE EXAMPLE:*
```python
from pyteal import *

def approval_program():
    # Your contract logic here
    # IMPORTANT: Return a PyTeal expression directly, NOT a function call
    return Approve()  # or Cond(), Seq(), If(), etc.
    # DO NOT return a function like: return some_function() where some_function is a Python function
    # DO return PyTeal expressions like: return If(condition, Approve(), Reject())

def clear_program():
    return Approve()

# Optional: Include if __name__ == "__main__" block for testing
if __name__ == "__main__":
    print(compileTeal(approval_program(), mode=Mode.Application, version=8))
    print(compileTeal(clear_program(), mode=Mode.Application, version=8))
```

*CRITICAL PYTEAL RULES:*
- approval_program() MUST return a PyTeal expression (Expr), NOT a Python function
- Use PyTeal expressions: Approve(), Reject(), If(), Cond(), Seq(), etc.
- DO NOT define helper functions that return PyTeal expressions and then call them in approval_program
- DO define helper functions that RETURN PyTeal expressions and use them directly: helper_expr = helper_function(); return helper_expr
- All PyTeal operations must be expressions, not statements
"""

    def __init__(self, model: str = "sonar", temperature: float = 0.2):
        self.model = model
        self.temperature = temperature
        self.generation_history = []
        self.ai_provider = AI_PROVIDER
        self.client = None

    def _get_client(self, provider: str) -> OpenAI:
        """Get configured OpenAI client for different providers."""
        if provider == 'perplexity':
            if not PERPLEXITY_API_KEY or PERPLEXITY_API_KEY == 'pplx-your-key-here':
                raise ValueError("PERPLEXITY_API_KEY not set. Please configure it in your .env file.")
            return OpenAI(
                api_key=PERPLEXITY_API_KEY,
                base_url="https://api.perplexity.ai"
            )
        else:  # openai
            if not OPENAI_API_KEY or OPENAI_API_KEY.startswith('sk-your-key'):
                raise ValueError("OPENAI_API_KEY not set. Please configure it in your .env file.")
        return OpenAI(api_key=OPENAI_API_KEY)

    def _get_model(self, provider: str, model: str) -> str:
        """Get appropriate model name for provider - uses correct Perplexity model names."""
        if provider == 'perplexity':
            if model in ['sonar', 'sonar-pro']:
                return model
            return 'sonar'
        else:  # openai
            if not model or not model.startswith('gpt'):
                return "gpt-4"
        return model

    def generate_pyteal_contract(
        self,
        description: str,
        max_retries: int = 3,
        ai_provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate PyTeal contract with automatic validation and retry.

        Args:
            description: Natural language contract description
            max_retries: Maximum retry attempts
            ai_provider: 'perplexity' or 'openai' (overrides default)
            model: Specific model to use (overrides default)

        Returns:
            Dict with keys: code, explanation, deployment, audit
        """
        provider = ai_provider or self.ai_provider
        selected_model = self._get_model(provider, model or self.model)
        client = self._get_client(provider)

        attempt = 0
        last_error = None

        while attempt < max_retries:
            try:
                logging.info(
                    f"Generation attempt {attempt + 1} for: "
                    f"{description[:100]} using {provider}/{selected_model}"
                )

                response = client.chat.completions.create(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": self._build_user_prompt(description, last_error)}
                    ],
                    temperature=self.temperature,
                    max_tokens=4000  # Increased to ensure complete code generation
                )

                # Safely extract response content
                if not response.choices or len(response.choices) == 0:
                    last_error = "AI API returned empty response. Please try again."
                    attempt += 1
                    logging.warning(f"Empty response from AI: {last_error}")
                    continue
                raw_output = response.choices[0].message.content
                if not raw_output:
                    last_error = "AI API returned empty content. Please try again."
                    attempt += 1
                    logging.warning(f"Empty content from AI: {last_error}")
                    continue
                parsed = self._parse_ai_response(raw_output)
                
                # Safety check: ensure parsed is a dict
                if not isinstance(parsed, dict):
                    last_error = "Failed to parse AI response. Response format was unexpected."
                    attempt += 1
                    logging.warning(f"Parse failed: {last_error}")
                    continue
                
                code = parsed.get('code', '')
                
                # Validate that code was extracted
                if not code or code == "No code extracted":
                    last_error = "No code could be extracted from AI response. Please ensure the AI generates valid PyTeal code in a code block."
                    attempt += 1
                    logging.warning(f"Code extraction failed: {last_error}")
                    continue
                
                validation_result = self._validate_pyteal_syntax(code)
                
                # Safety check: ensure validation_result is a dict
                if not isinstance(validation_result, dict):
                    last_error = "Validation returned unexpected result. Using default error."
                    validation_result = {"valid": False, "error": last_error}
                    logging.error(f"Validation result was not a dict: {type(validation_result)}")

                if validation_result.get('valid', False):
                    self._log_generation(
                        description, parsed, attempt + 1, provider, selected_model
                    )
                    return {
                        'success': True,
                        'code': code,
                        'explanation': parsed.get('explanation', ''),
                        'deployment': parsed.get('deployment', ''),
                        'audit': parsed.get('audit', ''),
                        'metadata': {
                            'model': selected_model,
                            'provider': provider,
                            'attempts': attempt + 1,
                            'timestamp': datetime.utcnow().isoformat()
                        }
                    }

                # Safely extract error message
                if isinstance(validation_result, dict):
                    last_error = validation_result.get('error', 'Unknown validation error')
                else:
                    last_error = f"Validation failed: {str(validation_result)}"
                attempt += 1
                logging.warning(f"Validation failed: {last_error}")
                
                # If it's a syntax error, provide more specific guidance
                if 'Syntax Error' in last_error or 'syntax error' in last_error.lower() or 'invalid syntax' in last_error.lower():
                    # Extract line number if available
                    line_info = ""
                    if 'line' in last_error.lower():
                        import re
                        line_match = re.search(r'line (\d+)', last_error, re.IGNORECASE)
                        if line_match:
                            line_num = int(line_match.group(1))
                            lines = code.split('\n')
                            if line_num <= len(lines):
                                problem_line = lines[line_num - 1]
                                line_info = f"\n\nProblematic line {line_num}: {problem_line}"
                    
                    # Check for common syntax errors
                    specific_guidance = ""
                    if "=' instead of '=='" in last_error or "=' instead of ':='" in last_error:
                        specific_guidance = "\n\n⚠️ CRITICAL: You used '=' (assignment) where you need '==' (comparison) or ':=' (walrus operator).\n- Use '==' for comparisons: if x == y:\n- Use ':=' for assignment expressions: if (result := some_function()):\n- NEVER use '=' in if/while conditions - it's invalid Python syntax!"
                    
                    last_error = f"SYNTAX ERROR DETECTED: {last_error}{line_info}{specific_guidance}\n\nPlease fix:\n- Ensure all string literals are properly closed with matching quotes\n- Use '==' for comparisons, not '='\n- Check for incomplete function definitions\n- Verify all parentheses, brackets, and braces are matched\n- Generate COMPLETE code - do not truncate in the middle of strings or functions"

            except Exception as e:
                last_error = str(e)
                attempt += 1
                logging.error(f"Generation error: {e}")

        return {
            'success': False,
            'error': f"Failed after {max_retries} attempts. Last error: {last_error}",
            'partial_code': None
        }

    def _build_user_prompt(self, description: str, previous_error: str = None) -> str:
        """Construct user prompt with self-correction context."""
        base = f"""Generate a PyTeal smart contract for the following requirement:

{description}

Ensure the contract is production-ready and follows all security guidelines."""
        if previous_error:
            base += f"""

PREVIOUS ATTEMPT FAILED WITH ERROR:
{previous_error}
"""
        return base

    def _parse_ai_response(self, raw_output: str) -> Dict[str, str]:
        """Extract PyTeal code from AI response, handling markdown code blocks."""
        import re
        
        # STEP 1: Find the code block and extract content
        code_start = raw_output.find('```')
        code = ""
        explanation_text = ""
        text_before_code = ""  # Initialize for use in section extraction
        
        if code_start != -1:
            # Get text BEFORE code block for explanation (intro text)
            text_before_code = raw_output[:code_start].strip()
            
            # Find the closing ``` marker after the opening one
            code_end = raw_output.find('```', code_start + 3)
            if code_end != -1:
                # CRITICAL: Extract ONLY the content between the opening and closing markers
                # Do NOT include anything after the closing marker
                code_content = raw_output[code_start + 3:code_end].strip()
                
                # Additional safety: if code_content somehow contains a closing marker, 
                # extract only up to that point
                if '```' in code_content:
                    code_content = code_content.split('```')[0].strip()
                
                # CRITICAL: Remove language identifier more aggressively
                # Handle cases like: ```python\ncode or ```python\n\ncode
                lines = code_content.split('\n')
                first_non_empty_idx = 0
                
                # Skip empty lines at the start
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped:
                        # Check if it's a language identifier
                        if stripped.lower() in ['python', 'py']:
                            first_non_empty_idx = i + 1
                        else:
                            first_non_empty_idx = i
                        break
                
                code_content = '\n'.join(lines[first_non_empty_idx:]).strip()
                
                # CRITICAL: Find where actual Python code starts
                # Look for: from pyteal, import pyteal, def, class, or # comments
                code_lines = code_content.split('\n')
                python_start_idx = -1
                
                for i, line in enumerate(code_lines):
                    stripped = line.strip()
                    # Skip empty lines
                    if not stripped:
                        continue
                    # Stop at markdown headers or horizontal rules (these shouldn't be in code block)
                    if stripped.startswith('##') or stripped.startswith('###') or stripped == '---':
                        break
                    # Check if this is actual Python code
                    if (re.match(r'^(from pyteal|import pyteal|from\s+pyteal|def\s+\w+|class\s+\w+)', stripped, re.IGNORECASE) or
                        stripped.startswith('#') or
                        stripped.startswith('from ') or
                        stripped.startswith('import ')):
                        python_start_idx = i
                        break
                    # If we see markdown patterns, skip them
                    if (stripped.startswith('**') and stripped.endswith('**') and 
                        not any(c in stripped for c in ['(', ')', '=', '[', ']', '"', "'", '#'])):
                        continue
                    # If we see text that's clearly not code, skip it
                    if any(phrase in stripped.lower() for phrase in [
                        'here is', 'this contract', 'production-ready', 'smart contract',
                        'time-locked', 'vault', 'releases funds'
                    ]) and not any(c in stripped for c in ['(', ')', '=', '[', ']', '"', "'", '#']):
                        continue
                
                # Extract only from Python code start
                if python_start_idx >= 0:
                    # Extract from Python start, but stop at any markdown markers
                    # IMPORTANT: Only stop if we're sure it's markdown, not legitimate Python code
                    final_code_lines = []
                    for i in range(python_start_idx, len(code_lines)):
                        line = code_lines[i]
                        stripped = line.strip()
                        
                        # CRITICAL: Stop at markdown markers - but be careful not to stop at legitimate code
                        # Only stop if it's clearly markdown (not in a string or comment)
                        if stripped == '---' and not any(c in line for c in ['"', "'", '#']):
                            # Horizontal rule - stop
                            break
                        if stripped.startswith('---') and len(stripped) >= 3 and not any(c in stripped for c in ['"', "'", '=', '#']):
                            break
                        # Markdown headers - but only if they're at the start of line and not in code
                        if (stripped.startswith('##') or stripped.startswith('###')) and not any(c in line for c in ['"', "'", '#']):
                            # Check if it's actually a markdown header (not a comment or string)
                            if not line.strip().startswith('#'):  # Not a Python comment
                                break
                        if stripped == '```' or (stripped.startswith('```') and len(stripped) <= 5):
                            break
                        # Stop at explanation section headers - but only if they're clearly markdown
                        if any(header in stripped for header in [
                            'Contract Purpose', 'Purpose Summary', 'Logic Walkthrough',
                            'Security Considerations', 'Security Audit', 'Deployment Parameters'
                        ]) and not any(c in line for c in ['"', "'", '#']):
                            # Only stop if it's not in a string or comment
                            break
                        final_code_lines.append(line)
                    code = '\n'.join(final_code_lines).strip()
                else:
                    # If we didn't find a clear start, try to find first line with Python keywords
                    for i, line in enumerate(code_lines):
                        stripped = line.strip()
                        if (stripped.startswith(('from ', 'import ', 'def ', 'class ')) or
                            (stripped.startswith('#') and 'pyteal' in stripped.lower())):
                            # Extract from here, but stop at markdown markers
                            final_code_lines = []
                            for j in range(i, len(code_lines)):
                                line2 = code_lines[j]
                                stripped2 = line2.strip()
                                if stripped2 == '---' or stripped2.startswith('---'):
                                    break
                                if stripped2.startswith('##') or stripped2.startswith('###'):
                                    break
                                if stripped2 == '```' or stripped2.startswith('```'):
                                    break
                                if any(header in stripped2 for header in [
                                    'Contract Purpose', 'Purpose Summary', 'Logic Walkthrough',
                                    'Security Considerations', 'Security Audit', 'Deployment Parameters'
                                ]):
                                    break
                                final_code_lines.append(line2)
                            code = '\n'.join(final_code_lines).strip()
                            break
                    else:
                        # Last resort: use everything but filter out markdown
                        # Still need to stop at markdown markers
                        final_code_lines = []
                        for line in code_lines:
                            stripped = line.strip()
                            if stripped == '---' or stripped.startswith('---'):
                                break
                            if stripped.startswith('##') or stripped.startswith('###'):
                                break
                            if stripped == '```' or stripped.startswith('```'):
                                break
                            if any(header in stripped for header in [
                                'Contract Purpose', 'Purpose Summary', 'Logic Walkthrough',
                                'Security Considerations', 'Security Audit', 'Deployment Parameters'
                            ]):
                                break
                            final_code_lines.append(line)
                        code = '\n'.join(final_code_lines).strip()
                
                # Get text after the code block for explanation sections
                explanation_text = raw_output[code_end + 3:].strip()
                # Also include text before code block in explanation
                if text_before_code:
                    if explanation_text:
                        explanation_text = text_before_code + "\n\n" + explanation_text
                    else:
                        explanation_text = text_before_code
            else:
                # No closing marker found
                code_content = raw_output[code_start + 3:].strip()
                lines = code_content.split('\n')
                if lines and lines[0].strip().lower() in ['python', 'py', '']:
                    code_content = '\n'.join(lines[1:]).strip()
                code = code_content
                explanation_text = raw_output[:code_start].strip()
        else:
            # No code blocks found - try to find Python code directly
            lines = raw_output.split('\n')
            code_lines = []
            in_code = False
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                
                # Start capturing when we see imports or def/class
                if re.match(r'^(from pyteal|import pyteal|from\s+pyteal|def\s+\w+|class\s+\w+)', stripped, re.IGNORECASE):
                    in_code = True
                    code_lines.append(line)
                elif in_code:
                    # Stop if we hit a markdown header (## or ###) or horizontal rule
                    if stripped.startswith('##') or stripped.startswith('###') or stripped == '---':
                        explanation_text = '\n'.join(lines[i:]).strip()
                        break
                    # Continue collecting code lines
                    code_lines.append(line)
            
            code = '\n'.join(code_lines).strip() if code_lines else raw_output
            if not explanation_text:
                explanation_text = raw_output
        
        # STEP 2: Aggressively clean the code - remove ALL markdown and non-Python text
        if code:
            lines = code.split('\n')
            cleaned_lines = []
            found_python_start = False
            in_code_block = False  # Track if we're in actual code
            lines_collected = 0  # Track how many lines we've collected
            
            for line in lines:
                stripped = line.strip()
                
                # CRITICAL: Stop at any markdown markers (these shouldn't be in code, but just in case)
                if stripped == '```' or (stripped.startswith('```') and len(stripped) <= 5):
                    # This is the end marker - stop immediately
                    break
                
                # IMPORTANT: Only stop at markdown if we haven't collected much code yet
                # If we've collected substantial code, be more careful about stopping
                # This prevents cutting off legitimate code that might look like markdown
                
                # CRITICAL: Stop at horizontal rules - but only if they're clearly markdown
                # Don't stop if we're in the middle of substantial code
                if lines_collected < 5 or (stripped == '---' and not any(c in line for c in ['"', "'", '=', '#'])):
                    if stripped == '---' or (stripped.startswith('---') and len(stripped) >= 3 and 
                                             not any(c in stripped for c in ['"', "'", '=', '#'])):
                        # Only stop if we haven't collected much code, or if it's clearly a markdown separator
                        if lines_collected < 10:
                            break
                
                # CRITICAL: Stop at markdown headers - but be careful
                # Only stop if we haven't collected much code yet
                if lines_collected < 10:
                    if (stripped.startswith('##') or stripped.startswith('###')) and not any(c in line for c in ['"', "'", '#']):
                        # Check if it's actually a markdown header (not a comment)
                        if not line.strip().startswith('#'):
                            break
                
                # CRITICAL: Stop at explanation section headers - but only early in extraction
                if lines_collected < 10:
                    if any(header in stripped for header in [
                        'Contract Purpose', 'Purpose Summary', 'Logic Walkthrough', 
                        'Security Considerations', 'Security Audit', 'Deployment Parameters',
                        'References', 'This contract is ready', '**Contract Purpose'
                    ]) and not any(c in line for c in ['"', "'", '#']):
                        break
                
                # Skip markdown bold text (unless it's in a string/comment)
                if (stripped.startswith('**') and stripped.endswith('**') and len(stripped) > 4 and
                    not any(c in stripped for c in ['(', ')', '=', '[', ']', '"', "'", '#'])):
                    continue
                
                # Skip introductory text that's clearly not code
                if not found_python_start:
                    # Skip lines that are clearly markdown/text, not code
                    if (any(phrase in stripped.lower() for phrase in [
                        'here is', 'this contract', 'production-ready', 'smart contract',
                        'time-locked', 'vault', 'releases funds', 'beneficiary'
                    ]) and not any(c in stripped for c in ['(', ')', '=', '[', ']', '"', "'", '#', 'import', 'from', 'def', 'class'])):
                        continue
                    # Once we find actual Python code, start keeping lines
                    if (stripped.startswith(('from ', 'import ', 'def ', 'class ', '#')) or
                        re.match(r'^[A-Z_][A-Z0-9_]*\s*=', stripped) or  # Variable assignment
                        re.match(r'^[a-z_][a-z0-9_]*\s*\(', stripped)):  # Function call
                        found_python_start = True
                        in_code_block = True
                
                # Keep lines if we've found Python start, or if they look like code
                if found_python_start or stripped.startswith(('from ', 'import ', 'def ', 'class ', '#')) or not stripped:
                    cleaned_lines.append(line)
                    lines_collected += 1
                    if found_python_start:
                        in_code_block = True
            
            code = '\n'.join(cleaned_lines).strip()
        
        # STEP 3: Final code cleanup - remove any remaining markdown markers
        # Remove lines that are just markdown code block markers
        if code:
            code_lines_final = []
            for line in code.split('\n'):
                stripped = line.strip()
                # Skip lines that are just markdown markers (```python, ```, etc.)
                if stripped and (stripped.startswith('```') or stripped == '```python' or stripped == '```py'):
                    continue
                code_lines_final.append(line)
            code = '\n'.join(code_lines_final).strip()
        
        # Remove leading ```python or ``` markers if still present (more aggressive)
        while code.startswith('```'):
            # Find the first newline after ```
            first_newline = code.find('\n')
            if first_newline > 0:
                code = code[first_newline:].strip()
            else:
                # No newline, try to find closing ```
                closing = code.find('```', 3)
                if closing > 0:
                    code = code[3:closing].strip()
                else:
                    # Just remove the leading ```
                    code = code[3:].strip()
            # Also remove language identifier if present
            if code.startswith('python') or code.startswith('py'):
                code = code[6:].strip() if code.startswith('python') else code[2:].strip()
        
        # STEP 4: Extract explanation sections from the text AFTER the code block
        explanation = ""
        deployment = ""
        audit = ""
        
        if explanation_text:
            # Extract different sections using markdown headers
            # Try multiple patterns to match various formats
            sections = {}
            
            # Contract Purpose Summary - try multiple patterns
            # Pattern 1: ### Contract Purpose or ### 📝 Contract Purpose
            # Pattern 2: **Contract Purpose Summary:** (bold format)
            purpose_patterns = [
                r'(?:###\s*[📝]*\s*)?Contract Purpose[:\s]*[\s\S]*?(?=\n---|\n###|\n##|Logic Walkthrough|Security|Deployment|$)',
                r'(?:\*\*)?Contract Purpose Summary[:\s]*\*\*?[\s\S]*?(?=\n---|\n###|\n##|Logic Walkthrough|Security|Deployment|$)',
                r'(?:###\s*)?Purpose Summary[:\s]*[\s\S]*?(?=\n---|\n###|\n##|Logic Walkthrough|Security|Deployment|$)',
                r'(?:###\s*)?Purpose[:\s]*[\s\S]*?(?=\n---|\n###|\n##|Logic Walkthrough|Security|Deployment|$)',
                r'\*\*Contract Purpose[:\s]*\*\*[\s\S]*?(?=\n---|\n###|\n##|Logic Walkthrough|Security|Deployment|$)',
            ]
            
            for pattern in purpose_patterns:
                purpose_match = re.search(pattern, explanation_text, re.IGNORECASE | re.MULTILINE)
                if purpose_match:
                    purpose_text = purpose_match.group(0).strip()
                    # Remove the header line itself (with emoji support)
                    purpose_text = re.sub(r'^#+\s*[📝]*\s*(?:Contract Purpose|Purpose Summary|Purpose)[:\s]*\n?', '', 
                                          purpose_text, flags=re.IGNORECASE | re.MULTILINE)
                    # Remove markdown formatting
                    purpose_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', purpose_text)
                    purpose_text = re.sub(r'^---+\s*$', '', purpose_text, flags=re.MULTILINE).strip()
                    if purpose_text:
                        sections['purpose'] = purpose_text
                        break
            
            # Logic Walkthrough - try multiple patterns
            logic_patterns = [
                r'(?:###\s*[🔍]*\s*)?Logic Walkthrough[:\s]*[\s\S]*?(?=\n---|\n###|\n##|Security|Deployment|$)',
                r'(?:###\s*)?Walkthrough[:\s]*[\s\S]*?(?=\n---|\n###|\n##|Security|Deployment|$)',
                r'\*\*Logic Walkthrough[:\s]*\*\*[\s\S]*?(?=\n---|\n###|\n##|Security|Deployment|$)',
                r'\*\*🔍 Logic Walkthrough[:\s]*\*\*[\s\S]*?(?=\n---|\n###|\n##|Security|Deployment|$)',
            ]
            
            for pattern in logic_patterns:
                logic_match = re.search(pattern, explanation_text, re.IGNORECASE | re.MULTILINE)
                if logic_match:
                    logic_text = logic_match.group(0).strip()
                    logic_text = re.sub(r'^#+\s*[🔍]*\s*Logic Walkthrough[:\s]*\n?', '', logic_text, 
                                       flags=re.IGNORECASE | re.MULTILINE)
                    logic_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', logic_text)
                    logic_text = re.sub(r'^---+\s*$', '', logic_text, flags=re.MULTILINE).strip()
                    if logic_text:
                        sections['logic'] = logic_text
                        break
            
            # Security Considerations / Audit - try multiple patterns
            security_patterns = [
                r'(?:###\s*[🔐]*\s*)?Security (Considerations|Audit|Summary)[:\s]*[\s\S]*?(?=\n---|\n###|\n##|Deployment|Parameters|$)',
                r'(?:###\s*)?Security[:\s]*[\s\S]*?(?=\n---|\n###|\n##|Deployment|Parameters|$)',
                r'\*\*Security (Considerations|Audit|Summary)[:\s]*\*\*[\s\S]*?(?=\n---|\n###|\n##|Deployment|Parameters|$)',
                r'\*\*🔐 Security[:\s]*\*\*[\s\S]*?(?=\n---|\n###|\n##|Deployment|Parameters|$)',
            ]
            
            for pattern in security_patterns:
                security_match = re.search(pattern, explanation_text, re.IGNORECASE | re.MULTILINE)
                if security_match:
                    security_text = security_match.group(0).strip()
                    security_text = re.sub(r'^#+\s*[🔐]*\s*Security (Considerations|Audit|Summary)[:\s]*\n?', '', 
                                          security_text, flags=re.IGNORECASE | re.MULTILINE)
                    security_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', security_text)
                    security_text = re.sub(r'^---+\s*$', '', security_text, flags=re.MULTILINE).strip()
                    if security_text:
                        sections['security'] = security_text
                        break
            
            # Deployment Parameters / Instructions - try multiple patterns
            deployment_patterns = [
                r'(?:###\s*[🚀]*\s*)?Deployment (Parameters|Instructions|Needed)[:\s]*[\s\S]*?(?=\n---|\n###|\n##|Security|Usage|This contract|References|$)',
                r'(?:###\s*)?Deployment[:\s]*[\s\S]*?(?=\n---|\n###|\n##|Security|Usage|This contract|References|$)',
                r'\*\*Deployment (Parameters|Instructions|Needed)[:\s]*\*\*[\s\S]*?(?=\n---|\n###|\n##|Security|Usage|This contract|References|$)',
                r'\*\*🚀 Deployment[:\s]*\*\*[\s\S]*?(?=\n---|\n###|\n##|Security|Usage|This contract|References|$)',
            ]
            
            for pattern in deployment_patterns:
                deployment_match = re.search(pattern, explanation_text, re.IGNORECASE | re.MULTILINE)
                if deployment_match:
                    deployment_text = deployment_match.group(0).strip()
                    deployment_text = re.sub(r'^#+\s*[🚀]*\s*Deployment (Parameters|Instructions|Needed)[:\s]*\n?', '', 
                                            deployment_text, flags=re.IGNORECASE | re.MULTILINE)
                    deployment_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', deployment_text)
                    deployment_text = re.sub(r'^---+\s*$', '', deployment_text, flags=re.MULTILINE).strip()
                    if deployment_text:
                        sections['deployment'] = deployment_text
                        break
            
            # Combine sections appropriately
            if 'purpose' in sections:
                explanation = sections['purpose']
            if 'logic' in sections:
                if explanation:
                    explanation += "\n\n" + sections['logic']
                else:
                    explanation = sections['logic']
            
            if 'security' in sections:
                audit = sections['security']
            
            if 'deployment' in sections:
                deployment = sections['deployment']
            
            # If we didn't find structured sections, try to extract from intro text or use all explanation text
            if not explanation:
                if text_before_code:
                    # Use intro text as explanation if no structured sections found
                    intro_clean = text_before_code
                    intro_clean = re.sub(r'^#+\s*[^\n]+\n?', '', intro_clean, flags=re.MULTILINE)
                    intro_clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', intro_clean)
                    intro_clean = re.sub(r'^---+\s*$', '', intro_clean, flags=re.MULTILINE).strip()
                    if intro_clean:
                        explanation = intro_clean[:500]  # Limit length
                elif explanation_text:
                    # If no structured sections found, use the explanation text as-is (cleaned)
                    # This is a fallback to show something rather than "No explanation provided"
                    fallback_text = explanation_text
                    # Remove markdown headers
                    fallback_text = re.sub(r'^#+\s*[^\n]+\n?', '', fallback_text, flags=re.MULTILINE)
                    # Remove horizontal rules
                    fallback_text = re.sub(r'^---+\s*$', '', fallback_text, flags=re.MULTILINE)
                    # Clean up bold markers but keep the text
                    fallback_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', fallback_text)
                    fallback_text = fallback_text.strip()
                    if fallback_text and len(fallback_text) > 50:  # Only use if substantial
                        explanation = fallback_text[:1000]  # Limit length but allow more than intro
            
            # Similar fallback for deployment and audit if not found
            if not deployment and explanation_text:
                # Try to find any deployment-related content
                deployment_fallback = re.search(r'[Dd]eployment[:\s]*[\s\S]*?(?=\n---|\n###|\n##|Security|References|$)', 
                                               explanation_text, re.IGNORECASE | re.MULTILINE)
                if deployment_fallback:
                    deployment = deployment_fallback.group(0).strip()
                    deployment = re.sub(r'^#+\s*[^\n]+\n?', '', deployment, flags=re.MULTILINE)
                    deployment = re.sub(r'\*\*([^*]+)\*\*', r'\1', deployment)
                    deployment = re.sub(r'^---+\s*$', '', deployment, flags=re.MULTILINE).strip()
            
            if not audit and explanation_text:
                # Try to find any security-related content
                security_fallback = re.search(r'[Ss]ecurity[:\s]*[\s\S]*?(?=\n---|\n###|\n##|Deployment|References|$)', 
                                             explanation_text, re.IGNORECASE | re.MULTILINE)
                if security_fallback:
                    audit = security_fallback.group(0).strip()
                    audit = re.sub(r'^#+\s*[^\n]+\n?', '', audit, flags=re.MULTILINE)
                    audit = re.sub(r'\*\*([^*]+)\*\*', r'\1', audit)
                    audit = re.sub(r'^---+\s*$', '', audit, flags=re.MULTILINE).strip()
        
        # FINAL SAFEGUARD: Ensure code doesn't contain any markdown content
        # This is a last check to prevent markdown from leaking into the code
        # BUT: Only stop if we're sure it's markdown, not legitimate code
        if code:
            code_lines = code.split('\n')
            final_code_lines = []
            code_line_count = 0
            for line in code_lines:
                stripped = line.strip()
                code_line_count += 1
                
                # CRITICAL: Stop immediately at code block markers
                if stripped == '```' or (stripped.startswith('```') and len(stripped) <= 5):
                    break
                
                # Only stop at markdown if we haven't collected much code yet
                # If we have substantial code, be very careful about stopping
                if code_line_count < 20:
                    # CRITICAL: Stop immediately at any markdown indicators (early in code)
                    if stripped == '---' and not any(c in line for c in ['"', "'", '=', '#']):
                        break
                    if (stripped.startswith('---') and len(stripped) >= 3 and 
                        not any(c in stripped for c in ['"', "'", '=', '#'])):
                        break
                    if (stripped.startswith('##') or stripped.startswith('###')) and not any(c in line for c in ['"', "'", '#']):
                        # Not a Python comment
                        if not line.strip().startswith('#'):
                            break
                    if any(header in stripped for header in [
                        'Contract Purpose', 'Purpose Summary', 'Logic Walkthrough',
                        'Security Considerations', 'Security Audit', 'Deployment Parameters',
                        '**Contract Purpose', '**Logic Walkthrough', '**Security', '**Deployment'
                    ]) and not any(c in line for c in ['"', "'", '#']):
                        break
                else:
                    # We have substantial code - only stop at very clear markdown markers
                    # Don't stop at things that might be legitimate code
                    if stripped == '---' and len(stripped) == 3 and not any(c in line for c in ['"', "'", '=', '#']):
                        # Only stop at standalone --- that's clearly markdown
                        break
                
                final_code_lines.append(line)
            code = '\n'.join(final_code_lines).strip()
        
        # Clean up any remaining markdown artifacts
        explanation = re.sub(r'^---+\s*$', '', explanation, flags=re.MULTILINE).strip() if explanation else ""
        deployment = re.sub(r'^---+\s*$', '', deployment, flags=re.MULTILINE).strip() if deployment else ""
        audit = re.sub(r'^---+\s*$', '', audit, flags=re.MULTILINE).strip() if audit else ""
        
        # Log what we extracted for debugging
        logging.debug(f"Extracted code length: {len(code)}, explanation length: {len(explanation)}, "
                     f"deployment length: {len(deployment)}, audit length: {len(audit)}")
        
        # Final validation: ensure code doesn't start with markdown
        if code and (code.startswith('---') or code.startswith('##') or code.startswith('###') or 
                     code.startswith('**Contract') or code.startswith('```')):
            logging.warning(f"Code still contains markdown at start: {code[:100]}")
            # Try to find where actual code starts
            lines = code.split('\n')
            for i, line in enumerate(lines):
                stripped = line.strip()
                if (stripped.startswith(('from ', 'import ', 'def ', 'class ')) or
                    (stripped.startswith('#') and not stripped.startswith('##'))):
                    code = '\n'.join(lines[i:]).strip()
                    break
        
        return {
            "code": code or "No code extracted",
            "explanation": explanation or "Generated PyTeal smart contract",
            "deployment": deployment or "Deploy using the Algorand TestNet deployment tab",
            "audit": audit or "Review the generated code for security best practices"
        }

    def _validate_pyteal_syntax(self, code: str) -> Dict[str, str]:
        """
        Validate PyTeal code structure and basic syntax.
        This is a preliminary check - actual compilation happens in algorand_utils.py
        """
        if not code or len(code.strip()) < 10:
            return {"valid": False, "error": "Code is empty or too short."}
        
        # Check for required function definitions
        has_approval = "def approval_program" in code or "approval_program" in code
        has_clear = "def clear_program" in code or "clear_program" in code
        
        if not has_approval:
            return {"valid": False, "error": "Missing approval_program() function definition."}
        
        # Clear program is optional but recommended - warn if missing
        if not has_clear:
            logging.warning("Generated code missing clear_program() - will use default clear program")
        
        # Check for basic PyTeal imports
        if "from pyteal import" not in code and "import pyteal" not in code:
            return {"valid": False, "error": "Missing PyTeal imports. Code must import from pyteal."}
        
        # Check for dangerous patterns (basic check)
        # Note: exec() and compile() are used internally for PyTeal execution, so we only check for user code
        dangerous_patterns = ["eval(", "__import__("]
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            # Skip comments and docstrings
            if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            
            # Check for common syntax error: using '=' instead of '==' in conditions
            # Look for patterns like: if x =, while x =, elif x =, etc.
            if any(stripped.startswith(keyword) for keyword in ['if ', 'elif ', 'while ', 'assert ']):
                # Check if there's a single '=' that's not '==' or ':='
                import re
                # Match patterns like "if x = y" or "while var = value" but not "if (x := y)" or "if x == y"
                # Pattern: word, optional spaces, single =, optional spaces, something that's not =
                if re.search(r'\b\w+\s*=\s*[^=:]', stripped) and '==' not in stripped and ':=' not in stripped:
                    # Additional check: make sure it's not inside parentheses (which might be valid walrus)
                    # This is a heuristic - actual compilation will catch it definitively
                    if stripped.count('=') == 1 and '(' not in stripped.split('=')[0]:
                        return {
                            "valid": False, 
                            "error": f"Python syntax error: invalid syntax at line {line_num}. You used '=' (assignment) where '==' (comparison) is required. Line: {line}\n\nFix: Change '=' to '==' for comparisons in if/while/elif statements."
                        }
            
            # Check for dangerous patterns
            for pattern in dangerous_patterns:
                if pattern in stripped:
                    return {"valid": False, "error": f"Dangerous pattern detected at line {line_num}: {pattern}. Security violation."}
        
        # Basic syntax check - try to compile as Python
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            # Provide more detailed error message
            error_msg = str(e)
            if hasattr(e, 'lineno') and e.lineno:
                lines = code.split('\n')
                if e.lineno <= len(lines):
                    problem_line = lines[e.lineno - 1]
                    error_msg = f"{error_msg}\nProblematic line {e.lineno}: {problem_line}"
            return {"valid": False, "error": f"Python syntax error: {error_msg}"}
        except Exception:
            # Other errors might be PyTeal-specific, which is OK
            pass
        
        return {"valid": True}

    def _log_generation(
        self,
        description: str,
        parsed: Dict[str, str],
        attempt: int,
        provider: str,
        model: str
    ) -> None:
        """Log successful generations to file."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "description": description,
            "attempt": attempt,
            "provider": provider,
            "model": model,
            "code_snippet": parsed.get('code', '')[:200]
        }
        logging.info(json.dumps(log_entry, indent=2))


# ---------------------------------------------------------------------
# Add-on utility function for contract explanation
# ---------------------------------------------------------------------

def explain_contract(code: str, ai_provider: Optional[str] = None) -> str:
    """
    Use AI to provide human-readable explanation of existing PyTeal code.
    """
    try:
        provider = ai_provider or AI_PROVIDER

        if provider == 'perplexity':
            if not PERPLEXITY_API_KEY or PERPLEXITY_API_KEY == 'pplx-your-key-here':
                raise ValueError("PERPLEXITY_API_KEY not set. Please configure it in your .env file.")
            client = OpenAI(
                api_key=PERPLEXITY_API_KEY,
                base_url="https://api.perplexity.ai"
            )
            model = "sonar"  # Use latest sonar model
        else:
            if not OPENAI_API_KEY or OPENAI_API_KEY.startswith('sk-your-key'):
                raise ValueError("OPENAI_API_KEY not set. Please configure it in your .env file.")
            client = OpenAI(api_key=OPENAI_API_KEY)
            model = "gpt-4"

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert at explaining blockchain smart contracts in simple terms. "
                        "Provide a clear, non-technical summary suitable for business stakeholders."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Explain this PyTeal smart contract:\n\n{code}\n\n"
                        "Include: purpose, key operations, user interactions, and risks."
                    )
                }
            ],
            temperature=0.3,
            max_tokens=800
        )
        if not response.choices or len(response.choices) == 0:
            return "Error: AI API returned empty response."
        content = response.choices[0].message.content
        return content if content else "Error: AI API returned empty content."

    except Exception as e:
        logging.error(f"Explanation generation failed: {e}")
        return f"Error generating explanation: {str(e)}"
