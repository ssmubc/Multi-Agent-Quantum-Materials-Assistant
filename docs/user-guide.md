# User Guide - Quantum Matter LLM Testing Platform

## Overview
The Quantum Matter LLM Testing Platform harnesses generative AI on AWS Cloud Infrastructure to enable quantum computing and materials science research through intelligent Large Language Model interactions. The platform supports both **Qiskit framework integration** with Materials Project MCP data and **Amazon Braket SDK** for quantum circuits and device information, providing comprehensive quantum simulations and materials analysis capabilities.

## Getting Started

### Accessing the Application

**Login Page**
![Alt text](images/Streamlit_login.png)
Existing users can sign in with their email and password through the secure AWS Cognito authentication system.

**Sign Up Page**
![Alt text](images/Streamlit_signin.png)
New users can create an account by providing their email, password, and confirming their password. 

*Password requirements:* minimum 8 characters with at least one uppercase letter, one lowercase letter, and one number.

**Email Verification Page**
![Alt text](images/Streamlit_verifyemail.png)
After signing up, users must verify their email address by entering the verification code sent to their registered email.
![Alt text](images/Streamlit_email_code.png)

**Main Application Interface**
![Alt text](images/main_page.png)
Once authenticated, users gain access to 8 different LLM models optimized for quantum computing and materials science queries, distributed across AWS regions for optimal performance.

## Main Interface Components

### 1. Model Selection
![Alt text](images/model_selection.png)

Choose from 8 available models:

- **Nova Pro** - Amazon's multimodal model with latest features and capabilities
- **Llama 4 Scout** - Meta's fast, efficient instruction-tuned model for quick responses
- **Claude Sonnet 4.5** - Anthropic's advanced reasoning model for complex coding tasks
- **Claude Opus 4.1** - Anthropic's most powerful model for complex analysis and research
- **Qwen 3-32B** - Alibaba's advanced reasoning model with structured output capabilities
- **DeepSeek R1** - DeepSeek's reasoning and problem-solving focused model
- **Llama 3 70B** - Meta's high-quality, detailed 70B parameter model
- **OpenAI OSS-120B** - OpenAI's open-source model providing alternative approaches

### 2. Framework Selection
![Alt text](images/framework_selection.png)

**When to Use Qiskit Framework:**
- Materials science research and analysis
- Crystal structure visualization and DFT calculations
- Integration with Materials Project database
- Academic research with real materials data
- Quantum simulations based on actual material properties
- Multi-agent workflows with Strands agents

**When to Use Braket Framework:**
- AWS quantum computing workflows
- Direct quantum circuit development
- Preparation for quantum hardware deployment
- Educational quantum algorithm examples
- Integration with Amazon Braket quantum devices

### 3. Technical Details View
![Alt text](images/show_technical_details.png)

Users can click "Show Technical Details" to view behind-the-scenes processes:
- **MCP Tools Used**: See which Materials Project MCP tools were called during Qiskit Framework queries
- **Braket Processes**: View Amazon Braket SDK operations and quantum device interactions
- **Agent Workflows**: Monitor AWS Strands agent coordination and task execution
- **API Calls**: Track real-time data retrieval and processing steps

### 4. Query Input
![Alt text](images/Enter_question.png)

Enter your quantum computing or materials science question in the text area. 

Examples using the Qiskit Framework:
- "Create a moire bilayer structure for graphene with 1.1 degree twist angle"
- "Create a 2x2x2 supercell from mp-149 for quantum simulation and generate the corresponding VQE ansatz."
- "Generate a VQE ansatz for mp-149 and show me the POSCAR structure file format."

For complete list of available tools and query capabilities when using Qiskit Framework mode, please refer to the [Materials Project MCP Integration](materials-project-mcp-integration.md) documentation.


Examples using the Braket Framework:
- "Generate a 4-qubit GHZ circuit with Braket MCP and show ASCII visualization"
- "Generate a Bell state circuit with Braket and explain the entanglement"
- "Create a 3-qubit GHZ state circuit using Amazon Braket"

For complete list of available tools and query capabilities when using Amazon Braket framework mode, please refer to the [Amazon Braket MCP Integration](braket-integration.md) documentation.

### 5. Model Parameters
![Alt text](images/advanced_param.png)

Adjust model behavior with these parameters:
- **Temperature** (0.0-1.0): Controls randomness in responses
- **Max Tokens** (default is 1000): Maximum length of generated response
- **Top P** (0.0-1.0): Controls diversity of word selection

## Backend Data and Logging

### Materials Project MCP JSON Example Results
For query: Create a moire bilayer structure for graphene with 1.1 degree twist angle:
![Alt text](images/materials_project_backend_result.png)

For query that uses the agentic workflow and a specialized agent process: Multi-material comparison of silicon, germanium, and carbon properties:
![Alt text](images/materials_project_backend_result2.png) 

### Strands Agents JSON Results
For query: Create a moire bilayer structure for graphene with 1.1 degree twist angle:
![Alt text](images/strands_analysis_result.png)

For query that uses the agentic workflow and a specialized agent process: Multi-material comparison of silicon, germanium, and carbon properties:
![Alt text](images/strands_analysis_agentic1.png)
![Alt text](images/strands_analysis_agentic2.png)

### Braket MCP JSON Results
[Add screenshot of Braket MCP JSON output]

View Amazon Braket SDK operations and quantum device data:
- Quantum circuit definitions and gate sequences
- Device availability and specifications
- Simulation results and measurement outcomes
- Hardware compatibility information

### System Logging and Monitoring
For query: Create a moire bilayer structure for graphene with 1.1 degree twist angle:
![Alt text](images/activity_log.png)

For query that uses the agentic workflow and a specialized agent process: Multi-material comparison of silicon, germanium, and carbon properties:
![Alt text](images/activity_log2.png)

## Example Outputs

### 1. Qiskit Framework Code Generation Examples
For query: Batch analysis of transition metal dichalcogenides:
![Alt text](images/code_gen_ex.png)

For query: Create a 2x2x2 supercell from mp-149 for quantum simulation and generate the corresponding VQE ansatz:
![Alt text](images/supercell_codegen.png)

For query: Generate tight-binding Hamiltonian for graphene with realistic DFT parameters:
![Alt text](images/binding_hamiltonian.png)

### 2. Amazon Braket SDK Code, Visualization, and Device Information Examples
For query: Generate a 4-qubit GHZ circuit with Braket MCP and show ASCII visualization:
![Alt text](images/ascii_visualization.png)

For query: Generate a Bell state circuit with Braket and explain the entanglement:
![Alt text](images/bell_state_code.png)

For query: Create a quantum Fourier transform circuit using Braket MCP:
![Alt text](images/qft_braket.png)
![Alt text](images/inverse_qft.png)

For Amazon Braket framework query that asks to show available Amazon Braket devices and their status:
![Alt text](images/code_device.png)
![Alt text](images/device_info.png)

### 3. Explanation and Analysis Examples
For Qiskit framework query that uses the agentic workflow and a specialized agent process: Multi-material comparison of silicon, germanium, and carbon properties:
![Alt text](images/theory_gen.png)

For Qiskit framework query that searches material data: Get detailed information about material mp-149 including its structure and properties:
![Alt text](images/material_info.png)

For Amazon Braket framework query that generates a Bell state circuit with Braket and explain the entanglement:
![Alt text](images/bell_state_explain.png)

Key insights and application explanations:
![Alt text](images/insights_applications_braket.png)


ASCII Circuit Diagram and Gate Sequence information:

![Alt text](images/ascii_gate_seq.png)

### 4. POSCAR File Generation Example
![Alt text](images/poscar_datastructure.png)


## Model Comparison

### Model Strengths and Use Cases

**Nova Pro**
- **Best for**: Multimodal queries, latest AI features, cutting-edge capabilities
- **Use when**: You need the most advanced model features and multimodal understanding

**Llama 4 Scout**
- **Best for**: Fast responses, efficient processing, simple to moderate queries
- **Use when**: You need quick results for straightforward quantum computing tasks

**Llama 3 70B**
- **Best for**: Detailed explanations, complex reasoning, high-quality output
- **Use when**: You need comprehensive analysis and detailed quantum algorithm explanations

**Claude Sonnet 4.5**
- **Best for**: Advanced reasoning, complex coding tasks, structured problem-solving
- **Use when**: You need sophisticated quantum circuit design and optimization

**Claude Opus 4.1**
- **Best for**: Complex analysis, research-level tasks, comprehensive materials science
- **Use when**: You need the highest level of analytical depth and research capabilities

**OpenAI OSS-120B**
- **Best for**: Alternative approaches, good code structure, diverse perspectives
- **Use when**: You want different algorithmic approaches or code organization styles

**Qwen 3-32B**
- **Best for**: Structured output, mathematical reasoning, precise calculations
- **Use when**: You need mathematically rigorous quantum algorithms and structured results

**DeepSeek R1**
- **Best for**: Problem-solving focus, step-by-step solutions, debugging
- **Use when**: You need detailed problem breakdown and systematic solution approaches

## Usage Limits and Guidelines

### Rate Limiting
- **Request Limit**: 5 requests per 60 seconds per user session
- **Purpose**: Prevents system overload and ensures fair access for all users
- **What happens**: If exceeded, you'll see a message asking you to wait before making another request
- **Tip**: Use the time between requests to review and analyze previous responses

### Data Privacy and Security
- **Authentication**: Secure AWS Cognito with email verification
- **Data Handling**: No persistent storage of user queries or responses
- **Session Management**: Automatic cleanup and memory management
- **Audit Logging**: Security events tracked with correlation IDs
- **Code Security**: Generated code includes security warnings and validation

## Tips for Best Results

### Query Optimization
- Be specific about what you want to generate
- Include material IDs (e.g., mp-149) for Materials Project queries
- Specify quantum algorithms or circuit types
- Ask for explanations when learning