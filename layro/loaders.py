"""
Configuration file loaders for the config manager.

This module provides functions for loading configuration from different file formats.
Currently supports YAML, with potential for extension to JSON, TOML, etc.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional


def load_yaml_config(file_path: Path) -> Dict[str, Any]:
    """Load a YAML file into a dictionary.
    
    Args:
        file_path: Path to the YAML file
        
    Returns:
        Dictionary containing the YAML contents
        
    Raises:
        FileNotFoundError: If the file does not exist
        yaml.YAMLError: If the YAML is invalid
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Config file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        try:
            return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing YAML file {file_path}: {e}")


def find_config_file(
    file_path: Optional[Path] = None, 
    default_locations: list = None,
    required: bool = False
) -> Optional[Path]:
    """Find a configuration file in the specified location or default locations.
    
    Args:
        file_path: Explicitly provided file path
        default_locations: List of default locations to check
        required: Whether the file is required
        
    Returns:
        Path to the found config file, or None if not found and not required
        
    Raises:
        FileNotFoundError: If the file is required but not found
    """
    # If file path is explicitly provided, use it
    if file_path is not None:
        if file_path.exists():
            return file_path
        elif required:
            raise FileNotFoundError(f"Required config file not found: {file_path}")
        else:
            return None
            
    # Check default locations
    if default_locations:
        for location in default_locations:
            if location.exists():
                return location
    
    # Not found
    if required:
        raise FileNotFoundError(f"Required config file not found in default locations: {default_locations}")
    
    return None 