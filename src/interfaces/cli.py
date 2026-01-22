#Command-line interface for deadlock detection system

import sys
from typing import Optional
from ..simulation.controller import SimulationController, SimulationConfig
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CLI:
    #Interactive command-line interface
    
    def __init__(self):
        self.controller: Optional[SimulationController] = None
        self.config = SimulationConfig()
    
    def run(self):
        #Main CLI loop
        print("=" * 60)
        print("DEADLOCK DETECTION AND RECOVERY SYSTEM v1.0")
        print("=" * 60)
        print()
        
        while True:
            self._print_menu()
            choice = input("\nEnter choice: ").strip()
            
            if choice == '1':
                self._define_scenario()
            elif choice == '2':
                self._load_scenario()
            elif choice == '3':
                self._configure_detection()
            elif choice == '4':
                self._run_simulation()
            elif choice == '5':
                self._view_results()
            elif choice == '6':
                print("\nThank you for using Deadlock Detection System!")
                break
            else:
                print("\n✘ Invalid choice. Please try again.")
    
    def _print_menu(self):
        #Print main menu
        print("\n" + "=" * 60)
        print("MAIN MENU")
        print("=" * 60)
        print("[1] Define New Scenario")
        print("[2] Load Scenario from File")
        print("[3] Configure Detection Settings")
        print("[4] Run Simulation")
        print("[5] View Results")
        print("[6] Exit")
        print("=" * 60)
    
    def _define_scenario(self):
        #Interactive scenario definition
        print("\n" + "=" * 60)
        print("DEFINE NEW SCENARIO")
        print("=" * 60)
        
        self.controller = SimulationController(self.config)
        
        print("\n--- Define Processes ---")
        num_processes = self._get_int_input("How many processes? ", 1, 10)
        
        for i in range(num_processes):
            print(f"\nProcess {i+1}:")
            pid = input("  Process ID (e.g., P1): ").strip()
            priority = self._get_int_input("  Priority (1-10, 1=highest): ", 1, 10)
            execution_time = self._get_int_input("  Execution time (ms): ", 10, 1000)
            
            self.controller.add_process(pid, priority, execution_time)
        
        print("\n--- Define Resources ---")
        num_resources = self._get_int_input("How many resources? ", 1, 10)
        
        for i in range(num_resources):
            print(f"\nResource {i+1}:")
            rid = input("  Resource ID (e.g., R1): ").strip()
            instances = self._get_int_input("  Number of instances: ", 1, 10)
            res_type = input("  Resource type (CPU/Memory/File/Device): ").strip() or "Generic"
            
            self.controller.add_resource(rid, instances, res_type)
        
        print("\n--- Define Initial Allocations ---")
        while True:
            add_more = input("Add allocation? (y/n): ").strip().lower()
            if add_more != 'y':
                break
            
            pid = input("  Process ID: ").strip()
            rid = input("  Resource ID: ").strip()
            
            try:
                self.controller.request_resource(pid, rid)
                print(f"  ✓ Allocated {rid} to {pid}")
            except Exception as e:
                print(f"  ✘ Error: {e}")
        
        print("\n--- Define Resource Requests ---")
        while True:
            add_more = input("Add request? (y/n): ").strip().lower()
            if add_more != 'y':
                break
            
            pid = input("  Process ID: ").strip()
            rid = input("  Resource ID: ").strip()
            
            try:
                self.controller.request_resource(pid, rid)
                print(f"  ✓ {pid} requested {rid}")
            except Exception as e:
                print(f"  ✘ Error: {e}")
        
        print("\nV Scenario defined successfully!")
    
    def _load_scenario(self):
        #Load scenario from file
        print("\n--- Load Scenario from File ---")
        filename = input("Enter filename (JSON/YAML): ").strip()
        
        try:
            from .config_loader import load_scenario
            self.controller = load_scenario(filename, self.config)
            print(f"✓ Scenario loaded from {filename}")
        except Exception as e:
            print(f"✘ Error loading scenario: {e}")
    
    def _configure_detection(self):
        #Configure detection settings
        print("\n" + "=" * 60)
        print("DETECTION SETTINGS")
        print("=" * 60)
        
        print("\n1. Detection Strategy:")
        print("   [1] Immediate (on every block)")
        print("   [2] Periodic (fixed interval)")
        print("   [3] CPU-Triggered (low CPU usage)")
        strategy_choice = input("Choose strategy (1-3): ").strip()
        
        strategy_map = {'1': 'immediate', '2': 'periodic', '3': 'cpu_triggered'}
        self.config.detection_strategy = strategy_map.get(strategy_choice, 'periodic')
        
        if self.config.detection_strategy == 'periodic':
            interval = self._get_float_input("Detection interval (seconds): ", 0.1, 10.0)
            self.config.detection_interval = interval
        
        print("\n2. Recovery Strategy:")
        print("   [1] Priority-based")
        print("   [2] Cost-based (recommended)")
        print("   [3] Time-based")
        print("   [4] Resource-based")
        recovery_choice = input("Choose strategy (1-4): ").strip()
        
        recovery_map = {'1': 'priority', '2': 'cost', '3': 'time', '4': 'resources'}
        self.config.recovery_strategy = recovery_map.get(recovery_choice, 'cost')
        
        print("\n✓ Configuration updated:")
        print(f"   Detection: {self.config.detection_strategy}")
        print(f"   Recovery: {self.config.recovery_strategy}")
    
    def _run_simulation(self):
        #Run complete simulation
        if not self.controller:
            print("\n✘ Please define or load a scenario first!")
            return
        
        print("\n" + "=" * 60)
        print("RUNNING SIMULATION")
        print("=" * 60)
        
        steps = self._get_int_input("Max iterations (0 for unlimited): ", 0, 1000)
        steps = steps if steps > 0 else None
        
        print("\n🚀 Starting simulation...")
        report = self.controller.run_simulation(steps)
        
        print("\n" + "=" * 60)
        print("SIMULATION COMPLETE")
        print("=" * 60)
        self._print_report(report)
    
    def _view_results(self):
        #View current results
        if not self.controller:
            print("\n✘ No simulation data available!")
            return
        
        state = self.controller.get_current_state()
        
        print("\n" + "=" * 60)
        print("CURRENT SYSTEM STATE")
        print("=" * 60)
        print(f"Iteration: {state['iteration']}")
        print(f"System State: {state['system_state']}")
        print(f"Running: {state['running']}")
        
        print("\nProcesses:")
        for pid, proc in state['processes'].items():
            print(f"  {pid}: {proc['state']} (priority={proc['priority']})")
        
        print("\nResources:")
        for rid, res in state['resources'].items():
            print(f"  {rid}: {res['state']} (available={res['available_instances']}/{res['total_instances']})")
    
    def _print_report(self, report: dict):
        #Print simulation report
        summary = report['summary']
        metrics = report['metrics']
        
        print(f"\nIterations: {summary['total_iterations']}")
        print(f"Final System State: {summary['system_final_state']}")
        print(f"\nDetections Run: {metrics['total_detections']}")
        print(f"Deadlocks Found: {metrics['deadlocks_found']}")
        print(f"Processes Terminated: {metrics['processes_terminated']}")
        print(f"Avg Detection Time: {metrics['avg_detection_time']:.2f}ms")
        if metrics['deadlocks_found'] > 0:
            print(f"Avg Recovery Time: {metrics['avg_recovery_time']:.2f}s")
    
    def _get_int_input(self, prompt: str, min_val: int, max_val: int) -> int:
        #Get validated integer input
        while True:
            try:
                value = int(input(prompt))
                if min_val <= value <= max_val:
                    return value
                print(f"Please enter a value between {min_val} and {max_val}")
            except ValueError:
                print("Please enter a valid number")
    
    def _get_float_input(self, prompt: str, min_val: float, max_val: float) -> float:
        #Get validated float input
        while True:
            try:
                value = float(input(prompt))
                if min_val <= value <= max_val:
                    return value
                print(f"Please enter a value between {min_val} and {max_val}")
            except ValueError:
                print("Please enter a valid number")


def main():
    #Entry point for CLI
    cli = CLI()
    try:
        cli.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(0)


if __name__ == '__main__':
    main()