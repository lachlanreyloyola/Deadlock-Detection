#Performance metrics tracking and analysis

from dataclasses import dataclass, field
from typing import List, Dict
import time


@dataclass
class MetricSnapshot:
    #Single metric snapshot at a point in time
    timestamp: float
    iteration: int
    system_state: str
    active_processes: int
    blocked_processes: int
    deadlocked_processes: int
    free_resources: int
    allocated_resources: int


@dataclass
class PerformanceMetrics:
    #Comprehensive performance metrics
    
    #Detection metrics
    total_detections: int = 0
    deadlocks_found: int = 0
    false_positives: int = 0
    detection_times: List[float] = field(default_factory=list)
    
    #Recovery metrics
    total_recoveries: int = 0
    recovery_times: List[float] = field(default_factory=list)
    processes_terminated: int = 0
    
    #System metrics
    total_iterations: int = 0
    simulation_duration: float = 0.0
    snapshots: List[MetricSnapshot] = field(default_factory=list)
    
    def record_detection(self, detection_time: float, deadlock_found: bool):
        #Record a detection event
        self.total_detections += 1
        self.detection_times.append(detection_time)
        if deadlock_found:
            self.deadlocks_found += 1
    
    def record_recovery(self, recovery_time: float, terminated_count: int):
        #Record a recovery event
        self.total_recoveries += 1
        self.recovery_times.append(recovery_time)
        self.processes_terminated += terminated_count
    
    def take_snapshot(self, controller):
        #Take a snapshot of current system state
        snapshot = MetricSnapshot(
            timestamp=time.time(),
            iteration=controller.iteration,
            system_state=controller.system_state.state,
            active_processes=sum(1 for p in controller.processes.values() 
                               if p.state not in ['Terminated']),
            blocked_processes=sum(1 for p in controller.processes.values() 
                                if p.state == 'Blocked'),
            deadlocked_processes=sum(1 for p in controller.processes.values() 
                                   if p.state == 'Deadlocked'),
            free_resources=sum(r.available_instances for r in controller.resources.values()),
            allocated_resources=sum(r.total_instances - r.available_instances 
                                  for r in controller.resources.values())
        )
        self.snapshots.append(snapshot)
    
    def get_average_detection_time(self) -> float:
        #Get average detection time in milliseconds
        if not self.detection_times:
            return 0.0
        return sum(self.detection_times) / len(self.detection_times)
    
    def get_average_recovery_time(self) -> float:
        #Get average recovery time in milliseconds
        if not self.recovery_times:
            return 0.0
        return sum(self.recovery_times) / len(self.recovery_times)
    
    def get_detection_overhead(self) -> float:
        #Get detection overhead as percentage of total time
        if self.simulation_duration == 0:
            return 0.0
        total_detection_time = sum(self.detection_times)
        return (total_detection_time / self.simulation_duration) * 100
    
    def to_dict(self) -> Dict:
        #Convert metrics to dictionary
        return {
            'detection': {
                'total_detections': self.total_detections,
                'deadlocks_found': self.deadlocks_found,
                'false_positives': self.false_positives,
                'average_detection_time_ms': self.get_average_detection_time(),
                'detection_overhead_percent': self.get_detection_overhead()
            },
            'recovery': {
                'total_recoveries': self.total_recoveries,
                'average_recovery_time_ms': self.get_average_recovery_time(),
                'processes_terminated': self.processes_terminated
            },
            'system': {
                'total_iterations': self.total_iterations,
                'simulation_duration_seconds': self.simulation_duration,
                'snapshots_taken': len(self.snapshots)
            }
        }
    
    def __repr__(self):
        return (
            f"PerformanceMetrics(detections={self.total_detections}, "
            f"deadlocks={self.deadlocks_found}, "
            f"recoveries={self.total_recoveries})"
        )