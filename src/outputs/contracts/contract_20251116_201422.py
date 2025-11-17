"""
AI-Generated Smart Contract
Generated: 2025-11-16T20:14:22.713553
Description: Create a 2-of-3 multi-signature wallet for secure fund management.
"""

```python
from pyteal import *

def approval_program():
    """
    2-of-3 Multi-Signature Wallet Contract
    
    This contract implements a secure multi-signature wallet requiring 2 out of 3
    authorized signers to approve fund transfers. It maintains signer management,
    transaction proposals, and approval tracking with comprehensive security checks.
    """
    
    # ============================================================================
    # STATE VARIABLES
    # ============================================================================
    
    # Global state keys
    signer_1 = Bytes("signer_1")
    signer_2 = Bytes("signer_2")
    signer_3 = Bytes("signer_3")
    required_signatures = Bytes("required_sigs")  # Set to 2
    transaction_count = Bytes("tx_count")
    
    # Local state keys (per-user tracking)
    user_approvals = Bytes("approvals")
    
    # ============================================================================
    # HELPER FUNCTIONS
    # ============================================================================
    
    def is_valid_signer(address):
        """Check if address is one of the three authorized signers"""
        return Or(
            address == Global.get(signer_1),
            address == Global.get(signer_2),
            address == Global.get(signer_3)
        )
    
    def get_approval_count(txn_id):
        """Count total approvals for a transaction across all signers"""
        return (
            If(App.localGet(Global.get(signer_1), Concat(Bytes("tx_"), txn_id)) == Int(1))
            .Then(Int(1))
            .Else(Int(0))
        ) + (
            If(App.localGet(Global.get(signer_2), Concat(Bytes("tx_"), txn_id)) == Int(1))
            .Then(Int(1))
            .Else(Int(0))
        ) + (
            If(App.localGet(Global.get(signer_3), Concat(Bytes("tx_"), txn_id)) == Int(1))
            .Then(Int(1))
            .Else(Int(0))
        )
    
    # ============================================================================
    # INITIALIZATION
    # ============================================================================
    
    on_init = Seq([
        # Verify exactly 3 signers provided in application arguments
        Assert(Txn.application_args.length() == Int(3)),
        
        # Store the three signers
        App.globalPut(signer_1, Txn.application_args[0]),
        App.globalPut(signer_2, Txn.application_args[1]),
        App.globalPut(signer_3, Txn.application_args[2]),
        
        # Set required signatures to 2
        App.globalPut(required_signatures, Int(2)),
        
        # Initialize transaction counter
        App.globalPut(transaction_count, Int(0)),
        
        # Return success
        Int(1)
    ])
    
    # ============================================================================
    # PROPOSE TRANSACTION
    # ============================================================================
    
    on_propose = Seq([
        # Verify caller is a valid signer
        Assert(is_valid_signer(Txn.sender)),
        
        # Verify application arguments: [receiver, amount]
        Assert(Txn.application_args.length() == Int(2)),
        
        # Verify amount is positive
        Assert(Btoi(Txn.application_args[1]) > Int(0)),
        
        # Verify receiver address is valid (non-empty)
        Assert(Len(Txn.application_args[0]) == Int(32)),
        
        # Increment transaction counter
        App.globalPut(
            transaction_count,
            App.globalGet(transaction_count) + Int(1)
        ),
        
        # Initialize approval tracking for this transaction
        App.localPut(
            Txn.sender,
            Concat(Bytes("tx_"), Itob(App.globalGet(transaction_count))),
            Int(1)  # Proposer auto-approves
        ),
        
        # Store transaction details
        App.localPut(
            Txn.sender,
            Concat(Bytes("receiver_"), Itob(App.globalGet(transaction_count))),
            Txn.application_args[0]
        ),
        App.localPut(
            Txn.sender,
            Concat(Bytes("amount_"), Itob(App.globalGet(transaction_count))),
            Txn.application_args[1]
        ),
        
        # Return success
        Int(1)
    ])
    
    # ============================================================================
    # APPROVE TRANSACTION
    # ============================================================================
    
    on_approve = Seq([
        # Verify caller is a valid signer
        Assert(is_valid_signer(Txn.sender)),
        
        # Verify transaction ID provided
        Assert(Txn.application_args.length() == Int(1)),
        
        # Verify transaction ID is valid (numeric)
        Assert(Len(Txn.application_args[0]) <= Int(8)),
        
        # Verify signer hasn't already approved this transaction
        Assert(
            App.localGet(Txn.sender, Concat(Bytes("tx_"), Txn.application_args[0])) == Int(0)
        ),
        
        # Record approval
        App.localPut(
            Txn.sender,
            Concat(Bytes("tx_"), Txn.application_args[0]),
            Int(1)
        ),
        
        # Return success
        Int(1)
    ])
    
    # ============================================================================
    # EXECUTE TRANSACTION
    # ============================================================================
    
    on_execute = Seq([
        # Verify caller is a valid signer
        Assert(is_valid_signer(Txn.sender)),
        
        # Verify transaction ID provided
        Assert(Txn.application_args.length() == Int(1)),
        
        # Verify we have sufficient approvals (2 out of 3)
        Assert(get_approval_count(Txn.application_args[0]) >= App.globalGet(required_signatures)),
        
        # Verify contract has sufficient balance
        Assert(Balance(Global.current_application_address()) > Int(0)),
        
        # Verify payment transaction is present (index 1)
        Assert(Txn.group_size() == Int(2)),
        Assert(Gtxn(1).type_enum() == TxnType.Payment),
        
        # Verify payment receiver matches proposed receiver
        Assert(
            Gtxn(1).receiver() == Txn.application_args[0]
        ),
        
        # Verify payment amount matches proposed amount
        Assert(
            Gtxn(1).amount() == Btoi(Txn.application_args[1])
        ),
        
        # Verify payment is from this contract
        Assert(Gtxn(1).sender() == Global.current_application_address()),
        
        # Verify fee is reasonable (max 1000 microAlgos)
        Assert(Gtxn(1).fee() <= Int(1000)),
        
        # Mark transaction as executed
        App.localPut(
            Txn.sender,
            Concat(Bytes("executed_"), Txn.application_args[0]),
            Int(1)
        ),
        
        # Return success
        Int(1)
    ])
    
    # ============================================================================
    # GET TRANSACTION STATUS
    # ============================================================================
    
    on_status = Seq([
        # Verify transaction ID provided
        Assert(Txn.application_args.length() == Int(1)),
        
        # Return approval count for this transaction
        get_approval_count(Txn.application_args[0])
    ])
    
    # ============================================================================
    # MAIN APPROVAL LOGIC
    # ============================================================================
    
    program = Cond(
        # Handle contract creation
        [