import threading
import time
import hashlib
import os
import logging
from typing import List, Optional
from seirchain.core.data_types.base import Triad, Triangle
from seirchain.core.data_types.transaction import Transaction
from seirchain.config import config

logger = logging.getLogger(__name__)

class Miner:
    """
    Manages mining operations with thread safety, fractal PoW, and transaction pool handling.
    """

    def __init__(self, ledger: object, node: object, wallet_manager: object, miner_address: str, num_threads: int = 1) -> None:
        self.ledger = ledger
        self.node = node
        self.wallet_manager = wallet_manager
        self.miner_address = miner_address
        self.shutdown_event = threading.Event()
        self.threads: List[threading.Thread] = []
        self.mining_lock = threading.Lock()
        self.num_threads = num_threads
        self.transaction_pool_lock = threading.Lock()

        # Metrics
        self.hashes_computed = 0
        self.successful_mines = 0
        self.total_mining_time = 0.0

        # Configuration validation
        if not isinstance(self.num_threads, int) or self.num_threads <= 0:
            raise ValueError("num_threads must be a positive integer")
        if not hasattr(config, 'DIFFICULTY') or not isinstance(config.DIFFICULTY, int) or config.DIFFICULTY < 1:
            raise ValueError("config.DIFFICULTY must be an integer >= 1")
        if not hasattr(config, 'MAX_NONCE_ATTEMPTS') or not isinstance(config.MAX_NONCE_ATTEMPTS, int) or config.MAX_NONCE_ATTEMPTS < 1:
            raise ValueError("config.MAX_NONCE_ATTEMPTS must be an integer >= 1")

    def start(self) -> None:
        """
        Start mining with multiple threads.
        """
        with self.mining_lock:
            if self.threads and any(thread.is_alive() for thread in self.threads):
                logger.warning("Mining already started")
                return
            self.shutdown_event.clear()
        for i in range(self.num_threads):
            thread = threading.Thread(
                target=self.mine,
                name=f"Miner-Thread-{i+1}",
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
        logger.info(f"Starting fractal mining with {self.num_threads} threads")

    def stop(self) -> None:
        """
        Stop all mining operations gracefully.
        """
        self.shutdown_event.set()
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        self.threads = []

    def mine(self) -> None:
        """
        Mine new triads using fractal proof-of-work.
        """
        thread_name = threading.current_thread().name
        logger.info(f"{thread_name}: Starting fractal mining")

        while not self.shutdown_event.is_set():
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
                import random
                nonce = random.randint(0, 1000000)  # Randomized nonce start
                start_time = time.time()
                solution_found = False

                while not self.shutdown_event.is_set():
                    triad_node.triad.hash_value = self.calculate_fractal_hash(triad_node, nonce)
                    triad_node.triad.hash = triad_node.triad.hash_value  # Ensure 'hash' attribute is set

                    # Increment metrics
                    self.hashes_computed += 1

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
                    # Removed removal of transactions from transaction_pool to keep immutability
                    # self.ledger.transaction_pool = self.ledger.transaction_pool[len(transactions):]
                    # Immediately save ledger after adding triad
                    try:
                        self.ledger.save_ledger(config.NETWORK_NAME)
                    except Exception as e:
                        logger.error(f"Error saving ledger after mining triad: {e}")

                # Add mining reward
                if self.wallet_manager:
                    reward_tx = self.create_reward_transaction()
                    self.wallet_manager.update_balances(reward_tx)

                # Broadcast new triad
                if self.node.running:
                    self.node.broadcast(triad_node.triad)

                # Log success with token name and symbol
                mining_time = time.time() - start_time
                self.successful_mines += 1
                self.total_mining_time += mining_time
                logger.info(f"{thread_name}: Mined triad {triad_node.triad.triad_id[:8]} "
                      f"at depth {triad_node.triad.depth} in {mining_time:.2f}s, "
                      f"reward: {config.MINING_REWARD} {config.TOKEN_SYMBOL} ({config.TOKEN_NAME})")

                # Brief pause between mining cycles
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"{thread_name}: Mining error - {str(e)}", exc_info=True)
                time.sleep(1)

        logger.info(f"{thread_name}: Mining stopped")

    def get_parent_triads(self) -> List[Triad]:
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

    def calculate_fractal_hash(self, triad_node: Triangle, nonce: int) -> str:
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
                logging.getLogger(__name__).warning(f"Transaction missing tx_hash attribute: {tx}")
        data = f"{triad_node.triad.depth}-{nonce}-{tx_hashes}"

        # Double SHA-256
        first_hash = hashlib.sha256(data.encode()).hexdigest()
        return hashlib.sha256(first_hash.encode()).hexdigest()

    def create_reward_transaction(self) -> Transaction:
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

    def add_transaction_to_pool(self, transaction: Transaction) -> None:
        """
        Add a transaction to the ledger's transaction pool safely.
        """
        with self.transaction_pool_lock:
            # Validate transaction before adding
            if not self._validate_transaction(transaction):
                logger.warning(f"Invalid transaction rejected: {transaction}")
                return
            # Deduplicate transactions
            if transaction in self.ledger.transaction_pool:
                logger.info(f"Duplicate transaction ignored: {transaction}")
                return
            self.ledger.transaction_pool.append(transaction)

    def _validate_transaction(self, transaction: Transaction) -> bool:
        """
        Validate transaction structure and fields.
        """
        required_attrs = ['from_addr', 'to_addr', 'amount', 'fee', 'timestamp']
        for attr in required_attrs:
            if not hasattr(transaction, attr) and not (hasattr(transaction, 'transaction_data') and attr in transaction.transaction_data):
                logger.warning(f"Transaction missing required attribute: {attr}")
                return False
        # Additional validation can be added here (e.g., amount > 0)
        try:
            amount = getattr(transaction, 'amount', None) or transaction.transaction_data.get('amount', None)
            if amount is None or amount <= 0:
                logger.warning("Transaction amount must be positive")
                return False
        except Exception:
            return False
        return True
