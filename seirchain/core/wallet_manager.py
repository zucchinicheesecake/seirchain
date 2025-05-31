import json
import os
import time
import logging
from seirchain.data_types import Transaction

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Wallet:
    """
    Represents a wallet with an address, balance, public key, and transaction history.
    """
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
    """
    Manages multiple wallets, providing methods to get, add, update, and save wallets.
    """
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
        if not self._is_valid_address(address):
            raise ValueError(f"Invalid wallet address: {address}")
        if address not in self.wallets:
            self.wallets[address] = Wallet(address, initial_balance)
        return self.wallets[address]

    def wallet_exists(self, address):
        return address in self.wallets

    def update_balances(self, transaction):
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
            from_addr = transaction.transaction_data.get('from_addr')
            to_addr = transaction.transaction_data.get('to_addr')
            amount = transaction.transaction_data.get('amount')
            fee = transaction.transaction_data.get('fee')

        zero_address_64 = "0" * 64
        if len(from_addr) == 40:
            from_addr = from_addr.rjust(64, '0')
        if from_addr.strip() == zero_address_64:
            receiver = self.get_wallet(to_addr)
            try:
                receiver.update_balance(amount)
            except ValueError as e:
                logger.error(f"Balance update error: {e}")
                return False
            receiver.add_transaction(transaction.tx_hash)
            return True

        sender = self.get_wallet(from_addr)
        receiver = self.get_wallet(to_addr)

        try:
            sender.update_balance(-amount - fee)
            receiver.update_balance(amount)
        except ValueError as e:
            logger.error(f"Balance update error: {e}")
            return False

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
        try:
            sender = self.get_wallet(from_addr)
            receiver = self.get_wallet(to_addr)
            sender.update_balance(-amount - fee)
            receiver.update_balance(amount)
            return True
        except ValueError as e:
            logger.error(f"Transfer funds error: {e}")
            return False

    def load_wallets(self, network):
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


global_wallets = WalletManager()

def create_wallet(address, initial_balance=0.0):
    return global_wallets.add_wallet(address, initial_balance)

def get_balance(address):
    wallet = global_wallets.get_wallet(address)
    return wallet.balance

def get_wallet(address):
    return global_wallets.get_wallet(address)

def send_transaction(from_addr, to_addr, amount, fee):
    from seirchain.network import node
    if not global_wallets._is_valid_address(from_addr):
        logger.error(f"Invalid from_addr: {from_addr}")
        return None
    if not global_wallets._is_valid_address(to_addr):
        logger.error(f"Invalid to_addr: {to_addr}")
        return None
    if amount <= 0 or fee < 0:
        logger.error(f"Invalid amount or fee: amount={amount}, fee={fee}")
        return None

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

    node.broadcast(dummy_tx)
    return dummy_tx

def generate_new_address():
    import os
    return os.urandom(32).hex()

def list_wallets():
    return list(global_wallets.wallets.keys())

def wallet_exists(address):
    return global_wallets.wallet_exists(address)
</create_file>
