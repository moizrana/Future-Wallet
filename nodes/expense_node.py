"""
Expense node implementations.
Supports fixed expenses, variable expenses, and conditional spending.
"""

from decimal import Decimal
from datetime import date
from typing import Callable, Optional

from dag_engine import Node, ExecutionContext
from models import WalletState, Transaction


class FixedExpenseNode(Node):
    """Fixed recurring expenses (rent, subscriptions, etc.)."""
    
    def __init__(
        self,
        node_id: str,
        amount: Decimal,
        payment_day: int = 1,
        description: str = "Fixed expense",
        dependencies: list = None
    ):
        super().__init__(node_id, dependencies)
        self.amount = Decimal(str(amount))
        self.payment_day = payment_day
        self.description = description
        self.last_payment_month = None
    
    def execute(self, state: WalletState, context: ExecutionContext) -> Decimal:
        """Deduct expense on specified day."""
        current_date = context.current_date
        
        if (current_date.day == self.payment_day and
            (self.last_payment_month is None or
             current_date.month != self.last_payment_month)):
            
            self.last_payment_month = current_date.month
            
            state.balance -= self.amount
            state.total_expenses_ytd += self.amount
            
            transaction = Transaction(
                timestamp=current_date,
                amount=-self.amount,
                description=self.description,
                category="expense:fixed",
                balance_after=state.balance
            )
            state.transaction_history.append(transaction)
            
            return self.amount
        
        return Decimal("0")


class VariableExpenseNode(Node):
    """Variable daily expenses (food, entertainment, etc.)."""
    
    def __init__(
        self,
        node_id: str,
        daily_mean: Decimal,
        daily_std_dev: Decimal,
        description: str = "Variable expense",
        dependencies: list = None
    ):
        super().__init__(node_id, dependencies)
        self.daily_mean = Decimal(str(daily_mean))
        self.daily_std_dev = Decimal(str(daily_std_dev))
        self.description = description
    
    def execute(self, state: WalletState, context: ExecutionContext) -> Decimal:
        """Generate daily expense from normal distribution."""
        amount = context.prng.gauss(
            float(self.daily_mean),
            float(self.daily_std_dev)
        )
        amount = max(Decimal("0"), Decimal(str(amount)))
        
        state.balance -= amount
        state.total_expenses_ytd += amount
        
        transaction = Transaction(
            timestamp=context.current_date,
            amount=-amount,
            description=self.description,
            category="expense:variable",
            balance_after=state.balance
        )
        state.transaction_history.append(transaction)
        
        return amount


class ConditionalExpenseNode(Node):
    """Expenses triggered by specific conditions."""
    
    def __init__(
        self,
        node_id: str,
        amount: Decimal,
        condition: Callable[[WalletState, ExecutionContext], bool],
        description: str = "Conditional expense",
        dependencies: list = None
    ):
        super().__init__(node_id, dependencies)
        self.amount = Decimal(str(amount))
        self.condition = condition
        self.description = description
    
    def execute(self, state: WalletState, context: ExecutionContext) -> Decimal:
        """Deduct expense if condition is met."""
        if self.condition(state, context):
            state.balance -= self.amount
            state.total_expenses_ytd += self.amount
            
            transaction = Transaction(
                timestamp=context.current_date,
                amount=-self.amount,
                description=self.description,
                category="expense:conditional",
                balance_after=state.balance
            )
            state.transaction_history.append(transaction)
            
            return self.amount
        
        return Decimal("0")


class DebtPaymentNode(Node):
    """Automatic debt payments."""
    
    def __init__(
        self,
        node_id: str,
        payment_day: int = 15,
        dependencies: list = None
    ):
        super().__init__(node_id, dependencies)
        self.payment_day = payment_day
        self.last_payment_month = None
    
    def execute(self, state: WalletState, context: ExecutionContext) -> Decimal:
        """Make monthly payments on all debts."""
        current_date = context.current_date
        total_payment = Decimal("0")
        
        if (current_date.day == self.payment_day and
            (self.last_payment_month is None or
             current_date.month != self.last_payment_month)):
            
            self.last_payment_month = current_date.month
            
            for debt in state.debts:
                # Check if we can afford the payment
                if state.balance >= debt.monthly_payment:
                    state.balance -= debt.monthly_payment
                    
                    # Calculate interest
                    monthly_interest_rate = debt.interest_rate / Decimal("12")
                    interest = debt.principal * monthly_interest_rate
                    principal_payment = debt.monthly_payment - interest
                    
                    # Update debt principal
                    debt.principal = max(Decimal("0"), debt.principal - principal_payment)
                    
                    total_payment += debt.monthly_payment
                    
                    transaction = Transaction(
                        timestamp=current_date,
                        amount=-debt.monthly_payment,
                        description=f"Debt payment: {debt.name}",
                        category="expense:debt",
                        balance_after=state.balance
                    )
                    state.transaction_history.append(transaction)
                else:
                    # Missed payment
                    debt.missed_payments += 1
            
            state.total_expenses_ytd += total_payment
        
        return total_payment
