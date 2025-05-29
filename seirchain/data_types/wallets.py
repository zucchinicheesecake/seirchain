import json
import os
import secrets # For generating secure random wallet IDs
import hashlib

class Wallets:
    """
    Manages all wallets (addresses and balances) for the blockchain simulation.
    Implemented as a Singleton to ensure a single source of truth for wallet data.
    """
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Wallets, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.wallets = {}  # Stores wallet_id: balance
            self._initialized = True

    @classmethod
    def instance(cls):
        """Returns the singleton instance of Wallets."""
        if cls._instance is None:
            cls() # This calls __init__
        return cls._instance

    def generate_wallet_id(self):
        """Generates a unique cryptographic wallet ID (public address)."""
        # A simple method to generate a unique ID. In a real system, this would involve
        # public/private key pairs and more robust cryptographic methods.
        return hashlib.sha256("".join(secrets.token_hex(32)).encode('utf-8')).hexdigest() # Corrected to sha256

    def create_wallet(self, initial_balance=0.0, wallet_name=None):
        """Creates a new wallet with an optional initial balance and name."""
        wallet_id = self.generate_wallet_id()
        self.wallets[wallet_id] = {
            "balance": initial_balance,
            "name": wallet_name # Optional human-readable name
        }
        return wallet_id

    def add_funds(self, wallet_id, amount):
        """Adds funds to a specified wallet."""
        if wallet_id in self.wallets:
            self.wallets[wallet_id]["balance"] += amount
            return True
        return False

    def deduct_funds(self, wallet_id, amount):
        """Deducts funds from a specified wallet."""
        if wallet_id in self.wallets and self.wallets[wallet_id]["balance"] >= amount:
            self.wallets[wallet_id]["balance"] -= amount
            return True
        return False

    def transfer_funds(self, sender_id, receiver_id, amount, fee=0.0):
        """Transfers funds between two wallets, deducting a fee."""
        total_cost = amount + fee
        if sender_id not in self.wallets or receiver_id not in self.wallets:
            print("Error: Sender or receiver wallet not found.")
            return False
        if self.wallets[sender_id]["balance"] < total_cost:
            print(f"Error: Insufficient funds in sender wallet {sender_id[:8]}... (Balance: {self.wallets[sender_id]['balance']:.2f}, Needed: {total_cost:.2f})")
            return False

        if self.deduct_funds(sender_id, total_cost):
            self.add_funds(receiver_id, amount)
            # In a real system, the fee would go to the miner or be burned
            # For now, it's just deducted from sender.
            return True
        return False

    def get_balance(self, wallet_id):
        """Returns the balance of a specified wallet."""
        return self.wallets.get(wallet_id, {"balance": 0.0})["balance"]

    def get_all_wallet_ids(self):
        """Returns a list of all active wallet IDs."""
        return list(self.wallets.keys())

    def get_wallet_id_by_name(self, name):
        """
        Returns the wallet ID for a given wallet name.
        Assumes names are unique or returns the first match.
        """
        for wallet_id, details in self.wallets.items():
            if details.get("name") == name:
                return wallet_id
        return None # Return None if no wallet with that name is found

    def load_wallets(self, network):
        """Loads wallet data from a JSON file for the specified network."""
        wallets_file = f"wallets_{network}.json"
        if os.path.exists(wallets_file):
            try:
                with open(wallets_file, 'r') as f:
                    data = json.load(f)
                    self.wallets = data.get('wallets', {})
                print(f"Wallets loaded from {wallets_file}.")
            except Exception as e:
                print(f"Error loading wallets: {e}. Initializing default wallets.")
                self._initialize_default_wallets()
        else:
            print(f"No existing wallets file found at {wallets_file}. Initializing default wallets.")
            self._initialize_default_wallets()

    def _initialize_default_wallets(self):
        """Initializes default wallets for a new or corrupted wallets file."""
        self.wallets = {}
        # Create a genesis wallet for mining rewards
        genesis_wallet_id = self.create_wallet(initial_balance=2000000.0, wallet_name="GENESIS_MINE_WALLET")
        # Create one more generic wallet for transactions
        self.create_wallet(initial_balance=1000.0) # No name, just an ID
        print("Default wallets initialized.")

    def save_wallets(self, network):
        """Saves the current wallet data to a JSON file for the specified network."""
        wallets_file = f"wallets_{network}.json"
        with open(wallets_file, 'w') as f:
            json.dump({"wallets": self.wallets}, f, indent=2)

    def print_balances(self, top_n=5):
        """Prints the balances of wallets, sorted by balance."""
        sorted_wallets = sorted(self.wallets.items(), key=lambda item: item[1]['balance'], reverse=True)
        for i, (wallet_id, details) in enumerate(sorted_wallets):
            if i >= top_n:
                break
            name_tag = f" ({details['name']})" if details['name'] else ""
            print(f"  Wallet {wallet_id[:8]}...{name_tag} Balance: {details['balance']:.2f}")
