# seirchain/config.py
import json
import os

class Config:
    """
    Manages the simulation's configuration.
    Implemented as a Singleton to ensure all parts of the application
    use the same configuration.
    """
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.DIFFICULTY = 4 # Default mining difficulty (number of leading zeros)
            self.MAX_DEPTH = 8 # Maximum depth of the Triad Matrix
            self.MINING_REWARD = 10.0 # Reward for mining a Triad
            self.TRANSACTION_FEE = 0.05 # Fee per transaction
            self.MAX_TRANSACTIONS_TO_SIMULATE = 20 # Default number of transactions for simulation
            # Note: More config parameters can be added here as needed (e.g., node count, etc.)

            self._initialized = True

    @classmethod
    def instance(cls):
        """Returns the singleton instance of Config."""
        if cls._instance is None:
            cls() # This calls __init__
        return cls._instance

    def load_config(self, network="mainnet"):
        """
        Loads configuration from a JSON file based on the network name.
        Allows overriding default values.
        """
        config_file = f"config_{network}.json"
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', config_file)

        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config_data = json.load(f)
                
                # Update instance attributes with values from the config file
                self.DIFFICULTY = config_data.get('DIFFICULTY', self.DIFFICULTY)
                self.MAX_DEPTH = config_data.get('MAX_DEPTH', self.MAX_DEPTH)
                self.MINING_REWARD = config_data.get('MINING_REWARD', self.MINING_REWARD)
                self.TRANSACTION_FEE = config_data.get('TRANSACTION_FEE', self.TRANSACTION_FEE)
                self.MAX_TRANSACTIONS_TO_SIMULATE = config_data.get('MAX_TRANSACTIONS_TO_SIMULATE', self.MAX_TRANSACTIONS_TO_SIMULATE)

                print(f"Configuration loaded from {config_file}.")
        else:
            print(f"Warning: Config file '{config_file}' not found. Using default configurations.")

    def to_dict(self):
        """Returns the current configuration as a dictionary."""
        return {
            "DIFFICULTY": self.DIFFICULTY,
            "MAX_DEPTH": self.MAX_DEPTH,
            "MINING_REWARD": self.MINING_REWARD,
            "TRANSACTION_FEE": self.TRANSACTION_FEE,
            "MAX_TRANSACTIONS_TO_SIMULATE": self.MAX_TRANSACTIONS_TO_SIMULATE
        }

