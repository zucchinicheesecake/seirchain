import json
import os
import time
import hashlib

from seirchain.data_types.triad import Triad # Import the Triad class
from seirchain.config import Config # Import Config to get difficulty

class TriangularLedger:
    """
    Manages the blockchain (ledger) for the simulation.
    Implemented as a Singleton to ensure a single source of truth.
    """
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TriangularLedger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.chain = []
            self.config = Config.instance() # Get the singleton config instance
            self._initialized = True

    @classmethod
    def instance(cls):
        """Returns the singleton instance of TriangularLedger."""
        if cls._instance is None:
            cls() # This calls __init__
        return cls._instance

    def add_triad(self, triad):
        """Adds a new Triad to the ledger."""
        if triad.hash.startswith('0' * self.config.DIFFICULTY):
            self.chain.append(triad)
            return True
        return False

    def get_latest_triad(self):
        """Returns the latest Triad in the ledger."""
        return self.chain[-1] if self.chain else None

    def load_ledger(self, network, max_depth):
        """Loads the ledger from a JSON file, or initializes with Genesis Triad."""
        ledger_file = f"ledger_{network}.json"
        if os.path.exists(ledger_file):
            try:
                with open(ledger_file, 'r') as f:
                    data = json.load(f)
                    # Reconstruct Triad objects from dictionary data
                    self.chain = [Triad.from_dict(t_data) for t_data in data.get('chain', [])]
                print(f"Ledger loaded with {len(self.chain)} Triads and max depth {max_depth}.")
            except Exception as e:
                print(f"Error loading ledger: {e}. Initializing with Genesis Triad.")
                self._initialize_genesis_triad()
        else:
            print(f"No existing ledger file found at {ledger_file}. Initializing with Genesis Triad.")
            self._initialize_genesis_triad()

    def _initialize_genesis_triad(self):
        """Initializes the ledger with a Genesis Triad."""
        # Calculate a consistent hash for the genesis triad
        genesis_hash = hashlib.sha256(b"genesis_triad").hexdigest()

        genesis_triad = Triad(
            index=0,
            timestamp=time.time(),
            transactions=[],
            nonce=0,
            previous_hash="0" * 64, # A string of 64 zeros for the first block
            hash=genesis_hash, # CORRECTED: Changed 'current_hash' to 'hash'
            difficulty=self.config.DIFFICULTY,
            miner_address="GENESIS_MINE_WALLET_ADDRESS" # Placeholder for genesis miner
        )
        self.chain.append(genesis_triad)
        print("Ledger initialized with Genesis Triad.")

    def save_ledger(self, network):
        """Saves the current ledger data to a JSON file."""
        ledger_file = f"ledger_{network}.json"
        # Convert Triad objects to dictionaries for serialization
        chain_data = [triad.to_dict() for triad in self.chain]
        with open(ledger_file, 'w') as f:
            json.dump({"chain": chain_data}, f, indent=2)

    def print_ledger_status(self):
        """Prints a summary of the ledger's current state."""
        print(f"  Total Triads in Ledger: {len(self.chain)}")
        if self.chain:
            last_triad = self.get_latest_triad()
            print(f"  Last Triad Index: {last_triad.index}")
            print(f"  Last Triad Hash: {last_triad.hash[:10]}...")
            print(f"  Last Triad Transactions: {len(last_triad.transactions)}")
