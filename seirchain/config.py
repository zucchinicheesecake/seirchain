import json
import os

class Config:
    """
    Manages global configuration settings for the blockchain network.
    Implemented as a Singleton.
    """
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.DIFFICULTY = 0          # Number of leading zeros required for proof-of-work
            self.MAX_DEPTH = 0           # Max depth for ledger/chain
            self.MINING_REWARD = 0.0     # Reward for mining a block
            self.TRANSACTION_FEE = 0.0   # Fee for a transaction
            self._initialized = True

    @classmethod
    def instance(cls):
        """Returns the singleton instance of Config."""
        if cls._instance is None:
            cls() # This ensures __init__ is called only once for the singleton
        return cls._instance

    def load_config(self, network_name):
        """
        Loads configuration from a JSON file for the specified network.
        If the file doesn't exist or there's an error, it uses default values.
        """
        config_file = f"config_{network_name}.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    self.DIFFICULTY = data.get('difficulty', 4)
                    self.MAX_DEPTH = data.get('max_depth', 8)
                    self.MINING_REWARD = data.get('mining_reward', 10.0)
                    self.TRANSACTION_FEE = data.get('transaction_fee', 0.05)
                print(f"Configuration loaded from {config_file}.")
            except Exception as e:
                print(f"Error loading config from {config_file}: {e}. Using default values.")
                self._set_default_config() # Set program defaults if file loading fails
        else:
            print(f"No existing config file found at {config_file}. Initializing with default values.")
            self._set_default_config() # Set program defaults if file doesn't exist

        # Ensure a config file is always saved after loading/initializing
        self._save_config(network_name)

    def _set_default_config(self):
        """Internal method to set predefined default configuration values."""
        self.DIFFICULTY = 4
        self.MAX_DEPTH = 8
        self.MINING_REWARD = 10.0
        self.TRANSACTION_FEE = 0.05

    def _save_config(self, network_name):
        """Internal method to save the current configuration to a JSON file."""
        config_file = f"config_{network_name}.json"
        data = {
            'difficulty': self.DIFFICULTY,
            'max_depth': self.MAX_DEPTH,
            'mining_reward': self.MINING_REWARD,
            'transaction_fee': self.TRANSACTION_FEE
        }
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=2)
