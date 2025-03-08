"""
Service for parsing, validating, and improving test cases.
"""

import logging
import re

logger = logging.getLogger(__name__)

class TestCaseService:
    """Service for test case processing operations."""
    
    def parse_test_cases(self, test_cases_text, ticket_key):
        """
        Parse the generated test cases into a structured format.
        
        Args:
            test_cases_text (str): Raw text of generated test cases
            ticket_key (str): The Jira ticket key
            
        Returns:
            list: List of parsed test case dictionaries
        """
        # Split the test cases by each test case
        test_cases = []
        
        # First, normalize the text by converting markdown style headers to plain text
        normalized_text = re.sub(r'#{1,6}\s+', '', test_cases_text)
        
        # Use regex to find test case blocks
        test_case_pattern = r'Test Case ([\w-]+):(.*?)(?=Test Case [\w-]+:|$)'
        matches = re.findall(test_case_pattern, normalized_text, re.DOTALL)
        
        if not matches:
            logger.warning(f"No test cases found in generated text for ticket {ticket_key}")
            # Try a more lenient pattern if the first one fails
            test_case_pattern = r'(ID-\d+):(.*?)(?=ID-\d+:|$)'
            matches = re.findall(test_case_pattern, normalized_text, re.DOTALL)
        
        # Ensure we have at least one match
        if not matches:
            logger.error(f"Failed to parse any test cases from text for ticket {ticket_key}")
            return []
            
        parsed_count = 0
        for idx, (test_id, content) in enumerate(matches, 1):
            try:
                # Default values with empty strings instead of placeholders
                test_case_id = f"TC-{test_id.strip()}" if test_id.strip() else f"TC-{idx:03d}"
                section = "General"
                preconditions = ""
                steps = ""
                expected_result = ""
                input_data = ""
                notes = ""
                
                # Clean up the content by removing extra whitespace and normalizing newlines
                content = re.sub(r'\n{3,}', '\n\n', content.strip())
                
                # Extract section
                section_match = re.search(r'Section:\s*(.*?)(?=\n|$)', content)
                if section_match and section_match.group(1).strip():
                    section = section_match.group(1).strip()
                
                # Extract preconditions - improved pattern matching
                preconditions_pattern = r'Preconditions?:\s*(.*?)(?=\nSteps|\n[Ss]teps:|$)'
                preconditions_match = re.search(preconditions_pattern, content, re.DOTALL)
                if preconditions_match and preconditions_match.group(1).strip():
                    preconditions = self._clean_field_content(preconditions_match.group(1))
                
                # Extract steps using multiple potential patterns
                steps_patterns = [
                    r'Steps?:(.*?)(?=Expected Result|[Ee]xpected [Rr]esult:|$)',
                    r'Steps?:(.*?)(?=\nExpected|\n[Ee]xpected:|$)'
                ]
                
                for pattern in steps_patterns:
                    steps_match = re.search(pattern, content, re.DOTALL)
                    if steps_match and steps_match.group(1).strip():
                        steps_text = steps_match.group(1).strip()
                        steps = self._format_steps(steps_text)
                        break
                
                # If steps are still empty, try one more pattern specifically for the issue mentioned
                if not steps and "Steps:" in content:
                    # Special case for steps in preconditions
                    content_parts = content.split("Steps:")
                    if len(content_parts) > 1:
                        potential_steps = content_parts[1].strip()
                        # Look for a numbered list
                        if re.search(r'^\s*\d+\.', potential_steps, re.MULTILINE):
                            steps_text = potential_steps.split("Expected Result:")[0].strip()
                            steps = self._format_steps(steps_text)
                            # If we found steps here, we need to clean up preconditions
                            if preconditions and "Steps:" in preconditions:
                                preconditions = preconditions.split("Steps:")[0].strip()
                
                # Extract expected result with multiple potential patterns
                expected_patterns = [
                    r'Expected Result:?\s*(.*?)(?=\nInput|\n[Ii]nput:|$)',
                    r'Expected Result:?\s*(.*?)(?=\nInput Data|\n[Ii]nput [Dd]ata:|$)'
                ]
                
                for pattern in expected_patterns:
                    expected_match = re.search(pattern, content, re.DOTALL)
                    if expected_match and expected_match.group(1).strip():
                        expected_result = self._clean_field_content(expected_match.group(1))
                        break
                
                # Extract input data with multiple potential patterns
                input_patterns = [
                    r'Input:?\s*(.*?)(?=\nNotes|\n[Nn]otes:|$)',
                    r'Input Data:?\s*(.*?)(?=\nNotes|\n[Nn]otes:|$)'
                ]
                
                for pattern in input_patterns:
                    input_match = re.search(pattern, content, re.DOTALL)
                    if input_match and input_match.group(1).strip():
                        input_data = self._clean_field_content(input_match.group(1))
                        break
                
                # Extract notes - improved pattern matching to catch end of content
                notes_patterns = [
                    r'Notes:?\s*(.*?)$',
                    r'Notes:?\s*(.*)$'
                ]
                
                for pattern in notes_patterns:
                    notes_match = re.search(pattern, content, re.DOTALL)
                    if notes_match and notes_match.group(1).strip():
                        notes = self._clean_field_content(notes_match.group(1))
                        break
                
                # If we can't find expected result but we found steps, try to extract it from the steps
                if not expected_result and steps:
                    step_parts = re.split(r'\nExpected Result:|\n[Ee]xpected [Rr]esult:', steps)
                    if len(step_parts) > 1:
                        # Found expected result in steps, fix both
                        steps = self._format_steps(step_parts[0])
                        expected_result = self._clean_field_content(step_parts[1])
                
                # Check if test case is incomplete
                incomplete_fields = []
                if not preconditions:
                    incomplete_fields.append("preconditions")
                if not steps:
                    incomplete_fields.append("steps")
                if not expected_result:
                    incomplete_fields.append("expected_result")
                
                # Log warning for incomplete test cases
                if incomplete_fields:
                    logger.warning(
                        f"Test case {test_case_id} for ticket {ticket_key} "
                        f"is missing required fields: {', '.join(incomplete_fields)}"
                    )
                
                # Add the test case to the list
                test_cases.append({
                    'id': test_case_id,
                    'ticket_key': ticket_key,
                    'section': section,
                    'preconditions': preconditions,
                    'steps': steps,
                    'expected_result': expected_result,
                    'input_data': input_data,
                    'notes': notes,
                    'is_complete': len(incomplete_fields) == 0
                })
                parsed_count += 1
                
            except Exception as e:
                logger.error(f"Error parsing test case {idx} for ticket {ticket_key}: {str(e)}")
                # Continue with the next test case
        
        logger.info(f"Successfully parsed {parsed_count} test cases for ticket {ticket_key}")
        if parsed_count < len(matches):
            logger.warning(f"{len(matches) - parsed_count} test cases could not be parsed for ticket {ticket_key}")
        
        # Check if any test cases have missing fields
        incomplete_count = sum(1 for tc in test_cases if not tc['is_complete'])
        if incomplete_count > 0:
            logger.warning(f"{incomplete_count} test cases have missing fields and need review")
        
        return test_cases
    
    def _clean_field_content(self, content):
        """Clean up field content by removing markdown and extra whitespace."""
        if not content:
            return ""
            
        # Remove markdown formatting markers
        content = re.sub(r'#{1,6}\s+', '', content)
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
        content = re.sub(r'\*(.*?)\*', r'\1', content)
        
        # Normalize newlines and remove extra whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()
    
    def _format_steps(self, steps_text):
        """Format steps to ensure they are properly numbered."""
        if not steps_text:
            return ""
            
        # Clean up steps text
        steps_text = self._clean_field_content(steps_text)
        
        # Split into lines
        step_lines = [line.strip() for line in steps_text.split('\n') if line.strip()]
        formatted_steps = []
        
        for line in step_lines:
            # Check if line starts with a number
            if re.match(r'^\d+\.', line):
                formatted_steps.append(line)
            else:
                # Add a number if missing
                formatted_steps.append(f"{len(formatted_steps) + 1}. {line}")
        
        return '\n'.join(formatted_steps)
    
    def validate_test_cases(self, test_cases):
        """
        Validate generated test cases against quality metrics.
        
        Args:
            test_cases (list): List of test case dictionaries
            
        Returns:
            list: List of quality score dictionaries
        """
        quality_scores = []
        
        for test_case in test_cases:
            # Count steps in steps field
            step_count = len(re.findall(r'^\d+\.', test_case['steps'], re.MULTILINE))
            
            # Log the number of steps for each test case
            logger.debug(f"Test case {test_case['id']} has {step_count} steps")
            
            # Scoring Criteria
            criteria = {
                'has_preconditions': len(test_case['preconditions']) > 5,
                'has_minimum_steps': step_count >= 3,  # Minimum of 3 steps required
                'has_appropriate_step_count': self._has_appropriate_step_count(test_case['section'], step_count),
                'has_expected_result': len(test_case['expected_result']) > 10,
                'has_input_data': len(test_case['input_data']) > 3,
                'covers_multiple_scenarios': any([
                    'invalid' in test_case.get('input_data', '').lower(),
                    'edge case' in test_case.get('notes', '').lower(),
                    'boundary' in test_case.get('notes', '').lower()
                ]),
                'is_complete': test_case.get('is_complete', False)
            }
            
            # Calculate score
            score = sum(criteria.values()) * 100 / len(criteria)  # Max score 100
            
            # Define areas for improvement based on criteria
            areas_for_improvement = [
                key for key, value in criteria.items() if not value
            ]
            
            # Get incomplete fields if they exist
            incomplete_fields = []
            if not test_case.get('is_complete', False):
                if not test_case.get('preconditions', ''):
                    incomplete_fields.append('preconditions')
                if not test_case.get('steps', ''):
                    incomplete_fields.append('steps')
                if not test_case.get('expected_result', ''):
                    incomplete_fields.append('expected_result')
            
            # Create quality score entry
            quality_scores.append({
                'test_case_id': test_case['id'],  # Updated field name
                'score': score,
                'areas_for_improvement': areas_for_improvement,
                'incomplete_fields': incomplete_fields
            })
        
        return quality_scores
    
    def _has_appropriate_step_count(self, section: str, step_count: int) -> bool:
        """
        Determine if the number of steps is appropriate for the type of test case.
        
        Args:
            section (str): The section/component being tested
            step_count (int): The number of steps in the test case
            
        Returns:
            bool: True if the step count is appropriate, False otherwise
        """
        # For simple operations, 3-5 steps is usually sufficient
        simple_sections = ['login', 'logout', 'search', 'filter', 'sort', 'view']
        
        # For complex operations, expect more steps
        complex_sections = ['upload', 'workflow', 'wizard', 'checkout', 'registration', 'import', 'export']
        
        section_lower = section.lower()
        
        # Check if this is a simple section (needs fewer steps)
        if any(simple in section_lower for simple in simple_sections):
            return 3 <= step_count <= 6
            
        # Check if this is a complex section (needs more steps)
        elif any(complex in section_lower for complex in complex_sections):
            return step_count >= 5
            
        # For all other sections, just ensure there are at least 3 steps
        return step_count >= 3
    
    def improve_test_cases(self, test_cases, quality_scores):
        """
        Provide recommendations for improving test cases.
        
        Args:
            test_cases (list): List of test case dictionaries
            quality_scores (list): List of quality score dictionaries
            
        Returns:
            list: List of recommendation strings
        """
        recommendations = []
        
        for score_info in quality_scores:
            if score_info['score'] < 60 or score_info.get('incomplete_fields'):
                recommendation = f"Test Case {score_info['test_case_id']} needs improvement in:"
                
                # Handle missing fields first as highest priority
                if score_info.get('incomplete_fields'):
                    recommendation += "\n- Missing fields that need completion:"
                    for field in score_info['incomplete_fields']:
                        recommendation += f"\n  * {field.replace('_', ' ').capitalize()}"
                        
                # Handle improvement areas next
                if score_info.get('areas_for_improvement'):
                    recommendation += "\n- Areas for improvement:"
                    for area in score_info['areas_for_improvement']:
                        # Skip is_complete since we've already covered missing fields
                        if area != 'is_complete':
                            recommendation += f"\n  * {area.replace('has_', '').replace('_', ' ').capitalize()}"
                
                recommendations.append(recommendation)
        
        return recommendations
    
    def filter_incomplete_test_cases(self, test_cases):
        """
        Filter test cases that need review due to missing fields.
        
        Args:
            test_cases (list): List of test case dictionaries
            
        Returns:
            tuple: (complete_test_cases, incomplete_test_cases)
        """
        complete = []
        incomplete = []
        
        for test_case in test_cases:
            if not test_case.get('is_complete', False):  # Updated field name
                incomplete.append(test_case)
            else:
                complete.append(test_case)
        
        return complete, incomplete
    
    def clean_test_cases(self, test_cases):
        """
        Clean up test cases by removing internal metadata fields.
        
        Args:
            test_cases (list): List of test case dictionaries
            
        Returns:
            list: Cleaned test cases suitable for export
        """
        cleaned_cases = []
        
        for test_case in test_cases:
            # Create a copy without internal tracking fields
            cleaned = {k: v for k, v in test_case.items() 
                      if k not in ['is_complete']}  # Updated field name
            cleaned_cases.append(cleaned)
        
        return cleaned_cases