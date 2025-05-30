import time
import random
from seirchain.config import config as global_config
from seirchain.data_types.triangular_ledger import TriangularLedger
from seirchain.data_types.triad import Triad
from seirchain.data_types.wallets import wallets as global_wallets
from seirchain.data_types.transaction_node import TransactionNode 

class Miner:
    def __init__(self, ledger_instance, wallets_instance):
        self.config = global_config
        self.ledger = ledger_instance # Miner works on a shared ledger instance
        self.wallets = wallets_instance # Miner works on a shared wallets instance
        self.transaction_pool = [] # Simple in-memory transaction pool for demonstration
        self.mining_stats = {
            "hashrate": "0 H/s",
            "last_nonce": 0,
            "mining_target": '0' * self.config.DIFFICULTY,
            "triads_mined_session": 0
        }

    def add_transaction_to_pool(self, tx):
        """Adds a new transaction to the miner's pending pool."""
        # In a real system, comprehensive validation would occur here.
        self.transaction_pool.append(tx)

    def select_transactions(self, max_tx_count=None):
        """Selects transactions from the pool for inclusion in a new triad."""
        if max_tx_count is None:
            max_tx_count = self.config.MAX_TRANSACTIONS_PER_TRIAD
        
        selected_txs = []
        while self.transaction_pool and len(selected_txs) < max_tx_count:
            selected_txs.append(self.transaction_pool.pop(0)) # FIFO
        return selected_txs

    def mine_next_triad(self, miner_address):
        """
        Attempts to mine a single new triad and add it to the ledger.
        Returns the newly mined triad if successful, None otherwise.
        """
        candidate_parents = self.ledger.get_candidate_parents()
        
        if not candidate_parents:
            # If no parents are available, it implies the genesis triad needs to be mined first.
            # The orchestrator (run_node_with_visualizer.py) handles genesis initialization.
            return None

        # Select a parent triad (simplified for now: random choice)
        parent_triad = random.choice(candidate_parents)
        parent_hashes = [parent_triad.hash] # For simple 1-parent connection

        selected_transactions = self.select_transactions()
        
        # Add a coinbase transaction (mining reward) if there are no other transactions
        # or as a standard part of block/triad creation
        if not selected_transactions: # Always ensure there's at least a coinbase transaction
            coinbase_tx = TransactionNode(
                sender_address="0x0", # Special address for coinbase
                recipient_address=miner_address,
                amount=self.config.MINING_REWARD,
                fee=0.0,
                timestamp=time.time(),
                tx_id=f"coinbase_{time.time()}_{random.randint(0,100000)}" 
            )
            selected_transactions.append(coinbase_tx)


        # Construct the prospective triad
        new_triad_id = f"triad_{self.ledger.get_max_current_depth() + 1}_{time.time()}_{random.randint(0,100000)}"
        new_depth = parent_triad.depth + 1
        
        prospective_triad = Triad(
            triad_id=new_triad_id,
            depth=new_depth,
            parent_hashes=parent_hashes,
            transactions=selected_transactions,
            nonce=0,
            difficulty=self.config.DIFFICULTY,
            miner_address=miner_address
        )

        start_time = time.time()
        found_nonce = False
        hash_attempts = 0

        # Proof-of-Work mining loop
        for nonce_attempt in range(self.config.MAX_NONCE_ATTEMPTS):
            prospective_triad.nonce = nonce_attempt
            current_hash = prospective_triad.calculate_hash()
            hash_attempts += 1

            if current_hash.startswith('0' * self.config.DIFFICULTY):
                prospective_triad.hash = current_hash # Set the final hash
                found_nonce = True
                break
        
        end_time = time.time()
        time_taken = end_time - start_time
        hashrate = f"{hash_attempts / time_taken:.2f} H/s" if time_taken > 0 else "N/A"

        # Update internal mining statistics
        self.mining_stats["hashrate"] = hashrate
        self.mining_stats["last_nonce"] = prospective_triad.nonce
        self.mining_stats["mining_target"] = '0' * self.config.DIFFICULTY

        if found_nonce:
            # Attempt to add the newly mined triad to the ledger
            if self.ledger.add_triad(prospective_triad):
                self.mining_stats["triads_mined_session"] += 1
                return prospective_triad
            else:
                # Triad was valid but ledger logic (e.g., parent became full) refused it
                return None
        else:
            # Failed to find a nonce within allowed attempts
            return None

    def get_mining_stats(self):
        """Returns the current mining statistics."""
        return self.mining_stats

