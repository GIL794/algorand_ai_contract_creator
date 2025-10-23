"""
AI-Generated Smart Contract
Generated: 2025-10-19T10:51:43.001968
Description: Build a voting contract where users lock tokens to vote on proposals with a 7-day deadline.
"""

from pyteal import *

# Constants
VOTE_DURATION = Int(7 * 24 * 60 * 60)  # 7 days in seconds
PROPOSAL_KEY = Bytes("proposal")
VOTE_AMOUNT_KEY = Bytes("vote_amount")
VOTE_DEADLINE_KEY = Bytes("vote_deadline")
VOTE_COUNT_KEY = Bytes("vote_count")
VOTE_LOCKED_KEY = Bytes("vote_locked")
VOTE_OPTED_IN_KEY = Bytes("opted_in")

def approval_program():
    # On creation: Initialize global state with proposal, vote amount, and deadline
    on_creation = Seq([
        Assert(Txn.application_args.length() == Int(3)),  # proposal, vote_amount, deadline
        App.globalPut(PROPOSAL_KEY, Txn.application_args[0]),
        App.globalPut(VOTE_AMOUNT_KEY, Btoi(Txn.application_args[1])),
        App.globalPut(VOTE_DEADLINE_KEY, Btoi(Txn.application_args[2])),
        App.globalPut(VOTE_COUNT_KEY, Int(0)),
        Approve(),
    ])

    # Opt-in: Record user opted-in status and initialize locked amount to 0
    on_opt_in = Seq([
        App.localPut(Txn.sender(), VOTE_LOCKED_KEY, Int(0)),
        App.localPut(Txn.sender(), VOTE_OPTED_IN_KEY, Int(1)),
        Approve(),
    ])

    # On call: Handle voting logic
    on_call_method = Txn.application_args[0]
    on_vote = Seq([
        # Check: Must be during voting period
        Assert(Global.latest_timestamp() < App.globalGet(VOTE_DEADLINE_KEY)),
        # Check: Must have opted in
        Assert(App.localGet(Txn.sender(), VOTE_OPTED_IN_KEY)),
        # Check: Must not have voted before
        Assert(App.localGet(Txn.sender(), VOTE_LOCKED_KEY) == Int(0)),
        # Check: Must send exact vote amount
        Assert(
            And(
                Gtxn[0].type_enum() == TxnType.Payment,
                Gtxn[0].receiver() == Global.current_application_address(),
                Gtxn[0].amount() == App.globalGet(VOTE_AMOUNT_KEY),
                Gtxn[0].sender() == Txn.sender(),
            )
        ),
        # Check: No rekey, no close remainder
        Assert(
            And(
                Gtxn[0].rekey_to() == Global.zero_address(),
                Gtxn[0].close_remainder_to() == Global.zero_address(),
            )
        ),
        # Check: Fee is reasonable
        Assert(Gtxn[0].fee() <= Int(10000)),
        # Record vote
        App.localPut(Txn.sender(), VOTE_LOCKED_KEY, App.globalGet(VOTE_AMOUNT_KEY)),
        App.globalPut(VOTE_COUNT_KEY, App.globalGet(VOTE_COUNT_KEY) + Int(1)),
        Approve(),
    ])

    # On close-out: Refund locked tokens if before deadline, else forfeit
    on_close_out = Seq([
        If(
            Global.latest_timestamp() < App.globalGet(VOTE_DEADLINE_KEY),
            Seq([
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields({
                    TxnField.type_enum: TxnType.Payment,
                    TxnField.receiver: Txn.sender(),
                    TxnField.amount: App.localGet(Txn.sender(), VOTE_LOCKED_KEY),
                    TxnField.fee: Int(0),  # fee paid by outer txn
                }),
                InnerTxnBuilder.Submit(),
            ]),
        ),
        Approve(),
    ])

    # On delete: Only creator can delete, and only after deadline
    on_delete = Seq([
        Assert(Txn.sender() == Global.creator_address()),
        Assert(Global.latest_timestamp() >= App.globalGet(VOTE_DEADLINE_KEY)),
        Approve(),
    ])

    # Main router
    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.OptIn, on_opt_in],
        [Txn.on_completion() == OnComplete.CloseOut, on_close_out],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete],
        [Txn.on_completion() == OnComplete.NoOp, on_call_method],
    )

    return program

def clear_state_program():
    # On clear state: Forfeit locked tokens (no refund after deadline)
    return Approve()

if __name__ == "__main__":
    with open("vote_approval.teal", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=6)
        f.write(compiled)
    with open("vote_clear_state.teal", "w") as f:
        compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=6)
        f.write(compiled)