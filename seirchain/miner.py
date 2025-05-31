import threading
import time
import hashlib
import os
from seirchain.data_types import Triad, Transaction, Triangle

class Miner:
    def __init__(self, ledger, node, wallet_manager, miner_address, num_threads=1):
        self.ledger = ledger
        self.node = node
        self.wallet_manager = wallet_manager
        self.miner_address = miner_address
        self.mining = False
        self.threads = []
        self.mining_lock = threading.Lock()
        self.num_threads = num_threads

    def start(self):
        """Start mining with multiple threads"""
        self.mining = True
        for i in range(self.num_threads):
            thread = threading.Thread(
                target=self.mine,
                name=f"Miner-Thread-{i+1}",
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
        print(f"Starting fractal mining with {self.num_threads} threads")

    def stop(self):
        """Stop all mining operations"""
        self.mining = False
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        self.threads = []

    def mine(self):
        """Mine new triads using fractal PoW"""
        thread_name = threading.current_thread().name
        print(f"{thread_name}: Starting fractal mining")

        while self.mining:
            try:
                # Get current transaction pool (thread-safe)
                with self.mining_lock:
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

                while self.mining and not solution_found:
                    triad_node.triad.hash_value = self.calculate_fractal_hash(triad_node, nonce)

                    # Check PoW solution
                    if triad_node.triad.hash_value.startswith("00000"):
                        solution_found = True
                        break

                    nonce += 1

                    # Yield CPU every 1000 iterations
                    if nonce % 1000 == 0:
                        time.sleep(0.001)

                # If mining was stopped
                if not self.mining:
                    print(f"{thread_name}: Mining stopped")
                    return

                # Set triad ID
                triad_node.triad.triad_id = triad_node.triad.hash_value

                # Add to ledger
                with self.mining_lock:
                    self.ledger.add_triad(triad_node.triad)
                    self.ledger.transaction_pool = self.ledger.transaction_pool[len(transactions):]

                # Add mining reward
                if self.wallet_manager:
                    reward_tx = self.create_reward_transaction()
                    self.wallet_manager.update_balances(reward_tx)

                # Broadcast new triad
                if self.node.running:
                    self.node.broadcast(triad_node.triad)

                # Log success
                mining_time = time.time() - start_time
                print(f"{thread_name}: Mined triad {triad_node.triad.triad_id[:8]} "
                      f"at depth {triad_node.triad.depth} in {mining_time:.2f}s")

                # Brief pause between mining cycles
                time.sleep(0.5)

            except Exception as e:
                print(f"{thread_name}: Mining error - {str(e)}")
                import traceback
                traceback.print_exc()
                time.sleep(1)

    def get_parent_triads(self):
        """Select parent triads for the new triad"""
        if not self.ledger.triads:
            return []
        return [self.ledger.triads[-1]]

    def calculate_fractal_hash(self, triad_node, nonce):
        """Calculate fractal hash for triad"""
        tx_hashes = "".join(tx.tx_hash for tx in triad_node.get_transactions())
        data = f"{triad_node.triad.depth}-{nonce}-{tx_hashes}"

        # Double SHA-256
        first_hash = hashlib.sha256(data.encode()).hexdigest()
        return hashlib.sha256(first_hash.encode()).hexdigest()

    def create_reward_transaction(self):
        """Create mining reward transaction"""
        return Transaction(
            transaction_data={
                'from_addr': "0"*40,
                'to_addr': self.miner_address,
                'amount': 50.0,
                'fee': 0.0
            },
            tx_hash=hashlib.sha256(os.urandom(32)).hexdigest(),
            timestamp=time.time()
        )
