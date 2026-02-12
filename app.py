"""
Streamlit dashboard for Future Wallet.
Interactive visualization and scenario exploration.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, timedelta
from decimal import Decimal
import pandas as pd

from models import SimulationConfig, Asset, AssetType, Debt
from dag_engine import DAGEngine
from simulation_engine import SimulationEngine
from analytics import DataPacketGenerator
from nodes.income_node import SalaryNode, VariableIncomeNode, InvestmentReturnNode
from nodes.expense_node import FixedExpenseNode, VariableExpenseNode, DebtPaymentNode
from nodes.asset_node import AssetPortfolioNode, LiquidationNode, AssetPurchaseNode
from nodes.tax_node import IncomeTaxNode
from nodes.credit_node import CreditScoreNode, BankruptcyCheckNode


# Page config
st.set_page_config(
    page_title="Future Wallet Engine",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Future Wallet Engine")
st.markdown("*Deterministic Financial Simulation for DATAFEST'26*")

# Sidebar configuration
st.sidebar.header("⚙️ Simulation Configuration")

# Date range
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input(
        "Start Date",
        value=date.today()
    )
with col2:
    simulation_years = st.number_input(
        "Years",
        min_value=1,
        max_value=10,
        value=3
    )

end_date = start_date + timedelta(days=365 * simulation_years)

# Initial conditions
st.sidebar.subheader("Initial Conditions")
initial_balance = st.sidebar.number_input(
    "Initial Balance ($)",
    min_value=-100000.0,
    max_value=1000000.0,
    value=10000.0,
    step=1000.0
)

initial_credit_score = st.sidebar.slider(
    "Initial Credit Score",
    min_value=300,
    max_value=850,
    value=700
)

random_seed = st.sidebar.number_input(
    "Random Seed (for determinism)",
    min_value=0,
    max_value=9999,
    value=42
)

# Income parameters
st.sidebar.subheader("💵 Income")
annual_salary = st.sidebar.number_input(
    "Annual Salary ($)",
    min_value=0.0,
    max_value=500000.0,
    value=60000.0,
    step=5000.0
)

variable_income = st.sidebar.checkbox("Add Variable Income (e.g., freelance)")
if variable_income:
    var_income_mean = st.sidebar.number_input(
        "Monthly Variable Income Mean ($)",
        value=1000.0,
        step=100.0
    )
    var_income_std = st.sidebar.number_input(
        "Std Dev ($)",
        value=300.0,
        step=50.0
    )

# Expense parameters
st.sidebar.subheader("💸 Expenses")
monthly_rent = st.sidebar.number_input(
    "Monthly Rent ($)",
    min_value=0.0,
    max_value=10000.0,
    value=1500.0,
    step=100.0
)

daily_expenses_mean = st.sidebar.number_input(
    "Daily Variable Expenses Mean ($)",
    min_value=0.0,
    max_value=500.0,
    value=50.0,
    step=5.0
)

daily_expenses_std = st.sidebar.number_input(
    "Daily Expenses Std Dev ($)",
    min_value=0.0,
    max_value=200.0,
    value=20.0,
    step=5.0
)

# Assets
st.sidebar.subheader("📈 Initial Assets")
initial_stocks = st.sidebar.number_input(
    "Stock Portfolio Value ($)",
    min_value=0.0,
    max_value=1000000.0,
    value=5000.0,
    step=1000.0
)

# Debt
st.sidebar.subheader("💳 Initial Debt")
has_debt = st.sidebar.checkbox("Add Debt")
if has_debt:
    debt_amount = st.sidebar.number_input(
        "Debt Principal ($)",
        value=10000.0,
        step=1000.0
    )
    debt_interest = st.sidebar.number_input(
        "Annual Interest Rate (%)",
        value=5.0,
        step=0.5
    ) / 100
    debt_payment = st.sidebar.number_input(
        "Monthly Payment ($)",
        value=300.0,
        step=50.0
    )

# Run simulation button
run_simulation = st.sidebar.button("🚀 Run Simulation", type="primary")


def build_dag() -> DAGEngine:
    """Build the DAG with configured nodes."""
    dag = DAGEngine()
    
    # Income nodes
    dag.add_node(SalaryNode(
        "salary",
        annual_salary=Decimal(str(annual_salary)),
        payment_day=1
    ))
    
    if variable_income:
        dag.add_node(VariableIncomeNode(
            "variable_income",
            mean_monthly=Decimal(str(var_income_mean)),
            std_dev=Decimal(str(var_income_std)),
            payment_probability=Decimal("0.1")
        ))
    
    # Expense nodes
    dag.add_node(FixedExpenseNode(
        "rent",
        amount=Decimal(str(monthly_rent)),
        payment_day=1,
        description="Rent payment"
    ))
    
    dag.add_node(VariableExpenseNode(
        "daily_expenses",
        daily_mean=Decimal(str(daily_expenses_mean)),
        daily_std_dev=Decimal(str(daily_expenses_std)),
        description="Daily living expenses"
    ))
    
    if has_debt:
        dag.add_node(DebtPaymentNode(
            "debt_payment",
            payment_day=15
        ))
    
    # Asset nodes
    if initial_stocks > 0:
        dag.add_node(InvestmentReturnNode(
            "investment_returns",
            annual_return_rate=Decimal("0.07")
        ))
    
    dag.add_node(AssetPortfolioNode("asset_portfolio"))
    
    dag.add_node(LiquidationNode(
        "liquidation",
        min_balance_threshold=Decimal("0"),
        dependencies=["asset_portfolio"]
    ))
    
    dag.add_node(AssetPurchaseNode(
        "asset_purchase",
        investment_threshold=Decimal("5000"),
        investment_percentage=Decimal("0.3"),
        dependencies=["asset_portfolio"]
    ))
    
    # Tax node
    dag.add_node(IncomeTaxNode(
        "income_tax",
        payment_month=12,
        payment_day=31,
        dependencies=["salary"]
    ))
    
    # Credit score node
    dag.add_node(CreditScoreNode(
        "credit_score",
        dependencies=["income_tax", "asset_portfolio"]
    ))
    
    # Bankruptcy check
    dag.add_node(BankruptcyCheckNode(
        "bankruptcy_check",
        dependencies=["credit_score"]
    ))
    
    return dag


if run_simulation or 'simulation_result' not in st.session_state:
    with st.spinner("Running simulation..."):
        # Create configuration
        config = SimulationConfig(
            start_date=start_date,
            end_date=end_date,
            initial_balance=Decimal(str(initial_balance)),
            initial_credit_score=Decimal(str(initial_credit_score)),
            random_seed=random_seed
        )
        
        # Build DAG
        dag = build_dag()
        
        # Create engine
        engine = SimulationEngine(config, dag)
        
        # Add initial assets
        if initial_stocks > 0:
            engine.current_state.assets["stocks_portfolio"] = Asset(
                name="stocks_portfolio",
                asset_type=AssetType.STOCKS,
                value=Decimal(str(initial_stocks)),
                is_liquid=True,
                liquidation_penalty=Decimal("0.02")
            )
        
        # Add initial debt
        if has_debt:
            engine.current_state.debts.append(Debt(
                name="Personal Loan",
                principal=Decimal(str(debt_amount)),
                interest_rate=Decimal(str(debt_interest)),
                monthly_payment=Decimal(str(debt_payment))
            ))
        
        # Run simulation
        result = engine.run()
        daily_metrics = engine.get_daily_metrics()
        timeline_data = engine.get_timeline_data()
        
        # Generate data packet
        data_packet = DataPacketGenerator.generate(result, daily_metrics)
        
        # Store in session state
        st.session_state.simulation_result = result
        st.session_state.daily_metrics = daily_metrics
        st.session_state.timeline_data = timeline_data
        st.session_state.data_packet = data_packet
        st.session_state.engine = engine


# Display results
if 'simulation_result' in st.session_state:
    result = st.session_state.simulation_result
    data_packet = st.session_state.data_packet
    timeline_data = st.session_state.timeline_data
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Final Balance",
            f"${float(result.final_balance):,.2f}",
            delta=f"${float(result.final_balance - Decimal(str(initial_balance))):,.2f}"
        )
    
    with col2:
        st.metric(
            "Credit Score",
            f"{float(result.final_state.credit_score):.0f}",
            delta=f"{float(result.final_state.credit_score - Decimal(str(initial_credit_score))):+.0f}"
        )
    
    with col3:
        st.metric(
            "Net Worth",
            f"${float(result.net_asset_value):,.2f}"
        )
    
    with col4:
        vibe_score = data_packet['behavioral_metrics']['financial_vibe_score']
        st.metric(
            "Financial Vibe",
            f"{float(vibe_score):.0f}/100",
            delta=data_packet['behavioral_metrics']['financial_vibe_description']
        )
    
    # Pet State - large emoji  display
    st.markdown(f"### {data_packet['behavioral_metrics']['pet_state']}")
    
    # Trajectory plot
    st.subheader("📊 Financial Trajectory")
    
    df = pd.DataFrame({
        'Date': timeline_data['dates'],
        'Balance': timeline_data['balance'],
        'Net Worth': timeline_data['net_worth'],
        'Credit Score': [cs * 100 for cs in timeline_data['credit_score']]  # Scale for visibility
    })
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Balance'],
        mode='lines',
        name='Balance',
        line=dict(color='#2E86DE', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Net Worth'],
        mode='lines',
        name='Net Worth',
        line=dict(color='#10AC84', width=2)
    ))
    
    fig.update_layout(
        title="Balance & Net Worth Over Time",
        xaxis_title="Date",
        yaxis_title="Amount ($)",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Credit score plot
    fig_credit = go.Figure()
    
    fig_credit.add_trace(go.Scatter(
        x=df['Date'],
        y=timeline_data['credit_score'],
        mode='lines',
        name='Credit Score',
        line=dict(color='#EE5A24', width=2),
        fill='tozeroy'
    ))
    
    fig_credit.update_layout(
        title="Credit Score Evolution",
        xaxis_title="Date",
        yaxis_title="Credit Score",
        yaxis=dict(range=[300, 850]),
        height=300
    )
    
    st.plotly_chart(fig_credit, use_container_width=True)
    
    # Risk dashboard
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⚠️ Risk Metrics")
        collapse_prob = float(data_packet['risk_metrics']['collapse_probability'])
        rsi = float(data_packet['risk_metrics']['shock_resilience_index'])
        
        st.metric("Collapse Probability", f"{collapse_prob:.1%}")
        st.metric("Shock Resilience Index", f"{rsi:.2f}/10")
        
        # Gauge chart for RSI
        fig_rsi = go.Figure(go.Indicator(
            mode="gauge+number",
            value=rsi,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Resilience"},
            gauge={
                'axis': {'range': [None, 10]},
                'bar': {'color': "darkgreen"},
                'steps': [
                    {'range': [0, 3], 'color': "lightcoral"},
                    {'range': [3, 7], 'color': "lightyellow"},
                    {'range': [7, 10], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 5
                }
            }
        ))
        
        fig_rsi.update_layout(height=250)
        st.plotly_chart(fig_rsi, use_container_width=True)
    
    with col2:
        st.subheader("💼 Portfolio Health")
        nav = float(data_packet['portfolio_health']['net_asset_value'])
        liquidity = float(data_packet['portfolio_health']['liquidity_ratio'])
        
        st.metric("Net Asset Value", f"${nav:,.2f}")
        st.metric("Liquidity Ratio", f"{min(liquidity, 999):.2f}")
        
        # Asset breakdown
        if result.final_state.assets:
            asset_data = {
                name: float(asset.value)
                for name, asset in result.final_state.assets.items()
            }
            asset_data['Cash'] = max(0, float(result.final_state.balance))
            
            fig_pie = px.pie(
                values=list(asset_data.values()),
                names=list(asset_data.keys()),
                title="Asset Allocation"
            )
            fig_pie.update_layout(height=250)
            st.plotly_chart(fig_pie, use_container_width=True)
    
    # What-if scenarios
    st.subheader("🔮 What-If Scenarios")
    st.markdown("Create branching scenarios to explore alternative financial paths.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        branch_amount = st.number_input(
            "Balance Modification ($)",
            min_value=-100000.0,
            max_value=100000.0,
            value=10000.0,
            step=1000.0
        )
    
    with col2:
        branch_year = st.number_input(
            "Branch at Year",
            min_value=1,
            max_value=simulation_years,
            value=2
        )
    
    with col3:
        st.write("")  # Spacing
        st.write("")
        create_branch = st.button("Create Branch")
    
    if create_branch:
        st.info("Branch scenario feature requires re-running simulation with modified parameters. Adjust initial balance or income/expenses above and re-run.")
    
    # Export data packet
    st.subheader("📦 Export Data Packet")
    
    import json
    json_str = json.dumps(data_packet, indent=2)
    
    st.download_button(
        label="Download JSON",
        data=json_str,
        file_name=f"future_wallet_result_{random_seed}.json",
        mime="application/json"
    )
    
    with st.expander("View Data Packet"):
        st.json(data_packet)

else:
    st.info("Configure parameters in the sidebar and click 'Run Simulation' to begin.")
