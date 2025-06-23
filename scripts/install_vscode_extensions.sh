#!/bin/bash

# Script to install useful VS Code extensions for Python development

set -e  # Exit on error
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

echo -e "${GREEN}=== Installing VS Code Extensions for Python Development ===${NC}"

# Check if VS Code is installed
if ! command -v code &> /dev/null; then
    echo -e "${RED}Error: VS Code is not installed or not in PATH${NC}"
    echo "Please install VS Code first: https://code.visualstudio.com/download"
    exit 1
fi

# Function to install VS Code extension
install_extension() {
    local extension=$1
    local description=$2
    
    echo -e "${YELLOW}Installing: ${extension} - ${description}${NC}"
    code --install-extension "$extension" --force
    echo -e "${GREEN}✓ Installed: ${extension}${NC}"
}

# Core Python extensions
echo -e "\n${GREEN}=== Installing Core Python Extensions ===${NC}"
install_extension "ms-python.python" "Main Python extension with IntelliSense, linting, debugging, etc."
install_extension "ms-python.vscode-pylance" "Fast, feature-rich language server for Python"
install_extension "ms-python.debugpy" "Debug adapter for Python"

# Testing and linting
echo -e "\n${GREEN}=== Installing Testing & Linting Extensions ===${NC}"
install_extension "littlefoxteam.vscode-python-test-adapter" "Python test explorer"
install_extension "matangover.mypy" "MyPy type checking for Python"
install_extension "ms-python.flake8" "Flake8 linting for Python"

# Formatting
echo -e "\n${GREEN}=== Installing Formatting Extensions ===${NC}"
install_extension "ms-python.black-formatter" "Black formatter for Python"
install_extension "ms-python.isort" "Import organization for Python"
install_extension "njpwerner.autodocstring" "Python docstring generator"

# Productivity
echo -e "\n${GREEN}=== Installing Productivity Extensions ===${NC}"
install_extension "kevinrose.vsc-python-indent" "Python indentation"
install_extension "visualstudioexptteam.vscodeintellicode" "AI-assisted development"
install_extension "oderwat.indent-rainbow" "Makes indentation more readable"
install_extension "streetsidesoftware.code-spell-checker" "Spelling checker"
install_extension "aaron-bond.better-comments" "Better code comments"

# Jupyter support
echo -e "\n${GREEN}=== Installing Jupyter Extensions ===${NC}"
install_extension "ms-toolsai.jupyter" "Jupyter notebooks support"
install_extension "ms-toolsai.jupyter-keymap" "Jupyter keymaps"
install_extension "ms-toolsai.jupyter-renderers" "Jupyter renderers"

# Git integration
echo -e "\n${GREEN}=== Installing Git Extensions ===${NC}"
install_extension "mhutchie.git-graph" "Git Graph visualization"
install_extension "eamodio.gitlens" "GitLens - Git supercharged"

# Helpful UI enhancements
echo -e "\n${GREEN}=== Installing UI Enhancement Extensions ===${NC}"
install_extension "pkief.material-icon-theme" "Material Icon Theme"
install_extension "gruntfuggly.todo-tree" "Todo Tree for tracking TODOs"

echo -e "\n${GREEN}=== All extensions have been installed! ===${NC}"
echo -e "You may need to restart VS Code for all extensions to activate properly."
echo -e "Recommended workspace settings to add to your .vscode/settings.json:"
echo -e "${YELLOW}"
echo '{
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.nosetestsEnabled": false,
    "python.testing.pytestArgs": [
        "tests"
    ]
}'
echo -e "${NC}"

echo -e "${GREEN}Happy coding with your Hack Tractor project!${NC}"
