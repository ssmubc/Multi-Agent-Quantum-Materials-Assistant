# AWS Authentication & Model Access Pattern

This document outlines the authentication and model access patterns used in the Empathetic Communication project, which can be replicated for other AWS projects with ML models and databases.

## 1. Authentication Flow

### Frontend → API Gateway → Lambda

```typescript
// CDK: API Gateway with Cognito authorization
const authorizer = new apigateway.CognitoUserPoolsAuthorizer(this, 'auth', {
  cognitoUserPools: [userPool]
});

// Lambda gets JWT token from API Gateway event
const token = event.headers.Authorization; // "Bearer eyJ..."
```

### Lambda → Bedrock Models

```python
# Lambda uses IAM role credentials (no API keys needed)
bedrock_client = boto3.client("bedrock-runtime", region_name=region)

# Region-specific model access with fallback
deployment_region = os.environ.get('AWS_REGION', 'us-east-1')
if 'nova' in model_id.lower():
    region = 'us-east-1'  # Nova models only in us-east-1
else:
    region = deployment_region
```

## 2. Secrets Management

### Database Credentials

```typescript
// CDK: Store DB credentials in Secrets Manager
const dbSecret = new secretsmanager.Secret(this, 'DBSecret', {
  generateSecretString: {
    secretStringTemplate: JSON.stringify({ username: 'admin' }),
    generateStringKey: 'password',
    excludeCharacters: '"@/\\'
  }
});
```

```python
# Lambda: Retrieve secrets
secrets_client = boto3.client('secretsmanager')
secret = secrets_client.get_secret_value(SecretId=secret_name)
db_creds = json.loads(secret['SecretString'])
```

### API Keys (if needed)

```python
# Store in Systems Manager Parameter Store
ssm_client = boto3.client('ssm')
api_key = ssm_client.get_parameter(
    Name='/myapp/api-key',
    WithDecryption=True
)['Parameter']['Value']
```

## 3. Multi-Region Model Strategy

```python
def get_bedrock_client(model_id, deployment_region):
    """Smart region selection for different models"""
    
    # Nova models: us-east-1 only
    if 'nova' in model_id.lower():
        region = 'us-east-1'
    # Claude models: multiple regions
    elif 'claude' in model_id.lower():
        region = deployment_region
    else:
        region = 'us-east-1'  # fallback
    
    return boto3.client("bedrock-runtime", region_name=region)

# Usage with fallback
try:
    client = get_bedrock_client(model_id, deployment_region)
    response = client.invoke_model(...)
except Exception as e:
    # Fallback to us-east-1
    fallback_client = boto3.client("bedrock-runtime", region_name="us-east-1")
    response = fallback_client.invoke_model(...)
```

## 4. IAM Permissions Pattern

```typescript
// CDK: Grant Lambda permissions
lambda.addToRolePolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream"
  ],
  resources: ["arn:aws:bedrock:*:*:foundation-model/*"]
}));

lambda.addToRolePolicy(new iam.PolicyStatement({
  actions: ["secretsmanager:GetSecretValue"],
  resources: [dbSecret.secretArn]
}));
```

## 5. Environment Variables

```typescript
// CDK: Pass config to Lambda
environment: {
  SM_DB_CREDENTIALS: dbSecret.secretName,
  RDS_PROXY_ENDPOINT: rdsProxy.endpoint,
  AWS_REGION: this.region,
  BEDROCK_MODEL_ID: "amazon.nova-pro-v1:0"
}
```

## 6. Smithy Authentication (for Nova Sonic)

```python
# Fix for smithy authentication issues
from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver

config = Config(
    endpoint_uri=f"https://bedrock-runtime.{region}.amazonaws.com",
    region=region,
    aws_credentials_identity_resolver=EnvironmentCredentialsResolver(),
)

client = BedrockRuntimeClient(config=config)
```

## 7. Database Connection Management

### RDS Proxy Configuration

```typescript
// CDK: RDS Proxy for connection pooling
const rdsProxy = new rds.DatabaseProxy(this, 'RDSProxy', {
  proxyTarget: rds.ProxyTarget.fromInstance(dbInstance),
  secrets: [dbSecret],
  vpc: vpc,
  requireTLS: true
});
```

### Centralized Connection Manager

```python
# voice_db_manager.py
class VoiceDBManager:
    def __init__(self):
        self.pool = None
        self.pool_lock = Lock()
    
    def get_connection(self):
        with self.pool_lock:
            if self.pool is None:
                self._initialize_pool()
            return self.pool.getconn()
    
    def return_connection(self, conn):
        self.pool.putconn(conn)
```

## 8. Complete Authentication Stack

### CDK Infrastructure

```typescript
// 1. Cognito User Pool
const userPool = new cognito.UserPool(this, 'UserPool', {
  signInAliases: { email: true },
  autoVerify: { email: true }
});

// 2. API Gateway with Cognito Auth
const api = new apigateway.RestApi(this, 'API', {
  defaultCorsPreflightOptions: {
    allowOrigins: apigateway.Cors.ALL_ORIGINS,
    allowMethods: apigateway.Cors.ALL_METHODS
  }
});

const authorizer = new apigateway.CognitoUserPoolsAuthorizer(this, 'Authorizer', {
  cognitoUserPools: [userPool]
});

// 3. Lambda with proper IAM roles
const lambda = new lambda.Function(this, 'Function', {
  // ... configuration
  environment: {
    SM_DB_CREDENTIALS: dbSecret.secretName,
    RDS_PROXY_ENDPOINT: rdsProxy.endpoint
  }
});
```

### Lambda Implementation

```python
# main.py
def handler(event, context):
    # 1. Extract Cognito token
    auth_token = event['headers'].get('Authorization')
    
    # 2. Get database credentials from Secrets Manager
    secrets_client = boto3.client('secretsmanager')
    db_secret = secrets_client.get_secret_value(SecretId=secret_name)
    
    # 3. Create Bedrock client with region logic
    bedrock_client = get_bedrock_client(model_id, region)
    
    # 4. Process request with proper error handling
    try:
        response = bedrock_client.invoke_model(...)
        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

## Key Benefits

- ✅ **No API keys in code** - Uses IAM roles
- ✅ **Automatic credential rotation** - Secrets Manager
- ✅ **Region flexibility** - Smart model routing
- ✅ **Secure secrets** - Encrypted at rest
- ✅ **Least privilege** - Specific IAM permissions
- ✅ **Connection pooling** - RDS Proxy optimization
- ✅ **Centralized management** - Single source of truth

## Security Best Practices

1. **Never hardcode credentials** - Always use Secrets Manager or Parameter Store
2. **Use least privilege IAM** - Grant only necessary permissions
3. **Enable encryption** - At rest and in transit
4. **Rotate credentials** - Automatic rotation with Secrets Manager
5. **Monitor access** - CloudTrail and CloudWatch logging
6. **Use VPC endpoints** - Keep traffic within AWS network

This pattern provides a secure, scalable foundation for any AWS project requiring ML model access and database connectivity.