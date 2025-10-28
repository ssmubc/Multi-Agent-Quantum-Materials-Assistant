# SSL Certificate Setup for Elastic Beanstalk

## Option 1: AWS Certificate Manager (Recommended)

### Step 1: Request SSL Certificate
1. **Go to AWS Certificate Manager (ACM)**
2. **Request a certificate**
3. **Domain names:**
   - Add your custom domain: `quantum-matter.yourdomain.com`
   - Or use wildcard: `*.yourdomain.com`
4. **Validation method:** DNS validation (recommended)
5. **Request certificate**

### Step 2: Validate Domain
1. **Add DNS records** provided by ACM to your domain's DNS
2. **Wait for validation** (can take a few minutes to hours)
3. **Certificate status** should show "Issued"

### Step 3: Configure Load Balancer
1. **Go to Elastic Beanstalk Console**
2. **Configuration** → **Load balancer**
3. **Listeners** → **Add listener**
4. **Settings:**
   - Port: `443`
   - Protocol: `HTTPS`
   - SSL certificate: Select your ACM certificate
5. **Apply changes**

### Step 4: Redirect HTTP to HTTPS
1. **Configuration** → **Load balancer**
2. **Modify HTTP listener (port 80)**
3. **Default action:** Redirect to HTTPS
4. **Apply changes**

## Option 2: Custom Domain Setup

### Step 1: Configure Route 53 (if using AWS DNS)
1. **Go to Route 53**
2. **Create hosted zone** for your domain
3. **Create A record:**
   - Name: `quantum-matter` (or subdomain)
   - Type: `A - IPv4 address`
   - Alias: Yes
   - Alias target: Your Beanstalk environment

### Step 2: Update Beanstalk Environment
1. **Configuration** → **Software**
2. **Environment properties:**
   - Add: `SERVER_NAME` = `quantum-matter.yourdomain.com`

## Option 3: Free SSL with Let's Encrypt (Advanced)

### Create .ebextensions/ssl.config:
```yaml
files:
  "/opt/elasticbeanstalk/hooks/appdeploy/post/99_install_certbot.sh":
    mode: "000755"
    owner: root
    group: root
    content: |
      #!/bin/bash
      # Install certbot for Let's Encrypt
      yum update -y
      yum install -y certbot python3-certbot-nginx
      
      # Get certificate (replace with your domain)
      certbot --nginx -d your-domain.com --non-interactive --agree-tos --email your-email@domain.com
      
      # Setup auto-renewal
      echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -

container_commands:
  01_install_ssl:
    command: "chmod +x /opt/elasticbeanstalk/hooks/appdeploy/post/99_install_certbot.sh"
```

## Testing SSL Setup

### 1. Check Certificate
- Visit: `https://your-domain.com`
- Look for green padlock in browser
- Check certificate details

### 2. Test SSL Rating
- Use: https://www.ssllabs.com/ssltest/
- Should get A or A+ rating

### 3. Verify Redirect
- Visit: `http://your-domain.com`
- Should automatically redirect to `https://`

## Cost Considerations

- **ACM Certificate:** Free for AWS resources
- **Route 53 Hosted Zone:** ~$0.50/month
- **Custom Domain:** Domain registration cost
- **Load Balancer:** Already included in Beanstalk

## Security Headers (Optional)

Add to your Streamlit app for better security:

```python
# Add to app.py
st.markdown("""
<script>
// Security headers via meta tags
document.head.innerHTML += '<meta http-equiv="Strict-Transport-Security" content="max-age=31536000; includeSubDomains">';
document.head.innerHTML += '<meta http-equiv="X-Content-Type-Options" content="nosniff">';
document.head.innerHTML += '<meta http-equiv="X-Frame-Options" content="DENY">';
</script>
""", unsafe_allow_html=True)
```