"""
Behavioral metrics and analytics.
Calculates Financial Vibe, Pet State, Recovery Slope, and risk metrics.
"""

from decimal import Decimal
from typing import List, Dict, Optional, Tuple
import statistics


class FinancialVibeCalculator:
    """
    Calculates "Financial Vibe" - a qualitative measure of financial health.
    Based on balance volatility and trend.
    """
    
    @staticmethod
    def calculate_vibe(daily_metrics: List[Dict]) -> Tuple[Decimal, str]:
        """
        Calculate vibe score [0-100] and description.
        
        Returns:
            (vibe_score, vibe_description)
        """
        if len(daily_metrics) < 7:
            return Decimal("50"), "Neutral"
        
        # Extract recent balance data (last 30 days)
        recent_days = min(30, len(daily_metrics))
        recent_balances = [
            float(m['balance']) for m in daily_metrics[-recent_days:]
        ]
        
        # Calculate trend
        avg_balance = statistics.mean(recent_balances)
        trend = recent_balances[-1] - recent_balances[0]
        
        # Calculate volatility
        if len(recent_balances) > 1:
            volatility = statistics.stdev(recent_balances)
        else:
            volatility = 0
        
        # Base score on average balance
        if avg_balance > 50000:
            base_score = 80
        elif avg_balance > 10000:
            base_score = 60
        elif avg_balance > 0:
            base_score = 40
        else:
            base_score = 20
        
        # Adjust for trend
        if trend > 1000:
            base_score += 15
        elif trend < -1000:
            base_score -= 15
        
        # Adjust for volatility (lower is better)
        if volatility > 10000:
            base_score -= 10
        
        # Clamp to [0, 100]
        vibe_score = max(0, min(100, base_score))
        
        # Determine description
        if vibe_score >= 80:
            description = "Thriving"
        elif vibe_score >= 60:
            description = "Stable"
        elif vibe_score >= 40:
            description = "Cautious"
        elif vibe_score >= 20:
            description = "Stressed"
        else:
            description = "Critical"
        
        return Decimal(str(vibe_score)), description


class PetStateIndicator:
    """
    Determines "Pet State" emoji based on financial vibe.
    """
    
    @staticmethod
    def get_pet_state(vibe_score: Decimal) -> str:
        """
        Map vibe score to pet emoji.
        """
        if vibe_score >= Decimal("80"):
            return "🎉 Celebrating"
        elif vibe_score >= Decimal("60"):
            return "😊 Happy"
        elif vibe_score >= Decimal("40"):
            return "😐 Neutral"
        elif vibe_score >= Decimal("20"):
            return "😰 Anxious"
        else:
            return "😱 Panicking"


class RecoverySlopeAnalyzer:
    """
    Analyzes recovery slope - how fast user bounces back from debt.
    """
    
    @staticmethod
    def calculate_recovery_slope(daily_metrics: List[Dict]) -> Optional[Decimal]:
        """
        Calculate recovery slope after hitting negative balance.
        
        Returns:
            Slope in $ per day, or None if no negative period
        """
        # Find periods of negative balance
        negative_periods = []
        current_period = []
        
        for i, metric in enumerate(daily_metrics):
            balance = float(metric['balance'])
            
            if balance < 0:
                current_period.append(i)
            else:
                if current_period:
                    negative_periods.append(current_period)
                    current_period = []
        
        if not negative_periods:
            return None  # Never went negative
        
        # Analyze recovery from most recent negative period
        last_negative_period = negative_periods[-1]
        
        # Find recovery window (30 days after exiting negative)
        if last_negative_period[-1] + 30 < len(daily_metrics):
            recovery_start = last_negative_period[-1]
            recovery_end = min(recovery_start + 30, len(daily_metrics) - 1)
            
            start_balance = float(daily_metrics[recovery_start]['balance'])
            end_balance = float(daily_metrics[recovery_end]['balance'])
            
            days_elapsed = recovery_end - recovery_start
            
            if days_elapsed > 0:
                slope = (end_balance - start_balance) / days_elapsed
                return Decimal(str(slope))
        
        return Decimal("0")


class RiskMetrics:
    """
    Calculates risk-related metrics.
    """
    
    @staticmethod
    def calculate_collapse_probability(daily_metrics: List[Dict]) -> Decimal:
        """
        Estimate probability of bankruptcy.
        Based on frequency of negative balance periods.
        """
        if not daily_metrics:
            return Decimal("0")
        
        # Count days with negative balance
        negative_days = sum(
            1 for m in daily_metrics if float(m['balance']) < 0
        )
        
        total_days = len(daily_metrics)
        probability = Decimal(str(negative_days / total_days))
        
        return probability
    
    @staticmethod
    def calculate_shock_resilience(daily_metrics: List[Dict]) -> Decimal:
        """
        Shock Resilience Index (RSI).
        Measures ability to absorb unexpected expenses.
        Based on liquid assets relative to average expenses.
        """
        if len(daily_metrics) < 30:
            return Decimal("0")
        
        # Get current liquid assets
        current_liquid = float(daily_metrics[-1]['liquid_assets'])
        current_balance = float(daily_metrics[-1]['balance'])
        total_liquid = current_liquid + current_balance
        
        # Estimate monthly expenses (change in balance over last 30 days)
        recent_30 = daily_metrics[-30:]
        balance_change = (
            float(recent_30[-1]['balance']) - float(recent_30[0]['balance'])
        )
        
        # Rough monthly expense estimate (if balance decreased)
        if balance_change < 0:
            monthly_expense = abs(balance_change)
        else:
            monthly_expense = 1000  # Default assumption
        
        if monthly_expense == 0:
            return Decimal("10")  # Very resilient
        
        # RSI = months of expenses covered by liquid assets
        rsi = total_liquid / monthly_expense
        
        return Decimal(str(max(0, min(10, rsi))))  # Clamp to [0, 10]
    
    @staticmethod
    def calculate_volatility(daily_metrics: List[Dict]) -> Decimal:
        """Calculate balance volatility (standard deviation)."""
        if len(daily_metrics) < 2:
            return Decimal("0")
        
        balances = [float(m['balance']) for m in daily_metrics]
        volatility = statistics.stdev(balances)
        
        return Decimal(str(volatility))


class StatisticalAnalyzer:
    """
    Statistical analysis across multiple scenarios.
    """
    
    @staticmethod
    def calculate_percentiles(
        results: List,
        key: str = 'final_balance'
    ) -> Dict[str, Decimal]:
        """
        Calculate percentiles across multiple simulation results.
        
        Args:
            results: List of SimulationResult objects
            key: Attribute to analyze
            
        Returns:
            Dict with p5, p50, p95, mean
        """
        values = [float(getattr(r, key)) for r in results]
        values.sort()
        
        n = len(values)
        
        p5_idx = max(0, int(n * 0.05))
        p50_idx = max(0, int(n * 0.50))
        p95_idx = max(0, int(n * 0.95))
        
        return {
            'p5': Decimal(str(values[p5_idx])),
            'p50': Decimal(str(values[p50_idx])),
            'p95': Decimal(str(values[p95_idx])),
            'mean': Decimal(str(statistics.mean(values)))
        }
