import matplotlib.pyplot as plt
import numpy as np
from protocol.tokenomics import *
from protocol.difficulty import *
from protocol.burn_mechanism import *
from protocol.liquidity_vault import *

def run_economic_simulation():
    print("Sierpiński Mathematical Liquidity Protocol Simulation")
    print("=" * 60)
    
    # Initialize simulation parameters
    depths = np.arange(0, 21)
    years = np.array([1, 2, 3, 5])
    initial_vault = 1000000  # 1M USDT
    
    # Table 3.1: Supply-Complexity Relationship
    print("\nTable 3.1: Supply-Complexity Relationship Analysis")
    print("-" * 90)
    print("| Depth | Supply (WŁA) | Triangles | Density (WŁA/triangle) | Difficulty | Scarcity Index |")
    print("|-------|--------------|-----------|-------------------------|------------|----------------|")
    
    for n in depths:
        supply = calculate_supply(n)
        triangles = calculate_mining_units(n)
        density = calculate_token_density(n)
        difficulty = calculate_difficulty(n)
        scarcity = calculate_scarcity_index(n)
        
        print(f"| {n:5} | {supply:12.2f} | {triangles:9} | {density:23.6f} | {difficulty:10.2f} | {scarcity:14.2f} |")
    
    # Table 3.2: Commitment Tier Structure
    print("\n\nTable 3.2: Commitment Tier Structure")
    print("-" * 90)
    print("| USDT Range       | Access Depth | Multiplier | Tier               |")
    print("|------------------|--------------|------------|--------------------|")
    
    tiers = [
        (10.00, "Insufficient"),
        (13.01, "Entry"),
        (50.00, "Entry"),
        (100.00, "Moderate"),
        (500.00, "Moderate"),
        (1000.00, "Significant"),
        (5000.00, "Significant"),
        (10000.00, "Institutional"),
        (50000.00, "Institutional")
    ]
    
    for amount, tier_name in tiers:
        tier = get_commitment_tier(amount)
        print(f"| {amount:16.2f} | {tier['access_depth']:12} | {tier['multiplier']:10.2f}x | {tier['tier']:18} |")
    
    # Table 4.1: Economic Timeline Projections
    print("\n\nTable 4.1: Economic Timeline Projections")
    print("-" * 90)
    print("| Year | Depth Range | Supply Range (WŁA) | Reduction % | Market Cap Multiplier |")
    print("|------|-------------|---------------------|-------------|------------------------|")
    
    year_depths = [(1, (0, 5)), (2, (5, 10)), (3, (10, 15)), (5, (15, 20))]
    for year, (start, end) in year_depths:
        start_supply = calculate_supply(start)
        end_supply = calculate_supply(end)
        reduction = 100 * (1 - end_supply / GENESIS_SUPPLY)
        multiplier = calculate_scarcity_index(end)
        
        print(f"| {year:4} | {start}-{end:7} | {start_supply/1e6:.1f}M-{end_supply/1e6:.1f}M | {reduction:10.1f}% | {multiplier:21.1f}x |")
    
    # Vault growth simulation
    print("\n\nLiquidity Vault Growth Projection (Initial = 1M USDT)")
    print("-" * 90)
    print("| Month | Vault Size (USDT) | Growth Rate |")
    print("|-------|-------------------|-------------|")
    
    for month in range(0, 37, 6):
        vault = calculate_vault_growth(initial_vault, month)
        growth_rate = (vault / initial_vault - 1) * 100
        print(f"| {month:5} | {vault:17.2f} | {growth_rate:10.2f}% |")
    
    # Generate plots
    plt.figure(figsize=(15, 10))
    
    # Supply vs Depth
    plt.subplot(2, 2, 1)
    supplies = [calculate_supply(n) for n in depths]
    plt.semilogy(depths, supplies, 'b-o')
    plt.title('Token Supply vs Depth (Log Scale)')
    plt.xlabel('Depth (n)')
    plt.ylabel('Supply (WŁA)')
    plt.grid(True, which="both", ls="-")
    
    # Difficulty vs Depth
    plt.subplot(2, 2, 2)
    difficulties = [calculate_difficulty(n) for n in depths]
    plt.semilogy(depths, difficulties, 'r-o')
    plt.title('Mining Difficulty vs Depth')
    plt.xlabel('Depth (n)')
    plt.ylabel('Difficulty')
    plt.grid(True, which="both", ls="-")
    
    # Scarcity Index vs Depth
    plt.subplot(2, 2, 3)
    scarcities = [calculate_scarcity_index(n) for n in depths]
    plt.plot(depths, scarcities, 'g-o')
    plt.title('Scarcity Index vs Depth')
    plt.xlabel('Depth (n)')
    plt.ylabel('Scarcity Index (S₀/S(n))')
    plt.grid(True)
    
    # Vault Growth Projection
    plt.subplot(2, 2, 4)
    months = np.arange(0, 37)
    vaults = [calculate_vault_growth(initial_vault, m) for m in months]
    plt.plot(months, vaults, 'm-o')
    plt.title('Liquidity Vault Growth Projection')
    plt.xlabel('Months')
    plt.ylabel('Vault Size (USDT)')
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig('smlp_economic_model.png')
    print("\nSimulation complete. Charts saved to smlp_economic_model.png")

if __name__ == "__main__":
    run_economic_simulation()
