#!/bin/bash

# Exit on error
set -e

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

echo -e "${GREEN}=== Setting up Hack Tractor development environment ===${NC}"

# Define the virtual environment directory
VENV_DIR="venv"
PROJECT_ROOT=$(pwd)

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
  echo -e "${YELLOW}Creating virtual environment in $VENV_DIR...${NC}"
  python3 -m venv $VENV_DIR
else
  echo -e "${YELLOW}Virtual environment already exists in $VENV_DIR${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source $VENV_DIR/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
  echo -e "${YELLOW}Installing dependencies from requirements.txt...${NC}"
  pip install -r requirements.txt
else
  echo -e "${RED}Warning: requirements.txt not found.${NC}"
  exit 1
fi

# Ensure mypy and other development tools are installed
echo -e "${YELLOW}Installing development tools...${NC}"
pip install mypy flake8 black isort pytest

# Create VS Code settings directory if it doesn't exist
mkdir -p .vscode

# Create VS Code settings to use the virtual environment
echo -e "${YELLOW}Configuring VS Code settings...${NC}"
cat > .vscode/settings.json << EOF
{
    "python.defaultInterpreterPath": "${PROJECT_ROOT}/${VENV_DIR}/bin/python",
    "python.linting.enabled": true,
    "python.linting.mypyEnabled": true,
    "python.linting.flake8Enabled": true,
    "mypy.dmypyExecutable": "${PROJECT_ROOT}/${VENV_DIR}/bin/dmypy",
    "mypy.runUsingActiveInterpreter": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "python.linting.pylintEnabled": false,
    "python.analysis.typeCheckingMode": "basic",
    "python.analysis.extraPaths": [
        "${PROJECT_ROOT}"
    ],
    "python.envFile": "${PROJECT_ROOT}/.env",
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.nosetestsEnabled": false,
    "python.testing.pytestArgs": [
        "tests"
    ]
}
EOF

# Create a .env file for environment variables
if [ ! -f ".env" ]; then
  echo -e "${YELLOW}Creating .env file...${NC}"
  cat > .env << EOF
# Environment variables for Hack Tractor project
PYTHONPATH=${PROJECT_ROOT}
EOF
fi

echo -e "${GREEN}=== Development environment setup complete! ===${NC}"
echo -e "To activate the virtual environment, run: ${YELLOW}source $VENV_DIR/bin/activate${NC}"
echo -e "Restart VS Code or reload the window to apply the settings."
echo
echo -e "${YELLOW}Installed packages:${NC}"
pip list
