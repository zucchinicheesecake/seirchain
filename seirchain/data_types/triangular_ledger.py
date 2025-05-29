# seirchain/data_types/triangular_ledger.py
import json
import os
import time
import hashlib
import uuid

from seirchain.data_types.triad import Triad
from seirchain.data_types.transaction_node import TransactionNode
from seirchain.config import Config

class TriangularLedger:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TriangularLedger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.triads = {}
            self.config = Config.instance()
            self._initialized = True

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls()
        return cls._instance

    def add_triad(self, new_triad):
        if not new_triad.hash.startswith('0' * self.config.DIFFICULTY):
            print(f"Failed to add Triad {new_triad.triad_id[:8]}...: Hash does not meet difficulty.")
            return False

        if new_triad.hash in self.triads:
            print(f"Failed to add Triad {new_triad.triad_id[:8]}...: Triad with this hash already exists.")
            return False

        for parent_hash in new_triad.parent_hashes:
            if parent_hash not in self.triads:
                print(f"Failed to add Triad {new_triad.triad_id[:8]}...: Parent hash {parent_hash[:8]}... not found in ledger.")
                return False
            parent_triad = self.triads[parent_hash]
            if parent_triad.is_full():
                print(f"Failed to add Triad {new_triad.triad_id[:8]}...: Parent Triad {parent_hash[:8]}... is already full (3 children).")
                return False
            parent_triad.add_child_hash(new_triad.hash)

        self.triads[new_triad.hash] = new_triad
        print(f"Successfully added Triad {new_triad.triad_id[:8]}... (Depth: {new_triad.depth}) to ledger.")
        return True

    def get_triad(self, triad_hash):
        return self.triads.get(triad_hash)

    def get_candidate_parents(self):
        candidates = []
        for triad_hash, triad in self.triads.items():
            if not triad.is_full() and triad.depth < self.config.MAX_DEPTH:
                candidates.append(triad)
        
        candidates.sort(key=lambda x: (x.depth, len(x.child_hashes)))
        return candidates

    def get_max_current_depth(self):
        if not self.triads:
            return 0
        return max(triad.depth for triad in self.triads.values())

    def load_ledger(self, network, max_depth):
        ledger_file = f"ledger_{network}.json"
        if os.path.exists(ledger_file):
            try:
                with open(ledger_file, 'r') as f:
                    data = json.load(f)
                    self.triads = {
                        triad_hash: Triad.from_dict(t_data)
                        for triad_hash, t_data in data.get('triads', {}).items()
                    }
                print(f"Fractal ledger loaded: {len(self.triads)} Triads across {self.get_max_current_depth()} depths.")
                if not self.triads:
                    self._initialize_genesis_triad()
            except Exception as e:
                print(f"Error loading ledger: {e}. Initializing with Genesis Triad.")
                self._initialize_genesis_triad()
        else:
            print(f"No existing ledger file found at {ledger_file}. Initializing with Genesis Triad.")
            self._initialize_genesis_triad()

    def _initialize_genesis_triad(self):
        if not self.triads:
            genesis_triad_id = str(uuid.uuid4())
            genesis_parent_hashes = []
            genesis_transactions = []

            temp_genesis_triad = Triad(
                triad_id=genesis_triad_id,
                depth=0,
                parent_hashes=genesis_parent_hashes,
                transactions=genesis_transactions,
                nonce=0,
                hash="temp_hash",
                difficulty=self.config.DIFFICULTY,
                miner_address="GENESIS_MINE_WALLET_ADDRESS"
            )
            genesis_hash = temp_genesis_triad.calculate_hash()

            genesis_triad = Triad(
                triad_id=genesis_triad_id,
                depth=0,
                parent_hashes=genesis_parent_hashes,
                transactions=genesis_transactions,
                nonce=0,
                hash=genesis_hash,
                difficulty=self.config.DIFFICULTY,
                miner_address="GENESIS_MINE_WALLET_ADDRESS"
            )
            self.triads[genesis_triad.hash] = genesis_triad
            print("Ledger initialized with Genesis Triad.")
        else:
            print("Genesis Triad already exists.")

    def save_ledger(self, network):
        ledger_file = f"ledger_{network}.json"
        triads_data = {hash_key: triad.to_dict() for hash_key, triad in self.triads.items()}
        with open(ledger_file, 'w') as f:
            json.dump({"triads": triads_data}, f, indent=2)

    def print_ledger_status(self):
        print(f"  Total Triads in Ledger: {len(self.triads)}")
        print(f"  Current Max Depth: {self.get_max_current_depth()}")
        if self.triads:
            depth_counts = {}
            for triad in self.triads.values():
                depth_counts[triad.depth] = depth_counts.get(triad.depth, 0) + 1
            print("  Triads per Depth Level:")
            for depth in sorted(depth_counts.keys()):
                print(f"    Depth {depth}: {depth_counts[depth]} Triads")

