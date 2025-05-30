# Layro

A robust, reusable configuration management package for Python applications, providing a unified interface for layered configuration from multiple sources. It's designed to be easily integrated into various projects as a standalone package.

## Features

- **Layered Configuration with Priority Order**:
  1. Command-Line Arguments (CLI) - Highest priority, parsed by `tyro`.
  2. User Config Files (specified by one or more `--config` arguments) - Second priority, with later files overriding earlier ones.
  3. Mode-specific Default Config (e.g., `default_flow.yaml` if `model_type="flow"`) - Third priority.
  4. Base Default Config (e.g., `default.yaml`) - Fourth priority.
  5. Dataclass Defaults - Lowest priority.

- **Sophisticated CLI Argument Handling**:
  - Uses `argparse` for an initial scan of directive arguments (like `--config` and mode-setting arguments).
  - Leverages `tyro` for comprehensive parsing of all other arguments, supporting standard CLI conventions (e.g., `--arg=value`, `--arg value`, boolean flags, nested parameters like `--model.learning-rate`).

- **Support for Mode-specific Defaults**:
  - Loads mode-specific configuration files based on a specified field (e.g., `mode_field="model_type"`).

- **Accurate and Contextual Help Text**:
  - A key advantage: `--help` output (generated by `tyro`) accurately shows default values reflecting all loaded YAML configurations (default, mode-specific, and user-specified).

- **Type Safety**:
  - Automatic type conversion with validation for CLI arguments via `tyro`.
  - Internal type conversion for YAML-loaded values.
  - Support for nested dataclasses, `Optional` types, and other complex Python types.
  - Clear error messages for invalid configuration.

## Installation

```bash
# Install from PyPI
pip install layro
```

For development:
```bash
# Clone the repository
git clone https://github.com/yourusername/layro.git
cd layro

# Install in editable mode
pip install -e .
```

## Basic Usage

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Import from layro package
from layro import ConfigManager 

@dataclass
class ModelConfig:
    num_layers: int = 2
    hidden_size: int = 64

@dataclass
class TrainingConfig:
    # Special field for the user config file path
    # When multiple config files are provided, this will store the path to the last one
    config: Optional[Path] = None 
    learning_rate: float = 0.001
    model_type: str = "basic" # Example mode_field
    model: ModelConfig = field(default_factory=ModelConfig)

# --- In your main script ---
# Define the directory where your default YAML config files are located
# This path is typically relative to your script or project root.
CONFIG_DIR = Path(__file__).parent / "configs" # Example

# Create a config manager instance
config_manager = ConfigManager(
    config_class=TrainingConfig,
    default_config_dir=CONFIG_DIR, # Directory for default.yaml, default_<mode>.yaml
    mode_field="model_type",       # Field in TrainingConfig that determines the mode
    config_field="config"          # Field in TrainingConfig for the user YAML path
)

# Parse arguments from CLI, YAMLs, and defaults
try:
    config = config_manager.parse_args()
    # Now use the 'config' object
    print(f"Learning Rate: {config.learning_rate}")
    print(f"Model Type: {config.model_type}")
    print(f"Model Layers: {config.model.num_layers}")
except SystemExit:
    # Handle cases like --help where the script should exit
    pass
```

## Configuration Files

Place your default configuration files in the directory specified by `default_config_dir`.

**Example `configs/default.yaml`**:
```yaml
learning_rate: 0.005
model:
  hidden_size: 128
```

**Example `configs/default_advanced.yaml`** (mode-specific for `model_type="advanced"`):
```yaml
model:
  num_layers: 4
  hidden_size: 256
```

**Example `my_custom_config.yaml` (User-supplied)**:
```yaml
learning_rate: 0.0007
# model_type: "advanced" # Can also be set here
```

## Multiple Configuration Files

Layro supports specifying multiple configuration files that are merged together, with later files taking precedence over earlier ones:

```python
# In Python, the config manager handles multiple files automatically
config = config_manager.parse_args()  # Will process all --config arguments
```

**Example usage with multiple configuration files:**

```bash
# Base configuration + project-specific overrides + user-specific overrides
python your_script.py --config=base.yaml --config=project.yaml --config=user.yaml
```

When multiple configuration files are specified, they are processed in order:
1. Files are loaded and validated in the order specified
2. Settings from later files override those from earlier files
3. Nested structures are deeply merged (not completely replaced)
4. The `config` field in your dataclass will store the path to the last specified config file

This allows for a flexible configuration approach:
- Base configs with common settings
- Project-specific configs that override some base settings
- User-specific configs with personal preferences
- All still overridable via command-line arguments

## Command-line Usage

```bash
# Display help with accurate default values from all relevant YAMLs
python your_script.py --help

# Override configuration values from command line
python your_script.py --learning-rate=0.01 --model-type=advanced --model.num-layers=5

# Use a specific config file (which itself can be overridden by CLI args)
python your_script.py --config=my_custom_config.yaml --model.hidden-size=512

# Use multiple config files, with later files overriding earlier ones
python your_script.py --config=base_config.yaml --config=override_config.yaml

# Multiple config files with CLI overrides
python your_script.py --config=base_config.yaml --config=project_config.yaml --config=user_overrides.yaml --learning-rate=0.003
```

## Dependencies

- **PyYAML**: For loading YAML configuration files.
- **tyro**: For robust CLI argument parsing and help generation.
  *(Note: `argparse` is used internally for pre-scanning but is part of the Python standard library.)*

## Example

See the `examples/example_usage.py` file (once moved to the new structure) for a complete runnable example demonstrating various features.
The `tests/fixtures/example_configs/` directory contains sample configuration files used for testing.