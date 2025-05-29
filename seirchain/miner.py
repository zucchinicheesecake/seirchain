import hashlib
import time
from tqdm import tqdm # Import tqdm
import json

from seirchain.config import Config
from seirchain.data_types.triad import Triad
from seirchain.data_types.wallets import Wallets

class Miner:
    """
    Simulates a blockchain miner.
    Implemented as a Singleton to ensure a single instance.
    """
    _instance = None
    _initialized = False

    def __new__(cls, miner_address, network):
        if cls._instance is None:
            cls._instance = super(Miner, cls).__new__(cls)
        return cls._instance

    def __init__(self, miner_address, network):
        if not self._initialized:
            self.miner_address = miner_address
            self.config = Config.instance()
            self.wallets = Wallets.instance()
            self.network = network # Store the network name
            self._initialized = True

    @classmethod
    def instance(cls, miner_address=None, network=None):
        """
        Returns the singleton instance of Miner.
        Requires miner_address and network for initial creation.
        """
        if cls._instance is None:
            if miner_address is None or network is None:
                raise ValueError("Miner must be initialized with an address and network.")
            cls(miner_address, network) # This calls __init__
        return cls._instance

    def _calculate_hash(self, index, previous_hash, timestamp, transactions, nonce):
        """Calculates the SHA256 hash for a Triad."""
        # Ensure transactions are serialized consistently
        transaction_string = json.dumps(transactions, sort_keys=True)
        triad_string = f"{index}{previous_hash}{timestamp}{transaction_string}{nonce}{self.config.DIFFICULTY}"
        return hashlib.sha256(triad_string.encode('utf-8')).hexdigest()

    def mine_triad(self, index, previous_hash, transactions, network_name):
        """
        Mines a new Triad by finding a nonce that satisfies the difficulty.
        The progress bar is added here.
        """
        start_time = time.time()
        nonce = 0
        difficulty_prefix = '0' * self.config.DIFFICULTY

        print(f"Miner {self.miner_address[:8]}... starting to mine Triad {index}...")

        # Adjusted total to 100,000 for a more realistic average for difficulty 4
        with tqdm(total=100000, desc=f"Mining Triad {index}", unit="hash", leave=True, dynamic_ncols=True) as pbar:
            while True:
                current_hash = self._calculate_hash(index, previous_hash, start_time, transactions, nonce)
                if current_hash.startswith(difficulty_prefix):
                    # Found the nonce, break the loop
                    break
                nonce += 1
                pbar.update(1) # Increment the progress bar

                # To prevent infinite loops in low-difficulty scenarios or if a valid nonce
                # is very hard to find with fixed total, limit checks for demo.
                # In real mining, this loop would theoretically be infinite.
                if nonce > 10000000: # Max attempts to find nonce for this demo
                    print(f"\nMax nonce attempts reached for Triad {index}. Mining failed.")
                    return None

        end_time = time.time()
        mining_time = end_time - start_time
        print(f"\nMiner found nonce: {nonce}, Triad Hash: {current_hash[:10]}... (Time: {mining_time:.2f}s)")

        # Reward the miner
        self.wallets.add_funds(self.miner_address, self.config.MINING_REWARD)
        print(f"Mining reward {self.config.MINING_REWARD:.2f} added to miner {self.miner_address[:8]}... wallet.")

        # Create and return the new Triad
        return Triad(
            index=index,
            timestamp=start_time, # Use block creation timestamp
            transactions=transactions, # Transactions included in this block
            nonce=nonce,
            previous_hash=previous_hash,
            hash=current_hash,
            difficulty=self.config.DIFFICULTY,
            miner_address=self.miner_address
        )
