"""
Example usage of the ConfigManager.

This script demonstrates how to use the ConfigManager with a simple configuration dataclass.
Run it with:

    python -m utils.config_manager.example --help
    python -m utils.config_manager.example --learning-rate=0.01
    python -m utils.config_manager.example --model-type=advanced --model.num-layers=4
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List

from utils.config_manager import ConfigManager


@dataclass
class ModelConfig:
    """Configuration for the model architecture."""
    num_layers: int = 2
    hidden_size: int = 64
    dropout: float = 0.1


@dataclass
class DataConfig:
    """Configuration for data loading."""
    batch_size: int = 32
    num_workers: int = 4


@dataclass
class TrainingConfig:
    """Example training configuration."""
    # Special argument for the config file
    config: Optional[Path] = None
    
    # Training parameters
    learning_rate: float = 0.001
    epochs: int = 10
    model_type: str = "basic"  # Used for mode-specific defaults
    
    # Nested configurations
    model: ModelConfig = field(default_factory=ModelConfig)
    data: DataConfig = field(default_factory=DataConfig)


def main():
    """Run the example."""
    # Create a config manager
    config_manager = ConfigManager(
        config_class=TrainingConfig,
        default_config_dir=Path(__file__).parent / "example_configs",
        mode_field="model_type",
        enable_debug=True
    )
    
    # Parse arguments
    config = config_manager.parse_args()
    
    # Print the final configuration
    print("\nFinal Configuration:")
    print(f"  learning_rate: {config.learning_rate}")
    print(f"  epochs: {config.epochs}")
    print(f"  model_type: {config.model_type}")
    print(f"  model:")
    print(f"    num_layers: {config.model.num_layers}")
    print(f"    hidden_size: {config.model.hidden_size}")
    print(f"    dropout: {config.model.dropout}")
    print(f"  data:")
    print(f"    batch_size: {config.data.batch_size}")
    print(f"    num_workers: {config.data.num_workers}")


if __name__ == "__main__":
    # Create example config files if they don't exist
    example_config_dir = Path(__file__).parent / "example_configs"
    example_config_dir.mkdir(exist_ok=True)
    
    # Create default.yaml
    default_yaml = """
learning_rate: 0.005
epochs: 20
model:
  hidden_size: 128
"""
    default_yaml_path = example_config_dir / "default.yaml"
    if not default_yaml_path.exists():
        default_yaml_path.write_text(default_yaml)
        
    # Create default_advanced.yaml
    advanced_yaml = """
model:
  num_layers: 3
  hidden_size: 256
data:
  batch_size: 64
"""
    advanced_yaml_path = example_config_dir / "default_advanced.yaml"
    if not advanced_yaml_path.exists():
        advanced_yaml_path.write_text(advanced_yaml)
    
    # Run the example
    main() 