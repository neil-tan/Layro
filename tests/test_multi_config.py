"""
Tests for multiple configuration file support.
"""

import pytest
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List

from layro.manager import ConfigManager
from layro.loaders import load_yaml_config


@dataclass
class MultiConfigTest:
    """Test configuration for multi-config testing."""
    config: Optional[Path] = None
    value: int = 1
    name: str = "default"
    nested_value: Optional[int] = None
    list_values: List[str] = field(default_factory=list)


def test_multi_config_layering(tmp_path):
    """Test that multiple configuration files are layered correctly."""
    # Create config manager
    config_manager = ConfigManager(
        config_class=MultiConfigTest,
    )
    
    # Create config files
    # Config 1: Sets base values
    config1 = tmp_path / "config1.yaml"
    config1.write_text("""
    value: 10
    name: config1
    list_values:
      - item1
      - item2
    """)
    
    # Config 2: Overrides some values, adds nested_value
    config2 = tmp_path / "config2.yaml"
    config2.write_text("""
    value: 20
    nested_value: 100
    list_values:
      - item3
      - item4
    """)
    
    # Config 3: Final overrides
    config3 = tmp_path / "config3.yaml"
    config3.write_text("""
    name: config3
    """)
    
    # Test with a single config file
    config_single = config_manager.parse_args(["--config", str(config1)])
    assert config_single.value == 10
    assert config_single.name == "config1"
    assert config_single.nested_value is None
    assert config_single.list_values == ["item1", "item2"]
    
    # Test with two config files (config2 overrides config1)
    config_two = config_manager.parse_args(["--config", str(config1), "--config", str(config2)])
    assert config_two.value == 20  # From config2
    assert config_two.name == "config1"  # From config1 (not overridden)
    assert config_two.nested_value == 100  # From config2
    assert config_two.list_values == ["item3", "item4"]  # From config2
    
    # Test with three config files
    config_three = config_manager.parse_args([
        "--config", str(config1), 
        "--config", str(config2), 
        "--config", str(config3)
    ])
    assert config_three.value == 20  # From config2 (not overridden by config3)
    assert config_three.name == "config3"  # From config3
    assert config_three.nested_value == 100  # From config2 (not overridden by config3)
    assert config_three.list_values == ["item3", "item4"]  # From config2 (not overridden by config3)


def test_multi_config_with_cli_overrides(tmp_path):
    """Test that CLI args override all config files."""
    # Create config manager
    config_manager = ConfigManager(
        config_class=MultiConfigTest,
    )
    
    # Create config files
    config1 = tmp_path / "config1.yaml"
    config1.write_text("""
    value: 10
    name: config1
    """)
    
    config2 = tmp_path / "config2.yaml"
    config2.write_text("""
    value: 20
    name: config2
    """)
    
    # Test that CLI args override config files
    config = config_manager.parse_args([
        "--config", str(config1), 
        "--config", str(config2), 
        "--value", "30",
        "--name", "cli_override"
    ])
    
    assert config.value == 30  # From CLI
    assert config.name == "cli_override"  # From CLI
    assert config.config == config2  # Should be the last config file


if __name__ == "__main__":
    pytest.main(["-v", __file__])
