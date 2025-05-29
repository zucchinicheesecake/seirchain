def calculate_vault_growth(initial_vault: float, months: int, alpha: float = 0.20) -> float:
    """
    Calculate vault growth: V(t) = V₀ × (1 + α)ᵗ
    """
    return initial_vault * ((1 + alpha) ** months)

def validate_minimum_commitment(usdt_amount: float) -> bool:
    """
    Validate minimum USDT commitment
    """
    return usdt_amount >= 13.01
