import unittest
from seirchain.data_types import Triad, Transaction
from seirchain.triangular_ledger.triangle import Triangle

class TestTriangle(unittest.TestCase):
    def setUp(self):
        triad = Triad(triad_id='triad1', depth=1, hash_value='hash', parent_hashes=[])
        self.triangle = Triangle(triad, coordinates=(1, 2))

    def test_add_and_get_transactions(self):
        tx1 = Transaction(transaction_data={}, tx_hash='tx1', timestamp=0)
        tx2 = Transaction(transaction_data={}, tx_hash='tx2', timestamp=0)
        self.triangle.add_transaction(tx1)
        self.triangle.add_transaction(tx2)
        transactions = self.triangle.get_transactions()
        self.assertIn(tx1, transactions)
        self.assertIn(tx2, transactions)

    def test_add_child(self):
        child_triad = Triad(triad_id='child', depth=2, hash_value='hash2', parent_hashes=['triad1'])
        child_triangle = Triangle(child_triad, coordinates=(2, 3))
        self.triangle.add_child(child_triangle)
        self.assertIn(child_triangle, self.triangle.children)

    def test_fractal_position(self):
        pos = self.triangle.fractal_position(depth=3)
        self.assertEqual(pos, (1 * 8, 2 * 8))

if __name__ == "__main__":
    unittest.main()
