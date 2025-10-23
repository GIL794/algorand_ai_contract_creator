"""
AI-Generated Smart Contract
Generated: 2025-10-19T10:43:34.955294
Description: Design a vault that releases funds to a beneficiary only after a specified timestamp.
"""

from pyteal import *

# Define constants
RELEASE_TIMESTAMP = Int(123456789)  # Example release timestamp (round number)
BENEFICIARY_ADDRESS = Addr("REPLACE_WITH_BENEFICIARY_ADDRESS")  # Replace with beneficiary address
MAX_FEE = Int(1000)  # Maximum acceptable transaction fee

# Approval Program
def approval_program():
    # Check if the transaction is an opt-in
    is_opt_in = Txn.application_args.length() == Int(0)
    
    # Check if the transaction is a close-out
    is_close_out = Txn.on_completion() == OnComplete.DeleteApplication
    
    # Check if the transaction is a payment to the beneficiary after the release timestamp
    is_payment_after_release = And(
        Txn.type_enum() == TxnType.Payment,
        Txn.receiver() == BENEFICIARY_ADDRESS,
        Global.round() >= RELEASE_TIMESTAMP,
        Txn.close_remainder_to() == Global.zero_address(),
        Txn.rekey_to() == Global.zero_address(),
        Txn.fee() <= MAX_FEE
    )
    
    # Allow opt-in and payment after release timestamp
    return Cond(
        [is_opt_in, Approve()],
        [is_close_out, Reject()],
        [is_payment_after_release, Approve()],
        [True, Reject()]
    )

# Clear Program
def clear_program():
    # Always approve clearing state
    return Approve()

# Compile programs
if __name__ == "__main__":
    with open("./approval.teal", "w") as f:
        compiled = compileTeal(approval_program(), Mode.Application, version=6)
        f.write(compiled)

    with open("./clear.teal", "w") as f:
        compiled = compileTeal(clear_program(), Mode.Application, version=6)
        f.write(compiled)