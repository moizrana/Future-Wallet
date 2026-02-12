"""
Example: Complete simulation with all features.
Demonstrates the full capabilities of the Future Wallet engine.
"""

from decimal import Decimal
from datetime import date, timedelta

from models import SimulationConfig, Asset, AssetType, Debt
from dag_engine import DAGEngine
from simulation_engine import SimulationEngine
from analytics import DataPacketGenerator

from nodes.income_node import SalaryNode, VariableIncomeNode, InvestmentReturnNode
from nodes.expense_node import FixedExpenseNode, VariableExpenseNode, DebtPaymentNode
from nodes.asset_node import AssetPortfolioNode, LiquidationNode, AssetPurchaseNode
from nodes.tax_node import IncomeTaxNode
from nodes.credit_node import CreditScoreNode, BankruptcyCheckNode


def build_comprehensive_dag():
    """Build a DAG with all node types."""
    dag = DAGEngine()
    
    # Income nodes
    dag.add_node(SalaryNode(
        "salary",
        annual_salary=Decimal("75000"),
        payment_day=1
    ))
    
    dag.add_node(VariableIncomeNode(
        "freelance",
        mean_monthly=Decimal("1500"),
        std_dev=Decimal("500"),
        payment_probability=Decimal("0.15")
    ))
    
    # Expense nodes
    dag.add_node(FixedExpenseNode(
        "rent",
        amount=Decimal("2000"),
        payment_day=1,
        description="Monthly rent"
    ))
    
    dag.add_node(FixedExpenseNode(
        "subscriptions",
        amount=Decimal("150"),
        payment_day=5,
        description="Subscriptions (Netflix, Spotify, etc.)"
    ))
    
    dag.add_node(VariableExpenseNode(
        "daily_living",
        daily_mean=Decimal("60"),
        daily_std_dev=Decimal("25"),
        description="Food, transport, entertainment"
    ))
    
    dag.add_node(DebtPaymentNode(
        "debt_payments",
        payment_day=15
    ))
    
    # Asset nodes
    dag.add_node(InvestmentReturnNode(
        "investment_returns",
        annual_return_rate=Decimal("0.08")
    ))
    
    dag.add_node(AssetPortfolioNode("portfolio"))
    
    dag.add_node(LiquidationNode(
        "auto_liquidation",
        min_balance_threshold=Decimal("0"),
        dependencies=["portfolio"]
    ))
    
    dag.add_node(AssetPurchaseNode(
        "auto_invest",
        target_asset_type=AssetType.STOCKS,
        investment_threshold=Decimal("5000"),
        investment_percentage=Decimal("0.4"),
        dependencies=["portfolio"]
    ))
    
    # Tax node
    dag.add_node(IncomeTaxNode(
        "taxes",
        payment_month=12,
        payment_day=31,
        dependencies=["salary", "freelance"]
    ))
    
    # Credit score node
    dag.add_node(CreditScoreNode(
        "credit_score",
        dependencies=["taxes", "portfolio", "debt_payments"]
    ))
    
    # Bankruptcy check
    dag.add_node(BankruptcyCheckNode(
        "bankruptcy",
        dependencies=["credit_score"]
    ))
    
    return dag


def main():
    print("="*70)
    print("FUTURE WALLET ENGINE - COMPREHENSIVE EXAMPLE")
    print("="*70)
    
    # Configuration
    config = SimulationConfig(
        start_date=date(2024, 1, 1),
        end_date=date(2027, 1, 1),  # 3 years
        initial_balance=Decimal("15000"),
        initial_credit_score=Decimal("720"),
        random_seed=42
    )
    
    print(f"\n📅 Simulation Period: {config.start_date} to {config.end_date}")
    print(f"💰 Initial Balance: ${config.initial_balance}")
    print(f"📊 Initial Credit Score: {config.initial_credit_score}")
    print(f"🎲 Random Seed: {config.random_seed}")
    
    # Build DAG
    print("\n🔧 Building financial component DAG...")
    dag = build_comprehensive_dag()
    
    # Display DAG structure
    print("\n" + dag.visualize_graph())
    
    # Create engine
    engine = SimulationEngine(config, dag)
    
    # Add initial assets
    engine.current_state.assets["stock_portfolio"] = Asset(
        name="stock_portfolio",
        asset_type=AssetType.STOCKS,
        value=Decimal("10000"),
        is_liquid=True,
        liquidation_penalty=Decimal("0.02")
    )
    
    engine.current_state.assets["emergency_bonds"] = Asset(
        name="emergency_bonds",
        asset_type=AssetType.BONDS,
        value=Decimal("5000"),
        is_liquid=True,
        liquidation_penalty=Decimal("0.01")
    )
    
    # Add debt
    engine.current_state.debts.append(Debt(
        name="Student Loan",
        principal=Decimal("15000"),
        interest_rate=Decimal("0.045"),
        monthly_payment=Decimal("300")
    ))
    
    # Run simulation
    print("\n🚀 Running 3-year simulation...")
    print("(This may take a few seconds)")
    
    result = engine.run()
    daily_metrics = engine.get_daily_metrics()
    
    # Generate comprehensive data packet
    print("\n📦 Generating data packet...")
    data_packet = DataPacketGenerator.generate(result, daily_metrics)
    
    # Display results
    DataPacketGenerator.print_summary(data_packet)
    
    # Test determinism
    print("\n🔬 Testing Determinism...")
    print("Running simulation again with same seed...")
    
    engine2 = SimulationEngine(config, build_comprehensive_dag())
    engine2.current_state.assets["stock_portfolio"] = Asset(
        name="stock_portfolio",
        asset_type=AssetType.STOCKS,
        value=Decimal("10000"),
        is_liquid=True,
        liquidation_penalty=Decimal("0.02")
    )
    engine2.current_state.assets["emergency_bonds"] = Asset(
        name="emergency_bonds",
        asset_type=AssetType.BONDS,
        value=Decimal("5000"),
        is_liquid=True,
        liquidation_penalty=Decimal("0.01")
    )
    engine2.current_state.debts.append(Debt(
        name="Student Loan",
        principal=Decimal("15000"),
        interest_rate=Decimal("0.045"),
        monthly_payment=Decimal("300")
    ))
    
    result2 = engine2.run()
    
    if result.final_balance == result2.final_balance:
        print("✅ DETERMINISM VERIFIED: Identical results!")
        print(f"   Final Balance (Run 1): ${result.final_balance}")
        print(f"   Final Balance (Run 2): ${result2.final_balance}")
    else:
        print("❌ DETERMINISM FAILED: Results differ!")
    
    # Export data packet
    print("\n💾 Exporting data packet to JSON...")
    DataPacketGenerator.export_to_json(data_packet, "simulation_result.json")
    print("   Saved to: simulation_result.json")
    
    print("\n✨ Simulation complete!")
    print("\nTo visualize these results, run:")
    print("   streamlit run app.py")
    

if __name__ == "__main__":
    main()
