#!/bin/bash

# Company Research Agent - AWS Elastic Beanstalk Deployment Script
# This script helps deploy the application to AWS Elastic Beanstalk

set -e

echo "🚀 Company Research Agent - AWS Deployment Script"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_requirements() {
    print_status "Checking requirements..."
    
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v eb &> /dev/null; then
        print_error "EB CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_warning "Docker is not installed. You may need it for local testing."
    fi
    
    print_status "Requirements check passed!"
}

# Initialize EB application
init_eb() {
    print_status "Initializing Elastic Beanstalk application..."
    
    if [ ! -f .elasticbeanstalk/config.yml ]; then
        print_status "Running eb init..."
        eb init --platform docker --region us-east-1
    else
        print_status "EB already initialized."
    fi
}

# Set environment variables
set_env_vars() {
    print_status "Setting environment variables..."
    
    # Check if required environment variables are provided
    if [ -z "$TAVILY_API_KEY" ]; then
        print_error "TAVILY_API_KEY environment variable is required"
        exit 1
    fi
    
    if [ -z "$OPENAI_API_KEY" ]; then
        print_error "OPENAI_API_KEY environment variable is required"
        exit 1
    fi
    
    if [ -z "$MONGODB_URI" ]; then
        print_warning "MONGODB_URI not provided. You may need to set it later."
    fi
    
    # Set environment variables
    eb setenv TAVILY_API_KEY="$TAVILY_API_KEY"
    eb setenv OPENAI_API_KEY="$OPENAI_API_KEY"
    
    if [ ! -z "$MONGODB_URI" ]; then
        eb setenv MONGODB_URI="$MONGODB_URI"
    fi
    
    print_status "Environment variables set successfully!"
}

# Deploy application
deploy_app() {
    print_status "Deploying application..."
    
    # Check if environment exists
    if ! eb list | grep -q "production"; then
        print_status "Creating production environment..."
        eb create production --timeout 20
    fi
    
    print_status "Deploying to production environment..."
    eb deploy production
    
    print_status "Deployment completed!"
}

# Show deployment info
show_info() {
    print_status "Deployment Information:"
    echo "======================="
    
    # Get application URL
    APP_URL=$(eb status | grep "CNAME" | awk '{print $2}')
    
    echo "Application URL: http://$APP_URL"
    echo "Health Check: http://$APP_URL/"
    echo "WebSocket: ws://$APP_URL/research/ws/{job_id}"
    
    print_status "To view logs: eb logs"
    print_status "To view health: eb health"
    print_status "To view environment: eb open"
}

# Main deployment function
main() {
    echo "Starting deployment process..."
    
    check_requirements
    init_eb
    set_env_vars
    deploy_app
    show_info
    
    print_status "🎉 Deployment completed successfully!"
    print_status "Your application should be available at the URL shown above."
}

# Help function
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -i, --init     Initialize EB application only"
    echo "  -d, --deploy   Deploy application only"
    echo "  -s, --status   Show deployment status"
    echo ""
    echo "Environment variables required:"
    echo "  TAVILY_API_KEY    Your Tavily API key"
    echo "  OPENAI_API_KEY    Your OpenAI API key"
    echo "  MONGODB_URI       Your MongoDB connection string (optional)"
    echo ""
    echo "Example:"
    echo "  export TAVILY_API_KEY='your_key'"
    echo "  export OPENAI_API_KEY='your_key'"
    echo "  export MONGODB_URI='mongodb://...'"
    echo "  $0"
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -i|--init)
        check_requirements
        init_eb
        ;;
    -d|--deploy)
        check_requirements
        deploy_app
        ;;
    -s|--status)
        eb status
        eb health
        ;;
    *)
        main
        ;;
esac 