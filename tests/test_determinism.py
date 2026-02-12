"""
Test determinism of the simulation engine.
Ensures identical inputs produce identical outputs.
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import SimulationConfig
from dag_engine import DAGEngine
from simulation_engine import SimulationEngine
from nodes.income_node import SalaryNode
from nodes.expense_node import FixedExpenseNode, VariableExpenseNode


def create_basic_dag():
    """Create a basic DAG for testing."""
    dag = DAGEngine()
    dag.add_node(SalaryNode("salary", annual_salary=Decimal("60000")))
    dag.add_node(FixedExpenseNode("rent", amount=Decimal("1500"), payment_day=1))
    dag.add_node(VariableExpenseNode("daily", daily_mean=Decimal("50"), daily_std_dev=Decimal("20")))
    return dag


def test_determinism_same_seed():
    """Test that same seed produces identical results."""
    config = SimulationConfig(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        initial_balance=Decimal("10000"),
        random_seed=42
    )
    
    dag1 = create_basic_dag()
    engine1 = SimulationEngine(config, dag1)
    result1 = engine1.run()
    
    dag2 = create_basic_dag()
    engine2 = SimulationEngine(config, dag2)
    result2 = engine2.run()
    
    # Results should be identical
    assert result1.final_balance == result2.final_balance
    assert result1.final_state.credit_score == result2.final_state.credit_score
    assert len(engine1.daily_metrics) == len(engine2.daily_metrics)
    
    # Check daily metrics match
    for m1, m2 in zip(engine1.daily_metrics, engine2.daily_metrics):
        assert m1['balance'] == m2['balance']
        assert m1['credit_score'] == m2['credit_score']


def test_determinism_different_seed():
    """Test that different seeds produce different results."""
    config1 = SimulationConfig(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        initial_balance=Decimal("10000"),
        random_seed=42
    )
    
    config2 = SimulationConfig(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        initial_balance=Decimal("10000"),
        random_seed=99
    )
    
    dag1 = create_basic_dag()
    engine1 = SimulationEngine(config1, dag1)
    result1 = engine1.run()
    
    dag2 = create_basic_dag()
    engine2 = SimulationEngine(config2, dag2)
    result2 = engine2.run()
    
    # Results should be different (with high probability)
    assert result1.final_balance != result2.final_balance


def test_multiple_runs_consistency():
    """Test 10 runs with same seed all produce identical results."""
    config = SimulationConfig(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 6, 30),  # 6 months
        initial_balance=Decimal("10000"),
        random_seed=42
    )
    
    results = []
    for _ in range(10):
        dag = create_basic_dag()
        engine = SimulationEngine(config, dag)
        result = engine.run()
        results.append(result.final_balance)
    
    # All results should be identical
    assert len(set(results)) == 1  # Only one unique value


def test_prng_state_preservation():
    """Test that PRNG state is correctly preserved in snapshots."""
    config = SimulationConfig(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        initial_balance=Decimal("10000"),
        random_seed=42
    )
    
    dag = create_basic_dag()
    engine = SimulationEngine(config, dag)
    
    # Run to mid-year
    mid_year = date(2024, 6, 30)
    engine.run(start_date=config.start_date, end_date=mid_year)
    
    # Create snapshot
    snapshot_id = engine.create_snapshot("Mid-year")
    
    # Verify PRNG state is captured
    assert engine.current_state.prng_state is not None


if __name__ == "__main__":
    print("Running determinism tests...")
    test_determinism_same_seed()
    print("✅ Same seed test passed")
    
    test_determinism_different_seed()
    print("✅ Different seed test passed")
    
    test_multiple_runs_consistency()
    print("✅ Multiple runs consistency test passed")
    
    test_prng_state_preservation()
    print("✅ PRNG state preservation test passed")
    
    print("\n🎉 All determinism tests passed!")
