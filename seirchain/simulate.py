import sys
import os
import time
import random
import json
import traceback # Import traceback for detailed error logging

# Ensure the seirchain package is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from seirchain.data_types.wallets import Wallets
from seirchain.data_types.triangular_ledger import TriangularLedger
from seirchain.miner import Miner
from seirchain.config import Config
from seirchain.data_types.triad import Triad # Import the new Triad class

# --- Configuration ---
# These are singleton instances, loaded once at the script's entry point
config = Config.instance()
wallets = Wallets.instance()
ledger = TriangularLedger.instance()

# --- Simulation Functions ---

def generate_random_transaction_params():
    """Generates random sender, receiver, and amount for a transaction using actual wallet IDs."""
    all_wallet_ids = wallets.get_all_wallet_ids()
    
    # Ensure there are at least two wallets to pick from for a transaction
    if len(all_wallet_ids) < 2:
        print("Error: Not enough wallets to generate a transaction. Need at least two.")
        return None, None, None # Indicate failure to generate

    sender_wallet_id = random.choice(all_wallet_ids)
    receiver_wallet_id = random.choice(all_wallet_ids)

    # Ensure sender and receiver are different for meaningful transactions
    while sender_wallet_id == receiver_wallet_id:
        receiver_wallet_id = random.choice(all_wallet_ids)

    amount = round(random.uniform(1.0, 500.0), 2)
    return sender_wallet_id, receiver_wallet_id, amount

def run_simulation(num_transactions, network_name):
    """
    Runs the blockchain simulation for a specified network.
    """
    try:
        print(f"Running simulation for the {network_name} network...")
        
        print(f"Configuration loaded for network: {network_name}")
        print(f"  Difficulty: {config.DIFFICULTY}")
        print(f"  Max Depth: {config.MAX_DEPTH}")
        print(f"  Mining Reward: {config.MINING_REWARD}")
        print(f"  Transaction Fee: {config.TRANSACTION_FEE}")
        print(f"  Max Transactions to Simulate: {num_transactions}")

        # Initialize miner with the GENESIS_MINE_WALLET address
        miner_address = wallets.get_wallet_id_by_name("GENESIS_MINE_WALLET")
        if miner_address is None:
            print("Error: 'GENESIS_MINE_WALLET' not found. Ensure wallets are properly initialized.")
            sys.exit(1) # Exit if the critical miner wallet isn't found
            
        miner = Miner.instance(miner_address, network_name)

        print("Starting simulation...")
        start_time = time.time()
        
        transactions_processed_count = 0
        pending_transactions = [] # Placeholder for a transaction pool (future enhancement)

        # For now, we will directly process transactions into blocks
        # In a future step, this will be replaced by pulling from a mempool
        for i in range(1, num_transactions + 1):
            print(f"--- Processing Transaction {i} ---")
            sender, receiver, amount = generate_random_transaction_params()
            fee = config.TRANSACTION_FEE

            if sender is None: # Check if generate_random_transaction_params failed (e.g., not enough wallets)
                print("Skipping transaction due to insufficient wallets.")
                continue

            # Attempt to process the transaction
            if wallets.transfer_funds(sender, receiver, amount, fee):
                # For now, just a placeholder of the transaction data, not a full Transaction object
                # This will be enhanced later when we create a full Transaction class
                transaction_data = {
                    "sender": sender,
                    "receiver": receiver,
                    "amount": amount,
                    "fee": fee,
                    "timestamp": time.time()
                }
                pending_transactions.append(transaction_data) # Add to pending for the block

                print(f"Transaction successful. Balances updated.")

                # If we have enough transactions for a block, or it's the last one, mine a block
                # For simplicity, we'll mine a block after each transaction for now.
                # In a real scenario, a block contains multiple transactions from a mempool.
                
                # Get the previous hash for the new Triad
                previous_hash = ledger.chain[-1].hash if ledger.chain else "genesis_triad_hash"
                next_index = len(ledger.chain)

                # Corrected from miner.get_miner_address() to miner.miner_address
                print(f"Miner {miner.miner_address[:8]}... starting to mine Triad...")
                
                # Mine a new Triad (passing current pending transactions)
                new_triad = miner.mine_triad(next_index, previous_hash, pending_transactions, network_name)

                if new_triad:
                    ledger.add_triad(new_triad)
                    print(f"Adding Triad {new_triad.index} to ledger...")
                    transactions_processed_count += len(pending_transactions) # Count transactions added to this block
                    pending_transactions = [] # Clear pending transactions after mining a block
                else:
                    print(f"Mining failed for Triad {next_index}. Transactions not processed into a block.")
                    # In a real system, these transactions would return to the mempool
                    
            else:
                print("Transaction failed. Insufficient funds or invalid details.")

        end_time = time.time()
        print("Simulation finished. Total transactions processed:", transactions_processed_count)
        print(f"Time taken: {end_time - start_time:.2f} seconds")

        # Save current state of wallets and ledger
        wallets.save_wallets(network_name)
        ledger.save_ledger(network_name)
        print(f"Wallets and Ledger saved for {network_name}.")

        print_final_status()

    except Exception as e:
        print(f"Simulation failed for {network_name} network. Exiting.")
        print("Traceback (most recent call last):")
        traceback.print_exc() # This prints the detailed error
        sys.exit(1) # Exit with an error code

    print(f"Simulation completed successfully for {network_name} network.") # This line should only be reached on success

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
    parser.add_argument("--transactions", type=int, default=5,
                        help="Number of transactions to simulate. Default is 5.")

    args = parser.parse_args()

    # Create dummy wallets/config/ledger files if they don't exist for the network
    # This ensures a clean start or continues from last state
    # These singleton instances MUST be loaded/initialized BEFORE run_simulation is called
    config.load_config(args.network)
    wallets.load_wallets(args.network)
    ledger.load_ledger(args.network, config.MAX_DEPTH)

    run_simulation(args.transactions, args.network)
