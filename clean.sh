#!/bin/bash

# Clean up Python bytecode files
echo "Cleaning up Python bytecode files..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete

# Clean up logs if needed
echo "Cleaning up logs..."
if [ "$1" == "--logs" ]; then
    echo "Removing log files..."
    find . -type f -name "*.log" -delete
else
    echo "Logs preserved. Use --logs flag to remove log files."
fi

# Clean up other temporary files
echo "Cleaning up temporary files..."
find . -type f -name "*.swp" -delete
find . -type f -name "*.swo" -delete
find . -type f -name ".DS_Store" -delete

echo "Cleanup complete!" 