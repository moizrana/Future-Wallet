"""
Test decimal precision - verify no floating point drift.
"""

import pytest
from decimal import Decimal, getcontext
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import WalletState, Transaction, Asset, AssetType
from datetime import date


def test_decimal_precision():
    """Test that Decimal maintains precision."""
    # This would fail with float
    a = Decimal("0.1")
    b = Decimal("0.2")
    c = a + b
    
    assert c == Decimal("0.3")  # ✅ Exact with Decimal (would be ≈0.30000000000000004 with float)


def test_no_drift_large_transactions():
    """Test that many transactions don't accumulate drift."""
    balance = Decimal("10000")
    
    # Perform 10,000 small transactions
    for _ in range(10000):
        balance += Decimal("0.01")
        balance -= Decimal("0.01")
    
    # Balance should be exactly as started
    assert balance == Decimal("10000")


def test_wallet_state_precision():
    """Test WalletState maintains precision."""
    state = WalletState(
        current_date=date.today(),
        balance=Decimal("1000.50"),
        credit_score=Decimal("750")
    )
    
    # Add many small transactions
    for i in range(1000):
        state.balance += Decimal("0.01")
    
    assert state.balance == Decimal("1010.50")


def test_asset_value_precision():
    """Test asset value calculations maintain precision."""
    asset = Asset(
        name="test",
        asset_type=AssetType.STOCKS,
        value=Decimal("100.00"),
        is_liquid=True,
        liquidation_penalty=Decimal("0.02")
    )
    
    # Apply 1000 small increments
    for _ in range(1000):
        asset.value += Decimal("0.001")
    
    assert asset.value == Decimal("101.000")


def test_division_precision():
    """Test division maintains precision."""
    annual = Decimal("60000")
    monthly = annual / Decimal("12")
    
    assert monthly == Decimal("5000")
    
    # Reconstruct annual
    reconstructed = monthly * Decimal("12")
    assert reconstructed == annual


if __name__ == "__main__":
    print("Running precision tests...")
    
    test_decimal_precision()
    print("✅ Basic decimal precision test passed")
    
    test_no_drift_large_transactions()
    print("✅ No drift test passed")
    
    test_wallet_state_precision()
    print("✅ Wallet state precision test passed")
    
    test_asset_value_precision()
    print("✅ Asset value precision test passed")
    
    test_division_precision()
    print("✅ Division precision test passed")
    
    print("\n🎉 All precision tests passed!")
