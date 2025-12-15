# Security Guide

## Overview

The application uses AWS cloud services with security features including:
- AWS Cognito authentication
- Encrypted data storage and transmission
- Input validation and rate limiting
- Basic audit logging

---

## 1. Authentication

### AWS Cognito
- Email verification required for account creation
- Password policies enforced (8+ chars, upper/lower/numbers)
- JWT token validation for session management
- 3-tab interface: Sign In, Sign Up, Email Verification

### Demo Mode (Local Development)
- **Fallback authentication** when Cognito is not configured
- **Credentials**: Username: `demo`, Password: `quantum2025`
- **Local testing only** - not used in AWS deployment

---

## 2. Data Protection

### Secrets Management
- **Materials Project API Key**: Stored securely in AWS Secrets Manager
- **AWS Credentials**: Managed through IAM roles and SSO
- **Cognito Configuration**: Retrieved from Parameter Store with validation
- **No hardcoded secrets** in application code

### Configuration Security
- Environment validation at startup
- Parameter Store integration for Cognito config
- Configuration error handling

### Encryption
**Data at Rest:**
- AWS Secrets Manager uses KMS encryption
- EBS volumes encrypted with AWS managed keys

**Data in Transit:**
- HTTPS/TLS encryption for all web traffic
- SSL certificates automatically managed by CloudFront
- Secure API calls to AWS services

---

## 3. Application Security

### Input Validation
- Chemical formulas validated (regex pattern matching)
- User queries sanitized (HTML/XML tag removal)
- File uploads validated (path traversal protection)
- Python executables validated (regex pattern matching)
- Working directories validated (path traversal protection)

### Rate Limiting
- **Application Level**: 10 requests per 60 seconds per user session
- **Infrastructure Level**: AWS WAF rate limiting (400 requests/minute per IP)
- Session-based tracking using correlation IDs
- Automatic blocking with TooManyRequestsError
- CloudFront DDoS protection

### Security Headers
- **XSS Protection**: Prevents cross-site scripting attacks
- **Content Security Policy**: Controls resource loading
- **Frame Options**: Prevents clickjacking attacks

### Code Security
- Generated code validation (checks for dangerous imports/functions)
- Security warnings added to code displays
- Detects prohibited operations (file system, network, eval/exec)
- Provides safe code guidelines

---

## 4. AWS Service Security

### Amazon Bedrock (LLM Models)
- IAM permissions control access to 8 models
- Basic request logging for model interactions

### Amazon Braket (Quantum Computing)
- Access to quantum simulators and devices
- Basic circuit validation

### Materials Project Integration
- API key stored in AWS Secrets Manager
- Input validation for chemical formulas

---

## 5. Infrastructure Security

### AWS Elastic Beanstalk
- **Automatic security updates** for the underlying platform
- **Isolated environments** for different deployment stages
- **Health monitoring** tracks application and infrastructure status

### CloudFront CDN + AWS WAF
- **Global DDoS protection** through AWS Shield
- **Automatic SSL certificates** for HTTPS encryption
- **AWS WAF Web Application Firewall** with enterprise-grade protection:
  - **XSS Protection**: Blocks cross-site scripting attacks immediately
  - **SQL Injection Protection**: Prevents database manipulation attempts
  - **OWASP Top 10 Protection**: Comprehensive coverage of web vulnerabilities
  - **Rate Limiting**: 400 requests per minute per IP address
  - **Known Bad Inputs**: Blocks malicious patterns and payloads
- **Edge security** filters malicious traffic before it reaches your application
- **CloudFront Pro tier** includes 25 WAF rules at no extra cost

---

## 6. Security Features Implemented

### ✅ What's Protected
- User authentication with AWS Cognito and JWT validation
- API keys stored in AWS Secrets Manager
- Web traffic encrypted with HTTPS/TLS
- User inputs validated and sanitized
- Generated code validated for security risks
- Rate limiting prevents abuse
- Security headers protect against common attacks
- Basic audit logging for authentication and model usage
- Configuration validation prevents injection attacks

### ✅ AWS Security Services Used
- **IAM roles** for secure service access
- **Secrets Manager** for credential storage
- **CloudFront Pro** for global CDN and DDoS protection
- **AWS WAF** for web application firewall protection
- **Elastic Beanstalk** managed security updates

---

## 7. User Security Tips

### For Account Security
- Use a **strong, unique password** for your account
- **Verify your email** during registration
- **Log out** when finished using the application
- **Report suspicious activity** if you notice anything unusual

### For Data Protection
- **Don't share** your login credentials
- **Use secure networks** when accessing the application
- **Keep your browser updated** for the latest security features

---

## 8. AWS WAF Protection Details

### Enterprise Security Features
The application uses **AWS WAF (Web Application Firewall)** integrated with CloudFront Pro to provide military-grade security:

**Core Protections (Always Active):**
- **Cross-Site Scripting (XSS)**: Blocks malicious scripts injected into web pages
- **SQL Injection**: Prevents unauthorized database access attempts
- **Command Injection**: Stops attempts to execute system commands
- **Path Traversal**: Blocks attempts to access unauthorized files
- **Remote File Inclusion**: Prevents loading of malicious external files
- **CSRF Protection**: Guards against cross-site request forgery

**Rate Limiting:**
- **Limit**: 400 requests per minute per IP address (2000 per 5-minute window)
- **Mode**: Monitor mode (logs violations, allows traffic) - can be switched to block mode
- **Scope**: Per IP address tracking
- **Purpose**: Prevents abuse while supporting ~80 concurrent users

**Managed Rule Sets:**
- **AWSManagedRulesCommonRuleSet**: OWASP Top 10 and common attack patterns
- **AWSManagedRulesKnownBadInputsRuleSet**: Known malicious payloads and signatures
- **Automatic Updates**: AWS continuously updates rules for new threats

### WAF Management

**Monitoring:**
- View blocked requests in AWS WAF console
- CloudWatch metrics for attack patterns
- Real-time security dashboards

**Rate Limiting Control:**
1. Go to **AWS WAF console**
2. Find your Web ACL (quantum-matter-waf-*)
3. Locate **RateLimitRule**
4. Change Action from **Count** (monitor) to **Block** (enforce)

**Security Benefits:**
- **Zero-day protection**: Blocks unknown attack patterns
- **Global threat intelligence**: AWS-managed rule updates
- **Performance**: Filtering at edge locations (minimal latency)
- **Cost-effective**: 25 rules included with CloudFront Pro

---

## 9. Getting Help

If you have security concerns or questions:

1. **Check the logs** in the application for error messages
2. **Review the troubleshooting guide** in the deployment documentation
3. **Contact support** if you suspect a security issue
4. **Report vulnerabilities** through appropriate channels

---

## Security Implementation Summary

This application implements security features including:
- AWS Cognito authentication with JWT validation
- Input validation and sanitization
- Generated code security scanning
- Session-based rate limiting
- Configuration validation
- Basic audit logging
- Path traversal and injection attack prevention
- AWS security services (Cognito, Secrets Manager, CloudFront)

Security features are implemented in the codebase.
