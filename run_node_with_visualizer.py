import time
import os
import sys
import random # Ensure random is imported for dummy transactions
from multiprocessing import Process, Manager 

# Import core components
from seirchain.config import config as global_config
from seirchain.data_types.wallets import wallets as global_wallets
from seirchain.data_types.triangular_ledger import TriangularLedger
from seirchain.miner import Miner
from seirchain.data_types.transaction_node import TransactionNode 
from seirchain.visualizer.sierpinski_visualizer import SierpinskiVisualizer

def miner_process_fn(shared_ledger_data, shared_wallets_data, shared_miner_stats_data):
    """
    Function to be run in a separate process for mining.
    It operates on shared data structures.
    """
    # Re-instantiate local instances of config and wallets within this new process.
    # This is important because global objects loaded before forking might not be
    # truly independent or writable by child processes.
    # The actual data (dictionaries) will be the shared ones.
    from seirchain.config import config as local_config 
    from seirchain.data_types.wallets import wallets as local_wallets
    
    # Initialize local Ledger and Wallets instances to interact with shared data.
    # The internal .triads and .wallets dictionaries of these instances are set
    # to the shared Manager.dict objects.
    ledger = TriangularLedger()
    ledger.triads = shared_ledger_data # Link ledger's internal data to the shared dict
    ledger.max_current_depth = shared_ledger_data.get('__max_current_depth', -1) # Sync initial depth

    wallets = local_wallets 
    wallets.wallets = shared_wallets_data # Link wallets' internal data to the shared dict

    miner = Miner(ledger, wallets)

    # Initialize genesis if the ledger is effectively empty (first run).
    # This must be done by the miner process as it's the one that "mints" new triads.
    if not ledger.get_total_triads():
        print("Miner Process: Ledger is empty, attempting to initialize genesis triad...")
        miner_wallet_id = wallets.get_wallet_id_by_name("GENESIS_MINE_WALLET")
        if not miner_wallet_id:
            # This case should ideally not happen if main process ensures the wallet.
            # But as a fallback:
            miner_wallet_id = wallets.add_wallet("GENESIS_MINE_WALLET", 0)
        
        if miner.ledger.initialize_genesis_triad(miner_wallet_id):
            print("Miner Process: Genesis triad successfully initialized.")
        else:
            print("Miner Process: Failed to initialize genesis triad. Exiting miner process.")
            return

    print("Miner Process: Starting continuous mining loop...")
    last_save_time = time.time()
    SAVE_INTERVAL = 30 # Save every 30 seconds to disk

    while True:
        try:
            current_miner_wallet_id = wallets.get_wallet_id_by_name("GENESIS_MINE_WALLET")
            if not current_miner_wallet_id:
                # This would be an error in a long-running system, but for now, re-create if missing
                current_miner_wallet_id = wallets.add_wallet("GENESIS_MINE_WALLET", 0)
                if not current_miner_wallet_id:
                    print("Miner Process: FATAL - Could not acquire miner wallet ID. Exiting.")
                    break

            # Add dummy transactions to the pool for testing the transaction processing.
            if random.random() < local_config.DUMMY_TRANSACTION_CHANCE: 
                # Pick two distinct wallet IDs for sender and receiver
                all_wallets = list(wallets.wallets.keys())
                if len(all_wallets) >= 2:
                    sender_id, recipient_id = random.sample(all_wallets, 2)
                    
                    # Ensure sender has sufficient simulated funds (not real, just for demo)
                    if wallets.get_balance(sender_id) < 50.0: 
                        wallets.add_funds(sender_id, 100.0) # Top up for tx simulation

                    # Create a dummy transaction
                    dummy_tx = TransactionNode(
                        sender_address=sender_id,
                        recipient_address=recipient_id,
                        amount=random.uniform(1.0, 20.0),
                        fee=local_config.TRANSACTION_FEE,
                        timestamp=time.time(),
                        tx_id=f"sim_tx_{time.time()}_{random.randint(0,100000)}"
                    )
                    miner.add_transaction_to_pool(dummy_tx)
                    # print(f"Miner Process: Added dummy transaction to pool from {sender_id[:6]} to {recipient_id[:6]}")


            # Attempt to mine the next triad
            new_triad = miner.mine_next_triad(current_miner_wallet_id)
            if new_triad:
                # The ledger.add_triad method already updates the shared_ledger_data
                # (via the ledger.triads reference) and shared_wallets_data
                # (via wallets.wallets reference, as global_wallets is passed to Ledger).
                pass 

            # Update shared mining statistics for the visualizer
            shared_miner_stats_data.update(miner.get_mining_stats())

            # Periodically save ledger and wallets state to disk
            if time.time() - last_save_time > SAVE_INTERVAL:
                ledger.save_ledger("mainnet")
                wallets.save_wallets("mainnet")
                print("Miner Process: Ledger and Wallets state saved.")
                last_save_time = time.time()

            time.sleep(0.05) # Small delay to prevent 100% CPU usage

        except KeyboardInterrupt:
            print("\nMiner Process: Stopping gracefully...")
            break
        except Exception as e:
            print(f"Miner Process Error: {e}")
            time.sleep(2) # Sleep on error to prevent rapid crash loop

def visualizer_process_fn(shared_ledger_data, shared_miner_stats_data):
    """
    Function to be run in a separate process for visualization.
    It reads from shared data structures.
    """
    # Define proxy classes to provide a consistent interface for the visualizer,
    # even though the underlying data is a multiprocessing.Manager.dict.
    class SharedLedgerProxy:
        def __init__(self, shared_data):
            self._shared_data = shared_data
        
        @property
        def triads(self):
            # The visualizer will iterate over this shared dictionary directly
            return self._shared_data 
        
        @property
        def max_current_depth(self):
            return self._shared_data.get('__max_current_depth', -1)
        
        def get_total_triads(self):
            # Calculate total triads, excluding the internal __max_current_depth key
            return len([k for k in self._shared_data.keys() if not k.startswith('__')]) 

    class SharedMinerStatsProxy:
        def __init__(self, shared_data):
            self._shared_data = shared_data
        
        def get_mining_stats(self):
            # Return the shared dictionary of mining stats
            return self._shared_data


    visualizer = SierpinskiVisualizer(max_display_depth=global_config.MAX_DEPTH) 
    
    # Pass the proxy objects to the visualizer's animate method
    visualizer.animate(
        SharedLedgerProxy(shared_ledger_data), 
        SharedMinerStatsProxy(shared_miner_stats_data)
    )

if __name__ == "__main__":
    print("Starting Seirchain Node with Visualizer...")
    
    # The main process initializes the core components and sets up shared data.
    
    # Load initial wallets state (or create if none exist).
    # This happens in the main process, and then its *data* is shared.
    global_wallets.load_wallets("mainnet")
    
    # Ensure the primary mining wallet exists.
    if not global_wallets.get_wallet_id_by_name("GENESIS_MINE_WALLET"):
        print("Main Process: 'GENESIS_MINE_WALLET' not found, creating it...")
        global_wallets.add_wallet("GENESIS_MINE_WALLET", 0)
        # Add a couple of generic wallets for transaction simulation if needed, without specific names.
        global_wallets.add_wallet("SimWallet_A", 1000.0) 
        global_wallets.add_wallet("SimWallet_B", 500.0)
        global_wallets.save_wallets("mainnet")
        print("Main Process: Initial wallets created/ensured.")
    
    # Load initial ledger state.
    ledger_instance = TriangularLedger()
    ledger_instance.load_ledger("mainnet")
    
    if not ledger_instance.get_total_triads():
        print("Main Process: Ledger is empty. Miner process will initialize genesis triad upon startup.")

    # Use multiprocessing.Manager to create truly shared data structures.
    # Manager.dict allows child processes to read/write to the same underlying dictionary.
    with Manager() as manager:
        # 1. Shared ledger data (stores triad dictionaries)
        shared_ledger_data = manager.dict()
        # Copy existing ledger data (if loaded) into the shared dictionary.
        for triad_hash, triad_dict in ledger_instance.triads.items():
            if not triad_hash.startswith('__'): # Exclude internal keys when copying
                shared_ledger_data[triad_hash] = triad_dict
        # Ensure the __max_current_depth key is present and synced
        shared_ledger_data['__max_current_depth'] = ledger_instance.max_current_depth
        
        # 2. Shared wallets data (stores wallet dictionaries)
        shared_wallets_data = manager.dict(global_wallets.wallets) 
        
        # 3. Shared mining statistics data
        shared_miner_stats_data = manager.dict() 
        # Initialize with default stats so visualizer doesn't error on first read
        shared_miner_stats_data.update({
            "hashrate": "0 H/s",
            "last_nonce": 0,
            "mining_target": '0' * global_config.DIFFICULTY,
            "triads_mined_session": 0
        })

        # Create and start the miner process
        miner_proc = Process(target=miner_process_fn, args=(shared_ledger_data, shared_wallets_data, shared_miner_stats_data))
        miner_proc.start()

        # Create and start the visualizer process
        visualizer_proc = Process(target=visualizer_process_fn, args=(shared_ledger_data, shared_miner_stats_data))
        visualizer_proc.start()

        print("\nMain Process: Miner and Visualizer processes started. Press Ctrl+C to stop.")

        try:
            # Keep the main process alive, waiting for child processes to finish (or for Ctrl+C).
            miner_proc.join()
            visualizer_proc.join()
        except KeyboardInterrupt:
            print("\nMain Process: Received Ctrl+C. Initiating graceful shutdown of child processes...")
            # Terminate child processes on KeyboardInterrupt
            miner_proc.terminate()
            visualizer_proc.terminate()
            miner_proc.join() # Wait for termination
            visualizer_proc.join()
            print("Main Process: Child processes terminated.")

        # Save final state when stopping, pulling data from the shared Manager.dicts
        print("Main Process: Saving final ledger and wallets state...")
        ledger_instance.triads = dict(shared_ledger_data) # Convert Manager.dict back to regular dict
        ledger_instance.max_current_depth = ledger_instance.triads.get('__max_current_depth', -1)
        global_wallets.wallets = dict(shared_wallets_data) # Convert Manager.dict back to regular dict
        
        ledger_instance.save_ledger("mainnet")
        global_wallets.save_wallets("mainnet")
        print("Main Process: Final state saved. Exiting.")

