"""
Service for generating test cases using Together AI API.
"""

import logging
import time
import requests
import json
from typing import Optional, Dict, Any, List
from requests.exceptions import RequestException, Timeout

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-powered test case generation using LLM APIs."""
    
    def __init__(self, model_id: str, api_key: str, timeout: int = 30, max_retries: int = 3, retry_delay: float = 2.0):
        """
        Initialize AI service with API credentials.
        
        Args:
            model_id (str): Together AI model ID
            api_key (str): Together AI API key
            timeout (int): Request timeout in seconds
            max_retries (int): Maximum number of retries for failed API calls
            retry_delay (float): Delay between retries in seconds
        """
        if not model_id:
            raise ValueError("Model ID is required")
        if not api_key:
            raise ValueError("API key is required")
            
        self.model_id = model_id
        self.api_key = api_key
        self.api_url = "https://api.together.xyz/v1/chat/completions"
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        logger.info(f"Initialized AIService with model: {model_id}")
        
    def generate_test_cases(self, ticket_description: str) -> Optional[str]:
        """
        Generate test cases using the Together AI API.
        
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
        
        # Create system and user prompts
        system_prompt = """You are an expert test case generator following ISTQB best practices. 
You design comprehensive test cases with an appropriate number of steps based on the complexity of the feature being tested. 
Simple features may need only 3-4 steps, while complex workflows might require 8-10 detailed steps.
Focus on creating thorough, practical test cases that QA engineers can easily follow."""
        user_prompt = self._create_test_case_prompt(ticket_description)
        
        # Create API payload
        payload = self._create_api_payload(system_prompt, user_prompt)
        
        # Create headers with authentication
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # Make API request with retries
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"API request attempt {attempt}/{self.max_retries}")
                response = requests.post(
                    self.api_url, 
                    json=payload, 
                    headers=headers, 
                    timeout=self.timeout
                )
                
                # Check for successful response
                if response.status_code == 200:
                    response_json = response.json()
                    response_text = self._extract_response_text(response_json)
                    logger.info("Successfully generated test cases")
                    return response_text
                
                # Handle rate limiting
                if response.status_code == 429:
                    wait_time = min(self.retry_delay * attempt * 2, 60)  # Exponential backoff
                    logger.warning(f"Rate limited. Waiting {wait_time}s before retry.")
                    time.sleep(wait_time)
                    continue
                    
                # Log other errors
                logger.error(f"API error (Status {response.status_code}): {response.text}")
                
                # Don't retry for client errors except rate limiting
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    break
                    
            except Timeout:
                logger.warning(f"Request timed out (attempt {attempt}/{self.max_retries})")
            except RequestException as e:
                logger.error(f"Request exception (attempt {attempt}/{self.max_retries}): {str(e)}")
            except Exception as e:
                logger.exception(f"Unexpected error: {str(e)}")
                break
                
            # Wait before retrying (if not the last attempt)
            if attempt < self.max_retries:
                time.sleep(self.retry_delay * attempt)  # Progressive delay
                
        logger.error("Failed to generate test cases after all retries")
        return None
            
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