import json
import boto3

def lambda_handler(event, context):
    """Lambda handler that proxies requests to Bedrock Agent"""
    
    try:
        # Extract payload from API Gateway event
        if 'body' in event:
            if event.get('isBase64Encoded', False):
                import base64
                body = base64.b64decode(event['body']).decode('utf-8')
            else:
                body = event['body']
            
            if body:
                payload = json.loads(body)
            else:
                payload = {}
        else:
            payload = event.get('queryStringParameters', {}) or {}
        
        # Extract user input
        user_input = payload.get('input', payload.get('query', payload.get('prompt', '')))
        session_id = payload.get('session_id', context.aws_request_id)
        
        if not user_input:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing "input" or "query" in request body',
                    'status': 'error'
                })
            }
        
        # Initialize client once at top
        agentcore_client = boto3.client('bedrock-agentcore', region_name='ap-southeast-2')

        # Inside handler:
        response = agentcore_client.invoke_agent_runtime(
            agentRuntimeArn='arn:aws:bedrock-agentcore:ap-southeast-2:683627574351:runtime/app-hac9w07iO1',
            runtimeSessionId=session_id,  # can use context.aws_request_id or random
            payload=json.dumps({
                "prompt": user_input}
            ),
            qualifier="DEFAULT"
        )

        
        # Parse the streaming response from flow
        response_body = response['response'].read()
        response_data = json.loads(response_body)

        # Return the Agent's response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")  # CloudWatch logs
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e),
                'status': 'error'
            })
        }