"""
Resource class with integrated FSA for state management
"""
from typing import Set
from dataclasses import dataclass, field
from collections import deque
from .fsa import FiniteStateAutomaton


@dataclass
class Resource:
    """Represents a system resource"""
    rid: str
    total_instances: int = 1
    resource_type: str = "Generic"
    available_instances: int = field(init=False)
    allocated_to: Set[str] = field(default_factory=set)
    wait_queue: deque = field(default_factory=deque)
    
    def __post_init__(self):
        """Initialize Resource FSA"""
        self.available_instances = self.total_instances
        
        states = {'Free', 'Allocated'}
        alphabet = {'allocate', 'release'}
        
        transitions = {
            ('Free', 'allocate'): 'Allocated',
            ('Allocated', 'release'): 'Free',
        }
        
        self.fsa = FiniteStateAutomaton(
            name=f"Resource-{self.rid}",
            states=states,
            alphabet=alphabet,
            transition_function=transitions,
            initial_state='Free'
        )
    
    @property
    def state(self) -> str:
        """Get current state from FSA"""
        return self.fsa.current_state
    
    def is_available(self) -> bool:
        """Check if resource has available instances"""
        return self.available_instances > 0
    
    def allocate(self, process_id: str) -> bool:
        """Allocate resource to process"""
        if not self.is_available():
            return False
        
        self.available_instances -= 1
        self.allocated_to.add(process_id)
        
        if self.available_instances == 0 and self.fsa.current_state == 'Free':
            self.fsa.transition('allocate')
        
        return True
    
    def release(self, process_id: str) -> bool:
        """Release resource from process"""
        if process_id not in self.allocated_to:
            return False
        
        self.allocated_to.remove(process_id)
        self.available_instances += 1
        
        if self.available_instances == self.total_instances and self.fsa.current_state == 'Allocated':
            self.fsa.transition('release')
        
        return True
    
    def add_to_wait_queue(self, process_id: str):
        """Add process to wait queue"""
        if process_id not in self.wait_queue:
            self.wait_queue.append(process_id)
    
    def remove_from_wait_queue(self, process_id: str):
        """Remove process from wait queue"""
        if process_id in self.wait_queue:
            self.wait_queue.remove(process_id)
    
    def __repr__(self):
        return (
            f"Resource(rid='{self.rid}', state='{self.state}', "
            f"available={self.available_instances}/{self.total_instances})"
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'rid': self.rid,
            'state': self.state,
            'total_instances': self.total_instances,
            'available_instances': self.available_instances,
            'resource_type': self.resource_type,
            'allocated_to': list(self.allocated_to),
            'wait_queue': list(self.wait_queue)
        }