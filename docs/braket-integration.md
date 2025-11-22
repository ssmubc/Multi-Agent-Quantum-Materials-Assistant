# Amazon Braket Integration Guide

## Overview
This guide explains how to set up and use Amazon Braket quantum computing features in the Quantum Matter application.

## What is Amazon Braket?
Amazon Braket is AWS's quantum computing service that provides access to quantum simulators and real quantum hardware from multiple providers (IonQ, Rigetti, Oxford Quantum Computing).

## AWS Credentials and Permissions

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
1. Create IAM user with Braket permissions (JSON above)
2. Configure credentials: `aws configure`
3. Or use AWS SSO: `aws configure sso`

**For Elastic Beanstalk:**
1. Go to IAM Console → Roles
2. Find `aws-elasticbeanstalk-ec2-role`
3. Add inline policy with Braket permissions (JSON above)
4. Deploy application - permissions are automatically available

## Quantum Simulators Used

### Local Simulator (Default)
- **Type**: Classical simulation on your local machine
- **Provider**: Amazon Braket SDK
- **Cost**: Free
- **Use Case**: Development and testing
- **Limitations**: Limited to ~25 qubits due to memory constraints

### AWS Simulators
- **SV1**: State vector simulator (up to 34 qubits)
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

## Using Braket Features

### Framework Selection
In the Streamlit app sidebar:
1. Select "Braket Framework" from the dropdown
2. The app will generate Braket-specific quantum circuits
3. Circuits will run on the local simulator by default

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

### Available Features
- **Bell pair circuits**: Quantum entanglement demonstrations
- **GHZ states**: Multi-qubit entangled states
- **Quantum Fourier Transform**: Fundamental quantum algorithm
- **VQE circuits**: Variational quantum eigensolvers for materials science
- **Custom quantum algorithms**: Based on your prompts

## Workspace Organization
The setup creates a workspace directory structure:
```
~/quantum_workspace/
├── braket_visualizations/    # Circuit diagrams and plots
├── circuits/                 # Saved quantum circuits
└── results/                  # Execution results and data
```

## Cost Management

### Free Tier Usage
- Local simulator: Always free
- AWS simulators: First 1 hour free per month
- Real hardware: No free tier

### Cost Optimization Tips
1. **Start with local simulator** for development
2. **Use AWS simulators** for larger circuits
3. **Reserve real hardware** for final experiments
4. **Monitor costs** in AWS Billing Console
5. **Set billing alerts** to avoid surprises

## Troubleshooting

### Common Issues

**"Braket integration not available"**
- Check AWS credentials: `aws sts get-caller-identity`
- Verify Braket permissions: `aws braket search-devices`
- Reinstall dependencies: `pip install --upgrade amazon-braket-sdk`

**Import errors**
- Check Python version (3.8+ required)
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
```bash
# Set default quantum device
export BRAKET_DEFAULT_DEVICE_ARN=arn:aws:braket:us-east-1::device/qpu/ionq/Harmony
```

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

## Next Steps
Once Braket integration is working:
1. Try generating Bell pair circuits
2. Experiment with VQE for molecular systems
3. Compare Qiskit vs Braket implementations
4. Explore real quantum hardware when ready
5. Monitor costs and optimize usage patterns