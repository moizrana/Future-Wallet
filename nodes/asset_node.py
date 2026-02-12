"""
Asset management and liquidation logic.
Handles liquid/illiquid assets and automatic selling to cover deficits.
"""

from decimal import Decimal
from typing import List, Tuple
import heapq

from dag_engine import Node, ExecutionContext
from models import WalletState, Asset, AssetType, Transaction


class AssetPortfolioNode(Node):
    """Manages asset portfolio and tracks valuations."""
    
    def __init__(
        self,
        node_id: str,
        dependencies: list = None
    ):
        super().__init__(node_id, dependencies)
    
    def execute(self, state: WalletState, context: ExecutionContext) -> Decimal:
        """
        Calculate total asset value.
        This is primarily informational - actual returns are handled by InvestmentReturnNode.
        """
        total_value = state.get_total_assets()
        return total_value


class LiquidationNode(Node):
    """
    Automatically liquidates assets to cover negative balances.
    Prioritizes assets with lowest liquidation penalty.
    """
    
    def __init__(
        self,
        node_id: str,
        min_balance_threshold: Decimal = Decimal("0"),
        dependencies: list = None
    ):
        super().__init__(node_id, dependencies)
        self.min_balance_threshold = Decimal(str(min_balance_threshold))
    
    def execute(self, state: WalletState, context: ExecutionContext) -> Decimal:
        """Liquidate assets if balance falls below threshold."""
        if state.balance >= self.min_balance_threshold:
            return Decimal("0")
        
        deficit = self.min_balance_threshold - state.balance
        total_liquidated = Decimal("0")
        
        # Build priority queue of assets (penalty, name, asset)
        asset_queue = []
        for name, asset in state.assets.items():
            # Only liquidate liquid assets automatically
            if asset.is_liquid:
                heapq.heappush(
                    asset_queue,
                    (float(asset.liquidation_penalty), name, asset)
                )
        
        # Liquidate assets until deficit is covered
        assets_to_remove = []
        
        while deficit > Decimal("0") and asset_queue:
            penalty_float, name, asset = heapq.heappop(asset_queue)
            penalty = Decimal(str(penalty_float))
            
            # Calculate net proceeds after penalty
            net_value = asset.value * (Decimal("1") - penalty)
            
            if net_value >= deficit:
                # Partial liquidation
                amount_needed = deficit / (Decimal("1") - penalty)
                asset.value -= amount_needed
                proceeds = amount_needed * (Decimal("1") - penalty)
                
                state.balance += proceeds
                total_liquidated += proceeds
                deficit = Decimal("0")
                
                transaction = Transaction(
                    timestamp=context.current_date,
                    amount=proceeds,
                    description=f"Partial liquidation of {name} (penalty: {penalty*100}%)",
                    category="liquidation",
                    balance_after=state.balance
                )
                state.transaction_history.append(transaction)
            else:
                # Full liquidation
                state.balance += net_value
                total_liquidated += net_value
                deficit -= net_value
                
                transaction = Transaction(
                    timestamp=context.current_date,
                    amount=net_value,
                    description=f"Full liquidation of {name} (penalty: {penalty*100}%)",
                    category="liquidation",
                    balance_after=state.balance
                )
                state.transaction_history.append(transaction)
                
                assets_to_remove.append(name)
        
        # Remove fully liquidated assets
        for name in assets_to_remove:
            del state.assets[name]
        
        return total_liquidated


class AssetPurchaseNode(Node):
    """
    Automatically invest surplus cash into assets.
    """
    
    def __init__(
        self,
        node_id: str,
        target_asset_type: AssetType = AssetType.STOCKS,
        investment_threshold: Decimal = Decimal("5000"),
        investment_percentage: Decimal = Decimal("0.5"),  # Invest 50% of surplus
        dependencies: list = None
    ):
        super().__init__(node_id, dependencies)
        self.target_asset_type = target_asset_type
        self.investment_threshold = Decimal(str(investment_threshold))
        self.investment_percentage = Decimal(str(investment_percentage))
    
    def execute(self, state: WalletState, context: ExecutionContext) -> Decimal:
        """Invest surplus cash into assets."""
        surplus = state.balance - self.investment_threshold
        
        if surplus > Decimal("0"):
            investment_amount = surplus * self.investment_percentage
            
            # Find or create target asset
            asset_name = f"{self.target_asset_type}_portfolio"
            
            if asset_name in state.assets:
                state.assets[asset_name].value += investment_amount
            else:
                state.assets[asset_name] = Asset(
                    name=asset_name,
                    asset_type=self.target_asset_type,
                    value=investment_amount,
                    is_liquid=True,
                    liquidation_penalty=Decimal("0.02")  # 2% penalty
                )
            
            state.balance -= investment_amount
            
            transaction = Transaction(
                timestamp=context.current_date,
                amount=-investment_amount,
                description=f"Investment in {asset_name}",
                category="investment",
                balance_after=state.balance
            )
            state.transaction_history.append(transaction)
            
            return investment_amount
        
        return Decimal("0")
