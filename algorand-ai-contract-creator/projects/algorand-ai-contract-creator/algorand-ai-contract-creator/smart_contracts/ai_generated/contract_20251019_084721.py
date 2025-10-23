"""
AI-Generated Smart Contract
Generated: 2025-10-19T08:47:21.255746
Description: Design a vault that releases funds to a beneficiary only after a specified timestamp.
"""

from pyteal import *

# Define the global variables
TIMESTAMP_KEY = Bytes("timestamp")
BENEFICIARY_KEY = Bytes("beneficiary")

# Approval Program
def approval_program():
    # Get the current application arguments
    on_init = Seq(
        [
            # Set the timestamp and beneficiary in global state
            App.globalPut(TIMESTAMP_KEY, Btoi(Txn.application_args[1])),
            App.globalPut(BENEFICIARY_KEY, Txn.application_args[2]),
            Approve(),
        ]
    )

    # Handle OptIn transaction
    on_optin = Seq(
        [
            # No specific logic for OptIn, just approve
            Approve(),
        ]
    )

    # Handle NoOp transaction
    on_noop = Seq(
        [
            # Check if the transaction is a payment to the beneficiary after the specified timestamp
            If(
                And(
                    Txn.application_args.length() > 0,
                    Txn.application_args[0] == Bytes("withdraw"),
                    Global.round() >= App.globalGet(TIMESTAMP_KEY),
                    Txn.sender() == App.globalGet(BENEFICIARY_KEY),
                    Txn.type_enum() == TxnType.Payment,
                    Txn.fee() <= Int(1000),  # Fee check
                    Global.group_size() == Int(1),  # Ensure transaction is not part of a group
                    Txn.rekey_to() == Global.zero_address(),  # Prevent rekeying
                ),
                Seq(
                    [
                        # Payment logic: Send funds to the beneficiary
                        InnerTxnBuilder.Begin(),
                        InnerTxnBuilder.SetFields(
                            {
                                TxnField.type_enum: TxnType.Payment,
                                TxnField.sender: Txn.sender(),
                                TxnField.receiver: App.globalGet(BENEFICIARY_KEY),
                                TxnField.amount: Int(1000000),  # Example amount
                                TxnField.fee: Int(1000),
                            }
                        ),
                        InnerTxnBuilder.Submit(),
                        Approve(),
                    ]
                ),
                Reject(),  # Reject if conditions are not met
            ),
        ]
    )

    # Handle DeleteApplication transaction
    on_delete = Seq(
        [
            # Only allow deletion if the sender is the beneficiary
            If(
                Txn.sender() == App.globalGet(BENEFICIARY_KEY),
                Approve(),
                Reject(),
            ),
        ]
    )

    # Handle ClearState transaction
    on_clear_state = Seq(
        [
            # Always approve ClearState
            Approve(),
        ]
    )

    # Main approval program logic
    program = Cond(
        [Txn.application_id() == Int(0), on_init],
        [Txn.on_completion() == OnComplete.OptIn, on_optin],
        [Txn.application_args.length() > 0, on_noop],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete],
        [Txn.on_completion() == OnComplete.ClearState, on_clear_state],
    )

    return program

# Clear Program
def clear_program():
    return Approve()

# Compile the programs
if __name__ == "__main__":
    with open("./approval.teal", "w") as f:
        compiled = compileTeal(
            approval_program(), Mode.Application, version=6
        )
        f.write(compiled)

    with open("./clear.teal", "w") as f:
        compiled = compileTeal(
            clear_program(), Mode.Application, version=6
        )
        f.write(compiled)