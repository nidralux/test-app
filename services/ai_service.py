"""
Service for generating test cases using a local LLM API.
"""

import logging
import time
import requests
import json
from typing import Optional, Dict, Any, List
from requests.exceptions import RequestException, Timeout

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-powered test case generation using a local LLM API."""
    
    def __init__(self, model_id: str, api_key: Optional[str] = None):
        """
        Initialize AI service with the LM Studio endpoint.
        
        Args:
            model_id (str): Model ID to use
            api_key (str, optional): Not needed for LM Studio
        """
        if not model_id:
            raise ValueError("Model ID is required")
            
        self.model_id = model_id
        # Use the exact IP and port from your curl command
        self.api_url = "http://192.168.0.81:14342/v1/chat/completions"
        
        logger.info(f"Initialized AIService with local LLM model: {model_id}")
        
    def generate_test_cases(self, ticket_description: str) -> Optional[str]:
        """
        Generate test cases using the LM Studio API.
        
        Args:
            ticket_description (str): Description of the ticket
            
        Returns:
            str: Generated test cases text or None on failure
        
        Raises:
            ValueError: If ticket_description is empty or not a string
        """
        if not ticket_description:
            raise ValueError("Ticket description cannot be empty")
        if not isinstance(ticket_description, str):
            raise ValueError("Ticket description must be a string")
            
        logger.info(f"Generating test cases for ticket with {len(ticket_description)} chars")
        
        # Create prompt for test case generation
        prompt = self._create_test_case_prompt(ticket_description)
        
        # Format payload exactly like your curl command
        payload = {
            "model": self.model_id,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert test case generator following ISTQB best practices."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 2000
            # Remove the response_format part for now as it was incomplete
        }

        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            # Make the API request
            max_retries = 3
            for attempt in range(1, max_retries + 1):
                logger.debug(f"API request attempt {attempt}/{max_retries}")
                
                response = requests.post(self.api_url, json=payload, headers=headers)
                
                # Parse and return the response
                if response.status_code == 200:
                    # Chat completions return content in a different format than completions
                    response_json = response.json()
                    response_text = response_json.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    logger.info("Successfully generated test cases")
                    return response_text
                else:
                    logger.error(f"API error (Status {response.status_code}): {response.text}")
                    
                    if attempt < max_retries:
                        time.sleep(2)  # Wait before retrying
                    else:
                        return None
        except Exception as e:
            logger.exception(f"Exception while generating test cases: {e}")
            return None

    def list_available_models(self) -> List[Dict[str, Any]]:
        """
        Get a list of available models from the local LLM API.
        
        Returns:
            List[Dict[str, Any]]: List of available models or empty list on failure
        """
        models_url = f"{self.base_url}/v1/models"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        try:
            response = requests.get(models_url, headers=headers, timeout=self.timeout)
            if response.status_code == 200:
                return response.json().get("data", [])
            else:
                logger.error(f"Failed to list models: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return []
            
    def _create_api_payload(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Create the API request payload.
        
        Args:
            system_prompt (str): The system prompt for the model
            user_prompt (str): The user prompt containing the test case generation instructions
            
        Returns:
            Dict[str, Any]: The formatted API payload
        """
        return {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
    def _extract_response_text(self, response_json: Dict[str, Any]) -> str:
        """
        Extract text content from API response.
        
        Args:
            response_json (Dict[str, Any]): The API response JSON
            
        Returns:
            str: The extracted text content
            
        Raises:
            ValueError: If response format is unexpected
        """
        try:
            choices = response_json.get("choices", [])
            if not choices:
                raise ValueError("No choices in response")
                
            message = choices[0].get("message", {})
            if not message:
                raise ValueError("No message in first choice")
                
            content = message.get("content", "").strip()
            if not content:
                raise ValueError("No content in message")
                
            return content
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Error extracting response text: {str(e)}")
            logger.debug(f"Response JSON: {response_json}")
            raise ValueError(f"Unexpected response format: {str(e)}")
            
    def _create_test_case_prompt(self, ticket_description: str) -> str:
        """
        Create a prompt for test case generation.
        
        Args:
            ticket_description (str): Description of the ticket
            
        Returns:
            str: Formatted prompt
        """
        return f"""Generate comprehensive test cases for any type of functionality based on this ticket description: {ticket_description}

TESTING STANDARDS:
- Use ISTQB (International Software Testing Qualifications Board) best practices
- Follow the Given-When-Then format for test case design
- Ensure test cases cover positive, negative, and edge case scenarios
- Include boundary value analysis
- Consider security, performance, and usability aspects

TEST CASE QUALITY CRITERIA:
- Precision: Clearly defined steps
- Reproducibility: Exact input conditions
- Completeness: Cover multiple scenarios
- Traceability: Link to specific requirements

TECHNICAL REQUIREMENTS:
- Identify potential security vulnerabilities
- Test input validation mechanisms
- Check error handling and graceful degradation
- Validate input sanitization

SPECIFICS TO INCLUDE FOR EACH TEST CASE:
- Unique Test Case ID (use ID-001 format)
- Section name (like "Header", "Navigation", "Login", etc.)
- Detailed Preconditions (keep this brief and focused)
- APPROPRIATE NUMBER OF DETAILED, NUMBERED STEPS (use as many as needed for the specific test - could be 3, 5, 8, or more)
- Expected Results (what should happen when steps are executed correctly)
- Input Data (specific values to use in testing)
- Notes (optional additional context)

STRICT FORMAT REQUIREMENTS FOR EACH TEST CASE:
Follow this EXACT structure with proper spacing and clear section headers:

Test Case ID-001:
Section: [Feature or component name]
Preconditions: [Brief setup conditions - do NOT include the steps here]
Steps:
1. [First step]
2. [Second step]
3. [Third step]
... [Add more steps as needed for thoroughness]
Expected Result: [Clearly state what should happen]
Input: [Specific test data]
Notes: [Additional context if needed]

FORMATTING RULES:
1. NEVER place the steps inside the preconditions section
2. ALWAYS place test steps in the Steps section with numbered steps (1., 2., etc.)
3. ALWAYS make Expected Result a separate section after Steps
4. DO NOT use markdown headers (like ### or ####) within test cases
5. DO NOT use placeholders like 'None' or 'N/A' - provide actual content for each field
6. Separate each test case with a blank line
7. Keep fields clearly separated - don't mix content between fields

EXAMPLE OF A PROPERLY FORMATTED TEST CASE:
Test Case ID-001:
Section: Login
Preconditions: User has a valid account with username "testuser" and password "securepass123"
Steps:
1. Open the login page
2. Enter username "testuser" in the username field
3. Enter password "securepass123" in the password field
4. Click the "Login" button
Expected Result: User is successfully logged in and dashboard page is displayed
Input: Username: testuser, Password: securepass123
Notes: This test verifies the basic login functionality with valid credentials

Test Case ID-002:
Section: File Upload
Preconditions: User is logged in and on the file upload page; has a 5MB PDF file available for testing
Steps:
1. Click the "Choose File" button
2. Select a valid PDF file (5MB in size)
3. Verify the file name appears in the interface
4. Click the "Upload" button
5. Wait for the progress bar to complete
6. Verify success message appears
7. Navigate to the "My Files" section
8. Confirm the uploaded file appears in the file list
Expected Result: The file is successfully uploaded, a confirmation message is shown, and the file is accessible in the user's file list
Input: File type: PDF, File size: 5MB
Notes: This test demonstrates a more complex workflow with more steps due to the nature of the file upload feature

IMPORTANT: Generate 8-10 comprehensive test cases covering different aspects of the functionality described in the ticket. Ensure each test case is complete and follows the exact format above. Use an appropriate number of steps for each test case based on the complexity of what's being tested."""