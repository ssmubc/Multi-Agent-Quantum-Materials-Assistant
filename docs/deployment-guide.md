# Deployment Guide

## Table of Contents

### [Local Development](#local-development)
- [Quick Start (5 minutes)](#local-quick-start)
- [Manual Setup](#local-manual-setup)
- [Troubleshooting Local Issues](#local-troubleshooting)

### [AWS Elastic Beanstalk Deployment](#aws-elastic-beanstalk-deployment)
- [Prerequisites Checklist](#aws-prerequisites)
- [Step-by-Step Deployment](#aws-step-by-step)
- [CloudFront Integration (SSL/CDN)](#cloudfront-integration)
- [Cost Estimation](#cost-estimation)
- [Troubleshooting AWS Issues](#aws-troubleshooting)

### [Quick Reference](#quick-reference)
- [Environment Variables](#environment-variables-reference)
- [IAM Permissions](#iam-permissions-reference)
- [Security Best Practices](#security-best-practices)

---

## Overview
This guide provides step-by-step instructions for:
1. **Local Development**: Run the app on your computer for testing
2. **AWS Deployment**: Deploy to production with SSL and global CDN

**Choose your path:**
- **Local Development**: Testing and development (5 minutes)
- **AWS Production**: Public deployment with SSL (30 minutes)

---

# Local Development

## Prerequisites for Local Development

**Required:**
- [ ] Python 3.8+ installed
- [ ] Git installed
- [ ] AWS CLI configured (for Bedrock access)
- [ ] Materials Project API key from [materialsproject.org](https://materialsproject.org/)

**Optional:**
- [ ] AWS SSO configured (recommended)
- [ ] Amazon Braket access (for quantum circuits)

---

## Local Quick Start

**Time Required: 5 minutes**

### Step 1: Clone and Setup (2 minutes)
```bash
# Clone repository
git clone <repository-url>
cd Quantum_Matter_Streamlit_App

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure API Keys (2 minutes)
```bash
# Option A: Use setup script (recommended)
python setup/setup_secrets.py

# Option B: Set environment variable
export MP_API_KEY=your-materials-project-key
```

### Step 3: Configure AWS (1 minute)
```bash
# Option A: Use existing AWS profile
export AWS_PROFILE=your-profile-name  # Linux/Mac
set AWS_PROFILE=your-profile-name     # Windows

# Option B: Configure new profile
aws configure sso
```

### Step 4: Run Application
```bash
# Quick start (sets defaults automatically)
python run_local.py

# OR run directly
streamlit run app.py
```

**✅ Success**: App should open at http://localhost:8501

---

## Local Manual Setup

**Use this if quick start doesn't work**

### Step 1: Install Dependencies
```bash
# Create virtual environment (recommended)
python -m venv quantum_env
source quantum_env/bin/activate  # Windows: quantum_env\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
```bash
# Linux/Mac
export AWS_PROFILE=your-aws-profile
export MP_API_KEY=your-materials-project-key
export DEMO_USERNAME=demo
export DEMO_PASSWORD=quantum2025

# Windows
set AWS_PROFILE=your-aws-profile
set MP_API_KEY=your-materials-project-key
set DEMO_USERNAME=demo
set DEMO_PASSWORD=quantum2025
```

### Step 3: Test AWS Connection
```bash
# Verify AWS credentials work
aws sts get-caller-identity

# Should show your AWS account info
```

### Step 4: Run Application
```bash
streamlit run app.py --server.port 8501
```

---

## Local Troubleshooting

**App won't start:**
- Check Python version: `python --version` (need 3.8+)
- Install missing packages: `pip install -r requirements.txt`
- Check AWS credentials: `aws sts get-caller-identity`

**Models not working:**
- Verify AWS profile has Bedrock access
- Check correct regions: us-east-1, us-west-2
- Test with simple query first

**Materials Project errors:**
- Verify API key at materialsproject.org
- Check network connectivity
- Use dummy data mode if API unavailable

---

# AWS Elastic Beanstalk Deployment

## AWS Prerequisites

**Time Required: 30-45 minutes**

### Required AWS Access
- [ ] AWS account with billing enabled
- [ ] IAM permissions for Elastic Beanstalk, Bedrock, Secrets Manager
- [ ] AWS CLI installed and configured
- [ ] EB CLI installed (only needed for command line deployment):
  ```bash
  pip install awsebcli
  ```

### Required API Keys
- Materials Project API key from [materialsproject.org](https://materialsproject.org/)

### Cost Expectations (AWS Elastic Beanstalk)
- **Single Instance (t3.medium)**: ~$30-35/month
- **Single Instance (t3.large)**: ~$60-70/month  
- **Single Instance (t3.xlarge)**: ~$120-140/month
- **High Availability + Load Balancer**: +$20/month
- **CloudFront SSL/CDN**: $0/month (within free tier)
- **Local Development**: $0/month (only Bedrock API costs)

---

## AWS Step-by-Step

### Phase 1: Setup (10 minutes)

#### Step 1.1: Store API Key in AWS Secrets Manager
```bash
# Run setup script to store Materials Project API key securely
python setup/setup_secrets.py
```

**What this does:**
- Creates AWS Secrets Manager secret
- Stores your Materials Project API key securely
- Configures automatic retrieval in production

#### Step 1.2: Create IAM Roles and Permissions

**Action Required: Create 2 IAM Roles**

#### A. Create EC2 Instance Profile Role

**Step-by-step:**
1. **Open AWS Console** → **IAM** → **Roles** → **Create role**
2. **Select trusted entity:**
   - Trusted entity type: **AWS service**
   - Service: **EC2**
   - Use case: **EC2**
   - Click **Next**

3. **Add AWS managed permissions** (search and select each):
   - ✅ `AWSElasticBeanstalkWebTier`
   - ✅ `AWSElasticBeanstalkWorkerTier`
   - ✅ `AWSElasticBeanstalkMulticontainerDocker`
   - ✅ `AmazonBraketFullAccess`
   - Click **Next**

4. **Create custom policy for Secrets Manager:**
   - Click **Create policy** (opens new tab)
   - Click **JSON** tab
   - **Copy and paste this JSON:**

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": "arn:aws:secretsmanager:*:*:secret:materials-project/*"
        }
    ]
}
```

5. **Save the policy:**
   - Policy name: `QuantumMatterAppPermissions`
   - Click **Create policy**
   - **Go back to role creation tab**

6. **Attach policies to role:**
   - Refresh policy list
   - Search and select: `QuantumMatterAppPermissions`
   - **Verify all 6 policies are selected:**
     - 4 AWS managed policies (from step 3)
     - 1 custom policy (QuantumMatterAppPermissions)
     - Plus any additional Bedrock policies you may have
   - Click **Next**

7. **Name and create role:**
   - Role name: `aws-elasticbeanstalk-ec2-role`
   - Click **Create role**

#### B. Create Service Role

**Step-by-step:**
1. **Create new role** → **AWS service** → **Elastic Beanstalk**
2. **Select use case:** **Elastic Beanstalk - Customizable**
3. **Add permissions:**
   - ✅ `AWSElasticBeanstalkEnhancedHealth`
   - ✅ `AWSElasticBeanstalkManagedUpdatesCustomerRolePolicy`
4. **Role name:** `aws-elasticbeanstalk-service-role`
5. **Create role**

**✅ Checkpoint**: You should now have 2 IAM roles created

---

### Phase 2: Create Deployment Package (5 minutes)

#### Step 2.1: Generate Deployment ZIP
```bash
# Run deployment script from project root
python deployment/deploy_fixed_integration.py
```

**What this does:**
- Creates optimized deployment package
- Includes all required files and dependencies
- Generates `quantum_matter_app_fixed.zip`

**✅ Success**: You should see "Deployment package created" message

---

### Phase 3: Deploy to Elastic Beanstalk (15 minutes)

#### Step 3.1: Create Elastic Beanstalk Application



**Action Required: Create Elastic Beanstalk Environment**

**Go to AWS Console → Elastic Beanstalk → Create application**

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
     python deployment/deploy_fixed_integration.py
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
1. **VPC:** Select default VPC (usually shows as `vpc-xxxxxxx | default`)
2. **Public IP address:** **Activated**
3. **Instance subnets:** Select **ONLY public subnets** (avoid private subnets)
4. **Database:** Leave unchecked (saves costs)
5. **Click "Next"**

#### Configure Instance Traffic and Scaling
![](images/eb-10-create-application1.png)
![](images/eb-10-create-application2.png)
1. **Root volume:** Change from 8GB to **20GB** (recommended)
2. **Instance types:** Remove `t3.micro`, keep `t3.medium` (minimum for our app)
   - **For heavy usage:** Consider t3.large or t3.xlarge
3. **IMDSv1:** Keep **Disabled** (security best practice)
4. **Security groups:** Default security group
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

**Copy these environment variables exactly:**

**Required Variables (copy-paste each):**
```
AWS_DEFAULT_REGION = us-east-1
STREAMLIT_SERVER_HEADLESS = true
STREAMLIT_SERVER_ADDRESS = 0.0.0.0
STREAMLIT_SERVER_PORT = 8501
MCP_SERVER_ENABLED = true
MCP_PYTHON_PATH = python3.12
MCP_MATERIALS_SERVER_PATH = /var/app/current/enhanced_mcp_materials
PYTHONPATH = /usr/local/lib/python3.12/site-packages:/var/app/current
```

**Authentication Variables (add unless using CloudFront public mode):**
```
DEMO_USERNAME = demo
DEMO_PASSWORD = quantum2025
```

**Note:** Skip authentication variables if you plan to use CloudFront with public access

   Enter each property name and value exactly as shown above.

6. **Click "Next"**

#### Review and Submit

1. **Review all settings**
2. **Click "Submit"**
3. **Wait 5-10 minutes** for environment creation

**✅ Success Indicators:**
- Environment Health: Green "Ok"
- Application URL appears in console
- No error messages in logs

---

### Phase 4: Verify Deployment (5 minutes)

#### Step 4.1: Test Basic Functionality
1. **Click the URL** in Elastic Beanstalk console
2. **Login** with demo/quantum2025 (or your credentials)
3. **Test a simple query:** "What is silicon?"
4. **Verify models load** in the sidebar

#### Step 4.2: Check Application Health
- **Environment Health:** Should show "Ok" (green)
- **Application Logs:** No critical errors
- **Model Status:** Models appear in dropdown

**❌ If deployment fails:** See [AWS Troubleshooting](#aws-troubleshooting) section

---

### Alternative: EB CLI Method

**For advanced users who prefer command line:**

```bash
# Initialize and deploy
eb init quantum-matter-app --platform docker --region us-east-1
eb create quantum-matter-env --instance-types t3.medium
eb setenv AWS_DEFAULT_REGION=us-east-1 STREAMLIT_SERVER_HEADLESS=true
eb deploy
```

**Your app URL:** `http://quantum-matter-env.region.elasticbeanstalk.com`

---

### Phase 5: CloudFront Integration (Optional - SSL/CDN)

**Time Required: 10 minutes setup + 20 minutes deployment**

#### Step 5.1: Deploy CloudFront Distribution
```bash
# Run CloudFront setup script
python deployment/setup_cloudfront.py
```

**What you get:**
- ✅ Free SSL certificate (HTTPS)
- ✅ Global CDN (400+ locations)
- ✅ DDoS protection
- ✅ Better performance worldwide

#### Step 5.2: Configure Authentication
```bash
# Option A: Keep authentication (recommended for security)
eb setenv DEMO_USERNAME=your-username DEMO_PASSWORD=your-password

# Option B: Public access 
eb setenv PUBLIC_ACCESS=true CLOUDFRONT_ENABLED=true
eb deploy
```

**⚠️ Security Note:** Public access removes authentication and may increase costs due to unrestricted usage.

#### Step 5.3: Verify CloudFront (20 minutes)
- **Wait 15-20 minutes** for CloudFront deployment
- **Test HTTPS URL:** Use the CloudFront domain provided by the setup script
- **Verify SSL certificate** (lock icon in browser)

**✅ Success:** Your app now has enterprise-grade SSL and global CDN

---

## Quick Reference

### Environment Variables Reference

**Required for all deployments:**
```bash
AWS_DEFAULT_REGION=us-east-1
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_PORT=8501
MCP_SERVER_ENABLED=true
MCP_PYTHON_PATH=python3.12
MCP_MATERIALS_SERVER_PATH=/var/app/current/enhanced_mcp_materials
PYTHONPATH=/usr/local/lib/python3.12/site-packages:/var/app/current
```

**Authentication (recommended for security):**
```bash
DEMO_USERNAME=demo
DEMO_PASSWORD=quantum2025
```

**CloudFront public access (use with caution):**
```bash
PUBLIC_ACCESS=true  # Removes authentication - demo use only
CLOUDFRONT_ENABLED=true  # When using CloudFront
```

### Cost Estimation (AWS Elastic Beanstalk)

| Component | t3.medium | t3.large | t3.xlarge | Notes |
|-----------|-----------|----------|-----------|-------|
| **EC2 Instance** | $30-35/month | $60-70/month | $120-140/month | 24/7 running |
| **Load Balancer** | +$20/month | +$20/month | +$20/month | High availability only |
| **CloudFront** | $0 | $0 | $0 | Free tier: 1TB + 10M requests |
| **SSL Certificate** | $0 | $0 | $0 | Always free via ACM |
| **Bedrock API** | $0.01-0.10/query | $0.01-0.10/query | $0.01-0.10/query | Pay per use |
| **Secrets Manager** | $0.40/month | $0.40/month | $0.40/month | Per secret |
| **Single Instance Total** | **~$30-35/month** | **~$60-70/month** | **~$120-140/month** | |
| **High Availability Total** | **~$50-55/month** | **~$80-90/month** | **~$140-160/month** | |

### IAM Permissions Reference

**EC2 Instance Profile needs (minimum 5 policies):**
- `AWSElasticBeanstalkWebTier`
- `AWSElasticBeanstalkWorkerTier`
- `AWSElasticBeanstalkMulticontainerDocker`
- `AmazonBraketFullAccess`
- `QuantumMatterAppPermissions` (custom policy for Secrets Manager)

**Optional additional policies:**
- `Bedrock-DeepSeek-InvokePolicy` (if you have specific Bedrock model policies)
- Other custom Bedrock policies as needed

**Service Role needs:**
- `AWSElasticBeanstalkEnhancedHealth`
- `AWSElasticBeanstalkManagedUpdatesCustomerRolePolicy`

### Updating the Application

**Code Updates:**
```bash
# Create new deployment package
python deployment/deploy_fixed_integration.py

# Deploy via EB CLI
eb deploy
```

**Configuration Updates:**
- Use Elastic Beanstalk console
- Modify environment variables
- Update instance settings

---

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

## CloudFront Integration (Recommended)

### Overview
CloudFront provides enterprise-grade SSL/TLS encryption, global CDN distribution, and enhanced security for your Quantum Matter application at no additional cost within AWS Free Tier limits.

### Technical Benefits
- **Enterprise SSL/TLS**: Automatic TLS 1.2/1.3 encryption with free certificates
- **Global CDN**: 400+ edge locations worldwide for low latency
- **Security Features**: DDoS protection, WAF integration, security headers
- **Performance**: Caching, compression, HTTP/2 support
- **Cost Effective**: 1TB data transfer + 10M requests/month free

### Prerequisites
- Deployed Elastic Beanstalk application
- AWS CLI configured with CloudFront permissions
- Python 3.7+ for setup script

### Step 1: Deploy CloudFront Distribution

#### Automated Setup (Recommended)
```bash
# Run the CloudFront setup script
python deployment/setup_cloudfront.py
```

The script will:
1. **Detect AWS profiles** and let you select the appropriate one
2. **Find your EB environment** automatically or prompt for manual entry
3. **Create CloudFront distribution** with optimized settings
4. **Configure SSL certificate** automatically (free via AWS Certificate Manager)
5. **Provide HTTPS URL** for immediate access

#### Manual Setup via AWS Console
1. **Go to CloudFront Console** → **Create Distribution**
2. **Origin Settings:**
   - Origin Domain: Your EB environment URL (e.g., `quantum-matter-env.us-east-1.elasticbeanstalk.com`)
   - Protocol: HTTP Only (EB handles HTTPS internally)
   - Origin Path: Leave blank

3. **Cache Behavior Settings:**
   - Viewer Protocol Policy: **Redirect HTTP to HTTPS**
   - Allowed HTTP Methods: **GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE**
   - Cache Policy: **CachingDisabled** (for dynamic Streamlit app)
   - Origin Request Policy: **CORS-S3Origin**

4. **Distribution Settings:**
   - Price Class: **Use Only US, Canada and Europe** (cost optimization)
   - SSL Certificate: **Default CloudFront Certificate** (free)
   - Security Policy: **TLSv1.2_2021**

### Step 2: Configure Authentication Options

#### Option A: Keep Authentication (Internal Use)
```bash
# Set authentication credentials
eb setenv DEMO_USERNAME=your-username DEMO_PASSWORD=your-password -e your-environment-name
```

#### Option B: Enable Public Access (Demo Mode)
```bash
# Enable public access without authentication
eb setenv PUBLIC_ACCESS=true CLOUDFRONT_ENABLED=true -e your-environment-name
eb deploy your-environment-name
```

### Step 3: Verify Deployment

#### Check Distribution Status
```bash
aws cloudfront get-distribution --id your-distribution-id
```

**Status Indicators:**
- ✅ **Ready**: URL loads your application (15-20 minutes)
- ⏳ **Still deploying**: Error page or timeout (wait longer)
- 🔍 **Check Console**: CloudFront → Distributions → Status = "Deployed"

### Step 4: Advanced Configuration

#### Custom Domain Setup
1. **Create SSL Certificate in ACM:**
   ```bash
   aws acm request-certificate \
     --domain-name your-domain.com \
     --validation-method DNS \
     --region us-east-1
   ```

2. **Update CloudFront Distribution:**
   - Add custom domain to Alternate Domain Names (CNAMEs)
   - Select your ACM certificate
   - Update DNS records to point to CloudFront domain

#### Security Headers Configuration
The deployment includes `.ebextensions/06_cloudfront_headers.config` which adds:
- `Strict-Transport-Security`: Force HTTPS
- `X-Content-Type-Options`: Prevent MIME sniffing
- `X-Frame-Options`: Clickjacking protection
- `X-XSS-Protection`: XSS filtering
- `Referrer-Policy`: Control referrer information

### Step 5: Performance Optimization

#### Cache Configuration
```json
{
  "DefaultCacheBehavior": {
    "ViewerProtocolPolicy": "redirect-to-https",
    "MinTTL": 0,
    "DefaultTTL": 0,
    "MaxTTL": 31536000,
    "ForwardedValues": {
      "QueryString": true,
      "Cookies": {"Forward": "all"},
      "Headers": ["Host", "Origin", "Referer"]
    }
  }
}
```

#### Monitoring and Logging
- **CloudWatch Metrics**: Monitor requests, errors, cache hit ratio
- **Real-time Logs**: Enable for detailed request analysis
- **AWS WAF**: Add web application firewall for enhanced security

### Troubleshooting CloudFront

**Distribution Not Working**
- Wait 15-20 minutes for full deployment
- Check origin domain is accessible directly
- Verify cache behaviors allow all HTTP methods

**SSL Certificate Issues**
- Ensure certificate is in us-east-1 region
- Verify domain validation is complete
- Check certificate status in ACM console

**Authentication Problems**
- Verify environment variables are set correctly
- Check if PUBLIC_ACCESS=true for demo mode
- Test direct EB URL first, then CloudFront URL

### Cost Analysis

| Service | Free Tier | Typical Usage | Monthly Cost |
|---------|-----------|---------------|-------------|
| CloudFront | 1TB + 10M requests | <100GB + <1M requests | $0 |
| SSL Certificate | Always free | 1 certificate | $0 |
| Data Transfer | 1TB/month | Academic usage | $0 |
| **Total CloudFront** | | | **$0** |

### Production Checklist
- [ ] CloudFront distribution deployed and accessible
- [ ] SSL certificate working (HTTPS)
- [ ] Authentication configured appropriately
- [ ] Security headers enabled
- [ ] Monitoring and logging configured
- [ ] Custom domain configured (if needed)
- [ ] Performance testing completed

## Security Best Practices
1. Use IAM roles instead of hardcoded credentials
2. Store API keys in AWS Secrets Manager
3. Enable CloudWatch logging for monitoring
4. Use least privilege IAM permissions
5. Regularly update dependencies and platform versions
6. Use CloudFront for SSL/TLS encryption and DDoS protection
7. Enable security headers via CloudFront
8. Monitor CloudFront access logs for security analysis