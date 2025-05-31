from seirchain.triangular_ledger.ledger import TriangularLedger
print("Fractal core imported successfully!")
try:
    print(f"Triad structure: {TriangularLedger.Triangle.__name__}")
except Exception as e:
    print(f"Error: {str(e)}")
