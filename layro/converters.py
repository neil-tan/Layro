"""
Type conversion and dictionary utilities for the config manager.

This module provides functions for:
- Converting between dataclasses and dictionaries
- Converting values to specified types, handling Optional and other special types
- Deep merging of dictionaries with proper overriding
"""

import ast
from dataclasses import fields
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Tuple, Union, get_args, get_origin, get_type_hints


def deep_merge(override: dict, base: dict) -> dict:
    """Recursively merge override dict into base dict.
    
    The override dictionary takes precedence over the base dictionary.
    
    Args:
        override: Dictionary with values to override
        base: Base dictionary with default values
        
    Returns:
        Merged dictionary
    """
    result = dict(base)
    for k, v in override.items():
        if (
            isinstance(v, dict)
            and k in result
            and isinstance(result[k], dict)
        ):
            result[k] = deep_merge(v, result[k])
        else:
            result[k] = v
    return result


def convert_value_to_type(value: Any, target_type: type) -> Any:
    """Convert a value to the specified target type, handling special cases.
    
    Handles:
    - Basic types (int, float, str, bool)
    - Optional types
    - List types
    - Path
    - Union types
    
    Args:
        value: Value to convert
        target_type: Type to convert to
        
    Returns:
        Converted value
        
    Raises:
        ValueError: If conversion is not possible
    """
    # Handle None values
    if value is None:
        return None
        
    # Handle Optional types
    origin = get_origin(target_type)
    if origin is Union:
        # Get the non-None type from Optional[T]
        args = get_args(target_type)
        if len(args) == 2 and type(None) in args:
            target_type = next(arg for arg in args if arg is not type(None))
        else:
            # For other Union types, try each type until one works
            for arg in args:
                try:
                    return convert_value_to_type(value, arg)
                except (ValueError, TypeError):
                    continue
            raise ValueError(f"Could not convert {value} to any of {args}")
    
    # Handle basic types
    if target_type == bool:
        if isinstance(value, str):
            return value.lower() in ('true', 'yes', '1', 'y')
        return bool(value)
    elif target_type == int:
        return int(float(value)) if isinstance(value, str) else int(value)
    elif target_type == float:
        return float(value)
    elif target_type == str:
        return str(value)
    elif target_type == Path:
        return Path(value)
    elif get_origin(target_type) is list:
        item_type = get_args(target_type)[0]
        if isinstance(value, str):
            # Try to parse string representation of a list (e.g., "[1,2,3]" or "1,2,3")
            try:
                # Handle strings like "[1, 2, 3]"
                parsed_value = ast.literal_eval(value)
                if not isinstance(parsed_value, list):
                    raise ValueError("String did not evaluate to a list.")
                return [convert_value_to_type(item, item_type) for item in parsed_value]
            except (ValueError, SyntaxError):
                # Handle strings like "1,2,3" (comma-separated without brackets)
                try:
                    return [convert_value_to_type(item.strip(), item_type) for item in value.split(',')]
                except Exception as e:
                    raise ValueError(f"Could not parse string '{value}' as list for item type {item_type}. Original error: {e}")
        elif not isinstance(value, list):
            raise ValueError(f"Expected list or string representation of a list, got {type(value)}")
        # If value is already a list
        return [convert_value_to_type(item, item_type) for item in value]
    
    # If no special handling is needed, return the value as is
    return value


def dataclass_to_dict(obj: Any) -> dict:
    """Convert a dataclass instance to a nested dictionary.
    
    Args:
        obj: A dataclass instance or any other object
        
    Returns:
        A nested dictionary representation of the dataclass
    """
    if not hasattr(obj, '__dataclass_fields__'):
        return obj
    
    result = {}
    for field_name, field in obj.__dataclass_fields__.items():
        value = getattr(obj, field_name)
        if hasattr(value, '__dataclass_fields__'):
            # Recursively convert nested dataclass
            result[field_name] = dataclass_to_dict(value)
        elif isinstance(value, (list, tuple)):
            # Handle lists/tuples of dataclasses
            result[field_name] = [dataclass_to_dict(item) if hasattr(item, '__dataclass_fields__') else item 
                                for item in value]
        else:
            result[field_name] = value
    return result


def dict_to_dataclass(data: dict, dataclass_type: Type) -> Any:
    """Convert a dictionary to a dataclass instance with automatic type conversion.
    
    Args:
        data: Dictionary to convert
        dataclass_type: Target dataclass type
        
    Returns:
        Dataclass instance
        
    Raises:
        TypeError: If conversion fails
    """
    if not hasattr(dataclass_type, '__dataclass_fields__'):
        # If the target type is not a dataclass itself, return the data as is
        return data 
        
    type_hints = get_type_hints(dataclass_type)
    field_values = {}
    
    # Iterate through fields defined in the target dataclass
    for field_name, field in dataclass_type.__dataclass_fields__.items():
        if field_name in data:
            value = data[field_name]
            field_type = type_hints[field_name]
            
            # Check if the field type is Optional[T]
            origin = get_origin(field_type)
            if origin is Union:
                args = get_args(field_type)
                if len(args) == 2 and type(None) in args:
                    # Get the non-None type from Optional[T]
                    actual_field_type = next(arg for arg in args if arg is not type(None))
                    
                    # If the actual type is a dataclass, recursively convert
                    if value is not None and hasattr(actual_field_type, '__dataclass_fields__'):
                        field_values[field_name] = dict_to_dataclass(value, actual_field_type)
                    else:
                        field_values[field_name] = convert_value_to_type(value, field_type)
                else:
                    # Handle other Union types
                    field_values[field_name] = convert_value_to_type(value, field_type)
            # If the field type is a dataclass, recursively convert
            elif hasattr(field_type, '__dataclass_fields__'):
                if value is not None:
                    field_values[field_name] = dict_to_dataclass(value, field_type)
                else:
                    field_values[field_name] = None
            else:
                # Otherwise, convert using the basic type converter
                field_values[field_name] = convert_value_to_type(value, field_type)
        # If field_name is not in data, the dataclass __init__ will use its default/default_factory
                
    # Instantiate the dataclass with the processed values
    try:
        return dataclass_type(**field_values)
    except TypeError as e:
        # Provide more context on TypeError during instantiation
        raise TypeError(f"Error instantiating {dataclass_type.__name__} with fields: {field_values}. Original error: {e}") 