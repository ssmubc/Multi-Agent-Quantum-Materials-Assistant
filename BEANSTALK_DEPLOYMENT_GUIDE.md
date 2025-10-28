# Complete AWS Elastic Beanstalk Deployment Guide
## Quantum Matter Streamlit App

This guide walks you through deploying your Streamlit app to AWS Elastic Beanstalk from start to finish.

## Prerequisites

- AWS Account with appropriate permissions
- Materials Project API key
- Your Streamlit app code ready

## Step 1: Prepare Your Application Files

### Required Files in ZIP:
```
quantum-matter-app-clean.zip
├── app.py                    # Main Streamlit application
├── demo_mode.py             # Demo responses for fallback
├── Dockerfile               # Container configuration
├── requirements.txt         # Python dependencies
├── models/                  # LLM model classes
│   ├── __init__.py
│   ├── base_model.py
│   ├── nova_pro_model.py
│   ├── llama3_model.py
│   ├── llama4_model.py
│   └── openai_model.py
├── utils/                   # Utility functions
│   ├── __init__.py
│   ├── materials_project_agent.py
│   └── secrets_manager.py
└── .streamlit/              # Streamlit configuration
    └── config.toml
```

### Files to EXCLUDE from ZIP:
- `.ebextensions/` (causes configuration conflicts)
- `Dockerrun.aws.json` (causes static file errors)
- `apprunner.yaml` (not needed for Beanstalk)
- `.git/` folders
- `__pycache__/` folders
- Virtual environment folders

## Step 2: Create IAM Roles

### 2.1 Create EC2 Instance Profile Role

1. **Go to IAM Console** → **Roles** → **Create role**
2. **Select trusted entity:**
   - Trusted entity type: **AWS service**
   - Service: **Elastic Beanstalk**
   - Use case: **Elastic Beanstalk - Compute**
3. **Add permissions:**
   - `AWSElasticBeanstalkEnhancedHealth`
   - `AWSElasticBeanstalkManagedUpdatesCustomerRolePolicy`
4. **Role name:** `aws-elasticbeanstalk-ec2-role`
5. **Create role**

### 2.2 Create Service Role (if needed)

1. **Go to IAM Console** → **Roles** → **Create role**
2. **Select trusted entity:**
   - Trusted entity type: **AWS service**
   - Service: **Elastic Beanstalk**
   - Use case: **Elastic Beanstalk - Environment**
3. **Add default permissions** (AWS will suggest appropriate policies)
4. **Role name:** `aws-elasticbeanstalk-service-role`
5. **Create role**

## Step 3: Set Up VPC (if needed)

### Option A: Use Default VPC (Recommended)
- Most AWS accounts have a default VPC with public subnets
- Check VPC Console to confirm internet gateway is attached

### Option B: Create New VPC
1. **Go to VPC Console** → **Create VPC**
2. **Resources to create:** **VPC and more**
3. **Settings:**
   - Name: `quantum-matter-vpc`
   - IPv4 CIDR: `10.0.0.0/16`
   - IPv6 CIDR: **No IPv6 CIDR block**
   - Tenancy: **Default**
4. **Create VPC** (this creates public/private subnets automatically)

## Step 4: Create Elastic Beanstalk Application

### 4.1 Create Application
1. **Go to Elastic Beanstalk Console**
2. **Create application**
3. **Application information:**
   - Application name: `quantum-matter-app`
   - Platform: **Docker**
   - Platform branch: **Docker running on 64bit Amazon Linux 2023**
   - Platform version: **Latest recommended**

### 4.2 Upload Application Code
1. **Application code:** **Upload your code**
2. **Version label:** `v1.0` (or current version)
3. **Source code origin:** **Local file**
4. **Choose file:** Select your `quantum-matter-app-clean.zip`

### 4.3 Configure Presets
- **Configuration presets:** **Single instance (free tier eligible)**

## Step 5: Configure Service Access

1. **Service role:** `aws-elasticbeanstalk-service-role`
2. **EC2 instance profile:** `aws-elasticbeanstalk-ec2-role`
3. **EC2 key pair:** Leave blank (optional)

## Step 6: Set Up Networking

1. **VPC:** Select your VPC (default or custom)
2. **Public IP address:** **Enable**
3. **Instance subnets:** Select **PUBLIC subnets only**
   - Look for subnets named with "public" or check route tables
   - Avoid private subnets (causes connectivity issues)
4. **Database:** Leave unchecked
5. **Tags:** 
   - Key: `Project`, Value: `quantum-matter-app`

## Step 7: Configure Instance Traffic and Scaling

### Instance Settings:
- **IMDSv1:** **Disabled** (security best practice)
- **EC2 Security Groups:** Use default security group for your VPC
- **Environment type:** **Single instance**
- **Fleet composition:** **On-Demand instance**
- **Instance types:** `t3.medium`, `t3.large` (remove t3.micro/small)

## Step 8: Configure Updates, Monitoring, and Logging

### Monitoring:
- **Health reporting:** **Enhanced**
- **Health event streaming:** **Disable** (saves costs)

### Updates:
- **Managed updates:** **Enable**
- **Update level:** **Minor and patch**

### Email Notifications:
- **Email:** Enter your email for alerts

### Rolling Updates:
- **Deployment policy:** **All at once**
- **Rolling update type:** **Disabled**

### Platform Software:
- **Proxy server:** **Nginx**
- **X-Ray:** **Disable** (saves costs)
- **S3 log storage:** **Disable** (saves costs)
- **CloudWatch logs:** **Enable** (useful for debugging)

### Environment Properties (CRITICAL):
Add these two environment variables:

1. **Property 1:**
   - Source: **Plain text**
   - Name: `AWS_DEFAULT_REGION`
   - Value: `us-east-1`

2. **Property 2:**
   - Source: **Plain text**
   - Name: `STREAMLIT_SERVER_HEADLESS`
   - Value: `true`

## Step 9: Review and Create

1. **Review all settings**
2. **Click "Create environment"**
3. **Wait 5-10 minutes for deployment**
4. **Watch Events tab for progress**

## Step 10: Add Application Permissions

After successful deployment, add permissions for Bedrock and Secrets Manager:

### 10.1 Create Custom Policy
1. **Go to IAM Console** → **Roles**
2. **Find your EC2 role:** `aws-elasticbeanstalk-ec2-role`
3. **Add permissions** → **Create inline policy**

### 10.2 Add Permissions (Visual Editor)

**First Permission Block:**
- **Service:** `Bedrock`
- **Actions:** `InvokeModel`, `InvokeModelWithResponseStream`
- **Resources:** `All resources`

**Second Permission Block:**
- **Service:** `Secrets Manager`
- **Actions:** `GetSecretValue`
- **Resources:** `arn:aws:secretsmanager:*:*:secret:materials-project/*`

### 10.3 Create Policy
- **Policy name:** `QuantumMatterAppPermissions`
- **Create policy**

## Step 11: Set Up Materials Project API Key (Optional)

### Option A: Store in AWS Secrets Manager
```bash
aws secretsmanager create-secret \
    --name "materials-project/api-key" \
    --description "Materials Project API Key for Quantum Matter App" \
    --secret-string '{"MP_API_KEY":"your_api_key_here"}'
```

### Option B: Enter Manually in App
- Users can enter API key directly in the app interface

## Step 12: Access Your Application

1. **Wait for Health status:** Unknown → Ok
2. **Get URL from Domain field:** `http://your-app.elasticbeanstalk.com`
3. **Test your application**

## Troubleshooting Common Issues

### Deployment Fails with Configuration Errors:
- **Cause:** `.ebextensions` or `Dockerrun.aws.json` in ZIP file
- **Solution:** Remove these files and redeploy

### No Internet Gateway Error:
- **Cause:** VPC missing internet gateway or using private subnets
- **Solution:** Use default VPC or create VPC with public subnets

### Permission Denied Errors:
- **Cause:** Missing IAM permissions for Bedrock/Secrets Manager
- **Solution:** Add custom policy from Step 10

### App Won't Start:
- **Cause:** Missing environment variables
- **Solution:** Ensure `AWS_DEFAULT_REGION` and `STREAMLIT_SERVER_HEADLESS` are set

## Updating Your Application

### For Code Changes:
1. **Create new ZIP file** with updated code
2. **Go to Beanstalk Console** → **Upload and deploy**
3. **Select new ZIP file**
4. **Deploy**

### For Configuration Changes:
1. **Go to Configuration tab** in Beanstalk Console
2. **Edit relevant section**
3. **Apply changes**

## Cost Optimization

- **Single instance:** ~$30-35/month (t3.medium)
- **Load balanced:** ~$50-60/month (includes ALB)
- **Bedrock:** Pay per API call (~$0.01-0.10 per query)
- **Secrets Manager:** ~$0.40/month per secret

## Security Best Practices

1. **Use IAM roles** instead of access keys
2. **Store secrets** in AWS Secrets Manager
3. **Enable CloudWatch logging** for monitoring
4. **Use least privilege** IAM permissions
5. **Regularly update** platform versions

## Next Steps for Adding Models

When adding new LLM models:

1. **Update your code** with new model classes
2. **Update requirements.txt** if needed
3. **Create new ZIP file** with same structure
4. **Deploy via "Upload and deploy"**
5. **Test new models** in the deployed app

The same Beanstalk environment can be reused - just upload new versions of your application code!