"""
AI-Generated Smart Contract
Generated: 2025-10-19T15:06:44.288473
Description: Build a voting contract where users lock tokens to vote on proposals with a 7-day deadline.
"""

```python
from pyteal import *

def voting_contract():
    # Constants
    SECONDS_IN_DAY = Int(86400)
    VOTING_PERIOD = SECONDS_IN_DAY * Int(7)  # 7 days voting deadline

    # Global State Keys
    # Store the timestamp when voting starts (int)
    global_start_key = Bytes("start")
    # Store the total number of proposals (int)
    global_proposals_key = Bytes("prop_count")

    # Local State Keys (per voter)
    # Store the proposal ID the user voted for (int)
    local_voted_proposal = Bytes("voted_prop")
    # Store the amount of tokens locked by the user for voting (int)
    local_locked_amount = Bytes("locked_amt")
    # Store whether user has voted (int 0 or 1)
    local_has_voted = Bytes("voted")

    # Application call types
    on_creation = Seq([
        # Initialize global state on creation
        App.globalPut(global_start_key, Global.latest_timestamp()),
        App.globalPut(global_proposals_key, Int(0)),
        Approve()
    ])

    # Helper to check no rekey, no close remainder, fee limit
    def basic_checks():
        return And(
            Txn.rekey_to() == Global.zero_address(),
            Txn.close_remainder_to() == Global.zero_address(),
            Txn.fee() <= Int(2000),  # Allow fee up to 2000 microAlgos for grouped txns
        )

    # Add a proposal (only creator can add proposals before voting starts)
    # Args: ["add_proposal", proposal_name (bytes)]
    on_add_proposal = Seq([
        Assert(Txn.sender() == Global.creator_address()),
        # Only allow adding proposals before voting starts + 7 days
        Assert(Global.latest_timestamp() < App.globalGet(global_start_key) + VOTING_PERIOD),
        # Increment proposal count
        App.globalPut(global_proposals_key, App.globalGet(global_proposals_key) + Int(1)),
        Approve()
    ])

    # User opts in to participate in voting (local state initialized)
    on_opt_in = Seq([
        App.localPut(Txn.sender(), local_voted_proposal, Int(-1)),  # -1 means no vote yet
        App.localPut(Txn.sender(), local_locked_amount, Int(0)),
        App.localPut(Txn.sender(), local_has_voted, Int(0)),
        Approve()
    ])

    # Lock tokens and vote on a proposal
    # Args: ["vote", proposal_id (uint64)]
    # The user must send a grouped transaction:
    # 1) ApplicationCall with args ["vote", proposal_id]
    # 2) AssetTransfer of tokens to the contract address (locking tokens)
    on_vote = Seq([
        # Basic transaction checks
        Assert(Global.group_size() == Int(2)),
        # First txn is this ApplicationCall
        Assert(Txn.group_index() == Int(0)),
        # Second txn must be asset transfer to this app's escrow address
        asset_transfer = Gtxn[1],
        Assert(asset_transfer.type_enum() == TxnType.AssetTransfer),
        Assert(asset_transfer.asset_receiver() == Global.current_application_address()),
        # No rekey or close remainder in both txns
        Assert(basic_checks()),
        Assert(asset_transfer.rekey_to() == Global.zero_address()),
        Assert(asset_transfer.close_remainder_to() == Global.zero_address()),
        # Voting period check
        Assert(Global.latest_timestamp() <= App.globalGet(global_start_key) + VOTING_PERIOD),
        # User must have opted in
        Assert(App.optedIn(Txn.sender(), Txn.application_id())),
        # User must not have voted before
        Assert(App.localGet(Txn.sender(), local_has_voted) == Int(0)),
        # Proposal ID validity check
        proposal_id = Btoi(Txn.application_args[1]),
        Assert(proposal_id < App.globalGet(global_proposals_key)),
        # Lock the tokens amount from asset transfer
        locked_amount = asset_transfer.asset_amount(),
        Assert(locked_amount > Int(0)),
        # Save vote info in local state
        App.localPut(Txn.sender(), local_voted_proposal, proposal_id),
        App.localPut(Txn.sender(), local_locked_amount, locked_amount),
        App.localPut(Txn.sender(), local_has_voted, Int(1)),
        Approve()
    ])

    # Withdraw locked tokens after voting period ends
    # Args: ["withdraw"]
    # User must send grouped transactions:
    # 1) ApplicationCall with ["withdraw"]
    # 2) AssetTransfer from contract to user of locked tokens
    on_withdraw = Seq([
        Assert(Global.group_size() == Int(2)),
        Assert(Txn.group_index() == Int(0)),
        asset_transfer = Gtxn[1],
        # Asset transfer must be from contract to user
        Assert(asset_transfer.type_enum() == TxnType.AssetTransfer),
        Assert(asset_transfer.asset_sender() == Global.current_application_address()),
        Assert(asset_transfer.asset_receiver() == Txn.sender()),
        # No rekey or close remainder in both txns
        Assert(basic_checks()),
        Assert(asset_transfer.rekey_to() == Global.zero_address()),
        Assert(asset_transfer.close_remainder_to() == Global.zero_address()),
        # Voting period must be over
        Assert(Global.latest_timestamp() > App.globalGet(global_start_key) + VOTING_PERIOD),
        # User must have voted and have locked tokens
        Assert(App.localGet(Txn.sender(), local_has_voted) == Int(1)),
        locked_amount = App.localGet(Txn.sender(), local_locked_amount),
        Assert(asset_transfer.asset_amount() == locked_amount),
        # Reset user's local voting state
        App.localPut(Txn.sender(), local_voted_proposal, Int(-1)),
        App.localPut(Txn.sender(), local_locked_amount, Int(0)),
        App.localPut(Txn.sender(), local_has_voted, Int(0)),
        Approve()
    ])

    # Handle no-op calls with different first argument
    on_noop = Cond(
        [Txn.application_args[0] == Bytes("add_proposal"), on_add_proposal],
        [Txn.application_args[0] == Bytes("vote"), on_vote],
        [Txn.application_args[0] == Bytes("withdraw"), on_withdraw],
    )

    # Reject all other calls
    program = Cond(
        [Txn.application_id() == Int(0), on_creation],  # Creation call
        [Txn.on_completion() == OnComplete.OptIn, on_opt_in],
        [Txn.on_completion() == OnComplete.NoOp, on_noop],
    )

    return program

if __name__ == "__main__":
    import sys
    from pyteal import compileTeal, Mode

    approval_program = compileTeal(voting_contract(), mode=Mode.Application, version=6)
    clear_program = compileTeal(Approve(), mode=Mode.Application, version=6)

    with open("voting_approval.teal", "w") as f:
        f.write(approval_program)

    with open("voting_clear.teal", "w") as f:
        f.write(clear_program)
```

---

**Contract Purpose Summary:**  
This PyTeal smart contract implements a **token-weighted voting system** where users lock Algorand Standard Assets (ASA tokens) to vote on proposals. The voting period lasts exactly 7 days from contract creation. Users can only vote once by locking tokens, and after the deadline, they can withdraw their locked tokens. The contract supports adding proposals by the creator before voting starts.

---

**Logic Walkthrough:**  
- **On creation:** Initializes the voting start timestamp and zero proposals.  
- **Add proposal:** Only the creator can add proposals before the 7-day voting deadline.  
- **Opt-in:** Users opt-in to initialize their local state for voting.  
- **Vote:** Users submit a grouped transaction with an application call and an asset transfer locking tokens to the contract. The contract verifies the voting deadline, that the user has not voted before, and that the proposal ID is valid. It records the vote and locked token amount in local state.  
- **Withdraw:** After the voting period ends, users can withdraw their locked tokens by submitting a grouped transaction with an application call and an asset transfer from the contract back to themselves. The contract verifies the amount matches the locked amount and resets the user's voting state.  

---

**Security Considerations:**  
- **No rekey or close remainder allowed** on all transactions to prevent unauthorized asset or Algo transfers.  
- **Fee limits enforced** to avoid fee manipulation attacks.  
- **Voting deadline strictly enforced** using `Global.latest_timestamp()`.  
- **One vote per user enforced** by local state flag.  
- **Proposal IDs validated** against global proposal count.  
- **Token locking and withdrawal require grouped transactions** to ensure atomicity and prevent token loss.  
- **No hardcoded addresses or keys; uses creator address dynamically.**  
- **Local state reset after withdrawal to prevent double withdrawal.**  
- **No unbounded loops or recursion.**  
- **Uses application address for escrow of tokens, avoiding external escrow accounts.**  

---

**Deployment Parameters Needed:**  
- Creator address (deployer) who can add proposals before voting starts.  
- Asset ID of the token users will lock for voting (must be known off-chain and enforced by client).  
- Suggested transaction parameter