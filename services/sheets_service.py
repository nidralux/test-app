import logging
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    """Service for Google Sheets operations."""
    
    # Scopes required for the Google Sheets API
    _SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    
    def __init__(self, spreadsheet_id, keyfile_path):
        """
        Initialize Google Sheets service.
        
        Args:
            spreadsheet_id (str): Google Sheets spreadsheet ID
            keyfile_path (str): Path to service account JSON key file
        """
        self.spreadsheet_id = spreadsheet_id
        self.keyfile_path = keyfile_path
        self.service = None
        
        self._authenticate()
        
    def _authenticate(self):
        """Authenticate with Google Sheets API."""
        try:
            creds = Credentials.from_service_account_file(
                self.keyfile_path, 
                scopes=self._SCOPES
            )
            self.service = build("sheets", "v4", credentials=creds)
            logger.info("Successfully authenticated with Google Sheets")
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Sheets: {e}")
            raise
    
    def upload_test_cases(self, test_cases, quality_scores, ticket_key):
        """
        Upload test cases to Google Sheets.
        
        Args:
            test_cases (List[Dict]): List of parsed test cases
            quality_scores (List[Dict]): List of quality scores corresponding to test cases
            ticket_key (str): Jira ticket key
            
        Returns:
            bool: True if upload succeeded, False otherwise
        """
        try:
            # Get current timestamp for the upload
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Prepare formatted values
            formatted_values = []
            
            # Check if sheet needs headers (first time use)
            sheets_data = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range="Sheet1!A1:K1"
            ).execute()
            
            values = sheets_data.get('values', [])
            headers_needed = not values or len(values[0]) < 11 or values[0][0] != "Timestamp"
            
            # If headers are needed, add them to the formatted values
            # AND upload them separately first
            if headers_needed:
                headers = [
                    "Timestamp", "Ticket", "Test Case ID", "Section/Module", 
                    "Preconditions", "Steps", "Expected Result", "Input Data", 
                    "Notes", "Quality Score"
                ]
                
                # Write headers separately
                header_body = {
                    "values": [headers]
                }
                
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range="Sheet1!A1",
                    valueInputOption="RAW",
                    body=header_body
                ).execute()
                
                logger.info("Added headers to spreadsheet")
            
            # Add test cases to formatted values with quality scores (no headers)
            for test_case, score_info in zip(test_cases, quality_scores):
                improvement_areas = ', '.join(score_info['areas_for_improvement']) if score_info['areas_for_improvement'] else 'None'
                
                formatted_values.append([
                    timestamp,
                    ticket_key,
                    test_case['id'],  # Updated field name
                    test_case['section'],
                    test_case['preconditions'],
                    test_case['steps'],
                    test_case['expected_result'],
                    test_case['input_data'],
                    test_case['notes'],
                    f"{score_info['score']}%"
                ])
            
            # Prepare the request body for test cases only
            body = {
                "values": formatted_values
            }
            
            # Use append to add rows to the end of existing data (after headers)
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range="Sheet1!A2",  # Start from A2 to append after headers
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body=body
            ).execute()
            
            updated_range = result.get('updates', {}).get('updatedRange', 'unknown')
            logger.info(f"Added {len(test_cases)} rows to {updated_range} in spreadsheet for ticket {ticket_key}")
            
            return True
            
        except Exception as e:
            logger.exception(f"Error uploading test cases to Google Sheets: {str(e)}")
            return False
    
    def create_ticket_sheet(self, ticket_key):
        """
        Create a new sheet for a specific ticket if it doesn't exist.
        
        Args:
            ticket_key (str): The Jira ticket key
            
        Returns:
            bool: True if created or already exists, False on error
        """
        try:
            # Get all existing sheets
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            sheet_titles = [sheet['properties']['title'] for sheet in sheet_metadata['sheets']]
            
            # If sheet already exists, we're done
            if ticket_key in sheet_titles:
                logger.info(f"Sheet for ticket {ticket_key} already exists")
                return True
            
            # Create a new sheet for this ticket
            body = {
                'requests': [
                    {
                        'addSheet': {
                            'properties': {
                                'title': ticket_key
                            }
                        }
                    }
                ]
            }
            
            result = self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            logger.info(f"Created new sheet for ticket {ticket_key}")
            return True
            
        except HttpError as e:
            logger.error(f"Error creating sheet for ticket {ticket_key}: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error creating sheet: {e}")
            return False
    
    def upload_test_cases_to_ticket_sheet(self, test_cases, quality_scores, ticket_key):
        """
        Upload test cases to a dedicated sheet for the ticket.
        
        Args:
            test_cases (list): List of test case dictionaries
            quality_scores (list): List of quality score dictionaries
            ticket_key (str): The Jira ticket key
            
        Returns:
            bool: True if successful, False otherwise
        """
        # First ensure the sheet exists
        if not self.create_ticket_sheet(ticket_key):
            return False
        
        try:
            # Add headers to the sheet
            headers = [
                "Timestamp", "Test Case ID", "Section/Module", 
                "Preconditions", "Steps", "Expected Result", "Input Data", 
                "Notes", "Quality Score"
            ]
            
            # Get current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Clear existing content
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=f"{ticket_key}!A1:Z1000"
            ).execute()
            
            # Create formatted data
            formatted_values = [headers]
            
            # Add test cases
            for test_case, score_info in zip(test_cases, quality_scores):
                
                
                formatted_values.append([
                    timestamp,
                    test_case['test_case_id'],
                    test_case['section'],
                    test_case['preconditions'],
                    test_case['steps'],
                    test_case['expected_result'],
                    test_case['input_data'],
                    test_case['notes'],
                    f"{score_info['score']}%",
                    improvement_areas
                ])
            
            # Write data to the sheet
            body = {
                "values": formatted_values
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{ticket_key}!A1",
                valueInputOption="RAW",
                body=body
            ).execute()
            
            logger.info(f"Updated sheet for ticket {ticket_key} with {len(test_cases)} test cases")
            return True
            
        except HttpError as e:
            logger.error(f"Error writing to ticket sheet: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error writing to ticket sheet: {e}")
            return False
    
    def get_spreadsheet_url(self) -> str:
        """
        Get the URL for the Google Spreadsheet.
        
        Returns:
            str: URL to access the spreadsheet in a browser
        """
        return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/edit"

    def add_test_cases_batch(self, ticket_key, test_cases):
        """Add multiple test cases in a single batch operation."""
        try:
            # Format all test cases as rows
            rows = []
            for tc in test_cases:
                row = [
                    ticket_key,
                    tc.get('id', ''),
                    tc.get('section', ''),
                    tc.get('preconditions', ''),
                    tc.get('steps', ''),
                    tc.get('expected_result', ''),
                    tc.get('input', ''),
                    tc.get('notes', ''),
                    tc.get('status', 'Not Run'),  # Default status
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
                rows.append(row)
            
            # Use a single batch request to add all rows
            body = {
                'values': rows
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range='Sheet1!A2',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"Added {len(rows)} rows to {result.get('updates', {}).get('updatedRange')} in spreadsheet for ticket {ticket_key}")
            return True
        except Exception as e:
            logger.exception(f"Error adding test cases: {str(e)}")
            return False