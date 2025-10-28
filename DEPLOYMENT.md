# AWS Elastic Beanstalk Deployment Guide

## Prerequisites

1. **AWS Account** with access to:
   - AWS Elastic Beanstalk
   - Amazon Bedrock
   - AWS Secrets Manager
   - IAM (for role creation)
   - EC2 (for instances)

2. **AWS CLI** installed and configured
3. **EB CLI** installed (`pip install awsebcli`)
4. **Docker** installed locally (optional, for testing)

## Deployment Steps

### 1. Create IAM Role for Beanstalk EC2 Instances

Create an IAM role with these permissions (or use existing `aws-elasticbeanstalk-ec2-role`):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": "arn:aws:bedrock:*:*:foundation-model/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:CreateSecret",
                "secretsmanager:UpdateSecret"
            ],
            "Resource": "arn:aws:secretsmanager:*:*:secret:materials-project/*"
        }
    ]
}
```

**Trust Policy:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

**Attach to Instance Profile:** `aws-elasticbeanstalk-ec2-role`

### 2. Store Materials Project API Key

Store your Materials Project API key in AWS Secrets Manager:

```bash
aws secretsmanager create-secret \
    --name "materials-project/api-key" \
    --description "Materials Project API Key for Quantum Matter App" \
    --secret-string '{"MP_API_KEY":"your_api_key_here"}'
```

### 3. Deploy to Elastic Beanstalk

#### Option A: Using EB CLI (Recommended)

1. **Initialize Beanstalk application:**
```bash
eb init quantum-matter-app --platform docker --region us-east-1
```

2. **Create environment:**
```bash
eb create quantum-matter-env --instance-types t3.medium --envvars AWS_DEFAULT_REGION=us-east-1
```

3. **Deploy:**
```bash
eb deploy
```

#### Option B: Using AWS Console

1. **Go to Elastic Beanstalk Console**
2. **Create Application:**
   - Application name: `quantum-matter-app`
   - Platform: Docker
   - Platform version: Latest

3. **Upload Code:**
   - Create ZIP file of your project (exclude .git, venv, etc.)
   - Upload ZIP or connect to GitHub

4. **Configure Environment:**
   - Environment name: `quantum-matter-env`
   - Instance type: t3.medium or larger
   - Load balancer: Application Load Balancer

5. **Set Environment Variables:**
   - `AWS_DEFAULT_REGION`: us-east-1
   - `STREAMLIT_SERVER_HEADLESS`: true

6. **Configure Security:**
   - EC2 instance profile: `aws-elasticbeanstalk-ec2-role`
   - Service role: `aws-elasticbeanstalk-service-role`

### 4. Access Your App

After deployment (5-10 minutes), you'll get a URL like:
```
http://quantum-matter-env.eba-abcd1234.us-east-1.elasticbeanstalk.com
```

For HTTPS, configure SSL certificate in the Load Balancer settings.

## Cost Estimation

- **EC2 Instance (t3.medium)**: ~$30-35/month
- **Application Load Balancer**: ~$20/month
- **Bedrock**: Pay per API call (~$0.01-0.10 per query)
- **Secrets Manager**: ~$0.40/month per secret
- **Total**: ~$50-60/month

## Monitoring

- **Beanstalk Console**: Application health and logs
- **CloudWatch**: Automatic metrics and logging
- **Health Checks**: Built-in application monitoring
- **Log Files**: Available in Beanstalk console

## Updating the App

1. **Using EB CLI:**
```bash
eb deploy
```

2. **Using Console:**
   - Upload new ZIP file
   - Or trigger deployment from connected repository

3. **Rolling Deployments:**
   - Beanstalk supports zero-downtime deployments

## Troubleshooting

### Common Issues:

1. **Build Failures**
   - Check Dockerfile syntax
   - Verify requirements.txt dependencies

2. **Permission Errors**
   - Verify IAM role has correct permissions
   - Check role is attached to App Runner service

3. **Model Access Issues**
   - Ensure Bedrock model access is enabled in AWS Console
   - Verify correct regions for each model

4. **Secrets Manager Issues**
   - Verify secret exists and has correct format
   - Check IAM permissions for secret access

## Security Best Practices

1. **Use IAM roles** instead of access keys
2. **Store secrets** in AWS Secrets Manager
3. **Enable logging** for monitoring
4. **Use least privilege** IAM permissions
5. **Monitor costs** regularly

## Scaling

Beanstalk auto-scaling configuration:
- **Minimum instances**: 1
- **Maximum instances**: 10 (configurable)
- **Auto-scaling triggers**: CPU, memory, network, or custom metrics
- **Load balancer**: Distributes traffic across instances