"""
Base Finite State Automaton implementation
"""
from typing import Any, Dict, Optional
from dataclasses import dataclass
import logging
import time

logger = logging.getLogger(__name__)


class FSAException(Exception):
    """Base exception for FSA errors"""
    pass


@dataclass
class Transition:
    """Represents a state transition"""
    from_state: str
    to_state: str
    input_symbol: str
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None


class FiniteStateAutomaton:
    """
    Generic Finite State Automaton implementation
    """
    
    def __init__(
        self,
        name: str,
        states: set,
        alphabet: set,
        transition_function: Dict[tuple, str],
        initial_state: str,
        accepting_states: set = None
    ):
        self.name = name
        self.states = states
        self.alphabet = alphabet
        self.transition_function = transition_function
        self.initial_state = initial_state
        self.current_state = initial_state
        self.accepting_states = accepting_states or set()
        self.transition_history = []
        self._validate()
    
    def _validate(self):
        """Validate FSA definition"""
        if self.initial_state not in self.states:
            raise FSAException(f"Initial state {self.initial_state} not in states")
        
        if not self.accepting_states.issubset(self.states):
            raise FSAException("Accepting states must be subset of states")
    
    def transition(self, input_symbol: str, metadata: Dict[str, Any] = None) -> str:
        """Execute a state transition"""
        if input_symbol not in self.alphabet:
            raise FSAException(f"Invalid input symbol '{input_symbol}' for FSA '{self.name}'")
        
        transition_key = (self.current_state, input_symbol)
        
        if transition_key not in self.transition_function:
            raise FSAException(
                f"No transition defined from state '{self.current_state}' "
                f"with input '{input_symbol}' for FSA '{self.name}'"
            )
        
        next_state = self.transition_function[transition_key]
        
        trans = Transition(
            from_state=self.current_state,
            to_state=next_state,
            input_symbol=input_symbol,
            timestamp=time.time(),
            metadata=metadata
        )
        self.transition_history.append(trans)
        
        logger.debug(f"FSA '{self.name}': {self.current_state} --({input_symbol})--> {next_state}")
        
        self.current_state = next_state
        return next_state
    
    def reset(self):
        """Reset FSA to initial state"""
        self.current_state = self.initial_state
        self.transition_history = []
        logger.info(f"FSA '{self.name}' reset to initial state '{self.initial_state}'")
    
    def is_in_accepting_state(self) -> bool:
        """Check if current state is an accepting state"""
        return self.current_state in self.accepting_states
    
    def get_transition_history(self) -> list:
        """Get list of all transitions"""
        return self.transition_history.copy()
    
    def __repr__(self):
        return (
            f"FSA(name='{self.name}', current_state='{self.current_state}', "
            f"states={len(self.states)}, transitions={len(self.transition_history)})"
        )