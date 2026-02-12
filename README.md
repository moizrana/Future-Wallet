# Future Wallet Engine 💰

**Deterministic Financial Simulation for DATAFEST'26**

A high-fidelity financial simulation engine that models multi-year financial trajectories with daily granularity. Built with strict determinism, DAG-based component resolution, and support for "what-if" scenario branching.

## 🎯 Key Features

- ✅ **Bit-Exact Determinism**: Identical inputs produce identical outputs using fixed-seed PRNG
- ✅ **Decimal Precision**: Zero floating-point drift using Python's `decimal` module
- ✅ **DAG-Based Resolution**: Financial components resolved via topological sort
- ✅ **State Branching**: Create parallel "what-if" scenarios from any point
- ✅ **Comprehensive Metrics**: Vibe scores, risk analysis, portfolio health
- ✅ **Interactive Dashboard**: Streamlit UI with real-time visualization

## 🚀 Quick Start

### Installation

```bash
# Clone or navigate to project directory
cd future_wallet

# Install dependencies
pip install -r requirements.txt
```

### Run the Dashboard

```bash
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8501`.

### Basic Usage

```python
from decimal import Decimal
from datetime import date, timedelta
from models import SimulationConfig
from dag_engine import DAGEngine
from simulation_engine import SimulationEngine
from nodes.income_node import SalaryNode
from nodes.expense_node import FixedExpenseNode, VariableExpenseNode

# Configure simulation
config = SimulationConfig(
    start_date=date.today(),
    end_date=date.today() + timedelta(days=365*3),  # 3 years
    initial_balance=Decimal("10000"),
    random_seed=42
)

# Build DAG
dag = DAGEngine()
dag.add_node(SalaryNode("salary", annual_salary=Decimal("60000")))
dag.add_node(FixedExpenseNode("rent", amount=Decimal("1500"), payment_day=1))
dag.add_node(VariableExpenseNode("daily", daily_mean=Decimal("50"), daily_std_dev=Decimal("20")))

# Run simulation
engine = SimulationEngine(config, dag)
result = engine.run()

print(f"Final Balance: ${result.final_balance}")
print(f"Credit Score: {result.final_state.credit_score}")
```

## 📊 Architecture

```
┌─────────────────────────────────────────┐
│      Streamlit Dashboard (app.py)       │
├─────────────────────────────────────────┤
│   Simulation Engine (orchestrator)      │
├─────────────────────────────────────────┤
│      DAG Resolution (NetworkX)           │
├─────────────────────────────────────────┤
│    Financial Component Nodes             │
│  ┌──────┬──────┬──────┬──────┬──────┐  │
│  │Income│Expense│Asset│Tax   │Credit│  │
│  └──────┴──────┴──────┴──────┴──────┘  │
├─────────────────────────────────────────┤
│   State Management & Branching           │
├─────────────────────────────────────────┤
│      Data Models (Pydantic)              │
└─────────────────────────────────────────┘
```

## 🧩 Components

### Financial Nodes

- **Income**: `SalaryNode`, `VariableIncomeNode`, `InvestmentReturnNode`
- **Expenses**: `FixedExpenseNode`, `VariableExpenseNode`, `DebtPaymentNode`
- **Assets**: `AssetPortfolioNode`, `LiquidationNode`, `AssetPurchaseNode`
- **Tax**: `IncomeTaxNode` with progressive brackets
- **Credit**: `CreditScoreNode`, `BankruptcyCheckNode`

### Metrics

- **Financial Vibe**: Qualitative health score (0-100)
- **Pet State**: Emoji indicator of financial status
- **Collapse Probability**: Bankruptcy likelihood
- **Shock Resilience Index**: Ability to absorb unexpected expenses
- **Recovery Slope**: Bounce-back rate from debt

## 🔬 Determinism Verification

```python
# Run simulation twice with same seed
result1 = engine.run()
result2 = engine.run()

assert result1.final_balance == result2.final_balance  # ✅ Always true
```

## 🌳 Branching Scenarios

```python
# Run to year 2
engine.run(start_date=config.start_date, end_date=config.start_date + timedelta(days=730))

# Create snapshot
snapshot_id = engine.create_snapshot("Year 2 baseline")

# Branch with windfall
branch = engine.create_branch(
    snapshot_id,
    modifications={'balance': Decimal("20000")}  # +$10k windfall
)

# Run branch forward
branch_result = branch.run(
    start_date=config.start_date + timedelta(days=731),
    end_date=config.end_date
)
```

## 📦 Output Data Packet

```json
{
  "final_state": {
    "balance": "15234.56",
    "credit_score": "745",
    "net_worth": "23450.00"
  },
  "risk_metrics": {
    "collapse_probability": "0.05",
    "shock_resilience_index": "6.7"
  },
  "behavioral_metrics": {
    "financial_vibe_score": "72",
    "pet_state": "😊 Happy"
  },
  "portfolio_health": {
    "net_asset_value": "23450.00",
    "liquidity_ratio": "3.2"
  }
}
```

## 🧪 Testing

```bash
# Run test suite (coming soon)
pytest tests/ -v

# Test determinism
pytest tests/test_determinism.py -v

# Test precision
pytest tests/test_precision.py -v
```

## 🏆 Competition Readiness

This engine is designed to meet DATAFEST'26 requirements:

- ✅ **Deterministic**: Fixed PRNG seed ensures reproducibility
- ✅ **Precise**: Decimal arithmetic prevents drift
- ✅ **Extensible**: DAG allows easy addition of components
- ✅ **Visual**: Streamlit dashboard for presentation
- ✅ **Documented**: Comprehensive code and usage docs

## 📄 License

MIT License - Built for DATAFEST'26

## 🙏 Acknowledgments

Built using:
- Python 3.11+
- Pydantic for validation
- NetworkX for DAG resolution
- Streamlit for visualization
- Plotly for interactive charts
