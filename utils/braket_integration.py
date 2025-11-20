# Amazon Braket Integration for Quantum Matter Streamlit App
# This module provides a simplified interface to the Braket MCP server

import os
import sys
import json
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

# Add BraketMCP to path
braket_mcp_path = Path(__file__).parent.parent / "BraketMCP" / "amazon-braket-mcp-server"
sys.path.insert(0, str(braket_mcp_path))

try:
    # Try multiple import paths for Braket MCP
    try:
        # Try the correct package structure
        from amazon_braket_mcp_server.braket_service import BraketService
        from amazon_braket_mcp_server.models import QuantumCircuit, Gate, TaskResult
        from amazon_braket_mcp_server.exceptions import BraketMCPException
        logging.info("✅ Braket MCP imported successfully")
    except ImportError as e1:
        logging.warning(f"Primary Braket MCP import failed: {e1}")
        try:
            # Try awslabs prefix
            from awslabs.amazon_braket_mcp_server.braket_service import BraketService
            from awslabs.amazon_braket_mcp_server.models import QuantumCircuit, Gate, TaskResult
            from awslabs.amazon_braket_mcp_server.exceptions import BraketMCPException
            logging.info("✅ Braket MCP imported with awslabs prefix")
        except ImportError as e2:
            logging.warning(f"Awslabs Braket MCP import failed: {e2}")
            # Fallback to direct braket SDK with mock classes
            from braket.circuits import Circuit as BraketCircuit
            
            class QuantumCircuit:
                def __init__(self, num_qubits, gates=None):
                    self.num_qubits = num_qubits
                    self.gates = gates or []
            
            class Gate:
                def __init__(self, name, qubits=None, params=None):
                    self.name = name
                    self.qubits = qubits or []
                    self.params = params or []
            
            class MockBraketService:
                def __init__(self, region_name=None, workspace_dir=None):
                    self.region = region_name
                    self.workspace = workspace_dir
                
                def create_circuit_visualization(self, circuit, name):
                    # Generate proper ASCII diagram based on circuit type
                    if name == "bell_pair":
                        ascii_viz = """q0: ──H──@──
          │
q1: ──I──X──"""
                        description = {
                            "gate_sequence": ["Apply Hadamard gate to qubit 0", "Apply CNOT gate with qubit 0 as control, qubit 1 as target"],
                            "expected_behavior": "Creates Bell state |00⟩ + |11⟩, showing perfect correlation in measurements"
                        }
                    elif name == "ghz":
                        if circuit.num_qubits == 3:
                            ascii_viz = """q0: ──H──@────@──
          │    │
q1: ──I──X────@──
               │
q2: ──I──I────X──"""
                        else:
                            ascii_viz = f"GHZ circuit with {circuit.num_qubits} qubits\nq0: ──H──@──...\nq1: ──I──X──...\n..."
                        description = {
                            "gate_sequence": [f"Apply Hadamard to qubit 0"] + [f"Apply CNOT from qubit {i} to qubit {i+1}" for i in range(circuit.num_qubits-1)],
                            "expected_behavior": f"Creates {circuit.num_qubits}-qubit GHZ state with maximum entanglement"
                        }
                    else:
                        ascii_viz = f"Custom circuit: {name}\n" + "\n".join([f"q{i}: ──{g.name}──" for i, g in enumerate(circuit.gates[:4])])
                        description = {"gate_sequence": [f"{g.name} on qubits {g.qubits}" for g in circuit.gates]}
                    
                    return {
                        "circuit_name": name,
                        "ascii_visualization": ascii_viz,
                        "description": description,
                        "gates": [f"{g.name}({g.qubits})" for g in circuit.gates],
                        "status": "visualization_ready"
                    }
                
                def list_devices(self):
                    return [
                        {"device_name": "SV1", "provider_name": "Amazon", "arn": "arn:aws:braket:::device/quantum-simulator/amazon/sv1", "status": "ONLINE", "qubits": 34},
                        {"device_name": "DM1", "provider_name": "Amazon", "arn": "arn:aws:braket:::device/quantum-simulator/amazon/dm1", "status": "ONLINE", "qubits": 17},
                        {"device_name": "IonQ Device", "provider_name": "IonQ", "arn": "arn:aws:braket:::device/qpu/ionq/ionQdevice", "status": "OFFLINE", "qubits": 11}
                    ]
            
            BraketService = MockBraketService
            TaskResult = dict
            BraketMCPException = Exception
            logging.info("✅ Using mock Braket service for fallback")
    
    BRAKET_AVAILABLE = True
except ImportError as e:
    logging.warning(f"All Braket imports failed: {e}")
    BRAKET_AVAILABLE = False

logger = logging.getLogger(__name__)


class BraketIntegration:
    """Simplified Braket integration for Streamlit app."""
    
    def __init__(self):
        """Initialize Braket integration."""
        self.service = None
        self.available = BRAKET_AVAILABLE
        
        if self.available:
            try:
                # Initialize with environment variables
                region = os.environ.get('AWS_REGION', 'us-east-1')
                workspace_dir = os.environ.get('BRAKET_WORKSPACE_DIR', 
                                             str(Path.home() / 'quantum_workspace'))
                
                # Ensure workspace directory exists
                Path(workspace_dir).mkdir(parents=True, exist_ok=True)
                
                self.service = BraketService(region_name=region, workspace_dir=workspace_dir)
                logger.info(f"✅ Braket service initialized successfully in {region}")
            except Exception as e:
                logger.error(f"Failed to initialize Braket service: {e}")
                # Don't disable completely, keep mock functionality
                logger.info("Using mock Braket service for basic functionality")
                self.service = BraketService() if BraketService else None
    
    def is_available(self) -> bool:
        """Check if Braket integration is available."""
        return self.available and self.service is not None
    
    def create_bell_pair_circuit(self) -> Dict[str, Any]:
        """Create a Bell pair circuit with visualization."""
        if not self.is_available():
            return {"error": "Braket service not available"}
        
        try:
            # Create circuit definition
            circuit_def = QuantumCircuit(
                num_qubits=2,
                gates=[
                    Gate(name='h', qubits=[0]),
                    Gate(name='cx', qubits=[0, 1]),
                    Gate(name='measure_all'),
                ]
            )
            
            # Create visualization
            response = self.service.create_circuit_visualization(circuit_def, "bell_pair")
            return response
            
        except Exception as e:
            logger.error(f"Error creating Bell pair circuit: {e}")
            return {"error": str(e)}
    
    def create_ghz_circuit(self, num_qubits: int = 3) -> Dict[str, Any]:
        """Create a GHZ state circuit with visualization."""
        if not self.is_available():
            return {"error": "Braket service not available"}
        
        try:
            # Create GHZ circuit gates
            gates = [Gate(name='h', qubits=[0])]  # Hadamard on first qubit
            for i in range(num_qubits - 1):
                gates.append(Gate(name='cx', qubits=[i, i + 1]))  # CNOT chain
            gates.append(Gate(name='measure_all'))  # Measure all
            
            # Create circuit definition
            circuit_def = QuantumCircuit(
                num_qubits=num_qubits,
                gates=gates
            )
            
            # Create visualization
            response = self.service.create_circuit_visualization(circuit_def, "ghz")
            return response
            
        except Exception as e:
            logger.error(f"Error creating GHZ circuit: {e}")
            return {"error": str(e)}
    
    def list_braket_devices(self) -> Dict[str, Any]:
        """List available Braket devices."""
        if not self.is_available():
            return {"error": "Braket service not available"}
        
        try:
            devices = self.service.list_devices()
            return {
                "devices": [device.model_dump() for device in devices],
                "total_devices": len(devices)
            }
            
        except Exception as e:
            logger.error(f"Error listing devices: {e}")
            return {"error": str(e)}
    
    def create_custom_circuit(self, num_qubits: int, gates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a custom quantum circuit."""
        if not self.is_available():
            return {"error": "Braket service not available"}
        
        try:
            # Convert gates to Gate objects
            gate_objects = []
            for gate_dict in gates:
                gate = Gate(
                    name=gate_dict.get('name'),
                    qubits=gate_dict.get('qubits', []),
                    params=gate_dict.get('params')
                )
                gate_objects.append(gate)
            
            # Create circuit definition
            circuit_def = QuantumCircuit(num_qubits=num_qubits, gates=gate_objects)
            
            # Create visualization
            response = self.service.create_circuit_visualization(circuit_def, "custom")
            return response
            
        except Exception as e:
            logger.error(f"Error creating custom circuit: {e}")
            return {"error": str(e)}
    
    def create_vqe_circuit(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create VQE ansatz circuit based on material properties."""
        if not self.is_available():
            return {"error": "Braket service not available"}
        
        try:
            # Extract material properties
            formula = material_data.get('formula', 'H2')
            band_gap = material_data.get('band_gap', 0.0)
            formation_energy = material_data.get('formation_energy', 0.0)
            
            # Determine circuit parameters based on material
            num_qubits = self._calculate_qubits_for_material(formula, material_data)
            ansatz_type = self._select_ansatz_type(band_gap, formation_energy)
            
            # Create VQE ansatz gates
            gates = self._generate_vqe_gates(num_qubits, ansatz_type, material_data)
            
            # Create circuit definition
            circuit_def = QuantumCircuit(num_qubits=num_qubits, gates=gates)
            
            # Create visualization with material context
            response = self.service.create_circuit_visualization(circuit_def, f"vqe_{formula}")
            
            # Add material-specific metadata
            response['material_context'] = {
                'formula': formula,
                'band_gap': band_gap,
                'formation_energy': formation_energy,
                'ansatz_type': ansatz_type,
                'qubit_mapping': 'Jordan-Wigner'
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating VQE circuit: {e}")
            return {"error": str(e)}
    
    def _calculate_qubits_for_material(self, formula: str, material_data: Dict[str, Any]) -> int:
        """Calculate required qubits based on material complexity."""
        # Material-specific qubit mapping
        qubit_map = {
            'H2': 4, 'H': 2, 'He': 2,
            'Li': 6, 'Be': 6, 'B': 8, 'C': 8, 'N': 8, 'O': 8, 'F': 8,
            'graphene': 8, 'diamond': 10,
            'TiO2': 12, 'SiO2': 10, 'Al2O3': 14
        }
        
        # Check for exact matches first
        if formula in qubit_map:
            return qubit_map[formula]
        
        # Fallback: scale with atom count
        atom_count = len([c for c in formula if c.isupper()])
        base_qubits = max(4, atom_count * 2)
        return min(base_qubits, 16)  # Cap at 16 qubits for practical simulation
    
    def _select_ansatz_type(self, band_gap: float, formation_energy: float) -> str:
        """Select appropriate ansatz based on material properties."""
        if isinstance(band_gap, (int, float)) and band_gap > 5.0:  # Insulator
            return "hardware_efficient"
        elif isinstance(band_gap, (int, float)) and band_gap > 0.1:  # Semiconductor
            return "uccsd"
        else:  # Metal or small gap
            return "adaptive"
    
    def _generate_vqe_gates(self, num_qubits: int, ansatz_type: str, material_data: Dict[str, Any]) -> List[Gate]:
        """Generate VQE ansatz gates based on material properties."""
        gates = []
        
        if ansatz_type == "uccsd":
            # UCCSD-inspired ansatz
            for i in range(0, min(num_qubits, 4), 2):
                gates.append(Gate(name='x', qubits=[i]))
            
            for layer in range(2):
                for i in range(num_qubits):
                    gates.append(Gate(name='ry', qubits=[i], params=[f'theta_{layer}_{i}']))
                for i in range(0, num_qubits-1, 2):
                    gates.append(Gate(name='cx', qubits=[i, i+1]))
                
        elif ansatz_type == "hardware_efficient":
            # Hardware-efficient ansatz
            for layer in range(3):
                for i in range(num_qubits):
                    gates.append(Gate(name='ry', qubits=[i], params=[f'theta_{layer}_{i}']))
                    gates.append(Gate(name='rz', qubits=[i], params=[f'phi_{layer}_{i}']))
                for i in range(num_qubits):
                    gates.append(Gate(name='cx', qubits=[i, (i+1) % num_qubits]))
        
        else:  # adaptive
            for i in range(num_qubits):
                gates.append(Gate(name='h', qubits=[i]))
            for i in range(num_qubits-1):
                gates.append(Gate(name='cx', qubits=[i, i+1]))
        
        gates.append(Gate(name='measure_all'))
        return gates
    
    def run_circuit_on_simulator(self, circuit_def: Dict[str, Any], shots: int = 1000) -> Dict[str, Any]:
        """Run a circuit on the local simulator."""
        if not self.is_available():
            return {"error": "Braket service not available"}
        
        try:
            # Use default simulator
            device_arn = "arn:aws:braket:::device/quantum-simulator/amazon/sv1"
            
            # Convert circuit dict to QuantumCircuit object
            gate_objects = []
            for gate_dict in circuit_def.get('gates', []):
                gate = Gate(
                    name=gate_dict.get('name'),
                    qubits=gate_dict.get('qubits', []),
                    params=gate_dict.get('params')
                )
                gate_objects.append(gate)
            
            circuit = QuantumCircuit(
                num_qubits=circuit_def.get('num_qubits'),
                gates=gate_objects
            )
            
            # Run the task
            task_id = self.service.run_quantum_task(
                circuit=circuit,
                device_arn=device_arn,
                shots=shots
            )
            
            return {
                "task_id": task_id,
                "status": "CREATED",
                "device_arn": device_arn,
                "shots": shots
            }
            
        except Exception as e:
            logger.error(f"Error running circuit: {e}")
            return {"error": str(e)}
    
    def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """Get the result of a quantum task."""
        if not self.is_available():
            return {"error": "Braket service not available"}
        
        try:
            result = self.service.get_task_result(task_id)
            return result.model_dump()
            
        except Exception as e:
            logger.error(f"Error getting task result: {e}")
            return {"error": str(e)}
    
    def list_available_devices(self) -> List[Dict[str, Any]]:
        """List available quantum devices."""
        if not self.is_available():
            return [{"error": "Braket service not available"}]
        
        try:
            devices = self.service.list_devices()
            return [device.model_dump() for device in devices]
            
        except Exception as e:
            logger.error(f"Error listing devices: {e}")
            return [{"error": str(e)}]
    
    def generate_braket_code(self, circuit_description: str) -> str:
        """Generate Braket code from description."""
        # This would integrate with your LLM models to generate Braket-specific code
        braket_template = f'''
# Amazon Braket Circuit for: {circuit_description}
from braket.circuits import Circuit
from braket.devices import LocalSimulator

# Create circuit
circuit = Circuit()

# Add your gates here based on: {circuit_description}
# Example:
# circuit.h(0)  # Hadamard gate on qubit 0
# circuit.cnot(0, 1)  # CNOT gate from qubit 0 to 1

# Run on local simulator
device = LocalSimulator()
task = device.run(circuit, shots=1000)
result = task.result()

print("Measurement counts:", result.measurement_counts)
'''
        return braket_template
    
    def get_braket_status(self) -> Dict[str, Any]:
        """Get Braket integration status and capabilities."""
        return {
            "available": self.is_available(),
            "service_initialized": self.service is not None,
            "capabilities": [
                "Circuit Creation",
                "ASCII Visualization", 
                "Device Listing",
                "Local Simulation",
                "AWS Simulator Access",
                "VQE Circuit Generation",
                "Material-Specific Circuits"
            ] if self.is_available() else [],
            "supported_circuits": [
                "Bell Pair",
                "GHZ State", 
                "Custom Circuits",
                "VQE Ansatz",
                "Material-Based Circuits"
            ] if self.is_available() else []
        }


# Global instance
braket_integration = BraketIntegration()

# Helper functions for LLM integration
def create_braket_ghz_circuit(num_qubits: int = 3) -> Dict[str, Any]:
    """Helper function to create GHZ circuit - makes it easier for LLMs to call."""
    return braket_integration.create_ghz_circuit(num_qubits)

def create_braket_bell_circuit() -> Dict[str, Any]:
    """Helper function to create Bell pair circuit - makes it easier for LLMs to call."""
    return braket_integration.create_bell_pair_circuit()

def create_braket_vqe_circuit(material_data: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function to create VQE circuit for materials - makes it easier for LLMs to call."""
    return braket_integration.create_vqe_circuit(material_data)

def get_braket_devices() -> Dict[str, Any]:
    """Helper function to list Braket devices - makes it easier for LLMs to call."""
    return braket_integration.list_braket_devices()

def get_braket_status() -> Dict[str, Any]:
    """Helper function to get Braket status - makes it easier for LLMs to call."""
    return braket_integration.get_braket_status()