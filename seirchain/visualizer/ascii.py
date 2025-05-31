from seirchain.triangular_ledger import TriangularLedger

def render_ascii(ledger_instance: TriangularLedger):
    """Render Triad Matrix in ASCII art (simplified for now)"""
    print("==== TRIAD MATRIX ====")
    print(f"Depth: {max(t.depth for t in ledger_instance.triads) if ledger_instance.triads else 0}")
    print(f"Triads: {len(ledger_instance.triads)}")
    print(f"Pending Transactions: {len(ledger_instance.transaction_pool)}")
    print("Fractal Representation:")
    print("      △      ")
    print("     /△\\     ")
    print("    △ △ △    ")
    print("   /△\\△/△\\   ")
    print("  △△△△△△△△△  ")
    print("================")
