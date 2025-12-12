# Deployment Guide

## Quick Navigation
- [Prerequisites](#prerequisites)
- [Local Development (Optional)](#local-development-optional)
- [AWS Deployment (25 min)](#aws-deployment)
  - [Phase 1: Setup AWS Resources](#phase-1-setup-aws-resources-10-minutes)
  - [Phase 2: Deploy Application](#phase-2-deploy-application-15-minutes)
  - [Phase 3: Optional Enhancements](#phase-3-optional-enhancements)
- [Security Measures](#security-measures-implemented)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### AWS Account Setup
Before starting, you need an AWS account with proper access:

1. **Create AWS Account**: Visit [aws.amazon.com](https://aws.amazon.com/) and create a free account
2. **Install AWS CLI**: Follow the [AWS CLI installation guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
3. **Configure SSO**: Run `aws configure sso` or see [AWS SSO configuration guide](https://docs.aws.amazon.com/cli/latest/userguide/sso-configure-profile-token.html)

### Required Tools
- **Python 3.8+**: Download from [python.org](https://www.python.org/downloads/)
- **Materials Project API Key**: Register at [materialsproject.org](https://materialsproject.org/) for free API access

## Overview
**Local Development (Optional)**: Test locally with demo authentication  
**AWS Deployment**: Deploy with enterprise authentication, SSL, and global CDN

## Local Development (Optional)
```bash
git clone <repository-url>
cd Quantum_Matter_Streamlit_App
pip install -r requirements.txt
python setup/setup_secrets.py
export AWS_PROFILE=your-profile-name
python run_local.py
```

**Login**: Username: `demo`, Password: `quantum2025`

## AWS Deployment

**Order**: Deploy app first, then add optional features

## Phase 1: Setup AWS Resources (10 minutes)

### Step 1: Store API Key
```bash
python setup/setup_secrets.py
```

### Step 2: Create IAM Roles
**Create 2 [IAM roles](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html) in AWS Console → IAM → Roles:**

**A. EC2 Instance Profile Role**
- Name: `aws-elasticbeanstalk-ec2-role`
- Trusted entity: **EC2**
- [AWS managed policies](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_managed-vs-inline.html): `AWSElasticBeanstalkWebTier`, `AWSElasticBeanstalkWorkerTier`, `AWSElasticBeanstalkMulticontainerDocker`, `AmazonBraketFullAccess`
- Custom [inline policy](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_managed-vs-inline.html) for Secrets Manager:

Begin by opening AWS Console → IAM → Roles → aws-elasticbeanstalk-ec2-role

Select "Roles" under "Access management."
You will see:
![](images/permission_policies.png)
In order to add these policies you can select "Add permissions" and then select "Attach Policies".

Now in the search bar enter the folowing policy names and add them.
- `AWSElasticBeanstalkWebTier`
- `AWSElasticBeanstalkWorkerTier`
- `AWSElasticBeanstalkMulticontainerDocker`
- `AmazonBraketFullAccess`

Then go back to the Permissions page and select "Add permissions" again but this time select "Create inline policy."

Under "Specify permissions" select the "JSON editor" option and enter the following JSON lines:
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
It should look like this:
![](images/specify_permission_inline.png)

Then click on the button "Next" on the bottom right corner. 

You will now see the following page:
![](images/policy_name.png)

Enter a policy name (e.g., MaterialsProjectKey) and click "Create policy."

- **Required for Admin Authentication**: Custom inline policy for Cognito admin access:

Go back to the Permissions page and select "Add permissions" again and select "Create inline policy."

Under "Specify permissions" select the "JSON editor" option and enter the following JSON lines:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cognito-idp:ListUsers",
                "cognito-idp:AdminDeleteUser",
                "cognito-idp:CreateGroup",
                "cognito-idp:AdminAddUserToGroup",
                "cognito-idp:AdminRemoveUserFromGroup",
                "cognito-idp:ListGroups",
                "cognito-idp:ListUsersInGroup",
                "cognito-idp:AdminListGroupsForUser",
                "cognito-idp:AdminCreateUser",
                "cognito-idp:AdminSetUserPassword"
            ],
            "Resource": "arn:aws:cognito-idp:*:YOUR_ACCOUNT_ID:userpool/*"
        }
    ]
}
```
**Note**: Replace `YOUR_ACCOUNT_ID` with your actual AWS account ID

It should look like this:
![](images/cognito_policy.png)

Then click on the button "Next" on the bottom right corner. 

You will now see the following page:
![](images/policy_name.png)

Enter a policy name (e.g., CognitoAdminAccess) and click "Create policy."

**B. Service Role**
- Name: `aws-elasticbeanstalk-service-role`
- Trusted entity: **[Elastic Beanstalk](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/concepts-roles-service.html)**
- AWS managed policies: [`AWSElasticBeanstalkEnhancedHealth`](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/health-enhanced.html), [`AWSElasticBeanstalkManagedUpdatesCustomerRolePolicy`](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/environment-platform-update-managed.html)

Begin by opening AWS Console → IAM → Roles → 
aws-elasticbeanstalk-service-role

Select "Roles" under "Access management."
You will see:
![](images/service_role_policy.png)
In order to add these properties you can select "Add permissions" and then select "Attach Policies".

Now in the search bar enter the folowing policy names and add them so it looks like the example image above.
- `AWSElasticBeanstalkEnhancedHealth`
- `AWSElasticBeanstalkManagedUpdatesCustomerRolePolicy`

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

11. **On the Configure updates, monitoring, and logging page (Step 5 - optional) set these under Environment variables/Enviornment properties:**

Leave the Monitoring, Updates, and Log sections unchanged.
Provide the following under the Environment variables/Enviornment properties section:

| Source | Key | Value |
|--------|-----|-------|
| Plain text | AWS_DEFAULT_REGION | us-east-1 |
| Plain text | STREAMLIT_SERVER_HEADLESS | true |
| Plain text | STREAMLIT_SERVER_ADDRESS | 0.0.0.0 |
| Plain text | STREAMLIT_SERVER_PORT | 8501 |
| Plain text | MCP_SERVER_ENABLED | true |
| Plain text | DEMO_USERNAME | demo |
| Plain text | DEMO_PASSWORD | quantum2025 |

**Note**: Demo credentials provide fallback authentication if Cognito is not configured.

**✅ Success**: App accessible at EB URL (5-10 minutes)

## Phase 3: Optional Enhancements

### Add Cognito Authentication (Optional)
**Run AFTER successful deployment:**
```bash
python setup/setup_cognito.py
```
**What this does:**
- Creates Cognito User Pool and App Client with admin-only signup
- Automatically sets EB environment variables
- Configures email verification
- Takes priority over demo credentials
- Enables bootstrap admin system for first-time setup

**Admin Authentication Setup:**
1. **First login**: Use existing account or create an initial account through the Amazon Cognito Console before accessing the bootstrap system
2. **Bootstrap admin**: Click "Become Admin" button (appears only when no admins exist)
3. **Sign out and login**: After becoming admin, sign out and log back in to refresh your session
4. **Admin panel**: Access user management in sidebar after becoming admin
5. **Create users and other admins**: Only admins can create new accounts with temporary passwords

### Add CloudFront SSL/CDN (Optional)
**Run AFTER successful deployment:**
```bash
python deployment/setup_cloudfront.py
```
**Benefits**: Free SSL, global CDN, 15-20 minutes deployment time  
**Access**: CloudFront URL will be displayed in terminal output and available in AWS Console → CloudFront → Distributions

## Security Measures Implemented

**Authentication & Access Control:**
- Multi-layer authentication with Amazon Cognito integration
- Secure credential management via AWS Secrets Manager
- IAM role-based access with least privilege principles

**Application Security:**
- Comprehensive input validation and sanitization
- Rate limiting protection (5 requests per 60 seconds)
- HTTP security headers for XSS and CSRF protection
- Command injection prevention with secure subprocess handling

**Monitoring & Compliance:**
- Security event audit logging
- CloudWatch monitoring integration
- SSL/TLS encryption via CloudFront

## Troubleshooting

**Deployment Issues:**
- Verify IAM roles and permissions are correctly configured
- Ensure all required files are included in deployment package
- Review application logs in Elastic Beanstalk console
- Check environment variables are properly set

**Model Access Issues:**
- Verify region settings match model availability

**Materials Project Integration:**
- Ensure API key is correctly stored in AWS Secrets Manager
- Test network connectivity to Materials Project API
- Verify MCP server status in application logs

**Authentication Problems:**
- For Cognito: Run setup script after successful EB deployment
- Verify User Pool creation in correct AWS region
- Check demo credentials if Cognito is not configured
- **Admin setup issues**: Ensure EC2 role has Cognito permissions (see Step 2A)
- **Bootstrap admin fails**: Check CloudWatch logs for IAM permission errors
- **User creation fails**: Verify admin has proper Cognito group membership

**CloudFront Deployment:**
- Allow 15-20 minutes for global distribution
- Test Elastic Beanstalk URL before CloudFront URL
- Verify SSL certificate provisioning status