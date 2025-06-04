#!/usr/bin/env python3
"""
Hack Tractor - Main Application Entry Point

This script serves as the main entry point for the Hack Tractor application,
integrating equipment interfaces, AI models, and the dashboard.
"""

import os
import sys
import logging
import argparse
import json
import time
from pathlib import Path
import importlib
import threading
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"hack_tractor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("hack_tractor")

# Ensure necessary directories exist in project structure
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
CONFIG_DIR = PROJECT_ROOT / "config"
MODELS_DIR = PROJECT_ROOT / "models"

for directory in [DATA_DIR, LOGS_DIR, CONFIG_DIR, MODELS_DIR]:
    directory.mkdir(exist_ok=True)

def check_dependencies():
    """Check if all required dependencies are installed."""
    required_modules = [
        "numpy", "pandas", "tensorflow", "torch", "fastapi", "uvicorn",
        "can", "obd", "pyserial", "pymodbus", "opencv-python"
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            importlib.import_module(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        logger.error(f"Missing required dependencies: {', '.join(missing_modules)}")
        logger.info("Please install missing dependencies with: pip install -r requirements.txt")
        return False
    return True

def load_config(config_path):
    """Load configuration from a JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Config file not found: {config_path}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in config file: {config_path}")
        return {}

def initialize_equipment_interfaces(config):
    """Initialize equipment interfaces based on configuration."""
    interfaces = {}
    
    # Initialize CAN interface if configured
    if config.get("enable_can", False):
        try:
            from src.equipment.interfaces.can.tractor_can_interface import TractorCANInterface
            
            can_config = config.get("can", {})
            can_interface = TractorCANInterface(
                channel=can_config.get("channel", "can0"),
                bustype=can_config.get("bustype", "socketcan"),
                bitrate=can_config.get("bitrate", 250000),
                config_file=can_config.get("config_file")
            )
            
            if can_interface.connect():
                interfaces["can"] = can_interface
                logger.info("CAN interface initialized successfully")
                
                # Start monitoring if configured
                if can_config.get("auto_monitor", True):
                    can_interface.start_monitoring()
        except Exception as e:
            logger.error(f"Failed to initialize CAN interface: {e}")
    
    # Initialize OBD interface if configured
    if config.get("enable_obd", False):
        try:
            from src.equipment.interfaces.obd.tractor_obd_interface import TractorOBDInterface
            
            obd_config = config.get("obd", {})
            obd_interface = TractorOBDInterface(
                portstr=obd_config.get("port"),
                baudrate=obd_config.get("baudrate", 38400),
                protocol=obd_config.get("protocol"),
                config_file=obd_config.get("config_file")
            )
            
            if obd_interface.connect():
                interfaces["obd"] = obd_interface
                logger.info("OBD interface initialized successfully")
                
                # Start monitoring if configured
                if obd_config.get("auto_monitor", True):
                    commands = obd_config.get("monitor_commands")
                    interval = obd_config.get("monitor_interval", 1.0)
                    obd_interface.start_monitoring(commands, interval)
        except Exception as e:
            logger.error(f"Failed to initialize OBD interface: {e}")
    
    # Initialize John Deere API if configured
    if config.get("enable_john_deere_api", False):
        try:
            from src.equipment.interfaces.john_deere.john_deere_client import JohnDeereClient
            
            jd_config = config.get("john_deere_api", {})
            jd_client = JohnDeereClient(
                client_id=jd_config.get("client_id", ""),
                client_secret=jd_config.get("client_secret", ""),
                redirect_uri=jd_config.get("redirect_uri", ""),
                config_file=jd_config.get("config_file")
            )
            
            # Set organization if provided
            if jd_config.get("organization_id"):
                jd_client.set_organization(jd_config["organization_id"])
                
            interfaces["john_deere"] = jd_client
            logger.info("John Deere API client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize John Deere API client: {e}")
    
    return interfaces

def initialize_ai_models(config):
    """Initialize AI models based on configuration."""
    models = {}
    
    # Initialize predictive maintenance model if configured
    if config.get("enable_predictive_maintenance", False):
        try:
            from src.ai.models.predictive_maintenance import PredictiveMaintenanceModel
            
            pm_config = config.get("predictive_maintenance", {})
            pm_model = PredictiveMaintenanceModel(config=pm_config)
            
            # Load pre-trained model if specified
            model_path = pm_config.get("model_path")
            if model_path and os.path.exists(model_path):
                pm_model.load(model_path)
                logger.info(f"Loaded predictive maintenance model from {model_path}")
            
            models["predictive_maintenance"] = pm_model
            logger.info("Predictive maintenance model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize predictive maintenance model: {e}")
    
    return models

def start_backend_server(config, interfaces, models):
    """Start the FastAPI backend server in a separate thread."""
    if not config.get("enable_backend", True):
        logger.info("Backend server disabled in configuration")
        return None
    
    try:
        import uvicorn
        from fastapi import FastAPI
        
        # Create a simple FastAPI app or import the existing one
        try:
            from src.backend.app import app
            # Update app state with interfaces and models
            app.state.interfaces = interfaces
            app.state.models = models
            app.state.config = config
        except ImportError:
            # Create a minimal app if the main one isn't available
            app = FastAPI(title="Hack Tractor API")
            
            @app.get("/")
            async def root():
                return {"message": "Hack Tractor API is running"}
            
            @app.get("/status")
            async def status():
                return {
                    "interfaces": list(interfaces.keys()),
                    "models": list(models.keys()),
                    "timestamp": datetime.now().isoformat()
                }
        
        # Get configuration for the server
        host = config.get("backend", {}).get("host", "0.0.0.0")
        port = config.get("backend", {}).get("port", 8000)
        
        # Start server in a separate thread
        server_thread = threading.Thread(
            target=uvicorn.run,
            args=(app,),
            kwargs={"host": host, "port": port},
            daemon=True
        )
        server_thread.start()
        
        logger.info(f"Backend server started at http://{host}:{port}")
        return server_thread
    except Exception as e:
        logger.error(f"Failed to start backend server: {e}")
        return None

def data_collection_loop(interfaces, models, config):
    """Main data collection loop."""
    collection_interval = config.get("data_collection", {}).get("interval", 60)
    save_interval = config.get("data_collection", {}).get("save_interval", 300)
    last_save_time = time.time()
    
    logger.info(f"Starting data collection loop (interval: {collection_interval}s)")
    
    try:
        while True:
            # Collect data from interfaces
            collected_data = {}
            
            for name, interface in interfaces.items():
                try:
                    if name == "can" and hasattr(interface, "get_data"):
                        collected_data[name] = interface.get_data()
                    elif name == "obd" and hasattr(interface, "get_data"):
                        collected_data[name] = interface.get_data()
                except Exception as e:
                    logger.error(f"Error collecting data from {name} interface: {e}")
            
            # Process data with AI models if needed
            for name, model in models.items():
                try:
                    if name == "predictive_maintenance" and hasattr(model, "predict"):
                        # This would need proper data preparation in a real scenario
                        pass
                except Exception as e:
                    logger.error(f"Error processing data with {name} model: {e}")
            
            # Save data periodically
            current_time = time.time()
            if current_time - last_save_time >= save_interval:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Save interface data
                for name, interface in interfaces.items():
                    try:
                        if name == "can" and hasattr(interface, "save_log"):
                            interface.save_log(str(DATA_DIR / f"can_log_{timestamp}.json"))
                        elif name == "obd" and hasattr(interface, "save_log"):
                            interface.save_log(str(DATA_DIR / f"obd_log_{timestamp}.json"))
                        elif name == "john_deere" and hasattr(interface, "save_equipment_data"):
                            interface.save_equipment_data(str(DATA_DIR / f"jd_data_{timestamp}.json"))
                    except Exception as e:
                        logger.error(f"Error saving data from {name} interface: {e}")
                
                last_save_time = current_time
                logger.info(f"Saved data at {timestamp}")
            
            # Sleep until next collection
            time.sleep(collection_interval)
    except KeyboardInterrupt:
        logger.info("Data collection loop interrupted")
    except Exception as e:
        logger.error(f"Error in data collection loop: {e}")

def cleanup(interfaces):
    """Clean up resources before exiting."""
    logger.info("Cleaning up resources...")
    
    for name, interface in interfaces.items():
        try:
            if hasattr(interface, "disconnect"):
                interface.disconnect()
                logger.info(f"Disconnected {name} interface")
        except Exception as e:
            logger.error(f"Error disconnecting {name} interface: {e}")

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Hack Tractor - Farm Equipment Control System")
    parser.add_argument("-c", "--config", default="config/config.json", help="Path to configuration file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--simulation", action="store_true", help="Run in simulation mode without real hardware")
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting Hack Tractor")
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Load configuration
    config_path = args.config
    if not os.path.isabs(config_path):
        config_path = os.path.join(PROJECT_ROOT, config_path)
    
    config = load_config(config_path)
    
    # Override config for simulation mode
    if args.simulation:
        logger.info("Running in simulation mode")
        config["simulation_mode"] = True
        config["enable_can"] = False
        config["enable_obd"] = False
        # TODO: Add simulation interfaces if needed
    
    # Initialize components
    interfaces = initialize_equipment_interfaces(config)
    models = initialize_ai_models(config)
    
    # Start backend server
    server_thread = start_backend_server(config, interfaces, models)
    
    try:
        # Run the main data collection loop
        data_collection_loop(interfaces, models, config)
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    finally:
        # Clean up resources
        cleanup(interfaces)
    
    logger.info("Hack Tractor stopped")
    return 0

if __name__ == "__main__":
    sys.exit(main())
