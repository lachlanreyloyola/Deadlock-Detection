#!/usr/bin/env python3
"""
Main entry point for Deadlock Detection and Recovery System
"""
import sys
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.interfaces.cli import CLI
from src.interfaces.config_loader import load_scenario, create_example_scenarios
from src.interfaces.web_api import start_server

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Deadlock Detection and Recovery System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start CLI interface
  python main.py --cli
  
  # Run from config file
  python main.py --config scenarios/simple_deadlock.json
  
  # Start web server
  python main.py --web --port 5000
  
  # Generate example scenarios
  python main.py --generate-scenarios
        """
    )
    
    parser.add_argument('--cli', action='store_true', help='Start interactive CLI interface')
    parser.add_argument('--config', type=str, help='Load and run scenario from config file')
    parser.add_argument('--web', action='store_true', help='Start web server for GUI')
    parser.add_argument('--port', type=int, default=5000, help='Port for web server')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host for web server')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--generate-scenarios', action='store_true', help='Generate example scenarios')
    parser.add_argument('--version', action='version', version='Deadlock Detection System v1.0.0')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.generate_scenarios:
        logger.info("Generating example scenarios...")
        create_example_scenarios()
        print("✅ Example scenarios created in 'scenarios/' directory")
        return 0
    
    if args.cli:
        logger.info("Starting CLI interface...")
        cli = CLI()
        cli.run()
        return 0
    
    if args.config:
        logger.info(f"Loading scenario from {args.config}...")
        try:
            controller = load_scenario(args.config)
            logger.info("Running simulation...")
            report = controller.run_simulation()
            
            print("\n" + "="*60)
            print("SIMULATION COMPLETE")
            print("="*60)
            print(f"Iterations: {report['summary']['total_iterations']}")
            print(f"System State: {report['summary']['system_final_state']}")
            print(f"Deadlocks Found: {report['metrics']['deadlocks_found']}")
            print(f"Processes Terminated: {report['metrics']['processes_terminated']}")
            print("="*60)
            
            return 0
        except Exception as e:
            logger.error(f"Error: {e}")
            return 1
    
    if args.web:
        logger.info(f"Starting web server on {args.host}:{args.port}...")
        print(f"\n🌐 Access web interface at: http://localhost:{args.port}\n")
        start_server(host=args.host, port=args.port, debug=args.debug)
        start_server(debug=True)
        return 0
    
    parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())