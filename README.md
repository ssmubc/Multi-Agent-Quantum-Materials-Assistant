# Quantum Matter LLM Testing Platform

## Credits

This application was architected and developed was developed by [Sharon Marfatia](https://www.linkedin.com/in/sharon-cs/). Thanks to the UBC Cloud Innovation Centre Technical and Project Management teams for their guidance and support.

## About
A Streamlit application for testing and comparing different Large Language Models (LLMs) for quantum computing and materials science applications.


## Features

- **6 LLM Models Support:**
  - **Nova Pro** (us-east-1) - Amazon's latest multimodal model
  - **Llama 4 Scout 17B** (us-east-1) - Meta's latest instruction-tuned model  
  - **Llama 3 70B** (us-west-2) - Meta's powerful 70B parameter model
  - **OpenAI GPT OSS** (us-west-2) - OpenAI's open-source model
  - **Qwen 3-32B** (us-east-1) - Alibaba's advanced reasoning model
  - **DeepSeek R1** (us-east-1) - DeepSeek's reasoning-focused model

- **Materials Project Integration:**
  - Automatic material property lookup
  - Real molecular geometries
  - Band gap and formation energy data
  - AWS Secrets Manager integration for API keys

- **Quantum Computing Code Generation:**
  - VQE ansatz generation (UCCSD, Hardware-Efficient)
  - Qiskit circuit construction
  - Materials Hamiltonian modeling
  - Multiple qubit mapping strategies

## Prerequisites

### AWS Configuration
You need AWS credentials configured with access to Amazon Bedrock. The models are region-specific:

- **us-east-1**: Nova Pro, Llama 4 Scout
- **us-west-2**: Llama 3 70B, OpenAI GPT OSS

### Required IAM Permissions
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

### Materials Project API Key
Get your free API key from [Materials Project](https://materialsproject.org/) and either:
1. Store it in AWS Secrets Manager (recommended)
2. Enter it manually in the app interface

## Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd Quantum_Matter_Streamlit_App
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure AWS credentials:**
```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1

# Option 3: AWS Profile
export AWS_PROFILE=your_profile_name
```

4. **Store Materials Project API Key (Optional):**
```python
from utils.secrets_manager import store_mp_api_key
store_mp_api_key("your_mp_api_key_here")
```

## Usage

### Local Development

1. **Quick Start (using helper script):**
```bash
# Option 1: Use the local development script
python run_local.py
```

2. **Manual Start:**
```bash
# Option 2: Start Streamlit directly
streamlit run app.py
```

3. **Local Environment Variables (Optional):**
   The `run_local.py` script sets these defaults if not already configured:
   ```bash
   # Override defaults by setting your own:
   export AWS_PROFILE=your-aws-profile-name
   export DEMO_USERNAME=your-username  # For local auth
   export DEMO_PASSWORD=your-password  # For local auth
   export MP_API_KEY=your-materials-project-key
   ```

4. **Configure the application:**
   - Verify AWS credentials are detected (uses AWS SSO/profiles for local dev)
   - Set up Materials Project API key
   - Check model status in sidebar

5. **Test the models:**
   - Select a model from the dropdown
   - Enter your quantum/materials science question
   - Adjust parameters if needed
   - Generate and compare responses

### Production Deployment

For Elastic Beanstalk deployment, the application automatically uses IAM instance profiles - **no hardcoded credentials or ARNs required**. The app dynamically detects available AWS authentication at runtime and complies with enterprise security policies that prohibit long-term credential storage.

## Example Queries

### Quantum Computing
```
Generate a VQE ansatz for H2 molecule using UCCSD with Jordan-Wigner mapping
Create a hardware-efficient ansatz for LiH with 3 layers and circular entanglement
Build an initial state preparation circuit for a 4-qubit system
```

### Materials Science
```
Analyze the electronic properties of TiO2 and generate a Hubbard model
Create a quantum simulation for graphene using Materials Project data
Generate VQE code for mp-149 (silicon) with active space reduction
```

## Architecture

```
app.py                          # Main Streamlit application
├── models/
│   ├── base_model.py          # Base class for all models
│   ├── nova_pro_model.py      # Nova Pro implementation
│   ├── llama4_model.py        # Llama 4 Scout implementation
│   ├── llama3_model.py        # Llama 3 70B implementation
│   └── openai_model.py        # OpenAI GPT implementation
└── utils/
    ├── materials_project_agent.py  # Materials Project API client
    └── secrets_manager.py          # AWS Secrets Manager utilities
```

## Model Configurations

| Model | Region | Model ID | Use Case |
|-------|--------|----------|----------|
| Nova Pro | us-east-1 | `amazon.nova-pro-v1:0` | Multimodal, latest features |
| Llama 4 Scout | us-east-1 | `us.meta.llama4-scout-17b-instruct-v1:0` | Fast, efficient |
| Llama 3 70B | us-west-2 | `meta.llama3-70b-instruct-v1:0` | High quality, detailed |
| OpenAI GPT | us-west-2 | `openai.gpt-oss-20b-1:0` | Alternative approach |
| Qwen 3-32B | us-east-1 | `qwen.qwen3-32b-v1:0` | Advanced reasoning, structured output |
| DeepSeek R1 | us-east-1 | `us.deepseek.r1-v1:0` | Reasoning and problem-solving |

## Troubleshooting

### AWS Credentials Issues
- Ensure your AWS credentials have Bedrock access
- Check that you're using the correct regions for each model
- Verify IAM permissions include `bedrock:InvokeModel`

### Model Access Issues
- Some models may require explicit access requests in AWS Console
- Check Bedrock model access in your AWS account
- Ensure you're in the correct region for each model

### Materials Project API Issues
- Verify your API key is valid at materialsproject.org
- Check network connectivity to Materials Project servers
- Use dummy data mode if API is unavailable

### Dependencies Issues
```bash
# If you encounter package conflicts, create a virtual environment
python -m venv quantum_env
source quantum_env/bin/activate  # On Windows: quantum_env\Scripts\activate
pip install -r requirements.txt
```

## Security Best Practices

1. **Never hardcode credentials** - Use AWS IAM roles or environment variables
2. **Use Secrets Manager** - Store API keys securely in AWS Secrets Manager
3. **Least privilege** - Grant only necessary IAM permissions
4. **Monitor usage** - Track Bedrock API calls and costs
5. **Rotate keys** - Regularly rotate API keys and access credentials

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## AWS Elastic Beanstalk Deployment

For web deployment without requiring users to clone the repository:

1. **See DEPLOYMENT.md** for complete deployment guide
2. **Deploy to AWS Elastic Beanstalk** for shared web access
3. **Users access via URL** - no setup required
4. **Auto-scaling** and load balancing included

### Quick Deploy
```bash
# 1. Install EB CLI
pip install awsebcli

# 2. Initialize and deploy
eb init quantum-matter-app --platform docker --region us-east-1
eb create quantum-matter-env --instance-types t3.medium
eb deploy

# 3. Configure SSL Certificate (Optional)
eb setenv SSL_CERT_ARN=your_certificate_arn_here

# 4. Get URL
eb status
```

### SSL/HTTPS Configuration

To enable HTTPS for your deployment:

1. **Create SSL Certificate in AWS Certificate Manager:**
   - Go to AWS Console → Certificate Manager
   - Request a public certificate for your domain
   - Complete domain validation

2. **Configure SSL in Elastic Beanstalk:**
   ```bash
   # Set the certificate ARN as environment variable
   eb setenv SSL_CERT_ARN=arn:aws:acm:region:account:certificate/cert-id
   
   # Deploy the configuration
   eb deploy
   ```

3. **Verify HTTPS Access:**
   - Your app will be available at both HTTP and HTTPS URLs
   - HTTPS: `https://your-app-name.elasticbeanstalk.com`
   - HTTP: `http://your-app-name.elasticbeanstalk.com`

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review AWS Bedrock documentation
3. Check Materials Project API documentation
4. See DEPLOYMENT.md for deployment issues
5. Open an issue in the repository