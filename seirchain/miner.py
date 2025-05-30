import time
import random
import hashlib
from seirchain.data_types.triad import Triad
from seirchain.data_types.transaction import Transaction, TransactionNode
from seirchain.config import config
from seirchain.data_types.wallets import wallets as main_wallets_manager # Import the manager

class Miner:
    def __init__(self, ledger, wallets_manager): # walets_manager is now the main_wallets_manager instance
        self.ledger = ledger
        self.wallets_manager = wallets_manager # Store the wallets manager instance
        self.transaction_pool = []
        self.mining_stats = {"hash_attempts": 0, "triads_mined_session": 0}

    def add_transaction_to_pool(self, tx_node):
        """Adds a validated transaction (as TransactionNode) to the miner's pool."""
        # In a real system, more validation would occur here (e.g., signature check)
        self.transaction_pool.append(tx_node)

    def _get_transactions_for_triad(self):
        """
        Selects transactions from the pool for inclusion in a new triad.
        Prioritizes transactions with higher fees (if applicable), or simply selects
        a limited number for simulation.
        """
        num_to_select = min(len(self.transaction_pool), config.MAX_TRANSACTIONS_PER_TRIAD)

        # For simplicity, just take the first N transactions.
        # In a real system, fees would be considered.
        selected_tx_nodes = self.transaction_pool[:num_to_select]
        self.transaction_pool = self.transaction_pool[num_to_select:] # Remove from pool

        return selected_tx_nodes

    def mine_next_triad(self, miner_address):
        """
        Attempts to mine a new triad.
        1. Selects candidate parent triads from the current ledger tips.
        2. Gathers transactions from the pool.
        3. Creates a coinbase transaction for the mining reward.
        4. Performs Proof-of-Work to find a valid nonce.
        5. Adds the valid triad to the ledger.
        """
        # 1. Get candidate parent triads from the ledger
        tip_hashes = self.ledger.get_current_tip_triad_hashes()

        candidate_parents = []
        if not tip_hashes:
            # This implies no genesis triad yet. Miner should create a genesis triad.
            print("No tips found. Attempting to mine genesis triad...")
            # Genesis triad has no parents
            parent_hashes = []
        else:
            # For simplicity, choose a random tip as the parent.
            # In a real system, more complex parent selection logic (e.g., longest chain)
            # and multiple parents would be considered for a triangular structure.
            for h in tip_hashes:
                parent_triad = self.ledger._find_triad_by_hash(h)
                if parent_triad:
                    candidate_parents.append(parent_triad)

            if not candidate_parents: # If for some reason tips didn't translate to objects
                print("Could not retrieve parent Triad objects from tips.")
                return None

            # Select a parent triad (simplified for now: random choice from valid parents)
            parent_triad = random.choice(candidate_parents)
            parent_hashes = [parent_triad.hash] # Use the actual hash attribute

            # Update depth for the new triad based on parent
            new_triad_depth = parent_triad.depth + 1

        # 2. Gathers transactions
        transactions_for_triad = self._get_transactions_for_triad()

        # 3. Create a coinbase transaction (mining reward + transaction fees)
        total_fees = sum(tx_node.transaction.fee for tx_node in transactions_for_triad)
        coinbase_amount = config.MINING_REWARD + total_fees

        # The coinbase transaction "sender" is typically 0x0 or an empty address
        coinbase_tx = Transaction(
            sender="0x0", # Special address for coinbase
            receiver=miner_address,
            amount=coinbase_amount,
            fee=0.0, # Coinbase has no fee
            timestamp=time.time(),
            signature="coinbase_tx"
        )
        # Wrap coinbase transaction in a TransactionNode for consistency
        coinbase_tx_node = TransactionNode(coinbase_tx, parent_hash=None) # Coinbase has no parent in the transaction graph
        transactions_for_triad.insert(0, coinbase_tx_node) # Add coinbase as the first transaction

        # 4. Perform Proof-of-Work
        nonce = 0
        current_hash = ""
        start_time = time.time()

        # For genesis triad, depth is 0
        if not self.ledger.genesis_triad:
            new_triad_depth = 0
        elif candidate_parents: # If we have parents, depth is max parent depth + 1
            new_triad_depth = max(p.depth for p in candidate_parents) + 1
        else: # Fallback if no parents or genesis
            new_triad_depth = 0

        # Create a prospective Triad object to calculate its hash
        # Triad ID can be a random UUID or derived from parents
        triad_id = hashlib.sha256(str(time.time()).encode() + str(random.random()).encode()).hexdigest()

        prospective_triad = Triad(
            triad_id=triad_id,
            depth=new_triad_depth,
            parent_hashes=parent_hashes,
            transactions=transactions_for_triad,
            nonce=nonce, # Initial nonce
            difficulty=config.DIFFICULTY,
            miner_address=miner_address,
            timestamp=time.time()
        )

        found_nonce = False
        for nonce_attempt in range(config.MAX_NONCE_ATTEMPTS):
            self.mining_stats["hash_attempts"] += 1
            prospective_triad.nonce = nonce_attempt
            current_hash = prospective_triad.calculate_hash()

            if current_hash.startswith('0' * config.DIFFICULTY):
                found_nonce = True
                break

        end_time = time.time()
        hash_rate = self.mining_stats["hash_attempts"] / (end_time - start_time) if (end_time - start_time) > 0 else 0
        self.mining_stats["hashrate"] = hash_rate

        if found_nonce:
            prospective_triad.hash = current_hash # Set the final hash
            # 5. Add the newly mined triad to the ledger
            if self.ledger.add_triad(prospective_triad):
                self.mining_stats["triads_mined_session"] += 1

                # Apply coinbase reward to miner's wallet
                miner_wallet_id = self.wallets_manager.get_wallet_id_by_name(miner_address)
                if miner_wallet_id:
                    self.wallets_manager.add_funds(miner_wallet_id, coinbase_amount)
                else:
                    print(f"Warning: Miner wallet not found for address {miner_address}. Reward not applied.")

                return prospective_triad
            else:
                print("Failed to add mined triad to ledger (parent not found or other issue).")
                return None
        else:
            # print(f"Mining failed after {config.MAX_NONCE_ATTEMPTS} attempts. No valid nonce found.")
            return None

    def get_mining_stats(self):
        return self.mining_stats

