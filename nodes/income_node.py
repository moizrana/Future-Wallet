"""
Income node implementations.
Supports fixed salaries, variable income, and investment returns.
"""

from decimal import Decimal
from datetime import date
from typing import Optional
import calendar

from dag_engine import Node, ExecutionContext
from models import WalletState, Transaction


class SalaryNode(Node):
    """Fixed periodic salary income."""
    
    def __init__(
        self, 
        node_id: str,
        annual_salary: Decimal,
        payment_day: int = 1,  # Day of month for payment
        dependencies: list = None
    ):
        super().__init__(node_id, dependencies)
        self.annual_salary = Decimal(str(annual_salary))
        self.monthly_salary = self.annual_salary / Decimal("12")
        self.payment_day = payment_day
        self.last_payment_month = None
    
    def execute(self, state: WalletState, context: ExecutionContext) -> Decimal:
        """Pay salary on specified day of month."""
        current_date = context.current_date
        
        # Check if it's payment day and we haven't paid this month
        if (current_date.day == self.payment_day and 
            (self.last_payment_month is None or 
             current_date.month != self.last_payment_month)):
            
            self.last_payment_month = current_date.month
            
            # Add to balance
            state.balance += self.monthly_salary
            state.total_income_ytd += self.monthly_salary
            
            # Record transaction
            transaction = Transaction(
                timestamp=current_date,
                amount=self.monthly_salary,
                description=f"Salary payment",
                category="income:salary",
                balance_after=state.balance
            )
            state.transaction_history.append(transaction)
            
            return self.monthly_salary
        
        return Decimal("0")


class VariableIncomeNode(Node):
    """Variable/stochastic income (e.g., freelance, bonuses)."""
    
    def __init__(
        self,
        node_id: str,
        mean_monthly: Decimal,
        std_dev: Decimal,
        payment_probability: Decimal = Decimal("0.1"),  # 10% chance per day
        dependencies: list = None
    ):
        super().__init__(node_id, dependencies)
        self.mean_monthly = Decimal(str(mean_monthly))
        self.std_dev = Decimal(str(std_dev))
        self.payment_probability = Decimal(str(payment_probability))
    
    def execute(self, state: WalletState, context: ExecutionContext) -> Decimal:
        """Randomly generate income based on probability."""
        # Use PRNG to determine if income occurs
        if context.prng.random() < float(self.payment_probability):
            # Generate amount using normal distribution
            amount = context.prng.gauss(
                float(self.mean_monthly), 
                float(self.std_dev)
            )
            amount = max(Decimal("0"), Decimal(str(amount)))
            
            state.balance += amount
            state.total_income_ytd += amount
            
            transaction = Transaction(
                timestamp=context.current_date,
                amount=amount,
                description="Variable income",
                category="income:variable",
                balance_after=state.balance
            )
            state.transaction_history.append(transaction)
            
            return amount
        
        return Decimal("0")


class InvestmentReturnNode(Node):
    """Returns from asset holdings."""
    
    def __init__(
        self,
        node_id: str,
        annual_return_rate: Decimal = Decimal("0.07"),  # 7% annual
        dependencies: list = None
    ):
        super().__init__(node_id, dependencies)
        self.annual_return_rate = Decimal(str(annual_return_rate))
        self.daily_return_rate = self.annual_return_rate / Decimal("365")
    
    def execute(self, state: WalletState, context: ExecutionContext) -> Decimal:
        """Apply daily returns to investment assets."""
        total_return = Decimal("0")
        
        # Apply returns to stocks, bonds, crypto
        investable_types = ['stocks', 'bonds', 'crypto']
        
        for asset_name, asset in state.assets.items():
            if asset.asset_type in investable_types:
                daily_gain = asset.value * self.daily_return_rate
                
                # Add some stochasticity
                volatility = context.prng.gauss(1.0, 0.01)  # 1% daily volatility
                daily_gain *= Decimal(str(volatility))
                
                asset.value += daily_gain
                total_return += daily_gain
        
        # Add returns to balance (realized gains)
        if total_return != Decimal("0"):
            state.balance += total_return
            state.total_income_ytd += total_return
            
            transaction = Transaction(
                timestamp=context.current_date,
                amount=total_return,
                description="Investment returns",
                category="income:investment",
                balance_after=state.balance
            )
            state.transaction_history.append(transaction)
        
        return total_return
