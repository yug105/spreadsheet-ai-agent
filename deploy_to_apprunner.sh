#!/bin/bash

# AWS App Runner Deployment Script
# This script helps deploy the Enhanced Sheets AI Backend to AWS App Runner

set -e

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
# Resolve the account id from the current credentials so nothing is hardcoded.
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}"
ECR_REPOSITORY_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/sheetsai-backend"
IMAGE_TAG="latest"
SERVICE_NAME="sheetsai-backend"
API_KEY="${OPENROUTER_API_KEY}"
DEFAULT_SPREADSHEET_ID="${DEFAULT_SPREADSHEET_ID:-your_spreadsheet_id_here}"

echo "🚀 Deploying Enhanced Sheets AI Backend to AWS App Runner"
echo "=========================================================="

# Step 1: Create Secrets Manager Secret
echo "🔐 Step 1: Creating AWS Secrets Manager Secret..."
SECRET_NAME="sheetsai/openrouter-api-key"

# Check if secret already exists
if aws secretsmanager describe-secret --secret-id "$SECRET_NAME" --region "$AWS_REGION" 2>/dev/null; then
    echo "✅ Secret already exists: $SECRET_NAME"
else
    echo "📝 Creating new secret: $SECRET_NAME"
    aws secretsmanager create-secret \
        --name "$SECRET_NAME" \
        --description "OpenRouter API Key for SheetsAI Backend" \
        --secret-string "{\"api_key\":\"$API_KEY\"}" \
        --region "$AWS_REGION"
    echo "✅ Secret created successfully"
fi

# Step 2: Create App Runner Service
echo ""
echo "☁️  Step 2: Creating App Runner Service..."

# Create service configuration
cat > apprunner-service.json << EOF
{
  "ServiceName": "$SERVICE_NAME",
  "SourceConfiguration": {
    "ImageRepository": {
      "ImageIdentifier": "$ECR_REPOSITORY_URI:$IMAGE_TAG",
      "ImageConfiguration": {
        "Port": "8080",
        "RuntimeEnvironmentVariables": [
          {
            "Name": "DEFAULT_SPREADSHEET_ID",
            "Value": "${DEFAULT_SPREADSHEET_ID}"
          },
          {
            "Name": "LOG_LEVEL",
            "Value": "INFO"
          },
          {
            "Name": "MODEL_NAME",
            "Value": "anthropic/claude-3.5-sonnet"
          },
          {
            "Name": "MAX_TURNS",
            "Value": "8"
          }
        ]
      },
      "ImageRepositoryType": "ECR"
    }
  },
  "InstanceConfiguration": {
    "Cpu": "1 vCPU",
    "Memory": "2 GB",
    "InstanceRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/AppRunnerECRAccessRole"
  },
  "HealthCheckConfiguration": {
    "Protocol": "HTTP",
    "Path": "/health",
    "Interval": 5,
    "Timeout": 2,
    "HealthyThreshold": 1,
    "UnhealthyThreshold": 5
  }
}
EOF

echo "📋 Service configuration created"

# Check if service already exists
if aws apprunner describe-service --service-name "$SERVICE_NAME" --region "$AWS_REGION" 2>/dev/null; then
    echo "🔄 Updating existing service: $SERVICE_NAME"
    aws apprunner update-service --service-name "$SERVICE_NAME" --region "$AWS_REGION" --cli-input-json file://apprunner-service.json
else
    echo "🆕 Creating new service: $SERVICE_NAME"
    aws apprunner create-service --region "$AWS_REGION" --cli-input-json file://apprunner-service.json
fi

echo ""
echo "⏳ Waiting for service to be ready..."
sleep 30

# Step 3: Get service URL
echo ""
echo "🌐 Step 3: Getting service URL..."
SERVICE_URL=$(aws apprunner describe-service --service-name "$SERVICE_NAME" --region "$AWS_REGION" --query 'Service.ServiceUrl' --output text)
echo "✅ Service URL: $SERVICE_URL"

# Step 4: Test the deployment
echo ""
echo "🧪 Step 4: Testing deployment..."
echo "Testing health endpoint..."
curl -s "$SERVICE_URL/health" | python3 -m json.tool

echo ""
echo "🎉 Deployment completed successfully!"
echo "=================================="
echo "Service Name: $SERVICE_NAME"
echo "Service URL: $SERVICE_URL"
echo "Health Check: $SERVICE_URL/health"
echo ""
echo "📋 Environment Variables:"
echo "- OPENROUTER_API_KEY: [Stored in Secrets Manager]"
echo "- DEFAULT_SPREADSHEET_ID: ${DEFAULT_SPREADSHEET_ID}"
echo "- LOG_LEVEL: INFO"
echo "- MODEL_NAME: anthropic/claude-3.5-sonnet"
echo "- MAX_TURNS: 8"
echo ""
echo "🔗 Next Steps:"
echo "1. Test the API endpoint: $SERVICE_URL"
echo "2. Test a query: POST $SERVICE_URL/api/process_query"
echo "3. Monitor logs in AWS App Runner console"
echo "4. Set up custom domain if needed"

# Clean up
rm -f apprunner-service.json 