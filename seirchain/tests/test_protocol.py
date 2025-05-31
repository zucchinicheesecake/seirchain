import unittest
from unittest.mock import MagicMock
from seirchain.network.protocol import MessageHandler
from seirchain.data_types import Transaction, Triad

class TestMessageHandler(unittest.TestCase):
    def setUp(self):
        self.node = MagicMock()
        self.ledger = MagicMock()
        self.wallet_manager = MagicMock()
        self.handler = MessageHandler(self.node, self.ledger, self.wallet_manager)

    def test_validate_transaction_valid(self):
        tx = Transaction(
            transaction_data={'from_addr': 'a'*64, 'to_addr': 'b'*64, 'amount': 10, 'fee': 1, 'timestamp': 123},
            tx_hash='txhash',
            timestamp=123
        )
        self.assertTrue(self.handler.validate_transaction(tx))

    def test_validate_transaction_invalid_address(self):
        tx = Transaction(
            transaction_data={'from_addr': 'invalid', 'to_addr': 'b'*64, 'amount': 10, 'fee': 1, 'timestamp': 123},
            tx_hash='txhash',
            timestamp=123
        )
        self.assertFalse(self.handler.validate_transaction(tx))

    def test_validate_triad_valid(self):
        triad = Triad(
            triad_id='triad1',
            depth=1,
            hash_value='0'*5 + 'abc',
            parent_hashes=['parent1']
        )
        self.ledger._triad_map = {'parent1': MagicMock()}
        from seirchain.config import config
        config.DIFFICULTY = 5
        self.assertTrue(self.handler.validate_triad(triad))

    def test_validate_triad_invalid_hash(self):
        triad = Triad(
            triad_id='triad1',
            depth=1,
            hash_value='abc',
            parent_hashes=['parent1']
        )
        self.ledger._triad_map = {'parent1': MagicMock()}
        from seirchain.config import config
        config.DIFFICULTY = 5
        self.assertFalse(self.handler.validate_triad(triad))

    def test_validate_triad_missing_parent(self):
        triad = Triad(
            triad_id='triad1',
            depth=1,
            hash_value='0'*5 + 'abc',
            parent_hashes=['missing_parent']
        )
        self.ledger._triad_map = {}
        from seirchain.config import config
        config.DIFFICULTY = 5
        self.assertFalse(self.handler.validate_triad(triad))

if __name__ == "__main__":
    unittest.main()
