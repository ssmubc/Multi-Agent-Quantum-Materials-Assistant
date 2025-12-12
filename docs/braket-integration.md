# Amazon Braket Integration Guide

## What is Amazon Braket?

[Amazon Braket](https://aws.amazon.com/braket/) is AWS's quantum computing service that provides access to quantum simulators and real quantum hardware from companies like IonQ, Rigetti, and Oxford Quantum Computing. Think of it as a cloud platform where you can design, test, and run quantum algorithms.

**Business Value**: Braket enables researchers and developers to experiment with quantum computing without investing in expensive quantum hardware. You can prototype quantum algorithms, test them on simulators, and eventually run them on real quantum computers.

## What is MCP (Model Context Protocol)?

MCP is a communication standard that allows AI applications to connect to external data sources and tools. In our case, the Braket MCP server acts as a bridge between the AI models and quantum computing capabilities.

**Why MCP Matters**: Instead of the AI generating random quantum code, it can access real quantum device information, create proper circuit visualizations, and provide educational explanations based on actual quantum computing principles.

## How This Integration Helps You

The Braket MCP integration transforms the Quantum Matter application from a basic code generator into an intelligent quantum computing assistant that:

- **Educates**: Explains quantum concepts with step-by-step breakdowns
- **Visualizes**: Shows ASCII circuit diagrams and quantum state evolution
- **Validates**: Ensures generated circuits follow quantum computing best practices
- **Connects**: Links theoretical concepts to real quantum hardware capabilities

## What You Can Do

With this integration, you can ask questions like:
- "Show me how quantum entanglement works with a Bell pair"
- "Create a VQE circuit for hydrogen molecule optimization"
- "What quantum computers are available and what can they do?"
- "Explain quantum superposition with a simple example"

The system will provide educational explanations, working code, and visual diagrams to help you understand quantum computing concepts.

## Setting Up AWS Access

### Why Do You Need AWS Permissions?

To use Amazon Braket features, the application needs permission to:
- **Query quantum devices**: Check what simulators and hardware are available
- **Access device information**: Get specifications like qubit counts and gate sets
- **Store results**: Save quantum computation results to S3 storage

Think of [IAM permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html) as a security keycard that grants specific access to AWS services.

### Required IAM Permissions
Your AWS credentials need these permissions for Braket integration:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "braket:SearchDevices",
                "braket:GetDevice", 
                "braket:CreateQuantumTask",
                "braket:GetQuantumTask",
                "braket:CancelQuantumTask"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": "arn:aws:s3:::amazon-braket-*/*"
        }
    ]
}
```

### How Credentials Are Used

**Local Development:**
- Uses your AWS profile configured with `aws configure` or `AWS_PROFILE` environment variable
- Credentials are read from `~/.aws/credentials` and `~/.aws/config`

**Elastic Beanstalk Deployment:**
- Uses IAM instance profile attached to EC2 instances
- Permissions are assigned to the `aws-elasticbeanstalk-ec2-role` IAM role
- No hardcoded credentials needed - handled automatically by AWS

### Setting Up IAM Permissions

**For Local Development:**
1. Create [IAM user](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html) with Braket permissions (JSON above)
2. Configure credentials: `aws configure` (see [AWS CLI configuration guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html))
3. Or use [AWS SSO](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html): `aws configure sso`

**For Elastic Beanstalk:**
1. Go to [IAM Console](https://console.aws.amazon.com/iam/) → Roles
2. Find `aws-elasticbeanstalk-ec2-role`
3. Click **Add permissions** → **Attach policies**
4. Search and select [`AmazonBraketFullAccess`](https://docs.aws.amazon.com/braket/latest/developerguide/braket-manage-access.html) (recommended)
5. Click **Add permissions**
6. Deploy application - permissions are automatically available

## Quantum Simulators Used

### AWS Simulators
- **SV1**: State vector simulator (up to 34 qubits) - **Default**
- **TN1**: Tensor network simulator (up to 50 qubits)
- **DM1**: Density matrix simulator (up to 17 qubits with noise)
- **Cost**: Pay per simulation (~$0.075 per task)

### Real Quantum Hardware
- **IonQ Harmony**: Trapped ion quantum computer
- **Rigetti Aspen**: Superconducting quantum processor
- **Oxford Quantum Computing**: Photonic quantum computer
- **Cost**: $0.01-$35 per task depending on device and circuit complexity

## Installation and Setup

### Automatic Setup
```bash
# Run the setup script
python setup/install_braket.py
```

This script will:
- Install required Python packages
- Check AWS credentials
- Test Braket integration
- Create workspace directories

### Manual Setup
```bash
# Install dependencies
pip install amazon-braket-sdk>=1.70.0
pip install qiskit-braket-provider>=0.4.0
pip install fastmcp>=0.5.0

# Test installation
python -c "from braket.circuits import Circuit; print('Braket installed successfully')"
```

## Using Braket MCP Features

### Framework Selection
In the Streamlit app sidebar:
1. Select "Braket Framework" from the dropdown
2. The app will generate Braket-specific quantum circuits with detailed analysis
3. Circuits are processed through the Braket MCP server for comprehensive visualization and educational insights

### Example Usage
```python
# Generated Braket code example:
from braket.circuits import Circuit
from braket.devices import LocalSimulator

# Create Bell pair circuit
circuit = Circuit()
circuit.h(0)
circuit.cnot(0, 1)
circuit.measure([0, 1])

# Run on local simulator
device = LocalSimulator()
task = device.run(circuit, shots=1000)
result = task.result()
print(result.measurement_counts)
```

### Available MCP Tools

The application uses these specific Braket MCP tools for quantum circuit analysis:

#### Circuit Creation Tools
- `create_bell_pair_circuit()` - Creates entangled two-qubit Bell states
- `create_ghz_circuit(num_qubits)` - Multi-qubit GHZ entangled states
- `create_vqe_circuit(material_data)` - VQE circuits optimized for materials science
- `create_custom_circuit(num_qubits, gates)` - Custom circuits with specific gate sequences

#### Analysis and Visualization Tools
- `create_circuit_visualization(circuit, name)` - Generates ASCII diagrams and detailed analysis
- `list_devices()` - Lists available quantum simulators and hardware
- `get_braket_status()` - Returns integration status and capabilities

#### Educational Features
- **ASCII Circuit Diagrams**: Text-based visualizations (e.g., `q0: ─H──●──M─`)
- **Step-by-step Analysis**: Gate sequence explanations and quantum behavior predictions
- **Materials Integration**: VQE ansatz selection based on band gaps and formation energies
- **Circuit Complexity Analysis**: Depth, gate counts, and estimated runtime assessments

## Workspace Organization
The setup creates a workspace directory structure:
```
~/quantum_workspace/
├── braket_visualizations/    # Circuit diagrams and plots
├── circuits/                 # Saved quantum circuits
└── results/                  # Execution results and data
```

## Cost Management

### Braket MCP Usage
- **Circuit Analysis**: Completely free - no AWS charges
- **ASCII Visualizations**: Generated locally at no cost
- **Educational Features**: Unlimited learning and exploration
- **Circuit Design**: Test and validate quantum algorithms without execution costs

### MCP Integration Capabilities

The Braket MCP server provides:

```python
# Example MCP tool usage in the application
bell_circuit = create_bell_pair_circuit()
# Returns: ASCII visualization, gate analysis, quantum behavior explanations

ghz_circuit = create_ghz_circuit(num_qubits=4) 
# Returns: Multi-qubit entanglement analysis with step-by-step breakdown

vqe_circuit = create_vqe_circuit(material_data={"formula": "H2", "band_gap": 0.5})
# Returns: Materials-optimized ansatz with Jordan-Wigner mapping

devices = list_devices()
# Returns: Available simulators (SV1, TN1, DM1) and quantum hardware status
```

**Key Benefits:**
- **Professional Analysis**: Uses Braket's quantum computing framework standards
- **Educational Value**: Detailed explanations of quantum phenomena and gate operations
- **Materials Focus**: VQE circuits tailored for molecular and solid-state systems
- **Cost-Free Learning**: Comprehensive quantum education without execution charges

## Troubleshooting

### Common Issues

**"Braket integration not available"**
- Check AWS credentials: `aws sts get-caller-identity`
- Verify Braket permissions: `aws braket search-devices`
- Reinstall dependencies: `pip install --upgrade amazon-braket-sdk`

**Import errors**
- Check Python version (3.12+ required)
- Verify virtual environment activation
- Check for conflicting package versions

**AWS permission errors**
- Verify IAM permissions include all required Braket actions
- Check S3 permissions for result storage
- Ensure credentials are properly configured

### Getting Help
1. Check the Braket integration status in the app sidebar
2. Review error messages in the Streamlit interface
3. Test with simple circuits first (Bell pair)
4. Verify AWS credentials and permissions
5. Check AWS Braket Console for device availability

## Advanced Configuration

### Custom Device Selection
**Note**: The application currently uses SV1 simulator by default. Custom device selection would require code modifications to the `braket_integration.py` file.

### S3 Result Storage
```bash
# Configure S3 bucket for results
export BRAKET_S3_BUCKET=my-quantum-results
export BRAKET_S3_PREFIX=experiments/2024/
```

## Security Best Practices
1. **Never hardcode credentials** in your code
2. **Use IAM roles** for EC2 instances
3. **Monitor quantum task costs** regularly
4. **Use least privilege** IAM permissions
5. **Store sensitive data** in AWS Secrets Manager

## Sample Queries

Try these example queries in the Quantum Matter application to explore Braket MCP capabilities:

### Quantum Entanglement
```
"Create a Bell pair circuit and show me the quantum entanglement"
"Generate a 4-qubit GHZ state and explain the entanglement pattern"
"What happens when I measure entangled qubits?"
```

### Materials Science Applications
```
"Create a VQE circuit for H2 molecule optimization"
"Generate a quantum circuit for TiO2 electronic structure analysis"
"Show me a VQE ansatz for silicon with band gap 1.1 eV"
```

### Quantum Algorithm Learning
```
"Explain quantum superposition with a Hadamard gate example"
"Create a custom 3-qubit circuit with rotation gates"
"What quantum devices are available for my circuits?"
```

### Circuit Analysis and Visualization
```
"Show me the ASCII diagram for a Bell state circuit"
"Analyze the complexity of my quantum circuit"
"What gates are needed for quantum teleportation?"
```

### Educational Exploration
```
"How do CNOT gates create entanglement?"
"What's the difference between X, Y, and Z gates?"
"Explain quantum interference in simple terms"
```

## Next Steps
Once Braket integration is working:
1. Try the sample queries above to explore different quantum concepts
2. Experiment with VQE circuits for various materials
3. Learn quantum gate operations through interactive examples
4. Explore circuit complexity analysis and optimization
5. Compare different ansatz types for materials science applications