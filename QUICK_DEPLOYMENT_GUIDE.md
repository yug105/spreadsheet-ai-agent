# 🚀 Quick ECR Deployment Guide

## ✅ Files Created
- `Dockerfile` - Optimized for FastAPI with layer caching
- `.dockerignore` - Clean build context
- `deploy_to_ecr.sh` - Automated ECR deployment script

## 🚀 Deployment Steps

### 1. Configure AWS (if needed)
```bash
aws configure
```

### 2. Deploy to ECR
```bash
cd src
./deploy_to_ecr.sh
```

### 3. Expected Output
```
✅ Docker image pushed to: [ACCOUNT_ID].dkr.ecr.us-east-1.amazonaws.com/sheetsai-backend:latest
Use this URI for AWS App Runner custom container deployment.
```

### 4. Configure App Runner
1. Go to AWS App Runner console
2. Select your service → Configuration → Edit
3. Choose **"Container image"** as deployment method
4. Use the ECR URI from step 3
5. Set **Port** to `8080`
6. Add environment variables:
   ```
   OPENROUTER_API_KEY=your-api-key
   PORT=8080
   ```

## 🎯 Key Benefits
- ✅ **Layer caching** - Faster builds
- ✅ **Clean context** - Smaller images
- ✅ **Monorepo friendly** - Works with src/ structure
- ✅ **Predictable deployments** - No App Runner source detection issues

## 🔧 Architecture Notes
- All app code copied to `/app` in container
- `app.py` exposes FastAPI `app` instance
- Uvicorn serves on port 8080
- ECR handles image storage and versioning 