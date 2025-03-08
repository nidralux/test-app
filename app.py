# app.py
# app.py
"""
Test Case Generator - Webhook Application

This application receives Jira webhook events and generates automated test cases
when tickets transition to "Ready for QA" status.
"""

import logging
import json
import traceback
import sys
from datetime import datetime
from functools import wraps
from typing import Dict, Any, Optional, Callable, Union, Tuple

from flask import Flask, request, jsonify, Response
import hmac
import hashlib

from services.jira_service import JiraService
from services.ai_service import AIService
from services.sheets_service import GoogleSheetsService
from services.test_case_service import TestCaseService
from config import Config, ConfigurationError

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler('webhook.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Add a simple test endpoint
@app.route('/webhook-test', methods=['GET', 'POST'])
def webhook_test():
    """Simple endpoint to test webhook connectivity."""
    logger.info(f"Webhook test received - Method: {request.method}")
    if request.is_json:
        logger.info(f"Test webhook payload: {request.json}")
    return jsonify({"status": "success", "message": "Webhook test endpoint reached"}), 200

@app.route('/test-qa-transition/<ticket_key>', methods=['GET'])
def test_qa_transition(ticket_key):
    """
    Test endpoint to simulate a ticket transition to "Ready for QA" status.
    This is useful for debugging when Jira webhooks aren't working.
    
    Args:
        ticket_key: The Jira ticket key to test (e.g., "PROJ-123")
    
    Returns:
        JSON response with test results
    """
    logger.info(f"Manual test requested for ticket {ticket_key}")
    
    try:
        # Create a simulated webhook event
        mock_webhook_data = {
            "webhookEvent": "jira:issue_updated",
            "issue": {
                "key": ticket_key,
                "fields": {
                    "status": {
                        "name": "Ready for QA"
                    }
                }
            },
            "changelog": {
                "items": [
                    {
                        "field": "status",
                        "fromString": "In Progress",
                        "toString": "Ready for QA"
                    }
                ]
            }
        }
        
        # Process the mock event
        logger.info(f"Processing mock webhook for {ticket_key}")
        issue_event = _parse_webhook_data(mock_webhook_data)
        
        if not issue_event:
            return jsonify({"status": "error", "message": "Failed to parse mock webhook data"}), 500
            
        # Process the ticket
        result = _process_ready_for_qa_ticket(ticket_key)
        
        if result:
            return jsonify({
                "status": "success", 
                "message": f"Successfully generated test cases for {ticket_key}"
            }), 200
        else:
            return jsonify({
                "status": "error", 
                "message": f"Failed to generate test cases for {ticket_key}"
            }), 500
            
    except Exception as e:
        logger.exception(f"Error in test endpoint: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Validate configuration on startup
try:
    Config.validate_config()
    Config.log_config()
except ConfigurationError as e:
    logger.critical(f"Configuration error: {str(e)}")
    sys.exit(1)

# Initialize services
try:
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

    sheets_service = GoogleSheetsService(
        Config.SPREADSHEET_ID,
        Config.JSON_KEYFILE_PATH
    )

    test_case_service = TestCaseService()
    
    logger.info("All services initialized successfully")
except Exception as e:
    logger.critical(f"Error initializing services: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

def validate_webhook_signature(f: Callable) -> Callable:
    """
    Decorator to validate webhook signatures if WEBHOOK_SECRET_TOKEN is set.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs) -> Response:
        if Config.WEBHOOK_SECRET_TOKEN:
            signature = request.headers.get('X-Jira-Signature')
            if not signature:
                logger.warning("Missing webhook signature")
                return jsonify({"error": "Missing signature"}), 401
                
            # Calculate expected signature
            payload = request.get_data()
            expected = hmac.new(
                Config.WEBHOOK_SECRET_TOKEN.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected):
                logger.warning("Invalid webhook signature")
                return jsonify({"error": "Invalid signature"}), 401
                
        return f(*args, **kwargs)
    return decorated_function

@app.route('/jira-webhook', methods=['POST'])
@validate_webhook_signature
def jira_webhook():
    """Handle incoming Jira webhook events."""
    try:
        webhook_data = request.json
        
        # Handle different webhook events
        event_type = webhook_data.get('webhookEvent')
        
        if event_type == 'jira:issue_created' and _is_new_hire_ticket(webhook_data):
            # Handle new hire ticket creation
            return _handle_new_hire_ticket(webhook_data)
        elif event_type == 'jira:issue_updated':
            # Original test case generation logic
            issue_event = _parse_webhook_data(webhook_data)
            
            if not issue_event:
                return jsonify({"success": True, "message": "Event ignored - not a relevant issue event"}), 200
            
            # Check if this is a "Ready for QA" transition
            to_status = issue_event.get("to_status", "")
            ready_qa_variations = ["ready for qa", "ready for QA", "ready 4 qa", "ready for quality assurance"]
            
            is_ready_for_qa = to_status and any(variation in to_status.lower() for variation in ready_qa_variations)
            
            if is_ready_for_qa:
                ticket_key = issue_event.get("key")
                # Process the ticket for test case generation
                result = _process_ready_for_qa_ticket(ticket_key)
                # Return appropriate response
                # ...
        
        # Default response
        return jsonify({"success": True, "message": "Event processed but no action taken"}), 200
        
    except Exception as e:
        logger.exception(f"Error processing webhook: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def _handle_new_hire_ticket(webhook_data: Dict) -> Tuple[Response, int]:
    """Handle creation of a new hire ticket."""
    try:
        issue = webhook_data.get('issue', {})
        fields = issue.get('fields', {})
        
        # Extract employee information from the ticket
        employee_info = {
            'name': fields.get('customfield_10001', ''),  # Employee Name field
            'role': fields.get('customfield_10002', ''),  # Role field
            'team': fields.get('customfield_10003', ''),  # Team field
            'start_date': fields.get('customfield_10004', ''),  # Start Date field
            'manager': fields.get('customfield_10005', ''),  # Manager field
            'project_key': fields.get('project', {}).get('key', 'SCRUM')
        }
        
        # Log the extracted information
        logger.info(f"Extracted employee info: {json.dumps(employee_info)}")
        
        # Validate required fields
        missing_fields = [k for k, v in employee_info.items() if not v]
        if missing_fields:
            logger.error(f"Missing required fields: {missing_fields}")
            return jsonify({
                "success": False,
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Generate onboarding plan
        success = onboarding_service.generate_onboarding_plan(employee_info)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Generated onboarding plan for {employee_info['name']}"
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Failed to generate onboarding plan"
            }), 500
            
    except Exception as e:
        logger.exception(f"Error handling new hire ticket: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

def _parse_webhook_data(webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse webhook data to extract issue event information.
    
    Args:
        webhook_data (Dict[str, Any]): Raw webhook data
        
    Returns:
        Optional[Dict[str, Any]]: Extracted issue event or None if not relevant
    """
    try:
        # Log the entire webhook payload for debugging
        logger.debug(f"Webhook payload: {json.dumps(webhook_data)}")
        
        # Check for issue event type
        event_type = webhook_data.get("webhookEvent")
        logger.info(f"Received webhook event type: {event_type}")
        
        if not event_type or "issue" not in event_type:
            logger.info(f"Ignoring non-issue event: {event_type}")
            return None
            
        # Extract the issue key
        issue_key = webhook_data.get("issue", {}).get("key")
        
        if not issue_key:
            logger.warning("Missing issue key in webhook data")
            return None
            
        # Check for status info in different locations
        # First try changelog for transition events
        changelog = webhook_data.get("changelog")
        from_status = None
        to_status = None
        
        if changelog:
            # Look for status change in items
            for item in changelog.get("items", []):
                if item.get("field") == "status":
                    from_status = item.get("fromString")
                    to_status = item.get("toString")
                    logger.info(f"Status transition detected for {issue_key}: {from_status} -> {to_status}")
                    break
                    
        # If no status change in changelog, try to get current status
        if not to_status:
            current_status = webhook_data.get("issue", {}).get("fields", {}).get("status", {}).get("name")
            if current_status:
                logger.info(f"No transition, current status for {issue_key}: {current_status}")
                # For issues with no transition but already in Ready for QA
                if current_status == "Ready for QA":
                    to_status = current_status
                    logger.info(f"Issue {issue_key} is already in Ready for QA status")
                else:
                    logger.info(f"Ignoring issue {issue_key} with status {current_status} (not a transition to Ready for QA)")
                    return None
            else:
                logger.warning(f"No status information found for issue {issue_key}")
                return None
                
        # Return the parsed event
        event_data = {
            "key": issue_key,
            "from_status": from_status,
            "to_status": to_status
        }
        logger.info(f"Parsed webhook data: {event_data}")
        return event_data
        
    except Exception as e:
        logger.exception(f"Error parsing webhook data: {str(e)}")
        return None


def _process_ready_for_qa_ticket(ticket_key: str) -> bool:
    """
    Process a ticket that has transitioned to "Ready for QA" status
    by generating test cases and storing them.
    
    Args:
        ticket_key (str): The Jira ticket key
        
    Returns:
        bool: True if processing succeeded, False otherwise
    """
    try:
        # Fetch ticket details from Jira
        ticket = jira_service.get_issue(ticket_key)
        
        if not ticket:
            logger.error(f"Failed to fetch ticket {ticket_key} from Jira")
            return False
            
        # Extract relevant info for test case generation
        ticket_summary = ticket.fields.summary if hasattr(ticket, 'fields') else "No summary"
        ticket_description = ticket.fields.description if hasattr(ticket, 'fields') and ticket.fields.description else ""
        
        if not ticket_description:
            logger.warning(f"Ticket {ticket_key} has no description")
            return False
            
        # Generate test cases using AI service
        logger.info(f"Generating test cases for ticket {ticket_key}")
        test_cases_text = ai_service.generate_test_cases(ticket_description)
        
        if not test_cases_text:
            logger.error(f"Failed to generate test cases for ticket {ticket_key}")
            return False
            
        # Structure the test cases
        parsed_test_cases = test_case_service.parse_test_cases(test_cases_text, ticket_key)
        
        if not parsed_test_cases:
            logger.error(f"Failed to parse test cases for ticket {ticket_key}")
            return False
        
        # Validate and score test cases    
        quality_scores = test_case_service.validate_test_cases(parsed_test_cases)
        
        # Upload to Google Sheets
        sheet_result = sheets_service.upload_test_cases(parsed_test_cases, quality_scores, ticket_key)
        
        if not sheet_result:
            logger.error(f"Failed to upload test cases for ticket {ticket_key} to Google Sheets")
            return False
            
        # Add comment to Jira ticket with link to spreadsheet
        comment = f"Test cases have been generated and stored in the [Test Cases spreadsheet|{sheets_service.get_spreadsheet_url()}]."
        jira_result = jira_service.add_comment(ticket_key, comment)
        
        if not jira_result:
            logger.warning(f"Failed to add comment to ticket {ticket_key}")
            # Continue anyway as this is non-critical
            
        return True
            
    except Exception as e:
        logger.exception(f"Error processing ticket {ticket_key}: {str(e)}")
        return False

# Add this helper function to check if a ticket is a new hire ticket
def _is_new_hire_ticket(webhook_data):
    """Check if the webhook is for a new hire ticket."""
    try:
        issue_type = webhook_data.get('issue', {}).get('fields', {}).get('issuetype', {}).get('name', '')
        return issue_type == 'New Hire'
    except Exception:
        return False

if __name__ == "__main__":
    logger.info(f"Starting Test Case Generator on {Config.HOST}:{Config.PORT}")
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )