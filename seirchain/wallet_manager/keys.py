import hashlib
import time

class Wallet:
    """Represents a simple wallet with an address and balance."""
    def __init__(self, address: str = None, initial_balance: float = 0.0):
        self.address = address if address else self._generate_address()
        self.balance = initial_balance

    def _generate_address(self) -> str:
        """Generates a simple, unique wallet address (e.g., a hash of a timestamp)."""
        # In a real blockchain, this would involve public key derivation.
        return hashlib.sha256(str(time.time()).encode()).hexdigest()

    def __repr__(self):
        return f"Wallet(Address: {self.address[:10]}..., Balance: {self.balance:.2f})"

