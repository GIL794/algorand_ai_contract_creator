"""
AI-Generated Smart Contract
Generated: 2025-10-19T13:11:56.177024
Description: Build a voting contract where users lock tokens to vote on proposals with a 7-day deadline.
"""

```python
from pyteal import *

def voting_contract():

    # Constants
    VOTING_DURATION = Int(7 * 24 * 60 * 60)  # 7 days in seconds
    TOKEN_ID_KEY = Bytes("token_id")          # Global key to store ASA ID used for voting
    PROPOSAL_KEY = Bytes("proposal")          # Global key to store current proposal (bytes)
    START_TIME_KEY = Bytes("start_time")      # Global key to store voting start timestamp
    TOTAL_VOTES_KEY = Bytes("total_votes")    # Global key to store total tokens locked (votes)
    VOTER_LOCK_KEY = Bytes("lock_")           # Prefix for local state key to store locked tokens per voter

    # Application global state schema:
    # - token_id: uint64 (ASA ID)
    # - proposal: bytes (proposal description or ID)
    # - start_time: uint64 (voting start timestamp)
    # - total_votes: uint64 (total tokens locked for voting)

    # Local state schema:
    # - lock_<app_id>: uint64 (tokens locked by voter for this proposal)

    # Helper to get local state key for locked tokens for this voter
    def voter_lock_key():
        # Use app id suffix to avoid collisions if multiple apps
        return Concat(VOTER_LOCK_KEY, Itob(Global.current_application_id()))

    # On creation: initialize global state with token ASA ID, proposal, start time, total_votes=0
    on_creation = Seq(
        Assert(Txn.application_args.length() == Int(3)),
        # Args: [token_id (uint64), proposal (bytes), start_time (uint64)]
        App.globalPut(TOKEN_ID_KEY, Btoi(Txn.application_args[0])),
        App.globalPut(PROPOSAL_KEY, Txn.application_args[1]),
        App.globalPut(START_TIME_KEY, Btoi(Txn.application_args[2])),
        App.globalPut(TOTAL_VOTES_KEY, Int(0)),
        Approve()
    )

    # Helper: check voting period is active (current timestamp < start_time + 7 days)
    voting_active = And(
        Global.latest_timestamp() >= App.globalGet(START_TIME_KEY),
        Global.latest_timestamp() < App.globalGet(START_TIME_KEY) + VOTING_DURATION
    )

    # Helper: check voting period ended
    voting_ended = Global.latest_timestamp() >= App.globalGet(START_TIME_KEY) + VOTING_DURATION

    # On opt-in: initialize local locked tokens to 0
    on_opt_in = Seq(
        App.localPut(Txn.sender(), voter_lock_key(), Int(0)),
        Approve()
    )

    # On closeout: only allow if user has no locked tokens (to prevent losing locked tokens)
    on_closeout = Seq(
        Assert(App.localGet(Txn.sender(), voter_lock_key()) == Int(0)),
        Approve()
    )

    # On update or delete: disallow (for security)
    on_update = Reject()
    on_delete = Reject()

    # On vote:
    # Args: ["vote", amount_to_lock (uint64)]
    # User must send an inner transaction transferring 'amount_to_lock' tokens (ASA) to this contract
    # Lock tokens in local state and increase total_votes global state
    on_vote = Seq(
        Assert(Txn.application_args.length() == Int(2)),
        Assert(voting_active),

        # Parse amount to lock
        (amount := Btoi(Txn.application_args[1])),

        # Must be > 0
        Assert(amount > Int(0)),

        # Check user opted in local state
        Assert(App.optedIn(Txn.sender(), Global.current_application_id())),

        # Check inner transaction is present and valid:
        # Inner transaction must be an Asset Transfer of the correct ASA from sender to this contract
        Assert(Global.group_size() == Int(2)),
        (inner_txn := Gtxn[1]),
        Assert(inner_txn.type_enum() == TxnType.AssetTransfer),
        Assert(inner_txn.xfer_asset() == App.globalGet(TOKEN_ID_KEY)),
        Assert(inner_txn.asset_amount() == amount),
        Assert(inner_txn.sender() == Txn.sender()),
        Assert(inner_txn.asset_receiver() == Global.current_application_address()),
        Assert(inner_txn.fee() <= Int(1000)),  # reasonable fee limit

        # Update local locked tokens and global total votes
        (current_locked := App.localGet(Txn.sender(), voter_lock_key())),
        App.localPut(Txn.sender(), voter_lock_key(), current_locked + amount),
        App.globalPut(TOTAL_VOTES_KEY, App.globalGet(TOTAL_VOTES_KEY) + amount),

        Approve()
    )

    # On withdraw:
    # Args: ["withdraw", amount_to_unlock (uint64)]
    # User can unlock tokens after voting period ended by transferring tokens back from contract to user
    # Contract must send tokens back via inner transaction
    on_withdraw = Seq(
        Assert(Txn.application_args.length() == Int(2)),
        Assert(voting_ended),

        (amount := Btoi(Txn.application_args[1])),

        # Must be > 0
        Assert(amount > Int(0)),

        # Check user opted in local state
        Assert(App.optedIn(Txn.sender(), Global.current_application_id())),

        (current_locked := App.localGet(Txn.sender(), voter_lock_key())),
        Assert(current_locked >= amount),

        # Prepare inner transaction to send tokens back to user
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.AssetTransfer,
            TxnField.xfer_asset: App.globalGet(TOKEN_ID_KEY),
            TxnField.asset_receiver: Txn.sender(),
            TxnField.asset_amount: amount,
            TxnField.fee: Int(0),  # fee pooling by outer txn
        }),
        InnerTxnBuilder.Submit(),

        # Update local and global state
        App.localPut(Txn.sender(), voter_lock_key(), current_locked - amount),
        App.globalPut(TOTAL_VOTES_KEY, App.globalGet(TOTAL_VOTES_KEY) - amount),

        Approve()
    )

    # Handle no-op calls: vote or withdraw
    on_noop = Cond(
        [Txn.application_args[0] == Bytes("vote"), on_vote],
        [Txn.application_args[0] == Bytes("withdraw"), on_withdraw],
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_creation],  # Creation call
        [Txn.on_completion() == OnComplete.OptIn, on_opt_in],
        [Txn.on_completion() == OnComplete.CloseOut, on_closeout],
        [Txn.on_completion() == OnComplete.UpdateApplication, on_update],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete],
        [Txn.on_completion() == OnComplete.NoOp, on_noop],
    )

    return program


if __name__ == "__main__":
    import sys
    from pyteal import compileTeal, Mode

    approval_program = compileTeal(voting_contract(), mode=Mode.Application, version=6)
    clear_state_program = compileTeal(Approve(), mode=Mode.Application, version=6)

    print("// Approval Program")
    print(approval_program)
    print("// Clear State Program")
    print(clear_state_program)
```

---

**Contract Purpose Summary:**  
This PyTeal smart contract implements a **token-weighted voting system** where users lock a specified Algorand Standard Asset (ASA) to vote on a proposal within a fixed 7-day voting period. Users lock tokens by transferring them to the contract during the voting period and can withdraw their tokens only after the voting deadline has passed.

---

**Logic Walkthrough:**  
- **Creation:** The contract is initialized with three arguments: the ASA token ID used for voting, the proposal identifier (arbitrary bytes), and the voting start timestamp. It sets these in global state and initializes total votes to zero.  
- **Opt-in:** Users must opt-in to the app to participate; their locked token balance is initialized to zero in local state.  
- **Voting:** During the 7-day voting window, users submit a "vote" call with the amount of tokens to lock. They must include an inner transaction transferring that amount of the specified ASA from their account to the contract. The contract updates the user's locked token balance and the global total votes accordingly.  
- **Withdrawal:** After the voting period ends, users can call "withdraw" with an amount to unlock tokens. The contract sends back the tokens via an inner transaction and updates local and global states.  
- **Closeout:** Users can only close out if they have no locked tokens, preventing accidental loss of locked tokens.  
- **Update/Delete:** Disabled for security to prevent unauthorized changes.  
- **Fee Checks:** Inner transactions have fee limits, and the outer transaction must cover fees (fee pooling).  
- **Security:** The contract enforces strict checks on transaction types, sender/receiver addresses, and voting period boundaries.

---

**Security Considerations:**  
- **No hardcoded addresses or keys:** The ASA token ID and proposal are set at creation.  
- **No unbounded loops:** The contract uses no loops.  
- **Reentrancy safe:** Inner transactions are atomic and controlled; no reentrant calls possible.  
- **Safe global/local state manipulation:** Uses explicit keys and checks.  
- **Integer overflow:** PyT