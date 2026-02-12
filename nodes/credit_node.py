"""
Credit score evolution model.
Updates based on debt ratio, payment punctuality, and restructuring events.
"""

from decimal import Decimal
from datetime import date

from dag_engine import Node, ExecutionContext
from models import WalletState, Transaction


class CreditScoreNode(Node):
    """
    Evolves credit score based on financial behavior.
    Formula: CS_{t+1} = CS_t + α * f(debt_ratio, punctuality, restructuring)
    """
    
    def __init__(
        self,
        node_id: str,
        alpha: Decimal = Decimal("0.1"),  # Learning rate
        dependencies: list = None
    ):
        super().__init__(node_id, dependencies)
        self.alpha = Decimal(str(alpha))
        self.last_update_date = None
    
    def calculate_debt_ratio_impact(self, state: WalletState) -> Decimal:
        """
        Calculate impact of debt ratio on credit score.
        Lower debt ratio = positive impact
        """
        total_debt = state.get_total_debt()
        
        # Use annual income as denominator (approximate)
        annual_income = state.total_income_ytd
        if annual_income == Decimal("0"):
            annual_income = Decimal("50000")  # Default assumption
        
        debt_ratio = total_debt / annual_income
        
        # Good: < 0.3, Warning: 0.3-0.5, Bad: > 0.5
        if debt_ratio < Decimal("0.3"):
            return Decimal("2.0")  # Positive impact
        elif debt_ratio < Decimal("0.5"):
            return Decimal("0")  # Neutral
        else:
            return Decimal("-3.0")  # Negative impact
    
    def calculate_punctuality_impact(self, state: WalletState) -> Decimal:
        """
        Calculate impact of payment punctuality.
        Missed payments hurt credit score.
        """
        total_missed = sum(debt.missed_payments for debt in state.debts)
        
        if total_missed == 0:
            return Decimal("1.0")  # Positive impact
        elif total_missed <= 2:
            return Decimal("-2.0")  # Minor negative
        else:
            return Decimal("-5.0")  # Major negative
    
    def calculate_balance_impact(self, state: WalletState) -> Decimal:
        """
        Positive balance improves credit score.
        Negative balance hurts it.
        """
        if state.balance > Decimal("10000"):
            return Decimal("1.0")
        elif state.balance > Decimal("0"):
            return Decimal("0.5")
        elif state.balance > Decimal("-1000"):
            return Decimal("-1.0")
        else:
            return Decimal("-3.0")
    
    def execute(self, state: WalletState, context: ExecutionContext) -> Decimal:
        """
        Update credit score daily based on multiple factors.
        """
        # Calculate component impacts
        debt_impact = self.calculate_debt_ratio_impact(state)
        punctuality_impact = self.calculate_punctuality_impact(state)
        balance_impact = self.calculate_balance_impact(state)
        
        # Combined impact
        total_impact = debt_impact + punctuality_impact + balance_impact
        
        # Apply change with learning rate
        change = self.alpha * total_impact
        
        # Update credit score
        new_score = state.credit_score + change
        
        # Clamp to valid range [300, 850]
        state.credit_score = max(
            Decimal("300"),
            min(Decimal("850"), new_score)
        )
        
        self.last_update_date = context.current_date
        
        return state.credit_score


class BankruptcyCheckNode(Node):
    """
    Checks for bankruptcy conditions.
    Triggers if balance is deeply negative and no liquid assets remain.
    """
    
    def __init__(
        self,
        node_id: str,
        bankruptcy_threshold: Decimal = Decimal("-50000"),
        dependencies: list = None
    ):
        super().__init__(node_id, dependencies)
        self.bankruptcy_threshold = Decimal(str(bankruptcy_threshold))
        self.is_bankrupt = False
    
    def execute(self, state: WalletState, context: ExecutionContext) -> Decimal:
        """Check bankruptcy conditions."""
        liquid_assets = state.get_liquid_assets()
        net_worth = state.get_net_worth()
        
        if net_worth < self.bankruptcy_threshold and liquid_assets < Decimal("100"):
            self.is_bankrupt = True
            
            # Severely impact credit score
            state.credit_score = Decimal("300")
            
            transaction = Transaction(
                timestamp=context.current_date,
                amount=Decimal("0"),
                description="Bankruptcy event",
                category="bankruptcy",
                balance_after=state.balance
            )
            state.transaction_history.append(transaction)
            
            return Decimal("1")  # Bankruptcy occurred
        
        return Decimal("0")  # No bankruptcy
