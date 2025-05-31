import unittest
from seirchain.data_types import Triad, Transaction
from seirchain.triangular_ledger.triangular_ledger import TriangularLedger

class TestTriangularLedger(unittest.TestCase):
    def setUp(self):
        self.ledger = TriangularLedger(max_depth=10)

    def test_add_genesis_triad(self):
        genesis = Triad(triad_id='genesis', depth=0, hash_value='0'*5, parent_hashes=[])
        result = self.ledger.add_triad(genesis)
        self.assertTrue(result)
        self.assertEqual(self.ledger.genesis_triad, genesis)

    def test_add_triad_with_parent(self):
        genesis = Triad(triad_id='genesis', depth=0, hash_value='0'*5, parent_hashes=[])
        self.ledger.add_triad(genesis)
        child = Triad(triad_id='child', depth=1, hash_value='0'*5, parent_hashes=['genesis'])
        result = self.ledger.add_triad(child)
        self.assertTrue(result)
        self.assertIn('child', self.ledger._triad_map)
        self.assertIn('child', genesis.children)

    def test_add_transaction_thread_safe(self):
        tx = Transaction(transaction_data={}, tx_hash='tx1', timestamp=0)
        self.ledger.add_transaction(tx)
        self.assertIn(tx, self.ledger.transaction_pool)

    def test_get_current_tip_triad_hashes(self):
        genesis = Triad(triad_id='genesis', depth=0, hash_value='0'*5, parent_hashes=[])
        self.ledger.add_triad(genesis)
        child1 = Triad(triad_id='child1', depth=1, hash_value='0'*5, parent_hashes=['genesis'])
        child2 = Triad(triad_id='child2', depth=1, hash_value='0'*5, parent_hashes=['genesis'])
        self.ledger.add_triad(child1)
        self.ledger.add_triad(child2)
        tips = self.ledger.get_current_tip_triad_hashes()
        self.assertIn('child1', tips)
        self.assertIn('child2', tips)
        self.assertNotIn('genesis', tips)

if __name__ == "__main__":
    unittest.main()
