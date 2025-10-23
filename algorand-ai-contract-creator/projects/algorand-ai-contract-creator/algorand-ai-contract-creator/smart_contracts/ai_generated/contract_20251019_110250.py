"""
AI-Generated Smart Contract
Generated: 2025-10-19T11:02:50.877625
Description: Build a voting contract where users lock tokens to vote on proposals with a 7-day deadline.
"""

from pyteal import *

# Constants
VOTE_DURATION = Int(604800)  # 7 days in seconds
MIN_LOCK_AMOUNT = Int(100000)  # Minimum microAlgos to lock per vote (adjust as needed)
MAX_VOTE_OPTIONS = Int(10)     # Maximum number of vote options per proposal (prevents state bloat)

def approval_program():
    # OnCreate: Initialize global state for a new proposal
    on_create = Seq([
        # Set proposal creator (sender of ApplicationCreateTxn)
        App.globalPut(Bytes("creator"), Txn.sender()),
        # Set proposal start time (current round timestamp)
        App.globalPut(Bytes("start_time"), Global.latest_timestamp()),
        # Set proposal end time (start + 7 days)
        App.globalPut(Bytes("end_time"), Global.latest_timestamp() + VOTE_DURATION),
        # Initialize vote counts for each option (0..MAX_VOTE_OPTIONS-1)
        *[App.globalPut(Concat(Bytes("votes_"), Itob(i)), Int(0)) for i in range(MAX_VOTE_OPTIONS.value)],
        # Initialize total locked amount
        App.globalPut(Bytes("total_locked"), Int(0)),
        Approve()
    ])

    # OnOptIn: User opts in to participate (must lock tokens)
    on_opt_in = Seq([
        # Ensure the user is not already opted in
        Assert(App.localGet(Int(0), Bytes("opted_in")) == Int(0)),
        # Ensure the user sends the minimum lock amount with the opt-in
        Assert(Gtxn[0].type_enum() == TxnType.Payment),
        Assert(Gtxn[0].receiver() == Global.current_application_address()),
        Assert(Gtxn[0].amount() >= MIN_LOCK_AMOUNT),
        # Mark user as opted in and record locked amount
        App.localPut(Int(0), Bytes("opted_in"), Int(1)),
        App.localPut(Int(0), Bytes("locked_amount"), Gtxn[0].amount()),
        # Increment global locked total
        App.globalPut(Bytes("total_locked"), App.globalGet(Bytes("total_locked")) + Gtxn[0].amount()),
        Approve()
    ])

    # OnCloseOut: User closes out; refund locked tokens if voting is over
    on_close_out = Seq([
        # Only allow close-out after voting ends
        Assert(Global.latest_timestamp() >= App.globalGet(Bytes("end_time"))),
        # Refund locked amount to user
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.Payment,
            TxnField.receiver: Txn.sender(),
            TxnField.amount: App.localGet(Int(0), Bytes("locked_amount")),
            TxnField.fee: Int(0),  # Fee paid by outer transaction
        }),
        InnerTxnBuilder.Submit(),
        # Decrement global locked total
        App.globalPut(Bytes("total_locked"), App.globalGet(Bytes("total_locked")) - App.localGet(Int(0), Bytes("locked_amount"))),
        Approve()
    ])

    # OnUpdateApplication: Only creator can update
    on_update = Seq([
        Assert(Txn.sender() == App.globalGet(Bytes("creator"))),
        Approve()
    ])

    # OnDeleteApplication: Only creator can delete, and only after voting ends
    on_delete = Seq([
        Assert(Txn.sender() == App.globalGet(Bytes("creator"))),
        Assert(Global.latest_timestamp() >= App.globalGet(Bytes("end_time"))),
        Approve()
    ])

    # Vote: User casts a vote for a specific option
    on_vote = Seq([
        # Ensure user is opted in
        Assert(App.localGet(Int(0), Bytes("opted_in")) == Int(1)),
        # Ensure voting period is active
        Assert(Global.latest_timestamp() < App.globalGet(Bytes("end_time"))),
        # Ensure user has not voted before
        Assert(App.localGet(Int(0), Bytes("voted")) == Int(0)),
        # Ensure vote option is valid
        option = Btoi(Txn.application_args[1]),
        Assert(option < MAX_VOTE_OPTIONS),
        Assert(option >= Int(0)),
        # Mark user as voted
        App.localPut(Int(0), Bytes("voted"), Int(1)),
        # Increment vote count for the chosen option
        vote_key = Concat(Bytes("votes_"), Itob(option)),
        App.globalPut(vote_key, App.globalGet(vote_key) + Int(1)),
        Approve()
    ])

    # Main router
    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.OptIn, on_opt_in],
        [Txn.on_completion() == OnComplete.CloseOut, on_close_out],
        [Txn.on_completion() == OnComplete.UpdateApplication, on_update],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete],
        [Txn.application_args[0] == Bytes("vote"), on_vote],
    )

    return program

def clear_program():
    # Allow any user to clear their local state (no refund here; must use CloseOut)
    return Approve()

# Compile to TEAL
if __name__ == "__main__":
    approval_teal = compileTeal(approval_program(), mode=Mode.Application, version=6)
    clear_teal = compileTeal(clear_program(), mode=Mode.Application, version=6)
    print("=== Approval Program ===")
    print(approval_teal)
    print("=== Clear Program ===")
    print(clear_teal)