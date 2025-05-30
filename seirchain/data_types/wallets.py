import json
import os
import hashlib
import random
import time # <--- ENSURE THIS IS PRESENT

# Import config for data_dir
from seirchain.config import config as global_config

class Wallets:
    def __init__(self):
        self.wallets = {}  # Dictionary to store wallet_id: {name: str, balance: float}
        self.config = global_config
        self.wallets_file_path = os.path.join(self.config.data_dir, 'wallets.json')

    def generate_wallet_id(self):
        """Generates a simple unique wallet ID based on a hash of random data and timestamp."""
        unique_string = str(random.getrandbits(256)) + str(time.time()) + str(os.urandom(16)) # Add os.urandom for more entropy
        return hashlib.sha256(unique_string.encode('utf-8')).hexdigest()[:32] # Use 32 chars for uniqueness

    def add_wallet(self, wallet_name, initial_balance=0.0):
        """Adds a new wallet to the system."""
        wallet_id = self.generate_wallet_id()
        if wallet_id in self.wallets:
            # Very unlikely, but handle collision
            return self.add_wallet(wallet_name, initial_balance)
        
        self.wallets[wallet_id] = {
            "name": wallet_name,
            "balance": float(initial_balance)
        }
        # print(f"Added wallet '{wallet_name}' with ID {wallet_id} and balance {initial_balance}")
        return wallet_id

    def get_balance(self, wallet_id):
        """Returns the balance of a given wallet."""
        return self.wallets.get(wallet_id, {}).get("balance", 0.0)

    def add_funds(self, wallet_id, amount):
        """Adds funds to a wallet."""
        if wallet_id in self.wallets:
            self.wallets[wallet_id]["balance"] += float(amount)
            # print(f"Added {amount} to wallet {wallet_id}. New balance: {self.get_balance(wallet_id)}")
            return True
        # print(f"Wallet {wallet_id} not found to add funds.")
        return False

    def deduct_funds(self, wallet_id, amount):
        """Deducts funds from a wallet, ensuring sufficient balance."""
        if wallet_id in self.wallets and self.wallets[wallet_id]["balance"] >= float(amount):
            self.wallets[wallet_id]["balance"] -= float(amount)
            # print(f"Deducted {amount} from wallet {wallet_id}. New balance: {self.get_balance(wallet_id)}")
            return True
        # print(f"Insufficient funds or wallet {wallet_id} not found to deduct {amount}.")
        return False

    def transfer_funds(self, sender_id, recipient_id, amount, fee=0.0):
        """Transfers funds from one wallet to another, applying a fee."""
        if sender_id == recipient_id:
            # print("Sender and recipient cannot be the same.")
            return False

        total_amount_to_deduct = float(amount) + float(fee)
        
        if self.deduct_funds(sender_id, total_amount_to_deduct):
            if self.add_funds(recipient_id, float(amount)):
                # Fee is implicitly handled: deducted from sender, not added to recipient here.
                # Miner collects reward separately.
                return True
            else:
                # If recipient fails, revert sender's deduction
                self.add_funds(sender_id, total_amount_to_deduct)
                # print(f"Failed to add funds to recipient {recipient_id}. Transaction aborted.")
                return False
        # print(f"Transfer failed: Sender {sender_id} does not have enough funds for {total_amount_to_deduct}.")
        return False

    def get_random_wallet_id(self):
        """Returns a random wallet ID for simulation purposes (excluding the Genesis miner wallet for transfers)."""
        candidate_ids = [wid for wid, wdata in self.wallets.items() if wdata['name'] != "GENESIS_MINE_WALLET"]
        if not candidate_ids:
            # If only genesis miner wallet exists, return None or handle as needed
            return None
        return random.choice(candidate_ids)
        
    def get_wallet_id_by_name(self, name):
        """Returns the ID of a wallet given its name."""
        for wallet_id, wallet_data in self.wallets.items():
            if wallet_data.get("name") == name:
                return wallet_id
        return None

    def save_wallets(self, network_name):
        """Saves current wallet balances to a JSON file."""
        save_path = os.path.join(self.config.data_dir, f'wallets_{network_name}.json')
        try:
            with open(save_path, 'w') as f:
                json.dump(self.wallets, f, indent=2)
            # print(f"Wallets saved to {save_path}")
            return True
        except IOError as e:
            print(f"Error saving wallets to {save_path}: {e}")
            return False

    def load_wallets(self, network_name):
        """Loads wallet balances from a JSON file."""
        load_path = os.path.join(self.config.data_dir, f'wallets_{network_name}.json')
        if os.path.exists(load_path):
            try:
                with open(load_path, 'r') as f:
                    self.wallets = json.load(f)
                # print(f"Wallets loaded from {load_path}")
                return True
            except json.JSONDecodeError as e:
                print(f"Error decoding wallets JSON from {load_path}: {e}")
                self.wallets = {}
                return False
            except IOError as e:
                print(f"Error loading wallets from {load_path}: {e}")
                self.wallets = {}
                return False
        else:
            # print(f"Wallets file '{os.path.basename(load_path)}' not found. Starting with empty wallets.")
            self.wallets = {}
            return False

# Instantiate the Wallets class so it can be imported by other modules
wallets = Wallets()
