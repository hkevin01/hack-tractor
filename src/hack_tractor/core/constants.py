"""
Constants for Hack Tractor educational toolkit.

Application-wide constants for equipment interfaces,
AI models, and safety parameters.
"""

# Application Information
APP_NAME = "Hack Tractor"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "Educational Agricultural Equipment Interface Toolkit"

# Educational and Safety
EDUCATIONAL_MODE = True
SAFETY_CHECKS_ENABLED = True
SIMULATION_MODE = True

# Equipment Interface Constants
EQUIPMENT_TYPES = [
    "tractor",
    "harvester", 
    "planter",
    "sprayer",
    "cultivator"
]

# Communication Protocols
CAN_BUS_PROTOCOLS = [
    "j1939",
    "iso11783",
    "custom"
]

OBD_PROTOCOLS = [
    "iso15765",
    "iso14230",
    "iso9141"
]

# Safety Parameters
EMERGENCY_STOP_TIMEOUT = 0.5  # seconds
MAX_COMMAND_RATE = 10  # commands per second
SAFETY_CHECK_INTERVAL = 1.0  # seconds

# AI Model Constants
MIN_PREDICTION_CONFIDENCE = 0.7
MAX_MODEL_AGE_DAYS = 30
MODEL_RETRAIN_THRESHOLD = 0.1  # accuracy drop

# Data Processing
MAX_SENSOR_VALUE_AGE = 5.0  # seconds
DATA_BUFFER_SIZE = 1000
REAL_TIME_THRESHOLD = 0.1  # seconds

# Dashboard Constants
DEFAULT_REFRESH_RATE = 1.0  # seconds
MAX_CHART_POINTS = 100
MOBILE_BREAKPOINT = 768  # pixels

# File and Directory Paths
DEFAULT_MODEL_DIR = "models"
DEFAULT_DATA_DIR = "data" 
DEFAULT_LOG_DIR = "logs"
DEFAULT_CONFIG_FILE = "config.yml"

# Equipment Simulation Parameters
SIMULATION_UPDATE_RATE = 0.1  # seconds
SENSOR_NOISE_LEVEL = 0.05  # 5% noise
FAILURE_SIMULATION_RATE = 0.001  # 0.1% chance per update

# Network and API
DEFAULT_API_TIMEOUT = 30.0  # seconds
MAX_RETRY_ATTEMPTS = 3
API_RATE_LIMIT = 100  # requests per minute

# Security
MIN_PASSWORD_LENGTH = 8
SESSION_TIMEOUT = 3600  # seconds
MAX_LOGIN_ATTEMPTS = 5

# Status Codes
class StatusCodes:
    """Equipment and system status codes."""
    OK = 0
    WARNING = 1
    ERROR = 2
    CRITICAL = 3
    UNKNOWN = 4


# Error Codes
class ErrorCodes:
    """Application error codes."""
    SUCCESS = 0
    GENERAL_ERROR = 1
    EQUIPMENT_ERROR = 10
    COMMUNICATION_ERROR = 20
    SAFETY_ERROR = 30
    AI_MODEL_ERROR = 40
    DATA_ERROR = 50
