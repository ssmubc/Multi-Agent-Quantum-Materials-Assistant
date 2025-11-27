# Quantum Materials Code Generation and Simulation
### AWS Bedrock, Amazon Braket, AWS Strands Agents & Model Context Protocol

This project harnesses generative AI on AWS Cloud Infrastructure to enable quantum computing and materials science research through intelligent Large Language Model interactions. The platform supports both **Qiskit framework integration** with Materials Project MCP data and **Amazon Braket SDK** for quantum circuits and device information, providing comprehensive quantum simulations and materials analysis capabilities.

| Index | Description |
|-------|-------------|
| [High Level Architecture](docs/architecture.md) | High level overview illustrating component interactions |
| [Deployment](#aws-deployment) | Complete deployment guide for local development and AWS production |
| [User Guide](docs/user-guide.md) | The working solution and interface guide |
| [Agentic Architecture](docs/agentic-architecture.md) | Detailed documentation on Strands agentic workflows |
| [Braket Integration](docs/braket-integration.md) | Amazon Braket quantum computing integration |
| [Materials Project MCP Integration](docs/materials-project-mcp-integration.md) | Complete MCP server documentation with tools and examples |
| [Troubleshooting Guide](#troubleshooting) | Documentation on how to troubleshoot common issues |
| [Credits](#credits) | Meet the team behind the solution |
| [License](#license) | License details |

## High-Level Architecture

The platform utilizes a sophisticated multi-agent architecture combining AWS Bedrock LLMs, Materials Project MCP servers, and Strands agentic workflows for intelligent quantum materials analysis.

<!-- Architecture diagram will be added here -->

For detailed architecture documentation, see [Architecture Guide](docs/architecture.md).


## Features

- **8 Advanced LLM Models** across us-east-1 and us-west-2 regions
- **Quantum Computing Frameworks**: Qiskit integration with Materials Project data + Amazon Braket SDK for quantum circuits and device information
- **Materials Project Integration** with real-time MCP server and auto-recovery
- **Strands Agentic Workflows** for multi-material analysis and DFT parameters
- **Enterprise Authentication** with AWS Cognito and email verification
- **Global CDN** with CloudFront SSL and enterprise security

For detailed feature documentation, see [User Guide](docs/user-guide.md).

## Prerequisites

- AWS account with Bedrock access
- Materials Project API key from [materialsproject.org](https://materialsproject.org/)
- Python 3.8+ and AWS CLI configured

For detailed setup requirements, see [Deployment Guide](docs/deployment-guide.md).

## Quick Start

### Local Development (5 minutes)
```bash
git clone <repository-url>
cd Quantum_Matter_Streamlit_App
pip install -r requirements.txt
python setup/setup_secrets.py  # Store Materials Project API key
export AWS_PROFILE=your-profile-name
python run_local.py
```

### AWS Production Deployment
See [Deployment Guide](docs/deployment-guide.md) for complete instructions.

## Example Queries

**Quantum Computing - Amazon Braket:**
```
Generate a VQE ansatz for H2 molecule using UCCSD with Jordan-Wigner mapping
Show me available Braket quantum devices and their properties
```

**Quantum Computing - Qiskit Framework:**
```
Create a hardware-efficient ansatz for LiH with 3 layers using Qiskit
Build a quantum circuit for QAOA optimization with Qiskit transpiler
```

**Materials Science:**
```
Analyze the electronic properties of TiO2 and generate a Hubbard model
Create a quantum simulation for graphene using Materials Project data
```

## Directories

```
├── .ebextensions/          # AWS Elastic Beanstalk configuration
│   └── 07_cognito_config.config  # Cognito authentication setup
├── agents/                 # Strands agentic workflow implementations
├── config/                 # Authentication and configuration
│   ├── cognito_auth.py     # Cognito authentication handler
│   ├── custom_cognito_auth.py  # Custom 3-tab Cognito interface
│   └── auth_module.py      # Demo authentication fallback
├── deployment/             # AWS deployment scripts and CloudFront setup
├── docs/                   # Complete documentation and guides
├── enhanced_mcp_materials/ # Materials Project MCP server with auto-recovery
├── models/                 # All 8 LLM model implementations with streaming
├── setup/                  # Setup utilities for AWS services
│   └── setup_cognito.py    # Cognito User Pool creation
├── utils/                  # Core utilities for MCP, Braket, AWS integration
├── BraketMCP/             # Amazon Braket MCP server
├── app.py                 # Main Streamlit application
└── requirements.txt       # Python dependencies
```

## Model Configurations

| Model | Region | Use Case |
|-------|--------|----------|
| Nova Pro | us-east-1 | Multimodal, latest features |
| Llama 4 Scout | us-east-1 | Fast, efficient |
| Llama 3 70B | us-west-2 | High quality, detailed |
| Claude Sonnet 4.5 | us-east-1 | Advanced reasoning, coding |
| Claude Opus 4.1 | us-east-1 | Complex analysis, research |
| OpenAI OSS-120B | us-west-2 | Alternative approach |
| Qwen 3-32B | us-east-1 | Advanced reasoning, structured output |
| DeepSeek R1 | us-east-1 | Reasoning and problem-solving |

## Cost Estimation (AWS)

- **t3.medium**: ~$30-35/month (minimum)
- **t3.large**: ~$60-70/month (recommended)
- **t3.xlarge**: ~$120-140/month (heavy usage)
- **CloudFront SSL/CDN**: $0/month (free tier)
- **Cognito**: $0/month (free tier)

## Security Best Practices

1. Use AWS IAM roles instead of hardcoded credentials
2. Store API keys in AWS Secrets Manager
3. Enable CloudWatch logging for monitoring
4. Use least privilege IAM permissions
5. Deploy with CloudFront for SSL/TLS and DDoS protection

## Troubleshooting

For troubleshooting common issues, see [Troubleshooting Guide](docs/deployment-guide.md#troubleshooting).

## Credits

This application was architected and developed by [Sharon Marfatia](https://www.linkedin.com/in/sharon-cs/). Thanks to the UBC Cloud Innovation Centre Technical and Project Management teams for their guidance and support.

## License

This project is distributed under the [MIT License](LICENSE).

Licenses of libraries and tools used by the system are listed below:

**Apache License 2.0**
- For Qiskit quantum circuit construction and simulation - [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
- For Strands Agents SDK agentic workflow implementation - [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
- For Amazon Braket MCP server - [Apache License 2.0](BraketMCP/amazon-braket-mcp-server/LICENSE)

**AWS Bedrock Foundation Models**
- For all 8 LLM models (Nova Pro, Llama 4 Scout, Llama 3 70B, Claude Sonnet 4.5, Claude Opus 4.1, OpenAI OSS-120B, Qwen 3-32B, DeepSeek R1) - [AWS Bedrock Third-Party Model Licenses](https://aws.amazon.com/legal/bedrock/third-party-models/)

**Materials Project API**
- For Materials Project data access - "Materials Project API is freely available for academic and non-commercial use"

**MCP.Science Framework**
- For Materials Project MCP server implementation - Path Integral Institute [MCP.Science](https://github.com/pathintegral-institute/mcp.science)