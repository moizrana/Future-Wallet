"""
DAG-based resolution engine for financial components.
Uses topological sort to resolve node dependencies.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Set
from datetime import date
from decimal import Decimal
import networkx as nx

from models import WalletState


class ExecutionContext:
    """Context passed to nodes during execution."""
    
    def __init__(self, current_date: date, prng):
        self.current_date = current_date
        self.prng = prng
        self.node_outputs: Dict[str, Any] = {}
    
    def set_output(self, node_id: str, value: Any):
        """Store output from a node."""
        self.node_outputs[node_id] = value
    
    def get_output(self, node_id: str) -> Any:
        """Retrieve output from a dependency node."""
        return self.node_outputs.get(node_id)


class Node(ABC):
    """
    Abstract base class for all financial component nodes.
    Each node represents a financial aspect (income, expense, tax, etc.)
    """
    
    def __init__(self, node_id: str, dependencies: List[str] = None):
        self.node_id = node_id
        self.dependencies = dependencies or []
        self.last_value: Any = None
    
    @abstractmethod
    def execute(self, state: WalletState, context: ExecutionContext) -> Decimal:
        """
        Execute the node's logic.
        
        Args:
            state: Current wallet state
            context: Execution context with dependencies
            
        Returns:
            The computed value (usually a Decimal amount)
        """
        pass
    
    def get_value(self) -> Any:
        """Return the last computed value."""
        return self.last_value
    
    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.node_id}, deps={self.dependencies})"


class DAGEngine:
    """
    Manages the directed acyclic graph of financial nodes.
    Resolves execution order via topological sort.
    """
    
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.graph: nx.DiGraph = nx.DiGraph()
        self._execution_order: List[str] = []
        self._dirty = True
    
    def add_node(self, node: Node):
        """Register a node in the DAG."""
        if node.node_id in self.nodes:
            raise ValueError(f"Node {node.node_id} already exists")
        
        self.nodes[node.node_id] = node
        self.graph.add_node(node.node_id)
        
        # Add edges for dependencies
        for dep_id in node.dependencies:
            if dep_id not in self.nodes:
                # Dependency not yet added - will be validated later
                pass
            self.graph.add_edge(dep_id, node.node_id)
        
        self._dirty = True
    
    def remove_node(self, node_id: str):
        """Remove a node from the DAG."""
        if node_id in self.nodes:
            del self.nodes[node_id]
            self.graph.remove_node(node_id)
            self._dirty = True
    
    def validate_dag(self) -> bool:
        """
        Validate the DAG structure.
        Checks for cycles and missing dependencies.
        """
        # Check for cycles
        if not nx.is_directed_acyclic_graph(self.graph):
            cycles = list(nx.simple_cycles(self.graph))
            raise ValueError(f"DAG contains cycles: {cycles}")
        
        # Check for missing dependencies
        for node_id, node in self.nodes.items():
            for dep_id in node.dependencies:
                if dep_id not in self.nodes:
                    raise ValueError(
                        f"Node {node_id} depends on {dep_id} which doesn't exist"
                    )
        
        return True
    
    def build_execution_order(self) -> List[str]:
        """
        Build topological execution order.
        Nodes with no dependencies execute first.
        """
        if not self._dirty and self._execution_order:
            return self._execution_order
        
        self.validate_dag()
        
        # Topological sort
        self._execution_order = list(nx.topological_sort(self.graph))
        self._dirty = False
        
        return self._execution_order
    
    def execute_daily(
        self, 
        state: WalletState, 
        current_date: date,
        prng
    ) -> WalletState:
        """
        Execute all nodes for a single day.
        
        Args:
            state: Current wallet state
            current_date: Date being simulated
            prng: Random number generator for stochastic nodes
            
        Returns:
            Updated wallet state
        """
        execution_order = self.build_execution_order()
        context = ExecutionContext(current_date, prng)
        
        # Execute nodes in topological order
        for node_id in execution_order:
            node = self.nodes[node_id]
            
            # Execute the node
            result = node.execute(state, context)
            node.last_value = result
            
            # Store output for dependent nodes
            context.set_output(node_id, result)
        
        return state
    
    def get_node(self, node_id: str) -> Node:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def get_execution_order(self) -> List[str]:
        """Get the current execution order."""
        return self.build_execution_order()
    
    def get_graph_info(self) -> Dict[str, Any]:
        """Get information about the DAG structure."""
        return {
            'num_nodes': len(self.nodes),
            'num_edges': self.graph.number_of_edges(),
            'execution_order': self.get_execution_order(),
            'is_valid': nx.is_directed_acyclic_graph(self.graph)
        }
    
    def visualize_graph(self) -> str:
        """
        Generate a simple text representation of the DAG.
        Useful for debugging.
        """
        lines = ["DAG Structure:"]
        execution_order = self.get_execution_order()
        
        for i, node_id in enumerate(execution_order, 1):
            node = self.nodes[node_id]
            deps_str = ", ".join(node.dependencies) if node.dependencies else "None"
            lines.append(f"{i}. {node_id} (deps: {deps_str})")
        
        return "\n".join(lines)
