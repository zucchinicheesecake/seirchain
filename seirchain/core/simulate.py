import argparse
import time
import os
import sys
from datetime import datetime, timedelta
import random
import hashlib
import logging

# Adjust path to allow imports from seirchain
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from seirchain.triangular_ledger.triangular_ledger import TriangularLedger
from seirchain.wallet_manager import global_wallets as main_wallets_manager
from seirchain.data_types.transaction import Transaction, TransactionNode
from seirchain.miner import Miner
from seirchain.config import config
from seirchain.network.node import Node

logger = logging.getLogger(__name__)

def generate_random_transactions(num_transactions, current_ledger, wallets_manager):
    """Generates random transactions between existing wallets using the central wallets manager."""
    import os
    transactions = []
    # Get actual wallet IDs from the manager
    wallet_ids = list(wallets_manager.wallets.keys())
    if len(wallet_ids) < 2:
        return []

    for _ in range(num_transactions):
        sender_id = random.choice(wallet_ids)
        receiver_id = random.choice([wid for wid in wallet_ids if wid != sender_id])
        sender_balance = wallets_manager.get_balance(sender_id)

        if sender_balance > 0:
            amount = random.uniform(1, max(sender_balance * 0.1, 1))
            fee = amount * 0.001
            total_amount = amount + fee
            if sender_balance >= total_amount:
                # Use the manager's transfer method
                if wallets_manager.transfer_funds(sender_id, receiver_id, amount, fee):
                    import os
                    tx = Transaction(
                        transaction_data={
                            'from_addr': sender_id,
                            'to_addr': receiver_id,
                            'amount': amount,
                            'fee': fee,
                            'timestamp': time.time(),
                            'signature': "simulated_sig"
                        },
                        tx_hash=os.urandom(32).hex(),
                        timestamp=time.time()
                    )
                    transactions.append(TransactionNode(tx))
    return transactions

def run_simulation(network_name):
    logger.info(f"Running simulation for the {network_name} network...")
    ledger_filename = f"ledger_{network_name}.json"
    wallets_filename = f"wallets_{network_name}.json"
    
    current_ledger = None # Initialize as None

    # Try to load existing ledger
    if os.path.exists(ledger_filename):
        try:
            current_ledger = TriangularLedger.load_from_json(filename=ledger_filename)
            logger.info(f"Ledger loaded successfully from {ledger_filename}")

            # Load wallets state from file, or initialize if not found
            if main_wallets_manager.load_wallets(network_name) is None:
                logger.warning(f"Wallets file '{wallets_filename}' not found or invalid. Initializing empty wallets within manager.")
            else:
                logger.info(f"Wallets loaded successfully from {wallets_filename}")

            # Reconstruct wallet balances from transactions in the loaded ledger
            logger.info("Reconstructing wallet states from loaded ledger...")
            all_transactions = list(current_ledger.get_all_transactions()) # Convert generator to list
            for tx in all_transactions:
                # Ensure wallets exist in the manager before modifying balances
                if not main_wallets_manager.wallet_exists(tx.from_addr) and tx.from_addr != "0x0":
                     main_wallets_manager.add_wallet(tx.from_addr, 0)
                if not main_wallets_manager.wallet_exists(tx.to_addr):
                     main_wallets_manager.add_wallet(tx.to_addr, 0)
                
                # Update balances based on transaction history
                sender_id = tx.from_addr if tx.from_addr != "0x0" else None
                receiver_id = tx.to_addr

                if tx.from_addr == "0x0": # Coinbase transaction (mining reward)
                    if receiver_id:
                        main_wallets_manager.add_funds(receiver_id, tx.amount)
                else:
                    if sender_id and receiver_id:
                        main_wallets_manager.deduct_funds(sender_id, tx.amount + tx.fee) # Deduct from sender
                        main_wallets_manager.add_funds(receiver_id, tx.amount) # Add to receiver
            logger.info(f"Reconstructed {len(main_wallets_manager.wallets)} wallet states within the manager.")

        except Exception as e:
            logger.error(f"Error loading ledger from {ledger_filename}: {e}")
            logger.error(f"Simulation failed for {network_name} network. Exiting.")
            return

    # If no ledger was loaded (first run or error during load), we initialize a new one.
    if not current_ledger:
        logger.info("No existing ledger found. Initializing new network...")
        current_ledger = TriangularLedger(config.MAX_DEPTH) # Initialize an empty ledger instance

        # Initialize wallets directly using the manager
        for _ in range(config.NUM_SIMULATED_WALLETS):
            main_wallets_manager.add_wallet(f"SimulatedWallet_{main_wallets_manager.generate_wallet_id()[:6]}",
initial_balance=0)
        logger.info(f"Created {len(main_wallets_manager.wallets)} initial wallets via manager.")

        # Ensure the genesis miner address exists as a wallet in the manager
        miner_address = config.GENESIS_MINER_ADDRESS_testnet if network_name == "testnet" else "SIMULATED_MINER"
        if not main_wallets_manager.wallet_exists(miner_address):
            main_wallets_manager.add_wallet(miner_address, initial_balance=0)

        # For the first run, let's distribute some initial funds to random wallets
        logger.info("Distributing initial funds to some wallets for starting transactions...")
        initial_distribution_targets = [wid for wid in main_wallets_manager.wallets.keys() if main_wallets_manager.wallets[wid].address != miner_address]
        if initial_distribution_targets:
            num_targets = min(len(initial_distribution_targets), 5) # Distribute to max 5 wallets
            for _ in range(num_targets):
                target_id = random.choice(initial_distribution_targets)
                main_wallets_manager.add_funds(target_id, config.INITIAL_DISTRIBUTION_AMOUNT / num_targets)
                logger.info(f"  {config.INITIAL_DISTRIBUTION_AMOUNT / num_targets:.2f} to {main_wallets_manager.wallets[target_id].address[:8]}...")
        
        # Ensure the genesis miner address has a wallet created for it.
        miner_wallet_id = main_wallets_manager.get_wallet(miner_address).address
        if not miner_wallet_id:
            miner_wallet_id = main_wallets_manager.add_wallet(miner_address, initial_balance=0).address


    # Determine the miner's address for this simulation run
    miner_address = config.GENESIS_MINER_ADDRESS_testnet if network_name == "testnet" else "SIMULATED_MINER"
    miner_wallet_id = main_wallets_manager.get_wallet(miner_address).address # Get ID if not already found

    # Create Node instance
    node_instance = Node(ledger=current_ledger, wallet_manager=main_wallets_manager)
    node_instance.start()

    # Initialize Miner instance with correct arguments
    miner_instance = Miner(current_ledger, node_instance, main_wallets_manager, miner_address)

    # Simulation loop parameters
    simulation_duration = timedelta(minutes=config.SIMULATION_DURATION_MINUTES)
    end_time = datetime.now() + simulation_duration

    logger.info(f"\nSimulation will run for {config.SIMULATION_DURATION_MINUTES} minutes.")
    logger.info(f"Miner Address: {miner_address} (ID: {miner_wallet_id})")

    try:
        # Start miner threads
        miner_instance.start()

        while datetime.now() < end_time:
            # Generate and add transactions to the miner's pool
            new_transactions = generate_random_transactions(
                config.TRANSACTIONS_PER_ITERATION, current_ledger, main_wallets_manager
            )
            for tx_node in new_transactions:
                miner_instance.add_transaction_to_pool(tx_node)

            # Sleep to allow mining threads to work
            time.sleep(config.SIMULATION_LOOP_INTERVAL)

    except KeyboardInterrupt:
        logger.info("\nSimulation interrupted by user.")
    except Exception as e:
        logger.error(f"\nAn unexpected error occurred during simulation: {e}")
    finally:
        # Final save of the ledger and wallets state
        logger.info("\nSimulation finished. Saving final ledger state...")
        if current_ledger: # <--- SIMPLIFIED CONDITION to ensure save if ledger object exists
            try: # <--- ADDED TRY-EXCEPT for robustness during save
                current_ledger.save_to_json(ledger_filename)
                logger.info(f"Final ledger saved to {ledger_filename}")
                logger.info(f"Total Triads in ledger: {current_ledger.get_total_triads()}")
            except Exception as save_e:
                logger.error(f"Error saving final ledger to {ledger_filename}: {save_e}")
        else:
            logger.warning("No ledger to save.")
        logger.info("\nSaving final wallets state...")
        try:
            main_wallets_manager.save_wallets(network_name)
            logger.info(f"Final wallets saved to {wallets_filename}")
        except Exception as save_e:
            logger.error(f"Error saving final wallets to {wallets_filename}: {save_e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the SeirChain simulation.")
    parser.add_argument("network", choices=["testnet", "mainnet"], help="Specify the network to simulate (testnet or mainnet).")
    args = parser.parse_args()
    run_simulation(args.network)
