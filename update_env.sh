#!/bin/bash

# Enhanced Sheets AI Backend Environment Update Script

echo "🔧 Enhanced Sheets AI Backend Environment Update"
echo "==============================================="

# Function to prompt for API key
get_api_key() {
    echo ""
    echo "🔑 Please enter your OpenRouter API key:"
    echo "   Get it from: https://openrouter.ai/"
    echo "   (Press Enter to skip if you don't have one yet)"
    read -p "OpenRouter API Key: " api_key
    
    if [ -n "$api_key" ]; then
        echo "✅ API key provided"
        return 0
    else
        echo "⚠️  No API key provided - AI functionality will be disabled"
        return 1
    fi
}

# Function to prompt for spreadsheet ID
get_spreadsheet_id() {
    echo ""
    echo "📊 Please enter your Google Spreadsheet ID:"
    echo "   Format: your_spreadsheet_id_here"
    echo "   (Press Enter to use default)"
    read -p "Spreadsheet ID: " spreadsheet_id
    
    if [ -n "$spreadsheet_id" ]; then
        echo "✅ Spreadsheet ID provided: $spreadsheet_id"
        return 0
    else
        echo "✅ Using default spreadsheet ID"
        spreadsheet_id="your_spreadsheet_id_here"
        return 1
    fi
}

# Get user input
get_api_key
api_key_provided=$?

get_spreadsheet_id
spreadsheet_id_provided=$?

# Create environment variables for different deployment methods
echo ""
echo "📋 Environment Variables for Deployment:"
echo "======================================="

echo ""
echo "🐳 For Docker Local Testing:"
echo "docker run \\"
if [ $api_key_provided -eq 0 ]; then
    echo "  -e OPENROUTER_API_KEY='$api_key' \\"
fi
if [ $spreadsheet_id_provided -eq 0 ]; then
    echo "  -e DEFAULT_SPREADSHEET_ID='$spreadsheet_id' \\"
fi
echo "  -p 8080:8080 sheetsai-backend:latest"

echo ""
echo "☁️  For AWS App Runner Environment Variables:"
if [ $api_key_provided -eq 0 ]; then
    echo "OPENROUTER_API_KEY = $api_key"
fi
if [ $spreadsheet_id_provided -eq 0 ]; then
    echo "DEFAULT_SPREADSHEET_ID = $spreadsheet_id"
fi
echo "LOG_LEVEL = INFO"
echo "MODEL_NAME = anthropic/claude-3.5-sonnet"
echo "MAX_TURNS = 8"

echo ""
echo "🔐 For AWS Secrets Manager:"
if [ $api_key_provided -eq 0 ]; then
    echo "Secret Name: sheetsai/openrouter-api-key"
    echo "Secret Value: $api_key"
    echo "Environment Variable: OPENROUTER_API_KEY"
fi

echo ""
echo "📦 For Local Development (.env file):"
echo "OPENROUTER_API_KEY=$api_key"
if [ $spreadsheet_id_provided -eq 0 ]; then
    echo "DEFAULT_SPREADSHEET_ID=$spreadsheet_id"
fi
echo "LOG_LEVEL=INFO"
echo "MODEL_NAME=anthropic/claude-3.5-sonnet"
echo "MAX_TURNS=8"

echo ""
echo "🎯 Next Steps:"
echo "1. Copy the appropriate environment variables above"
echo "2. Add them to your deployment platform"
echo "3. Test the application"
echo ""
echo "💡 Tip: For security, use AWS Secrets Manager for production deployments" 