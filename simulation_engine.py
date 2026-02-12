"""
Main simulation engine.
Orchestrates daily simulation loop with deterministic PRNG.
"""

from decimal import Decimal
from datetime import date, timedelta
from typing import Dict, List, Optional
import random
from copy import deepcopy

from models import WalletState, SimulationConfig, SimulationResult, Transaction
from dag_engine import DAGEngine
from state_manager import StateManager


class SimulationEngine:
    """
    Main simulation orchestrator.
    Runs day-by-day discrete-event simulation.
    """
    
    def __init__(self, config: SimulationConfig, dag_engine: DAGEngine):
        self.config = config
        self.dag = dag_engine
        self.state_manager = StateManager()
        
        # Initialize deterministic PRNG
        random.seed(config.random_seed)
        self.prng = random.Random(config.random_seed)
        
        # Initialize state
        self.current_state = WalletState(
            current_date=config.start_date,
            balance=config.initial_balance,
            credit_score=config.initial_credit_score
        )
        
        # Capture initial PRNG state
        self.current_state.prng_state = self.prng.getstate()
        
        # Daily metrics tracking
        self.daily_metrics: List[Dict] = []
        
        # Bankruptcy flag
        self.is_bankrupt = False
        self.bankruptcy_date: Optional[date] = None
    
    def run(self, start_date: Optional[date] = None, end_date: Optional[date] = None):
        """
        Run the simulation from start to end date.
        """
        start_date = start_date or self.config.start_date
        end_date = end_date or self.config.end_date
        
        current_date = start_date
        
        while current_date <= end_date:
            # Execute single day
            self.step(current_date)
            
            # Check for bankruptcy
            if self.is_bankrupt:
                self.bankruptcy_date = current_date
                break
            
            # Move to next day
            current_date += timedelta(days=1)
        
        return self.get_result()
    
    def step(self, current_date: date):
        """Execute simulation for a single day."""
        # Update state date
        self.current_state.current_date = current_date
        
        # Execute DAG nodes
        self.current_state = self.dag.execute_daily(
            self.current_state,
            current_date,
            self.prng
        )
        
        # Capture PRNG state for determinism
        self.current_state.prng_state = self.prng.getstate()
        
        # Record daily metrics
        metrics = {
            'date': current_date,
            'balance': self.current_state.balance,
            'credit_score': self.current_state.credit_score,
            'total_assets': self.current_state.get_total_assets(),
            'total_debt': self.current_state.get_total_debt(),
            'net_worth': self.current_state.get_net_worth(),
            'liquid_assets': self.current_state.get_liquid_assets()
        }
        self.daily_metrics.append(metrics)
        
        # Save state to timeline
        self.state_manager.add_state(current_date, deepcopy(self.current_state))
        
        # Check bankruptcy via node
        bankruptcy_node = self.dag.get_node('bankruptcy_check')
        if bankruptcy_node and hasattr(bankruptcy_node, 'is_bankrupt'):
            self.is_bankrupt = bankruptcy_node.is_bankrupt
    
    def create_snapshot(self, description: str = "") -> str:
        """Create a snapshot at current state."""
        snapshot = self.state_manager.create_snapshot(
            self.current_state,
            self.current_state.current_date,
            description
        )
        return snapshot.snapshot_id
    
    def create_branch(
        self,
        snapshot_id: str,
        modifications: Optional[Dict] = None,
        description: str = "Branch scenario"
    ):
        """
        Create a "what-if" branch from a snapshot.
        Returns a new SimulationEngine instance for the branch.
        """
        # Create new timeline
        new_timeline_id = self.state_manager.branch_from_snapshot(
            snapshot_id,
            modifications
        )
        
        # Get the branched state
        new_timeline = self.state_manager.get_timeline(new_timeline_id)
        branched_state = new_timeline.get_latest_state()
        
        # Create new engine with branched state
        branch_engine = SimulationEngine(self.config, self.dag)
        branch_engine.current_state = deepcopy(branched_state)
        
        # Restore PRNG state for determinism
        if branched_state.prng_state:
            branch_engine.prng.setstate(branched_state.prng_state)
        
        branch_engine.state_manager = self.state_manager
        branch_engine.state_manager.switch_timeline(new_timeline_id)
        
        return branch_engine
    
    def get_result(self) -> SimulationResult:
        """Generate final simulation result."""
        final_state = self.current_state
        
        result = SimulationResult(
            config=self.config,
            final_state=final_state,
            timeline_id=self.state_manager.current_timeline_id,
            final_balance=final_state.balance,
            net_asset_value=final_state.get_net_worth()
        )
        
        return result
    
    def get_daily_metrics(self) -> List[Dict]:
        """Get recorded daily metrics."""
        return self.daily_metrics
    
    def get_timeline_data(self) -> Dict:
        """Get full timeline data for visualization."""
        return {
            'dates': [m['date'] for m in self.daily_metrics],
            'balance': [float(m['balance']) for m in self.daily_metrics],
            'credit_score': [float(m['credit_score']) for m in self.daily_metrics],
            'net_worth': [float(m['net_worth']) for m in self.daily_metrics],
            'total_assets': [float(m['total_assets']) for m in self.daily_metrics],
            'total_debt': [float(m['total_debt']) for m in self.daily_metrics]
        }


class ScenarioRunner:
    """
    Runs multiple simulation scenarios.
    Useful for Monte Carlo or sensitivity analysis.
    """
    
    def __init__(self, base_config: SimulationConfig, dag_engine: DAGEngine):
        self.base_config = base_config
        self.dag_engine = dag_engine
        self.scenarios: List[SimulationEngine] = []
    
    def run_scenarios(self, num_scenarios: int = 100):
        """Run multiple scenarios with different random seeds."""
        results = []
        
        for i in range(num_scenarios):
            # Create config with different seed
            config = SimulationConfig(
                start_date=self.base_config.start_date,
                end_date=self.base_config.end_date,
                initial_balance=self.base_config.initial_balance,
                initial_credit_score=self.base_config.initial_credit_score,
                random_seed=self.base_config.random_seed + i
            )
            
            # Run simulation
            engine = SimulationEngine(config, self.dag_engine)
            result = engine.run()
            results.append(result)
        
        return results
