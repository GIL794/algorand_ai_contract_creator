"""
Algorand TestNet Deployment & Validation Utilities
Supports compilation, simulation, and deployment
"""

import os
import base64
import logging
from pathlib import Path
from typing import Dict, Optional
from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk.transaction import ApplicationCreateTxn, OnComplete, StateSchema, wait_for_confirmation
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
LOG_DIR = PROJECT_ROOT / "outputs" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)
if not logger.handlers:
    file_handler = logging.FileHandler(LOG_DIR / "deployment.log")
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)


class AlgorandDeployer:
    """Secure deployment manager for Algorand TestNet."""
    
    def __init__(self, verify_connection: bool = True):
        self.algod_token = os.getenv('ALGOD_TOKEN', 'a' * 64)
        self.algod_address = os.getenv('ALGOD_ADDRESS', 'https://testnet-api.algonode.cloud')
        self.algod_client = algod.AlgodClient(
            self.algod_token,
            self.algod_address
        )
        if verify_connection:
            try:
                self._verify_connection()
            except Exception as e:
                logger.warning(f"Could not verify Algorand connection at initialization: {e}")
                # Don't raise - allow deferred connection
    
    def _verify_connection(self):
        """Test Algorand node connectivity."""
        try:
            status = self.algod_client.status()
            logger.info(f"Connected to Algorand TestNet - Round: {status.get('last-round', 'unknown')}")
        except Exception as e:
            logger.error(f"Algorand connection failed: {e}")
            raise ConnectionError("Cannot connect to Algorand node")
    
    def compile_pyteal_to_teal(self, pyteal_code: str, mode=None) -> Dict:
        """
        Compile PyTeal source to TEAL bytecode with validation.
        
        Returns:
            Dict with 'success', 'teal', 'compiled', 'error'
        """
        # Lazy import pyteal to avoid startup issues
        try:
            from pyteal import compileTeal, Mode, Approve
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to import PyTeal: {str(e)}. Please ensure pyteal is installed and compatible with Python 3.13.'
            }
        
        if mode is None:
            mode = Mode.Application
        
        try:
            # Clean the code - remove any markdown artifacts that might remain
            import re
            cleaned_code = pyteal_code.strip()
            
            # Remove markdown code block markers at the start/end
            cleaned_code = re.sub(r'^```(?:python|py)?\s*\n?', '', cleaned_code, flags=re.MULTILINE)
            cleaned_code = re.sub(r'```\s*$', '', cleaned_code, flags=re.MULTILINE)
            
            # Remove any lines that are just markdown markers or markdown formatting
            lines = cleaned_code.split('\n')
            cleaned_lines = []
            for line in lines:
                stripped = line.strip()
                # Skip markdown artifacts
                if stripped.startswith('```'):
                    continue
                # Skip markdown headers
                if stripped.startswith('###') or (stripped.startswith('##') and not stripped.startswith('## ')):
                    continue
                # Skip markdown horizontal rules
                if stripped.startswith('---') or stripped.startswith('***') or stripped.startswith('==='):
                    continue
                # Skip markdown bold/italic on their own lines
                if (stripped.startswith('**') and stripped.endswith('**') and len(stripped) > 4 and 
                    not any(c in stripped for c in ['(', ')', '=', '[', ']'])):
                    continue
                # Keep everything else (including empty lines and actual code)
                cleaned_lines.append(line)
            cleaned_code = '\n'.join(cleaned_lines).strip()
            
            # Final check - if still starts with ```, remove it
            if cleaned_code.startswith('```'):
                first_newline = cleaned_code.find('\n')
                if first_newline > 0:
                    cleaned_code = cleaned_code[first_newline:].strip()
                else:
                    closing = cleaned_code.find('```', 3)
                    if closing > 0:
                        cleaned_code = cleaned_code[3:closing].strip()
            
            # Validate that we have actual code
            if not cleaned_code or len(cleaned_code) < 10:
                return {
                    'success': False,
                    'error': 'No valid PyTeal code found. The code appears to be empty or too short.'
                }
            
            # Check if it looks like Python code
            if not (cleaned_code.startswith('from ') or cleaned_code.startswith('import ') or 
                    cleaned_code.startswith('def ') or cleaned_code.startswith('class ')):
                return {
                    'success': False,
                    'error': f'Code does not appear to be valid Python/PyTeal. First 100 chars: {cleaned_code[:100]}'
                }
            
            # Check for common string literal issues
            # Count quotes to detect unmatched strings (simplified but more reliable approach)
            # This is a basic heuristic - actual parsing would be more accurate but slower
            try:
                # Simple check: try to compile the code as Python to catch syntax errors early
                compile(cleaned_code, '<string>', 'exec')
            except SyntaxError as syntax_err:
                # If it's a syntax error related to quotes, provide helpful message
                if 'unterminated string literal' in str(syntax_err).lower() or 'EOL' in str(syntax_err):
                    return {
                        'success': False,
                        'error': f'Unterminated string literal detected: {syntax_err}. Please check quotes in the generated code. Line {syntax_err.lineno if hasattr(syntax_err, "lineno") else "unknown"}.'
                    }
                # For other syntax errors, let them be caught by the exec() call below
                pass
            except Exception:
                # Other compilation errors are OK - they might be PyTeal-specific
                pass
            
            # Create temporary namespace for exec
            namespace = {}
            
            # Add pyteal imports to namespace for exec
            # Import common PyTeal functions that might be used
            from pyteal import (
                Approve, Reject, Return, If, Seq, And, Or, Not,
                Int, Bytes, Txn, Global, App, Cond, Assert,
                Len, Substring, Concat, Btoi, Itob,
                Add, Minus, Mul, Div, Mod,
                Eq, Neq, Gt, Ge, Lt, Le,  # Note: Ge (not Gte), Le (not Lte)
                compileTeal, Mode, OnComplete,
                InnerTxnBuilder, TxnField, TxnType,
                Balance, Addr
            )
            namespace.update({
                'Approve': Approve,
                'Reject': Reject,
                'Return': Return,
                'If': If,
                'Seq': Seq,
                'And': And,
                'Or': Or,
                'Not': Not,
                'Int': Int,
                'Bytes': Bytes,
                'Txn': Txn,
                'Global': Global,
                'App': App,
                'compileTeal': compileTeal,
                'Mode': Mode,
                'Cond': Cond,
                'Assert': Assert,
                'Len': Len,
                'Substring': Substring,
                'Concat': Concat,
                'Btoi': Btoi,
                'Itob': Itob,
                'Add': Add,
                'Minus': Minus,
                'Mul': Mul,
                'Div': Div,
                'Mod': Mod,
                'Eq': Eq,
                'Neq': Neq,
                'Gt': Gt,
                'Ge': Ge,  # Greater than or equal (NOT Gte)
                'Gte': Ge,  # Alias for backward compatibility
                'Lt': Lt,
                'Le': Le,  # Less than or equal (NOT Lte)
                'Lte': Le,  # Alias for backward compatibility
                'OnComplete': OnComplete,
                'InnerTxnBuilder': InnerTxnBuilder,
                'TxnField': TxnField,
                'TxnType': TxnType,
                'Balance': Balance,
                'Addr': Addr,
            })
            
            # Execute PyTeal code to get program
            exec(cleaned_code, namespace)
            
            # Look for approval_program or router
            approval_program = None
            clear_program_obj = None
            
            # First, try to find approval_program
            for name in ['approval_program', 'router', 'app']:
                if name in namespace:
                    approval_program = namespace[name]
                    break
            
            # Also try to find clear_program if it exists
            if 'clear_program' in namespace:
                clear_program_obj = namespace['clear_program']
            
            if approval_program is None:
                # Try to find any Expr object
                for obj in namespace.values():
                    if hasattr(obj, '_class_') and 'pyteal' in str(type(obj)).lower():
                        approval_program = obj
                        break
            
            if approval_program is None:
                return {
                    'success': False,
                    'error': 'No PyTeal program found. Ensure you define approval_program() function that returns a PyTeal expression.'
                }
            
            # If approval_program is a callable (function), call it to get the PyTeal expression
            # compileTeal() expects a PyTeal Expr object, not a Python function
            if callable(approval_program):
                try:
                    approval_program = approval_program()
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'Failed to call approval_program() function: {e}. Ensure it returns a PyTeal expression.'
                    }
            
            # Compile to TEAL
            teal_code = compileTeal(approval_program, mode, version=8)
            
            # Compile TEAL to bytecode
            compile_response = self.algod_client.compile(teal_code)
            
            # Safely extract response fields
            compiled_result = compile_response.get('result', '')
            compiled_hash = compile_response.get('hash', '')
            
            return {
                'success': True,
                'teal': teal_code,
                'compiled': compiled_result,
                'hash': compiled_hash,
                'error': None
            }
            
        except SyntaxError as e:
            error_msg = f'Syntax Error: {e}'
            # Try to provide more context
            if hasattr(e, 'lineno') and e.lineno:
                lines = cleaned_code.split('\n')
                if e.lineno <= len(lines):
                    error_line = lines[e.lineno-1]
                    error_msg += f'\n\nLine {e.lineno}: {error_line}'
                    # Show context around the error
                    start_line = max(0, e.lineno - 3)
                    end_line = min(len(lines), e.lineno + 2)
                    context_lines = lines[start_line:end_line]
                    error_msg += f'\n\nContext (lines {start_line+1}-{end_line}):'
                    for i, line in enumerate(context_lines, start=start_line+1):
                        marker = '>>> ' if i == e.lineno else '    '
                        error_msg += f'\n{marker}{i}: {line}'
            return {'success': False, 'error': error_msg}
        except NameError as e:
            return {'success': False, 'error': f'Name Error: {e}. Make sure all PyTeal functions are properly imported.'}
        except AttributeError as e:
            error_msg = f'Attribute Error: {e}'
            # Provide helpful guidance for common PyTeal errors
            if 'has_return' in str(e):
                error_msg += '\n\n💡 This usually means you are trying to use a Python function where a PyTeal expression is expected.'
                error_msg += '\n   - approval_program() must return a PyTeal expression (Expr), not a Python function'
                error_msg += '\n   - Use PyTeal expressions directly: return If(...), return Cond(...), return Seq(...)'
                error_msg += '\n   - DO NOT call Python functions that return PyTeal - use the expressions directly'
            return {'success': False, 'error': error_msg}
        except Exception as e:
            error_msg = f'Compilation failed: {str(e)}'
            # Add context for common errors
            if 'has_return' in str(e) or 'function' in str(e).lower():
                error_msg += '\n\n💡 Tip: Ensure approval_program() returns a PyTeal expression, not a function call.'
            return {'success': False, 'error': f'{error_msg}\n\nCode preview:\n{cleaned_code[:500]}'}
    
    def deploy_contract(
        self,
        approval_teal: str,
        clear_teal: str,
        sender_private_key: str,
        global_schema: StateSchema = StateSchema(num_uints=1, num_byte_slices=1),
        local_schema: StateSchema = StateSchema(num_uints=0, num_byte_slices=0)
    ) -> Dict:
        """
        Deploy smart contract to Algorand TestNet.
        
        Args:
            approval_teal: TEAL approval program
            clear_teal: TEAL clear program
            sender_private_key: Private key for deployment account
            global_schema: Global state schema
            local_schema: Local state schema
        
        Returns:
            Dict with app_id, txn_id, address
        """
        try:
            # Derive address from private key
            sender_address = account.address_from_private_key(sender_private_key)
            
            # Compile programs
            approval_compiled = self.algod_client.compile(approval_teal)
            clear_compiled = self.algod_client.compile(clear_teal)
            
            # Safely extract compilation results
            approval_result = approval_compiled.get('result')
            clear_result = clear_compiled.get('result')
            
            if not approval_result:
                raise ValueError("Failed to compile approval program")
            if not clear_result:
                raise ValueError("Failed to compile clear program")
            
            approval_program = base64.b64decode(approval_result)
            clear_program = base64.b64decode(clear_result)
            
            # Get suggested params
            params = self.algod_client.suggested_params()
            
            # Create application transaction
            txn = ApplicationCreateTxn(
                sender=sender_address,
                sp=params,
                on_complete=OnComplete.NoOpOC,
                approval_program=approval_program,
                clear_program=clear_program,
                global_schema=global_schema,
                local_schema=local_schema
            )
            
            # Sign transaction
            signed_txn = txn.sign(sender_private_key)
            
            # Send transaction
            txid = self.algod_client.send_transaction(signed_txn)
            
            # Wait for confirmation
            confirmed_txn = wait_for_confirmation(self.algod_client, txid, 4)
            
            # Safely extract app_id
            app_id = confirmed_txn.get('application-index')
            if app_id is None:
                raise ValueError("Transaction confirmed but no application index found")
            
            app_address = self._get_app_address(app_id)
            
            logger.info(f"Contract deployed - App ID: {app_id}, Txn: {txid}")
            
            return {
                'success': True,
                'app_id': app_id,
                'txn_id': txid,
                'address': app_address,
                'explorer_url': f'https://testnet.algoexplorer.io/application/{app_id}'
            }
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_app_address(self, app_id: int) -> str:
        """Calculate application address from app ID."""
        from algosdk.logic import get_application_address
        return get_application_address(app_id)
    
    def generate_test_account(self) -> Dict[str, str]:
        """Generate a new Algorand test account."""
        private_key, address = account.generate_account()
        mnem = mnemonic.from_private_key(private_key)
        
        return {
            'address': address,
            'private_key': private_key,
            'mnemonic': mnem,
            'faucet_url': f'https://testnet.algoexplorer.io/dispenser?account={address}'
        }
    
    def get_account_balance(self, address: str) -> Optional[int]:
        """Get account balance in microAlgos."""
        try:
            account_info = self.algod_client.account_info(address)
            return account_info.get('amount', 0)
        except Exception as e:
            logging.error(f"Balance check failed: {e}")
            return None


def create_simple_clear_program() -> str:
    """Generate minimal clear state program."""
    try:
        from pyteal import Approve, compileTeal, Mode
        return compileTeal(Approve(), Mode.Application, version=8)
    except Exception as e:
        raise ImportError(f'Failed to import PyTeal: {str(e)}. Please ensure pyteal is installed and compatible with Python 3.13.')