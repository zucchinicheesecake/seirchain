from protocol.tokenomics import *
from protocol.difficulty import *
from protocol.burn_mechanism import *
from protocol.liquidity_vault import *

def main():
    print("Sierpiński Mathematical Liquidity Protocol")
    print("=" * 50)
    
    while True:
        print("\n[1] Calculate Token Metrics")
        print("[2] Determine Commitment Tier")
        print("[3] Simulate Mining Operation")
        print("[4] Calculate Burn Amounts")
        print("[5] Exit")
        
        choice = input("\nSelect an option: ")
        
        if choice == "1":
            depth = int(input("Enter depth (n): "))
            print(f"\nToken Supply at Depth {depth}: {calculate_supply(depth):,.2f} WŁA")
            print(f"Mining Units at Depth {depth}: {calculate_mining_units(depth):,}")
            print(f"Token Density: {calculate_token_density(depth):.8f} WŁA/unit")
            print(f"Scarcity Index: {calculate_scarcity_index(depth):,.2f}")
            print(f"Mining Difficulty: {calculate_difficulty(depth):,.2f}")
            
        elif choice == "2":
            usdt = float(input("Enter USDT commitment amount: "))
            tier = get_commitment_tier(usdt)
            print(f"\nCommitment Tier: {tier['tier']}")
            print(f"Access Depth: Up to {tier['access_depth']}")
            print(f"Reward Multiplier: {tier['multiplier']}x")
            
        elif choice == "3":
            depth = int(input("Enter mining depth (n): "))
            usdt = float(input("Enter USDT commitment: "))
            
            if not validate_minimum_commitment(usdt):
                print("Error: Minimum commitment is 13.01 USDT")
                continue
                
            tier = get_commitment_tier(usdt)
            
            if depth > tier['access_depth']:
                print(f"Error: Insufficient commitment for depth {depth}")
                print(f"Your commitment allows access up to depth {tier['access_depth']}")
                continue
                
            difficulty = calculate_difficulty(depth)
            reward = calculate_token_density(depth) * tier['multiplier']
            
            print(f"\nMining Parameters at Depth {depth}:")
            print(f"Difficulty: {difficulty:,.2f}")
            print(f"Base Reward: {calculate_token_density(depth):.8f} WŁA")
            print(f"Multiplied Reward: {reward:.8f} WŁA")
            
        elif choice == "4":
            tx_amount = float(input("Enter transaction amount (WŁA): "))
            depth = int(input("Enter current depth: "))
            
            tx_burn = calculate_transaction_burn(tx_amount)
            depth_tax = calculate_depth_tax_burn(depth)
            
            print(f"\nBurn Amounts:")
            print(f"Transaction Fee Burn: {tx_burn:.6f} WŁA")
            print(f"Progressive Depth Tax: {depth_tax:.6f} WŁA")
            
        elif choice == "5":
            print("Exiting SMLP Protocol")
            break
            
        else:
            print("Invalid selection. Please try again.")

if __name__ == "__main__":
    main()
