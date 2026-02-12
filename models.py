"""
Data models for Future Wallet engine.
All monetary values use Decimal for precision.
"""

from decimal import Decimal, getcontext
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import copy

# Set decimal precision for financial calculations
getcontext().prec = 28


class AssetType(str, Enum):
    """Types of assets with different liquidity characteristics."""
    CASH = "cash"
    STOCKS = "stocks"
    BONDS = "bonds"
    REAL_ESTATE = "real_estate"
    CRYPTO = "crypto"
    OTHER = "other"


class Asset(BaseModel):
    """Asset definition with liquidation properties."""
    name: str
    asset_type: AssetType
    value: Decimal
    is_liquid: bool = True
    liquidation_penalty: Decimal = Field(default=Decimal("0.0"), ge=0, le=1)
    
    @field_validator('value', 'liquidation_penalty', mode='before')
    @classmethod
    def convert_to_decimal(cls, v):
        """Convert numeric inputs to Decimal."""
        if isinstance(v, (int, float, str)):
            return Decimal(str(v))
        return v
    
    class Config:
        arbitrary_types_allowed = True


class Debt(BaseModel):
    """Debt position with interest rate."""
    name: str
    principal: Decimal
    interest_rate: Decimal = Field(ge=0)  # Annual rate as decimal (e.g., 0.05 for 5%)
    monthly_payment: Decimal = Field(ge=0)
    missed_payments: int = 0
    
    @field_validator('principal', 'interest_rate', 'monthly_payment', mode='before')
    @classmethod
    def convert_to_decimal(cls, v):
        if isinstance(v, (int, float, str)):
            return Decimal(str(v))
        return v
    
    class Config:
        arbitrary_types_allowed = True


class Transaction(BaseModel):
    """Individual financial event."""
    timestamp: datetime
    amount: Decimal
    description: str
    category: str
    balance_after: Decimal
    
    @field_validator('amount', 'balance_after', mode='before')
    @classmethod
    def convert_to_decimal(cls, v):
        if isinstance(v, (int, float, str)):
            return Decimal(str(v))
        return v
    
    class Config:
        arbitrary_types_allowed = True


class WalletState(BaseModel):
    """Complete financial state at a point in time."""
    current_date: date
    balance: Decimal
    credit_score: Decimal = Field(default=Decimal("700"), ge=300, le=850)
    assets: Dict[str, Asset] = Field(default_factory=dict)
    debts: List[Debt] = Field(default_factory=list)
    transaction_history: List[Transaction] = Field(default_factory=list)
    
    # Metrics
    total_income_ytd: Decimal = Field(default=Decimal("0"))
    total_expenses_ytd: Decimal = Field(default=Decimal("0"))
    taxes_paid_ytd: Decimal = Field(default=Decimal("0"))
    
    # PRNG state for determinism
    prng_state: Optional[Tuple] = None
    
    @field_validator('balance', 'credit_score', 'total_income_ytd', 'total_expenses_ytd', 'taxes_paid_ytd', mode='before')
    @classmethod
    def convert_to_decimal(cls, v):
        if isinstance(v, (int, float, str)):
            return Decimal(str(v))
        return v
    
    class Config:
        arbitrary_types_allowed = True
    
    def __deepcopy__(self, memo):
        """Custom deep copy for efficient snapshotting."""
        return WalletState(
            current_date=self.current_date,
            balance=Decimal(str(self.balance)),
            credit_score=Decimal(str(self.credit_score)),
            assets={k: copy.deepcopy(v) for k, v in self.assets.items()},
            debts=copy.deepcopy(self.debts),
            transaction_history=copy.deepcopy(self.transaction_history),
            total_income_ytd=Decimal(str(self.total_income_ytd)),
            total_expenses_ytd=Decimal(str(self.total_expenses_ytd)),
            taxes_paid_ytd=Decimal(str(self.taxes_paid_ytd)),
            prng_state=self.prng_state
        )
    
    def get_total_assets(self) -> Decimal:
        """Calculate total asset value."""
        return sum(asset.value for asset in self.assets.values())
    
    def get_total_debt(self) -> Decimal:
        """Calculate total debt principal."""
        return sum(debt.principal for debt in self.debts)
    
    def get_net_worth(self) -> Decimal:
        """Calculate net worth (assets + balance - debts)."""
        return self.balance + self.get_total_assets() - self.get_total_debt()
    
    def get_liquid_assets(self) -> Decimal:
        """Get value of liquid assets only."""
        return sum(asset.value for asset in self.assets.values() if asset.is_liquid)


class Snapshot(BaseModel):
    """State snapshot for branching."""
    snapshot_id: str
    timestamp: datetime
    simulation_date: date
    state: WalletState
    parent_snapshot_id: Optional[str] = None
    description: str = ""
    
    class Config:
        arbitrary_types_allowed = True


class SimulationConfig(BaseModel):
    """Configuration parameters for simulation."""
    start_date: date
    end_date: date
    initial_balance: Decimal
    initial_credit_score: Decimal = Field(default=Decimal("700"), ge=300, le=850)
    random_seed: int = 42
    base_currency: str = "USD"
    
    @field_validator('initial_balance', 'initial_credit_score', mode='before')
    @classmethod
    def convert_to_decimal(cls, v):
        if isinstance(v, (int, float, str)):
            return Decimal(str(v))
        return v
    
    class Config:
        arbitrary_types_allowed = True


class SimulationResult(BaseModel):
    """Final output data packet."""
    config: SimulationConfig
    final_state: WalletState
    timeline_id: str
    
    # Statistical distributions
    final_balance: Decimal
    expected_value: Optional[Decimal] = None
    percentile_5: Optional[Decimal] = None
    percentile_95: Optional[Decimal] = None
    
    # Risk metrics
    collapse_probability: Optional[Decimal] = None
    shock_resilience: Optional[Decimal] = None
    recovery_slope: Optional[Decimal] = None
    
    # Portfolio health
    net_asset_value: Decimal
    liquidity_ratio: Optional[Decimal] = None
    
    # Behavioral metrics
    financial_vibe: Optional[Decimal] = None
    pet_state: str = "😐"
    
    @field_validator('final_balance', 'expected_value', 'percentile_5', 'percentile_95', 
                     'collapse_probability', 'shock_resilience', 'recovery_slope',
                     'net_asset_value', 'liquidity_ratio', 'financial_vibe', mode='before')
    @classmethod
    def convert_to_decimal(cls, v):
        if v is None:
            return v
        if isinstance(v, (int, float, str)):
            return Decimal(str(v))
        return v
    
    class Config:
        arbitrary_types_allowed = True
