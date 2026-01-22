#Main simulation orchestration engine

from typing import Dict, Optional
from dataclasses import dataclass
import time
import logging
from enum import Enum

from ..core.process import Process
from ..core.resource import Resource
from ..core.system_state import SystemState
from ..detection.detector import DeadlockDetector
from ..recovery.recovery import RecoveryModule
logger = logging.getLogger(__name__)


class DetectionStrategy(Enum):
    #Detection triggering strategies
    IMMEDIATE = "immediate"
    PERIODIC = "periodic"
    CPU_TRIGGERED = "cpu_triggered"


@dataclass
class SimulationConfig:
    #Simulation configuration
    detection_strategy: str = "periodic"
    detection_interval: float = 1.0  #seconds
    recovery_strategy: str = "cost"
    cpu_threshold: float = 20.0  #percent
    max_iterations: int = 100


@dataclass
class SimulationMetrics:
    #Simulation performance metrics
    total_detections: int = 0
    deadlocks_found: int = 0
    total_recovery_time: float = 0.0
    total_detection_time: float = 0.0
    processes_terminated: int = 0
    
    def to_dict(self) -> dict:
        return {
            'total_detections': self.total_detections,
            'deadlocks_found': self.deadlocks_found,
            'total_recovery_time': self.total_recovery_time,
            'total_detection_time': self.total_detection_time,
            'processes_terminated': self.processes_terminated,
            'avg_detection_time': (
                self.total_detection_time / self.total_detections
                if self.total_detections > 0 else 0
            ),
            'avg_recovery_time': (
                self.total_recovery_time / self.deadlocks_found
                if self.deadlocks_found > 0 else 0
            )
        }


class SimulationController:
    #Main simulation orchestration engine
    
    
    def __init__(self, config: SimulationConfig = None):
        #Initialize simulation controller
        self.config = config or SimulationConfig()
        
        #Core components
        self.processes: Dict[str, Process] = {}
        self.resources: Dict[str, Resource] = {}
        self.system_state = SystemState()
        self.detector = DeadlockDetector()
        self.recovery = RecoveryModule(strategy=self.config.recovery_strategy)
        
        #Simulation state
        self.metrics = SimulationMetrics()
        self.iteration = 0
        self.last_detection_time = 0.0
        self.simulation_log = []
        self.running = False
    
    def add_process(self, pid: str, priority: int = 5, execution_time: int = 100):
        #Add a process to the system
        if pid in self.processes:
            raise ValueError(f"Process {pid} already exists")
        
        process = Process(pid=pid, priority=priority, execution_time=execution_time)
        self.processes[pid] = process
        logger.info(f"Added process {pid}")
        return process
    
    def add_resource(self, rid: str, instances: int = 1, resource_type: str = "Generic"):
        #Add a resource to the system
        if rid in self.resources:
            raise ValueError(f"Resource {rid} already exists")
        
        resource = Resource(rid=rid, total_instances=instances, resource_type=resource_type)
        self.resources[rid] = resource
        logger.info(f"Added resource {rid}")
        return resource
    
    def request_resource(self, pid: str, rid: str):
        #Process requests a resource
        if pid not in self.processes:
            raise ValueError(f"Process {pid} not found")
        if rid not in self.resources:
            raise ValueError(f"Resource {rid} not found")
        
        process = self.processes[pid]
        resource = self.resources[rid]
        
        #Process FSA: transition to requesting
        if process.state == 'Ready':
            process.transition('start')
        
        process.request_resource(rid)
        
        #Try to allocate
        if resource.is_available():
            #Allocation successful
            resource.allocate(pid)
            process.allocate_resource(rid)
            process.transition('allocate')
            
            self._log_event(f"Process {pid} allocated resource {rid}")
            logger.info(f"Allocated {rid} to {pid}")
        else:
            #Block process
            process.transition('deny')
            resource.add_to_wait_queue(pid)
            
            self._log_event(f"Process {pid} blocked waiting for {rid}")
            logger.info(f"Process {pid} blocked on {rid}")
            
            #Trigger immediate detection if configured
            if self.config.detection_strategy == DetectionStrategy.IMMEDIATE.value:
                self._run_detection()
    
    def release_resource(self, pid: str, rid: str):
        #Process releases a resource"""
        if pid not in self.processes:
            raise ValueError(f"Process {pid} not found")
        if rid not in self.resources:
            raise ValueError(f"Resource {rid} not found")
        
        process = self.processes[pid]
        resource = self.resources[rid]
        
        if resource.release(pid):
            process.release_resource(rid)
            self._log_event(f"Process {pid} released resource {rid}")
            logger.info(f"Process {pid} released {rid}")
            
            #Try to unblock waiting processes
            if resource.wait_queue:
                waiting_pid = resource.wait_queue[0]
                if waiting_pid in self.processes:
                    waiting_process = self.processes[waiting_pid]
                    resource.allocate(waiting_pid)
                    waiting_process.allocate_resource(rid)
                    waiting_process.transition('allocate')
                    resource.remove_from_wait_queue(waiting_pid)
                    
                    self._log_event(f"Unblocked process {waiting_pid}, allocated {rid}")
    
    def run_simulation(self, steps: int = None):
        """
        Run the simulation
        
        Args:
            steps: Number of iterations (None for run until complete)
        """
        self.running = True
        self.iteration = 0
        max_steps = steps or self.config.max_iterations
        
        logger.info(f"Starting simulation with {len(self.processes)} processes, "
                   f"{len(self.resources)} resources")
        self._log_event("=== SIMULATION STARTED ===")
        
        while self.running and self.iteration < max_steps:
            self.iteration += 1
            current_time = time.time()
            
            #Check if detection should run
            if self._should_run_detection(current_time):
                self._run_detection()
            
            #Simulate process execution (simplified)
            #In a real system, processes would actually execute here
            
            # Small delay for periodic detection
            if self.config.detection_strategy == DetectionStrategy.PERIODIC.value:
                time.sleep(0.1)  # 100ms
            
            #Check termination condition
            if self._all_processes_terminated():
                self.running = False
                logger.info("All processes terminated - simulation complete")
                self._log_event("=== SIMULATION COMPLETE ===")
                break
        
        return self._get_final_report()
    
    def _should_run_detection(self, current_time: float) -> bool:
        #Determine if detection should run
        strategy = self.config.detection_strategy
        
        if strategy == DetectionStrategy.IMMEDIATE.value:
            return False  #Already triggered on block
        
        elif strategy == DetectionStrategy.PERIODIC.value:
            elapsed = current_time - self.last_detection_time
            return elapsed >= self.config.detection_interval
        
        elif strategy == DetectionStrategy.CPU_TRIGGERED.value:
            #Simplified: check if any processes are blocked
            blocked_count = sum(
                1 for p in self.processes.values() 
                if p.state in ['Blocked', 'Deadlocked']
            )
            return blocked_count > 0
        
        return False
    
    def _run_detection(self):
        #Run deadlock detection
        self.last_detection_time = time.time()
        
        result = self.detector.detect(self.processes, self.resources)
        self.metrics.total_detections += 1
        self.metrics.total_detection_time += result.detection_latency / 1000.0  # Convert to seconds
        
        self._log_event(
            f"Detection run: {'DEADLOCK FOUND' if result.deadlock_detected else 'SAFE'}"
        )
        
        if result.deadlock_detected:
            self.metrics.deadlocks_found += 1
            
            #Update system FSA
            self.system_state.transition('cycle_detected')
            
            #Update process FSAs
            for pid in result.deadlocked_processes:
                if pid in self.processes:
                    process = self.processes[pid]
                    if process.state != 'Deadlocked':
                        process.transition('detect_cycle')
            
            logger.warning(f"DEADLOCK DETECTED: {result.deadlocked_processes}")
            self._log_event(f"Deadlocked processes: {result.deadlocked_processes}")
            
            #Initiate recovery
            self._run_recovery(result.deadlocked_processes)
    
    def _run_recovery(self, deadlocked_pids: set):
        #Run deadlock recovery
        #Update system FSA
        self.system_state.transition('recovery_start')
        
        recovery_result = self.recovery.recover(
            self.processes,
            self.resources,
            deadlocked_pids
        )
        
        self.metrics.total_recovery_time += recovery_result.recovery_time / 1000.0
        self.metrics.processes_terminated += recovery_result.terminated_count
        
        self._log_event(
            f"Recovery: terminated {recovery_result.terminated_count} victim(s): "
            f"{recovery_result.victims}"
        )
        self._log_event(
            f"Recovery: unblocked {len(recovery_result.unblocked_processes)} process(es)"
        )
        
        #Update system FSA
        self.system_state.transition('recovery_complete')
        
        logger.info(f"Recovery complete: {recovery_result.to_dict()}")
    
    def _all_processes_terminated(self) -> bool:
        #Check if all processes are terminated
        return all(
            p.state == 'Terminated' 
            for p in self.processes.values()
        )
    
    def _log_event(self, message: str):
        #Log a simulation event
        event = {
            'iteration': self.iteration,
            'timestamp': time.time(),
            'message': message,
            'system_state': self.system_state.state
        }
        self.simulation_log.append(event)
    
    def _get_final_report(self) -> dict:
        #Generate final simulation report
        return {
            'summary': {
                'total_iterations': self.iteration,
                'total_processes': len(self.processes),
                'total_resources': len(self.resources),
                'system_final_state': self.system_state.state
            },
            'metrics': self.metrics.to_dict(),
            'processes': {
                pid: p.to_dict() 
                for pid, p in self.processes.items()
            },
            'resources': {
                rid: r.to_dict() 
                for rid, r in self.resources.items()
            },
            'log': self.simulation_log
        }
    
    def get_current_state(self) -> dict:
        #Get current system state snapshot
        return {
            'iteration': self.iteration,
            'system_state': self.system_state.state,
            'processes': {pid: p.to_dict() for pid, p in self.processes.items()},
            'resources': {rid: r.to_dict() for rid, r in self.resources.items()},
            'running': self.running
        }
    
    def reset(self):
        #Reset simulation to initial state
        self.processes.clear()
        self.resources.clear()
        self.system_state.reset()
        self.metrics = SimulationMetrics()
        self.iteration = 0
        self.simulation_log = []
        self.running = False
        logger.info("Simulation reset")