"""
State management and branching system for Future Wallet.
Handles snapshots, timeline trees, and "what-if" scenarios.
"""

from datetime import date, datetime
from typing import Dict, List, Optional
import copy
import uuid
from models import WalletState, Snapshot


class Timeline:
    """Represents a single simulation timeline."""
    
    def __init__(self, timeline_id: str, parent_id: Optional[str] = None):
        self.timeline_id = timeline_id
        self.parent_id = parent_id
        self.states: Dict[date, WalletState] = {}
        self.snapshots: Dict[str, Snapshot] = {}
        
    def add_state(self, simulation_date: date, state: WalletState):
        """Add a state for a specific date."""
        self.states[simulation_date] = state
    
    def get_state(self, simulation_date: date) -> Optional[WalletState]:
        """Retrieve state for a specific date."""
        return self.states.get(simulation_date)
    
    def get_latest_state(self) -> Optional[WalletState]:
        """Get the most recent state."""
        if not self.states:
            return None
        latest_date = max(self.states.keys())
        return self.states[latest_date]


class StateManager:
    """Manages state snapshots and timeline branching."""
    
    def __init__(self):
        self.timelines: Dict[str, Timeline] = {}
        self.main_timeline_id = str(uuid.uuid4())
        self.timelines[self.main_timeline_id] = Timeline(self.main_timeline_id)
        self.current_timeline_id = self.main_timeline_id
    
    def create_snapshot(
        self, 
        state: WalletState,
        simulation_date: date,
        description: str = "",
        parent_snapshot_id: Optional[str] = None
    ) -> Snapshot:
        """
        Create a snapshot of the current state.
        Captures complete state including PRNG for deterministic branching.
        """
        snapshot_id = str(uuid.uuid4())
        snapshot = Snapshot(
            snapshot_id=snapshot_id,
            timestamp=datetime.now(),
            simulation_date=simulation_date,
            state=copy.deepcopy(state),
            parent_snapshot_id=parent_snapshot_id,
            description=description
        )
        
        current_timeline = self.timelines[self.current_timeline_id]
        current_timeline.snapshots[snapshot_id] = snapshot
        
        return snapshot
    
    def branch_from_snapshot(
        self, 
        snapshot_id: str,
        modifications: Optional[Dict] = None
    ) -> str:
        """
        Create a new timeline branching from a snapshot.
        Returns the new timeline ID.
        """
        # Find the snapshot in any timeline
        source_snapshot = None
        source_timeline_id = None
        
        for timeline_id, timeline in self.timelines.items():
            if snapshot_id in timeline.snapshots:
                source_snapshot = timeline.snapshots[snapshot_id]
                source_timeline_id = timeline_id
                break
        
        if source_snapshot is None:
            raise ValueError(f"Snapshot {snapshot_id} not found")
        
        # Create new timeline
        new_timeline_id = str(uuid.uuid4())
        new_timeline = Timeline(new_timeline_id, parent_id=source_timeline_id)
        
        # Copy state and apply modifications
        new_state = copy.deepcopy(source_snapshot.state)
        
        if modifications:
            # Apply modifications to the state
            if 'balance' in modifications:
                new_state.balance = modifications['balance']
            if 'assets' in modifications:
                new_state.assets.update(modifications['assets'])
            if 'debts' in modifications:
                new_state.debts.extend(modifications['debts'])
        
        # Add initial state to new timeline
        new_timeline.add_state(source_snapshot.simulation_date, new_state)
        
        # Create snapshot in new timeline
        new_snapshot = Snapshot(
            snapshot_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            simulation_date=source_snapshot.simulation_date,
            state=copy.deepcopy(new_state),
            parent_snapshot_id=snapshot_id,
            description=f"Branch from {snapshot_id}"
        )
        new_timeline.snapshots[new_snapshot.snapshot_id] = new_snapshot
        
        self.timelines[new_timeline_id] = new_timeline
        
        return new_timeline_id
    
    def switch_timeline(self, timeline_id: str):
        """Switch to a different timeline."""
        if timeline_id not in self.timelines:
            raise ValueError(f"Timeline {timeline_id} not found")
        self.current_timeline_id = timeline_id
    
    def get_timeline(self, timeline_id: Optional[str] = None) -> Timeline:
        """Get a specific timeline or current timeline."""
        if timeline_id is None:
            timeline_id = self.current_timeline_id
        
        if timeline_id not in self.timelines:
            raise ValueError(f"Timeline {timeline_id} not found")
        
        return self.timelines[timeline_id]
    
    def get_current_state(self) -> Optional[WalletState]:
        """Get the current state from the active timeline."""
        current_timeline = self.get_timeline()
        return current_timeline.get_latest_state()
    
    def add_state(self, simulation_date: date, state: WalletState):
        """Add a state to the current timeline."""
        current_timeline = self.get_timeline()
        current_timeline.add_state(simulation_date, state)
    
    def get_all_timeline_ids(self) -> List[str]:
        """Get IDs of all timelines."""
        return list(self.timelines.keys())
    
    def get_timeline_tree(self) -> Dict:
        """Get the tree structure of timelines for visualization."""
        tree = {}
        for timeline_id, timeline in self.timelines.items():
            tree[timeline_id] = {
                'parent_id': timeline.parent_id,
                'num_states': len(timeline.states),
                'num_snapshots': len(timeline.snapshots)
            }
        return tree
