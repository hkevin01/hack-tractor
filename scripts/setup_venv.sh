#!/bin/bash

# Exit on error
set -e

echo "Setting up Hack Tractor development environment..."

# Define the virtual environment directory
VENV_DIR="venv"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment in $VENV_DIR..."
  python3 -m venv $VENV_DIR
else
  echo "Virtual environment already exists in $VENV_DIR"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
  echo "Installing dependencies from requirements.txt..."
  pip install -r requirements.txt
else
  echo "Warning: requirements.txt not found. No packages installed."
fi

# Install development dependencies
echo "Installing development dependencies..."
pip install pytest flake8 black isort mypy

# Create convenience scripts if needed
echo "Creating convenience scripts..."
mkdir -p .vscode 2>/dev/null || true

# Print success message
echo "Setup complete! Virtual environment is ready."
echo "To activate the virtual environment, run:"
echo "source $VENV_DIR/bin/activate"

# List installed packages
echo "Installed packages:"
pip list
