#!/bin/bash

# Study Tracker Application Launcher

echo ""
echo "================================"
echo "  Study Tracker - Starting..."
echo "================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.9+ from python.org"
    exit 1
fi

# Check if required packages are installed
python3 -c "import PIL" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required packages..."
    pip3 install -r requirements.txt
fi

# Run the app
python3 study_tracker.py
