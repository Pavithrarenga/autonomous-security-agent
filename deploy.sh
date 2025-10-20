#!/bin/bash

# Build and deploy the Lambda function with API Gateway
echo "Building and deploying vulnerability scanner agent..."

# Build
sam build

# Deploy
sam deploy --guided --stack-name asa-stack

echo "Deployment complete!"
echo "Your API endpoint will be displayed in the outputs."