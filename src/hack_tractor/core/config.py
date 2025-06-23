"""
Configuration management for Hack Tractor educational toolkit.

Handles application configuration, environment variables,
and default settings for the educational demonstration.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


@dataclass
class EquipmentConfig:
    """Equipment interface configuration."""
    default_interface: str = "can"
    can_interface: str = "socketcan"
    baudrate: int = 500000
    timeout: float = 1.0


@dataclass
class AIConfig:
    """AI model configuration."""
    model_path: str = "models/"
    prediction_threshold: float = 0.85
    retrain_interval: str = "7d"


@dataclass
class DashboardConfig:
    """Dashboard configuration."""
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "hack_tractor.log"


@dataclass
class Config:
    """Main application configuration."""
    equipment: EquipmentConfig
    ai: AIConfig
    dashboard: DashboardConfig
    logging: LoggingConfig

    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """Load configuration from YAML file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        return cls(
            equipment=EquipmentConfig(**data.get('equipment', {})),
            ai=AIConfig(**data.get('ai', {})),
            dashboard=DashboardConfig(**data.get('dashboard', {})),
            logging=LoggingConfig(**data.get('logging', {}))
        )

    @classmethod
    def default(cls) -> "Config":
        """Create default configuration."""
        return cls(
            equipment=EquipmentConfig(),
            ai=AIConfig(),
            dashboard=DashboardConfig(),
            logging=LoggingConfig()
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'equipment': self.equipment.__dict__,
            'ai': self.ai.__dict__,
            'dashboard': self.dashboard.__dict__,
            'logging': self.logging.__dict__
        }


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        config_path = os.getenv('HACK_TRACTOR_CONFIG_PATH')
        if config_path and os.path.exists(config_path):
            _config = Config.from_file(config_path)
        else:
            _config = Config.default()
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config


def reload_config() -> Config:
    """Reload configuration from file."""
    global _config
    _config = None
    return get_config()
