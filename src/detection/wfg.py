"""
Wait-For Graph construction and management
"""
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class WaitForGraph:
    """Represents a Wait-For Graph for deadlock detection"""
    nodes: Set[str] = field(default_factory=set)
    edges: List[Tuple[str, str]] = field(default_factory=list)
    adjacency_list: Dict[str, List[str]] = field(default_factory=dict)
    
    def add_node(self, process_id: str):
        """Add a process node to the graph"""
        self.nodes.add(process_id)
        if process_id not in self.adjacency_list:
            self.adjacency_list[process_id] = []
    
    def add_edge(self, from_process: str, to_process: str):
        """Add a directed edge"""
        if from_process not in self.nodes:
            self.add_node(from_process)
        if to_process not in self.nodes:
            self.add_node(to_process)
        
        edge = (from_process, to_process)
        if edge not in self.edges:
            self.edges.append(edge)
            self.adjacency_list[from_process].append(to_process)
    
    def get_neighbors(self, process_id: str) -> List[str]:
        """Get all processes that the given process waits for"""
        return self.adjacency_list.get(process_id, [])
    
    def clear(self):
        """Clear the graph"""
        self.nodes.clear()
        self.edges.clear()
        self.adjacency_list.clear()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for visualization"""
        return {
            'nodes': list(self.nodes),
            'edges': [{'from': e[0], 'to': e[1]} for e in self.edges]
        }
    
    def __repr__(self):
        return f"WFG(nodes={len(self.nodes)}, edges={len(self.edges)})"


def build_wait_for_graph(processes: Dict, resources: Dict) -> WaitForGraph:
    """Build Wait-For Graph from current system state"""
    wfg = WaitForGraph()
    
    for pid, process in processes.items():
        if process.state not in ['Terminated']:
            wfg.add_node(pid)
    
    for requesting_pid, requesting_process in processes.items():
        if requesting_process.state not in ['Blocked', 'Deadlocked']:
            continue
        
        for requested_rid in requesting_process.requested_resources:
            if requested_rid not in resources:
                continue
            
            resource = resources[requested_rid]
            
            for holding_pid in resource.allocated_to:
                if holding_pid in processes and holding_pid != requesting_pid:
                    wfg.add_edge(requesting_pid, holding_pid)
                    logger.debug(
                        f"WFG edge: {requesting_pid} waits for {holding_pid} "
                        f"(resource {requested_rid})"
                    )
    
    logger.info(f"Built {wfg}")
    return wfg