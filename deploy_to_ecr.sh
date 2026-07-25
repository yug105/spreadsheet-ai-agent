#!/bin/bash

# Deploy Docker image to Amazon ECR from the project root directory
# This script builds the Docker image and pushes it to ECR

set -e

# Configuration
AWS_REGION="us-east-1"
ECR_REPOSITORY_NAME="sheetsai-backend"
IMAGE_TAG="latest"

echo "🚀 Deploying Docker image to Amazon ECR (Fixed Platform)"
echo "=========================================================="

# Get AWS account ID and trim any whitespace
echo "📋 Getting AWS account ID..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text | tr -d '[:space:]')
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "❌ Failed to get AWS Account ID. Please check your AWS credentials."
    exit 1
fi
echo "✅ AWS Account ID: $AWS_ACCOUNT_ID"

# Create ECR repository if it doesn't exist
echo "📦 Creating ECR repository if it doesn't exist..."
aws ecr describe-repositories --repository-names $ECR_REPOSITORY_NAME --region $AWS_REGION 2>/dev/null || \
aws ecr create-repository --repository-name $ECR_REPOSITORY_NAME --region $AWS_REGION
echo "✅ ECR repository ready"

# Get ECR login token and login
echo "🔐 Getting ECR login token..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
echo "✅ ECR login successful"

# Set ECR repository URI
ECR_REPOSITORY_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY_NAME"

# Clean up any existing images to force fresh build
echo "🧹 Cleaning up existing images..."
docker rmi $ECR_REPOSITORY_NAME:$IMAGE_TAG 2>/dev/null || true
docker rmi $ECR_REPOSITORY_URI:$IMAGE_TAG 2>/dev/null || true

# Build Docker image from the project root with forced platform and no cache
echo "🔨 Building Docker image for AWS App Runner (no cache)..."
docker build --platform linux/amd64 --no-cache -t $ECR_REPOSITORY_NAME:$IMAGE_TAG .
echo "✅ Docker image built successfully"

# Tag the image for ECR
echo "🏷️  Tagging image for ECR..."
docker tag $ECR_REPOSITORY_NAME:$IMAGE_TAG $ECR_REPOSITORY_URI:$IMAGE_TAG
echo "✅ Image tagged for ECR"

# Push image to ECR
echo "📤 Pushing image to ECR..."
docker push $ECR_REPOSITORY_URI:$IMAGE_TAG
echo "✅ Image pushed to ECR successfully"

echo ""
echo "🎉 Deployment completed successfully!"
echo "====================================="
echo "Full Image URI: $ECR_REPOSITORY_URI:$IMAGE_TAG"
echo ""
echo "📋 Next Steps:"
echo "1. In AWS App Runner, choose 'Container image' as your source."
echo "2. Use the 'Full Image URI' above for the 'Image identifier'."
echo "3. Set port to 8080 and configure environment variables."
echo "4. Deploy the service!"
echo "" 