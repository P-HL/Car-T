#!/usr/bin/env python3
"""
Configuration Manager Module
配置管理模块

This module handles loading and merging configuration from multiple sources
with proper priority handling for the Blood Disease Clinical Prediction Project.
本模块处理来自多个源的配置加载和合并，为血液疾病临床预测项目提供适当的优先级处理。
"""

import os
import yaml
from typing import Dict, Any, Optional, Union, List
import logging


# Configure logging for this module
logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Configuration manager that handles loading and merging configuration from
    multiple sources with proper priority handling.
    配置管理器，处理来自多个源的配置加载和合并，提供适当的优先级处理。
    
    Priority order (highest to lowest):
    1. Command line arguments
    2. Environment variables  
    3. YAML configuration file
    4. Default values
    """
    
    def __init__(self, config_file: str = 'config.yaml') -> None:
        """
        Initialize configuration manager.
        初始化配置管理器。
        
        Args:
            config_file: Path to the YAML configuration file
        """
        self.config: Dict[str, Any] = self._get_default_config()
        self.config_file = config_file
        
        # Try to load config.yaml by default
        self.load_from_yaml(config_file)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration values.
        获取默认配置值。
        
        Returns:
            Default configuration dictionary
        """
        return {
            'paths': {
                'input_file': '/home/phl/PHL/Car-T/data_encoder/output/dataset/encoded_standardized.csv',
                'output_dir': '/home/phl/PHL/Car-T/dataset_clip/output',
                'backup_input_file': '/home/phl/PHL/Car-T/dataset_clip/encoded_standardized.csv'
            },
            'analysis': {
                'age_threshold': 65
            },
            'visualization': {
                'variables': [
                    'Age', 'Sex', 'Disease', 'BM disease burden', 'Bone marrow cellularity',
                    'extramedullary mass', 'extranodal involvement', 'B symptoms', 'Ann Arbor stage',
                    'Number of prior therapy lines', 'Prior hematopoietic stem cell', 'Prior CAR-T therapy',
                    'Bridging therapy', 'Costimulatory molecule', 'Type of construct(tandem/single target)',
                    'CAR-T therapy following auto-HSCT', 'CRS grade', 'ICANS grade', 'Early ICAHT grade',
                    'Late ICAHT grade', 'Infection grade'
                ],
                'figure_width': 25,
                'figure_height': 5,
                'spacing': 3.0,
                'max_categories': 10,
                'dpi': 300,
                'output_formats': ['png', 'pdf'],
                'colors': ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E',
                          '#577590', '#F8961E', '#F9844A', '#90A959', '#6494AA'],
                'alpha': 0.8,
                'grid_alpha': 0.3,
                'bar_width': 0.7,
                'category_spacing': 0.8,
                'variable_spacing': 1.5
            },
            'display': {
                'fonts': ['SimHei', 'DejaVu Sans', 'Arial Unicode MS'],
                'font_sizes': {
                    'small': 9,
                    'normal': 10,
                    'medium': 12,
                    'large': 16,
                    'title': 18
                }
            },
            'output': {
                'report_filename': 'categorical_analysis_report.txt',
                'visualization_filename': 'categorical_variables_visualization.png',
                'data_filename': 'categorical_variables_data.csv',
                'encoding': 'utf-8'
            }
        }
    
    def load_from_yaml(self, config_path: str) -> None:
        """
        Load configuration from YAML file.
        从YAML文件加载配置。
        
        Args:
            config_path: Path to the YAML configuration file
            
        Raises:
            FileNotFoundError: If config file is not found (warning only)
            yaml.YAMLError: If YAML format is invalid
        """
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    yaml_config = yaml.safe_load(f)
                    if yaml_config:
                        self._merge_config(yaml_config)
                        logger.info(f"Loaded configuration from: {config_path}")
                        print(f"Loaded configuration from: {config_path}")
            else:
                logger.warning(f"Config file not found: {config_path}")
                print(f"Warning: Config file not found: {config_path}")
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML config: {e}")
            print(f"Error parsing YAML config: {e}")
            print("Using default configuration...")
        except Exception as e:
            logger.error(f"Error loading YAML config: {e}")
            print(f"Error loading YAML config: {e}")
            print("Using default configuration...")
    
    def load_from_env(self) -> None:
        """
        Load configuration from environment variables.
        从环境变量加载配置。
        
        Environment variables mapping:
        - CLIP_INPUT_FILE -> paths.input_file
        - CLIP_OUTPUT_DIR -> paths.output_dir  
        - CLIP_AGE_THRESHOLD -> analysis.age_threshold
        - CLIP_FIGURE_WIDTH -> visualization.figure_width
        - CLIP_FIGURE_HEIGHT -> visualization.figure_height
        - CLIP_DPI -> visualization.dpi
        """
        env_mappings = {
            'CLIP_INPUT_FILE': ('paths', 'input_file'),
            'CLIP_OUTPUT_DIR': ('paths', 'output_dir'),
            'CLIP_AGE_THRESHOLD': ('analysis', 'age_threshold'),
            'CLIP_FIGURE_WIDTH': ('visualization', 'figure_width'),
            'CLIP_FIGURE_HEIGHT': ('visualization', 'figure_height'),
            'CLIP_DPI': ('visualization', 'dpi')
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Type conversion based on the key
                if key in ['age_threshold', 'figure_width', 'figure_height', 'dpi']:
                    try:
                        value = int(value) if key in ['age_threshold', 'dpi'] else float(value)
                    except ValueError:
                        print(f"Warning: Invalid value for {env_var}: {value}")
                        continue
                
                if section not in self.config:
                    self.config[section] = {}
                self.config[section][key] = value
                logger.info(f"Loaded from environment: {env_var} = {value}")
                print(f"Loaded from environment: {env_var} = {value}")
    
    def load_from_args(self, args: Any) -> None:
        """Load configuration from command line arguments."""
    def load_from_args(self, args: Any) -> None:
        """
        Load configuration from command line arguments.
        从命令行参数加载配置。
        
        Args:
            args: Argument parser namespace object
        """
        if hasattr(args, 'input_file') and args.input_file:
            self.config['paths']['input_file'] = args.input_file
        if hasattr(args, 'output_dir') and args.output_dir:
            self.config['paths']['output_dir'] = args.output_dir
        if hasattr(args, 'age_threshold') and args.age_threshold is not None:
            self.config['analysis']['age_threshold'] = args.age_threshold
        if hasattr(args, 'figure_width') and args.figure_width is not None:
            self.config['visualization']['figure_width'] = args.figure_width
        if hasattr(args, 'figure_height') and args.figure_height is not None:
            self.config['visualization']['figure_height'] = args.figure_height
        if hasattr(args, 'dpi') and args.dpi is not None:
            self.config['visualization']['dpi'] = args.dpi
    
    def _merge_config(self, new_config: Dict[str, Any]) -> None:
        """
        Recursively merge new configuration into existing config.
        递归地将新配置合并到现有配置中。
        
        Args:
            new_config: New configuration dictionary to merge
        """
        for key, value in new_config.items():
            if key in self.config and isinstance(self.config[key], dict) and isinstance(value, dict):
                self.config[key].update(value)
            else:
                self.config[key] = value
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get configuration value with optional default.
        获取配置值，支持可选的默认值。
        
        Args:
            section: Configuration section name
            key: Configuration key name
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self.config.get(section, {}).get(key, default)
    
    def get_path(self, key: str) -> str:
        """
        Get file path, ensuring proper path resolution.
        获取文件路径，确保适当的路径解析。
        
        Args:
            key: Path key name
            
        Returns:
            Resolved file path
        """
        path = self.get('paths', key)
        if path:
            return os.path.expanduser(os.path.expandvars(path))
        return ""
    
    def validate_config(self) -> bool:
        """
        Validate configuration values and check file accessibility.
        验证配置值并检查文件可访问性。
        
        Returns:
            True if configuration is valid, False otherwise
        """
        errors: List[str] = []
        
        # Validate input file
        input_file = self.get_path('input_file')
        backup_file = self.get_path('backup_input_file')
        
        if not os.path.exists(input_file):
            if backup_file and os.path.exists(backup_file):
                logger.info(f"Primary input file not found, using backup: {backup_file}")
                print(f"Primary input file not found, using backup: {backup_file}")
                self.config['paths']['input_file'] = backup_file
            else:
                errors.append(f"Input file not found: {input_file}")
        
        # Validate output directory
        output_dir = self.get_path('output_dir')
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"Created output directory: {output_dir}")
                print(f"Created output directory: {output_dir}")
            except Exception as e:
                errors.append(f"Cannot create output directory: {e}")
        
        # Validate numeric values
        validation_rules = [
            ('analysis', 'age_threshold', int, lambda x: x > 0, "Age threshold must be positive"),
            ('visualization', 'figure_width', (int, float), lambda x: x > 0, "Figure width must be positive"),
            ('visualization', 'figure_height', (int, float), lambda x: x > 0, "Figure height must be positive"),
            ('visualization', 'dpi', int, lambda x: x > 0, "DPI must be positive integer")
        ]
        
        for section, key, expected_type, validator, error_msg in validation_rules:
            value = self.get(section, key)
            if not isinstance(value, expected_type):
                errors.append(f"{error_msg}: {value} (invalid type)")
            elif not validator(value):
                errors.append(f"{error_msg}: {value}")
        
        if errors:
            logger.error("Configuration validation errors:")
            print("Configuration validation errors:")
            for error in errors:
                logger.error(f"  - {error}")
                print(f"  - {error}")
            return False
        
        return True
