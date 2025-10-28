# AWS Cognito Setup Guide

## Overview
This guide shows how to set up AWS Cognito authentication for the Quantum Matter LLM Testing Platform.

## Prerequisites
- AWS Account with appropriate permissions
- AWS CLI configured
- Streamlit app deployed on AWS Elastic Beanstalk

## Step 1: Create Cognito User Pool

### Using AWS Console:
1. Go to AWS Cognito console
2. Click "Create user pool"
3. Configure sign-in options:
   - ✅ Username
   - ✅ Email
4. Configure security requirements:
   - Password policy: Default
   - MFA: Optional (recommended: SMS or TOTP)
5. Configure sign-up experience:
   - ✅ Enable self-registration
   - ✅ Email verification
6. Configure message delivery:
   - Email provider: Cognito (for testing) or SES (for production)
7. Integrate your app:
   - User pool name: `quantum-matter-users`
   - App client name: `quantum-matter-app`
   - ✅ Generate a client secret
8. Review and create

### Using AWS CLI:
```bash
# Create user pool
aws cognito-idp create-user-pool \
    --pool-name quantum-matter-users \
    --policies PasswordPolicy='{MinimumLength=8,RequireUppercase=true,RequireLowercase=true,RequireNumbers=true,RequireSymbols=false}' \
    --auto-verified-attributes email \
    --username-attributes email

# Create app client
aws cognito-idp create-user-pool-client \
    --user-pool-id <USER_POOL_ID> \
    --client-name quantum-matter-app \
    --generate-secret \
    --explicit-auth-flows ADMIN_NO_SRP_AUTH USER_PASSWORD_AUTH
```

## Step 2: Configure Environment Variables

### For Local Development:
Create `.env` file:
```bash
COGNITO_POOL_ID=us-east-1_XXXXXXXXX
COGNITO_APP_CLIENT_ID=your_app_client_id
COGNITO_APP_CLIENT_SECRET=your_app_client_secret
```

### For Elastic Beanstalk:
Add environment variables in EB configuration:

```bash
# Using EB CLI
eb setenv COGNITO_POOL_ID=us-east-1_XXXXXXXXX
eb setenv COGNITO_APP_CLIENT_ID=your_app_client_id
eb setenv COGNITO_APP_CLIENT_SECRET=your_app_client_secret
```

Or via AWS Console:
1. Go to Elastic Beanstalk console
2. Select your application
3. Go to Configuration → Software
4. Add environment properties:
   - `COGNITO_POOL_ID`: Your user pool ID
   - `COGNITO_APP_CLIENT_ID`: Your app client ID
   - `COGNITO_APP_CLIENT_SECRET`: Your app client secret

## Step 3: Create Initial Users

### Using AWS Console:
1. Go to Cognito User Pool
2. Click "Users" tab
3. Click "Create user"
4. Fill in user details:
   - Username: `admin` or email
   - Email: user's email
   - Temporary password: Generate or set custom
   - ✅ Send invitation email

### Using AWS CLI:
```bash
# Create user
aws cognito-idp admin-create-user \
    --user-pool-id <USER_POOL_ID> \
    --username admin \
    --user-attributes Name=email,Value=admin@example.com \
    --temporary-password TempPass123! \
    --message-action SEND
```

## Step 4: Update Deployment

### Option A: Use Cognito Version
```bash
# Deploy with Cognito authentication
cp app_cognito.py app.py
eb deploy
```

### Option B: Keep Both Versions
Deploy both files and use different entry points:
- `app.py` - Simple password authentication
- `app_cognito.py` - Cognito authentication

## Step 5: Test Authentication

1. Access your deployed app
2. You should see Cognito login form
3. Login with created user credentials
4. First login will require password change
5. After successful login, you'll have full access to AWS models

## Configuration Options

### User Pool Settings:
- **Sign-in options**: Username, Email, Phone
- **Password policy**: Customize strength requirements
- **MFA**: SMS, TOTP, or disabled
- **Account recovery**: Email or SMS
- **Email verification**: Required for security

### App Client Settings:
- **Auth flows**: USER_PASSWORD_AUTH, USER_SRP_AUTH
- **Client secret**: Required for server-side apps
- **Token expiration**: Access (1 hour), Refresh (30 days)
- **Scopes**: openid, email, profile

## Security Best Practices

1. **Enable MFA** for production users
2. **Use strong password policies**
3. **Enable email verification**
4. **Set appropriate token expiration**
5. **Monitor failed login attempts**
6. **Use HTTPS only** (handled by Elastic Beanstalk)
7. **Rotate client secrets** regularly

## Troubleshooting

### Common Issues:

**"Cognito not configured" error:**
- Check environment variables are set correctly
- Verify user pool and app client exist
- Ensure app client has correct auth flows enabled

**Login fails:**
- Check username/password
- Verify user exists and is confirmed
- Check if temporary password needs to be changed

**"Access denied" errors:**
- Verify IAM permissions for Cognito
- Check app client configuration
- Ensure user pool is in correct region

### Debug Commands:
```bash
# Check user pool details
aws cognito-idp describe-user-pool --user-pool-id <USER_POOL_ID>

# List users
aws cognito-idp list-users --user-pool-id <USER_POOL_ID>

# Check app client
aws cognito-idp describe-user-pool-client \
    --user-pool-id <USER_POOL_ID> \
    --client-id <CLIENT_ID>
```

## Cost Considerations

### Cognito Pricing (as of 2024):
- **Free tier**: 50,000 MAUs (Monthly Active Users)
- **Paid tier**: $0.0055 per MAU after free tier
- **SMS MFA**: $0.05 per SMS
- **Email**: Free with Cognito, or use SES for custom emails

### Recommendations:
- Start with free tier for testing
- Monitor MAU usage
- Use email verification instead of SMS when possible
- Consider SES for production email delivery

## Migration from Simple Auth

To migrate from simple password authentication:

1. **Deploy Cognito version** alongside existing app
2. **Create users** in Cognito for existing users
3. **Test thoroughly** with new authentication
4. **Switch traffic** to Cognito version
5. **Remove old authentication** code

## Support

For issues with Cognito setup:
1. Check AWS Cognito documentation
2. Review CloudWatch logs for authentication errors
3. Test with AWS CLI commands
4. Contact AWS support for complex issues