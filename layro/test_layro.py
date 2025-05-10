"""
Test suite for the Layro package.

This module provides comprehensive test cases for:
- Type conversion utilities
- Dictionary merging and conversion
- YAML configuration loading
- Layered configuration priority
- CLI argument handling
- Integration tests for full configuration flow
"""

import pytest
import sys
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from layro.converters import (
    deep_merge,
    convert_value_to_type,
    dataclass_to_dict,
    dict_to_dataclass
)
from layro.loaders import load_yaml_config, find_config_file
from layro.manager import ConfigManager


# --- Test Dataclasses ---
@dataclass
class NestedConfig:
    value: int = 42
    name: str = "nested"

@dataclass
class ListConfig:
    items: List[NestedConfig] = None

    def __post_init__(self):
        if self.items is None:
            self.items = [NestedConfig()]

@dataclass
class TestConfig:
    config: Optional[Path] = None
    simple_value: int = 1
    model_type: str = "basic"
    nested: NestedConfig = field(default_factory=NestedConfig)
    list_config: ListConfig = None
    enable_feature: bool = False

    def __post_init__(self):
        if self.list_config is None:
            self.list_config = ListConfig()


# --- Type Conversion Tests ---
def test_convert_value_to_type_basic():
    """Test basic type conversions."""
    assert convert_value_to_type("42", int) == 42
    assert convert_value_to_type("3.14", float) == 3.14
    assert convert_value_to_type("hello", str) == "hello"
    assert convert_value_to_type("true", bool) is True
    assert convert_value_to_type("false", bool) is False
    assert convert_value_to_type("yes", bool) is True
    assert convert_value_to_type("no", bool) is False


def test_convert_value_to_type_optional():
    """Test conversion of Optional types."""
    assert convert_value_to_type(None, Optional[int]) is None
    assert convert_value_to_type("42", Optional[int]) == 42
    assert convert_value_to_type(None, Optional[str]) is None
    assert convert_value_to_type("hello", Optional[str]) == "hello"


def test_convert_value_to_type_list():
    """Test conversion of list types."""
    # List from string representation
    assert convert_value_to_type("[1, 2, 3]", List[int]) == [1, 2, 3]
    assert convert_value_to_type("1,2,3", List[int]) == [1, 2, 3]
    assert convert_value_to_type("1.1,2.2,3.3", List[float]) == [1.1, 2.2, 3.3]
    
    # List from list
    assert convert_value_to_type([1, 2, 3], List[int]) == [1, 2, 3]
    assert convert_value_to_type(["1", "2", "3"], List[int]) == [1, 2, 3]


def test_convert_value_to_type_path():
    """Test conversion to Path type."""
    assert convert_value_to_type("/tmp/test", Path) == Path("/tmp/test")
    assert convert_value_to_type("relative/path", Path) == Path("relative/path")


# --- Dictionary Conversion Tests ---
def test_dataclass_to_dict():
    """Test conversion from dataclass to dictionary."""
    config = TestConfig()
    result = dataclass_to_dict(config)
    
    assert isinstance(result, dict)
    assert result["simple_value"] == 1
    assert result["model_type"] == "basic"
    assert result["nested"]["value"] == 42
    assert result["nested"]["name"] == "nested"
    assert len(result["list_config"]["items"]) == 1
    assert result["list_config"]["items"][0]["value"] == 42

    # Test with custom values
    config = TestConfig(
        simple_value=100,
        model_type="advanced",
        nested=NestedConfig(value=200, name="custom"),
        list_config=ListConfig(items=[
            NestedConfig(value=300, name="item1"),
            NestedConfig(value=400, name="item2")
        ])
    )
    result = dataclass_to_dict(config)
    
    assert result["simple_value"] == 100
    assert result["model_type"] == "advanced"
    assert result["nested"]["value"] == 200
    assert result["nested"]["name"] == "custom"
    assert len(result["list_config"]["items"]) == 2
    assert result["list_config"]["items"][0]["value"] == 300
    assert result["list_config"]["items"][1]["value"] == 400


def test_dict_to_dataclass():
    """Test conversion from dictionary to dataclass."""
    data = {
        "simple_value": 100,
        "model_type": "advanced",
        "nested": {
            "value": 200,
            "name": "custom"
        },
        "list_config": {
            "items": [
                {"value": 300, "name": "item1"},
                {"value": 400, "name": "item2"}
            ]
        }
    }
    
    result = dict_to_dataclass(data, TestConfig)
    
    assert isinstance(result, TestConfig)
    assert result.simple_value == 100
    assert result.model_type == "advanced"
    assert result.nested.value == 200
    assert result.nested.name == "custom"
    assert len(result.list_config.items) == 2
    assert result.list_config.items[0].value == 300
    assert result.list_config.items[1].value == 400


def test_deep_merge():
    """Test deep merging of dictionaries."""
    base = {
        "simple_value": 1,
        "model_type": "basic",
        "nested": {
            "value": 42,
            "name": "nested"
        },
        "extra_field": "base_only"
    }
    
    override = {
        "simple_value": 100,
        "nested": {
            "value": 200
        },
        "new_field": "override_only"
    }
    
    result = deep_merge(override, base)
    
    assert result["simple_value"] == 100  # Override wins
    assert result["model_type"] == "basic"  # From base
    assert result["nested"]["value"] == 200  # Override wins
    assert result["nested"]["name"] == "nested"  # From base
    assert result["extra_field"] == "base_only"  # From base
    assert result["new_field"] == "override_only"  # From override


# --- YAML Loading Tests ---
def test_load_yaml_config(tmp_path):
    """Test loading configuration from YAML file."""
    yaml_content = """
    simple_value: 100
    model_type: advanced
    nested:
      value: 200
      name: custom
    list_config:
      items:
        - value: 300
          name: item1
        - value: 400
          name: item2
    """
    
    yaml_file = tmp_path / "test_config.yaml"
    yaml_file.write_text(yaml_content)
    
    result = load_yaml_config(yaml_file)
    
    assert result["simple_value"] == 100
    assert result["model_type"] == "advanced"
    assert result["nested"]["value"] == 200
    assert result["nested"]["name"] == "custom"
    assert len(result["list_config"]["items"]) == 2
    assert result["list_config"]["items"][0]["value"] == 300
    assert result["list_config"]["items"][1]["value"] == 400


def test_find_config_file(tmp_path):
    """Test finding configuration files in different locations."""
    # Test with existing file
    existing_file = tmp_path / "existing.yaml"
    existing_file.touch()
    
    result = find_config_file(existing_file)
    assert result == existing_file
    
    # Test with non-existing file, not required
    non_existing_file = tmp_path / "non_existing.yaml"
    result = find_config_file(non_existing_file, required=False)
    assert result is None
    
    # Test with non-existing file, required
    with pytest.raises(FileNotFoundError):
        find_config_file(non_existing_file, required=True)
    
    # Test with default locations
    default_file = tmp_path / "default.yaml"
    default_file.touch()
    result = find_config_file(None, default_locations=[default_file])
    assert result == default_file


# --- ConfigManager Tests ---
@pytest.fixture
def config_setup(tmp_path):
    """Set up a test configuration environment with config files."""
    # Create configs directory
    config_dir = tmp_path / "configs"
    config_dir.mkdir(exist_ok=True)
    
    # Create default.yaml
    default_yaml_content = """
    simple_value: 10
    model_type: basic
    nested:
      value: 100
      name: default
    """
    default_yaml_file = config_dir / "default.yaml"
    default_yaml_file.write_text(default_yaml_content)
    
    # Create default_advanced.yaml
    advanced_yaml_content = """
    nested:
      value: 200
      name: advanced
    list_config:
      items:
        - value: 300
          name: advanced_item
    """
    advanced_yaml_file = config_dir / "default_advanced.yaml"
    advanced_yaml_file.write_text(advanced_yaml_content)
    
    # Create user config.yaml
    user_yaml_content = """
    simple_value: 50
    nested:
      name: user
    """
    user_yaml_file = tmp_path / "user_config.yaml"
    user_yaml_file.write_text(user_yaml_content)
    
    return {
        "config_dir": config_dir,
        "default_yaml": default_yaml_file,
        "advanced_yaml": advanced_yaml_file,
        "user_yaml": user_yaml_file
    }


def test_config_manager_defaults(config_setup):
    """Test ConfigManager with default configuration."""
    config_manager = ConfigManager(
        config_class=TestConfig,
        default_config_dir=config_setup["config_dir"]
    )
    
    # Test without CLI args
    config = config_manager.parse_args([])
    
    assert config.simple_value == 10  # From default.yaml
    assert config.model_type == "basic"  # From default.yaml
    assert config.nested.value == 100  # From default.yaml
    assert config.nested.name == "default"  # From default.yaml


def test_config_manager_with_mode(config_setup):
    """Test ConfigManager with mode-specific configuration."""
    config_manager = ConfigManager(
        config_class=TestConfig,
        default_config_dir=config_setup["config_dir"],
        mode_field="model_type"
    )
    
    # Set model_type to advanced, which should load default_advanced.yaml
    config = config_manager.parse_args(["--model-type", "advanced"])
    
    assert config.simple_value == 10  # From default.yaml
    assert config.model_type == "advanced"  # From CLI arg
    assert config.nested.value == 200  # From default_advanced.yaml
    assert config.nested.name == "advanced"  # From default_advanced.yaml
    assert len(config.list_config.items) == 1
    assert config.list_config.items[0].value == 300  # From default_advanced.yaml
    assert config.list_config.items[0].name == "advanced_item"  # From default_advanced.yaml


def test_config_manager_with_user_config(config_setup):
    """Test ConfigManager with user-specified configuration file."""
    config_manager = ConfigManager(
        config_class=TestConfig,
        default_config_dir=config_setup["config_dir"],
        mode_field="model_type"
    )
    
    # Provide user config file
    config = config_manager.parse_args(["--config", str(config_setup["user_yaml"])])
    
    assert config.simple_value == 50  # From user_config.yaml
    assert config.model_type == "basic"  # From default.yaml
    assert config.nested.value == 100  # From default.yaml
    assert config.nested.name == "user"  # From user_config.yaml


def test_config_manager_priority_order(config_setup):
    """Test that ConfigManager correctly applies priority order for configuration values."""
    config_manager = ConfigManager(
        config_class=TestConfig,
        default_config_dir=config_setup["config_dir"],
        mode_field="model_type"
    )
    
    # Set up a scenario to test all layers:
    # 1. CLI args
    # 2. User config
    # 3. Mode-specific default
    # 4. Base default
    # 5. Dataclass defaults
    
    config = config_manager.parse_args([
        "--config", str(config_setup["user_yaml"]),
        "--model-type", "advanced",
        "--nested.value", "500"  # This should override all YAML values
    ])
    
    assert config.simple_value == 50  # From user_config.yaml
    assert config.model_type == "advanced"  # From CLI args
    assert config.nested.value == 500  # From CLI args
    assert config.nested.name == "user"  # From user_config.yaml
    assert len(config.list_config.items) == 1
    assert config.list_config.items[0].value == 300  # From default_advanced.yaml
    assert config.list_config.items[0].name == "advanced_item"  # From default_advanced.yaml


def test_config_manager_cli_formats(config_setup):
    """Test different CLI argument formats."""
    config_manager = ConfigManager(
        config_class=TestConfig,
        default_config_dir=config_setup["config_dir"]
    )
    
    # Test equals sign format
    config1 = config_manager.parse_args(["--simple-value=200"])
    assert config1.simple_value == 200
    
    # Test space format
    config2 = config_manager.parse_args(["--simple-value", "300"])
    assert config2.simple_value == 300
    
    # Test underscore naming
    config3 = config_manager.parse_args(["--simple_value=400"])
    assert config3.simple_value == 400
    
    # Test boolean flag (true)
    config4 = config_manager.parse_args(["--enable-feature"])
    assert config4.enable_feature is True
    
    # Test boolean flag (false, explicitly)
    config5 = config_manager.parse_args(["--no-enable-feature"])
    assert config5.enable_feature is False
    
    # Test nested parameters
    config6 = config_manager.parse_args(["--nested.value=600", "--nested.name=cli_nested"])
    assert config6.nested.value == 600
    assert config6.nested.name == "cli_nested"


def test_config_manager_help_text_with_defaults(config_setup, monkeypatch):
    """Test that default values from YAML are used for help text generation."""
    config_manager = ConfigManager(
        config_class=TestConfig,
        default_config_dir=config_setup["config_dir"],
        mode_field="model_type"
    )
    
    # Capture the default instance passed to tyro.cli
    captured_default_instance = None
    
    def mock_tyro_cli(cls, args=None, default=None, **kwargs):
        nonlocal captured_default_instance
        captured_default_instance = default
        
        # Simulate calling --help by raising SystemExit
        raise SystemExit(0)
    
    # Patch tyro.cli
    monkeypatch.setattr("tyro.cli", mock_tyro_cli)
    
    try:
        # Run parse_args which will call our mocked tyro.cli
        with pytest.raises(SystemExit):
            config_manager.parse_args(["--help"])
    except SystemExit:
        pass
    
    # Verify the default instance was created correctly
    assert captured_default_instance is not None
    assert captured_default_instance.simple_value == 10  # From default.yaml
    assert captured_default_instance.model_type == "basic"  # From default.yaml
    assert captured_default_instance.nested.value == 100  # From default.yaml
    assert captured_default_instance.nested.name == "default"  # From default.yaml


# --- Integration Tests ---
@pytest.fixture
def full_config_setup(tmp_path):
    """Create a complete configuration setup for integration testing."""
    # Create config files structure
    config_dir = tmp_path / "configs"
    config_dir.mkdir(exist_ok=True)
    
    # 1. Create default.yaml
    default_yaml_content = """
    simple_value: 10
    model_type: basic
    nested:
      value: 100
      name: default
    """
    default_yaml_file = config_dir / "default.yaml"
    default_yaml_file.write_text(default_yaml_content)
    
    # 2. Create default_advanced.yaml
    advanced_yaml_content = """
    nested:
      value: 200
      name: advanced
    list_config:
      items:
        - value: 310
          name: advanced_item1
        - value: 320
          name: advanced_item2
    """
    advanced_yaml_file = config_dir / "default_advanced.yaml"
    advanced_yaml_file.write_text(advanced_yaml_content)
    
    # 3. Create default_special.yaml
    special_yaml_content = """
    model_type: special
    simple_value: 30
    nested:
      value: 300
      name: special
    """
    special_yaml_file = config_dir / "default_special.yaml"
    special_yaml_file.write_text(special_yaml_content)
    
    # 4. Create user configs
    user_basic_yaml_content = """
    simple_value: 50
    nested:
      name: user_basic
    """
    user_basic_yaml_file = tmp_path / "user_basic.yaml"
    user_basic_yaml_file.write_text(user_basic_yaml_content)
    
    user_advanced_yaml_content = """
    model_type: advanced
    simple_value: 60
    nested:
      name: user_advanced
    """
    user_advanced_yaml_file = tmp_path / "user_advanced.yaml"
    user_advanced_yaml_file.write_text(user_advanced_yaml_content)
    
    return {
        "config_dir": config_dir,
        "default_yaml": default_yaml_file,
        "advanced_yaml": advanced_yaml_file,
        "special_yaml": special_yaml_file,
        "user_basic_yaml": user_basic_yaml_file,
        "user_advanced_yaml": user_advanced_yaml_file
    }


def test_integration_full_flow(full_config_setup):
    """Integration test for the full configuration flow."""
    config_manager = ConfigManager(
        config_class=TestConfig,
        default_config_dir=full_config_setup["config_dir"],
        mode_field="model_type"
    )
    
    # Test case 1: Basic defaults
    config1 = config_manager.parse_args([])
    assert config1.simple_value == 10
    assert config1.model_type == "basic"
    assert config1.nested.value == 100
    assert config1.nested.name == "default"
    
    # Test case 2: User config (basic model)
    config2 = config_manager.parse_args(["--config", str(full_config_setup["user_basic_yaml"])])
    assert config2.simple_value == 50
    assert config2.model_type == "basic"
    assert config2.nested.value == 100
    assert config2.nested.name == "user_basic"
    
    # Test case 3: User config (specifies advanced model)
    config3 = config_manager.parse_args(["--config", str(full_config_setup["user_advanced_yaml"])])
    assert config3.simple_value == 60
    assert config3.model_type == "advanced"
    assert config3.nested.value == 200  # From default_advanced.yaml
    assert config3.nested.name == "user_advanced"  # From user config
    assert len(config3.list_config.items) == 2  # From default_advanced.yaml
    
    # Test case 4: CLI overrides user config and default
    config4 = config_manager.parse_args([
        "--config", str(full_config_setup["user_advanced_yaml"]),
        "--simple-value", "999",
        "--nested.name", "cli_name"
    ])
    assert config4.simple_value == 999  # From CLI
    assert config4.model_type == "advanced"  # From user config
    assert config4.nested.value == 200  # From default_advanced.yaml
    assert config4.nested.name == "cli_name"  # From CLI
    
    # Test case 5: CLI mode overrides user config mode
    config5 = config_manager.parse_args([
        "--config", str(full_config_setup["user_advanced_yaml"]),
        "--model-type", "special"
    ])
    assert config5.simple_value == 60  # From user config
    assert config5.model_type == "special"  # From CLI
    assert config5.nested.value == 300  # From default_special.yaml
    assert config5.nested.name == "user_advanced"  # From user config


if __name__ == "__main__":
    pytest.main(["-v", __file__])