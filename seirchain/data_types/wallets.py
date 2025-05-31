class WalletManager:
    def __init__(self):
        self.wallets = {}
        
    def add_wallet(self, address, wallet):
        self.wallets[address] = wallet
        
    def get_balance(self, address):
        return self.wallets.get(address, {}).get('balance', 0)
        
# Global instance
wallets = WalletManager()
