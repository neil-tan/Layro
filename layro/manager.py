"""
Configuration Manager for handling layered configuration.

This module provides the main ConfigManager class that handles:
1. Command-line argument parsing
2. Configuration loading from YAML files
3. Type conversion and validation
4. Configuration merging with correct prioritization
"""

import sys
import tyro
from dataclasses import fields
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Type, TypeVar, get_type_hints
import argparse

from .converters import convert_value_to_type, dataclass_to_dict, dict_to_dataclass, deep_merge
from .loaders import load_yaml_config, find_config_file

T = TypeVar('T')  # Represents the config dataclass type

class ConfigManager:
    """Manager for layered configuration from CLI args, config files, and defaults.
    
    Provides a unified interface for loading and processing configuration from multiple sources:
    1. Command-Line Arguments (CLI) - highest priority
    2. User Config File (specified by --config) - second priority
    3. Mode-specific Default Config - third priority
    4. Base Default Config - fourth priority
    5. Dataclass Defaults - lowest priority
    
    Features:
    - Handles both dash and underscore naming conventions in CLI args
    - Supports --arg=value and --arg value formats
    - Provides accurate help text with defaults from config files
    - Automatically handles type conversion
    - Deep merges nested configurations with correct priority
    """
    
    def __init__(self, 
                 config_class: Type[T],
                 default_config_dir: Optional[Path] = None,
                 mode_field: Optional[str] = None,
                 config_field: str = "config",
                 enable_debug: bool = False):
        """Initialize the config manager.
        
        Args:
            config_class: The dataclass type to parse configuration into
            default_config_dir: Directory containing default config files (default.yaml, etc.)
            mode_field: Field name that determines the mode-specific default config
                        For example, if mode_field="model_type", and config has model_type="flow",
                        this would load default_flow.yaml as the mode-specific default config
            config_field: Field name for the user config file path (defaults to "config")
            enable_debug: Whether to print debug information during parsing
        """
        self.config_class = config_class
        self.default_config_dir = default_config_dir or Path.cwd() / "configs"
        self.mode_field = mode_field
        self.config_field = config_field
        self.debug = enable_debug
        
    def _debug(self, *args, **kwargs):
        """Print debug information if debug mode is enabled."""
        if self.debug:
            print("DEBUG:", *args, **kwargs)
            
    def parse_args(self, argv: Optional[List[str]] = None) -> T:
        """Parse configuration from CLI args and config files.
        
        This is the main entry point for users of ConfigManager.
        It uses a multi-stage process:
        1. Pre-parse directive CLI arguments (e.g., --config, mode field) using argparse.
        2. Load and merge all YAML configurations (Default, Mode-specific, User)
           to create a comprehensive default instance for tyro.
        3. Call tyro.cli() with remaining CLI arguments and the comprehensive default.
           This allows tyro's --help to reflect values from all loaded YAMLs.
        
        Args:
            argv: Command line arguments (defaults to sys.argv[1:])
            
        Returns:
            Configured instance of the config class
        """
        raw_argv = sys.argv[1:] if argv is None else argv
        self._debug(f"Raw argv: {raw_argv}")

        # 1. Pre-parse directive arguments using argparse to get config_path and initial mode
        pre_parser = argparse.ArgumentParser(add_help=False) # Disable help for this pre-parser
        
        # Add config_field argument (e.g., --config)
        # argparse stores dest with underscores, so normalize self.config_field
        config_field_dest = self.config_field.replace('-', '_')
        pre_parser.add_argument(f"--{self.config_field}", dest=config_field_dest, type=str, default=None)

        # Add mode_field argument (e.g., --model-type) if it exists
        cli_mode_value = None
        if self.mode_field:
            mode_field_dest = self.mode_field.replace('-', '_')
            # Add both dash and underscore variants if they are different, argparse handles one as alias if dest is same
            pre_parser.add_argument(f"--{self.mode_field.replace('_', '-')}", dest=mode_field_dest, type=str, default=None)
            if '_' in self.mode_field and '-' in self.mode_field: # e.g. mode_field itself has a dash
                 pass # already added
            elif '_' in self.mode_field: # e.g. model_type -> also allow model-type if specified in mode_field with underscore
                 pass # Covered by above if mode_field_dest matches
            # Ensure the original self.mode_field is also parsable if it's different from the dashed version
            if self.mode_field != self.mode_field.replace('_', '-'):
                 pre_parser.add_argument(f"--{self.mode_field}", dest=mode_field_dest, type=str, default=None)


        directive_ns, remaining_argv_for_tyro = pre_parser.parse_known_args(raw_argv)
        
        user_config_path_str = getattr(directive_ns, config_field_dest, None)
        user_config_path = Path(user_config_path_str) if user_config_path_str else None
        self._debug(f"Pre-parsed user_config_path: {user_config_path}")

        if self.mode_field:
            cli_mode_value = getattr(directive_ns, self.mode_field.replace('-', '_'), None)
        self._debug(f"Pre-parsed cli_mode_value: {cli_mode_value}")

        # 2. Build the default configuration dictionary for tyro.cli()
        #    This determines what tyro --help shows.
        #    Order of precedence for this 'default_instance_for_tyro':
        #    1. Dataclass Defaults
        #    2. Default YAML
        #    3. Mode Default YAML (selected based on overall mode)
        #    4. User YAML (from --config)

        #    a. Start with pure dataclass defaults
        dataclass_defaults_instance = self.config_class()
        final_default_dict_for_tyro = dataclass_to_dict(dataclass_defaults_instance)
        self._debug(f"Tyro default base (dataclass): {final_default_dict_for_tyro}")

        #    b. Merge Default YAML
        default_yaml_content = self._load_default_yaml()
        if default_yaml_content:
            final_default_dict_for_tyro = deep_merge(default_yaml_content, final_default_dict_for_tyro)
            self._debug(f"Tyro default after default.yaml: {final_default_dict_for_tyro}")

        #    c. Load user_yaml_content to help determine authoritative_mode
        user_yaml_content = self._load_user_yaml(user_config_path) if user_config_path else {}

        #    d. Determine the authoritative_mode that governs which mode_default.yaml is loaded
        #       Priority: Pre-parsed CLI > User YAML > Default YAML > Dataclass
        authoritative_mode = cli_mode_value
        if not authoritative_mode and self.mode_field:
            if user_yaml_content and self.mode_field in user_yaml_content:
                authoritative_mode = user_yaml_content[self.mode_field]
            elif default_yaml_content and self.mode_field in default_yaml_content:
                authoritative_mode = default_yaml_content[self.mode_field]
            else: # Fallback to dataclass default for mode
                authoritative_mode = getattr(dataclass_defaults_instance, self.mode_field, None)
        
        self._debug(f"Authoritative mode for selecting mode_default.yaml: {authoritative_mode}")

        #    e. Merge Mode Default YAML
        if self.mode_field and authoritative_mode:
            mode_default_yaml_content = self._load_mode_default_yaml(authoritative_mode)
            if mode_default_yaml_content:
                final_default_dict_for_tyro = deep_merge(mode_default_yaml_content, final_default_dict_for_tyro)
                self._debug(f"Tyro default after mode_default.yaml: {final_default_dict_for_tyro}")

        #    f. Merge User YAML (user_yaml_content already loaded)
        if user_yaml_content:
            final_default_dict_for_tyro = deep_merge(user_yaml_content, final_default_dict_for_tyro)
            self._debug(f"Tyro default after user.yaml: {final_default_dict_for_tyro}")
        
        # 3. Convert the final merged dictionary to a dataclass instance for tyro's default
        default_instance_for_tyro = dict_to_dataclass(final_default_dict_for_tyro, self.config_class)

        #    Ensure the pre-parsed user_config_path is correctly set on this instance,
        #    as it's a special field often not part of the YAMLs themselves.
        if hasattr(default_instance_for_tyro, self.config_field) and user_config_path:
             setattr(default_instance_for_tyro, self.config_field, user_config_path)
        
        # 4. Parse remaining CLI arguments with tyro, using the merged YAMLs as default
        #    tyro will override values in default_instance_for_tyro with args from remaining_argv_for_tyro.
        #    If --help is in remaining_argv_for_tyro, tyro handles it using default_instance_for_tyro.
        try:
            final_config_obj = tyro.cli(
                self.config_class,
                args=remaining_argv_for_tyro, 
                default=default_instance_for_tyro
            )
        except SystemExit as e:
            sys.exit(e.code) # Propagate exit for --help, etc.
            
        # 5. Final check: Ensure the actual user_config_path used for loading is on the final object.
        #    This is mostly for consistency, as tyro might have set it to None if 'config_field'
        #    wasn't in remaining_argv_for_tyro and its default was None.
        if hasattr(final_config_obj, self.config_field) and user_config_path:
            setattr(final_config_obj, self.config_field, user_config_path)
            
        return final_config_obj
    
    def _load_default_yaml(self) -> Dict[str, Any]:
        """Load the default YAML configuration file."""
        if not self.default_config_dir:
            return {}
            
        default_yaml_path = self.default_config_dir / "default.yaml"
        if not default_yaml_path.exists():
            return {}
            
        return load_yaml_config(default_yaml_path)
    
    def _load_mode_default_yaml(self, mode_value: str) -> Dict[str, Any]:
        """Load the mode-specific default YAML configuration file."""
        if not self.default_config_dir or not mode_value:
            return {}
            
        mode_default_yaml_path = self.default_config_dir / f"default_{mode_value}.yaml"
        if not mode_default_yaml_path.exists():
            return {}
            
        return load_yaml_config(mode_default_yaml_path)
    
    def _load_user_yaml(self, user_config_path: Optional[Path]) -> Dict[str, Any]:
        """Load the user-specified YAML configuration file."""
        if not user_config_path or not user_config_path.exists():
            return {}
            
        return load_yaml_config(user_config_path) 