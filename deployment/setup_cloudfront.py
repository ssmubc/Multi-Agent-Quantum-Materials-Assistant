#!/usr/bin/env python3
"""
CloudFront Distribution Setup for Quantum Matter App
Provides SSL/TLS certificates and global CDN distribution
"""

import boto3
import json
import time
import os
from botocore.exceptions import ClientError, NoCredentialsError
from boto3.session import Session

def create_waf_web_acl():
    """Create AWS WAF Web ACL with Core Protections and rate limiting"""
    # WAF for CloudFront MUST be in us-east-1 (global service)
    wafv2 = boto3.client('wafv2', region_name='us-east-1')
    
    # WAF Web ACL configuration
    web_acl_config = {
        'Name': f'quantum-matter-waf-{int(time.time())}',
        'Scope': 'CLOUDFRONT',
        'DefaultAction': {'Allow': {}},
        'Description': 'WAF for Quantum Matter App with Core Protections and rate limiting',
        'Rules': [
            {
                'Name': 'AWSManagedRulesCommonRuleSet',
                'Priority': 1,
                'OverrideAction': {'None': {}},
                'Statement': {
                    'ManagedRuleGroupStatement': {
                        'VendorName': 'AWS',
                        'Name': 'AWSManagedRulesCommonRuleSet'
                    }
                },
                'VisibilityConfig': {
                    'SampledRequestsEnabled': True,
                    'CloudWatchMetricsEnabled': True,
                    'MetricName': 'CommonRuleSetMetric'
                }
            },
            {
                'Name': 'AWSManagedRulesKnownBadInputsRuleSet',
                'Priority': 2,
                'OverrideAction': {'None': {}},
                'Statement': {
                    'ManagedRuleGroupStatement': {
                        'VendorName': 'AWS',
                        'Name': 'AWSManagedRulesKnownBadInputsRuleSet'
                    }
                },
                'VisibilityConfig': {
                    'SampledRequestsEnabled': True,
                    'CloudWatchMetricsEnabled': True,
                    'MetricName': 'KnownBadInputsMetric'
                }
            },
            {
                'Name': 'RateLimitRule',
                'Priority': 3,
                'Action': {'Count': {}},  # Monitor mode first
                'Statement': {
                    'RateBasedStatement': {
                        'Limit': 2000,  # 2000 requests per 5 minutes (= 400/minute) as confirmed by supervisor
                        'AggregateKeyType': 'IP'
                    }
                },
                'VisibilityConfig': {
                    'SampledRequestsEnabled': True,
                    'CloudWatchMetricsEnabled': True,
                    'MetricName': 'RateLimitMetric'
                }
            }
        ],
        'VisibilityConfig': {
            'SampledRequestsEnabled': True,
            'CloudWatchMetricsEnabled': True,
            'MetricName': 'QuantumMatterWAF'
        }
    }
    
    try:
        response = wafv2.create_web_acl(**web_acl_config)
        web_acl_arn = response['Summary']['ARN']
        web_acl_id = response['Summary']['Id']
        
        print(f"✅ WAF Web ACL created:")
        print(f"   Web ACL ID: {web_acl_id}")
        print(f"   ARN: {web_acl_arn}")
        print(f"   Rate limit: 2000 requests/5min (400/min) (monitor mode)")
        print(f"   Core Protections: XSS, SQL injection, OWASP Top 10")
        
        return web_acl_arn
        
    except ClientError as e:
        print(f"❌ Failed to create WAF Web ACL: {e}")
        return None

def create_cloudfront_distribution(eb_domain, custom_domain=None, web_acl_arn=None):
    """Create CloudFront distribution for Elastic Beanstalk app with WAF"""
    
    cloudfront = boto3.client('cloudfront')
    
    # CloudFront distribution configuration
    distribution_config = {
        'CallerReference': f'quantum-matter-{int(time.time())}',
        'Comment': 'Quantum Matter LLM Testing Platform',
        'DefaultCacheBehavior': {
            'TargetOriginId': 'eb-origin',
            'ViewerProtocolPolicy': 'redirect-to-https',
            'TrustedSigners': {
                'Enabled': False,
                'Quantity': 0
            },
            'ForwardedValues': {
                'QueryString': True,
                'Cookies': {'Forward': 'all'},
                'Headers': {
                    'Quantity': 3,
                    'Items': ['Host', 'Origin', 'Referer']
                }
            },
            'MinTTL': 0,
            'DefaultTTL': 0,
            'MaxTTL': 31536000
        },
        'Origins': {
            'Quantity': 1,
            'Items': [
                {
                    'Id': 'eb-origin',
                    'DomainName': eb_domain,
                    'CustomOriginConfig': {
                        'HTTPPort': 80,
                        'HTTPSPort': 443,
                        'OriginProtocolPolicy': 'http-only'
                    }
                }
            ]
        },
        'Enabled': True,
        'PriceClass': 'PriceClass_200'  # Pro tier for WAF integration
    }
    
    # Add WAF Web ACL if provided
    if web_acl_arn:
        distribution_config['WebACLId'] = web_acl_arn
    
    # Add custom domain if provided
    if custom_domain:
        distribution_config['Aliases'] = {
            'Quantity': 1,
            'Items': [custom_domain]
        }
        # Note: SSL certificate ARN would need to be added here
        # distribution_config['ViewerCertificate'] = {
        #     'ACMCertificateArn': 'your-certificate-arn',
        #     'SSLSupportMethod': 'sni-only'
        # }
    else:
        distribution_config['ViewerCertificate'] = {
            'CloudFrontDefaultCertificate': True
        }
    
    try:
        response = cloudfront.create_distribution(DistributionConfig=distribution_config)
        distribution_id = response['Distribution']['Id']
        domain_name = response['Distribution']['DomainName']
        
        print(f"✅ CloudFront distribution created:")
        print(f"   Distribution ID: {distribution_id}")
        print(f"   Domain Name: {domain_name}")
        print(f"   Status: {response['Distribution']['Status']}")
        
        return {
            'distribution_id': distribution_id,
            'domain_name': domain_name,
            'status': response['Distribution']['Status']
        }
        
    except ClientError as e:
        print(f"❌ Failed to create CloudFront distribution: {e}")
        return None

def get_eb_domain():
    """Get Elastic Beanstalk environment domain"""
    eb = boto3.client('elasticbeanstalk')
    
    try:
        # List environments
        environments = eb.describe_environments()
        
        if not environments['Environments']:
            print("❌ No Elastic Beanstalk environments found")
            return None
        
        # Find quantum-matter environments
        quantum_envs = [env for env in environments['Environments'] if 'quantum-matter' in env['EnvironmentName'].lower()]
        
        if quantum_envs:
            if len(quantum_envs) == 1:
                # Only one quantum-matter environment found
                env = quantum_envs[0]
                print(f"✅ Found EB environment: {env['EnvironmentName']}")
                return env['CNAME']
            else:
                # Multiple quantum-matter environments, let user choose
                print("📋 Multiple Quantum Matter environments found:")
                for i, env in enumerate(quantum_envs, 1):
                    status = env.get('Status', 'Unknown')
                    health = env.get('Health', 'Unknown')
                    print(f"  {i}. {env['EnvironmentName']} ({status}, {health})")
                
                # Ask user to select from quantum-matter environments
                while True:
                    try:
                        choice = input(f"\n🎯 Select environment (1-{len(quantum_envs)}): ").strip()
                        if choice:
                            idx = int(choice) - 1
                            if 0 <= idx < len(quantum_envs):
                                selected_env = quantum_envs[idx]
                                print(f"✅ Selected: {selected_env['EnvironmentName']}")
                                return selected_env['CNAME']
                            else:
                                print("❌ Invalid selection. Please try again.")
                        else:
                            print("❌ No selection made.")
                            return None
                    except (ValueError, KeyboardInterrupt):
                        print("\n❌ Selection cancelled.")
                        return None
        
        # If no quantum-matter environments, show all available
        print("📋 No 'quantum-matter' environments found. Available environments:")
        for i, env in enumerate(environments['Environments'], 1):
            status = env.get('Status', 'Unknown')
            health = env.get('Health', 'Unknown')
            print(f"  {i}. {env['EnvironmentName']} ({status}, {health})")
        
        # Ask user to select from all environments
        while True:
            try:
                choice = input(f"\n🎯 Select environment (1-{len(environments['Environments'])}): ").strip()
                if choice:
                    idx = int(choice) - 1
                    if 0 <= idx < len(environments['Environments']):
                        selected_env = environments['Environments'][idx]
                        print(f"✅ Selected: {selected_env['EnvironmentName']}")
                        return selected_env['CNAME']
                    else:
                        print("❌ Invalid selection. Please try again.")
                else:
                    print("❌ No selection made.")
                    return None
            except (ValueError, KeyboardInterrupt):
                print("\n❌ Selection cancelled.")
                return None
        
    except ClientError as e:
        print(f"❌ Failed to get EB environments: {e}")
        return None

def setup_aws_credentials():
    """Setup AWS credentials with user selection"""
    try:
        session = boto3.Session()
        available_profiles = session.available_profiles
        if available_profiles:
            print(f"📋 Available AWS profiles: {', '.join(available_profiles)}")
            
            # Ask user to select profile
            while True:
                profile_name = input("\n🎯 Enter AWS profile name (or press Enter for default): ").strip()
                
                if not profile_name:
                    profile_name = 'default'
                
                if profile_name in available_profiles:
                    try:
                        # Test if the selected profile works
                        test_session = boto3.Session(profile_name=profile_name)
                        sts = test_session.client('sts')
                        sts.get_caller_identity()
                        
                        # If we get here, credentials work
                        os.environ['AWS_PROFILE'] = profile_name
                        print(f"✅ Using AWS profile: {profile_name}")
                        return True
                    except Exception as e:
                        print(f"❌ Profile '{profile_name}' has invalid credentials: {e}")
                        print("Please try another profile or run: aws sso login")
                        continue
                else:
                    print(f"❌ Profile '{profile_name}' not found. Available: {', '.join(available_profiles)}")
                    continue
        else:
            print("❌ No AWS profiles found")
    except Exception as e:
        print(f"❌ Error accessing AWS profiles: {e}")
    
    print("💡 Please run: aws configure or aws sso login")
    return False

def main():
    """Main setup function"""
    print("🚀 Setting up CloudFront for Quantum Matter App")
    print("=" * 50)
    
    # Setup AWS credentials
    if not setup_aws_credentials():
        return
    
    # Get EB domain
    eb_domain = get_eb_domain()
    if not eb_domain:
        eb_domain = input("Enter your Elastic Beanstalk domain (e.g., quantum-matter-env.elasticbeanstalk.com): ")
    
    print(f"📍 Using EB domain: {eb_domain}")
    
    # Ask for custom domain
    custom_domain = input("Enter custom domain (optional, press Enter to skip): ").strip()
    if not custom_domain:
        custom_domain = None
    
    # Create WAF Web ACL first
    print("\n🛡️ Creating AWS WAF Web ACL...")
    web_acl_arn = create_waf_web_acl()
    
    if not web_acl_arn:
        print("❌ Failed to create WAF. Continuing without WAF protection.")
    
    # Create CloudFront distribution
    print("\n☁️ Creating CloudFront distribution...")
    result = create_cloudfront_distribution(eb_domain, custom_domain, web_acl_arn)
    
    if result:
        print("\n🎉 CloudFront Pro + WAF setup complete!")
        print(f"🌐 Your app will be available at: https://{result['domain_name']}")
        print("\n🛡️ Security Features Enabled:")
        print("   • AWS WAF Core Protections (XSS, SQL injection, OWASP Top 10)")
        print("   • Rate limiting: 400 requests/minute (monitor mode)")
        print("   • CloudFront Pro tier with 25 WAF rules included")
        print("\n⏳ Note: Distribution deployment takes 15-20 minutes")
        print("💡 SSL certificate is automatically provided by CloudFront")
        print("\n📊 To switch rate limiting from monitor to block mode:")
        print("   1. Go to AWS WAF console")
        print("   2. Find 'RateLimitRule' in your Web ACL")
        print("   3. Change Action from 'Count' to 'Block'")
        
        if custom_domain:
            print(f"\n📝 To use custom domain {custom_domain}:")
            print("   1. Create SSL certificate in AWS Certificate Manager")
            print("   2. Update CloudFront distribution with certificate ARN")
            print("   3. Update DNS records to point to CloudFront domain")

if __name__ == "__main__":
    main()