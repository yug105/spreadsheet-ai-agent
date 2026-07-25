# Environment Variables Setup

## 🔑 Required Environment Variables

### OPENROUTER_API_KEY
- **Required**: Yes (for AI functionality)
- **Source**: [OpenRouter](https://openrouter.ai/)
- **Purpose**: API key for accessing Claude 3.5 Sonnet model

## ⚙️ Optional Environment Variables

### DEFAULT_SPREADSHEET_ID
- **Default**: `your_spreadsheet_id_here`
- **Purpose**: Default Google Spreadsheet to analyze
- **Format**: Google Spreadsheet ID from URL

### SERVICE_ACCOUNT_FILE
- **Default**: `test_sheetsai.json`
- **Purpose**: Google Service Account credentials file
- **Note**: Already configured in your project

### LOG_LEVEL
- **Default**: `INFO`
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- **Purpose**: Application logging level

### MODEL_NAME
- **Default**: `anthropic/claude-3.5-sonnet`
- **Purpose**: AI model to use for analysis

### MAX_TURNS
- **Default**: `8`
- **Purpose**: Maximum AI conversation turns

## 🚀 Deployment Methods

### Local Development
```bash
export OPENROUTER_API_KEY="your_api_key_here"
export DEFAULT_SPREADSHEET_ID="your_spreadsheet_id"
python app.py
```

### Docker Local Testing
```bash
docker run -e OPENROUTER_API_KEY="your_api_key_here" \
           -e DEFAULT_SPREADSHEET_ID="your_spreadsheet_id" \
           -p 8080:8080 sheetsai-backend:latest
```

### AWS App Runner
Add these environment variables in the App Runner console:
- `OPENROUTER_API_KEY`: your_api_key_here
- `DEFAULT_SPREADSHEET_ID`: your_spreadsheet_id (optional)
- `LOG_LEVEL`: INFO (optional)
- `MODEL_NAME`: anthropic/claude-3.5-sonnet (optional)
- `MAX_TURNS`: 8 (optional)

### AWS Secrets Manager (Recommended for Production)
1. Store your API key in AWS Secrets Manager
2. Reference it in App Runner as:
   - Secret name: `sheetsai/openrouter-api-key`
   - Environment variable: `OPENROUTER_API_KEY`

## 🔧 Quick Setup Scripts

Run these scripts to help with setup:
```bash
# Setup environment guide
./setup_env.sh

# Update environment variables
./update_env.sh
```

## 📊 Current Configuration

Your current setup includes:
- ✅ Google Service Account: `test_sheetsai.json`
- ✅ Default Spreadsheet: `your_spreadsheet_id_here`
- ❌ OpenRouter API Key: **NEEDS TO BE ADDED**

## 🎯 Next Steps

1. **Get OpenRouter API Key**: Visit [OpenRouter](https://openrouter.ai/)
2. **Add Environment Variables**: Use one of the deployment methods above
3. **Test Application**: Verify AI functionality works
4. **Deploy to AWS**: Use the ECR image in App Runner 