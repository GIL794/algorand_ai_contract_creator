"""
AI-Generated Smart Contract
Generated: 2025-10-19T08:40:22.148334
Description: Build a voting contract where users lock tokens to vote on proposals with a 7-day deadline.
"""

from pyteal import *

def voting_contract(token_id: int, voting_period_seconds: int = 7 * 24 * 3600):
    """
    Stateful smart contract for token-weighted voting on proposals with a 7-day deadline.
    Users lock tokens (ASA) to vote on proposals before the deadline.
    """

    # Global State Keys
    # Store proposal count and voting start timestamp
    global_proposal_count = Bytes("PropCount")      # uint64
    global_voting_start = Bytes("StartTime")        # uint64 (Unix timestamp)
    global_voting_open = Bytes("VotingOpen")        # uint64 (0 or 1)

    # Local State Keys (per voter)
    local_vote_weight = Bytes("VoteWeight")         # uint64 tokens locked by voter
    local_voted = Bytes("Voted")                     # uint64 0 or 1 to prevent double voting

    # Proposal state keys are stored in global state as:
    # "P_<index>_name" : bytes (proposal name)
    # "P_<index>_votes": uint64 (total votes for proposal)

    # Helper to get proposal keys
    def proposal_name_key(i: int):
        return Concat(Bytes("P_"), Itob(i), Bytes("_name"))

    def proposal_votes_key(i: int):
        return Concat(Bytes("P_"), Itob(i), Bytes("_votes"))

    # On creation: initialize proposals and voting start time
    on_creation = Seq(
        Assert(Txn.application_args.length() >= Int(1)),
        # Number of proposals passed as first arg (uint64)
        # Followed by proposal names as bytes (max 5 proposals recommended due to global state limits)
        # Example: [b"3", b"Proposal1", b"Proposal2", b"Proposal3"]
        # Parse proposal count
        App.globalPut(global_proposal_count, Btoi(Txn.application_args[0])),
        App.globalPut(global_voting_start, Global.latest_timestamp()),
        App.globalPut(global_voting_open, Int(1)),

        # Initialize proposals in global state
        For(i := ScratchVar(TealType.uint64), i.store(Int(0)), i.load() < Btoi(Txn.application_args[0]), i.store(i.load() + Int(1))).Do(
            Seq(
                Assert(Txn.application_args.length() == (Int(1) + i.load() + Int(1))),
                App.globalPut(proposal_name_key(i.load()), Txn.application_args[i.load() + Int(1)]),
                App.globalPut(proposal_votes_key(i.load()), Int(0))
            )
        ),
        Approve()
    )

    # Helper: check voting is open (within 7 days)
    voting_open = And(
        App.globalGet(global_voting_open) == Int(1),
        Global.latest_timestamp() < App.globalGet(global_voting_start) + Int(voting_period_seconds)
    )

    # Lock tokens for voting: user sends an Asset Transfer grouped with this call to lock tokens
    # This call records the locked tokens in local state as vote weight
    # User can only lock tokens once (no unlocking or adding more tokens in this simple version)
    on_lock = Seq(
        Assert(Global.group_size() == Int(2)),  # Must be grouped with asset transfer
        # The asset transfer must be from sender to this contract address
        Assert(Gtxn[0].type_enum() == TxnType.AssetTransfer),
        Assert(Gtxn[0].xfer_asset() == Int(token_id)),
        Assert(Gtxn[0].asset_receiver() == Global.current_application_address()),
        Assert(Gtxn[0].sender() == Txn.sender()),
        Assert(Gtxn[0].asset_amount() > Int(0)),
        # Ensure local state not already set (no double locking)
        Assert(App.localGet(Txn.sender(), local_vote_weight) == Int(0)),
        # Record locked tokens as vote weight
        App.localPut(Txn.sender(), local_vote_weight, Gtxn[0].asset_amount()),
        Approve()
    )

    # Vote on a proposal by index (uint64)
    # User must have locked tokens and not voted yet
    # Votes counted as tokens locked (weight)
    on_vote = Seq(
        Assert(voting_open),
        Assert(Txn.application_args.length() == Int(2)),
        # Parse proposal index
        proposal_index = Btoi(Txn.application_args[1]),
        Assert(proposal_index < App.globalGet(global_proposal_count)),
        # Check user has locked tokens and not voted yet
        vote_weight = App.localGet(Txn.sender(), local_vote_weight),
        Assert(vote_weight > Int(0)),
        Assert(App.localGet(Txn.sender(), local_voted) == Int(0)),
        # Increment proposal votes by vote_weight
        App.globalPut(proposal_votes_key(proposal_index), App.globalGet(proposal_votes_key(proposal_index)) + vote_weight),
        # Mark user as voted
        App.localPut(Txn.sender(), local_voted, Int(1)),
        Approve()
    )

    # Close voting after deadline (anyone can call)
    on_close_voting = Seq(
        Assert(App.globalGet(global_voting_open) == Int(1)),
        Assert(Global.latest_timestamp() >= App.globalGet(global_voting_start) + Int(voting_period_seconds)),
        App.globalPut(global_voting_open, Int(0)),
        Approve()
    )

    # Opt-in to store local state for voting participation
    on_opt_in = Seq(
        App.localPut(Txn.sender(), local_vote_weight, Int(0)),
        App.localPut(Txn.sender(), local_voted, Int(0)),
        Approve()
    )

    # No closeout or delete allowed for safety
    on_closeout = Reject()
    on_update = Reject()
    on_delete = Reject()

    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.OptIn, on_opt_in],
        [Txn.on_completion() == OnComplete.NoOp, Seq(
            Cond(
                [Txn.application_args[0] == Bytes("lock"), on_lock],
                [Txn.application_args[0] == Bytes("vote"), on_vote],
                [Txn.application_args[0] == Bytes("close_voting"), on_close_voting],
            ),
            Reject()
        )],
        [Txn.on_completion() == OnComplete.CloseOut, on_closeout],
        [Txn.on_completion() == OnComplete.UpdateApplication, on_update],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete],
    )

    return program


if __name__ == "__main__":
    # Example: token_id = 123456 (replace with actual ASA ID)
    approval_program = compileTeal(voting_contract(token_id=123456), mode=Mode.Application, version=6)
    clear_program = compileTeal(Approve(), mode=Mode.Application, version=6)
    print("// Approval Program")
    print(approval_program)
    print("// Clear State Program")
    print(clear_program)