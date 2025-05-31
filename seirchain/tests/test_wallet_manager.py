import unittest
from seirchain.wallet_manager import WalletManager, Wallet, Transaction

class TestWalletManager(unittest.TestCase):
    def setUp(self):
        self.manager = WalletManager()

    def test_add_and_get_wallet(self):
        address = "a"*64
        wallet = self.manager.add_wallet(address, 100)
        self.assertEqual(wallet.address, address)
        self.assertEqual(wallet.balance, 100)
        fetched_wallet = self.manager.get_wallet(address)
        self.assertEqual(fetched_wallet, wallet)

    def test_update_balance(self):
        address = "b"*64
        wallet = self.manager.add_wallet(address, 50)
        wallet.update_balance(25)
        self.assertEqual(wallet.balance, 75)
        with self.assertRaises(ValueError):
            wallet.update_balance(-100)  # Should raise due to insufficient funds

    def test_update_balances_transaction(self):
        from_addr = "c"*64
        to_addr = "d"*64
        self.manager.add_wallet(from_addr, 100)
        self.manager.add_wallet(to_addr, 0)
        tx = Transaction(
            transaction_data={'from_addr': from_addr, 'to_addr': to_addr, 'amount': 30, 'fee': 1},
            tx_hash="txhash1",
            timestamp=0
        )
        result = self.manager.update_balances(tx)
        self.assertTrue(result)
        self.assertEqual(self.manager.get_wallet(from_addr).balance, 69)  # 100 - 30 - 1
        self.assertEqual(self.manager.get_wallet(to_addr).balance, 30)

    def test_invalid_address(self):
        with self.assertRaises(ValueError):
            self.manager.add_wallet("invalid_address")

if __name__ == "__main__":
    unittest.main()
