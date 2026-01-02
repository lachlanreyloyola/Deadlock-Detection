"""
Global system state FSA
"""
from .fsa import FiniteStateAutomaton
import logging

logger = logging.getLogger(__name__)


class SystemState:
    """Global system state controller using FSA"""
    
    def __init__(self):
        """Initialize System FSA"""
        states = {'Safe', 'Deadlock', 'Recovering'}
        alphabet = {'cycle_detected', 'recovery_start', 'recovery_complete'}
        
        transitions = {
            ('Safe', 'cycle_detected'): 'Deadlock',
            ('Deadlock', 'recovery_start'): 'Recovering',
            ('Recovering', 'recovery_complete'): 'Safe',
        }
        
        self.fsa = FiniteStateAutomaton(
            name="SystemState",
            states=states,
            alphabet=alphabet,
            transition_function=transitions,
            initial_state='Safe',
            accepting_states={'Safe'}
        )
    
    @property
    def state(self) -> str:
        """Get current system state"""
        return self.fsa.current_state
    
    def is_safe(self) -> bool:
        """Check if system is in safe state"""
        return self.state == 'Safe'
    
    def is_deadlocked(self) -> bool:
        """Check if system is deadlocked"""
        return self.state == 'Deadlock'
    
    def is_recovering(self) -> bool:
        """Check if system is recovering"""
        return self.state == 'Recovering'
    
    def transition(self, event: str):
        """Trigger system state transition"""
        try:
            new_state = self.fsa.transition(event)
            logger.info(f"System state changed to: {new_state}")
            return new_state
        except Exception as e:
            logger.error(f"System state transition failed: {e}")
            raise
    
    def reset(self):
        """Reset system to Safe state"""
        self.fsa.reset()
    
    def __repr__(self):
        return f"SystemState(state='{self.state}')"