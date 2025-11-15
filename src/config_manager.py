"""
Configuration Manager

Unified configuration management for the multi-agent scheduler.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """
    Unified configuration manager

    Features:
    - Multiple configuration sources (files, env vars, defaults)
    - Priority-based configuration
    - Type conversion
    - Validation

    Example:
        >>> config = ConfigManager()
        >>> api_key = config.get('anthropic.api_key')
        >>> max_tasks = config.get('scheduler.max_tasks', default=20)
    """

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager

        Args:
            config_file: Path to configuration file (YAML)
        """
        self.config_file = config_file or self._find_config_file()
        self.config_data: Dict[str, Any] = {}
        self.defaults: Dict[str, Any] = self._load_defaults()

        # Load configuration
        self._load_config()

    def _find_config_file(self) -> Optional[str]:
        """
        Find configuration file in standard locations

        Returns:
            Path to config file or None
        """
        search_paths = [
            'config.yaml',
            'config.yml',
            '.config/mas.yaml',
            Path.home() / '.mas' / 'config.yaml',
            '/etc/mas/config.yaml'
        ]

        for path in search_paths:
            if Path(path).exists():
                return str(path)

        return None

    def _load_defaults(self) -> Dict[str, Any]:
        """
        Load default configuration

        Returns:
            Default configuration dictionary
        """
        return {
            # Scheduler settings
            'scheduler': {
                'max_concurrent': 10,
                'max_tasks': 50,
                'default_timeout': 600,
            },

            # Agent settings
            'agents': {
                'claude': {
                    'model': 'claude-sonnet-4-5-20250929',
                    'max_tokens': 1024,
                    'max_concurrent': 20,
                },
                'openai': {
                    'model': 'gpt-4-turbo',
                    'max_tokens': 1024,
                    'max_concurrent': 20,
                },
                'gemini': {
                    'max_concurrent': 10,
                    'timeout': 600,
                },
            },

            # Meta-agent settings
            'meta_agent': {
                'min_tasks': 5,
                'max_tasks': 20,
                'model': 'claude-sonnet-4-5-20250929',
            },

            # Cache settings
            'cache': {
                'enabled': True,
                'max_size': 1000,
                'ttl': 3600,  # 1 hour
            },

            # Security settings
            'security': {
                'max_prompt_length': 50000,
                'validate_inputs': True,
            },

            # Workspace settings
            'workspace': {
                'base_dir': 'workspaces',
                'use_timestamps': True,
            },

            # Logging settings
            'logging': {
                'enabled': True,
                'log_dir': 'logs',
                'log_level': 'INFO',
            },
        }

    def _load_config(self) -> None:
        """Load configuration from file"""
        if self.config_file and Path(self.config_file).exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config_data = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"⚠️  Warning: Failed to load config file: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value

        Priority (highest to lowest):
        1. Environment variable
        2. Config file
        3. Provided default
        4. Built-in defaults

        Args:
            key: Configuration key (dot-separated path, e.g., 'scheduler.max_tasks')
            default: Default value if not found

        Returns:
            Configuration value

        Example:
            >>> config.get('scheduler.max_tasks')
            50
            >>> config.get('scheduler.max_tasks', default=100)
            50
        """
        # 1. Check environment variable
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._convert_type(env_value)

        # 2. Check config file
        value = self._get_nested(self.config_data, key)
        if value is not None:
            return value

        # 3. Check provided default
        if default is not None:
            return default

        # 4. Check built-in defaults
        default_value = self._get_nested(self.defaults, key)
        return default_value

    def _get_nested(self, data: Dict[str, Any], key: str) -> Any:
        """
        Get value from nested dictionary using dot-separated key

        Args:
            data: Dictionary to search
            key: Dot-separated key

        Returns:
            Value or None if not found
        """
        keys = key.split('.')
        value = data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None

        return value

    def _convert_type(self, value: str) -> Any:
        """
        Convert string value to appropriate type

        Args:
            value: String value

        Returns:
            Converted value
        """
        # Try boolean
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False

        # Try integer
        try:
            return int(value)
        except ValueError:
            pass

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value (in-memory only)

        Args:
            key: Configuration key
            value: Value to set
        """
        keys = key.split('.')
        data = self.config_data

        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]

        data[keys[-1]] = value

    def save(self, file_path: Optional[str] = None) -> None:
        """
        Save configuration to file

        Args:
            file_path: Path to save (uses original config_file if None)
        """
        save_path = file_path or self.config_file

        if not save_path:
            print("⚠️  Warning: No config file specified, cannot save")
            return

        try:
            # Create parent directory if needed
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)

            with open(save_path, 'w') as f:
                yaml.dump(self.config_data, f, default_flow_style=False)

            print(f"✓ Configuration saved to {save_path}")

        except Exception as e:
            print(f"❌ Failed to save configuration: {e}")

    def reload(self) -> None:
        """Reload configuration from file"""
        self._load_config()

    def print_config(self) -> None:
        """Print current configuration"""
        print("\n=== Current Configuration ===")
        print(yaml.dump(self.get_all_config(), default_flow_style=False))

    def get_all_config(self) -> Dict[str, Any]:
        """
        Get complete merged configuration

        Returns:
            Complete configuration dictionary
        """
        import copy
        merged = copy.deepcopy(self.defaults)

        # Merge with config file data
        self._deep_merge(merged, self.config_data)

        return merged

    def _deep_merge(self, base: Dict, update: Dict) -> None:
        """
        Deep merge dictionaries

        Args:
            base: Base dictionary (modified in-place)
            update: Update dictionary
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value


# Global config manager instance
_global_config: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get global ConfigManager instance"""
    global _global_config
    if _global_config is None:
        _global_config = ConfigManager()
    return _global_config


# Example usage
if __name__ == "__main__":
    config = ConfigManager()

    # Test get
    max_tasks = config.get('scheduler.max_tasks')
    print(f"Max tasks: {max_tasks}")

    # Test set
    config.set('scheduler.max_tasks', 100)

    # Test environment variable override
    os.environ['SCHEDULER_MAX_TASKS'] = '200'
    max_tasks = config.get('scheduler.max_tasks')
    print(f"Max tasks (with env override): {max_tasks}")

    # Print full config
    config.print_config()
