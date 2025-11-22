# Deployment Guide

## Overview
This guide covers deploying the Quantum Matter LLM Testing Platform to AWS Elastic Beanstalk and running it locally.

## Prerequisites

### AWS Account Setup
- AWS account with Elastic Beanstalk, Bedrock, and Secrets Manager access
- AWS CLI installed and configured
- EB CLI installed: `pip install awsebcli`

### API Keys
- Materials Project API key from [materialsproject.org](https://materialsproject.org/)

## Local Development

### Quick Start
```bash
# 1. Configure Materials Project API key
python setup/setup_secrets.py

# 2. Install Braket integration (optional)
python setup/install_braket.py

# 3. Run locally
python run_local.py
```

### Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure AWS credentials with SSO
aws configure sso
# OR use existing profile
export AWS_PROFILE=your-profile-name

# Run application
streamlit run app.py
```

## AWS Elastic Beanstalk Deployment

### Step 1: Setup API Key
```bash
# Store Materials Project API key in AWS Secrets Manager
python setup/setup_secrets.py
```

### Step 2: Create IAM Roles and Permissions

#### A. Create EC2 Instance Profile Role
1. **Go to AWS Console** → **IAM** → **Roles** → **Create role**
2. **Select trusted entity:**
   - Trusted entity type: **AWS service**
   - Service: **EC2**
   - Use case: **EC2**
3. **Add permissions policies:**
   - Search and attach: `AWSElasticBeanstalkWebTier`
   - Search and attach: `AWSElasticBeanstalkWorkerTier`
   - Search and attach: `AWSElasticBeanstalkMulticontainerDocker`
4. **Create custom policy** for Bedrock and Secrets Manager:
   - Click **Create policy** → **JSON** tab
   - Paste the JSON below:

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
                "secretsmanager:GetSecretValue"
            ],
            "Resource": "arn:aws:secretsmanager:*:*:secret:materials-project/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "braket:SearchDevices",
                "braket:GetDevice",
                "braket:CreateQuantumTask",
                "braket:GetQuantumTask",
                "braket:CancelQuantumTask"
            ],
            "Resource": "*"
        }
    ]
}
```

5. **Name the policy:** `QuantumMatterAppPermissions`
6. **Create policy** and go back to role creation
7. **Attach the custom policy** to your role
8. **Role name:** `aws-elasticbeanstalk-ec2-role`
9. **Create role**

#### B. Create Service Role (if needed)
1. **Go to IAM** → **Roles** → **Create role**
2. **Select trusted entity:**
   - Trusted entity type: **AWS service**
   - Service: **Elastic Beanstalk**
   - Use case: **Elastic Beanstalk - Customizable**
3. **Add permissions:**
   - `AWSElasticBeanstalkEnhancedHealth`
   - `AWSElasticBeanstalkManagedUpdatesCustomerRolePolicy`
4. **Role name:** `aws-elasticbeanstalk-service-role`
5. **Create role**

### Step 3: Create Elastic Beanstalk Application



#### Using AWS Console (Recommended for first-time setup)

1. **Click "Create environment"**
![](images/eb-01-create-application.png)
2. **Click "Web server environment"**
![](images/eb-02-create-application.png)
3. **Application information:**
![](images/eb-03-create-application.png)
   - Application name: `quantum-matter-app`
   - Application tags: (optional)

4. **Environment information:**
![](images/eb-04-create-application.png)
   - Environment name: `quantum-matter-env`
   - Domain: (leave blank for auto-generated)
   - **Note:** Domain names must be unique globally. If you want a custom domain, try alternatives like `quantum-ai-platform` or `your-quantum-llm`

5. **Platform:**
![](images/eb-05-create-application.png)
   - Platform type: **Managed platform**
   - Platform: **Docker**
   - Platform branch: **Docker running on 64bit Amazon Linux 2023**
   - Platform version: **Latest recommended**

6. **Application code:**
![](images/eb-06-create-application.png)
   - Source: **Upload your code**
   - **First, create deployment ZIP:**
     ```bash
     # Run this command in your project root directory
     python deploy_fixed_integration.py
     ```
   - **Then upload:** Click "Choose file" and select the ZIP file created above
   - Version label: `v1.0`

7. **Configuration presets:**
![](images/eb-07-create-application.png)
   - Select: **Single instance (free tier eligible)** (~$30-35/month)
   - Alternative: **High availability** for production (~$50-60/month)

8. **Click "Next"**

#### Configure Service Access
![](images/eb-08-create-application.png)
1. **Service role:** `aws-elasticbeanstalk-service-role`
2. **EC2 instance profile:** `aws-elasticbeanstalk-ec2-role`
3. **Click "Next"**

#### Set Up Networking
![](images/eb-09-create-application.png)
1. **VPC:** Select default VPC (usually `vpc-xxxxxxx | (172.31.0.0/16) | default`)
2. **Public IP address:** **Activated**
3. **Instance subnets:** Select **ONLY public subnets** (avoid private subnets)
4. **Database:** Leave unchecked (saves costs)
5. **Click "Next"**

#### Configure Instance Traffic and Scaling
![](images/eb-10-create-application1.png)
![](images/eb-10-create-application2.png)
1. **Root volume:** Change from 8GB to **20GB** (recommended)
2. **Instance types:** Remove `t3.micro`, keep `t3.medium` (minimum for our app)
3. **IMDSv1:** Keep **Disabled** (security best practice)
4. **Security groups:** Default VPC security group
5. **EC2 key pair:** (optional, for SSH access)
6. **Click "Next"**

#### Configure Updates, Monitoring, and Logging
1. **Monitoring:** System: **Basic**, Application health: **Enabled**
2. **Managed updates:** **Enabled**, Update level: **Minor and patch**
3. **Platform software:** Proxy server: **Nginx**, Log options: **Rotate logs**
4. **Cost optimization (optional):**
   - Health event streaming: **Disable** (saves CloudWatch costs)
   - X-Ray daemon: **Disable** (saves service charges)
   - S3 log storage: **Disable** (saves S3 charges)

5. **Environment properties:** Add these required environment variables by clicking "Add environment property" for each one:

   **Required (8 variables):**
   - `AWS_DEFAULT_REGION` = `us-east-1`
   - `STREAMLIT_SERVER_HEADLESS` = `true`
   - `STREAMLIT_SERVER_ADDRESS` = `0.0.0.0`
   - `STREAMLIT_SERVER_PORT` = `8501`
   - `MCP_SERVER_ENABLED` = `true`
   - `MCP_PYTHON_PATH` = `python3.12`
   - `MCP_MATERIALS_SERVER_PATH` = `/var/app/current/enhanced_mcp_materials`
   - `PYTHONPATH` = `/usr/local/lib/python3.12/site-packages:/var/app/current`

   **Optional (for authentication):**
   - `DEMO_USERNAME` = your chosen username
   - `DEMO_PASSWORD` = your chosen password
   - `CLOUDFRONT_HEADER_NAME` = custom header name
   - `CLOUDFRONT_HEADER_VALUE` = custom header value

   Enter each property name and value exactly as shown above.

6. **Click "Next"**

#### Review and Submit

1. **Review all settings**
2. **Click "Submit"**
3. **Wait 5-10 minutes** for environment creation

### Step 4: Using EB CLI (Alternative Method)
```bash
# Initialize Beanstalk application
eb init quantum-matter-app --platform docker --region us-east-1

# Create environment with specific settings
eb create quantum-matter-env \
  --instance-types t3.medium \
  --service-role aws-elasticbeanstalk-service-role \
  --instance-profile aws-elasticbeanstalk-ec2-role

# Set environment variables
eb setenv AWS_DEFAULT_REGION=us-east-1 STREAMLIT_SERVER_HEADLESS=true

# Deploy
eb deploy
```

### Step 5: Verify Deployment
1. **Check Environment Health:** Should show "Ok" (green)
2. **Access Application:** Click the URL in Beanstalk console
3. **Test Basic Functionality:** Try a simple query
4. **Check Logs:** Review application logs for any errors

### Step 6: Access Application
Your app will be available at the URL shown in the Beanstalk console, typically:
`http://quantum-matter-env.region.elasticbeanstalk.com`

## Updating the Application

### Code Updates
```bash
# Create new deployment package
python deploy_fixed_integration.py

# Deploy via EB CLI
eb deploy
```

### Configuration Updates
Use the Elastic Beanstalk console to modify environment variables and instance settings.

## Cost Estimation
- **EC2 Instance (t3.medium)**: ~$30-35/month
- **Application Load Balancer**: ~$20/month (if using load balancing)
- **Bedrock API calls**: ~$0.01-0.10 per query
- **Secrets Manager**: ~$0.40/month per secret
- **Total**: ~$50-60/month

## Troubleshooting

### Common Issues

**Deployment Fails**
- Check that all required files are included in deployment package
- Verify IAM permissions are correctly configured
- Check application logs in Beanstalk console

**Model Access Issues**
- Ensure Bedrock model access is enabled in AWS Console
- Verify correct regions for each model (us-east-1, us-west-2)

**Materials Project API Issues**
- Verify API key is stored correctly in Secrets Manager
- Check network connectivity to Materials Project servers

### Getting Help
1. Check application logs in Beanstalk console
2. Review CloudWatch logs for detailed error messages
3. Verify AWS credentials and permissions
4. Test with simple queries first

## Security Best Practices
1. Use IAM roles instead of hardcoded credentials
2. Store API keys in AWS Secrets Manager
3. Enable CloudWatch logging for monitoring
4. Use least privilege IAM permissions
5. Regularly update dependencies and platform versions