import numpy as np
import random
import time
from collections import defaultdict, deque
import json # For saving/loading history if needed

class Transaction:
    """
    Represents a single transaction in the blockchain.
    Attributes:
        tx_id (str): Unique identifier for the transaction.
        size (int): Conceptual size of the transaction (e.g., data units).
        processing_time (float): Time required to process this transaction in seconds.
        assigned_shard (int): The ID of the shard this transaction is assigned to.
        status (str): Current status of the transaction ("pending", "processing", "completed").
    """
    def __init__(self, tx_id: str, size: int, processing_time: float):
        self.tx_id = tx_id
        self.size = size
        self.processing_time = processing_time
        self.assigned_shard = None
        self.status = "pending"

    def __repr__(self):
        """Provides a string representation of the Transaction object."""
        return (f"Tx(ID={self.tx_id}, Size={self.size}, Time={self.processing_time:.2f}s, "
                f"Shard={self.assigned_shard if self.assigned_shard is not None else 'N/A'}, "
                f"Status={self.status})")

class FractalBlockchainSimulator:
    """
    Simulates the core logic of a fractal blockchain with triangular sharding.
    It focuses on dynamic load balancing and transaction processing to test scalability.
    """
    def __init__(self, num_shards: int):
        """
        Initializes the simulator with a specified number of shards.
        The `num_shards` can be chosen as a power of 3 (e.g., 9, 27, 81)
        to conceptually align with the recursive nature of a Sierpinski triangle.

        Args:
            num_shards (int): The total number of shards in the simulated blockchain.
        """
        if not isinstance(num_shards, int) or num_shards <= 0:
            raise ValueError("Number of shards must be a positive integer.")

        self.num_shards = num_shards
        # shard_states: Mimics Redis for in-memory shard data.
        # Each shard's state includes:
        #   'current_load': Sum of 'processing_time' for all transactions currently in its queue.
        #   'processing_queue': A deque (double-ended queue) of (Transaction object, start_processing_timestamp).
        self.shard_states = defaultdict(lambda: {'current_load': 0.0, 'processing_queue': deque()})
        
        self.total_transactions_processed = 0
        self.start_time = time.time()
        self.transaction_counter = 0 # Unique counter for transaction IDs
        self.shard_load_history = [] # Stores snapshots of shard loads over time
        self.total_transactions_generated = 0 # Track total generated for completion rate

        print(f"Fractal Blockchain Simulator initialized with {self.num_shards} shards.")
        print("Note: Shards are conceptually mapped to a Sierpinski triangle structure.")

    def generate_transactions(self, num_transactions: int):
        """
        Generates a batch of random transactions with varying sizes and processing times.

        Args:
            num_transactions (int): The number of transactions to generate in this batch.

        Returns:
            list[Transaction]: A list of newly created Transaction objects.
        """
        transactions = []
        for _ in range(num_transactions):
            self.transaction_counter += 1
            tx_id = f"TX-{self.transaction_counter:07d}" # Format ID for better readability
            
            # Random transaction size (e.g., 1 to 10 conceptual units)
            size = random.randint(1, 10)
            
            # Random processing time (e.g., 0.01 to 0.2 seconds per transaction)
            # This simulates varying complexity or data volume.
            processing_time = random.uniform(0.01, 0.2)
            
            transactions.append(Transaction(tx_id, size, processing_time))
        self.total_transactions_generated += num_transactions # Update total generated
        return transactions

    def _get_least_loaded_shard(self) -> int:
        """
        Identifies the shard with the lowest current processing load.
        This is the core of the dynamic load balancing strategy.

        Returns:
            int: The ID of the least loaded shard.
        """
        min_load = float('inf')
        least_loaded_shard_id = -1

        # Iterate through all shards to find the one with the minimum current load
        for i in range(self.num_shards):
            load = self.shard_states[i]['current_load']
            if load < min_load:
                min_load = load
                least_loaded_shard_id = i
        return least_loaded_shard_id

    def assign_and_distribute_transactions(self, transactions: list[Transaction], network_latency_ms: float = 0):
        """
        Assigns a list of transactions to shards based on the least loaded shard strategy.
        This simulates the chain coordinator's role in distributing work.

        Args:
            transactions (list[Transaction]): A list of Transaction objects to be assigned.
            network_latency_ms (float): Simulated network delay in milliseconds before assignment.
        """
        if network_latency_ms > 0:
            time.sleep(network_latency_ms / 1000.0) # Convert ms to seconds
            
        for tx in transactions:
            shard_id = self._get_least_loaded_shard()
            tx.assigned_shard = shard_id
            tx.status = "processing" # Mark as processing once assigned and queued
            
            # Add transaction to the shard's processing queue along with its start time
            self.shard_states[shard_id]['processing_queue'].append((tx, time.time()))
            
            # Add its processing time to the shard's current load
            self.shard_states[shard_id]['current_load'] += tx.processing_time
            
            # print(f"Assigned {tx.tx_id} to Shard {shard_id}. Shard {shard_id} Load: {self.shard_states[shard_id]['current_load']:.2f}")

    def process_shards(self):
        """
        Simulates the processing of transactions within each shard.
        Transactions are marked as 'completed' and removed from the queue
        once their simulated processing time has elapsed.
        """
        processed_in_cycle = 0
        current_time = time.time()

        for shard_id in range(self.num_shards):
            shard = self.shard_states[shard_id]
            queue = shard['processing_queue']
            
            # Use a temporary list to store transactions to remove
            completed_transactions = []
            
            # Iterate through the queue to find completed transactions
            # We iterate from the front as transactions are added to the right (append)
            # and processed from the left (popleft).
            while queue and current_time - queue[0][1] >= queue[0][0].processing_time:
                tx, _ = queue.popleft()
                tx.status = "completed"
                shard['current_load'] -= tx.processing_time # Reduce shard load
                self.total_transactions_processed += 1 # Increment global counter
                processed_in_cycle += 1
                completed_transactions.append(tx)
        
        return processed_in_cycle

    def run_simulation(self, duration_seconds: int = 30, initial_transactions: int = 5000, 
                       base_arrival_rate: int = 1000, arrival_rate_std_dev_factor: float = 0.25,
                       network_latency_ms: float = 0): # New parameter for network latency
        """
        Runs the full simulation of the fractal blockchain.

        Args:
            duration_seconds (int): How long the simulation should run in seconds.
            initial_transactions (int): Number of transactions to generate and assign at the start.
            base_arrival_rate (int): Average number of new transactions arriving per second.
            arrival_rate_std_dev_factor (float): Factor for standard deviation of arrival rate
                                                  (e.g., 0.25 means std dev is 25% of base rate).
            network_latency_ms (float): Simulated network delay in milliseconds for transaction assignment.
        """
        print(f"\nStarting simulation for {duration_seconds} seconds...")
        print(f"Initial transactions: {initial_transactions}")
        print(f"Base transaction arrival rate: {base_arrival_rate} transactions/second (with surges)")
        print(f"Simulated Network Latency: {network_latency_ms} ms")

        # Generate and assign initial transaction load
        initial_txs = self.generate_transactions(initial_transactions)
        self.assign_and_distribute_transactions(initial_txs, network_latency_ms) # Pass latency here
        print(f"Generated and assigned {initial_transactions} initial transactions to shards.")

        end_time = time.time() + duration_seconds
        last_report_time = time.time()
        
        # Main simulation loop
        while time.time() < end_time:
            # Simulate new transaction arrivals with random surges using a Gaussian distribution
            # This creates more realistic, varying loads.
            num_new_txs = int(random.gauss(base_arrival_rate, base_arrival_rate * arrival_rate_std_dev_factor))
            if num_new_txs < 0: # Ensure non-negative number of transactions
                num_new_txs = 0
            
            new_txs = self.generate_transactions(num_new_txs)
            self.assign_and_distribute_transactions(new_txs, network_latency_ms) # Pass latency here

            # Process transactions across all shards
            self.process_shards()

            # Report TPS and shard loads periodically
            if time.time() - last_report_time >= 1: # Report every second
                elapsed = time.time() - self.start_time
                current_tps = self.total_transactions_processed / elapsed if elapsed > 0 else 0
                
                print(f"\n--- Time: {elapsed:.1f}s ---")
                print(f"Total Transactions Processed: {self.total_transactions_processed}")
                print(f"Current Average TPS: {current_tps:.2f}")
                
                # Capture shard load snapshot for history
                shard_snapshot = {
                    'timestamp': elapsed,
                    'shard_data': {}
                }
                for i in range(self.num_shards):
                    load = self.shard_states[i]['current_load']
                    queue_size = len(self.shard_states[i]['processing_queue'])
                    shard_snapshot['shard_data'][f'shard_{i}'] = {'load': load, 'queue_size': queue_size}
                    # print(f"  Shard {i:02d}: Load={load:.2f}s, Queue Size={queue_size} transactions") # Uncomment for verbose output
                self.shard_load_history.append(shard_snapshot)
                
                last_report_time = time.time()
            
            # Small sleep to control simulation speed and prevent busy-waiting
            time.sleep(0.005) # Adjusted back to 0.005

        # --- Final processing to clear queues at the end of simulation ---
        print("\nFinalizing transaction processing...")
        grace_period_start = time.time()
        max_grace_period = 2.0 # seconds
        
        while True:
            processed_count = self.process_shards()
            if processed_count == 0:
                all_queues_empty = True
                for shard_id in range(self.num_shards):
                    if self.shard_states[shard_id]['processing_queue']:
                        all_queues_empty = False
                        break
                if all_queues_empty:
                    break
                
                time.sleep(0.01)
                if time.time() - grace_period_start > max_grace_period:
                    print(f"Grace period exceeded, stopping final processing.")
                    break
            else:
                grace_period_start = time.time()
            
            time.sleep(0.001)

        # Final report after simulation concludes
        self.final_elapsed = time.time() - self.start_time
        self.final_tps = self.total_transactions_processed / self.final_elapsed if self.final_elapsed > 0 else 0
        print(f"\n--- Simulation Finished ---")
        print(f"Final Total Transactions Processed: {self.total_transactions_processed}")
        print(f"Final Total Transactions Generated: {self.total_transactions_generated}")
        print(f"Final Total Simulation Time: {self.final_elapsed:.2f} seconds")
        print(f"Final Average TPS: {self.final_tps:.2f}")

# --- How to Run the Simulation (for manual testing) ---
if __name__ == "__main__":
    NUM_SHARDS = 27 

    simulator = FractalBlockchainSimulator(num_shards=NUM_SHARDS)

    simulator.run_simulation(
        duration_seconds=60,         
        initial_transactions=10000,  
        base_arrival_rate=15000,     
        arrival_rate_std_dev_factor=0.3,
        network_latency_ms=50 # Example: 50ms network latency
    )

    # You can now access simulator.shard_load_history for detailed analysis.
    # with open('shard_load_history.json', 'w') as f:
    #     json.dump(simulator.shard_load_history, f, indent=4)

