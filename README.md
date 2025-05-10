# Layro

A robust, reusable configuration management package for Python applications, providing a unified interface for layered configuration from multiple sources.

[![PyPI version](https://img.shields.io/pypi/v/layro.svg)](https://pypi.org/project/layro/)
[![Python Versions](https://img.shields.io/pypi/pyversions/layro.svg)](https://pypi.org/project/layro/)
[![License](https://img.shields.io/pypi/l/layro.svg)](https://github.com/yourusername/layro/blob/main/LICENSE)

## Features

- **Layered Configuration**: Combine settings from CLI arguments, user config files, mode-specific defaults, base defaults, and dataclass defaults with clear priority order
- **Type-Safe**: Built on Python dataclasses with automatic type validation and conversion
- **Developer-Friendly**: Clean API, intelligent CLI help text, and comprehensive error messages
- **Flexible**: Works with nested configurations and supports various data types

## Installation

```bash
pip install layro
```

## Quick Usage Example

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from layro import ConfigManager

@dataclass
class ModelConfig:
    num_layers: int = 2
    hidden_size: int = 64

@dataclass
class TrainingConfig:
    config: Optional[Path] = None  # For user config file
    learning_rate: float = 0.001
    model_type: str = "basic"      # Used as a mode selector
    model: ModelConfig = field(default_factory=ModelConfig)

# Create config manager and parse arguments
config_manager = ConfigManager(
    config_class=TrainingConfig,
    default_config_dir="./configs",
    mode_field="model_type",
    config_field="config"
)
config = config_manager.parse_args()
```

## Documentation

For detailed documentation and advanced usage examples, see [the full documentation](layro/README.md).

## License

MIT License - see the [LICENSE](LICENSE) file for details.