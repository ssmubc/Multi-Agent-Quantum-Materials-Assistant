# Quantum Materials Code Generation and Simulation

This project harnesses generative AI on AWS Cloud Infrastructure to enable quantum computing and materials science research through intelligent Large Language Model interactions. The platform supports both **Qiskit framework integration** with Materials Project MCP data and **Amazon Braket SDK** for quantum circuits and device information, providing comprehensive quantum simulations and materials analysis capabilities.

| Index | Description |
|-------|-------------|
| [High Level Architecture](docs/architecture.md) | High level overview illustrating component interactions |
| [Security Guide](docs/securityGuide.md) | Security architecture and best practices documentation |
| [Deployment Guide](docs/deployment-guide.md) | Complete deployment guide for local and AWS development |
| [User Guide](docs/user-guide.md) | The working solution and interface guide |
| [Agentic Architecture](docs/agentic-architecture.md) | Detailed documentation on Strands agentic workflows |
| [Braket Integration](docs/braket-integration.md) | Amazon Braket quantum computing integration |
| [Materials Project MCP Integration](docs/materials-project-mcp-integration.md) | Complete MCP server documentation with tools and examples |
| [Troubleshooting Guide](#troubleshooting) | Documentation on how to troubleshoot common issues |
| [Credits](#credits) | Meet the team behind the solution |
| [License](#license) | License details |

## High-Level Architecture

The following architecture diagram illustrates the various AWS components utilized to deliver the solution. For an in-depth explanation of the application architecture and data flow, please look at the [Architecture Guide](docs/architecture.md).

![Alt text](docs/images/ArchitectureDiagramQuantumStreamlitApp.png)

## Features

- **8 Advanced LLM Models** with diverse capabilities and specializations
- **Quantum Computing Frameworks**: Qiskit integration with Materials Project data + Amazon Braket SDK for quantum circuits and device information
- **Materials Project Integration** with real-time MCP server and auto-recovery
- **Strands Agentic Workflows** for multi-material analysis and DFT parameters
- **Enterprise Authentication** with Amazon Cognito and admin-controlled user creation
- **Global CDN** with CloudFront SSL and enterprise security

For detailed feature documentation, see [User Guide](docs/user-guide.md).

## Prerequisites

- AWS account with Bedrock access
- Materials Project API key from [materialsproject.org](https://materialsproject.org/)
- Python 3.12+ and AWS CLI configured

For detailed setup requirements, see [Deployment Guide](docs/deployment-guide.md).

## Quick Start

See [Deployment Guide](docs/deployment-guide.md) for complete setup and deployment instructions.

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
├── .ebextensions/          # AWS Elastic Beanstalk configuration files
├── .streamlit/             # Streamlit configuration
├── agents/                 # Strands agentic workflow implementations
├── BraketMCP/              # Amazon Braket MCP server implementation
├── config/                 # Application configuration and authentication
├── deployment/             # AWS deployment scripts and CloudFront setup
├── docs/                   # Complete documentation and guides
├── enhanced_mcp_materials/ # Enhanced Materials Project MCP server
├── models/                 # All 8 LLM model implementations with streaming
├── setup/                  # Setup utilities for AWS services and secrets
├── utils/                  # Core utilities for MCP, Braket, AWS integration
├── app.py                  # Main Streamlit application
├── demo_mode.py            # Demo authentication fallback
├── run_local.py            # Local development runner
└── requirements.txt        # Python dependencies
```

1. `/.ebextensions`: Contains AWS Elastic Beanstalk configuration files for environment setup, security headers, Cognito authentication, and MCP server installation
2. `/.streamlit`: Contains Streamlit application configuration including security settings, CORS configuration, and UI theme customization
3. `/agents`: Contains Strands agentic workflow implementations for multi-material analysis, DFT parameter optimization, and quantum structure generation
4. `/BraketMCP`: Contains Amazon Braket MCP server implementation with quantum device access, circuit visualization, and quantum computing tools
    - `/amazon-braket-mcp-server`: Core Braket MCP server with quantum device integration and circuit tools
5. `/config`: Contains application configuration and authentication modules including Cognito integration, custom auth handlers, and environment configuration
6. `/deployment`: Contains AWS deployment scripts, CloudFront setup, Dockerfile for containerized deployment, and Elastic Beanstalk configuration
7. `/docs`: Contains comprehensive documentation including architecture guides, security documentation, user guides, and deployment instructions
    - `/images`: Documentation images and architecture diagrams
8. `/enhanced_mcp_materials`: Contains enhanced Materials Project MCP server with auto-recovery, advanced structure analysis, and real-time data synchronization
9. `/models`: Contains all 8 LLM model implementations with streaming support, error handling, and model-specific optimizations for quantum computing tasks
10. `/setup`: Contains setup utilities for AWS services including Cognito User Pool creation, secrets management, and automated service configuration
11. `/utils`: Contains core utilities for MCP integration, Braket quantum computing, AWS service clients, security validation, audit logging, and rate limiting

## Troubleshooting

For troubleshooting common issues, see [Troubleshooting Guide](docs/deployment-guide.md#troubleshooting).

## Credits

This application was architected and developed by [Sharon Marfatia](https://www.linkedin.com/in/sharon-cs/) with project assistance by Anya Ameen. Thanks to the UBC Cloud Innovation Centre Technical and Project Management teams for their guidance and support.

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