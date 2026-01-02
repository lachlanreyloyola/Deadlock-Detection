"""
Basic tests for deadlock detection system
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.core.process import Process
from src.core.resource import Resource
from src.simulation.controller import SimulationController, SimulationConfig


def test_process_creation():
    """Test process creation and FSA"""
    process = Process(pid="P1", priority=5)
    assert process.state == 'Ready'
    
    process.transition('start')
    assert process.state == 'Running'
    print("✓ Process creation test passed")


def test_resource_creation():
    """Test resource creation and FSA"""
    resource = Resource(rid="R1", total_instances=1)
    assert resource.state == 'Free'
    
    resource.allocate("P1")
    assert resource.state == 'Allocated'
    print("✓ Resource creation test passed")


def test_simple_deadlock_detection():
    """Test detection of simple two-process deadlock"""
    config = SimulationConfig(detection_strategy='immediate')
    controller = SimulationController(config)
    
    controller.add_process("P1", priority=5)
    controller.add_process("P2", priority=5)
    controller.add_resource("R1", instances=1)
    controller.add_resource("R2", instances=1)
    
    controller.request_resource("P1", "R1")
    controller.request_resource("P2", "R2")
    controller.request_resource("P1", "R2")
    controller.request_resource("P2", "R1")
    
    result = controller.detector.detect(controller.processes, controller.resources)
    
    assert result.deadlock_detected == True
    assert len(result.deadlocked_processes) == 2
    print("✓ Deadlock detection test passed")


def test_no_deadlock_scenario():
    """Test system without deadlock"""
    config = SimulationConfig()
    controller = SimulationController(config)
    
    controller.add_process("P1", priority=5)
    controller.add_process("P2", priority=5)
    controller.add_resource("R1", instances=2)
    
    controller.request_resource("P1", "R1")
    controller.request_resource("P2", "R1")
    
    result = controller.detector.detect(controller.processes, controller.resources)
    
    assert result.deadlock_detected == False
    print("✓ No deadlock test passed")


if __name__ == '__main__':
    print("Running tests...")
    test_process_creation()
    test_resource_creation()
    test_simple_deadlock_detection()
    test_no_deadlock_scenario()
    print("\n✅ All tests passed!")