"""
Custom exceptions for Hack Tractor educational toolkit.

Defines application-specific exceptions for better error handling
and educational debugging.
"""


class HackTractorError(Exception):
    """Base exception for Hack Tractor application."""
    
    def __init__(self, message: str, error_code: int = 1):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self):
        return f"[Error {self.error_code}] {self.message}"


class SafetyError(HackTractorError):
    """Raised when safety checks fail or unsafe operations are attempted."""
    
    def __init__(self, message: str):
        super().__init__(f"SAFETY VIOLATION: {message}", error_code=30)


class EquipmentError(HackTractorError):
    """Raised when equipment communication or control fails."""
    
    def __init__(self, message: str, equipment_type: str = "unknown"):
        self.equipment_type = equipment_type
        super().__init__(
            f"Equipment Error ({equipment_type}): {message}", 
            error_code=10
        )


class CommunicationError(HackTractorError):
    """Raised when communication with equipment fails."""
    
    def __init__(self, message: str, protocol: str = "unknown"):
        self.protocol = protocol
        super().__init__(
            f"Communication Error ({protocol}): {message}",
            error_code=20
        )


class AIModelError(HackTractorError):
    """Raised when AI model operations fail."""
    
    def __init__(self, message: str, model_name: str = "unknown"):
        self.model_name = model_name
        super().__init__(
            f"AI Model Error ({model_name}): {message}",
            error_code=40
        )


class DataError(HackTractorError):
    """Raised when data validation or processing fails."""
    
    def __init__(self, message: str, data_type: str = "unknown"):
        self.data_type = data_type
        super().__init__(
            f"Data Error ({data_type}): {message}",
            error_code=50
        )


class ConfigurationError(HackTractorError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str):
        super().__init__(f"Configuration Error: {message}", error_code=60)


class SimulationError(HackTractorError):
    """Raised when simulation encounters problems."""
    
    def __init__(self, message: str, simulator: str = "unknown"):
        self.simulator = simulator
        super().__init__(
            f"Simulation Error ({simulator}): {message}",
            error_code=70
        )
