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
        # Check that threads are running and thread_states are updated
        self.assertTrue(any(thread.is_alive() for thread in self.miner.threads))
        self.assertTrue(all(state == "running" for state in self.miner.thread_states.values()))
        self.miner.stop()
        # After stop, threads list should be empty and thread_states cleared
        self.assertEqual(len(self.miner.threads), 0)
        self.assertEqual(len(self.miner.thread_states), 0)

    def test_thread_states_transitions(self):
        self.miner.start()
        # Initially, all threads should be running
        for state in self.miner.thread_states.values():
            self.assertEqual(state, "running")
        self.miner.stop()
        # After stop, all threads should be stopped or thread_states cleared
        self.assertEqual(len(self.miner.thread_states), 0)

    def test_metrics_properties_and_methods(self):
        # Reset metrics first
        self.miner.reset_metrics()
        self.assertEqual(self.miner.hashes_computed, 0)
        self.assertEqual(self.miner.successful_mines, 0)
        self.assertEqual(self.miner.total_mining_time, 0.0)

        # Simulate some mining activity
        self.miner.hashes_computed = 100
        self.miner.successful_mines = 5
        self.miner.total_mining_time = 123.45

        metrics = self.miner.metrics
        self.assertEqual(metrics["hashes_computed"], 100)
        self.assertEqual(metrics["successful_mines"], 5)
        self.assertAlmostEqual(metrics["total_mining_time"], 123.45)

        # Test log_metrics method (just ensure it runs without error)
        self.miner.log_metrics()

    def test_add_transaction_to_pool_validation_and_deduplication(self):
        # Create a valid transaction
        tx_data = {
            'from_addr': 'addr1',
            'to_addr': 'addr2',
            'amount': 10,
            'fee': 0.1,
            'timestamp': time.time(),
            'signature': 'sig'
        }
        tx = Transaction(transaction_data=tx_data, tx_hash='hash1', timestamp=time.time())

        # Add transaction to pool
        self.miner.add_transaction_to_pool(tx)
        self.assertIn(tx, self.miner.ledger.transaction_pool)

        # Add duplicate transaction (same tx_hash)
        duplicate_tx = Transaction(transaction_data=tx_data, tx_hash='hash1', timestamp=time.time())
        self.miner.add_transaction_to_pool(duplicate_tx)
        # Pool should not have duplicate
        tx_hashes = [t.tx_hash for t in self.miner.ledger.transaction_pool]
        self.assertEqual(tx_hashes.count('hash1'), 1)

        # Add invalid transaction (missing amount)
        invalid_tx_data = {
            'from_addr': 'addr1',
            'to_addr': 'addr2',
            'fee': 0.1,
            'timestamp': time.time(),
            'signature': 'sig'
        }
        invalid_tx = Transaction(transaction_data=invalid_tx_data, tx_hash='hash2', timestamp=time.time())
        self.miner.add_transaction_to_pool(invalid_tx)
        # Pool should not contain invalid transaction
        tx_hashes = [t.tx_hash for t in self.miner.ledger.transaction_pool]
        self.assertNotIn('hash2', tx_hashes)

if __name__ == "__main__":
    unittest.main()
