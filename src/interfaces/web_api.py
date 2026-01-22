#Flask-based REST API for web GUI

import os
import logging
from typing import Dict

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from ..simulation.controller import SimulationController, SimulationConfig


# -------------------- LOGGING --------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# -------------------- PATH SETUP --------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) # src/interfaces
SRC_DIR = os.path.dirname(CURRENT_DIR) # src
WEB_DIR = os.path.join(SRC_DIR, "web") # src/web

app = Flask(
    __name__,
    template_folder=os.path.join(WEB_DIR, "templates"),
    static_folder=os.path.join(WEB_DIR, "static")
)

CORS(app)


# -------------------- STATE --------------------
active_simulations: Dict[str, SimulationController] = {}
simulation_counter = 0


# -------------------- ROUTES --------------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'active_simulations': len(active_simulations)
    })


@app.route('/api/simulation/create', methods=['POST'])
def create_simulation():
    global simulation_counter

    try:
        data = request.get_json()

        config = SimulationConfig(
            detection_strategy=data.get('detection_strategy', 'periodic'),
            detection_interval=data.get('detection_interval', 1.0),
            recovery_strategy=data.get('recovery_strategy', 'cost')
        )

        controller = SimulationController(config)

        simulation_counter += 1
        sim_id = f"sim_{simulation_counter}"
        active_simulations[sim_id] = controller

        logger.info(f"Created simulation {sim_id}")

        return jsonify({
            'simulation_id': sim_id,
            'status': 'created',
            'config': {
                'detection_strategy': config.detection_strategy,
                'detection_interval': config.detection_interval,
                'recovery_strategy': config.recovery_strategy
            }
        }), 201

    except Exception as e:
        logger.error(f"Error creating simulation: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/simulation/<sim_id>/process', methods=['POST'])
def add_process(sim_id: str):
    if sim_id not in active_simulations:
        return jsonify({'error': 'Simulation not found'}), 404

    try:
        controller = active_simulations[sim_id]
        data = request.get_json()

        process = controller.add_process(
            pid=data['pid'],
            priority=data.get('priority', 5),
            execution_time=data.get('execution_time', 100)
        )

        return jsonify({
            'status': 'success',
            'process': process.to_dict()
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/simulation/<sim_id>/resource', methods=['POST'])
def add_resource(sim_id: str):
    if sim_id not in active_simulations:
        return jsonify({'error': 'Simulation not found'}), 404

    try:
        controller = active_simulations[sim_id]
        data = request.get_json()

        resource = controller.add_resource(
            rid=data['rid'],
            instances=data.get('instances', 1),
            resource_type=data.get('resource_type', 'Generic')
        )

        return jsonify({
            'status': 'success',
            'resource': resource.to_dict()
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/simulation/<sim_id>/request', methods=['POST'])
def request_resource(sim_id: str):
    if sim_id not in active_simulations:
        return jsonify({'error': 'Simulation not found'}), 404

    try:
        controller = active_simulations[sim_id]
        data = request.get_json()

        pid = data['process']
        rid = data['resource']

        process = controller.processes[pid]
        controller.request_resource(pid, rid)

        allocation_result = (
            'allocated' if rid in process.held_resources else 'blocked'
        )

        return jsonify({
            'status': 'success',
            'allocation_result': allocation_result,
            'process_state': process.state,
            'system_state': controller.system_state.state
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/simulation/<sim_id>/run', methods=['POST'])
def run_simulation(sim_id: str):
    if sim_id not in active_simulations:
        return jsonify({'error': 'Simulation not found'}), 404

    try:
        controller = active_simulations[sim_id]
        data = request.get_json() or {}

        steps = data.get('steps')
        report = controller.run_simulation(steps=steps)

        return jsonify({
            'status': 'complete',
            'report': report
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/simulation/<sim_id>/state', methods=['GET'])
def get_state(sim_id: str):
    if sim_id not in active_simulations:
        return jsonify({'error': 'Simulation not found'}), 404

    try:
        controller = active_simulations[sim_id]
        return jsonify(controller.get_current_state()), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/simulation/<sim_id>/reset', methods=['POST'])
def reset_simulation(sim_id: str):
    if sim_id not in active_simulations:
        return jsonify({'error': 'Simulation not found'}), 404

    try:
        active_simulations[sim_id].reset()
        return jsonify({'status': 'reset'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


# -------------------- SERVER --------------------
def start_server(host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
    logger.info(f"Starting Flask server on {host}:{port}")
    logger.info(f"Access web interface at http://localhost:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    start_server(debug=True)
