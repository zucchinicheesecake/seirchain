import threading
import time
import hashlib
import os
import logging
from seirchain.data_types.base import Triad, Triangle
from seirchain.data_types.transaction import Transaction
from seirchain.config import config

logger = logging.getLogger(__name__)

class Miner:
    """
    Manages mining operations with thread safety, fractal PoW, and transaction pool handling.
    """
    def __init__(self, ledger, node, wallet_manager, miner_address, num_threads=1):
        self.ledger = ledger
        self.node = node
        self.wallet_manager = wallet_manager
        self.miner_address = miner_address
        self.mining = False
        self.threads = []
        self.mining_lock = threading.Lock()
        self.num_threads = num_threads
        self.transaction_pool_lock = threading.Lock()

    def start(self):
        """
        Start mining with multiple threads.
        """
        with self.mining_lock:
            if self.mining:
                logger.warning("Mining already started")
                return
            self.mining = True
        for i in range(self.num_threads):
            thread = threading.Thread(
                target=self.mine,
                name=f"Miner-Thread-{i+1}",
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
        logger.info(f"Starting fractal mining with {self.num_threads} threads")

    def stop(self):
        """
        Stop all mining operations gracefully.
        """
        with self.mining_lock:
            self.mining = False
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        self.threads = []

    def mine(self):
        """
        Mine new triads using fractal proof-of-work.
        """
        thread_name = threading.current_thread().name
        logger.info(f"{thread_name}: Starting fractal mining")

        while True:
            with self.mining_lock:
                if not self.mining:
                    logger.info(f"{thread_name}: Mining stopped")
                    break
            try:
                # Get current transaction pool (thread-safe)
                with self.ledger.transaction_pool_lock:
                    transactions = self.ledger.transaction_pool[:10]

                # Create new triad
                parents = self.get_parent_triads()
                triad = Triad(
                    triad_id="",
                    depth=parents[0].depth + 1 if parents else 0,
                    hash_value="",
                    parent_hashes=[p.triad_id for p in parents]
                )

                # Create triad node with default coordinates
                triad_node = Triangle(triad, coordinates=(0, 0))
                for tx in transactions:
                    triad_node.add_transaction(tx)

                # Fractal PoW mining
                nonce = 0
                start_time = time.time()
                solution_found = False

                while True:
                    with self.mining_lock:
                        if not self.mining:
                            logger.info(f"{thread_name}: Mining stopped during PoW")
                            return

                    triad_node.triad.hash_value = self.calculate_fractal_hash(triad_node, nonce)
                    triad_node.triad.hash = triad_node.triad.hash_value  # Ensure 'hash' attribute is set

                    # Check PoW solution using dynamic difficulty
                    target_prefix = "0" * config.DIFFICULTY
                    if triad_node.triad.hash_value.startswith(target_prefix):
                        solution_found = True
                        break

                    nonce += 1

                    # Yield CPU every 1000 iterations
                    if nonce % 1000 == 0:
                        time.sleep(0.001)

                    if nonce > config.MAX_NONCE_ATTEMPTS:
                        logger.info(f"{thread_name}: Max nonce attempts reached, restarting mining cycle")
                        break

                if not solution_found:
                    continue

                # Set triad ID
                triad_node.triad.triad_id = triad_node.triad.hash_value

                # Add to ledger
                with self.ledger.transaction_pool_lock:
                    self.ledger.add_triad(triad_node.triad)
                    self.ledger.transaction_pool = self.ledger.transaction_pool[len(transactions):]

                # Add mining reward
                if self.wallet_manager:
                    reward_tx = self.create_reward_transaction()
                    self.wallet_manager.update_balances(reward_tx)

                # Broadcast new triad
                if self.node.running:
                    self.node.broadcast(triad_node.triad)

                # Log success with token name and symbol
                mining_time = time.time() - start_time
                logger.info(f"{thread_name}: Mined triad {triad_node.triad.triad_id[:8]} "
                      f"at depth {triad_node.triad.depth} in {mining_time:.2f}s, "
                      f"reward: {config.MINING_REWARD} {config.TOKEN_SYMBOL} ({config.TOKEN_NAME})")

                # Brief pause between mining cycles
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"{thread_name}: Mining error - {str(e)}", exc_info=True)
                time.sleep(1)

    def get_parent_triads(self):
        """
        Select parent triads for the new triad.
        """
        if not hasattr(self.ledger, '_triad_map'):
            return []
        tip_hashes = self.ledger.get_current_tip_triad_hashes()
        if not tip_hashes:
            return []
        # Retrieve triad objects from _triad_map using tip hashes
        parents = [self.ledger._triad_map[tip_hash] for tip_hash in tip_hashes if tip_hash in self.ledger._triad_map]
        return parents

    def calculate_fractal_hash(self, triad_node, nonce):
        """
        Calculate fractal hash for triad.
        """
        tx_hashes = ""
        for tx in triad_node.transactions:
            if hasattr(tx, 'tx_hash'):
                tx_hashes += tx.tx_hash
            elif hasattr(tx, 'transaction') and hasattr(tx.transaction, 'tx_hash'):
                tx_hashes += tx.transaction.tx_hash
            else:
                import logging
                logging.getLogger(__name__).warning(f"Transaction missing tx_hash attribute: {tx}")
        data = f"{triad_node.triad.depth}-{nonce}-{tx_hashes}"

        # Double SHA-256
        first_hash = hashlib.sha256(data.encode()).hexdigest()
        return hashlib.sha256(first_hash.encode()).hexdigest()

    def create_reward_transaction(self):
        """
        Create mining reward transaction.
        """
        # Create a Transaction object with attributes matching wallet_manager expectations
        tx_data = {
            'from_addr': "0"*64,
            'to_addr': self.miner_address,
            'amount': config.MINING_REWARD,
            'fee': 0.0,
            'timestamp': time.time(),
            'signature': None
        }
        # Create Transaction instance with property accessors for from_addr etc.
        reward_tx = Transaction(
            transaction_data=tx_data,
            tx_hash=hashlib.sha256(os.urandom(32)).hexdigest(),
            timestamp=time.time()
        )
        return reward_tx

    def add_transaction_to_pool(self, transaction):
        """
        Add a transaction to the ledger's transaction pool safely.
        """
        with self.transaction_pool_lock:
            self.ledger.transaction_pool.append(transaction)
