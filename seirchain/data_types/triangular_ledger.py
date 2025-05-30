import json
import os
import time
import hashlib

from seirchain.config import config as global_config
from seirchain.data_types.triad import Triad 
from seirchain.data_types.transaction_node import TransactionNode 
from seirchain.data_types.wallets import wallets as global_wallets

class TriangularLedger:
    def __init__(self):
        # self.triads will be replaced by a shared dict when run via multiprocessing Manager
        self.triads = {} 
        self.max_current_depth = -1 # Initial value; updated based on loaded data or new triads
        self.config = global_config
        self.wallets = global_wallets # Link to the global wallets instance
        self.ledger_file_path = os.path.join(self.config.data_dir, 'ledger.json')

    def initialize_genesis_triad(self, miner_address):
        # Check if the ledger is effectively empty (only contains the internal max_current_depth key)
        if not self.triads or (len(self.triads) == 1 and '__max_current_depth' in self.triads):
            genesis_triad = Triad(
                triad_id="genesis_triad",
                depth=0,
                parent_hashes=[],
                transactions=[], # Genesis typically has no transactions initially
                nonce=0,
                difficulty=self.config.DIFFICULTY,
                miner_address=miner_address
            )
            
            # Mine the genesis triad to meet the difficulty
            for nonce_attempt in range(self.config.MAX_NONCE_ATTEMPTS):
                genesis_triad.nonce = nonce_attempt
                current_hash = genesis_triad.calculate_hash()
                if current_hash.startswith('0' * self.config.DIFFICULTY):
                    genesis_triad.hash = current_hash # Set the final hash
                    break
            else:
                print("Failed to mine genesis triad within max attempts.")
                return False
            
            # Add the mined genesis triad to the ledger
            if self.add_triad(genesis_triad, is_genesis=True):
                return True
            else:
                print("Failed to add genesis triad to the ledger after mining.")
                return False
        else:
            # print("Ledger is not empty, genesis triad cannot be initialized.")
            return False

    def add_triad(self, triad, is_genesis=False):
        # If 'triad' is a dictionary (from multiprocessing Manager), convert it to a Triad object
        if not isinstance(triad, Triad):
            triad_obj = Triad.from_dict(triad)
        else:
            triad_obj = triad

        # Prevent adding if already exists (and not the internal key)
        if triad_obj.hash in self.triads and triad_obj.hash != '__max_current_depth':
            return False

        # Validate hash difficulty
        if not triad_obj.hash.startswith('0' * self.config.DIFFICULTY):
            return False

        # Validate non-genesis triad parentage and depth
        if not is_genesis:
            if not triad_obj.parent_hashes:
                return False # Non-genesis must have parents
            
            for parent_hash in triad_obj.parent_hashes:
                parent_triad_data = self.triads.get(parent_hash)
                if not parent_triad_data:
                    return False # Parent must exist
                
                parent_triad_obj = Triad.from_dict(parent_triad_data)

                if parent_triad_obj.is_full():
                    return False # Parent cannot accept more children
                if not triad_obj.depth == parent_triad_obj.depth + 1:
                    return False # Depth must be exactly one greater than parent

        # Validate genesis triad
        elif triad_obj.parent_hashes or triad_obj.depth != 0:
            return False # Genesis must have no parents and depth 0
            
        # Check against maximum ledger depth
        if triad_obj.depth > self.config.MAX_DEPTH:
            return False

        # Process transactions within the triad
        for tx in triad_obj.transactions:
            # Ensure tx is a TransactionNode object (convert if dict)
            if not isinstance(tx, TransactionNode):
                tx_obj = TransactionNode.from_dict(tx)
            else:
                tx_obj = tx

            if not self.process_transaction(tx_obj):
                return False # Transaction failed validation or transfer

        # Add the triad to the internal dictionary (which is the shared Manager.dict)
        self.triads[triad_obj.hash] = triad_obj.to_dict() # Store as serializable dict

        # Update parent's child_hashes in the shared dict
        for parent_hash in triad_obj.parent_hashes:
            parent_data = self.triads.get(parent_hash)
            if parent_data and triad_obj.hash not in parent_data.get('child_hashes', []):
                parent_data_copy = dict(parent_data) # Create a modifiable copy
                children = parent_data_copy.get('child_hashes', [])
                if len(children) < self.config.MAX_CHILD_CAPACITY: # Use config for capacity
                    children.append(triad_obj.hash)
                    parent_data_copy['child_hashes'] = children
                    self.triads[parent_hash] = parent_data_copy # Update the shared dict
        
        # Update max_current_depth
        if triad_obj.depth > self.max_current_depth:
            self.max_current_depth = triad_obj.depth
        
        # Store max_current_depth in the shared dictionary itself for easy access by other processes
        self.triads['__max_current_depth'] = self.max_current_depth 

        # Reward the miner
        if triad_obj.miner_address:
            self.wallets.add_funds(triad_obj.miner_address, self.config.MINING_REWARD)

        return True

    def process_transaction(self, transaction):
        """Processes a single transaction, moving funds between wallets."""
        if not self.wallets.transfer_funds(
            transaction.sender_address,
            transaction.recipient_address,
            transaction.amount,
            self.config.TRANSACTION_FEE
        ):
            return False
        return True

    def get_triad(self, triad_hash):
        """Retrieves a triad by its hash, converting from dict to Triad object."""
        data = self.triads.get(triad_hash)
        return Triad.from_dict(data) if data else None

    def get_max_current_depth(self):
        """Returns the current maximum depth of the ledger."""
        # When using shared_ledger_data, this will read from the special key
        return self.triads.get('__max_current_depth', -1)

    def get_total_triads(self):
        """Returns the total number of actual triads in the ledger (excluding internal keys)."""
        # Exclude the internal __max_current_depth key from count
        return len([k for k in self.triads.keys() if not k.startswith('__')])


    def get_candidate_parents(self):
        """
        Returns a list of Triad objects that can serve as parents for new triads.
        Candidates are typically from the current max depth or max_depth - 1, and not full.
        """
        candidates = []
        # If ledger is empty (or only contains the internal key), no parents yet
        if not self.triads or (len(self.triads) == 1 and '__max_current_depth' in self.triads): 
            return candidates

        # Filter out the internal __max_current_depth key and convert to Triad objects
        active_triads = {h: Triad.from_dict(t) for h, t in self.triads.items() if not h.startswith('__')}

        current_max_depth = self.get_max_current_depth() 

        for triad_hash, triad in active_triads.items():
            # Consider triads from the current max depth and one level below
            # that are not yet full, to allow new triads to connect.
            if triad.depth >= current_max_depth - 1 and not triad.is_full():
                candidates.append(triad)
        
        # Return a list of unique candidate Triad objects
        unique_candidates = {t.hash: t for t in candidates}.values()
        return list(unique_candidates)

    def save_ledger(self, network_name):
        """Saves the current state of the ledger to a JSON file."""
        save_path = os.path.join(self.config.data_dir, f'ledger_{network_name}.json')
        
        # Filter out internal keys like __max_current_depth before saving
        serializable_triads = {
            triad_hash: triad_data
            for triad_hash, triad_data in self.triads.items()
            if not triad_hash.startswith('__')
        }
        try:
            with open(save_path, 'w') as f:
                json.dump(serializable_triads, f, indent=2)
            return True
        except IOError as e:
            print(f"Error saving ledger to {save_path}: {e}")
            return False

    def load_ledger(self, network_name):
        """Loads the ledger state from a JSON file."""
        load_path = os.path.join(self.config.data_dir, f'ledger_{network_name}.json')
        if os.path.exists(load_path):
            try:
                with open(load_path, 'r') as f:
                    loaded_data = json.load(f)
                    self.triads = loaded_data # Load directly into the internal dict
                    
                    self.max_current_depth = -1 # Recalculate max depth from loaded data
                    for triad_hash, triad_dict in self.triads.items():
                        # Ensure 'depth' key exists before accessing
                        if isinstance(triad_dict, dict) and 'depth' in triad_dict:
                            if triad_dict['depth'] > self.max_current_depth:
                                self.max_current_depth = triad_dict['depth']
                        else:
                            print(f"Warning: Triad data for hash {triad_hash} is malformed, skipping.")
                            # Optionally remove malformed data from self.triads here
                            del self.triads[triad_hash] # Safely remove problematic entry
                
                # Store max_current_depth in the shared dict (important for multiprocessing)
                self.triads['__max_current_depth'] = self.max_current_depth 
                return True
            except json.JSONDecodeError as e:
                print(f"Error decoding ledger JSON from {load_path}: {e}")
                self.triads = {}
                return False
            except IOError as e:
                print(f"Error loading ledger from {load_path}: {e}")
                self.triads = {}
                return False
        else:
            self.triads = {}
            # Ensure the shared max_current_depth key is present even for an empty ledger
            self.triads['__max_current_depth'] = -1 
            return False

    def _reset_for_testing(self):
        """Resets the ledger state (for testing purposes only)."""
        self.triads = {}
        self.max_current_depth = -1
