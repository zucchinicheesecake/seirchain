import json
import os
import time
from seirchain.data_types import Transaction

class Wallet:
    def __init__(self, address, balance=0.0, public_key=None):
        self.address = address
        self.balance = balance
        self.public_key = public_key
        self.transaction_history = []
        
    def update_balance(self, delta):
        self.balance += delta
        
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
        if address not in self.wallets:
            self.wallets[address] = Wallet(address)
        return self.wallets[address]
    
    def add_wallet(self, address, initial_balance=0.0):
        """Explicitly add a wallet (if not already exists)"""
        if address not in self.wallets:
            self.wallets[address] = Wallet(address, initial_balance)
        return self.wallets[address]
    
    def wallet_exists(self, address):
        return address in self.wallets
    
    def update_balances(self, transaction):
        sender = self.get_wallet(transaction.from_addr)
        receiver = self.get_wallet(transaction.to_addr)
        
        # Update balances
        sender.update_balance(-transaction.amount - transaction.fee)
        receiver.update_balance(transaction.amount)
        
        # Record transaction
        sender.add_transaction(transaction.tx_hash)
        receiver.add_transaction(transaction.tx_hash)
        
    def load_wallets(self, network):
        """Load wallets from JSON file"""
        filename = f"data/wallets_{network}.json"
        if not os.path.exists(filename):
            return
            
        with open(filename, 'r') as f:
            wallets_data = json.load(f)
            for addr, data in wallets_data.items():
                self.wallets[addr] = Wallet.from_dict(data)
                
    def save_wallets(self, network):
        """Save wallets to JSON file"""
        wallets_data = {addr: wallet.to_dict() for addr, wallet in self.wallets.items()}
        filename = f"data/wallets_{network}.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(wallets_data, f, indent=2)
        
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

def send_transaction(from_addr, to_addr, amount, fee):
    from seirchain.network import node
    tx = Transaction(
        transaction_data={
            'from_addr': from_addr,
            'to_addr': to_addr,
            'amount': amount,
            'fee': fee
        },
        tx_hash=os.urandom(32).hex(),
        timestamp=time.time()
    )
    node.broadcast(tx)
    return tx

def generate_new_address():
    import os
    return os.urandom(32).hex()

def list_wallets():
    return list(global_wallets.wallets.keys())

def wallet_exists(address):
    return global_wallets.wallet_exists(address)
