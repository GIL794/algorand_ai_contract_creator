# Report 1: How This Repository Works

## Scope
This report summarizes how the project works on branch purple-bulldog, including architecture, runtime flow, key modules, operational behavior, and current quality posture.

## High-Level Purpose
This repository is an AI-assisted Algorand smart-contract generation tool:
- Accepts natural-language input.
- Generates PyTeal contract code through LLM providers (Perplexity or OpenAI).
- Performs validation and optional retries.
- Compiles PyTeal to TEAL.
- Supports TestNet deployment through a Streamlit interface.

## Runtime Flow
1. Entrypoint and startup
- main.py sets Python import paths for src layout.
- It launches the Streamlit app as a subprocess.
- It detects occupied port 8501, and on Windows attempts process termination on that port before fallback.

2. UI orchestration (Streamlit)
- Main UI lives in src/algorand_ai_contractor/ui/streamlit_app.py.
- Tabs: Generate, Explain, Deploy, History.
- Session state tracks current contract and generation history.
- Generated contracts are auto-saved into outputs/contracts.

3. Contract generation engine
- Core generation logic is in src/algorand_ai_contractor/core/ai_engine.py.
- ContractGenerator selects provider and model from env/config.
- Strong system prompt requests secure, complete PyTeal output.
- Generation loop supports retries with previous-error feedback.
- Output parsing attempts to separate code, explanation, deployment guidance, and security notes.

4. Validation and safety checks
- Pre-validation checks for:
  - Required approval_program presence.
  - Basic PyTeal import expectations.
  - Python syntax validity.
  - Basic dangerous patterns such as eval and __import__.
- Validation acts as early filtering before compile/deploy.

5. Compile and deploy path
- Blockchain utilities are in src/algorand_ai_contractor/core/algorand_utils.py.
- compile_pyteal_to_teal:
  - Cleans markdown artifacts from generated code.
  - Executes code in a controlled namespace to obtain PyTeal expressions.
  - Compiles to TEAL and then compiles TEAL through algod.
- deploy_contract:
  - Compiles approval and clear programs.
  - Builds/signs ApplicationCreate transaction.
  - Submits and waits for confirmation.
  - Returns app_id, txid, and explorer link.

6. Explain mode
- explain_contract in ai_engine.py sends existing code to LLM for human-readable explanation.

## Configuration and Packaging
- Packaging: pyproject.toml, src layout.
- Dependencies include streamlit, openai, pyteal, py-algorand-sdk, dotenv.
- Env template (.env.example) defaults to Perplexity provider and testnet algod endpoint.
- Additional runtime/project settings in .algokit.toml and contracts/config.py.

## Scripts and Operations
- scripts/install.sh and scripts/install.bat set up venv and install dependencies.
- scripts/run.sh and scripts/run.bat launch main.py.
- Logging files configured in code include ai_generations.log and deployment.log.

## Testing and Current Quality Posture
- Tests are in tests/test_contracts.py.
- Test characteristics:
  - Include live AI generation calls by default.
  - Depend on API keys and external services.
- Observed behavior during review:
  - Without editable install: import path test collection failure.
  - After editable install: tests execute, but 3 fail without PERPLEXITY_API_KEY.

## Notable Risks / Gaps
1. Reproducibility gap
- Test suite is environment-dependent and not isolated from external APIs.

2. Production-claim mismatch risk
- README describes production-grade and compliance posture, but engineering controls are still closer to prototype maturity.

3. Artifact integrity issue
- A checked-in generated contract artifact at src/outputs/contracts/contract_20251116_201422.py is truncated/incomplete.

4. Security-check depth
- Validation includes useful baseline checks, but does not replace rigorous static analysis, formal verification, or independent smart-contract audit.

## Bottom Line
The repository implements a functional AI-assisted contract generation and TestNet deployment workflow with a clear architecture and usable UI. It is useful as a developer tool, but current test reliability, artifact hygiene, and production-hardening depth indicate pre-production maturity rather than fully production-grade readiness.
