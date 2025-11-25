# Quantum Matter LLM Testing Platform

This project harnesses generative AI on AWS Cloud Infrastructure to enable quantum computing and materials science research through intelligent Large Language Model interactions. The platform integrates Materials Project data, Strands agentic workflows, and Amazon Braket quantum computing services to create comprehensive quantum simulations, generate VQE circuits, and analyze material properties with real-time MCP (Model Context Protocol) integration for enhanced accuracy and reliability.

| Index | Description |
|-------|-------------|
| [High Level Architecture](docs/architecture.md) | High level overview illustrating component interactions |
| [Deployment Guide](docs/deployment-guide.md) | How to deploy the project to AWS Elastic Beanstalk |
| [User Guide](docs/user-guide.md) | The working solution and interface guide |
| [Agentic Architecture](docs/agentic-architecture.md) | Detailed documentation on Strands agentic workflows |
| [Braket Integration](docs/braket-integration.md) | Amazon Braket quantum computing integration |
| [Troubleshooting Guide](#troubleshooting) | Documentation on how to troubleshoot common issues |
| [Credits](#credits) | Meet the team behind the solution |
| [License](#license) | License details |

## High-Level Architecture

The platform utilizes a sophisticated multi-agent architecture combining AWS Bedrock LLMs, Materials Project MCP servers, and Strands agentic workflows for intelligent quantum materials analysis.


## Features

- **8 Advanced LLM Models:**
  - **Nova Pro** (us-east-1) - Amazon's latest multimodal model
  - **Llama 4 Scout 17B** (us-east-1) - Meta's latest instruction-tuned model  
  - **Llama 3 70B** (us-west-2) - Meta's powerful 70B parameter model
  - **Claude Sonnet 4.5** (us-east-1) - Anthropic's advanced reasoning model
  - **Claude Opus 4.1** (us-east-1) - Anthropic's most capable model
  - **OpenAI OSS-120B** (us-west-2) - OpenAI's open-source model
  - **Qwen 3-32B** (us-east-1) - Alibaba's advanced reasoning model
  - **DeepSeek R1** (us-east-1) - DeepSeek's reasoning-focused model

- **Intelligent Materials Project Integration:**
  - Real-time MCP server with auto-recovery
  - Automatic material property lookup
  - Real molecular geometries and crystal structures
  - Band gap and formation energy data
  - AWS Secrets Manager integration for secure API keys

- **Advanced Quantum Computing Capabilities:**
  - VQE ansatz generation (UCCSD, Hardware-Efficient)
  - Qiskit and Amazon Braket circuit construction
  - Materials Hamiltonian modeling with DFT parameters
  - Multiple qubit mapping strategies (Jordan-Wigner, Parity)
  - Moire bilayer structure generation
  - 3D crystal structure visualization

- **Strands Agentic Workflows:**
  - Multi-material comparison analysis
  - Intelligent workflow dispatch
  - DFT parameter extraction
  - Iterative problem solving
  - POSCAR structure analysis

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
Get your free API key from [Materials Project](https://materialsproject.org/) and store it using the setup utility:

```bash
# Recommended: Use setup utility to store API key securely
python setup/setup_secrets.py
```

Alternatively, enter it manually in the app interface.

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
# Configure AWS SSO (recommended)
aws configure sso

# Set your AWS profile
export AWS_PROFILE=your_sso_profile_name
```

4. **Configure API Keys and Dependencies:**
```bash
# Store Materials Project API key (recommended)
python setup/setup_secrets.py

# Install Braket integration (optional, for quantum circuit features)
python setup/install_braket.py
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

## Directories

```
├── agents/
│   ├── strands_supervisor.py      # Main Strands supervisor with intelligent routing
│   ├── strands_agentic_loop.py    # Multi-material iterative analysis
│   ├── strands_dft_agent.py       # DFT parameter extraction
│   └── strands_structure_agent.py # POSCAR and structure analysis
├── config/
│   ├── auth_module.py             # Authentication configuration
│   └── .env.example               # Environment variables template
├── deployment/
│   ├── Dockerfile                 # Docker container configuration
│   ├── .ebignore                  # Elastic Beanstalk ignore rules
│   ├── .dockerignore              # Docker ignore rules
│   ├── .ebextensions/             # EB configuration files
│   └── deploy_fixed_integration.py # Deployment automation script
├── docs/
│   ├── deployment-guide.md        # Complete deployment instructions
│   ├── agentic-architecture.md    # Strands workflow documentation
│   └── braket-integration.md      # Quantum computing integration
├── enhanced_mcp_materials/
│   ├── local_server.py            # Enhanced MCP server with auto-recovery
│   ├── aws_server.py              # AWS-optimized MCP server
│   └── moire_helper.py            # Moire bilayer generation tools
├── models/
│   ├── base_model.py              # Base class with streaming support
│   ├── nova_pro_model.py          # Amazon Nova Pro implementation
│   ├── llama4_model.py            # Meta Llama 4 Scout implementation
│   ├── deepseek_model.py          # DeepSeek R1 implementation
│   └── qwen_model.py              # Qwen 3-32B implementation
├── setup/
│   ├── setup_secrets.py           # AWS Secrets Manager setup
│   └── install_braket.py          # Amazon Braket installation
├── utils/
│   ├── mcp_tools_wrapper.py       # MCP integration wrapper
│   ├── braket_integration.py      # Amazon Braket quantum circuits
│   ├── enhanced_mcp_client.py     # Robust MCP client with retries
│   └── secrets_manager.py         # AWS Secrets Manager utilities
├── BraketMCP/                     # Amazon Braket MCP server
├── app.py                         # Main Streamlit application
├── demo_mode.py                   # Demo authentication stub
└── requirements.txt               # Python dependencies
```

**Key Directories:**
- `/agents`: Strands agentic workflow implementations
- `/config`: Configuration files and authentication
- `/deployment`: AWS Elastic Beanstalk deployment files
- `/docs`: Comprehensive documentation
- `/enhanced_mcp_materials`: Materials Project MCP server with reliability enhancements
- `/models`: LLM model implementations with streaming support
- `/setup`: Setup utilities for AWS and quantum computing integration
- `/utils`: Core utilities for MCP, Braket, and AWS integration

## Model Configurations

| Model | Region | Model ID | Use Case |
|-------|--------|----------|----------|
| Nova Pro | us-east-1 | `amazon.nova-pro-v1:0` | Multimodal, latest features |
| Llama 4 Scout | us-east-1 | `us.meta.llama4-scout-17b-instruct-v1:0` | Fast, efficient |
| Llama 3 70B | us-west-2 | `meta.llama3-70b-instruct-v1:0` | High quality, detailed |
| Claude Sonnet 4.5 | us-east-1 | `us.anthropic.claude-sonnet-4-5-20250929-v1:0` | Advanced reasoning, coding |
| Claude Opus 4.1 | us-east-1 | `us.anthropic.claude-opus-4-1-20250805-v1:0` | Complex analysis, research |
| OpenAI OSS-120B | us-west-2 | `openai.gpt-oss-20b-1:0` | Alternative approach |
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

1. **See docs/deployment-guide.md** for complete deployment guide
2. **Deploy to AWS Elastic Beanstalk** for shared web access
3. **Users access via URL** - no setup required
4. **Auto-scaling** and load balancing included

### Quick Deploy
```bash
# 1. Configure Materials Project API key (REQUIRED)
python setup/setup_secrets.py

# 2. Install EB CLI
pip install awsebcli

# 3. Initialize and deploy
eb init quantum-matter-app --platform docker --region us-east-1
eb create quantum-matter-env --instance-types t3.medium
eb deploy

# 4. Configure SSL Certificate (Optional)
eb setenv SSL_CERT_ARN=your_certificate_arn_here

# 5. Get URL
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

## Strands Agentic Workflows

The platform implements sophisticated multi-agent workflows using AWS Strands framework:

- **Intelligent Workflow Dispatch**: Automatically routes queries to appropriate specialized agents
- **Multi-Material Analysis**: Processes complex comparisons across multiple materials
- **DFT Parameter Extraction**: Generates realistic tight-binding Hamiltonian parameters
- **Structure Analysis**: POSCAR matching and crystal structure analysis
- **Iterative Problem Solving**: Handles complex queries through iterative refinement

For detailed documentation, see [Agentic Architecture Guide](docs/agentic-architecture.md)

## Amazon Braket Integration

Seamless integration with Amazon Braket quantum computing services:

- **Quantum Circuit Generation**: VQE, Bell states, GHZ circuits
- **Device Management**: List and monitor quantum devices
- **Hybrid Algorithms**: Classical-quantum optimization
- **Circuit Visualization**: ASCII and graphical circuit diagrams

For setup instructions, see [Braket Integration Guide](docs/braket-integration.md)

## MCP Server Architecture

Robust Materials Project integration with enhanced reliability:

- **Auto-Recovery**: Automatic server restart on failures
- **Fallback Mechanisms**: Multiple API endpoints and caching
- **Consistent Structure IDs**: Standardized mp-123 format
- **Enhanced Error Handling**: Graceful degradation and retry logic
- **Real-time Monitoring**: Health checks and performance metrics

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

### MCP Server Issues
- Check MCP server logs in the application
- Verify Materials Project API key is configured
- Restart the application if MCP server becomes unresponsive

### Strands Agent Issues
- Ensure AWS credentials have access to Claude Sonnet 4.5
- Check Strands package versions: `strands-agents>=1.17.0`
- Verify MCP tools wrapper initialization

### Dependencies Issues
```bash
# If you encounter package conflicts, create a virtual environment
python -m venv quantum_env
source quantum_env/bin/activate  # On Windows: quantum_env\Scripts\activate
pip install -r requirements.txt
```

## Credits

This application was architected and developed by [Sharon Marfatia](https://www.linkedin.com/in/sharon-cs/). Thanks to the UBC Cloud Innovation Centre Technical and Project Management teams for their guidance and support.

## License

This project is distributed under the [MIT License](LICENSE).

Licenses of libraries and tools used by the system are listed below:

**Apache License 2.0**
- For Qiskit quantum circuit construction and simulation - [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
- For Strands Agents SDK agentic workflow implementation - [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
- For Amazon Braket MCP server - [Apache License 2.0](BraketMCP/amazon-braket-mcp-server/LICENSE)

**Materials Project API**
- For Materials Project data access - "Materials Project API is freely available for academic and non-commercial use"