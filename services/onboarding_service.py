"""
Service for generating and managing personalized onboarding tasks.
"""

import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class OnboardingService:
    """Service for generating personalized onboarding plans."""
    
    def __init__(self, jira_service, ai_service):
        """
        Initialize the onboarding service.
        
        Args:
            jira_service: Instance of JiraService for creating tasks
            ai_service: Instance of AIService for task customization
        """
        self.jira_service = jira_service
        self.ai_service = ai_service
        self.role_templates = self._load_role_templates()
        
    def generate_onboarding_plan(self, employee_info: Dict) -> bool:
        """
        Generate and create a personalized onboarding plan.
        
        Args:
            employee_info: Dict containing employee details including:
                - name: Employee's full name
                - role: Job role/title
                - team: Team name
                - start_date: Start date
                - manager: Manager's username
                - project_key: Jira project key
                
        Returns:
            bool: True if plan was created successfully, False otherwise
        """
        try:
            logger.info(f"Generating onboarding plan for {employee_info['name']}")
            
            # Get base tasks for the role
            base_tasks = self._get_base_tasks(employee_info['role'])
            if not base_tasks:
                logger.warning(f"No base tasks found for role: {employee_info['role']}")
                return False
            
            # Get team-specific tasks
            team_tasks = self._get_team_tasks(employee_info['team'])
            logger.debug(f"Found {len(team_tasks)} team-specific tasks")
            
            # Combine and enhance tasks using AI
            all_tasks = base_tasks + team_tasks
            customized_tasks = self._enhance_tasks(all_tasks, employee_info)
            
            if not customized_tasks:
                logger.error("Failed to generate customized tasks")
                return False
            
            # Create epic and tasks in Jira
            return self._create_onboarding_epic(employee_info, customized_tasks)
            
        except Exception as e:
            logger.exception(f"Error generating onboarding plan: {str(e)}")
            return False
    
    def _load_role_templates(self) -> Dict:
        """Load role-based task templates from configuration."""
        try:
            template_path = os.path.join(
                os.path.dirname(__file__), 
                '../config/onboarding_templates.json'
            )
            
            with open(template_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading role templates: {str(e)}")
            return {}
    
    def _get_base_tasks(self, role: str) -> List[Dict]:
        """Get base onboarding tasks for a specific role."""
        role = role.lower()
        templates = self.role_templates
        
        # Try exact match first
        if role in templates:
            return templates[role]
            
        # Try partial match
        for template_role, tasks in templates.items():
            if template_role.lower() in role or role in template_role.lower():
                return tasks
                
        return []
    
    def _get_team_tasks(self, team: str) -> List[Dict]:
        """Get team-specific onboarding tasks."""
        try:
            # Get team's active projects
            team_projects = self.jira_service.get_team_projects(team)
            
            # Get team's tech stack and tools from project metadata
            tech_stack = self._extract_tech_stack(team_projects)
            
            # Generate team-specific tasks
            team_tasks = [
                {
                    "title": f"Review {project['name']} Project Documentation",
                    "description": f"Familiarize yourself with the {project['name']} project:\n"
                                 f"- Review project documentation\n"
                                 f"- Understand project architecture\n"
                                 f"- Review recent sprint activities",
                    "category": "Project Knowledge",
                    "estimated_days": 2
                }
                for project in team_projects
            ]
            
            # Add tech stack specific tasks
            for tech in tech_stack:
                team_tasks.append({
                    "title": f"Setup and Configure {tech}",
                    "description": f"Install and configure {tech} for development:\n"
                                 f"- Follow setup documentation\n"
                                 f"- Verify installation\n"
                                 f"- Complete basic tutorial if needed",
                    "category": "Technical Setup",
                    "estimated_days": 1
                })
            
            return team_tasks
            
        except Exception as e:
            logger.error(f"Error getting team tasks: {str(e)}")
            return []
    
    def _extract_tech_stack(self, projects: List[Dict]) -> List[str]:
        """Extract unique tech stack items from project metadata."""
        tech_stack = set()
        
        for project in projects:
            # Extract from project properties or labels
            stack_items = self.jira_service.get_project_tech_stack(project['key'])
            tech_stack.update(stack_items)
        
        return list(tech_stack)
    
    def _enhance_tasks(self, tasks: List[Dict], employee_info: Dict) -> List[Dict]:
        """Use AI to enhance and personalize tasks."""
        try:
            # Prepare context for AI
            context = {
                "employee": employee_info,
                "base_tasks": tasks,
                "company_docs": self._get_documentation_links()
            }
            
            # Get AI suggestions
            enhanced_tasks = self.ai_service.enhance_onboarding_tasks(context)
            
            # Add timeline and dependencies
            return self._add_task_timeline(enhanced_tasks)
            
        except Exception as e:
            logger.error(f"Error enhancing tasks: {str(e)}")
            return tasks
    
    def _add_task_timeline(self, tasks: List[Dict]) -> List[Dict]:
        """Add timeline and dependencies to tasks."""
        current_day = 1
        for task in tasks:
            estimated_days = task.get('estimated_days', 1)
            task['start_day'] = current_day
            task['due_day'] = current_day + estimated_days
            
            if task['category'] == 'Technical Setup':
                current_day += estimated_days
                
        return tasks
    
    def _create_onboarding_epic(self, employee_info: Dict, tasks: List[Dict]) -> bool:
        """Create onboarding epic and subtasks in Jira."""
        try:
            # Create epic
            epic_summary = f"Onboarding Plan - {employee_info['name']}"
            epic_description = (
                f"Onboarding plan for {employee_info['name']}\n"
                f"Role: {employee_info['role']}\n"
                f"Team: {employee_info['team']}\n"
                f"Start Date: {employee_info['start_date']}\n"
                f"Manager: {employee_info['manager']}"
            )
            
            epic = self.jira_service.create_epic(
                project_key=employee_info['project_key'],
                summary=epic_summary,
                description=epic_description
            )
            
            if not epic:
                logger.error("Failed to create onboarding epic")
                return False
            
            # Create tasks
            start_date = datetime.strptime(employee_info['start_date'], '%Y-%m-%d')
            
            for task in tasks:
                due_date = start_date + timedelta(days=task['due_day'])
                
                self.jira_service.create_issue(
                    project_key=employee_info['project_key'],
                    summary=task['title'],
                    description=task['description'],
                    issue_type='Task',
                    epic_link=epic.key,
                    due_date=due_date.strftime('%Y-%m-%d'),
                    assignee=employee_info['name']
                )
            
            logger.info(f"Created onboarding epic {epic.key} with {len(tasks)} tasks")
            return True
            
        except Exception as e:
            logger.exception(f"Error creating onboarding epic: {str(e)}")
            return False
    
    def _get_documentation_links(self) -> Dict[str, str]:
        """Get relevant documentation links."""
        # This could be expanded to pull from a documentation management system
        return {
            "general": "https://confluence.company.com/onboarding",
            "engineering": "https://confluence.company.com/engineering",
            "product": "https://confluence.company.com/product",
            "qa": "https://confluence.company.com/qa"
        } 