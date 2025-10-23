"""
AI-Generated Smart Contract
Generated: 2025-10-18T23:59:58.016165
Description: Create an escrow contract that holds funds until both buyer and seller confirm the transaction.
"""

from pyteal import *

def escrow_contract(buyer: Addr, seller: Addr):
    """
    Escrow contract that holds funds until both buyer and seller confirm the transaction.
    Confirmation is done via application calls setting local state flags.
    Once both parties confirm, funds can be withdrawn by the seller.
    """

    # Constants
    FEE_LIMIT = Int(1000)  # Max fee allowed per transaction

    # Local state keys for confirmations
    buyer_confirm_key = Bytes("buyer_confirmed")
    seller_confirm_key = Bytes("seller_confirmed")

    # Helper to check no rekeying and no close remainder address
    def safety_checks(txn: Txn):
        return And(
            txn.rekey_to() == Global.zero_address(),
            txn.close_remainder_to() == Global.zero_address(),
            txn.fee() <= FEE_LIMIT,
        )

    # On creation: no special state needed, just approve
    on_creation = Seq([
        Assert(Global.group_size() == Int(1)),
        Approve()
    ])

    # On opt-in: allow buyer or seller to opt-in to store confirmation flags
    on_opt_in = Seq([
        Assert(Or(Txn.sender() == buyer, Txn.sender() == seller)),
        Approve()
    ])

    # On close-out: disallow to prevent accidental loss of confirmation flags
    on_close_out = Reject()

    # On update application: disallow to prevent unauthorized changes
    on_update = Reject()

    # On delete application: disallow to prevent accidental deletion
    on_delete = Reject()

    # Application call to confirm by buyer or seller
    # The sender must be buyer or seller, and sets their confirmation flag in local state
    confirm = Seq([
        Assert(Global.group_size() == Int(1)),
        Assert(Or(Txn.sender() == buyer, Txn.sender() == seller)),
        # Set local state key for sender to 1 (confirmed)
        If(Txn.sender() == buyer,
           App.localPut(Txn.sender(), buyer_confirm_key, Int(1)),
           App.localPut(Txn.sender(), seller_confirm_key, Int(1))
        ),
        Approve()
    ])

    # Withdraw funds by seller after both confirmed
    # This must be a grouped transaction:
    # Txn 0: Application call with argument "withdraw"
    # Txn 1: Payment transaction from escrow account to seller
    withdraw = Seq([
        Assert(Global.group_size() == Int(2)),

        # First txn must be this app call with arg "withdraw"
        Assert(Txn.application_args.length() == Int(1)),
        Assert(Txn.application_args[0] == Bytes("withdraw")),

        # Second txn must be payment from this escrow account to seller
        pay_txn = Gtxn[1],
        Assert(pay_txn.type_enum() == TxnType.Payment),
        Assert(pay_txn.sender() == Global.current_application_address()),
        Assert(pay_txn.receiver() == seller),
        Assert(pay_txn.close_remainder_to() == Global.zero_address()),
        Assert(pay_txn.rekey_to() == Global.zero_address()),
        Assert(pay_txn.fee() <= FEE_LIMIT),

        # Check that both buyer and seller have confirmed (local state == 1)
        buyer_confirmed = App.localGet(buyer, buyer_confirm_key),
        seller_confirmed = App.localGet(seller, seller_confirm_key),
        Assert(And(buyer_confirmed == Int(1), seller_confirmed == Int(1))),

        Approve()
    ])

    # Router to handle different application call types
    program = Cond(
        [Txn.application_id() == Int(0), on_creation],  # On create
        [Txn.on_completion() == OnComplete.OptIn, on_opt_in],
        [Txn.on_completion() == OnComplete.CloseOut, on_close_out],
        [Txn.on_completion() == OnComplete.UpdateApplication, on_update],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete],
        # NoOp calls: either confirm or withdraw
        [Txn.on_completion() == OnComplete.NoOp, 
            Cond(
                [Txn.application_args.length() == Int(1),
                 If(Txn.application_args[0] == Bytes("confirm"), confirm,
                    If(Txn.application_args[0] == Bytes("withdraw"), withdraw, Reject())
                 )
                ],
                # Reject if no or invalid args
                [Int(1), Reject()]
            )
        ],
    )

    # Ensure no rekeying or close remainder on all transactions
    safety = And(
        safety_checks(Txn),
        # Also check group size limits for withdraw
        Or(
            Global.group_size() == Int(1),
            Global.group_size() == Int(2)
        )
    )

    return And(safety, program)


if __name__ == "__main__":
    # Replace with actual buyer and seller Algorand addresses at deployment
    buyer_address = Addr("BUYER_ALGORAND_ADDRESS_HERE")
    seller_address = Addr("SELLER_ALGORAND_ADDRESS_HERE")

    approval_program = escrow_contract(buyer_address, seller_address)
    print(compileTeal(approval_program, mode=Mode.Application, version=6))