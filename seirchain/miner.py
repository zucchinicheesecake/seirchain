import hashlib
import time
from tqdm import tqdm
import json
import uuid

from seirchain.config import Config
from seirchain.data_types.triad import Triad
from seirchain.data_types.wallets import Wallets
from seirchain.data_types.transaction_node import TransactionNode

class Miner:
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
            self.network = network
            self._initialized = True

    @classmethod
    def instance(cls, miner_address=None, network=None):
        if cls._instance is None:
            if miner_address is None or network is None:
                raise ValueError("Miner must be initialized with an address and network.")
            cls(miner_address, network)
        return cls._instance

    def _calculate_hash(self, triad_id, depth, parent_hashes, timestamp, transactions, nonce):
        transactions_data = [tx.to_dict() for tx in transactions]
        transaction_string = json.dumps(transactions_data, sort_keys=True)
        
        parent_hashes_string = json.dumps(sorted(parent_hashes), sort_keys=True)

        triad_string = f"{triad_id}{depth}{parent_hashes_string}{timestamp}{transaction_string}{nonce}{self.config.DIFFICULTY}{self.miner_address}"
        return hashlib.sha256(triad_string.encode('utf-8')).hexdigest()

    def mine_triad(self, triad_id, depth, parent_hashes, transactions, network_name):
        start_time = time.time()
        nonce = 0
        difficulty_prefix = '0' * self.config.DIFFICULTY

        print(f"Miner {self.miner_address[:8]}... starting to mine Triad {triad_id[:8]}... (Depth: {depth})...")

        with tqdm(total=100000, desc=f"Mining Triad {depth}-{triad_id[:4]}", unit="hash", leave=True, dynamic_ncols=True) as pbar:
            while True:
                current_hash = self._calculate_hash(triad_id, depth, parent_hashes, start_time, transactions, nonce)
                if current_hash.startswith(difficulty_prefix):
                    break
                nonce += 1
                pbar.update(1)

                if nonce % 5000 == 0:
                    pbar.total = max(pbar.total, nonce + 10000)

                if nonce > 20000000:
                    print(f"\nMax nonce attempts reached for Triad {triad_id[:8]}... Mining failed.")
                    return None

        end_time = time.time()
        mining_time = end_time - start_time
        print(f"\nMiner found nonce: {nonce}, Triad Hash: {current_hash[:10]}... (Time: {mining_time:.2f}s)")

        self.wallets.add_funds(self.miner_address, self.config.MINING_REWARD)
        print(f"Mining reward {self.config.MINING_REWARD:.2f} added to miner {self.miner_address[:8]}... wallet.")

        return Triad(
            triad_id=triad_id,
            depth=depth,
            parent_hashes=parent_hashes,
            transactions=transactions,
            nonce=nonce,
            hash=current_hash,
            difficulty=self.config.DIFFICULTY,
            miner_address=self.miner_address
        )

