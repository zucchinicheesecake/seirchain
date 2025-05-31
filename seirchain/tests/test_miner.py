import unittest
from unittest.mock import MagicMock, patch
from seirchain.miner import Miner
from seirchain.data_types.base import Triad, Triangle

class TestMiner(unittest.TestCase):
    def setUp(self):
        self.ledger = MagicMock()
        self.node = MagicMock()
        self.wallet_manager = MagicMock()
        self.miner = Miner(self.ledger, self.node, self.wallet_manager, miner_address="miner1", num_threads=1)

    def test_create_reward_transaction(self):
        reward_tx = self.miner.create_reward_transaction()
        self.assertEqual(reward_tx.transaction_data['to_addr'], "miner1")
        self.assertEqual(reward_tx.transaction_data['amount'], self.miner.wallet_manager.config.MINING_REWARD if hasattr(self.miner.wallet_manager, 'config') else None)

    @patch('seirchain.miner.time')
    def test_calculate_fractal_hash(self, mock_time):
        triad = Triad(triad_id='id', depth=1, hash_value='hash', parent_hashes=[])
        tri_node = Triangle(triad)
        tri_node.transactions = []
        hash_val = self.miner.calculate_fractal_hash(tri_node, nonce=0)
        self.assertIsInstance(hash_val, str)
        self.assertEqual(len(hash_val), 64)  # SHA256 hex length

    def test_start_and_stop(self):
        self.miner.start()
        self.assertTrue(self.miner.mining)
        self.miner.stop()
        self.assertFalse(self.miner.mining)

if __name__ == "__main__":
    unittest.main()
