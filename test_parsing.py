#!/usr/bin/env python3
"""
Script to test the test case parsing logic with sample AI-generated output.
This helps validate that our parsing enhancements correctly handle various formatting issues.
"""

import sys
import argparse
import logging
from services.test_case_service import TestCaseService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

# Sample test cases with the formatting issues mentioned by the user
SAMPLE_TEST_CASES = """
Test Case ID-001:
Section: Header
Preconditions: The user is on the home page.
#### Steps:
1. Open the home page in a desktop browser (e.g., Google Chrome, Mozilla Firefox) with a screen resolution of 1920x1080 pixels.
2. Verify that the logo is displayed in the top-left corner of the header section.
3. Check that the logo is correctly sized and aligned according to the branding guidelines.
4. Click on the logo and verify that it redirects to the home page.
5. Repeat steps 1-4 on different devices (tablet, mobile) to ensure responsiveness.
6. Verify that the logo is accessible by keyboard navigation and that it has a clear alt text for screen readers.

#### Expected Result: The logo is correctly displayed, sized, and aligned in the header section across different devices and screen sizes. It redirects to the home page when clicked and is accessible.

#### Input: 
- Device: Desktop, Tablet, Mobile
- Browser: Google Chrome, Mozilla Firefox
- Screen Resolution: 1920x1080 pixels (desktop), variable (tablet, mobile)

#### Notes: This test case ensures the logo's visibility, responsiveness, and accessibility across different devices and browsers.

Test Case ID-002:
Section: Navigation
Preconditions: The user is on the home page with a working internet connection.
Steps:
1. Verify that the navigation menu is visible in the header section.
2. Hover over each navigation menu item to check for hover effects.
3. Click on each navigation menu item and verify it navigates to the correct page.
4. Test keyboard navigation through the menu items using the Tab key.
5. Test the navigation menu on mobile devices by triggering the hamburger menu.
Expected Result: All navigation menu items are visible, clickable, and navigate to the correct pages. The menu is accessible via keyboard and functions correctly on mobile devices.
Input: 
- Navigation menu items: Home, About, Features, Contact
- Devices: Desktop, Tablet, Mobile
Notes: This test verifies the functionality and accessibility of the main navigation menu.

Test Case ID-003:
Section: Search
Preconditions: The application is loaded and the search bar is visible in the header.
Steps:
1. Click on the search bar.
2. Enter a valid search term (e.g., "feature").
3. Press the search button or hit Enter.
4. Verify that search results appear.
5. Test with an empty search term.
6. Test with special characters in the search term.
Expected Result: The search functionality returns relevant results for valid queries, handles empty searches appropriately, and properly sanitizes special characters.
Input: 
- Valid search term: "feature"
- Empty search term: ""
- Special characters: "search!@#$%"
Notes: This test ensures the search functionality works as expected with various inputs.

Test Case ID-004:
Section: User Profile
Preconditions: The user is logged in to the application.
"""

def main():
    parser = argparse.ArgumentParser(description='Test the test case parsing logic')
    parser.add_argument('--file', '-f', help='Path to a file containing test cases to parse')
    args = parser.parse_args()
    
    test_case_service = TestCaseService()
    
    if args.file:
        try:
            with open(args.file, 'r') as f:
                test_cases_text = f.read()
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            return
    else:
        # Use the sample test cases
        test_cases_text = SAMPLE_TEST_CASES
    
    # Parse the test cases
    parsed_test_cases = test_case_service.parse_test_cases(test_cases_text, "TEST-001")
    
    # Display the results
    logger.info(f"Parsed {len(parsed_test_cases)} test cases")
    
    for i, test_case in enumerate(parsed_test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"ID: {test_case['id']}")
        print(f"Section: {test_case['section']}")
        print(f"Preconditions: {test_case['preconditions']}")
        print(f"Steps: {test_case['steps']}")
        print(f"Expected Result: {test_case['expected_result']}")
        print(f"Input Data: {test_case['input_data']}")
        print(f"Notes: {test_case['notes']}")
        print(f"Is Complete: {test_case['is_complete']}")
        print("-" * 40)

if __name__ == "__main__":
    main() 