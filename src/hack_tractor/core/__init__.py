"""
Core module for Hack Tractor educational toolkit.

This module provides fundamental utilities, configuration management,
and shared components used throughout the application.
"""

from .config import Config, get_config
from .constants import (
    CAN_BUS_PROTOCOLS,
    EQUIPMENT_TYPES,
    OBD_PROTOCOLS,
    SAFETY_CHECKS_ENABLED,
    SIMULATION_MODE,
)
from .exceptions import EquipmentError, HackTractorError, SafetyError
from .utils import setup_logging, validate_safety_checks

__all__ = [
    "Config",
    "get_config",
    "EQUIPMENT_TYPES",
    "CAN_BUS_PROTOCOLS", 
    "OBD_PROTOCOLS",
    "SAFETY_CHECKS_ENABLED",
    "SIMULATION_MODE",
    "HackTractorError",
    "SafetyError",
    "EquipmentError",
    "setup_logging",
    "validate_safety_checks",
]
