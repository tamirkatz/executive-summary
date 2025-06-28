# AWS Elastic Beanstalk Deployment Guide

This guide explains how to deploy the Company Research Agent application to AWS Elastic Beanstalk.

## Prerequisites

1. **AWS CLI** installed and configured

   ```bash
   pip install awscli
   aws configure
   ```

2. **EB CLI** installed

   ```bash
   pip install awsebcli
   ```

3. **Docker** installed locally (for building/testing)

## Pre-Deployment Setup

### 1. Database Configuration

For production, you'll need to set up a MongoDB database. Options include:

- **AWS DocumentDB**: Managed MongoDB-compatible service
- **MongoDB Atlas**: Cloud MongoDB service
- **Self-managed MongoDB on EC2**: Not recommended for production

### 2. Environment Variables

Set these environment variables in your AWS Elastic Beanstalk environment:

**Required:**

- `TAVILY_API_KEY`: Your Tavily API key
- `OPENAI_API_KEY`: Your OpenAI API key
- `MONGODB_URI`: Your MongoDB connection string

**Optional:**

- `LOG_LEVEL`: Set to "INFO" or "DEBUG"
- `MAX_WORKERS`: Number of worker processes (default: 4)

## Deployment Steps

### Option 1: Using EB CLI (Recommended)

1. **Initialize EB application:**

   ```bash
   eb init
   ```

   - Choose your region
   - Select "Docker" as platform
   - Choose application name: `company-research-agent`

2. **Create environment:**

   ```bash
   eb create production
   ```

   - This will create a new environment named "production"

3. **Set environment variables:**

   ```bash
   eb setenv TAVILY_API_KEY=your_key_here
   eb setenv OPENAI_API_KEY=your_key_here
   eb setenv MONGODB_URI=your_mongodb_uri_here
   ```

4. **Deploy:**
   ```bash
   eb deploy
   ```

### Option 2: Using AWS Console

1. **Create Application:**

   - Go to AWS Elastic Beanstalk console
   - Click "Create Application"
   - Choose "Docker" platform
   - Upload your project as a ZIP file

2. **Configure Environment:**

   - In Configuration > Software, add environment variables
   - Set health check URL to `/`

3. **Deploy:**
   - Upload your application ZIP file
   - Wait for deployment to complete

## Post-Deployment Configuration

### 1. Health Checks

The application includes a health check endpoint at `/` that AWS will use to monitor your application.

### 2. Logging

Logs are configured to stream to CloudWatch. You can view them in:

- AWS Console > CloudWatch > Logs
- Using EB CLI: `eb logs`

### 3. Auto Scaling

The application is configured with:

- Minimum 1 instance
- Maximum 10 instances (configurable)
- Target CPU utilization: 70%

## Monitoring and Maintenance

### View Application Logs

```bash
eb logs
```

### Monitor Application Health

```bash
eb health
```

### Scale Your Application

```bash
eb scale 3  # Scale to 3 instances
```

### Update Application

```bash
eb deploy
```

## Troubleshooting

### Common Issues

1. **502 Bad Gateway**: Usually indicates the application isn't starting properly

   - Check logs: `eb logs`
   - Verify environment variables are set correctly

2. **WebSocket Connection Issues**:

   - Ensure nginx configuration is applied
   - Check that WebSocket endpoints are accessible

3. **MongoDB Connection Errors**:
   - Verify `MONGODB_URI` is correct
   - Check security groups allow connection to database

### Environment Variable Issues

List current environment variables:

```bash
eb printenv
```

Update environment variables:

```bash
eb setenv VARIABLE_NAME=new_value
```

## Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **Database Security**: Use VPC and security groups to restrict database access
3. **HTTPS**: Consider setting up SSL/TLS certificates
4. **IAM Roles**: Use least-privilege IAM roles

## Cost Optimization

1. **Instance Types**: Start with t3.small, scale up as needed
2. **Auto Scaling**: Configure appropriate scaling policies
3. **Scheduled Scaling**: Scale down during off-hours if applicable

## Backup and Recovery

1. **Database Backups**: Configure automated backups for your MongoDB
2. **Application Backups**: EB automatically keeps application versions
3. **Configuration Backups**: Export EB configuration regularly

## Files Included for Deployment

- `Dockerrun.aws.json`: Main deployment configuration
- `.ebextensions/01_environment.config`: Environment and health check settings
- `.ebextensions/02_logging.config`: Logging configuration
- `.ebextensions/03_nginx.config`: Nginx configuration for WebSocket support

## Support

For issues with deployment, check:

1. AWS Elastic Beanstalk documentation
2. Application logs in CloudWatch
3. EB CLI logs: `eb logs`
