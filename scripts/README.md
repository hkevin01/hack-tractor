# Scripts

This directory contains utility scripts for the Hack Tractor project.

## Available Scripts

### `setup_venv.sh`
Sets up a Python virtual environment and installs all required dependencies.

#### Usage:
```bash
# From the project root directory
bash scripts/setup_venv.sh
```

#### What it does:
1. Creates a virtual environment named "venv" in the project root
2. Activates the virtual environment
3. Upgrades pip to the latest version
4. Installs all dependencies from requirements.txt
5. Installs development tools (pytest, flake8, black, etc.)

## Adding New Scripts

When adding new scripts to this directory, please:
1. Make them executable (`chmod +x script_name.sh`)
2. Document them in this README
3. Use the bash shebang (`#!/bin/bash`) at the beginning of each script
4. Include error handling and helpful output messages
