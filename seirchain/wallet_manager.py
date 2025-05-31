import json
import os
import time
import logging
from seirchain.data_types import Transaction

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Wallet:
    def __init__(self, address, balance=0.0, public_key=None):
        self.address = address
        self.balance = balance
        self.public_key = public_key
        self.transaction_history = []
        
    def update_balance(self, delta):
        new_balance = self.balance + delta
        if new_balance < 0:
            raise ValueError(f"Insufficient funds in wallet {self.address[:8]}: current balance {self.balance}, attempted change {delta}")
        self.balance = new_balance
        
    def add_transaction(self, tx_hash):
        self.transaction_history.append(tx_hash)
        
    def to_dict(self):
        return {
            'address': self.address,
            'balance': self.balance,
            'public_key': self.public_key,
            'transaction_history': self.transaction_history
        }
        
    @classmethod
    def from_dict(cls, data):
        wallet = cls(data['address'], data['balance'], data['public_key'])
        wallet.transaction_history = data['transaction_history']
        return wallet
        
    def __repr__(self):
        return f"Wallet({self.address[:12]}..., balance={self.balance})"


class WalletManager:
    def __init__(self):
        self.wallets = {}
        
    def get_wallet(self, address):
        if not self._is_valid_address(address):
            raise ValueError(f"Invalid wallet address: {address}")
        # Normalize address to 64 characters by padding with zeros if length is 40
        if len(address) == 40:
            address = address.rjust(64, '0')
        if address not in self.wallets:
            self.wallets[address] = Wallet(address)
        return self.wallets[address]
    
    def add_wallet(self, address, initial_balance=0.0):
        """Explicitly add a wallet (if not already exists)"""
        if not self._is_valid_address(address):
            raise ValueError(f"Invalid wallet address: {address}")
        if address not in self.wallets:
            self.wallets[address] = Wallet(address, initial_balance)
        return self.wallets[address]
    
    def wallet_exists(self, address):
        return address in self.wallets
    
    def update_balances(self, transaction):
        # Defensive: access from_addr via property or attribute
        from_addr = None
        to_addr = None
        amount = None
        fee = None
        try:
            from_addr = transaction.from_addr
            to_addr = transaction.to_addr
            amount = transaction.amount
            fee = transaction.fee
        except AttributeError:
            # Fallback to transaction_data dict if properties missing
            from_addr = transaction.transaction_data.get('from_addr')
            to_addr = transaction.transaction_data.get('to_addr')
            amount = transaction.transaction_data.get('amount')
            fee = transaction.transaction_data.get('fee')

        # Special case: if from_addr is zero address, skip balance deduction
        zero_address_40 = "0" * 40
        zero_address_64 = "0" * 64
        # Normalize from_addr length to 64 for comparison
        if len(from_addr) == 40:
            from_addr = from_addr.rjust(64, '0')
        logger.debug(f"Normalized from_addr: '{from_addr}' (len={len(from_addr)}), zero_address_64: '{zero_address_64}' (len={len(zero_address_64)})")
        if from_addr.strip() == zero_address_64:
            logger.debug(f"Special case: zero address detected, adding {amount} to {to_addr} without deduction")
            # Only add amount to receiver
            receiver = self.get_wallet(to_addr)
            try:
                receiver.update_balance(amount)
            except ValueError as e:
                logger.error(f"Balance update error: {e}")
                return False
            # Record transaction for receiver only
            receiver.add_transaction(transaction.tx_hash)
            return True

        sender = self.get_wallet(from_addr)
        receiver = self.get_wallet(to_addr)
        
        # Update balances
        try:
            sender.update_balance(-amount - fee)
            receiver.update_balance(amount)
        except ValueError as e:
            logger.error(f"Balance update error: {e}")
            return False
        
        # Record transaction
        sender.add_transaction(transaction.tx_hash)
        receiver.add_transaction(transaction.tx_hash)
        return True

    def add_funds(self, address, amount):
        wallet = self.get_wallet(address)
        wallet.update_balance(amount)

    def deduct_funds(self, address, amount):
        wallet = self.get_wallet(address)
        wallet.update_balance(-amount)

    def transfer_funds(self, from_addr, to_addr, amount, fee):
        """Transfer funds from one wallet to another, including fee deduction."""
        try:
            sender = self.get_wallet(from_addr)
            receiver = self.get_wallet(to_addr)
            sender.update_balance(-amount - fee)
            receiver.update_balance(amount)
            return True
        except ValueError as e:
            logger.error(f"Transfer funds error: {e}")
            return False

    def add_funds(self, address, amount):
        wallet = self.get_wallet(address)
        wallet.update_balance(amount)

    def deduct_funds(self, address, amount):
        wallet = self.get_wallet(address)
        wallet.update_balance(-amount)
        
    def load_wallets(self, network):
        """Load wallets from JSON file"""
        filename = f"data/wallets_{network}.json"
        if not os.path.exists(filename):
            logger.warning(f"Wallet file {filename} does not exist.")
            return None
            
        try:
            with open(filename, 'r') as f:
                wallets_data = json.load(f)
                for addr, data in wallets_data.items():
                    self.wallets[addr] = Wallet.from_dict(data)
            return True
        except Exception as e:
            logger.error(f"Error loading wallets from {filename}: {e}")
            return None
                
    def save_wallets(self, network):
        """Save wallets to JSON file"""
        wallets_data = {addr: wallet.to_dict() for addr, wallet in self.wallets.items()}
        filename = f"data/wallets_{network}.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        try:
            with open(filename, 'w') as f:
                json.dump(wallets_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving wallets to {filename}: {e}")
            return False
        
    def _is_valid_address(self, address):
        # Basic validation: address should be a 40 or 64-character hex string
        if not isinstance(address, str):
            return False
        if len(address) not in (40, 64):
            return False
        try:
            int(address, 16)
            return True
        except ValueError:
            return False
        
    def __repr__(self):
        return f"WalletManager({len(self.wallets)} wallets)"

# Global instance
global_wallets = WalletManager()

# Public API functions
def create_wallet(address, initial_balance=0.0):
    return global_wallets.add_wallet(address, initial_balance)

def get_balance(address):
    wallet = global_wallets.get_wallet(address)
    return wallet.balance

def get_wallet(address):
    return global_wallets.get_wallet(address)

# Add missing get_balance method to WalletManager class
def wallet_manager_get_balance(self, address):
    wallet = self.get_wallet(address)
    return wallet.balance

WalletManager.get_balance = wallet_manager_get_balance

def send_transaction(from_addr, to_addr, amount, fee):
    from seirchain.network import node
    # Validate addresses and amounts
    if not global_wallets._is_valid_address(from_addr):
        logger.error(f"Invalid from_addr: {from_addr}")
        return None
    if not global_wallets._is_valid_address(to_addr):
        logger.error(f"Invalid to_addr: {to_addr}")
        return None
    if amount <= 0 or fee < 0:
        logger.error(f"Invalid amount or fee: amount={amount}, fee={fee}")
        return None

    # Update balances locally before broadcasting
    dummy_tx_hash = os.urandom(32).hex()
    dummy_tx = Transaction(
        transaction_data={
            'from_addr': from_addr,
            'to_addr': to_addr,
            'amount': amount,
            'fee': fee
        },
        tx_hash=dummy_tx_hash,
        timestamp=time.time()
    )
    success = global_wallets.update_balances(dummy_tx)
    if not success:
        logger.error("Transaction failed due to insufficient funds.")
        return None

    # Broadcast transaction
    node.broadcast(dummy_tx)
    return dummy_tx

def generate_new_address():
    import os
    # Generate a 64-character hex string as address
    return os.urandom(32).hex()

def list_wallets():
    return list(global_wallets.wallets.keys())

def wallet_exists(address):
    return global_wallets.wallet_exists(address)
