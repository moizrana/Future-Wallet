"""
Analytics and output generation.
Creates final data packets with all required metrics.
"""

from decimal import Decimal
from typing import List, Dict, Optional
import json
from datetime import datetime

from models import SimulationResult, WalletState
from metrics import (
    FinancialVibeCalculator,
    PetStateIndicator,
    RecoverySlopeAnalyzer,
    RiskMetrics,
    StatisticalAnalyzer
)


class PortfolioHealthCalculator:
    """Calculate portfolio health metrics."""
    
    @staticmethod
    def calculate_nav(state: WalletState) -> Decimal:
        """
        Calculate Net Asset Value.
        NAV = Total Assets + Balance - Total Debt
        """
        return state.get_net_worth()
    
    @staticmethod
    def calculate_liquidity_ratio(state: WalletState) -> Decimal:
        """
        Calculate liquidity ratio.
        Ratio = Liquid Assets / Total Debt
        """
        liquid_assets = state.get_liquid_assets() + state.balance
        total_debt = state.get_total_debt()
        
        if total_debt == Decimal("0"):
            return Decimal("999")  # Effectively infinite
        
        return liquid_assets / total_debt
    
    @staticmethod
    def calculate_debt_to_income(state: WalletState) -> Decimal:
        """Calculate debt-to-income ratio."""
        total_debt = state.get_total_debt()
        annual_income = state.total_income_ytd
        
        if annual_income == Decimal("0"):
            return Decimal("0")
        
        return total_debt / annual_income


class DataPacketGenerator:
    """
    Generates final output data packet with all required metrics.
    """
    
    @staticmethod
    def generate(
        result: SimulationResult,
        daily_metrics: List[Dict],
        multi_scenario_results: Optional[List[SimulationResult]] = None
    ) -> Dict:
        """
        Generate comprehensive data packet.
        
        Args:
            result: Single simulation result
            daily_metrics: Daily metric history
            multi_scenario_results: Optional results from multiple runs
            
        Returns:
            Complete data packet as dict
        """
        # Calculate behavioral metrics
        vibe_score, vibe_description = FinancialVibeCalculator.calculate_vibe(daily_metrics)
        pet_state = PetStateIndicator.get_pet_state(vibe_score)
        recovery_slope = RecoverySlopeAnalyzer.calculate_recovery_slope(daily_metrics)
        
        # Calculate risk metrics
        collapse_prob = RiskMetrics.calculate_collapse_probability(daily_metrics)
        shock_resilience = RiskMetrics.calculate_shock_resilience(daily_metrics)
        volatility = RiskMetrics.calculate_volatility(daily_metrics)
        
        # Calculate portfolio health
        nav = PortfolioHealthCalculator.calculate_nav(result.final_state)
        liquidity_ratio = PortfolioHealthCalculator.calculate_liquidity_ratio(result.final_state)
        debt_to_income = PortfolioHealthCalculator.calculate_debt_to_income(result.final_state)
        
        # Update result object
        result.financial_vibe = vibe_score
        result.pet_state = pet_state
        result.collapse_probability = collapse_prob
        result.shock_resilience = shock_resilience
        result.recovery_slope = recovery_slope
        result.net_asset_value = nav
        result.liquidity_ratio = liquidity_ratio
        
        # Build data packet
        packet = {
            'meta': {
                'generated_at': datetime.now().isoformat(),
                'simulation_period': {
                    'start': result.config.start_date.isoformat(),
                    'end': result.config.end_date.isoformat()
                },
                'random_seed': result.config.random_seed
            },
            'final_state': {
                'balance': str(result.final_state.balance),
                'credit_score': str(result.final_state.credit_score),
                'total_assets': str(result.final_state.get_total_assets()),
                'total_debt': str(result.final_state.get_total_debt()),
                'net_worth': str(result.final_state.get_net_worth())
            },
            'statistical_distributions': {
                'final_balance': str(result.final_balance),
                'expected_value': None,
                'percentile_5': None,
                'percentile_50': None,
                'percentile_95': None
            },
            'risk_metrics': {
                'collapse_probability': str(collapse_prob),
                'shock_resilience_index': str(shock_resilience),
                'balance_volatility': str(volatility)
            },
            'portfolio_health': {
                'net_asset_value': str(nav),
                'liquidity_ratio': str(liquidity_ratio),
                'debt_to_income_ratio': str(debt_to_income)
            },
            'behavioral_metrics': {
                'financial_vibe_score': str(vibe_score),
                'financial_vibe_description': vibe_description,
                'pet_state': pet_state,
                'recovery_slope': str(recovery_slope) if recovery_slope else None
            }
        }
        
        # Add multi-scenario statistics if available
        if multi_scenario_results and len(multi_scenario_results) > 1:
            percentiles = StatisticalAnalyzer.calculate_percentiles(
                multi_scenario_results,
                'final_balance'
            )
            packet['statistical_distributions'].update({
                'expected_value': str(percentiles['mean']),
                'percentile_5': str(percentiles['p5']),
                'percentile_50': str(percentiles['p50']),
                'percentile_95': str(percentiles['p95'])
            })
        
        return packet
    
    @staticmethod
    def export_to_json(packet: Dict, filepath: str):
        """Export data packet to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(packet, f, indent=2)
    
    @staticmethod
    def print_summary(packet: Dict):
        """Print human-readable summary."""
        print("\n" + "="*60)
        print("FUTURE WALLET SIMULATION SUMMARY")
        print("="*60)
        
        print(f"\n📅 Simulation Period: {packet['meta']['simulation_period']['start']} to {packet['meta']['simulation_period']['end']}")
        print(f"🎲 Random Seed: {packet['meta']['random_seed']}")
        
        print("\n💰 Final State:")
        print(f"  Balance: ${packet['final_state']['balance']}")
        print(f"  Credit Score: {packet['final_state']['credit_score']}")
        print(f"  Net Worth: ${packet['final_state']['net_worth']}")
        
        print("\n📊 Risk Metrics:")
        print(f"  Collapse Probability: {float(packet['risk_metrics']['collapse_probability']):.1%}")
        print(f"  Shock Resilience: {packet['risk_metrics']['shock_resilience_index']}/10")
        
        print("\n🎭 Behavioral Metrics:")
        print(f"  Financial Vibe: {packet['behavioral_metrics']['financial_vibe_score']}/100 ({packet['behavioral_metrics']['financial_vibe_description']})")
        print(f"  Pet State: {packet['behavioral_metrics']['pet_state']}")
        
        print("\n💼 Portfolio Health:")
        print(f"  NAV: ${packet['portfolio_health']['net_asset_value']}")
        print(f"  Liquidity Ratio: {packet['portfolio_health']['liquidity_ratio']}")
        
        if packet['statistical_distributions']['expected_value']:
            print("\n📈 Multi-Scenario Statistics:")
            print(f"  Expected Final Balance: ${packet['statistical_distributions']['expected_value']}")
            print(f"  P5: ${packet['statistical_distributions']['percentile_5']}")
            print(f"  P95: ${packet['statistical_distributions']['percentile_95']}")
        
        print("\n" + "="*60)
