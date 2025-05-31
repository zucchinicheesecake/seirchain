import json
import os
import hashlib
import time
import uuid
from collections import deque
from seirchain.data_types.triad import Triad
from seirchain.data_types.transaction import TransactionNode, Transaction
from seirchain.config import config
import logging
import threading

logger = logging.getLogger(__name__)

class TriadEncoder(json.JSONEncoder):
    """
    Custom JSONEncoder to serialize Triad, TransactionNode, and Transaction objects.
    It simply calls the .to_dict() method on objects that have it.
    """
    def default(self, obj):
        if hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
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
        self._triad_map = {} # Stores all triads by their hash for quick lookup
        self.transaction_pool = []  # Add transaction pool to hold pending transactions
        self.transaction_pool_lock = threading.Lock()

        if self.genesis_triad:
            # If genesis provided, populate map with it, but the map itself should be built by load_from_json
            # This __init__ is primarily for initial creation or after loading
            self._triad_map[self.genesis_triad.hash_value] = self.genesis_triad
            logger.info("Ledger initialized with existing Genesis Triad.")
        else:
            logger.info("Ledger initialized without a Genesis Triad. Please run genesis generation.")

    def add_triad(self, new_triad):
        """
        Adds a new triad to the ledger.
        It finds the correct parent(s) based on current tip hashes and links the new triad.
        """
        if not self.genesis_triad:
            self.genesis_triad = new_triad
            self._triad_map[new_triad.hash_value] = new_triad # Add genesis to map
            logger.info(f"Genesis Triad set: {new_triad.hash_value}")
            return True

        # Debug log for new_triad attributes
        logger.debug(f"Adding triad: {new_triad}, attributes: {vars(new_triad)}")

        # Add new triad to map immediately
        if new_triad.hash_value not in self._triad_map:
            self._triad_map[new_triad.hash_value] = new_triad

        found_parent = False
        # Iterate through potential parent hashes of the new triad
        for parent_hash_of_new_triad in new_triad.parent_hashes:
            # Retrieve the parent triad object from the map
            parent_triad = self._triad_map.get(parent_hash_of_new_triad)
            if parent_triad:
                parent_triad.add_child(new_triad) # Link child to parent (adds child's hash)
                found_parent = True

        return found_parent

    def add_transaction(self, transaction):
        """
        Thread-safe addition of a transaction to the transaction pool.
        """
        with self.transaction_pool_lock:
            self.transaction_pool.append(transaction)
            logger.info(f"Transaction added to pool: {transaction.tx_hash}")

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
            if current_triad.hash_value in visited:
                continue
            visited.add(current_triad.hash_value)

            # Check if it's a tip
            if not current_triad.child_hashes: # Now correctly uses the populated child_hashes list
                tips.append(current_triad.hash_value)
            else:
                for child_hash in current_triad.child_hashes:
                    child_triad = self._triad_map.get(child_hash) # Get child from map
                    if child_triad and child_triad.hash_value not in visited:
                        q.append(child_triad)

        return tips if tips else [self.genesis_triad.hash_value]

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
            if current_triad.hash_value in visited:
                continue
            visited.add(current_triad.hash_value)

            for txn_node in current_triad.transactions:
                yield txn_node.transaction

            for child_hash in current_triad.child_hashes:
                child_triad = self._triad_map.get(child_hash) # Get child from map
                if child_triad and child_triad.hash_value not in visited:
                    q.append(child_triad)

    def _find_triad_by_hash(self, target_hash):
        """
        Helper method to find a triad by its hash.
        Now uses the _triad_map for direct O(1) lookup.
        """
        return self._triad_map.get(target_hash)

    def save_to_json(self, filename):
        """Saves the entire ledger (all triads in _triad_map) to a JSON file."""
        if not self.genesis_triad:
            logger.warning("No genesis triad to save.")
            return

        try:
            # Prepare a list of all triad dictionaries
            all_triads_data = [triad.to_dict() for triad in self._triad_map.values()]

            # Save the genesis hash and the list of all triads
            ledger_data = {
                "genesis_hash": self.genesis_triad.hash_value,
                "all_triads": all_triads_data
            }

            with open(filename, 'w') as f:
                json.dump(ledger_data, f, indent=2, cls=TriadEncoder)
            logger.info(f"Ledger data saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving ledger to {filename}: {e}")

    @staticmethod
    def load_from_json(filename):
        """Loads the entire ledger from a JSON file, reconstructing links."""
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Ledger file not found: {filename}")

        try:
            with open(filename, 'r') as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f"Error reading ledger JSON file {filename}: {e}")

        genesis_hash = data.get('genesis_hash')
        all_triads_data = data.get('all_triads', [])

        if not genesis_hash or not all_triads_data:
            raise ValueError(f"Invalid ledger JSON format in {filename}: missing 'genesis_hash' or 'all_triads' key.")

        # Step 1: Reconstruct all Triad objects and populate a temporary map
        temp_triad_map = {}
        for triad_data in all_triads_data:
            try:
                transactions = [
                    TransactionNode(
                        transaction=Transaction(
                            transaction_data={
                                'from_addr': tn_data['transaction_data'].get('from_addr') or tn_data['transaction_data'].get('sender'),
                                'to_addr': tn_data['transaction_data'].get('to_addr') or tn_data['transaction_data'].get('receiver'),
                                'amount': tn_data['transaction_data']['amount'],
                                'fee': tn_data['transaction_data']['fee'],
                                'timestamp': tn_data['transaction_data']['timestamp'],
                                'signature': tn_data['transaction_data'].get('signature')
                            },
                            tx_hash=tn_data.get('tx_hash') or tn_data.get('tx_hash'),
                            timestamp=tn_data.get('timestamp')
                        )
                    )
                    for tn_data in triad_data.get('transactions', [])
                ]
            except Exception as e:
                logger.error(f"Error reconstructing transactions for triad {triad_data.get('triad_id')}: {e}")
                transactions = []

            triad = Triad(
                triad_id=triad_data.get('triad_id'),
                depth=triad_data.get('depth'),
                hash_value=triad_data.get('triangle_id') or triad_data.get('hash_value'),
                parent_hashes=triad_data.get('parent_hashes', [])
            )
            # Set additional attributes if present
            for attr in ['nonce', 'difficulty', 'mined_by', 'timestamp', 'child_hashes']:
                if attr in triad_data:
                    setattr(triad, attr, triad_data[attr])
            triad.transactions = transactions
            temp_triad_map[triad.hash_value] = triad

        # Step 2: Re-establish parent-child object links by traversing the map
        for triad_hash, triad_obj in temp_triad_map.items():
            for child_hash_ref in triad_obj.child_hashes:
                if child_hash_ref in temp_triad_map:
                    # Links are implicitly managed by parent/child_hashes and the _triad_map
                    pass

        # Get the genesis triad object
        genesis_triad = temp_triad_map.get(genesis_hash)
        if not genesis_triad:
            raise ValueError(f"Genesis triad with hash {genesis_hash[:8]}... not found in loaded data.")

        # Create the ledger instance and assign the fully populated map
        ledger_instance = TriangularLedger(config.MAX_DEPTH, genesis_triad)
        ledger_instance._triad_map = temp_triad_map # Assign the map with all reconstructed triads

        return ledger_instance
