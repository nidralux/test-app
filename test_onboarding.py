#!/usr/bin/env python3
"""
Test script for the onboarding task generator.
This simulates creating a new hire ticket for a QA engineer.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.jira_service import JiraService
from services.ai_service import AIService
from services.onboarding_service import OnboardingService
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def main():
    """Test the onboarding task generator."""
    try:
        # Initialize services
        jira_service = JiraService(
            Config.JIRA_URL,
            Config.JIRA_USERNAME,
            Config.JIRA_API_TOKEN
        )
        
        ai_service = AIService(
            Config.TOGETHER_MODEL_ID,
            Config.TOGETHER_API_KEY,
            timeout=Config.API_TIMEOUT,
            max_retries=Config.API_MAX_RETRIES
        )
        
        onboarding_service = OnboardingService(jira_service, ai_service)
        
        # Create test employee info
        start_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        employee_info = {
            'name': 'Jane Smith',
            'role': 'QA Engineer',
            'team': 'Core Platform',
            'start_date': start_date,
            'manager': 'John Doe',
            'project_key': 'SCRUM'  # Use your actual project key
        }
        
        # Generate onboarding plan
        logger.info(f"Generating onboarding plan for {employee_info['name']}")
        success = onboarding_service.generate_onboarding_plan(employee_info)
        
        if success:
            logger.info("✅ Successfully generated onboarding plan!")
            logger.info(f"Check your Jira project {employee_info['project_key']} for the new epic")
        else:
            logger.error("❌ Failed to generate onboarding plan")
            
    except Exception as e:
        logger.exception(f"Error testing onboarding service: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main()) 