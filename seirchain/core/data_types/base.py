from dataclasses import dataclass, field
from typing import List, Tuple, Any, Optional
import hashlib

@dataclass(frozen=True)
class Triad:
    triad_id: str
    depth: int
    hash_value: str
    parent_hashes: List[str]
    child_hashes: List[str] = field(default_factory=list)

    def add_child(self, child_triad: 'Triad') -> 'Triad':
        # Since frozen, return a new instance with updated child_hashes
        new_child_hashes = self.child_hashes + [child_triad.hash_value]
        return Triad(
            triad_id=self.triad_id,
            depth=self.depth,
            hash_value=self.hash_value,
            parent_hashes=self.parent_hashes,
            child_hashes=new_child_hashes
        )

    def to_dict(self) -> dict:
        return {
            'triad_id': self.triad_id,
            'depth': self.depth,
            'hash_value': self.hash_value,
            'parent_hashes': self.parent_hashes,
            'child_hashes': self.child_hashes
        }

    @classmethod
    def from_dict(cls, data: dict) -> Optional['Triad']:
        try:
            triad_id = data['triad_id']
            depth = data['depth']
            hash_value = data['hash_value']
            parent_hashes = data['parent_hashes']
            child_hashes = data.get('child_hashes', [])
            # Validation
            if not isinstance(triad_id, str) or not isinstance(depth, int) or depth < 0:
                return None
            if not isinstance(hash_value, str) or not all(isinstance(h, str) for h in parent_hashes):
                return None
            if not all(isinstance(h, str) for h in child_hashes):
                return None
            # Validate hash format (hex and length 64)
            if len(hash_value) != 64 or not all(c in '0123456789abcdef' for c in hash_value.lower()):
                return None
            return cls(triad_id, depth, hash_value, parent_hashes, child_hashes)
        except (KeyError, TypeError):
            return None

    def __repr__(self):
        return f"Triad(id={self.triad_id[:8]}, depth={self.depth})"

    def __eq__(self, other):
        if not isinstance(other, Triad):
            return False
        return (self.triad_id == other.triad_id and
                self.depth == other.depth and
                self.hash_value == other.hash_value and
                self.parent_hashes == other.parent_hashes and
                self.child_hashes == other.child_hashes)

    def __hash__(self):
        return hash((self.triad_id, self.depth, self.hash_value, tuple(self.parent_hashes), tuple(self.child_hashes)))

@dataclass(frozen=True)
class Transaction:
    transaction_data: dict
    tx_hash: str
    timestamp: float

    def to_dict(self) -> dict:
        return {
            'transaction_data': self.transaction_data,
            'tx_hash': self.tx_hash,
            'timestamp': self.timestamp
        }

    @classmethod
    def from_dict(cls, data: dict) -> Optional['Transaction']:
        try:
            transaction_data = data['transaction_data']
            tx_hash = data['tx_hash']
            timestamp = data['timestamp']
            # Validate types
            if not isinstance(transaction_data, dict):
                return None
            if not isinstance(tx_hash, str) or len(tx_hash) != 64 or not all(c in '0123456789abcdef' for c in tx_hash.lower()):
                return None
            if not isinstance(timestamp, (int, float)):
                return None
            return cls(transaction_data, tx_hash, timestamp)
        except (KeyError, TypeError):
            return None

    def __repr__(self):
        return f"Transaction(hash={self.tx_hash[:8]})"

    def __eq__(self, other):
        if not isinstance(other, Transaction):
            return False
        return (self.transaction_data == other.transaction_data and
                self.tx_hash == other.tx_hash and
                self.timestamp == other.timestamp)

    def __hash__(self):
        return hash((frozenset(self.transaction_data.items()), self.tx_hash, self.timestamp))

@dataclass
class Triangle:
    triad: Triad
    coordinates: Tuple[int, int]
    transactions: List[Any] = field(default_factory=list)

    def add_transaction(self, transaction: Any) -> None:
        self.transactions.append(transaction)

    def get_transactions(self) -> List[Any]:
        return self.transactions

    def get_hash(self) -> str:
        return self.triad.hash_value

    def __repr__(self) -> str:
        return f"Triangle(triad={self.triad}, trans={len(self.transactions)})"
