# Lambda + API Gateway Deployment

## Prerequisites
- AWS CLI configured
- SAM CLI installed (`pip install aws-sam-cli`)
- Docker installed (for SAM build)

## Deployment Steps

1. **Install SAM CLI** (if not installed):
   ```bash
   pip install aws-sam-cli
   ```

2. **Deploy using SAM**:
   ```bash
   sam build --template-file deploy.yaml --use-container
   sam deploy --template-file deploy.yaml --guided
   ```

3. **Follow the prompts**:
   - Stack name: `asa-stack`
   - AWS Region: Choose your preferred region
   - Confirm changes before deploy: Y
   - Allow SAM to create IAM roles: Y
   - Save parameters to samconfig.toml: Y

## API Usage

After deployment, you'll get an API endpoint URL. Use it like this:

```bash
curl -X POST https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/Prod/scan \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/username/repo"}'
```

## Test the API

Update `test_api.py` with your actual API URL and run:
```bash
python test_api.py
```

## Architecture

- **Lambda Function**: Wraps your agent entrypoint
- **API Gateway**: Provides HTTPS endpoint
- **S3 Bucket**: Stores processed repositories (fixed-repo)
- **IAM Roles**: Permissions for Bedrock and S3 access