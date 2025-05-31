import argparse
import time
import os
import sys
import signal
from datetime import datetime, timedelta
import random
import hashlib
import logging

# Adjust path to allow imports from seirchain
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from seirchain.core.triangular_ledger.triangular_ledger import TriangularLedger
from seirchain.core.wallet_manager import global_wallets as main_wallets_manager
from seirchain.core.data_types.transaction import Transaction, TransactionNode
from seirchain.core.miner import Miner
from seirchain.config import config
from seirchain.core.network.node import Node

logger = logging.getLogger(__name__)

def validate_config():
    """
    Validate configuration parameters for simulation.
    """
    from seirchain.config import config
    if not isinstance(config.SIMULATION_DURATION_MINUTES, int) or config.SIMULATION_DURATION_MINUTES <= 0:
        raise ValueError("SIMULATION_DURATION_MINUTES must be a positive integer")
    if not isinstance(config.TRANSACTIONS_PER_ITERATION, int) or config.TRANSACTIONS_PER_ITERATION < 0:
        raise ValueError("TRANSACTIONS_PER_ITERATION must be a non-negative integer")
    if not isinstance(config.SIMULATION_LOOP_INTERVAL, (int, float)) or config.SIMULATION_LOOP_INTERVAL <= 0:
        raise ValueError("SIMULATION_LOOP_INTERVAL must be a positive number")
    if not isinstance(config.NUM_SIMULATED_WALLETS, int) or config.NUM_SIMULATED_WALLETS <= 0:
        raise ValueError("NUM_SIMULATED_WALLETS must be a positive integer")
    if not isinstance(config.MAX_DEPTH, int) or config.MAX_DEPTH <= 0:
        raise ValueError("MAX_DEPTH must be a positive integer")

def initialize_wallets(wallets_manager):
    """
    Initialize wallets for simulation.
    """
    wallets_manager.wallets.clear()
    for _ in range(config.NUM_SIMULATED_WALLETS):
        wallets_manager.add_wallet(wallets_manager.generate_wallet_id(), initial_balance=0)
    logging.info(f"Created {len(wallets_manager.wallets)} initial wallets via manager.")

def distribute_initial_funds(wallets_manager, miner_address):
    """
    Distribute initial funds to wallets for starting transactions.
    """
    initial_distribution_targets = [wid for wid in wallets_manager.wallets.keys() if wid != miner_address]
    if initial_distribution_targets:
        num_targets = min(len(initial_distribution_targets), 5)  # Distribute to max 5 wallets
        for _ in range(num_targets):
            target_id = random.choice(initial_distribution_targets)
            wallets_manager.add_funds(target_id, config.INITIAL_DISTRIBUTION_AMOUNT / num_targets)
            logging.info(f"  {config.INITIAL_DISTRIBUTION_AMOUNT / num_targets:.2f} to {target_id[:8]}...")

def generate_random_transactions(num_transactions, current_ledger, wallets_manager):
    """
    Generates random transactions between existing wallets using the central wallets manager.
    """
    transactions = []
    wallet_ids = list(wallets_manager.wallets.keys())
    if len(wallet_ids) < 2:
        return transactions

    for _ in range(num_transactions):
        sender_id = random.choice(wallet_ids)
        receiver_id = random.choice([wid for wid in wallet_ids if wid != sender_id])
        sender_balance = wallets_manager.get_balance(sender_id)

        if sender_balance > 0:
            amount = random.uniform(1, max(sender_balance * 0.1, 1))
            fee = amount * 0.001
            total_amount = amount + fee
            if sender_balance >= total_amount:
                if wallets_manager.transfer_funds(sender_id, receiver_id, amount, fee):
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

def initialize_simulation_wallets(wallets_manager, miner_address):
    """
    Initialize wallets and distribute initial funds for simulation.
    """
    initialize_wallets(wallets_manager)
    if not wallets_manager.wallet_exists(miner_address):
        wallets_manager.add_wallet(miner_address, initial_balance=0)
    distribute_initial_funds(wallets_manager, miner_address)

def process_transactions(miner_instance, current_ledger, wallets_manager):
    """
    Generate and add transactions to the miner's pool with retry/backoff.
    """
    retry_attempts = 3
    for attempt in range(retry_attempts):
        try:
            new_transactions = generate_random_transactions(
                config.TRANSACTIONS_PER_ITERATION, current_ledger, wallets_manager
            )
            for tx_node in new_transactions:
                miner_instance.add_transaction_to_pool(tx_node)
            break
        except Exception as e:
            logger.error(f"Error generating or adding transactions: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
    else:
        logger.error("Failed to generate or add transactions after retries.")

def simulation_loop(miner_instance, current_ledger, wallets_manager, end_time):
    """
    Main simulation loop.
    """
    last_log_time = datetime.now()
    last_tx_count = 0
    pause_simulation = False

    def handle_pause_resume():
        nonlocal pause_simulation
        pause_simulation = not pause_simulation
        logger.info(f"Simulation {'paused' if pause_simulation else 'resumed'}.")

    def pause_handler(signum, frame):
        nonlocal pause_simulation
        if not pause_simulation:
            pause_simulation = True
            logger.info("Simulation paused via signal.")

    def resume_handler(signum, frame):
        nonlocal pause_simulation
        if pause_simulation:
            pause_simulation = False
            logger.info("Simulation resumed via signal.")

    # Register signal handlers for pause/resume
    signal.signal(signal.SIGUSR1, pause_handler)
    signal.signal(signal.SIGUSR2, resume_handler)

    try:
        miner_instance.start()
        while datetime.now() < end_time:
            if pause_simulation:
                time.sleep(1)
                continue

            process_transactions(miner_instance, current_ledger, wallets_manager)

            if (datetime.now() - last_log_time).total_seconds() > 30:
                current_tx_count = len(wallets_manager.wallets)
                tx_rate = (current_tx_count - last_tx_count) / 30
                logger.info(f"Simulation running. Wallet count: {current_tx_count}, Transaction rate: {tx_rate:.2f} tx/s")
                # Log wallet balances summary (min, max, average)
                balances = [wallets_manager.get_balance(wid) for wid in wallets_manager.wallets]
                if balances:
                    min_balance = min(balances)
                    max_balance = max(balances)
                    avg_balance = sum(balances) / len(balances)
                    logger.info(f"Wallet balances - Min: {min_balance:.2f}, Max: {max_balance:.2f}, Avg: {avg_balance:.2f}")
                last_tx_count = current_tx_count
                last_log_time = datetime.now()

            time.sleep(config.SIMULATION_LOOP_INTERVAL)

    except KeyboardInterrupt:
        logger.info("\nSimulation interrupted by user.")
    except Exception as e:
        logger.error(f"\nAn unexpected error occurred during simulation: {e}")
    finally:
        logger.info("\nSimulation finished. Saving final ledger state...")
        if current_ledger:
            try:
                current_ledger.save_to_json(f"ledger_{config.NETWORK_NAME}.json")
                logger.info(f"Final ledger saved to ledger_{config.NETWORK_NAME}.json")
                logger.info(f"Total Triads in ledger: {current_ledger.get_total_triads()}")
            except Exception as save_e:
                logger.error(f"Error saving final ledger: {save_e}")
        else:
            logger.warning("No ledger to save.")
        logger.info("\nSaving final wallets state...")
        try:
            wallets_manager.save_wallets(config.NETWORK_NAME)
            logger.info(f"Final wallets saved to wallets_{config.NETWORK_NAME}.json")
        except Exception as save_e:
            logger.error(f"Error saving final wallets: {save_e}")

def run_simulation(network_name):
    logger.info(f"Running simulation for the {network_name} network...")
    ledger_filename = f"ledger_{network_name}.json"
    wallets_filename = f"wallets_{network_name}.json"

    from seirchain.config import config

    try:
        validate_config()
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return

    current_ledger = None

    if os.path.exists(ledger_filename):
        try:
            current_ledger = TriangularLedger.load_from_json(filename=ledger_filename)
            logger.info(f"Ledger loaded successfully from {ledger_filename}")

            if main_wallets_manager.load_wallets(network_name) is None:
                logger.warning(f"Wallets file '{wallets_filename}' not found or invalid. Initializing empty wallets within manager.")
                initialize_wallets(main_wallets_manager)
            else:
                logger.info(f"Wallets loaded successfully from {wallets_filename}")

            logger.info("Reconstructing wallet states from loaded ledger...")
            all_transactions = list(current_ledger.get_all_transactions())
            for tx in all_transactions:
                if not main_wallets_manager.wallet_exists(tx.from_addr) and tx.from_addr != "0x0":
                    main_wallets_manager.add_wallet(tx.from_addr, 0)
                if not main_wallets_manager.wallet_exists(tx.to_addr):
                    main_wallets_manager.add_wallet(tx.to_addr, 0)

                sender_id = tx.from_addr if tx.from_addr != "0x0" else None
                receiver_id = tx.to_addr

                if tx.from_addr == "0x0":
                    if receiver_id:
                        main_wallets_manager.add_funds(receiver_id, tx.amount)
                else:
                    if sender_id and receiver_id:
                        main_wallets_manager.deduct_funds(sender_id, tx.amount + tx.fee)
                        main_wallets_manager.add_funds(receiver_id, tx.amount)
            logger.info(f"Reconstructed {len(main_wallets_manager.wallets)} wallet states within the manager.")

        except Exception as e:
            logger.error(f"Error loading ledger from {ledger_filename}: {e}")
            logger.error(f"Simulation failed for {network_name} network. Exiting.")
            return

    if not current_ledger:
        logger.info("No existing ledger found. Initializing new network...")
        current_ledger = TriangularLedger(config.MAX_DEPTH)

        initialize_simulation_wallets(main_wallets_manager, config.GENESIS_MINER_ADDRESS_testnet if network_name == "testnet" else main_wallets_manager.generate_wallet_id())

    miner_address = config.GENESIS_MINER_ADDRESS_testnet if network_name == "testnet" else main_wallets_manager.generate_wallet_id()

    miner_wallet_id = main_wallets_manager.get_wallet(miner_address).address if main_wallets_manager.wallet_exists(miner_address) else None

    node_instance = Node(ledger=current_ledger, wallet_manager=main_wallets_manager)
    node_instance.start()

    miner_instance = Miner(current_ledger, node_instance, main_wallets_manager, miner_address)

    simulation_duration = timedelta(minutes=config.SIMULATION_DURATION_MINUTES)
    end_time = datetime.now() + simulation_duration

    simulation_loop(miner_instance, current_ledger, main_wallets_manager, end_time)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the SeirChain simulation.")
    parser.add_argument("network", choices=["testnet", "mainnet"], help="Specify the network to simulate (testnet or mainnet).")
    args = parser.parse_args()
    run_simulation(args.network)
