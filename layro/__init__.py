"""
Configuration management utilities for handling multi-layered configs with CLI, YAML, and defaults.

This package provides tools to manage configuration from multiple sources with proper priority ordering:
1. Command-Line Arguments (CLI)
2. User Config File (specified by --config)
3. Mode-specific Default Config
4. Base Default Config
5. Dataclass Defaults

Example usage:
    from dataclasses import dataclass
    from layro import ConfigManager
    
    @dataclass
    class MyConfig:
        learning_rate: float = 0.01
        batch_size: int = 32
        
    # Create a config manager
    config_manager = ConfigManager(
        config_class=MyConfig,
        default_config_dir="configs"
    )
    
    # Parse arguments
    config = config_manager.parse_args()
"""

from .manager import ConfigManager
from .converters import (
    convert_value_to_type,
    dataclass_to_dict,
    dict_to_dataclass,
    deep_merge,
)

__all__ = [
    "ConfigManager",
    "convert_value_to_type",
    "dataclass_to_dict", 
    "dict_to_dataclass",
    "deep_merge",
]

__version__ = "0.1.0"