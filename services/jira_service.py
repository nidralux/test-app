"""
Service for interacting with Jira API.
"""

import logging
from jira import JIRA
from jira.exceptions import JIRAError

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