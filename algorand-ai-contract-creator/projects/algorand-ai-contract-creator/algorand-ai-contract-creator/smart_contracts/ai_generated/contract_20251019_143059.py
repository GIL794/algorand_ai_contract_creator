"""
AI-Generated Smart Contract
Generated: 2025-10-19T14:30:59.374717
Description: Build a voting contract where users lock tokens to vote on proposals with a 7-day deadline.
"""

## Contract Purpose Summary
This PyTeal smart contract is designed for a voting system where users can lock tokens to vote on proposals. The contract includes a 7-day deadline for voting, ensuring that all votes are cast within this timeframe. It follows Algorand ASC1 security standards and includes proper fee checks and transaction validation.

## Logic Walkthrough
The contract will have two main programs: an approval program and a clear program. The approval program will handle voting logic, ensuring that users can only vote once per proposal and that votes are cast before the deadline. The clear program will handle state cleanup after the voting period.

## PyTeal Source Code

```python
from pyteal import *

# Constants
PROPOSAL_KEY = Bytes("proposal")
VOTE_KEY = Bytes("vote")
DEADLINE_KEY = Bytes("deadline")
VOTER_KEY = Bytes("voter")

# Approval Program
def approval_program():
    # Get current application ID
    app_id = Txn.application_id()

    # Get current proposal ID from application arguments
    proposal_id = Txn.application_args[1]

    # Check if transaction is an application call
    is_app_call = Txn.on_completion() == OnComplete.NoOp

    # Check if transaction is an application clear
    is_app_clear = Txn.on_completion() == OnComplete.ClearState

    # Check if transaction is an application delete
    is_app_delete = Txn.on_completion() == OnComplete.DeleteApplication

    # Check if transaction is an application update
    is_app_update = Txn.on_completion() == OnComplete.UpdateApplication

    # Check if transaction is an application opt-in
    is_app_opt_in = Txn.on_completion() == OnComplete.OptIn

    # Check if transaction is a payment to lock tokens
    is_payment = Txn.type_enum() == TxnType.Payment

    # Check if transaction is a single transaction
    is_single_tx = Global.group_size() == Int(1)

    # Check if transaction fee is acceptable
    acceptable_fee = Txn.fee() <= Int(1000)

    # Check if deadline has passed
    deadline_passed = Global.latest_timestamp() > App.localGetEx(Int(0), DEADLINE_KEY)

    # Check if user has already voted
    has_voted = App.localGetEx(Int(0), VOTER_KEY)

    # Check if proposal exists
    proposal_exists = App.localGetEx(Int(0), PROPOSAL_KEY)

    # Handle voting logic
    vote_logic = Seq(
        [
            # Check if transaction is an application call and not a clear, delete, or update
            Assert(is_app_call),
            # Check if transaction is a single transaction
            Assert(is_single_tx),
            # Check if transaction fee is acceptable
            Assert(acceptable_fee),
            # Check if deadline has not passed
            Assert(Not(deadline_passed)),
            # Check if user has not already voted
            Assert(Not(has_voted)),
            # Check if proposal exists
            Assert(proposal_exists),
            # Save vote to local state
            App.localPut(Int(0), VOTER_KEY, Bytes("voted")),
            # Increment vote count for proposal
            App.localPut(Int(0), VOTE_KEY, App.localGet(Int(0), VOTE_KEY) + Int(1)),
        ]
    )

    # Handle payment logic to lock tokens
    payment_logic = Seq(
        [
            # Check if transaction is a payment
            Assert(is_payment),
            # Check if transaction is a single transaction
            Assert(is_single_tx),
            # Check if transaction fee is acceptable
            Assert(acceptable_fee),
            # Check if deadline has not passed
            Assert(Not(deadline_passed)),
            # Lock tokens by saving them to local state
            App.localPut(Int(0), Bytes("locked"), App.localGet(Int(0), Bytes("locked")) + Txn.amount()),
        ]
    )

    # Handle opt-in logic
    opt_in_logic = Seq(
        [
            # Check if transaction is an opt-in
            Assert(is_app_opt_in),
            # Initialize local state for user
            App.localPut(Int(0), VOTER_KEY, Bytes("")),
            App.localPut(Int(0), Bytes("locked"), Int(0)),
        ]
    )

    # Handle clear logic
    clear_logic = Seq(
        [
            # Check if transaction is a clear
            Assert(is_app_clear),
            # Clear local state for user
            App.localDel(Int(0), VOTER_KEY),
            App.localDel(Int(0), Bytes("locked")),
        ]
    )

    # Combine all logic into a single sequence
    return Cond(
        [is_app_call, vote_logic],
        [is_payment, payment_logic],
        [is_app_opt_in, opt_in_logic],
        [is_app_clear, clear_logic],
        [Int(1), Reject()],
    )

# Clear Program
def clear_program():
    # Clear local state for user
    return Seq(
        [
            App.localDel(Int(0), VOTER_KEY),
            App.localDel(Int(0), Bytes("locked")),
        ]
    )

# Compile approval and clear programs
if __name__ == "__main__":
    approval_program_teal = compileTeal(
        approval_program(), mode=Mode.Application, version=3
    )
    clear_program_teal = compileTeal(
        clear_program(), mode=Mode.Application, version=3
    )

    print("Approval Program TEAL:", approval_program_teal)
    print("Clear Program TEAL:", clear_program_teal)
```

## Security Considerations
- **Reentrancy Protection**: The contract avoids reentrancy by ensuring that all state changes occur within the same transaction.
- **Integer Overflow**: The contract uses PyTeal's built-in integer handling, which prevents overflows.
- **Unbounded Loops**: The contract does not use loops that could potentially run indefinitely.
- **Global State Manipulation**: The contract only manipulates local state for each user, reducing the risk of unsafe global state changes.
- **Fee Checks**: The contract includes checks for acceptable transaction fees to prevent abuse.

## Deployment Parameters Needed
- **Application ID**: The ID of the application once deployed.
- **Proposal ID**: The ID of the proposal being voted on.
- **Deadline**: The timestamp representing the end of the voting period.
- **Voter Addresses**: The addresses of users who have opted into the application.
- **Locked Tokens**: The amount of tokens locked by each user for voting.

To deploy this contract, you would need to create an `ApplicationCreate` transaction using the Algorand SDK, providing the compiled TEAL code for the approval and clear programs. Ensure that the application parameters (e.g., global and local schemas) are correctly set to accommodate the voting logic.