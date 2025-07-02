# AWS Elastic Beanstalk Deployment Guide

Quick deployment guide for the Company Research Agent using AWS Elastic Beanstalk Console and AWS Image Manager.

## Prerequisites

- AWS account with CLI configured: `aws configure`
- MongoDB database (MongoDB Atlas)
- Required API keys: TAVILY_API_KEY, OPENAI_API_KEY

## Deployment Steps

### 1. Prepare Application

1. Build and push Docker image to AWS ECR:
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   docker build -t company-research-agent .
   docker tag company-research-agent:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/company-research-agent:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/company-research-agent:latest
   ```

### 2. Deploy via Elastic Beanstalk Console

1. **Create Application:**

   - Go to AWS Elastic Beanstalk Console
   - Create New Application → "company-research-agent"
   - Platform: Docker
   - Upload `Dockerrun.aws.json`

2. **Configure Environment:**

   - Configuration → Software → Environment Variables:
     - `TAVILY_API_KEY=your_key`
     - `OPENAI_API_KEY=your_key`
     - `MONGODB_URI=your_mongodb_uri`

3. **Deploy:**
   - Upload application version
   - Deploy to environment

### 3. AWS Image Manager Integration

- Use AWS Systems Manager for image management
- Configure automated deployments through ECR triggers
- Set up image scanning and vulnerability assessments

## Post-Deployment

- Health check endpoint: `/`
- View logs: CloudWatch or EB Console
- Scale: Modify capacity in EB Console

## Key Files

- `Dockerrun.aws.json`: EB Docker configuration
- `.ebextensions/`: Environment configurations for WebSocket support and logging
