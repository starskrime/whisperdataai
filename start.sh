#!/bin/bash

echo "=========================================="
echo "WhisperData - AI Excel Chat Application"
echo "=========================================="
echo ""

# Color codes for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    echo "Please install Python 3.12 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Found Python version: $PYTHON_VERSION"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating new setup...${NC}"
    echo ""

    echo "Step 1: Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
    echo ""

    echo "Step 2: Activating virtual environment..."
    source venv/bin/activate
    echo -e "${GREEN}✓${NC} Virtual environment activated"
    echo ""

    echo "Step 3: Upgrading pip..."
    pip install --upgrade pip --quiet
    echo -e "${GREEN}✓${NC} Pip upgraded"
    echo ""

    echo "Step 4: Installing dependencies..."
    pip install -r requirements.txt --quiet
    echo -e "${GREEN}✓${NC} Dependencies installed"
    echo ""

    echo "Step 5: Running database migrations..."
    python manage.py makemigrations
    python manage.py migrate
    echo -e "${GREEN}✓${NC} Database setup complete"
    echo ""

    echo -e "${GREEN}=========================================="
    echo "Initial Setup Complete!"
    echo "==========================================${NC}"
    echo ""
else
    echo -e "${GREEN}Found existing installation.${NC}"
    echo ""

    echo "Activating virtual environment..."
    source venv/bin/activate
    echo -e "${GREEN}✓${NC} Virtual environment activated"
    echo ""

    # Check if requirements have changed
    echo "Checking for dependency updates..."
    pip install -r requirements.txt --quiet
    echo -e "${GREEN}✓${NC} Dependencies up to date"
    echo ""

    # Run migrations in case there are new ones
    echo "Checking for database updates..."
    python manage.py migrate
    echo -e "${GREEN}✓${NC} Database up to date"
    echo ""
fi

# Check for .env file and API key configuration
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ Warning: .env file not found${NC}"
    echo ""
    echo "WhisperData requires a .env file for configuration."
    echo ""
    read -p "Would you like to create .env from .env.example? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo -e "${GREEN}✓${NC} Created .env file from template"
            echo ""
            echo "Please edit .env and add your Anthropic API key:"
            echo "  1. Get your API key from: https://console.anthropic.com/"
            echo "  2. Open .env file and replace 'anthropic-token-here' with your actual key"
            echo ""
            read -p "Press Enter once you've added your API key to .env..."
            echo ""
        else
            echo -e "${RED}Error: .env.example not found${NC}"
            exit 1
        fi
    else
        echo ""
        echo "You can create .env manually by copying .env.example:"
        echo "  cp .env.example .env"
        echo ""
        echo "Then edit .env and add your Anthropic API key."
        echo ""
    fi
fi

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
    echo -e "${GREEN}✓${NC} Environment variables loaded"
    echo ""
fi

# Check AI provider and validate corresponding API key
AI_PROVIDER_VALUE=${AI_PROVIDER:-anthropic}

if [ "$AI_PROVIDER_VALUE" = "anthropic" ]; then
    # Check Anthropic API key
    if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "anthropic-token-here" ]; then
        echo -e "${YELLOW}⚠ Warning: ANTHROPIC_API_KEY not configured properly${NC}"
        echo ""
        echo "Your Anthropic API key is either missing or using the default placeholder."
        echo ""
        read -p "Would you like to set your Anthropic API key now? (y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            read -p "Enter your Anthropic API key: " api_key
            if [ -f ".env" ]; then
                # Update .env file
                if grep -q "ANTHROPIC_API_KEY=" .env; then
                    sed -i '' "s/ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=$api_key/" .env
                else
                    echo "ANTHROPIC_API_KEY=$api_key" >> .env
                fi
                export ANTHROPIC_API_KEY="$api_key"
                echo -e "${GREEN}✓${NC} Anthropic API key saved to .env file"
                echo ""
            else
                export ANTHROPIC_API_KEY="$api_key"
                echo -e "${GREEN}✓${NC} Anthropic API key set for this session"
                echo ""
                echo "Note: Key is only set for this session. Create a .env file to persist it."
                echo ""
            fi
        else
            echo ""
            echo -e "${YELLOW}Warning: Application will not work without a valid Anthropic API key.${NC}"
            echo ""
        fi
    fi
elif [ "$AI_PROVIDER_VALUE" = "openai" ]; then
    # Check OpenAI API key
    if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "openai-token-here" ]; then
        echo -e "${YELLOW}⚠ Warning: OPENAI_API_KEY not configured properly${NC}"
        echo ""
        echo "Your OpenAI API key is either missing or using the default placeholder."
        echo ""
        read -p "Would you like to set your OpenAI API key now? (y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            read -p "Enter your OpenAI API key: " api_key
            if [ -f ".env" ]; then
                # Update .env file
                if grep -q "OPENAI_API_KEY=" .env; then
                    sed -i '' "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$api_key/" .env
                else
                    echo "OPENAI_API_KEY=$api_key" >> .env
                fi
                export OPENAI_API_KEY="$api_key"
                echo -e "${GREEN}✓${NC} OpenAI API key saved to .env file"
                echo ""
            else
                export OPENAI_API_KEY="$api_key"
                echo -e "${GREEN}✓${NC} OpenAI API key set for this session"
                echo ""
                echo "Note: Key is only set for this session. Create a .env file to persist it."
                echo ""
            fi
        else
            echo ""
            echo -e "${YELLOW}Warning: Application will not work without a valid OpenAI API key.${NC}"
            echo ""
        fi
    fi
else
    echo -e "${YELLOW}⚠ Warning: Unknown AI provider '$AI_PROVIDER_VALUE'${NC}"
    echo "Valid providers are 'anthropic' or 'openai'."
    echo ""
fi

# Start the server
echo "=========================================="
echo "Starting Development Server..."
echo "=========================================="
echo ""
echo -e "Server will be available at: ${GREEN}http://127.0.0.1:8000${NC}"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

python manage.py runserver
