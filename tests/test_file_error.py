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


@dataclass
class NestedConfig:
    """Nested configuration for testing deeper merges."""
    nested_value: int = 0
    nested_name: str = "default_nested"


@dataclass
class ComplexTestConfig:
    """A more complex test configuration with nested dataclasses."""
    config: Optional[Path] = None
    value: int = 42
    name: str = "default"
    nested: NestedConfig = field(default_factory=NestedConfig)


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


def test_multi_config_basic(tmp_path):
    """Test basic functionality of multiple config files."""
    config_manager = ConfigManager(
        config_class=SimpleTestConfig,
    )
    
    # Create two config files
    config1 = tmp_path / "config1.yaml"
    config1.write_text("""
    value: 100
    """)
    
    config2 = tmp_path / "config2.yaml"
    config2.write_text("""
    name: from_config2
    """)
    
    # Test with multiple config files
    config = config_manager.parse_args([
        "--config", str(config1),
        "--config", str(config2)
    ])
    
    # Values should be merged with config2 taking precedence
    assert config.value == 100  # From config1
    assert config.name == "from_config2"  # From config2


def test_multi_config_with_cli_override(tmp_path):
    """Test that CLI arguments override multiple config files."""
    config_manager = ConfigManager(
        config_class=SimpleTestConfig,
    )
    
    # Create config files
    config1 = tmp_path / "config1.yaml"
    config1.write_text("""
    value: 100
    name: from_config1
    """)
    
    config2 = tmp_path / "config2.yaml"
    config2.write_text("""
    value: 200
    """)
    
    # Test with multiple config files and CLI override
    config = config_manager.parse_args([
        "--config", str(config1),
        "--config", str(config2),
        "--value", "300"  # CLI override
    ])
    
    # CLI args should override all config files
    assert config.value == 300  # From CLI (overrides config1 and config2)
    assert config.name == "from_config1"  # From config1 (not overridden)
    # The config field should point to the last config file
    assert config.config == config2


def test_nested_config_merging(tmp_path):
    """Test merging of nested configuration structures."""
    config_manager = ConfigManager(
        config_class=ComplexTestConfig,
    )
    
    # Create config files with nested structures
    config1 = tmp_path / "config1.yaml"
    config1.write_text("""
    value: 100
    nested:
      nested_value: 500
    """)
    
    config2 = tmp_path / "config2.yaml"
    config2.write_text("""
    name: from_config2
    nested:
      nested_name: from_config2_nested
    """)
    
    # Test with multiple config files
    config = config_manager.parse_args([
        "--config", str(config1),
        "--config", str(config2)
    ])
    
    # Values should be deeply merged
    assert config.value == 100  # From config1
    assert config.name == "from_config2"  # From config2
    assert config.nested.nested_value == 500  # From config1
    assert config.nested.nested_name == "from_config2_nested"  # From config2


if __name__ == "__main__":
    pytest.main(["-v", __file__])
