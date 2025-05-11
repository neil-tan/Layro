"""
Simple test for multiple configuration files.
"""

import pytest
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from layro.manager import ConfigManager


@dataclass
class SimpleConfig:
    """Simple configuration class."""
    config: Optional[Path] = None
    value: int = 1


def test_simple():
    """Simple test to verify test discovery."""
    assert 1 == 1


if __name__ == "__main__":
    pytest.main(["-v", __file__])
