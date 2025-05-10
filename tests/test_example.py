"""
Simple test script for the ConfigManager.

Run with:
    python -m pytest tests/test_example.py
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Updated import to use the layro package
from layro.manager import ConfigManager


@dataclass
class SimpleConfig:
    """Simple configuration for testing."""
    config: Optional[Path] = None
    value: int = 42
    flag: bool = False


def test_simple_config():
    """Test the ConfigManager with a simple config."""
    config_manager = ConfigManager(
        config_class=SimpleConfig,
        enable_debug=True
    )
    
    # Parse args with specific test values
    config = config_manager.parse_args(['--value=123', '--flag'])
    
    # Print the result
    print("\nTest Result:")
    print(f"  value: {config.value} (expected: 123)")
    print(f"  flag: {config.flag} (expected: True)")
    
    assert config.value == 123, f"Expected value=123, got {config.value}"
    assert config.flag is True, f"Expected flag=True, got {config.flag}"
    print("All assertions passed!")


if __name__ == "__main__":
    # Can still be run as a script
    test_simple_config()