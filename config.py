# config.py
"""
Configuration settings for the Test Case Generator application.

This module loads and validates environment variables for application configuration.
It provides a centralized Config class for accessing validated settings throughout the app.
"""

import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Configure logger
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass

class Config:
    """Application configuration settings with validation."""
    
    # Flask Settings
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '5000'))
    
    # Jira Configuration
    JIRA_URL = os.getenv('JIRA_URL')
    JIRA_USERNAME = os.getenv('JIRA_USERNAME')
    JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
    
    # Together AI Configuration
    TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY', None)
    TOGETHER_MODEL_ID = os.getenv('TOGETHER_MODEL_ID', 'llama-3.3-70b-instruct')
    
    # Google Sheets Configuration
    SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
    JSON_KEYFILE_PATH = os.getenv('JSON_KEYFILE_PATH')
    
    # API Timeouts and Retries
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))
    API_MAX_RETRIES = int(os.getenv('API_MAX_RETRIES', '3'))
    
    # Webhook Security
    WEBHOOK_SECRET_TOKEN = os.getenv('WEBHOOK_SECRET_TOKEN', '')
    
    @classmethod
    def validate_config(cls) -> None:
        """
        Validate that all required configuration is present and valid.
        
        Raises:
            ConfigurationError: If any required configuration is missing or invalid
        """
        required_configs = {
            'JIRA_URL': cls.JIRA_URL,
            'JIRA_USERNAME': cls.JIRA_USERNAME,
            'JIRA_API_TOKEN': cls.JIRA_API_TOKEN,
            'TOGETHER_API_KEY': cls.TOGETHER_API_KEY,
            'TOGETHER_MODEL_ID': cls.TOGETHER_MODEL_ID,
            'SPREADSHEET_ID': cls.SPREADSHEET_ID,
            'JSON_KEYFILE_PATH': cls.JSON_KEYFILE_PATH
        }
        
        missing = [key for key, value in required_configs.items() if not value]
        
        if missing:
            error_msg = f"Missing required configuration: {', '.join(missing)}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        
        # File existence check
        if not os.path.exists(cls.JSON_KEYFILE_PATH):
            error_msg = f"Google service account JSON key file not found: {cls.JSON_KEYFILE_PATH}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        
        # Additional validation for other fields could be added here
        logger.info("Configuration validation passed")
    
    @classmethod
    def as_dict(cls) -> Dict[str, Any]:
        """
        Return configuration as a dictionary, excluding private attributes.
        
        Returns:
            Dict[str, Any]: Dictionary of configuration settings
        """
        return {
            key: value for key, value in cls.__dict__.items() 
            if not key.startswith('_') and key.isupper()
        }
        
    @classmethod
    def log_config(cls, obscure_secrets: bool = True) -> None:
        """
        Log the current configuration, optionally obscuring sensitive values.
        
        Args:
            obscure_secrets (bool): Whether to obscure sensitive values
        """
        config_dict = cls.as_dict()
        
        # Obscure sensitive values
        if obscure_secrets:
            for key in ['JIRA_API_TOKEN', 'TOGETHER_API_KEY', 'WEBHOOK_SECRET_TOKEN']:
                if key in config_dict and config_dict[key]:
                    config_dict[key] = f"{config_dict[key][:4]}...{config_dict[key][-4:]}"
        
        logger.info(f"Application configuration: {config_dict}")