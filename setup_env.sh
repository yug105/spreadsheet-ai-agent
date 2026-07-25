#!/bin/bash

# Enhanced Sheets AI Backend Environment Setup Script

echo "🔧 Enhanced Sheets AI Backend Environment Setup"
echo "=============================================="

# Check if .env file exists
if [ -f ".env" ]; then
    echo "✅ .env file already exists"
    echo "📋 Current environment variables:"
    cat .env
else
    echo "📝 Creating .env file from template..."
    cp environment.example .env
    echo "✅ .env file created from template"
    echo "⚠️  Please edit .env file with your actual values"
fi

echo ""
echo "🚀 Environment Variables for Different Deployments:"
echo ""

echo "📦 For Local Development:"
echo "export OPENROUTER_API_KEY='your_api_key_here'"
echo "export DEFAULT_SPREADSHEET_ID='your_spreadsheet_id'"
echo "export LOG_LEVEL='DEBUG'"
echo ""

echo "🐳 For Docker Local Testing:"
echo "docker run -e OPENROUTER_API_KEY='your_api_key_here' \\"
echo "           -e DEFAULT_SPREADSHEET_ID='your_spreadsheet_id' \\"
echo "           -p 8080:8080 sheetsai-backend:latest"
echo ""

echo "☁️  For AWS App Runner:"
echo "Environment Variables to add in App Runner console:"
echo "- OPENROUTER_API_KEY: your_api_key_here"
echo "- DEFAULT_SPREADSHEET_ID: your_spreadsheet_id (optional)"
echo "- LOG_LEVEL: INFO (optional)"
echo "- MODEL_NAME: anthropic/claude-3.5-sonnet (optional)"
echo "- MAX_TURNS: 8 (optional)"
echo ""

echo "🔐 For AWS Secrets Manager:"
echo "1. Store your API key in AWS Secrets Manager"
echo "2. Reference it in App Runner as:"
echo "   - Secret name: sheetsai/openrouter-api-key"
echo "   - Environment variable: OPENROUTER_API_KEY"
echo ""

echo "📋 Required Environment Variables:"
echo "✅ OPENROUTER_API_KEY - Get from https://openrouter.ai/"
echo ""
echo "📋 Optional Environment Variables:"
echo "⚙️  DEFAULT_SPREADSHEET_ID - Default spreadsheet to use"
echo "⚙️  SERVICE_ACCOUNT_FILE - Google service account file (default: test_sheetsai.json)"
echo "⚙️  LOG_LEVEL - Logging level (default: INFO)"
echo "⚙️  MODEL_NAME - AI model to use (default: anthropic/claude-3.5-sonnet)"
echo "⚙️  MAX_TURNS - Maximum AI conversation turns (default: 8)"
echo ""

echo "🎯 Next Steps:"
echo "1. Get your OpenRouter API key from https://openrouter.ai/"
echo "2. Add it to your .env file or deployment environment"
echo "3. Test the application locally or deploy to AWS" 