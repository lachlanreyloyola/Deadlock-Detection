#Configuration file loader for JSON/YAML scenarios

import json
import yaml
import logging
from pathlib import Path
from ..simulation.controller import SimulationController, SimulationConfig

logger = logging.getLogger(__name__)


def load_scenario(filename: str, config: SimulationConfig = None) -> SimulationController:
    #Load scenario from JSON or YAML file
    filepath = Path(filename)
    
    if not filepath.exists():
        raise FileNotFoundError(f"Configuration file not found: {filename}")
    
    with open(filepath, 'r') as f:
        if filepath.suffix == '.json':
            data = json.load(f)
        elif filepath.suffix in ['.yaml', '.yml']:
            data = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported file format: {filepath.suffix}")
    
    logger.info(f"Loaded scenario: {data.get('scenario_name', 'Unnamed')}")
    
    if config is None:
        config = SimulationConfig()
    
    if 'detection_strategy' in data:
        config.detection_strategy = data['detection_strategy']
    if 'detection_interval' in data:
        config.detection_interval = data['detection_interval']
    if 'recovery_strategy' in data:
        config.recovery_strategy = data['recovery_strategy']
    
    controller = SimulationController(config)
    
    for proc_data in data.get('processes', []):
        controller.add_process(
            pid=proc_data['pid'],
            priority=proc_data.get('priority', 5),
            execution_time=proc_data.get('execution_time', 100)
        )
    
    for res_data in data.get('resources', []):
        controller.add_resource(
            rid=res_data['rid'],
            instances=res_data.get('instances', 1),
            resource_type=res_data.get('type', 'Generic')
        )
    
    for alloc in data.get('initial_allocations', []):
        try:
            controller.request_resource(alloc['process'], alloc['resource'])
        except Exception as e:
            logger.warning(f"Failed to allocate: {e}")
    
    for req in data.get('resource_requests', []):
        try:
            controller.request_resource(req['process'], req['resource'])
        except Exception as e:
            logger.warning(f"Failed to request: {e}")
    
    logger.info(f"Scenario loaded: {len(controller.processes)} processes, {len(controller.resources)} resources")
    return controller


def create_example_scenarios():
    #Create example scenario files
    scenarios_dir = Path('scenarios')
    scenarios_dir.mkdir(exist_ok=True)
    
    simple_deadlock = {
        "scenario_name": "Simple Two-Process Deadlock",
        "detection_strategy": "periodic",
        "detection_interval": 1.0,
        "recovery_strategy": "cost",
        "processes": [
            {"pid": "P1", "priority": 5, "execution_time": 100},
            {"pid": "P2", "priority": 5, "execution_time": 100}
        ],
        "resources": [
            {"rid": "R1", "instances": 1, "type": "CPU"},
            {"rid": "R2", "instances": 1, "type": "Memory"}
        ],
        "initial_allocations": [
            {"process": "P1", "resource": "R1"},
            {"process": "P2", "resource": "R2"}
        ],
        "resource_requests": [
            {"process": "P1", "resource": "R2"},
            {"process": "P2", "resource": "R1"}
        ]
    }
    
    with open(scenarios_dir / 'simple_deadlock.json', 'w') as f:
        json.dump(simple_deadlock, f, indent=2)
    
    complex_deadlock = {
        "scenario_name": "Three-Process Circular Deadlock",
        "detection_strategy": "periodic",
        "detection_interval": 0.5,
        "recovery_strategy": "priority",
        "processes": [
            {"pid": "P1", "priority": 3, "execution_time": 150},
            {"pid": "P2", "priority": 5, "execution_time": 200},
            {"pid": "P3", "priority": 7, "execution_time": 100}
        ],
        "resources": [
            {"rid": "R1", "instances": 1, "type": "File"},
            {"rid": "R2", "instances": 1, "type": "Printer"},
            {"rid": "R3", "instances": 1, "type": "Database"}
        ],
        "initial_allocations": [
            {"process": "P1", "resource": "R1"},
            {"process": "P2", "resource": "R2"},
            {"process": "P3", "resource": "R3"}
        ],
        "resource_requests": [
            {"process": "P1", "resource": "R2"},
            {"process": "P2", "resource": "R3"},
            {"process": "P3", "resource": "R1"}
        ]
    }
    
    with open(scenarios_dir / 'complex_deadlock.json', 'w') as f:
        json.dump(complex_deadlock, f, indent=2)
    
    no_deadlock = {
        "scenario_name": "Safe System - No Deadlock",
        "detection_strategy": "periodic",
        "detection_interval": 1.0,
        "recovery_strategy": "cost",
        "processes": [
            {"pid": "P1", "priority": 5, "execution_time": 100},
            {"pid": "P2", "priority": 5, "execution_time": 100}
        ],
        "resources": [
            {"rid": "R1", "instances": 2, "type": "CPU"},
            {"rid": "R2", "instances": 1, "type": "Memory"}
        ],
        "initial_allocations": [
            {"process": "P1", "resource": "R1"}
        ],
        "resource_requests": [
            {"process": "P2", "resource": "R1"}
        ]
    }
    
    with open(scenarios_dir / 'no_deadlock.json', 'w') as f:
        json.dump(no_deadlock, f, indent=2)
    
    logger.info("Example scenarios created in 'scenarios/' directory")


if __name__ == '__main__':
    create_example_scenarios()