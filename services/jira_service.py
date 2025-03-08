"""
Service for interacting with Jira API.
"""

import logging
from jira import JIRA
from jira.exceptions import JIRAError
from typing import Any, List, Dict, Optional

logger = logging.getLogger(__name__)

class JiraService:
    """Service for Jira API operations."""
    
    def __init__(self, jira_url, username, api_token):
        """
        Initialize Jira service with authentication credentials.
        
        Args:
            jira_url (str): Jira instance URL
            username (str): Jira username (usually email)
            api_token (str): Jira API token
        """
        self.jira_url = jira_url
        self.username = username
        self.api_token = api_token
        self.client = None
        
        self._authenticate()
        
    def _authenticate(self):
        """Authenticate with Jira API."""
        try:
            self.client = JIRA(
                server=self.jira_url,
                basic_auth=(self.username, self.api_token)
            )
            logger.info("Successfully authenticated with JIRA")
        except JIRAError as e:
            logger.error(f"Failed to authenticate with JIRA: {e}")
            raise
            
    def get_issue(self, issue_key):
        """
        Retrieve issue details from Jira.
        
        Args:
            issue_key (str): The Jira issue key
            
        Returns:
            jira.Issue: The Jira issue object or None if not found
        """
        try:
            return self.client.issue(issue_key)
        except JIRAError as e:
            logger.error(f"Failed to retrieve issue {issue_key}: {e}")
            return None
            
    def add_comment(self, issue_key, comment_text):
        """
        Add a comment to a Jira issue.
        
        Args:
            issue_key (str): The Jira issue key
            comment_text (str): The comment text
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.client.add_comment(issue_key, comment_text)
            logger.info(f"Added comment to issue {issue_key}")
            return True
        except JIRAError as e:
            logger.error(f"Failed to add comment to issue {issue_key}: {e}")
            return False
    
    def create_epic(self, project_key: str, summary: str, description: str) -> Optional[Any]:
        """Create a new epic in Jira."""
        try:
            epic = self.client.create_issue(
                project=project_key,
                summary=summary,
                description=description,
                issuetype={'name': 'Epic'}
            )
            return epic
        except Exception as e:
            logger.error(f"Error creating epic: {str(e)}")
            return None
    
    def get_team_projects(self, team: str) -> List[Dict]:
        """Get active projects for a team."""
        try:
            # Search for projects with team label/component
            jql = f'project in projectsLeadByTeam("{team}") AND status != Closed'
            projects = self.client.search_issues(jql)
            
            return [
                {
                    'key': project.key,
                    'name': project.fields.summary,
                    'description': project.fields.description
                }
                for project in projects
            ]
        except Exception as e:
            logger.error(f"Error getting team projects: {str(e)}")
            return []
    
    def get_project_tech_stack(self, project_key: str) -> List[str]:
        """Get technology stack from project properties/labels."""
        try:
            project = self.client.project(project_key)
            # This assumes you store tech stack in project properties or labels
            tech_stack = project.raw.get('properties', {}).get('techStack', '').split(',')
            return [tech.strip() for tech in tech_stack if tech.strip()]
        except Exception as e:
            logger.error(f"Error getting project tech stack: {str(e)}")
            return []