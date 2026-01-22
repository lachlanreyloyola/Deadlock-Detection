
#Deadlock recovery through victim selection and termination

from typing import Dict, Set, List
from dataclasses import dataclass
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class RecoveryResult:
    #Result of recovery operation
    success: bool
    victims: List[str]
    terminated_count: int
    resources_released: Set[str]
    recovery_time: float
    unblocked_processes: Set[str]
    
    def to_dict(self) -> dict:
        #Convert to dictionary
        return {
            'success': self.success,
            'victims': self.victims,
            'terminated_count': self.terminated_count,
            'resources_released': list(self.resources_released),
            'recovery_time': self.recovery_time,
            'unblocked_processes': list(self.unblocked_processes)
        }


class VictimSelector:
    #Victim selection strategies
    
    @staticmethod
    def select_by_priority(processes: Dict, deadlocked_pids: Set[str]) -> str:
        #Select victim with lowest priority (highest priority number)
        victim = None
        lowest_priority = -1
        
        for pid in deadlocked_pids:
            process = processes[pid]
            if process.priority > lowest_priority:
                lowest_priority = process.priority
                victim = pid
        
        logger.info(f"Victim selected by priority: {victim} (priority={lowest_priority})")
        return victim
    
    @staticmethod
    def select_by_cost(processes: Dict, deadlocked_pids: Set[str]) -> str:
        #Select victim with minimum termination cost
        RESOURCE_WEIGHT = 10
        EXECUTION_WEIGHT = 1
        PROGRESS_WEIGHT = 5
        PRIORITY_WEIGHT = 20
        STARVATION_WEIGHT = 50
        
        victim = None
        min_cost = float('inf')
        
        for pid in deadlocked_pids:
            process = processes[pid]
            
            resources_cost = len(process.held_resources) * RESOURCE_WEIGHT
            execution_cost = process.execution_time * EXECUTION_WEIGHT
            progress_cost = process.get_elapsed_time() * PROGRESS_WEIGHT
            priority_cost = (10 - process.priority) * PRIORITY_WEIGHT
            starvation_penalty = process.victim_count * STARVATION_WEIGHT
            
            total_cost = (
                resources_cost + execution_cost + progress_cost + 
                priority_cost - starvation_penalty
            )
            
            logger.debug(f"Cost for {pid}: total={total_cost}")
            
            if total_cost < min_cost:
                min_cost = total_cost
                victim = pid
        
        logger.info(f"Victim selected by cost: {victim} (cost={min_cost})")
        return victim
    
    @staticmethod
    def select_by_time(processes: Dict, deadlocked_pids: Set[str]) -> str:
        #Select victim with least execution time (newest process)
        victim = None
        min_time = float('inf')
        
        for pid in deadlocked_pids:
            process = processes[pid]
            elapsed = process.get_elapsed_time()
            if elapsed < min_time:
                min_time = elapsed
                victim = pid
        
        logger.info(f"Victim selected by time: {victim} (time={min_time}s)")
        return victim
    
    @staticmethod
    def select_by_resources(processes: Dict, deadlocked_pids: Set[str]) -> str:
        #Select victim holding fewest resources
        victim = None
        min_resources = float('inf')
        
        for pid in deadlocked_pids:
            process = processes[pid]
            resource_count = len(process.held_resources)
            if resource_count < min_resources:
                min_resources = resource_count
                victim = pid
        
        logger.info(f"Victim selected by resource count: {victim} (resources={min_resources})")
        return victim


class RecoveryModule:
    #Handles deadlock recovery through process termination
    
    SELECTION_STRATEGIES = {
        'priority': VictimSelector.select_by_priority,
        'cost': VictimSelector.select_by_cost,
        'time': VictimSelector.select_by_time,
        'resources': VictimSelector.select_by_resources
    }
    
    def __init__(self, strategy: str = 'cost'):
        #Initialize recovery module
        if strategy not in self.SELECTION_STRATEGIES:
            raise ValueError(f"Invalid strategy: {strategy}")
        
        self.strategy = strategy
        self.selector = self.SELECTION_STRATEGIES[strategy]
        self.recovery_count = 0
    
    def recover(
        self, 
        processes: Dict, 
        resources: Dict, 
        deadlocked_pids: Set[str]
    ) -> RecoveryResult:
        #Recover from deadlock by terminating victim process(es)
        start_time = time.time()
        self.recovery_count += 1
        
        victims = []
        resources_released = set()
        unblocked_processes = set()
        
        logger.info(f"Starting recovery for deadlock involving: {deadlocked_pids}")
        
        remaining_deadlocked = deadlocked_pids.copy()
        
        while remaining_deadlocked:
            victim_pid = self.selector(processes, remaining_deadlocked)
            victims.append(victim_pid)
            remaining_deadlocked.remove(victim_pid)
            
            victim_resources = self._terminate_victim(victim_pid, processes, resources)
            resources_released.update(victim_resources)
            
            if self._would_break_cycle(victim_pid, remaining_deadlocked, processes, resources):
                logger.info(f"Deadlock broken after terminating {len(victims)} victim(s)")
                break
        
        for pid in deadlocked_pids:
            if pid not in victims:
                process = processes[pid]
                if self._try_allocate_resources(process, resources):
                    process.transition('allocate')
                    unblocked_processes.add(pid)
                else:
                    process.transition('resume')
        
        recovery_time = (time.time() - start_time) * 1000
        
        result = RecoveryResult(
            success=True,
            victims=victims,
            terminated_count=len(victims),
            resources_released=resources_released,
            recovery_time=recovery_time,
            unblocked_processes=unblocked_processes
        )
        
        logger.info(f"Recovery complete: {len(victims)} victim(s) terminated")
        return result
    
    def _terminate_victim(self, victim_pid: str, processes: Dict, resources: Dict) -> Set[str]:
        #Terminate victim process and release its resources
        victim = processes[victim_pid]
        victim.transition('terminate')
        victim.victim_count += 1
        
        released_resources = victim.release_all_resources()
        
        for rid in released_resources:
            if rid in resources:
                resource = resources[rid]
                resource.release(victim_pid)
                logger.debug(f"Released resource {rid} from victim {victim_pid}")
        
        logger.info(f"Terminated victim {victim_pid}, released {len(released_resources)} resources")
        return released_resources
    
    def _would_break_cycle(self, victim_pid: str, remaining: Set[str], 
                          processes: Dict, resources: Dict) -> bool:
        #Check if removing victim would break the deadlock cycle
        return len(remaining) == 0 or len(remaining) < len(processes) / 2
    
    def _try_allocate_resources(self, process, resources: Dict) -> bool:
        #Try to allocate requested resources to process
        if not process.requested_resources:
            return True
        
        requested_rid = process.requested_resources[0]
        if requested_rid in resources:
            resource = resources[requested_rid]
            if resource.is_available():
                resource.allocate(process.pid)
                process.allocate_resource(requested_rid)
                return True
        
        return False
    
    def get_statistics(self) -> dict:
        #Get recovery statistics
        return {
            'recovery_count': self.recovery_count,
            'strategy': self.strategy
        }