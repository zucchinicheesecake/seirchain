# seirchain/simulate.py
import sys
import os
import time
import random
import json
import traceback
import uuid

# Ensure the seirchain package is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from seirchain.data_types.wallets import Wallets
from seirchain.data_types.triangular_ledger import TriangularLedger
from seirchain.data_types.triad import Triad
from seirchain.data_types.transaction_node import TransactionNode
from seirchain.miner import Miner
from seirchain.config import Config

# --- Configuration ---
config = Config.instance()
wallets = Wallets.instance()
ledger = TriangularLedger.instance()

# --- Simulation Functions ---

def generate_random_transaction_params():
    """Generates random sender, receiver, and amount for a transaction using actual wallet IDs."""
    all_wallet_ids = wallets.get_all_wallet_ids()
    
    if len(all_wallet_ids) < 2:
        return None, None, None

    sender_wallet_id = random.choice(all_wallet_ids)
    receiver_wallet_id = random.choice(all_wallet_ids)

    while sender_wallet_id == receiver_wallet_id:
        receiver_wallet_id = random.choice(all_wallet_ids)

    amount = round(random.uniform(1.0, 500.0), 2)
    return sender_wallet_id, receiver_wallet_id, amount

def run_parallel_mining_simulation(num_transactions_to_simulate, network_name):
    """
    Orchestrates the parallel mining simulation for the Triad Matrix.
    This simulates multiple miners choosing Triads to extend concurrently.
    Now specifically implements multi-parent selection.
    """
    print("Initializing SeirChain Triad Matrix simulation...")
    print(f"Configuration for network: {network_name}")
    print(f"  Difficulty: {config.DIFFICULTY}")
    print(f"  Max Depth: {config.MAX_DEPTH}")
    print(f"  Mining Reward: {config.MINING_REWARD}")
    print(f"  Transaction Fee: {config.TRANSACTION_FEE}")
    print(f"=== SeirChain Triad Matrix Simulation ===")
    print(f"Network: {network_name}")
    print(f"Implementing Sierpinski Triangle-based fractal ledger with multi-parent linking")
    print(f"Target transactions: {num_transactions_to_simulate}")

    miner_address = wallets.get_wallet_id_by_name("GENESIS_MINE_WALLET")
    if miner_address is None:
        print("Error: 'GENESIS_MINE_WALLET' not found. Ensure wallets are properly initialized.")
        return False
        
    miner = Miner.instance(miner_address, network_name)

    start_time = time.time()
    
    transaction_pool = []
    transactions_generated = 0
    transactions_processed_count = 0

    # Ensure Genesis Triad exists before starting
    if not ledger.triads:
        print("Ledger is empty, initializing Genesis Triad...")
        ledger._initialize_genesis_triad()
        ledger.save_ledger(network_name)

    print("\n--- Generating Transactions ---")
    while transactions_generated < num_transactions_to_simulate:
        sender, receiver, amount = generate_random_transaction_params()
        if sender is None:
            break

        fee = config.TRANSACTION_FEE
        transaction = TransactionNode(sender_address=sender, receiver_address=receiver, amount=amount, fee=fee)
        
        # Simulate signing the transaction with a simplified private key (sender's address for simplicity)
        transaction.sign(sender) 

        # In a real system, verification would happen at the peer level before entering mempool.
        # For this simulation, we'll verify it here as it's added to the pool.
        # This uses the sender's address as a pseudo public key for verification
        if not transaction.verify_signature(sender): 
            print(f"  Transaction {transaction.hash[:8]}... from {sender[:6]}... failed signature verification. Skipping.")
            continue # Skip invalid transactions
        
        if wallets.transfer_funds(sender, receiver, amount, fee):
            transaction_pool.append(transaction)
            transactions_generated += 1
        else:
            break

    print(f"\n--- Starting Mining Cycles ---")
    print(f"Total transactions generated: {transactions_generated}. Now mining them into Triads.")

    mining_cycle = 0
    while transaction_pool and ledger.get_max_current_depth() < config.MAX_DEPTH:
        mining_cycle += 1
        print(f"\n--- Mining Cycle {mining_cycle} ---")
        
        candidate_parents_list = ledger.get_candidate_parents()
        if not candidate_parents_list:
            print("No suitable parent Triads found to extend. Halting mining.")
            break

        selected_parent_hashes = []
        num_parents_to_select = random.randint(1, min(3, len(candidate_parents_list)))
        
        random.shuffle(candidate_parents_list) 
        
        for i in range(num_parents_to_select):
            if i < len(candidate_parents_list):
                selected_parent_hashes.append(candidate_parents_list[i].hash)
        
        if not selected_parent_hashes:
            print("Could not select any parents for new Triad. Halting mining.")
            break

        max_parent_depth = 0
        for p_hash in selected_parent_hashes:
            parent_triad = ledger.get_triad(p_hash)
            if parent_triad:
                max_parent_depth = max(max_parent_depth, parent_triad.depth)
        new_depth = max_parent_depth + 1

        if new_depth > config.MAX_DEPTH:
            print(f"Cannot mine new Triad: Max Depth ({config.MAX_DEPTH}) reached or exceeded. Halting mining.")
            break
            
        batch_size = min(random.randint(1, 5), len(transaction_pool))
        transactions_for_triad = [transaction_pool.pop(0) for _ in range(batch_size)]

        if not transactions_for_triad:
            print("Transaction pool is empty. Stopping mining.")
            break

        new_triad_id = str(uuid.uuid4())

        print(f"Miner {miner.miner_address[:8]}... attempting to mine new Triad {new_triad_id[:8]}...")
        print(f"  Selected Parent Hashes ({len(selected_parent_hashes)}): {[h[:8] + '...' for h in selected_parent_hashes]}")
        print(f"  New Triad Depth: {new_depth}")
        print(f"  Transactions in Triad: {len(transactions_for_triad)}")

        mined_triad = miner.mine_triad(
            triad_id=new_triad_id,
            depth=new_depth,
            parent_hashes=selected_parent_hashes,
            transactions=transactions_for_triad,
            network_name=network_name
        )

        if mined_triad:
            if ledger.add_triad(mined_triad):
                transactions_processed_count += len(mined_triad.transactions)
                print(f"  Successfully added Triad {mined_triad.triad_id[:8]}... to ledger. Total Triads: {len(ledger.triads)}")
                print(f"  Transactions processed so far: {transactions_processed_count}")
            else:
                print(f"  Failed to add Triad {mined_triad.triad_id[:8]}... to ledger. Transactions returned to pool.")
                transaction_pool.extend(transactions_for_triad)
        else:
            print(f"  Mining attempt for Triad {new_triad_id[:8]}... failed. Transactions returned to pool.")
            transaction_pool.extend(transactions_for_triad)

        time.sleep(0.1)

    end_time = time.time()
    print("\n--- Simulation Summary ---")
    print(f"Simulation finished. Total transactions processed: {transactions_processed_count} out of {transactions_generated} generated.")
    print(f"Remaining transactions in pool: {len(transaction_pool)}")
    print(f"Time taken: {end_time - start_time:.2f} seconds")

    wallets.save_wallets(network_name)
    ledger.save_ledger(network_name)
    print(f"Wallets and Ledger saved for {network_name}.")

    print_final_status()
    return True

def print_final_status():
    """Prints the final state of wallets and the ledger."""
    print("\n--- Final Wallet Balances (Top 5) ---")
    wallets.print_balances()

    print("\n--- Ledger Overview ---")
    ledger.print_ledger_status()


# --- Main Execution ---
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the SeirChain simulation.")
    parser.add_argument("network", type=str, help="The network to simulate (e.g., 'mainnet', 'testnet').")
    parser.add_argument("--transactions", type=int, default=config.MAX_TRANSACTIONS_TO_SIMULATE,
                        help=f"Number of transactions to simulate. Default is {config.MAX_TRANSACTIONS_TO_SIMULATE}.")

    args = parser.parse_args()

    config.load_config(args.network)
    wallets.load_wallets(args.network)
    ledger.load_ledger(args.network, config.MAX_DEPTH)

    try:
        success = run_parallel_mining_simulation(args.transactions, args.network)
        if success:
            print(f"\nSimulation completed successfully for {args.network} network.")
        else:
            print(f"\nSimulation failed for {args.network} network.")
            sys.exit(1)
    except Exception as e:
        print(f"\nSimulation failed for {args.network} network. Exiting.")
        print("Traceback (most recent call last):")
        traceback.print_exc()
        sys.exit(1)

