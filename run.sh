#!/bin/bash

set -e

VENV_DIR="venv"
PYTHON_CMD="python3"

if ! command -v $PYTHON_CMD &> /dev/null; then
    PYTHON_CMD="python"
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv $VENV_DIR
fi

echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Installing Playwright browsers..."
playwright install chromium

echo "Starting server on http://localhost:8000..."
uvicorn main:app --host localhost --port 8000 --reload
