#!/bin/bash

# Exit on error
set -e

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

echo -e "${GREEN}=== Setting up Jupyter environment for Hack Tractor ===${NC}"

# Check if virtual environment exists
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}Error: Virtual environment not found at $VENV_DIR${NC}"
    echo "Please run setup_venv.sh first to create the virtual environment."
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source $VENV_DIR/bin/activate

# Install Jupyter and dependencies
echo -e "${YELLOW}Installing Jupyter and dependencies...${NC}"
pip install jupyter ipykernel ipywidgets nbformat

# Create a kernel for the Hack Tractor project
echo -e "${YELLOW}Creating a Jupyter kernel for Hack Tractor...${NC}"
python -m ipykernel install --user --name=hack-tractor --display-name="Hack Tractor"

# Create notebooks directory if it doesn't exist
mkdir -p notebooks

echo -e "${GREEN}Jupyter environment setup complete!${NC}"
echo -e "To start Jupyter Notebook, run: ${YELLOW}jupyter notebook${NC}"
echo -e "To start Jupyter Lab, run: ${YELLOW}jupyter lab${NC}"
echo -e "Make sure to select the 'Hack Tractor' kernel when creating new notebooks."
echo -e "Example notebooks are available in the 'notebooks' directory."
