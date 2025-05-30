import hashlib
import time
import argparse
import os
from seirchain.triangular_ledger.ledger import TriangularLedger, Triangle, TransactionNode
from seirchain.data_types.transaction import Transaction
from seirchain.wallet_manager.keys import Wallet
from seirchain.enhanced_miner.cpu_miner import CpuMiner
from seirchain.config import config # Corrected import

def generate_genesis_triad(network_name: str):
    """
    Generates the genesis triad (root block and initial distribution) for the SeirChain.
    """
    print(f"\n?? Generating Genesis Triad for {network_name.upper()}...\n")

    # Use the globally imported 'config' object from seirchain.config.
    # The 'config' object is an instance of the Config class.
    # We'll derive network-specific values and access global config attributes.

    # Derive chain_id from network_name (e.g., 'testnet' or 'mainnet')
    chain_id = network_name

    # Derive ledger_file_name based on the network
    ledger_file_name = f"ledger_{network_name}.json"

    # Access attributes directly from the imported config object
    max_depth = config.MAX_DEPTH
    ledger_version = 1.0 # Assuming a default, as it's not explicitly in config.py
    genesis_difficulty = config.DIFFICULTY

    # The ledger file should be created/checked in the current working directory
    # where the run_genesis.sh script is executed.
    full_ledger_path = ledger_file_name # <--- SIMPLIFIED PATH HANDLING
    if os.path.exists(full_ledger_path):
        print(f"⚠️ Warning: {ledger_file_name} already exists. To regenerate, delete it first.")
        return
    # Step 1: Initialize the Ledger
    ledger = TriangularLedger(max_depth=max_depth, ledger_version=ledger_version)
    # Step 2: Mine the Genesis Block (Root Triangle)
    miner = CpuMiner()
    miner.difficulty = genesis_difficulty
    miner.miner_address = "GENESIS_MINER_" + chain_id
    print(f"⛏️ Mining Genesis block for {chain_id}...")
    genesis_initial_supply = 1_000_000.00
    genesis_tx = Transaction(
        sender="0"*40,
        receiver=miner.miner_address,
        amount=genesis_initial_supply,
        fee=0.0
    )
    genesis_tx_node = TransactionNode(genesis_tx.to_dict(), genesis_tx.hash_transaction())
    ledger.root.add_transaction(genesis_tx_node)
    mined_genesis_triangle = miner.mine(ledger.root, genesis_tx)
    if mined_genesis_triangle:
        print(f"✅   Genesis block mined by: {mined_genesis_triangle.mined_by} for {chain_id}")
    else:
        print(f"❌   Failed to mine Genesis block for {chain_id}. Exiting.")
        return
    # Step 3: Distribute Initial Funds
    num_initial_wallets = 5
    initial_fund_amount_per_wallet = 2000.00
    initial_wallets = [Wallet(initial_balance=0.0) for _ in range(num_initial_wallets)]
    distribution_transactions = []
    print(f"?? Distributing initial funds to {num_initial_wallets} wallets...")
    for wallet in initial_wallets:
        tx = Transaction(
            sender=miner.miner_address,
            receiver=wallet.address,
            amount=initial_fund_amount_per_wallet,
            fee=0.00
        )
        distribution_transactions.append(tx)
    print("⛏️ Mining initial distribution transactions...")
    mined_count = 0
    for tx in distribution_transactions:
        target_depth_for_dist = 0
        triangle_to_mine_into, _ = ledger.find_triangle(target_depth_for_dist)
        if not triangle_to_mine_into:
            print(f"⚠️ Could not find suitable triangle to mine distribution transaction {tx.hash_transaction()[:8]}...")
            continue
        mined_tx_triangle = miner.mine(triangle_to_mine_into, tx)
        if mined_tx_triangle:
            mined_count += 1
        else:
            print(f"❌  Failed to mine distribution transaction {tx.hash_transaction()[:8]}...")
    if mined_count == len(distribution_transactions):
        print("✅   All initial distribution transactions mined successfully.")
    else:
        print(f"⚠️ Only {mined_count}/{len(distribution_transactions)} initial distribution transactions mined.")
    # Step 4: Save the Genesis Ledger
    ledger.save_to_file(full_ledger_path) # Uses the simplified path
    print(f"?? Genesis Ledger for {chain_id} saved to {ledger_file_name}")
    print(f"Genesis Triad generation complete for {chain_id}.")
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate the genesis triad for SeirChain.")
    parser.add_argument('network', type=str, choices=['testnet', 'mainnet'],
                        help='Specify the network for which to generate the genesis triad (testnet or mainnet).')
    args = parser.parse_args()
    generate_genesis_triad(args.network)

