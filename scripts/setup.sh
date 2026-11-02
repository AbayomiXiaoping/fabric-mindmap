#!/usr/bin/env bash
# ==============================================================================
# Fabric Lakehouse Intelligence Explorer — Setup Script
# Configures Extension, Webview UI, and Python Runtime Environment
# ==============================================================================

set -e

# ANSI Colors
BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
RESET="\033[0m"

echo -e "${BOLD}${BLUE}======================================================${RESET}"
echo -e "${BOLD}${BLUE}  Fabric Lakehouse Intelligence Explorer — Setup     ${RESET}"
echo -e "${BOLD}${BLUE}======================================================${RESET}\n"

# 1. Check prerequisites
echo -e "${BOLD}[1/4] Checking prerequisites...${RESET}"

if ! command -v node >/dev/null 2>&1; then
    echo -e "${RED}Error: Node.js is not installed. Please install Node.js >= 18.0.0 (e.g. via 'brew install node').${RESET}"
    exit 1
fi
NODE_VERSION=$(node -v)
echo -e "  ✔ Node.js installed: ${GREEN}${NODE_VERSION}${RESET}"

if ! command -v npm >/dev/null 2>&1; then
    echo -e "${RED}Error: npm is not installed.${RESET}"
    exit 1
fi
echo -e "  ✔ npm installed: ${GREEN}$(npm -v)${RESET}"

PYTHON_BIN=""
for cmd in python3.11 python3.10 python3.12 python3.13 python3; do
    if command -v "$cmd" >/dev/null 2>&1; then
        PYTHON_BIN="$cmd"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo -e "${RED}Error: Python 3 is not installed. Please install Python >= 3.9.${RESET}"
    exit 1
fi
PYTHON_VER=$($PYTHON_BIN --version 2>&1)
echo -e "  ✔ Python installed: ${GREEN}${PYTHON_VER}${RESET} (${PYTHON_BIN})\n"

# 2. Build VS Code Extension
echo -e "${BOLD}[2/4] Setting up VS Code Extension (src/extension)...${RESET}"
cd src/extension
npm install --silent
npm run build
cd ../..
echo -e "  ✔ Extension compiled successfully (dist/extension.js)\n"

# 3. Build React Webview UI
echo -e "${BOLD}[3/4] Setting up React Webview UI (src/webview-ui)...${RESET}"
cd src/webview-ui
npm install --silent
npm run build
cd ../..
echo -e "  ✔ React Webview bundled successfully (dist/assets/)\n"

# 4. Setup Python Runtime & Virtualenv
echo -e "${BOLD}[4/4] Setting up Python Runtime (src/runtime)...${RESET}"
cd src/runtime
if [ ! -d ".venv" ]; then
    echo "  Creating virtual environment at src/runtime/.venv..."
    $PYTHON_BIN -m venv .venv
fi

# Activate virtualenv
source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -e ".[dev]" --quiet

echo -e "  ✔ Python dependencies installed in .venv"

# Run tests to verify setup
echo -e "  Running verification tests..."
pytest tests/unit/test_models.py --quiet
cd ../..

echo -e "\n${BOLD}${GREEN}======================================================${RESET}"
echo -e "${BOLD}${GREEN}  Setup Complete! Everything is ready to run.        ${RESET}"
echo -e "${BOLD}${GREEN}======================================================${RESET}\n"
echo -e "Next Steps:"
echo -e "  1. Open this workspace in VS Code:"
echo -e "       ${YELLOW}code .${RESET}"
echo -e "  2. Press ${BOLD}F5${RESET} to launch the Extension Development Host."
echo -e "  3. In the Lakehouse Intelligence sidebar, click ${BOLD}'Connect to Lakehouse'${RESET}."
echo -e "  4. For Copilot Agent, standard MCP tools are configured in ${YELLOW}.vscode/mcp.json${RESET}.\n"

