import json
import os
import hashlib
import time
from collections import deque
from seirchain.data_types.triad import Triad, TriadEncoder
from seirchain.data_types.transaction import TransactionNode, Transaction
from seirchain.config import Config # Import the Config class

class TriangularLedger:
    """
    Manages the SeirChain's triangular ledger structure.
    It's designed to hold a genesis triad and subsequent triads,
    maintaining a tree-like structure.
    """

    def __init__(self, max_depth, genesis_triad=None):
        self.max_depth = max_depth
        self.genesis_triad = genesis_triad
        self.difficulty = Config.instance().DIFFICULTY # Access current difficulty from Config

        if self.genesis_triad:
            print("Ledger initialized with existing Genesis Triad.")
        else:
            print("Ledger initialized without a Genesis Triad. Please run genesis generation.")

    def add_triad(self, new_triad):
        """
        Adds a new triad to the ledger.
        It finds the correct parent(s) based on current tip hashes and links the new triad.
        """
        if not self.genesis_triad:
            self.genesis_triad = new_triad
            print(f"Genesis Triad set: {new_triad.triad_hash}")
            return True

        # Find where to attach the new triad based on its parent hashes
        # This assumes new_triad.parent_hashes correctly points to existing tips
        found_parent = False
        for current_tip_hash in self.get_current_tip_triad_hashes():
            if current_tip_hash in new_triad.parent_hashes: # This is a direct parent
                parent_triad = self._find_triad_by_hash(current_tip_hash)
                if parent_triad:
                    parent_triad.add_child(new_triad)
                    found_parent = True
                    # print(f"Triad {new_triad.triad_hash} added as child of {current_tip_hash}")
                    break # Assuming one direct parent in current tips for simplicity
        
        # If not directly attached to a tip, it might be orphaned or needs more complex attachment logic
        if not found_parent:
            # This is a critical point for chain forks or orphaned triads.
            # For simplicity in initial implementation, we might print a warning.
            # print(f"Warning: Triad {new_triad.triad_hash} not directly attached to current tips. Possibly an orphaned triad or a fork.")
            pass # Handle more robustly later if forks are explicitly supported

        return found_parent


    def get_current_tip_triad_hashes(self):
        """
        Returns a list of hashes of the current 'tip' triads in the ledger.
        These are triads that have no children, representing the latest points for new mining.
        """
        if not self.genesis_triad:
            return []

        tips = []
        q = deque([self.genesis_triad])
        visited = set()

        while q:
            current_triad = q.popleft()
            if current_triad.triad_hash in visited:
                continue
            visited.add(current_triad.triad_hash)

            if not current_triad.children:
                tips.append(current_triad.triad_hash)
            else:
                for child in current_triad.children:
                    q.append(child)
        
        return tips if tips else [self.genesis_triad.triad_hash] # If no children anywhere, genesis is the only tip

    def get_total_triads(self):
        """
        Counts the total number of triads in the ledger by traversing the structure.
        """
        if not self.genesis_triad:
            return 0

        count = 0
        q = deque([self.genesis_triad])
        visited = set()

        while q:
            current_triad = q.popleft()
            if current_triad.triad_hash in visited:
                continue
            visited.add(current_triad.triad_hash)
            count += 1

            for child in current_triad.children:
                q.append(child)
        return count

    def get_all_transactions(self):
        """
        Generator that yields all individual Transaction objects from all Triads in the ledger.
        """
        if not self.genesis_triad:
            return

        q = deque([self.genesis_triad])
        visited = set()

        while q:
            current_triad = q.popleft()
            if current_triad.triad_hash in visited:
                continue
            visited.add(current_triad.triad_hash)

            for txn_node in current_triad.transactions:
                yield txn_node.transaction # Yield the actual Transaction object

            for child in current_triad.children:
                q.append(child)

    def _find_triad_by_hash(self, target_hash):
        """
        Helper method to find a triad by its hash by traversing the ledger.
        """
        if not self.genesis_triad:
            return None

        q = deque([self.genesis_triad])
        visited = set()

        while q:
            current_triad = q.popleft()
            if current_triad.triad_hash in visited:
                continue
            visited.add(current_triad.triad_hash)

            if current_triad.triad_hash == target_hash:
                return current_triad

            for child in current_triad.children:
                q.append(child)
        return None

    def save_to_json(self, filename):
        """Saves the entire ledger (starting from genesis triad) to a JSON file."""
        if not self.genesis_triad:
            print("No genesis triad to save.")
            return

        try:
            with open(filename, 'w') as f:
                json.dump(self.genesis_triad, f, indent=2, cls=TriadEncoder)
            # print(f"Ledger saved to {filename}")
        except Exception as e:
            print(f"Error saving ledger to {filename}: {e}")

    @classmethod
    def load_from_json(cls, filename):
        """Loads the entire ledger from a JSON file."""
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Ledger file not found: {filename}")

        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Recursively build Triad objects from the loaded data
        genesis_triad = cls._reconstruct_triad(data.get('root'))
        
        # Initialize ledger with max_depth from Config, as it's not stored in JSON
        config_instance = Config.instance()
        return cls(config_instance.MAX_DEPTH, genesis_triad)

    @staticmethod
    def _reconstruct_triad(triad_data):
        """Helper to recursively reconstruct Triad objects from JSON data."""
        if triad_data is None:
            return None
        
        # Reconstruct TransactionNodes (which contain Transactions)
        transactions = [
            TransactionNode(
                transaction=Transaction(
                    sender=tn_data['transaction_data']['from_addr'],
                    receiver=tn_data['transaction_data']['to_addr'],
                    amount=tn_data['transaction_data']['amount'],
                    fee=tn_data['transaction_data']['fee'],
                    timestamp=tn_data['transaction_data']['timestamp'],
                    signature=tn_data['transaction_data'].get('signature')
                ),
                parent_hash=tn_data.get('parent_hash') # TransactionNode might have its own parent_hash
            )
            for tn_data in triad_data['transactions']
        ]

        triad = Triad(
            parent_hashes=[], # Genesis Triad has no parent hashes
            difficulty=Config.instance().DIFFICULTY,
            transactions=transactions,
            nonce=triad_data['nonce'],
            timestamp=triad_data['timestamp'],
            triad_hash=triad_data['triangle_id'] # Reconstruct hash for existing triads
        )

        # Reconstruct children recursively
        for child_data in triad_data['children']:
            child_triad = TriangularLedger._reconstruct_triad(child_data)
            if child_triad:
                triad.add_child(child_triad) # Add child to the reconstructed parent

        return triad

