"""
Tax calculation with progressive brackets.
Supports income tax and capital gains tax.
"""

from decimal import Decimal
from typing import List, Tuple

from dag_engine import Node, ExecutionContext
from models import WalletState, Transaction


class TaxBracket:
    """Represents a single tax bracket."""
    
    def __init__(self, lower_bound: Decimal, upper_bound: Decimal, rate: Decimal):
        self.lower_bound = Decimal(str(lower_bound))
        self.upper_bound = Decimal(str(upper_bound)) if upper_bound is not None else None
        self.rate = Decimal(str(rate))


class IncomeTaxNode(Node):
    """
    Calculate and deduct income tax using progressive brackets.
    Applied annually or quarterly.
    """
    
    def __init__(
        self,
        node_id: str,
        tax_brackets: List[Tuple[Decimal, Decimal, Decimal]] = None,
        payment_month: int = 12,  # December
        payment_day: int = 31,
        dependencies: list = None
    ):
        super().__init__(node_id, dependencies)
        
        # Default US-style progressive brackets if none provided
        if tax_brackets is None:
            tax_brackets = [
                (Decimal("0"), Decimal("10000"), Decimal("0.10")),
                (Decimal("10000"), Decimal("40000"), Decimal("0.12")),
                (Decimal("40000"), Decimal("85000"), Decimal("0.22")),
                (Decimal("85000"), Decimal("160000"), Decimal("0.24")),
                (Decimal("160000"), None, Decimal("0.32"))
            ]
        
        self.brackets = [
            TaxBracket(lower, upper, rate)
            for lower, upper, rate in tax_brackets
        ]
        self.payment_month = payment_month
        self.payment_day = payment_day
        self.last_payment_year = None
    
    def calculate_tax(self, income: Decimal) -> Decimal:
        """Calculate tax using progressive brackets."""
        if income <= Decimal("0"):
            return Decimal("0")
        
        total_tax = Decimal("0")
        remaining_income = income
        
        for bracket in self.brackets:
            if remaining_income <= Decimal("0"):
                break
            
            # Determine taxable amount in this bracket
            if bracket.upper_bound is None:
                taxable_in_bracket = remaining_income
            else:
                bracket_width = bracket.upper_bound - bracket.lower_bound
                taxable_in_bracket = min(remaining_income, bracket_width)
            
            # Calculate tax for this bracket
            tax_in_bracket = taxable_in_bracket * bracket.rate
            total_tax += tax_in_bracket
            remaining_income -= taxable_in_bracket
        
        return total_tax
    
    def execute(self, state: WalletState, context: ExecutionContext) -> Decimal:
        """Deduct annual income tax on specified date."""
        current_date = context.current_date
        
        if (current_date.month == self.payment_month and
            current_date.day == self.payment_day and
            (self.last_payment_year is None or
             current_date.year != self.last_payment_year)):
            
            self.last_payment_year = current_date.year
            
            # Calculate tax on year-to-date income
            tax_owed = self.calculate_tax(state.total_income_ytd)
            
            # Deduct from balance
            state.balance -= tax_owed
            state.taxes_paid_ytd += tax_owed
            
            transaction = Transaction(
                timestamp=current_date,
                amount=-tax_owed,
                description=f"Annual income tax",
                category="tax:income",
                balance_after=state.balance
            )
            state.transaction_history.append(transaction)
            
            return tax_owed
        
        return Decimal("0")


class CapitalGainsTaxNode(Node):
    """Tax on realized investment gains."""
    
    def __init__(
        self,
        node_id: str,
        tax_rate: Decimal = Decimal("0.15"),  # 15% capital gains rate
        dependencies: list = None
    ):
        super().__init__(node_id, dependencies)
        self.tax_rate = Decimal(str(tax_rate))
        self.last_calculated_date = None
    
    def execute(self, state: WalletState, context: ExecutionContext) -> Decimal:
        """
        Calculate tax on investment gains.
        For simplicity, we tax a portion of investment income annually.
        """
        # This is handled primarily by IncomeTaxNode in practice
        # This node is a placeholder for more sophisticated capital gains tracking
        return Decimal("0")
