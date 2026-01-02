"""
Unit tests for Finite State Automaton
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.core.fsa import FiniteStateAutomaton, FSAException


def test_fsa_creation():
    """Test FSA creation with valid parameters"""
    states = {'S0', 'S1', 'S2'}
    alphabet = {'a', 'b'}
    transitions = {
        ('S0', 'a'): 'S1',
        ('S1', 'b'): 'S2'
    }
    
    fsa = FiniteStateAutomaton(
        name="TestFSA",
        states=states,
        alphabet=alphabet,
        transition_function=transitions,
        initial_state='S0',
        accepting_states={'S2'}
    )
    
    assert fsa.current_state == 'S0'
    assert fsa.name == "TestFSA"
    print("✓ FSA creation test passed")


def test_fsa_transitions():
    """Test FSA state transitions"""
    states = {'S0', 'S1', 'S2'}
    alphabet = {'a', 'b'}
    transitions = {
        ('S0', 'a'): 'S1',
        ('S1', 'b'): 'S2',
        ('S2', 'a'): 'S0'
    }
    
    fsa = FiniteStateAutomaton(
        name="TestFSA",
        states=states,
        alphabet=alphabet,
        transition_function=transitions,
        initial_state='S0'
    )
    
    # Test valid transitions
    fsa.transition('a')
    assert fsa.current_state == 'S1'
    
    fsa.transition('b')
    assert fsa.current_state == 'S2'
    
    fsa.transition('a')
    assert fsa.current_state == 'S0'
    
    print("✓ FSA transitions test passed")


def test_fsa_invalid_transition():
    """Test FSA with invalid transition"""
    states = {'S0', 'S1'}
    alphabet = {'a'}
    transitions = {
        ('S0', 'a'): 'S1'
    }
    
    fsa = FiniteStateAutomaton(
        name="TestFSA",
        states=states,
        alphabet=alphabet,
        transition_function=transitions,
        initial_state='S0'
    )
    
    try:
        fsa.transition('b')  # Invalid input
        assert False, "Should have raised FSAException"
    except FSAException:
        pass  # Expected
    
    print("✓ FSA invalid transition test passed")


def test_fsa_reset():
    """Test FSA reset functionality"""
    states = {'S0', 'S1'}
    alphabet = {'a'}
    transitions = {
        ('S0', 'a'): 'S1'
    }
    
    fsa = FiniteStateAutomaton(
        name="TestFSA",
        states=states,
        alphabet=alphabet,
        transition_function=transitions,
        initial_state='S0'
    )
    
    fsa.transition('a')
    assert fsa.current_state == 'S1'
    
    fsa.reset()
    assert fsa.current_state == 'S0'
    assert len(fsa.transition_history) == 0
    
    print("✓ FSA reset test passed")


def test_fsa_accepting_state():
    """Test FSA accepting state check"""
    states = {'S0', 'S1', 'S2'}
    alphabet = {'a', 'b'}
    transitions = {
        ('S0', 'a'): 'S1',
        ('S1', 'b'): 'S2'
    }
    
    fsa = FiniteStateAutomaton(
        name="TestFSA",
        states=states,
        alphabet=alphabet,
        transition_function=transitions,
        initial_state='S0',
        accepting_states={'S2'}
    )
    
    assert not fsa.is_in_accepting_state()
    
    fsa.transition('a')
    assert not fsa.is_in_accepting_state()
    
    fsa.transition('b')
    assert fsa.is_in_accepting_state()
    
    print("✓ FSA accepting state test passed")


if __name__ == '__main__':
    print("Running FSA tests...\n")
    test_fsa_creation()
    test_fsa_transitions()
    test_fsa_invalid_transition()
    test_fsa_reset()
    test_fsa_accepting_state()
    print("\n✅ All FSA tests passed!")