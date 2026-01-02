"""
Unit tests for deadlock detection
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.simulation.controller import SimulationController, SimulationConfig


def test_simple_deadlock_detection():
    """Test detection of simple two-process deadlock"""
    config = SimulationConfig(detection_strategy='immediate')
    controller = SimulationController(config)
    
    # Setup: P1 holds R1, P2 holds R2
    controller.add_process("P1", priority=5)
    controller.add_process("P2", priority=5)
    controller.add_resource("R1", instances=1)
    controller.add_resource("R2", instances=1)
    
    # Create deadlock
    controller.request_resource("P1", "R1")  # P1 gets R1
    controller.request_resource("P2", "R2")  # P2 gets R2
    controller.request_resource("P1", "R2")  # P1 blocked on R2
    controller.request_resource("P2", "R1")  # P2 blocked on R1
    
    # Detect
    result = controller.detector.detect(controller.processes, controller.resources)
    
    assert result.deadlock_detected == True
    assert len(result.deadlocked_processes) == 2
    assert 'P1' in result.deadlocked_processes
    assert 'P2' in result.deadlocked_processes
    
    print("✓ Simple deadlock detection test passed")


def test_three_process_deadlock():
    """Test detection of three-process circular deadlock"""
    config = SimulationConfig()
    controller = SimulationController(config)
    
    controller.add_process("P1", priority=5)
    controller.add_process("P2", priority=5)
    controller.add_process("P3", priority=5)
    controller.add_resource("R1", instances=1)
    controller.add_resource("R2", instances=1)
    controller.add_resource("R3", instances=1)
    
    # Create circular deadlock: P1->R2->P2->R3->P3->R1->P1
    controller.request_resource("P1", "R1")
    controller.request_resource("P2", "R2")
    controller.request_resource("P3", "R3")
    controller.request_resource("P1", "R2")
    controller.request_resource("P2", "R3")
    controller.request_resource("P3", "R1")
    
    result = controller.detector.detect(controller.processes, controller.resources)
    
    assert result.deadlock_detected == True
    assert len(result.deadlocked_processes) == 3
    
    print("✓ Three-process deadlock detection test passed")


def test_no_deadlock():
    """Test system without deadlock"""
    config = SimulationConfig()
    controller = SimulationController(config)
    
    controller.add_process("P1", priority=5)
    controller.add_process("P2", priority=5)
    controller.add_resource("R1", instances=2)  # Multiple instances
    
    controller.request_resource("P1", "R1")
    controller.request_resource("P2", "R1")
    
    result = controller.detector.detect(controller.processes, controller.resources)
    
    assert result.deadlock_detected == False
    assert len(result.deadlocked_processes) == 0
    
    print("✓ No deadlock test passed")


def test_sequential_execution():
    """Test sequential execution without deadlock"""
    config = SimulationConfig()
    controller = SimulationController(config)
    
    controller.add_process("P1", priority=5)
    controller.add_process("P2", priority=5)
    controller.add_resource("R1", instances=1)
    
    controller.request_resource("P1", "R1")
    controller.release_resource("P1", "R1")
    controller.request_resource("P2", "R1")
    
    result = controller.detector.detect(controller.processes, controller.resources)
    
    assert result.deadlock_detected == False
    
    print("✓ Sequential execution test passed")


def test_wfg_construction():
    """Test Wait-For Graph construction"""
    config = SimulationConfig()
    controller = SimulationController(config)
    
    controller.add_process("P1", priority=5)
    controller.add_process("P2", priority=5)
    controller.add_resource("R1", instances=1)
    controller.add_resource("R2", instances=1)
    
    controller.request_resource("P1", "R1")
    controller.request_resource("P2", "R2")
    controller.request_resource("P1", "R2")
    controller.request_resource("P2", "R1")
    
    from src.detection.wfg import build_wait_for_graph
    wfg = build_wait_for_graph(controller.processes, controller.resources)
    
    assert len(wfg.nodes) == 2
    assert len(wfg.edges) == 2
    assert ('P1', 'P2') in wfg.edges or ('P2', 'P1') in wfg.edges
    
    print("✓ WFG construction test passed")


if __name__ == '__main__':
    print("Running detection tests...\n")
    test_simple_deadlock_detection()
    test_three_process_deadlock()
    test_no_deadlock()
    test_sequential_execution()
    test_wfg_construction()
    print("\n✅ All detection tests passed!")