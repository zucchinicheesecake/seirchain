import hashlib
import time
from seirchain.data_types.triad import Triad
from seirchain.data_types.transaction import Transaction
from seirchain.config import Config # Import the Config class
import random

class Miner:
    """
    Handles the mining process for the SeirChain.
    This includes creating new triads, adding transactions,
    and finding a valid nonce through proof-of-work.
    """

    def __init__(self):
        self.config = Config.instance() # Get the Config instance
        self.difficulty = self.config.DIFFICULTY  # Use difficulty from Config
        self.mining_reward = self.config.MINING_REWARD # Mining reward from config

    def create_genesis_triad(self, genesis_transactions):
         """
         Creates the genesis triad. This is the first triad in the chain
         and has no parent.
         """
         return Triad(
             parent_hashes=[],
             transactions=genesis_transactions,
             difficulty=self.difficulty,
             nonce=0,  # Genesis block has a fixed nonce (can be 0)
             timestamp=time.time(),
             triad_hash="0"  # Genesis block has a predefined hash for simplicity
         )

    def mine_triad(self, parent_hashes, transactions):
        """
        Mines a new triad by finding a nonce that satisfies the difficulty.
        """
        triad = Triad(parent_hashes, transactions, self.difficulty)
        while not self.is_valid_hash(triad.calculate_hash()):
            triad.nonce += 1
            triad.timestamp = time.time()  # Update timestamp for each attempt
            triad.triad_hash = triad.calculate_hash() # Recalculate hash after changing nonce/timestamp
        print(f"Mined triad with hash: {triad.triad_hash} and nonce: {triad.nonce}")
        return triad

    def is_valid_hash(self, triad_hash):
        """Checks if a triad's hash meets the difficulty criteria."""
        prefix = '0' * self.difficulty
        return triad_hash.startswith(prefix)

    def add_mining_reward_transaction(self, miner_address):
        """Creates a transaction to reward the miner."""
        # Ensure the miner_address is not None
        if not miner_address:
            raise ValueError("Miner address cannot be None")

        reward_transaction = Transaction(
            sender="GENESIS_MINE_WALLET", # Use the genesis wallet as the sender
            receiver=miner_address,
            amount=self.mining_reward,
            fee=0.0  # No fee for mining reward
        )
        return reward_transaction

    def select_transactions_for_triad(self, pending_transactions, max_transactions):
        """Selects transactions for inclusion in a new triad, up to a maximum."""
        # Shuffle transactions to avoid bias
        random.shuffle(pending_transactions)
        return pending_transactions[:max_transactions]

    def process_transactions(self, wallets, transactions, transaction_fee):
        """Processes transactions, verifying balances and applying fees."""
        valid_transactions = []
        for tx in transactions:
            if wallets.process_transaction(tx.sender, tx.receiver, tx.amount, transaction_fee):
                valid_transactions.append(tx)
        return valid_transactions
