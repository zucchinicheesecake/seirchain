import json
import os
import hashlib
import time
import uuid
from collections import deque
from seirchain.data_types.triad import Triad
from seirchain.data_types.transaction import TransactionNode, Transaction
from seirchain.config import config

class TriadEncoder(json.JSONEncoder):
    """
    Custom JSONEncoder to serialize Triad, TransactionNode, and Transaction objects.
    """
    def default(self, obj):
        if isinstance(obj, Triad):
            return obj.to_dict()
        elif hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
            return obj.to_dict()
        return json.JSONEncoder.default(self, obj)

class TriangularLedger:
    """
    Manages the SeirChain's triangular ledger structure.
    It's designed to hold a genesis triad and subsequent triads,
    maintaining a tree-like structure.
    """
    def __init__(self, max_depth, genesis_triad=None):
        self.max_depth = max_depth
        self.genesis_triad = genesis_triad
        self.difficulty = config.DIFFICULTY
        self._triad_map = {} # New: Stores all triads by their hash for quick lookup

        if self.genesis_triad:
            # If genesis provided, populate map recursively
            self._populate_triad_map(self.genesis_triad)
            print("Ledger initialized with existing Genesis Triad.")
        else:
            print("Ledger initialized without a Genesis Triad. Please run genesis generation.")

    def _populate_triad_map(self, triad):
        """Helper to add a triad and its children to the _triad_map recursively."""
        if triad.hash not in self._triad_map:
            self._triad_map[triad.hash] = triad
            for child_hash in triad.child_hashes:
                # In a fully formed ledger, child_hash should exist as a key or be added later
                # For now, this is a helper to ensure loaded triads are mapped
                pass # Children will be mapped when they are processed by _reconstruct_triad or add_triad

    def add_triad(self, new_triad):
        """
        Adds a new triad to the ledger.
        It finds the correct parent(s) based on current tip hashes and links the new triad.
        """
        if not self.genesis_triad:
            self.genesis_triad = new_triad
            self._triad_map[new_triad.hash] = new_triad # Add genesis to map
            print(f"Genesis Triad set: {new_triad.hash}")
            return True

        # Add new triad to map immediately
        self._triad_map[new_triad.hash] = new_triad

        found_parent = False
        # Iterate through potential parent hashes of the new triad
        for parent_hash_of_new_triad in new_triad.parent_hashes:
            # Retrieve the parent triad object from the map
            parent_triad = self._triad_map.get(parent_hash_of_new_triad)
            if parent_triad:
                parent_triad.add_child(new_triad) # Link child to parent
                found_parent = True
                # In a triangular ledger, a triad might have multiple parents.
                # For simplicity, we'll assume linking to one parent is sufficient for validation here.
                # If you want to enforce multiple parents, adjust this logic.
                break # Assuming one parent link is enough for now

        if not found_parent:
            # This could mean the new triad has no valid parent in the current ledger,
            # which might indicate a fork or an issue.
            pass # Or raise an error, or log a warning

        return found_parent

    def get_current_tip_triad_hashes(self):
        """
        Returns a list of hashes of the current 'tip' triads in the ledger.
        These are triads that have no children, representing the latest points for new mining.
        Uses the _triad_map for efficient traversal.
        """
        if not self.genesis_triad:
            return []

        tips = []
        q = deque([self.genesis_triad])
        visited = set()

        while q:
            current_triad = q.popleft()
            if current_triad.hash in visited:
                continue
            visited.add(current_triad.hash)

            if not current_triad.child_hashes:
                tips.append(current_triad.hash)
            else:
                for child_hash in current_triad.child_hashes:
                    child_triad = self._triad_map.get(child_hash) # Get child from map
                    if child_triad and child_triad.hash not in visited:
                        q.append(child_triad)
        return tips if tips else [self.genesis_triad.hash]

    def get_total_triads(self):
        """
        Counts the total number of triads in the ledger using the _triad_map size.
        Much more efficient than traversal.
        """
        return len(self._triad_map)

    def get_all_transactions(self):
        """
        Generator that yields all individual Transaction objects from all Triads in the ledger.
        Uses the _triad_map for efficient traversal.
        """
        if not self.genesis_triad:
            return
        q = deque([self.genesis_triad])
        visited = set()
        while q:
            current_triad = q.popleft()
            if current_triad.hash in visited:
                continue
            visited.add(current_triad.hash)
            for txn_node in current_triad.transactions:
                yield txn_node.transaction
            for child_hash in current_triad.child_hashes:
                child_triad = self._triad_map.get(child_hash) # Get child from map
                if child_triad and child_triad.hash not in visited:
                    q.append(child_triad)

    def _find_triad_by_hash(self, target_hash):
        """
        Helper method to find a triad by its hash.
        Now uses the _triad_map for direct O(1) lookup.
        """
        return self._triad_map.get(target_hash)

    def save_to_json(self, filename):
        """Saves the entire ledger (starting from genesis triad) to a JSON file."""
        if not self.genesis_triad:
            print("No genesis triad to save.")
            return
        try:
            with open(filename, 'w') as f:
                # Corrected to wrap the genesis_triad data under a "root" key
                # Only serialize the genesis triad and let TriadEncoder handle recursion through children
                json.dump({"root": self.genesis_triad}, f, indent=2, cls=TriadEncoder)
        except Exception as e:
            print(f"Error saving ledger to {filename}: {e}")

    @classmethod
    def load_from_json(cls, filename):
        """Loads the entire ledger from a JSON file."""
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Ledger file not found: {filename}")
        with open(filename, 'r') as f:
            data = json.load(f)

        root_triad_data = data.get('root')
        if not root_triad_data:
            raise ValueError(f"Invalid ledger JSON format in {filename}: 'root' key not found.")

        # Pass a temporary map to _reconstruct_triad to build up all triads
        temp_triad_map = {}
        genesis_triad = cls._reconstruct_triad(root_triad_data, temp_triad_map)

        # Create ledger instance and explicitly set its _triad_map
        ledger_instance = cls(config.MAX_DEPTH, genesis_triad)
        ledger_instance._triad_map = temp_triad_map # Set the populated map

        return ledger_instance

    @staticmethod
    def _reconstruct_triad(triad_data, triad_map_ref):
        """
        Helper to recursively reconstruct Triad objects from JSON data
        and populate a shared triad_map_ref.
        """
        if triad_data is None:
            return None

        # Avoid reconstructing if already in map (for cycles/efficiency)
        existing_triad = triad_map_ref.get(triad_data.get('triangle_id'))
        if existing_triad:
            return existing_triad

        transactions = [
            TransactionNode(
                transaction=Transaction(
                    sender=tn_data['transaction_data']['sender'],
                    receiver=tn_data['transaction_data']['receiver'],
                    amount=tn_data['transaction_data']['amount'],
                    fee=tn_data['transaction_data']['fee'],
                    timestamp=tn_data['transaction_data']['timestamp'],
                    signature=tn_data['transaction_data'].get('signature')
                ),
                parent_hash=tn_data.get('parent_hash')
            )
            for tn_data in triad_data['transactions']
        ]

        triad = Triad(
            triad_id=triad_data.get('triad_id', str(uuid.uuid4())),
            depth=triad_data.get('depth', 0),
            parent_hashes=triad_data.get('parent_hashes', []),
            difficulty=config.DIFFICULTY,
            transactions=transactions,
            nonce=triad_data['nonce'],
            timestamp=triad_data['timestamp'],
            current_hash=triad_data['triangle_id'],
            miner_address=triad_data['mined_by']
        )

        triad_map_ref[triad.hash] = triad # Add to the map immediately

        # Recursively reconstruct children and link them
        for child_data in triad_data.get('children', []):
            child_triad = TriangularLedger._reconstruct_triad(child_data, triad_map_ref)
            if child_triad:
                triad.add_child(child_triad)
        return triad

