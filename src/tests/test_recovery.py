#Unit tests for deadlock recovery

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.simulation.controller import SimulationController, SimulationConfig


def test_recovery_with_priority_strategy():
    #Test recovery using priority-based victim selection
    config = SimulationConfig(recovery_strategy='priority')
    controller = SimulationController(config)
    
    # Create deadlock with different priorities
    controller.add_process("P1", priority=3)  # High priority
    controller.add_process("P2", priority=7)  # Low priority
    controller.add_resource("R1", instances=1)
    controller.add_resource("R2", instances=1)
    
    controller.request_resource("P1", "R1")
    controller.request_resource("P2", "R2")
    controller.request_resource("P1", "R2")
    controller.request_resource("P2", "R1")
    
    # Detect and recover
    result = controller.detector.detect(controller.processes, controller.resources)
    assert result.deadlock_detected == True
    
    recovery_result = controller.recovery.recover(
        controller.processes,
        controller.resources,
        result.deadlocked_processes
    )
    
    # Low priority process (P2) should be terminated
    assert recovery_result.success == True
    assert 'P2' in recovery_result.victims
    assert controller.processes['P2'].state == 'Terminated'
    
    print("✓ Priority-based recovery test passed")


def test_recovery_with_cost_strategy():
    #Test recovery using cost-based victim selection
    config = SimulationConfig(recovery_strategy='cost')
    controller = SimulationController(config)
    
    controller.add_process("P1", priority=5, execution_time=100)
    controller.add_process("P2", priority=5, execution_time=50)
    controller.add_resource("R1", instances=1)
    controller.add_resource("R2", instances=1)
    
    controller.request_resource("P1", "R1")
    controller.request_resource("P2", "R2")
    controller.request_resource("P1", "R2")
    controller.request_resource("P2", "R1")
    
    result = controller.detector.detect(controller.processes, controller.resources)
    recovery_result = controller.recovery.recover(
        controller.processes,
        controller.resources,
        result.deadlocked_processes
    )
    
    assert recovery_result.success == True
    assert len(recovery_result.victims) > 0
    
    print("✓ Cost-based recovery test passed")


def test_resource_release_after_recovery():
    #Test that resources are released after recovery
    config = SimulationConfig(recovery_strategy='cost')
    controller = SimulationController(config)
    
    controller.add_process("P1", priority=5)
    controller.add_process("P2", priority=5)
    controller.add_resource("R1", instances=1)
    controller.add_resource("R2", instances=1)
    
    controller.request_resource("P1", "R1")
    controller.request_resource("P2", "R2")
    controller.request_resource("P1", "R2")
    controller.request_resource("P2", "R1")
    
    # Before recovery
    assert controller.resources['R1'].available_instances == 0
    assert controller.resources['R2'].available_instances == 0
    
    # Detect and recover
    result = controller.detector.detect(controller.processes, controller.resources)
    recovery_result = controller.recovery.recover(
        controller.processes,
        controller.resources,
        result.deadlocked_processes
    )
    
    # After recovery, at least one resource should be freed
    total_available = (controller.resources['R1'].available_instances + 
                      controller.resources['R2'].available_instances)
    assert total_available > 0
    
    print("✓ Resource release after recovery test passed")


def test_multiple_recoveries():
    #Test system handling multiple recovery cycles
    config = SimulationConfig(recovery_strategy='cost')
    controller = SimulationController(config)
    
    controller.add_process("P1", priority=5)
    controller.add_process("P2", priority=5)
    controller.add_resource("R1", instances=1)
    controller.add_resource("R2", instances=1)
    
    # First deadlock
    controller.request_resource("P1", "R1")
    controller.request_resource("P2", "R2")
    controller.request_resource("P1", "R2")
    controller.request_resource("P2", "R1")
    
    result1 = controller.detector.detect(controller.processes, controller.resources)
    recovery1 = controller.recovery.recover(
        controller.processes,
        controller.resources,
        result1.deadlocked_processes
    )
    
    assert recovery1.success == True
    assert controller.recovery.recovery_count == 1
    
    print("✓ Multiple recoveries test passed")


def test_victim_count_tracking():
    #Test that victim count is tracked for starvation prevention
    config = SimulationConfig(recovery_strategy='cost')
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
    recovery_result = controller.recovery.recover(
        controller.processes,
        controller.resources,
        result.deadlocked_processes
    )
    
    # Check victim count increased
    victim_pid = recovery_result.victims[0]
    assert controller.processes[victim_pid].victim_count > 0
    
    print("✓ Victim count tracking test passed")


if __name__ == '__main__':
    print("Running recovery tests...\n")
    test_recovery_with_priority_strategy()
    test_recovery_with_cost_strategy()
    test_resource_release_after_recovery()
    test_multiple_recoveries()
    test_victim_count_tracking()
    print("\nAll recovery tests passed!")