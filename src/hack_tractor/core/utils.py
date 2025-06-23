"""
Utility functions for Hack Tractor educational toolkit.

Common utilities for logging, safety checks, validation,
and other shared functionality.
"""

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .constants import (
    DEFAULT_LOG_DIR,
    EMERGENCY_STOP_TIMEOUT,
    MAX_COMMAND_RATE,
    SAFETY_CHECKS_ENABLED,
)
from .exceptions import SafetyError


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        format_string: Custom format string for log messages
        
    Returns:
        Configured logger instance
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )
    
    logger = logging.getLogger("hack_tractor")
    logger.info(f"Logging initialized at level {level}")
    
    return logger


def validate_safety_checks(
    operation: str,
    parameters: Dict[str, Any],
    emergency_stop_active: bool = False
) -> bool:
    """
    Validate safety checks before performing equipment operations.
    
    Args:
        operation: Name of the operation being performed
        parameters: Operation parameters to validate
        emergency_stop_active: Whether emergency stop is currently active
        
    Returns:
        True if safety checks pass
        
    Raises:
        SafetyError: If safety validation fails
    """
    if not SAFETY_CHECKS_ENABLED:
        return True
    
    # Check for emergency stop
    if emergency_stop_active:
        raise SafetyError(
            f"Emergency stop active - cannot perform operation: {operation}"
        )
    
    # Validate operation name
    if not operation or not isinstance(operation, str):
        raise SafetyError("Invalid operation name")
    
    # Validate parameters
    if not isinstance(parameters, dict):
        raise SafetyError("Invalid operation parameters")
    
    # Check for required safety parameters
    if "safety_override" in parameters and not parameters["safety_override"]:
        raise SafetyError("Safety override required for this operation")
    
    return True


class RateLimiter:
    """Rate limiter for equipment commands to prevent overload."""
    
    def __init__(self, max_rate: float = MAX_COMMAND_RATE):
        """
        Initialize rate limiter.
        
        Args:
            max_rate: Maximum commands per second
        """
        self.max_rate = max_rate
        self.min_interval = 1.0 / max_rate
        self.last_command_time = 0.0
    
    def can_execute(self) -> bool:
        """Check if a command can be executed without exceeding rate limit."""
        current_time = time.time()
        time_since_last = current_time - self.last_command_time
        return time_since_last >= self.min_interval
    
    def wait_if_needed(self) -> None:
        """Wait if necessary to respect rate limit."""
        current_time = time.time()
        time_since_last = current_time - self.last_command_time
        
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_command_time = time.time()


def format_sensor_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format and validate sensor data for consistency.
    
    Args:
        data: Raw sensor data dictionary
        
    Returns:
        Formatted sensor data
    """
    formatted = {}
    
    for key, value in data.items():
        # Add timestamp if missing
        if key == "timestamp" and value is None:
            formatted[key] = time.time()
        # Format numeric values
        elif isinstance(value, (int, float)):
            formatted[key] = round(float(value), 3)
        # Keep string values as-is
        elif isinstance(value, str):
            formatted[key] = value
        else:
            formatted[key] = str(value)
    
    return formatted


def validate_equipment_parameters(parameters: Dict[str, Any]) -> bool:
    """
    Validate equipment operation parameters for safety and correctness.
    
    Args:
        parameters: Equipment parameters to validate
        
    Returns:
        True if parameters are valid
        
    Raises:
        SafetyError: If parameters are unsafe
        ValueError: If parameters are invalid
    """
    required_keys = ["command", "value"]
    
    # Check required keys
    for key in required_keys:
        if key not in parameters:
            raise ValueError(f"Missing required parameter: {key}")
    
    # Validate command
    command = parameters["command"]
    if not isinstance(command, str) or not command.strip():
        raise ValueError("Invalid command format")
    
    # Safety check for dangerous commands
    dangerous_commands = ["emergency_stop", "system_shutdown", "factory_reset"]
    if command in dangerous_commands and not parameters.get("confirmed", False):
        raise SafetyError(f"Dangerous command requires confirmation: {command}")
    
    return True


def create_emergency_stop() -> Dict[str, Any]:
    """
    Create an emergency stop command with proper safety protocols.
    
    Returns:
        Emergency stop command dictionary
    """
    return {
        "command": "emergency_stop",
        "timestamp": time.time(),
        "timeout": EMERGENCY_STOP_TIMEOUT,
        "priority": "critical",
        "safety_verified": True
    }
