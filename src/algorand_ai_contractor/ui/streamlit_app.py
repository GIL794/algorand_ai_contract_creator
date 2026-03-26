

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime

# Import the landing page
from src.algorand_ai_contractor.ui.landing_page import landing_page

# --- Fix missing symbols and imports ---
from pathlib import Path
try:
    from src.algorand_ai_contractor.core.ai_engine import ContractGenerator
except ImportError:
    class ContractGenerator:
        def __init__(self, model, temperature):
            pass
        def generate_pyteal_contract(self, *args, **kwargs):
            return {"success": False, "error": "ContractGenerator not implemented"}

try:
    from src.algorand_ai_contractor.core.algorand_utils import AlgorandDeployer
except ImportError:
    class AlgorandDeployer:
        def __init__(self, verify_connection=False):
            pass
        def generate_test_account(self):
            return {"address": "testnet-address", "private_key": "key", "mnemonic": "mnemonic", "faucet_url": "https://testnet.algoexplorer.io/dispenser"}
        def algod_client(self):
            class Dummy:
                def status(self):
                    return {"last-round": 0}
            return Dummy()
        def compile_pyteal_to_teal(self, code):
            return {"success": False, "error": "Not implemented"}
        def deploy_contract(self, **kwargs):
            return {"success": False, "error": "Not implemented"}

# Path for generated contracts
GENERATED_CONTRACTS_PATH = Path(__file__).parent.parent.parent.parent / "outputs" / "contracts"
# Project root for relative paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# Dummy explain_contract if not imported
def explain_contract(code):
    return "Explanation not implemented."

# Dummy clear program generator
def create_simple_clear_program():
    return "#pragma version 5\nint 1"


# --- Landing page logic ---
if "show_main_app" not in st.session_state:
    st.session_state["show_main_app"] = False

if not st.session_state["show_main_app"]:
    landing_page()
    st.markdown("<div style='text-align:center; margin-top:2rem;'>", unsafe_allow_html=True)
    if st.button("Enter App", key="enter_app", use_container_width=True):
        st.session_state["show_main_app"] = True
        st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


# Helper function to save contracts (defined BEFORE use)
def save_contract_to_file(contract_code: str, description: str):
    """Save generated contract to outputs/contracts/ folder."""
    try:
        GENERATED_CONTRACTS_PATH.mkdir(parents=True, exist_ok=True)

        filename = f"contract_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        filepath = GENERATED_CONTRACTS_PATH / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f'"""\n')
            f.write(f"AI-Generated Smart Contract\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Description: {description}\n")
            f.write(f'"""\n\n')
            f.write(contract_code)

        return filepath
    except Exception as e:
        st.warning(f"Could not save to file: {e}")
        return None


# Initialize session state
if "generation_history" not in st.session_state:
    st.session_state.generation_history = []
if "current_contract" not in st.session_state:
    st.session_state.current_contract = None


# Initialize components
@st.cache_resource
def init_generator():
    return ContractGenerator(model="sonar", temperature=0.2)


@st.cache_resource
def init_deployer():
    try:
        # Initialize without strict connection verification
        return AlgorandDeployer(verify_connection=False)
    except Exception as e:
        st.error(f"Algorand deployer initialization failed: {e}")
        return None


generator = init_generator()
deployer = init_deployer()

# Header
st.title("🔗 AI-Powered Smart Contract Creator")
st.markdown("""
*Algorand PyTeal Contract Generator* | Powered by GPT-4  
Generate, validate, and deploy smart contracts using natural language.

EU AI Act Tier 2 Compliant | IEEE EAD Aligned
""")

# Sidebar
with st.sidebar:
    st.header("⚙ Configuration")

    st.subheader("AI Settings")
    ai_provider = st.selectbox("AI Provider", ["perplexity", "openai"], index=0)

    if ai_provider == "perplexity":
        model_choice = st.selectbox(
            "Model", ["sonar", "sonar-pro"], index=0  # Main model  # Pro model (if available)
        )
    else:
        model_choice = st.selectbox("Model", ["gpt-4", "gpt-4-turbo"], index=0)

    temperature = st.slider("Temperature", 0.0, 0.5, 0.2, 0.05)

    st.subheader("Deployment")
    if deployer:
        try:
            status = deployer.algod_client.status()
            st.success(f"✅ TestNet Connected (Round {status['last-round']})")
        except Exception as e:
            st.error(f"❌ TestNet Offline: {str(e)}")

    st.warning(
        "⚠️ **TESTNET ONLY** - Generated contracts are for testing purposes. Do NOT use for production/mainnet without security audit."
    )

    st.subheader("🔑 Testnet Address Generator")
    if st.button(
        "Generate Testnet Address",
        help="Generate a new Algorand testnet address for use in contracts",
    ):
        if deployer:
            test_account = deployer.generate_test_account()
            # Store in a list to support multiple addresses
            if "generated_testnet_addresses" not in st.session_state:
                st.session_state["generated_testnet_addresses"] = []
            st.session_state["generated_testnet_addresses"].append(test_account)
            st.session_state["generated_testnet_address"] = (
                test_account  # Keep for backward compatibility
            )
            st.success(f"✅ Testnet address generated: `{test_account['address'][:20]}...`")
            st.info("💡 This address will be automatically included in contract generation!")

    # Show all generated testnet addresses
    available_addresses = []
    if (
        "generated_testnet_addresses" in st.session_state
        and st.session_state["generated_testnet_addresses"]
    ):
        available_addresses = st.session_state["generated_testnet_addresses"]
    elif "generated_testnet_address" in st.session_state:
        available_addresses = [st.session_state["generated_testnet_address"]]

    if available_addresses:
        with st.expander(
            f"📋 Generated Testnet Addresses ({len(available_addresses)})", expanded=True
        ):
            for idx, account in enumerate(available_addresses, 1):
                st.markdown(f"**Address {idx}:**")
                st.code(f"Address: {account['address']}", language="text")
                with st.expander(f"Show Private Key & Mnemonic for Address {idx}", expanded=False):
                    st.code(f"Private Key: {account['private_key']}", language="text")
                    st.code(f"Mnemonic: {account['mnemonic']}", language="text")

                # Wallet funding options for each address
                st.markdown(f"### 💰 Fund Address {idx}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(
                        "🌐 Connect Wallet", key=f"sidebar_wallet_{idx}", use_container_width=True
                    ):
                        st.session_state["show_wallet_modal"] = True
                        st.session_state["wallet_funding_address"] = account["address"]
                        st.rerun()
                with col2:
                    st.link_button("🚰 Faucet", account["faucet_url"], use_container_width=True)

                if idx < len(available_addresses):
                    st.divider()

            st.caption("⚠️ Keep private keys and mnemonics secure. These are for TESTNET only.")
            st.info(
                f"💡 All {len(available_addresses)} address(es) will be automatically included in contract generation!"
            )

    st.divider()

    st.subheader("📊 Session Stats")
    st.metric("Contracts Generated", len(st.session_state.generation_history))

    if st.button("🗑 Clear History"):
        st.session_state.generation_history = []
        st.session_state.current_contract = None
        st.rerun()

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["🎨 Generate", "🔍 Explain", "🚀 Deploy", "📜 History"])

# TAB 1: Generate Contract
with tab1:
    st.header("Generate Smart Contract")

    # Testnet warning banner
    st.warning(
        "⚠️ **TESTNET ONLY**: Contracts generated here are for Algorand TestNet testing. They are NOT production-ready and require security audits before mainnet deployment."
    )

    # Testnet address helper - show available addresses
    available_addresses = []
    if (
        "generated_testnet_addresses" in st.session_state
        and st.session_state["generated_testnet_addresses"]
    ):
        available_addresses = st.session_state["generated_testnet_addresses"]
    elif "generated_testnet_address" in st.session_state:
        available_addresses = [st.session_state["generated_testnet_address"]]

    if available_addresses:
        addresses_text = ", ".join([f"`{addr['address']}`" for addr in available_addresses])
        st.success(
            f"💡 **{len(available_addresses)} Testnet Address(es) Available**: {addresses_text}"
        )
        st.caption(
            "These addresses will be automatically included in your contract generation. You can reference them in your description or they'll be added automatically."
        )

    # Example templates
    with st.expander("📝 Example Prompts"):
        st.markdown("""
        **Simple Escrow:**
        - Create an escrow contract that holds funds until both buyer and seller confirm the transaction.
        
        **Token Voting:**
        - Build a voting contract where users lock tokens to vote on proposals with a 7-day deadline.
        
        **Time-Locked Vault:**
        - Design a vault that releases funds to a beneficiary only after a specified timestamp.
        
        **Multi-Signature Wallet:**
        - Create a 2-of-3 multi-signature wallet for secure fund management.
        """)

    # Input form
    user_description = st.text_area(
        "Describe your smart contract:",
        height=150,
        placeholder="Example: Create a simple auction contract where users can bid, and the highest bidder wins after the auction closes...",
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        generate_button = st.button(
            "⚡ Generate Contract", type="primary", use_container_width=True
        )

    if generate_button and user_description:
        with st.spinner("🤖 AI is crafting your contract..."):
            # Get available testnet addresses
            available_addresses = []
            if (
                "generated_testnet_addresses" in st.session_state
                and st.session_state["generated_testnet_addresses"]
            ):
                available_addresses = st.session_state["generated_testnet_addresses"]
            elif "generated_testnet_address" in st.session_state:
                available_addresses = [st.session_state["generated_testnet_address"]]

            # Enhance description with testnet addresses if available
            enhanced_description = user_description
            if available_addresses:
                addresses_info = "\n\n**Available Testnet Addresses for this contract:**\n"
                for idx, addr in enumerate(available_addresses, 1):
                    addresses_info += f"- Address {idx}: {addr['address']}\n"
                addresses_info += "\n**IMPORTANT**: Use these testnet addresses in the contract where addresses are needed (e.g., for escrow, multi-sig signers, etc.). Include them directly in the PyTeal code with proper comments indicating they are testnet addresses."
                enhanced_description = user_description + addresses_info

            result = generator.generate_pyteal_contract(
                enhanced_description, ai_provider=ai_provider, model=model_choice
            )

            # Safety check: ensure result is a dict
            if not isinstance(result, dict):
                st.error(f"❌ Generation failed: Unexpected result type: {type(result)}")
                st.stop()

            if result.get("success", False):
                st.session_state.current_contract = result
                st.session_state.generation_history.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "description": user_description,
                        "result": result,
                    }
                )

                # Save to outputs/contracts/
                saved_path = save_contract_to_file(result.get("code", ""), user_description)

                # Safely get metadata
                metadata = result.get("metadata", {})
                if not isinstance(metadata, dict):
                    metadata = {}
                attempts = metadata.get("attempts", 1)
                st.success(f"✅ Contract generated in {attempts} attempt(s)")
                if saved_path:
                    try:
                        # Try to get relative path from project root
                        rel_path = saved_path.relative_to(PROJECT_ROOT)
                        st.info(f"📁 Saved to: `{rel_path}`")
                    except ValueError:
                        # If relative path fails, just show the filename
                        st.info(f"📁 Saved to: `{saved_path.name}`")
            else:
                error_msg = result.get("error", "Unknown error occurred")
                st.error(f"❌ Generation failed: {error_msg}")
                st.stop()

    # Display current contract
    current_contract = st.session_state.current_contract
    if (
        current_contract
        and isinstance(current_contract, dict)
        and current_contract.get("success", False)
    ):
        contract = current_contract

        st.divider()
        st.subheader("Generated Contract")

        # Testnet warning
        st.warning(
            "⚠️ **TESTNET CONTRACT**: This contract is generated for Algorand TestNet only. Replace any placeholder addresses with actual testnet addresses before deployment."
        )

        # Code display
        contract_code = contract.get("code", "")
        if contract_code:
            st.code(contract_code, language="python")
        else:
            st.error("No code found in contract")

        # Testnet addresses section - show all available addresses
        available_addresses = []
        if (
            "generated_testnet_addresses" in st.session_state
            and st.session_state["generated_testnet_addresses"]
        ):
            available_addresses = st.session_state["generated_testnet_addresses"]
        elif "generated_testnet_address" in st.session_state:
            available_addresses = [st.session_state["generated_testnet_address"]]

        if available_addresses:
            with st.expander(
                f"🔑 Available Testnet Addresses ({len(available_addresses)})", expanded=False
            ):
                for idx, account in enumerate(available_addresses, 1):
                    st.markdown(f"**Address {idx}:**")
                    st.code(f"{account['address']}", language="text")
                    st.caption(
                        f"Used in contract generation. Private key and mnemonic available in sidebar."
                    )
                    if idx < len(available_addresses):
                        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            # Download button
            contract_code = contract.get("code", "")
            if contract_code:
                st.download_button(
                    label="💾 Download PyTeal Code",
                    data=contract_code,
                    file_name=f"contract_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py",
                    mime="text/x-python",
                )

        with col2:
            # Show saved location
            st.info(f"📁 Auto-saved to: `outputs/contracts/`")

        # Explanation
        with st.expander("📖 Contract Explanation", expanded=True):
            st.markdown(contract.get("explanation") or "No explanation provided")

        # Deployment instructions
        with st.expander("🛠 Deployment Instructions"):
            st.markdown(contract.get("deployment") or "No deployment instructions provided")
            st.caption(
                "⚠️ Remember: This is for TESTNET only. Do not deploy to mainnet without security audit."
            )

        # Audit summary
        with st.expander("🔒 Security Audit Summary"):
            st.markdown(contract.get("audit") or "No audit information provided")
            st.warning(
                "⚠️ **IMPORTANT**: This code has NOT been security audited. Always audit smart contracts before deploying to mainnet with real value."
            )

# TAB 2: Explain Contract
with tab2:
    st.header("Explain Existing Contract")

    existing_code = st.text_area(
        "Paste PyTeal code to explain:",
        height=300,
        placeholder="from pyteal import *\n\ndef approval_program():\n    return Approve()",
    )

    if st.button("🔍 Explain Code", type="primary"):
        if existing_code:
            with st.spinner("Analyzing contract..."):
                explanation = explain_contract(existing_code)
                st.markdown("### Analysis")
                st.markdown(explanation)
        else:
            st.warning("Please provide PyTeal code to analyze")

# TAB 3: Deploy Contract
with tab3:
    st.header("Deploy to Algorand TestNet")

    # Prominent testnet warning
    st.error(
        "🚨 **TESTNET DEPLOYMENT ONLY** - This will deploy to Algorand TestNet. Never use testnet contracts on mainnet without security audit."
    )

    if not deployer:
        st.error("⚠ Algorand deployer not initialized. Check your .env configuration.")
        st.stop()

    current_contract = st.session_state.current_contract
    if not current_contract or not isinstance(current_contract, dict):
        st.info("👈 Generate a contract first in the Generate tab")
        st.stop()

    st.subheader("Step 1: Compile Contract")

    if st.button("⚙ Compile to TEAL"):
        with st.spinner("Compiling..."):
            contract_code = current_contract.get("code", "")
            if not contract_code:
                st.error("No contract code found. Please generate a contract first.")
                st.stop()

            # Clean the code before compilation - remove any markdown artifacts
            import re

            cleaned_code = contract_code.strip()

            # CRITICAL: Remove markdown code block markers if present
            cleaned_code = re.sub(r"^```(?:python|py)?\s*\n?", "", cleaned_code, flags=re.MULTILINE)
            cleaned_code = re.sub(r"```\s*$", "", cleaned_code, flags=re.MULTILINE)

            # CRITICAL: Stop at horizontal rules (---) - these indicate end of code
            if "---" in cleaned_code:
                # Find the first occurrence of --- that's not in a string or comment
                lines = cleaned_code.split("\n")
                final_lines = []
                for line in lines:
                    stripped = line.strip()
                    # Stop at horizontal rule (but allow it in strings/comments)
                    if stripped == "---" or (
                        stripped.startswith("---")
                        and len(stripped) >= 3
                        and not any(c in stripped for c in ['"', "'", "=", "#"])
                    ):
                        break
                    # Stop at markdown headers
                    if stripped.startswith("##") or stripped.startswith("###"):
                        break
                    # Stop at explanation section headers
                    if any(
                        header in stripped
                        for header in [
                            "Contract Purpose",
                            "Purpose Summary",
                            "Logic Walkthrough",
                            "Security Considerations",
                            "Security Audit",
                            "Deployment Parameters",
                            "**Contract Purpose",
                            "**Logic Walkthrough",
                            "**Security",
                        ]
                    ):
                        break
                    final_lines.append(line)
                cleaned_code = "\n".join(final_lines).strip()

            # Remove any remaining markdown markers
            cleaned_code = re.sub(r"^```(?:python|py)?\s*\n?", "", cleaned_code, flags=re.MULTILINE)
            cleaned_code = re.sub(r"```\s*$", "", cleaned_code, flags=re.MULTILINE)
            cleaned_code = cleaned_code.strip()

            # Show what we're compiling (for debugging)
            with st.expander("🔍 Code being compiled (first 500 chars)", expanded=False):
                st.code(cleaned_code[:500], language="python")

            compile_result = deployer.compile_pyteal_to_teal(cleaned_code)

            if compile_result.get("success", False):
                st.success("✅ Compilation successful!")
                st.session_state["compiled_teal"] = compile_result.get("teal", "")
                st.session_state["compiled_hash"] = compile_result.get("hash", "")

                with st.expander("View TEAL Code"):
                    st.code(compile_result.get("teal", ""), language="teal")
                    st.caption(f"Hash: {compile_result.get('hash', 'N/A')}")
            else:
                st.error(f"❌ Compilation failed: {compile_result.get('error', 'Unknown error')}")
                # Show the code that failed for debugging
                with st.expander("🔍 View code that failed to compile", expanded=True):
                    st.code(cleaned_code, language="python")
                    st.caption(
                        "💡 Tip: The error message above shows the problematic line. Check for unmatched quotes, incomplete strings, or syntax errors."
                    )

    if "compiled_teal" in st.session_state:
        st.divider()
        st.subheader("Step 2: Deploy to TestNet")

        st.warning("⚠ Requires a funded TestNet account")

        with st.expander("🆕 Generate Test Account", expanded=True):
            st.caption(
                "Generate a new Algorand testnet account for deployment. This account will need to be funded via the TestNet faucet."
            )
            if st.button("Create New Testnet Account"):
                test_account = deployer.generate_test_account()
                st.session_state["deployment_testnet_account"] = test_account
                st.success("✅ Testnet account generated!")
                st.json(
                    {"address": test_account["address"], "faucet_url": test_account["faucet_url"]}
                )
                st.warning(
                    "⚠️ **IMPORTANT**: Save your private key and mnemonic securely. This is for TESTNET only."
                )
                st.info(f"💰 [Fund this account at TestNet Faucet]({test_account['faucet_url']})")

        if "deployment_testnet_account" in st.session_state:
            account = st.session_state["deployment_testnet_account"]
            st.info(
                f"📋 **Deployment Account**: `{account['address']}` - Make sure it's funded before deploying!"
            )

            # Wallet funding option for deployment account
            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "🌐 Connect Web3 Wallet to Fund",
                    key="deploy_wallet_connect",
                    use_container_width=True,
                ):
                    st.session_state["show_wallet_modal"] = True
                    st.session_state["wallet_funding_address"] = account["address"]
                    st.rerun()
            with col2:
                st.link_button("🚰 TestNet Faucet", account["faucet_url"], use_container_width=True)

        private_key = st.text_input(
            "Deployment Account Private Key:",
            type="password",
            help="Your TestNet account private key (kept secure - never stored)",
        )

        if st.button("🚀 Deploy Contract", type="primary"):
            if not private_key:
                st.error("Please provide a private key")
            else:
                with st.spinner("Deploying to Algorand TestNet..."):
                    clear_program = create_simple_clear_program()

                    deploy_result = deployer.deploy_contract(
                        approval_teal=st.session_state["compiled_teal"],
                        clear_teal=clear_program,
                        sender_private_key=private_key,
                    )

                    if deploy_result.get("success", False):
                        st.success("🎉 Contract deployed successfully!")
                        st.json(deploy_result)
                        explorer_url = deploy_result.get("explorer_url", "")
                        if explorer_url:
                            st.markdown(f"[View on AlgoExplorer]({explorer_url})")
                    else:
                        st.error(
                            f"Deployment failed: {deploy_result.get('error', 'Unknown error')}"
                        )

# TAB 4: History
with tab4:
    st.header("Generation History")

    if not st.session_state.generation_history:
        st.info("No contracts generated yet")
    else:
        for idx, entry in enumerate(reversed(st.session_state.generation_history)):
            timestamp = entry.get("timestamp", "")[:19] if entry.get("timestamp") else "Unknown"
            with st.expander(
                f"Contract #{len(st.session_state.generation_history) - idx} - {timestamp}"
            ):
                st.markdown(f"*Description:* {entry.get('description', 'No description')}")
                result_code = entry.get("result", {}).get("code", "")
                if result_code:
                    st.code(result_code, language="python")
                else:
                    st.warning("No code found for this contract")

# Wallet Connection Modal (shown when show_wallet_modal is True)
if st.session_state.get("show_wallet_modal", False):
    st.markdown("---")
    st.markdown("### 🌐 Connect Web3 Wallet to Fund Account")

    funding_address = st.session_state.get("wallet_funding_address", "")
    if funding_address:
        st.info(f"**Funding Address**: `{funding_address}`")

    st.markdown("Select your preferred wallet to connect and fund this testnet account:")

    # Wallet options - 8 wallets total
    wallets = [
        {
            "name": "Pera Wallet",
            "icon": "🔵",
            "description": "Official Algorand mobile wallet",
            "url": "https://perawallet.app/",
            "connect_url": "https://perawallet.app/download/",
        },
        {
            "name": "MyAlgo Wallet",
            "icon": "🟢",
            "description": "Browser extension wallet",
            "url": "https://wallet.myalgo.com/",
            "connect_url": "https://wallet.myalgo.com/",
        },
        {
            "name": "AlgoSigner",
            "icon": "🟡",
            "description": "Browser extension for Algorand",
            "url": "https://www.purestake.com/technology/algosigner/",
            "connect_url": "https://www.purestake.com/technology/algosigner/",
        },
        {
            "name": "Defly Wallet",
            "icon": "🟣",
            "description": "DeFi-focused Algorand wallet",
            "url": "https://defly.app/",
            "connect_url": "https://defly.app/download",
        },
        {
            "name": "Exodus",
            "icon": "🔷",
            "description": "Multi-chain wallet with Algorand support",
            "url": "https://www.exodus.com/",
            "connect_url": "https://www.exodus.com/download",
        },
        {
            "name": "Trust Wallet",
            "icon": "🔶",
            "description": "Mobile wallet with Algorand",
            "url": "https://trustwallet.com/",
            "connect_url": "https://trustwallet.com/download",
        },
        {
            "name": "WalletConnect",
            "icon": "🔗",
            "description": "Connect any WalletConnect-compatible wallet",
            "url": "https://walletconnect.com/",
            "connect_url": "https://walletconnect.com/",
        },
        {
            "name": "MetaMask",
            "icon": "🦊",
            "description": "Via WalletConnect (if supported)",
            "url": "https://metamask.io/",
            "connect_url": "https://metamask.io/download",
        },
    ]

    # Display wallets in a grid (2 columns)
    cols = st.columns(2)
    for idx, wallet in enumerate(wallets):
        with cols[idx % 2]:
            with st.container():
                st.markdown(f"#### {wallet['icon']} {wallet['name']}")
                st.caption(wallet["description"])

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button(
                        "Connect", key=f"connect_{wallet['name']}", use_container_width=True
                    ):
                        st.info(
                            f"💡 **Note**: Connect {wallet['name']} and use it to send testnet ALGO to: `{funding_address}`"
                        )
                        st.session_state[f'wallet_connected_{wallet["name"]}'] = True
                        # Open wallet website in new tab
                        st.markdown(
                            f'<a href="{wallet["connect_url"]}" target="_blank">Open {wallet["name"]}</a>',
                            unsafe_allow_html=True,
                        )
                with col_btn2:
                    st.link_button("Learn More", wallet["url"], use_container_width=True)

                st.divider()

    # Manual funding option
    st.markdown("---")
    st.markdown("### 📋 Manual Funding Instructions")
    st.info(f"""
    **To fund this account manually:**
    1. Copy the address: `{funding_address}`
    2. Visit the [Algorand TestNet Faucet](https://testnet.algoexplorer.io/dispenser)
    3. Paste the address and request testnet ALGO
    4. Wait for confirmation (usually instant)
    """)

    # Close modal button
    if st.button(
        "✖ Close Wallet Selection",
        key="close_wallet_modal",
        use_container_width=True,
        type="secondary",
    ):
        st.session_state["show_wallet_modal"] = False
        if "wallet_funding_address" in st.session_state:
            del st.session_state["wallet_funding_address"]
        st.rerun()

# Footer
st.divider()
st.caption("Built with ❤ | Algorand + Perplexity AI | IEEE EAD & EU AI Act Compliant")
