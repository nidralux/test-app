#!/usr/bin/env python3
"""
Mock test for the onboarding task generator.
This simulates the process without actually creating Jira tickets.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ai_service import AIService
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

class MockJiraService:
    """Mock Jira service for testing."""
    
    def create_epic(self, project_key, summary, description):
        """Mock creating an epic."""
        logger.info(f"MOCK: Creating epic in project {project_key}")
        logger.info(f"Summary: {summary}")
        logger.info(f"Description: {description}")
        return type('obj', (object,), {'key': 'MOCK-123'})
    
    def create_issue(self, **kwargs):
        """Mock creating an issue."""
        logger.info(f"MOCK: Creating issue in project {kwargs.get('project_key')}")
        logger.info(f"Summary: {kwargs.get('summary')}")
        logger.info(f"Type: {kwargs.get('issue_type')}")
        logger.info(f"Epic: {kwargs.get('epic_link')}")
        logger.info(f"Due: {kwargs.get('due_date')}")
        return type('obj', (object,), {'key': 'MOCK-456'})
    
    def get_team_projects(self, team):
        """Mock getting team projects."""
        return [
            {
                'key': 'MOCK',
                'name': 'Mock Project',
                'description': 'A mock project for testing'
            },
            {
                'key': 'TEST',
                'name': 'Test Automation',
                'description': 'Test automation framework'
            }
        ]
    
    def get_project_tech_stack(self, project_key):
        """Mock getting project tech stack."""
        tech_stacks = {
            'MOCK': ['Python', 'Flask', 'PostgreSQL'],
            'TEST': ['Selenium', 'Cypress', 'Jest']
        }
        return tech_stacks.get(project_key, [])

class MockAIService:
    """Mock AI service for testing."""
    
    def enhance_onboarding_tasks(self, context):
        """Mock enhancing onboarding tasks."""
        logger.info("MOCK: Enhancing onboarding tasks with AI")
        
        # Return the base tasks with some enhancements
        base_tasks = context['base_tasks']
        enhanced_tasks = base_tasks.copy()
        
        # Add a couple of AI-generated tasks
        enhanced_tasks.append({
            "title": "Learn Cypress Test Framework",
            "description": "Complete Cypress onboarding:\n- Go through Cypress documentation\n- Complete basic tutorial\n- Write a simple test for the login page",
            "category": "Technical Learning",
            "estimated_days": 3
        })
        
        enhanced_tasks.append({
            "title": "Shadow Senior QA Engineer",
            "description": "Shadow a senior QA engineer for a day:\n- Observe testing processes\n- Learn about test prioritization\n- Understand regression testing approach",
            "category": "Mentorship",
            "estimated_days": 1
        })
        
        return enhanced_tasks

def main():
    """Test the onboarding task generator with mocks."""
    try:
        # Import the OnboardingService here to avoid circular imports
        from services.onboarding_service import OnboardingService
        
        # Initialize mock services
        jira_service = MockJiraService()
        ai_service = MockAIService()
        
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
        else:
            logger.error("❌ Failed to generate onboarding plan")
            
    except Exception as e:
        logger.exception(f"Error testing onboarding service: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main()) 