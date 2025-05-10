"""
Test that the CLI errors out when a config file does not exist or has errors.
"""

import pytest
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List

from layro.manager import ConfigManager
from layro.loaders import load_yaml_config


@dataclass
class SimpleTestConfig:
    """A simple test configuration for the file error tests."""
    config: Optional[Path] = None
    value: int = 42
    name: str = "default"


def test_error_on_nonexistent_config_file(tmp_path):
    """Test that an error is raised when the specified config file does not exist."""
    config_manager = ConfigManager(
        config_class=SimpleTestConfig,
    )
    
    # Specify a non-existent config file
    non_existent_file = tmp_path / "does_not_exist.yaml"
    
    # This should raise a FileNotFoundError
    with pytest.raises(FileNotFoundError):
        config_manager.parse_args(["--config", str(non_existent_file)])


def test_error_on_invalid_yaml(tmp_path):
    """Test that an error is raised when the specified config file has invalid YAML."""
    config_manager = ConfigManager(
        config_class=SimpleTestConfig,
    )
    
    # Create a file with invalid YAML
    invalid_yaml_file = tmp_path / "invalid.yaml"
    invalid_yaml_file.write_text("""
    value: 100
    name: "unclosed string
    """)
    
    # This should raise a YAMLError
    with pytest.raises(Exception) as excinfo:
        config_manager.parse_args(["--config", str(invalid_yaml_file)])
    assert "YAML" in str(excinfo.value)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
