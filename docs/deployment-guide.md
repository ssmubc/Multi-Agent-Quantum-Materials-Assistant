# Deployment Guide

## Quick Navigation
- [Local Development (5 min)](#local-development)
- [AWS Production Deployment (25 min)](#aws-deployment)
- [Troubleshooting](#troubleshooting)

## Overview
**Local Development**: Test on your computer  
**AWS Production**: Deploy with SSL and global CDN

# Local Development

**Prerequisites**: Python 3.8+, AWS CLI, Materials Project API key

## Quick Start (5 minutes)
```bash
# 1. Clone and install
git clone <repository-url>
cd Quantum_Matter_Streamlit_App
pip install -r requirements.txt

# 2. Configure
python setup/setup_secrets.py  # Store Materials Project API key
export AWS_PROFILE=your-profile-name

# 3. Run
python run_local.py
```

**Local Login**: Username: `demo`, Password: `quantum2025`
Cognito authentication is only used for AWS Elastic Beanstalk deployment.

# AWS Deployment

**Correct Order**: Deploy app first, then add optional features

## Phase 1: Setup AWS Resources (10 minutes)

### Step 1: Store API Key
```bash
python setup/setup_secrets.py
```

### Step 2: Create IAM Roles
**Create 2 roles in AWS Console → IAM → Roles:**

**A. EC2 Instance Profile Role**
- Name: `aws-elasticbeanstalk-ec2-role`
- Trusted entity: **EC2**
- Policies: `AWSElasticBeanstalkWebTier`, `AWSElasticBeanstalkWorkerTier`, `AWSElasticBeanstalkMulticontainerDocker`, `AmazonBraketFullAccess`
- Custom policy for Secrets Manager:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["secretsmanager:GetSecretValue"],
            "Resource": "arn:aws:secretsmanager:*:*:secret:materials-project/*"
        }
    ]
}
```

**B. Service Role**
- Name: `aws-elasticbeanstalk-service-role`
- Trusted entity: **Elastic Beanstalk**
- Policies: `AWSElasticBeanstalkEnhancedHealth`, `AWSElasticBeanstalkManagedUpdatesCustomerRolePolicy`

## Phase 2: Deploy Application (15 minutes)

### Step 1: Create Deployment Package
```bash
python deployment/deploy_fixed_integration.py
```

### Step 2: Create Elastic Beanstalk Environment
**AWS Console → Elastic Beanstalk → Create application**

1. **Click "Create environment"**
![](images/eb-01-create-application.png)

2. **Click "Web server environment"**
![](images/eb-02-create-application.png)

3. **Application information:**
![](images/eb-03-create-application.png)
   - Application name: `quantum-matter-app`

4. **Environment information:**
![](images/eb-04-create-application.png)
   - Environment name: `quantum-matter-env`

5. **Platform:**
![](images/eb-05-create-application.png)
   - Platform: **Docker**
   - Platform branch: **Docker running on 64bit Amazon Linux 2023**

6. **Application code:**
![](images/eb-06-create-application.png)
   - Source: **Upload your code**
   - Upload ZIP file from Step 1

7. **Configuration presets:**
![](images/eb-07-create-application.png)
   - Select: **Single instance**

8. **Configure Service Access:**
![](images/eb-08-create-application.png)
   - Service role: `aws-elasticbeanstalk-service-role`
   - EC2 instance profile: `aws-elasticbeanstalk-ec2-role`

9. **Set Up Networking:**
![](images/eb-09-create-application.png)
   - VPC: Default VPC
   - Public IP address: **Activated**

10. **Configure Instance:**
![](images/eb-10-create-application1.png)
![](images/eb-10-create-application2.png)
    - Root volume: **20GB**
    - Instance types: **t3.medium** (minimum), **t3.large** (recommended), **t3.xlarge** (heavy usage)

11. **Environment variables:**
```
AWS_DEFAULT_REGION = us-east-1
STREAMLIT_SERVER_HEADLESS = true
STREAMLIT_SERVER_ADDRESS = 0.0.0.0
STREAMLIT_SERVER_PORT = 8501
MCP_SERVER_ENABLED = true
DEMO_USERNAME = demo
DEMO_PASSWORD = quantum2025
```
**Note**: Demo credentials provide fallback authentication if Cognito is not configured

**✅ Success**: App accessible at EB URL (5-10 minutes)

## Phase 3: Optional Enhancements

### Add Cognito Authentication (Optional)
**Run AFTER successful deployment:**
```bash
python setup/setup_cognito.py
```
**What this does:**
- Creates Cognito User Pool and App Client
- Automatically sets EB environment variables
- Configures email verification
- Takes priority over demo credentials

### Add CloudFront SSL/CDN (Optional)
**Run AFTER successful deployment:**
```bash
python deployment/setup_cloudfront.py
```
**Benefits**: Free SSL, global CDN, 15-20 minutes deployment time

## Security Status
**✅ All Critical Vulnerabilities Fixed:**
- Authentication bypass - Resolved with proper auth validation
- Command injection - Fixed with input validation and subprocess security
- Secrets exposure - Moved to AWS Secrets Manager
- Input validation - Comprehensive validation implemented
- Rate limiting - 5 requests per 60 seconds implemented
- Security headers - HTTP security headers configured
- Audit logging - Security event tracking enabled

## Cost Estimation
- **t3.medium** (minimum): ~$30-35/month
- **t3.large** (recommended): ~$60-70/month  
- **t3.xlarge** (heavy usage): ~$120-140/month
- **CloudFront**: $0/month (free tier)
- **Cognito**: $0/month (free tier)



# Troubleshooting

**Deployment fails:**
- Check IAM permissions are correctly configured
- Verify all required files in deployment package
- Check application logs in EB console

**Testing and Quality Assurance:**
- Current test coverage: 0% (development phase)
- Recommended tools: pytest, bandit (security), safety (dependencies)
- Priority testing areas: Authentication, MCP client, agent workflows

**Models not working:**
- Ensure Bedrock access enabled in AWS Console
- Verify correct regions: us-east-1, us-west-2

**Materials Project errors:**
- Verify API key stored in Secrets Manager
- Check network connectivity

**Cognito issues:**
- Run setup after successful EB deployment
- Verify User Pool created in us-east-1

**CloudFront issues:**
- Wait 15-20 minutes for deployment
- Test EB URL first, then CloudFront URL