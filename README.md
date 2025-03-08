# Test Case Generator

An automated webhook application that generates comprehensive test cases when Jira tickets transition to "Ready for QA" status. The application uses LLMs (Large Language Models) to generate test cases based on ticket descriptions, following ISTQB standards.

## Features

- **Automated Test Case Generation**: Automatically creates detailed test cases when tickets enter QA
- **Jira Integration**: Responds to Jira webhook events and adds comments to tickets
- **Google Sheets Integration**: Stores generated test cases in a structured format
- **LLM-Powered**: Uses the powerful Llama 3.3 model for high-quality test case generation
- **Robust Error Handling**: Includes retry logic, input validation, and comprehensive logging
- **Security Features**: Optional webhook signature validation

## System Requirements

- Python 3.8 or higher
- Access to Jira instance with webhook configuration rights
- Google Workspace account with Google Sheets
- Together AI account for API access

## Setup and Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd test-case-generator
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the template configuration file and edit it with your credentials:

```bash
cp .env.template .env
```

Edit the `.env` file with your:
- Jira credentials and URL
- Together AI API key
- Google Sheets ID and service account key path

### 5. Set Up Google Sheets API Access

1. Create a project in the [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Google Sheets API
3. Create a service account and download the JSON key file
4. Share your Google Sheet with the service account email address

### 6. Configure Jira Webhook

1. In your Jira instance, go to System Settings > WebHooks
2. Create a new webhook pointing to your server's `/jira-webhook` endpoint
3. Configure the webhook to trigger on "Issue Updated" events
4. Optional: Set up signature validation for enhanced security

## Running the Application

### Local Development

```bash
python app.py
```

### Production Deployment

For production, we recommend using a WSGI server like Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Consider using a process manager like Supervisor or systemd to ensure the application stays running.

## Project Maintenance

### Cleaning Up Temporary Files

The project includes a cleanup script to remove temporary files:

```bash
./clean.sh
```

To also remove log files:

```bash
./clean.sh --logs
```

### Testing Webhook Integration

To test the webhook integration without actually moving tickets in Jira:

```bash
./test_webhook.sh
```

You can also use the built-in test endpoints:
- `/webhook-test` - Simple endpoint to verify webhook connectivity
- `/test-qa-transition/<ticket-key>` - Simulate a ticket transition to Ready for QA

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| DEBUG | Enable debug mode | False |
| HOST | Host to bind server | 0.0.0.0 |
| PORT | Port to listen on | 5000 |
| JIRA_URL | Jira instance URL | None |
| JIRA_USERNAME | Jira username | None |
| JIRA_API_TOKEN | Jira API token | None |
| TOGETHER_API_KEY | Together AI API key | None |
| TOGETHER_MODEL_ID | LLM model ID | meta-llama/Llama-3.3-70B-Instruct-Turbo-Free |
| SPREADSHEET_ID | Google Spreadsheet ID | None |
| JSON_KEYFILE_PATH | Path to Google service account JSON | None |
| API_TIMEOUT | API request timeout in seconds | 30 |
| API_MAX_RETRIES | Maximum retry attempts for API calls | 3 |
| WEBHOOK_SECRET_TOKEN | Secret for webhook signature validation | None |

## Workflow

1. Jira webhook triggers when a ticket transitions to "Ready for QA" status
2. Application retrieves ticket information from Jira API
3. LLM generates comprehensive test cases based on ticket description
4. Test cases are structured and stored in Google Sheets
5. A comment with a link to the test cases is added to the Jira ticket

## Troubleshooting

Check the `webhook.log` file for detailed logs. Common issues include:

- **Missing Configuration**: Ensure all required environment variables are set
- **Authentication Errors**: Verify API keys and credentials
- **Network Issues**: Check connectivity to Jira, Together AI, and Google APIs
- **Webhook Configuration**: Confirm the Jira webhook is properly configured

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE) 