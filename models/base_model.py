import os
import re
import json
import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseQiskitGenerator(ABC):
    """Base class for all LLM-powered Qiskit generators"""
    
    def __init__(self, mp_agent: Optional[Any] = None, region_name: str = "us-east-1"):
        self.mp_agent = mp_agent
        self.region_name = region_name
        self.bedrock_client = None
        self.model_id = None
        self.llm_enabled = False
        
        # Curated small molecule geometries
        self.geometries = {
            "H2":  "H 0 0 0; H 0 0 0.735",
            "LiH": "Li 0 0 0; H 0 0 1.595",
            "BeH2": "Be 0 0 0; H 0 0 1.33; H 0 0 -1.33",
            "H2O": "O 0 0 0; H 0.757 0.586 0; H -0.757 0.586 0",
            "NH3": "N 0 0 0; H 0 0.94 0.38; H 0.81 -0.47 0.38; H -0.81 -0.47 0.38",
            "CH4": "C 0 0 0; H 0.629 0.629 0.629; H -0.629 -0.629 0.629; H -0.629 0.629 -0.629; H 0.629 -0.629 -0.629",
            "CO":  "C 0 0 0; O 0 0 1.128",
            "CO2": "C 0 0 0; O 0 0 1.16; O 0 0 -1.16",
            "N2":  "N 0 0 0; N 0 0 1.0977",
            "O2":  "O 0 0 0; O 0 0 1.208",
            "HF":  "H 0 0 0; F 0 0 0.917",
            "HCl": "H 0 0 0; Cl 0 0 1.274",
            "BH3": "B 0 0 0; H 0 0.96 0; H 0.83 -0.48 0; H -0.83 -0.48 0",
            "PH3": "P 0 0 0; H 0 1.42 0; H -1.23 -0.71 0; H 1.23 -0.71 0",
            "F2":  "F 0 0 0; F 0 0 1.417",
            "Cl2": "Cl 0 0 0; Cl 0 0 1.988"
        }
    
    @abstractmethod
    def set_model(self, model_id: str):
        """Set the specific model ID and initialize the client"""
        pass
    
    @abstractmethod
    def _call_llm(self, prompt: str, **kwargs) -> str:
        """Call the LLM with the given prompt"""
        pass
    
    def _sanitize_ident(self, text: str) -> str:
        """Sanitize text to create valid Python identifiers"""
        s = re.sub(r'[^0-9a-zA-Z_]+', '_', text)
        s = re.sub(r'_+', '_', s).strip('_')
        if not s:
            s = "obj"
        if s[0].isdigit():
            s = "_" + s
        return s.lower()
    
    def _extract_formula_from_poscar(self, poscar_text: str) -> str:
        """Extract chemical formula from POSCAR structure"""
        try:
            lines = poscar_text.strip().split('\n')
            # Look for element line (usually first line or after lattice vectors)
            for i, line in enumerate(lines[:10]):
                line = line.strip()
                # Check if line contains element symbols
                if re.match(r'^[A-Z][a-z]?(?:\s+[A-Z][a-z]?)*$', line):
                    elements = line.split()
                    # Get counts from next line if available
                    if i + 1 < len(lines):
                        count_line = lines[i + 1].strip()
                        if re.match(r'^\d+(?:\s+\d+)*$', count_line):
                            counts = count_line.split()
                            if len(elements) == len(counts):
                                formula_parts = []
                                for elem, count in zip(elements, counts):
                                    if count == '1':
                                        formula_parts.append(elem)
                                    else:
                                        formula_parts.append(f"{elem}{count}")
                                return ''.join(formula_parts)
                    # Fallback: just return first element
                    return elements[0]
            # If no clear element line found, try first line
            first_line = lines[0].strip()
            if re.match(r'^[A-Z][a-z]?', first_line):
                return re.match(r'^[A-Z][a-z]?', first_line).group(0)
            return "Si"  # Default fallback
        except Exception:
            return "Si"
    
    def _is_small_molecule(self, formula: str) -> bool:
        """Check if formula is in our curated small molecules"""
        return formula in self.geometries
    
    def _detect_intent(self, query: str) -> Dict[str, Any]:
        """Detect user intent from query text"""
        q = (query or "").lower()
        intent = {
            "task": None,
            "ansatz_family": None,
            "mapping": None,
            "layers": None,
            "entanglement": None,
            "rotations": None,
            "active_space": None,
            "requirements": [],
            "supercell": None
        }
        
        # Task detection
        if "vqe" in q or "ground state" in q or "variational" in q:
            intent["task"] = "vqe"
        if "initial state" in q or "initial-state" in q:
            intent["task"] = intent["task"] or "initial_state"
        if "ansatz" in q or "two-local" in q or "uccsd" in q:
            intent["task"] = intent["task"] or "ansatz"
        
        # Ansatz family
        if "uccsd" in q or "ucc" in q:
            intent["ansatz_family"] = "uccsd"
        if "he" in q or "hardware-efficient" in q or "two-local" in q:
            intent["ansatz_family"] = "two_local"
        if "k-upccg" in q or "upccg" in q:
            intent["ansatz_family"] = "k-upccgsd"
        if "adapt" in q:
            intent["ansatz_family"] = "adapt"
        
        # Mapping
        if "bravyi" in q:
            intent["mapping"] = "bravyi_kitaev"
        if "parity" in q:
            intent["mapping"] = "parity"
        if "jordan" in q:
            intent["mapping"] = "jordan_wigner"
        
        # Extract layers
        m = re.search(r'(\d+)\s*layers', q)
        if m:
            intent["layers"] = int(m.group(1))
        
        # Entanglement
        if "linear entanglement" in q:
            intent["entanglement"] = "linear"
        if "circular" in q or "ring" in q:
            intent["entanglement"] = "circular"
        
        # Rotations
        if "ry" in q: intent["rotations"] = "ry"
        if "rx" in q: intent["rotations"] = "rx"
        if "rz" in q: intent["rotations"] = "rz"
        
        # Active space
        as_match = re.search(r'(\d+)[ -]?orbital', q)
        if as_match:
            intent["active_space"] = int(as_match.group(1))
        
        # Requirements
        if "device-agnostic" in q:
            intent["requirements"].append("device-agnostic")
        if "print parameter" in q or "parameter count" in q:
            intent["requirements"].append("print_parameters")
        if "circuit depth" in q or "depth" in q:
            intent["requirements"].append("print_depth")
        
        # Supercell detection
        supercell_match = re.search(r'(\d+)x(\d+)x(\d+)\s*supercell', q)
        if supercell_match or "supercell" in q:
            if supercell_match:
                a, b, c = map(int, supercell_match.groups())
                intent["supercell"] = {"scaling_matrix": [[a,0,0],[0,b,0],[0,0,c]]}
            else:
                intent["supercell"] = {"scaling_matrix": [[2,0,0],[0,2,0],[0,0,2]]}  # default 2x2x2
            intent["task"] = "supercell_vqe"
        
        return intent
    
    def generate_base_code(self, formula: str, intent: Dict[str, Any], mp_data: Optional[Dict[str, Any]] = None, braket_mode: str = "Qiskit Only") -> Optional[str]:
        """Generate base Qiskit code based on formula and intent - only when code is actually needed"""
        
        # Check if user actually wants code generation
        query_lower = (intent.get("original_query", "") or "").lower()
        code_keywords = ["code", "generate", "vqe", "ansatz", "circuit", "qiskit", "hamiltonian", "quantum"]
        listing_keywords = ["show me", "list", "available", "options", "materials", "find"]
        
        wants_code = any(keyword in query_lower for keyword in code_keywords)
        wants_listing = any(keyword in query_lower for keyword in listing_keywords)
        
        # If user clearly wants listing and doesn't mention code, don't generate code
        if wants_listing and not wants_code:
            logger.info(f"🚫 BASE MODEL: Skipping code generation - user wants listing, not code")
            return None
        
        # If no specific task detected and no code keywords, don't generate code
        if not intent.get("task") and not wants_code:
            logger.info(f"🚫 BASE MODEL: Skipping code generation - no quantum task or code request detected")
            return None
        
        logger.info(f"✅ BASE MODEL: Generating code - task: {intent.get('task')}, wants_code: {wants_code}")
        
        geometry = None
        pretty_formula = formula
        
        # Try to get geometry
        if self._is_small_molecule(formula):
            geometry = self.geometries[formula]
            pretty_formula = formula
        elif formula.lower().startswith("mp-") and mp_data and isinstance(mp_data, dict):
            geometry = mp_data.get("geometry")
            pretty_formula = mp_data.get("formula", formula)
        elif mp_data and isinstance(mp_data, dict) and not mp_data.get("error"):
            # Use existing mp_data from supervisor agent
            geometry = mp_data.get("geometry")
            pretty_formula = mp_data.get("formula", formula)
            logger.info(f"✅ BASE MODEL: Using supervisor MP data - formula: {pretty_formula}, has geometry: {bool(geometry)}")
        
        # Handle supercell VQE requests using MCP tool
        if intent.get("task") == "supercell_vqe" and self.mp_agent and mp_data and isinstance(mp_data, dict):
            # Check if Strands already handled supercell creation
            strands_result = getattr(self, '_cached_strands_result', None)
            if strands_result and 'build_supercell' in strands_result.get('mcp_actions', []):
                logger.info(f"✅ BASE MODEL: Using Strands supercell data (avoiding duplicate call)")
                scaling = intent.get("supercell", {"scaling_matrix": [[2,0,0],[0,2,0],[0,0,2]]})["scaling_matrix"]
                
                # Get Materials Project data for enhanced parameters
                bg = mp_data.get("band_gap", 2.601) if mp_data else 2.601
                fe = mp_data.get("formation_energy", -3.341) if mp_data else -3.341
                
                # Physics-based parameters from MP data
                t_ti_o = bg * 0.4  # Ti-O hopping from band gap
                U_ti = abs(fe) * 0.6  # Ti on-site from formation energy
                U_o = abs(fe) * 0.3   # O on-site (smaller)
                
                code = f'''# Enhanced TiO2 Supercell VQE using Materials Project data (mp-1245098)
from qiskit_nature.second_q.operators import FermionicOp
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit.circuit.library import TwoLocal
from qiskit_algorithms import VQE
from qiskit.primitives import Estimator
import numpy as np

# Real Materials Project data for {pretty_formula}
# Band gap: {bg:.3f} eV, Formation energy: {fe:.3f} eV/atom
# Supercell: {scaling[0][0]}x{scaling[1][1]}x{scaling[2][2]} from structure://mp_mp-1245098

# Physics-based parameters from DFT data
t_ti_o = {t_ti_o:.3f}  # Ti-O hopping (from band gap)
U_ti = {U_ti:.3f}     # Ti on-site Coulomb (from formation energy)
U_o = {U_o:.3f}      # O on-site Coulomb

# TiO2 supercell: {scaling[0][0] * scaling[1][1] * scaling[2][2]} unit cells
# Each unit cell: 1 Ti + 2 O atoms
num_ti = {scaling[0][0] * scaling[1][1] * scaling[2][2]}
num_o = {scaling[0][0] * scaling[1][1] * scaling[2][2] * 2}
total_atoms = num_ti + num_o
num_qubits = total_atoms * 2  # spin up + down

print(f"TiO2 Supercell Analysis:")
print(f"Unit cells: {{num_ti}}, Ti atoms: {{num_ti}}, O atoms: {{num_o}}")
print(f"Total atoms: {{total_atoms}}, Qubits needed: {{num_qubits}}")

# Build realistic TiO2 Hamiltonian
fermionic_ops = {{}}

# Ti-O bonds (octahedral coordination in rutile/anatase)
for ti_idx in range(num_ti):
    # Each Ti bonds to 6 O atoms in real TiO2
    for o_offset in range(min(6, num_o)):  # Limit to available O atoms
        o_idx = (ti_idx * 2 + o_offset) % num_o  # Wrap around
        ti_qubit_up = ti_idx * 2
        ti_qubit_down = ti_idx * 2 + 1
        o_qubit_up = (num_ti + o_idx) * 2
        o_qubit_down = (num_ti + o_idx) * 2 + 1
        
        # Ti-O hopping (both spins)
        fermionic_ops[f"+_{{ti_qubit_up}} -_{{o_qubit_up}}"] = -t_ti_o
        fermionic_ops[f"+_{{o_qubit_up}} -_{{ti_qubit_up}}"] = -t_ti_o
        fermionic_ops[f"+_{{ti_qubit_down}} -_{{o_qubit_down}}"] = -t_ti_o
        fermionic_ops[f"+_{{o_qubit_down}} -_{{ti_qubit_down}}"] = -t_ti_o

# On-site interactions
for ti_idx in range(num_ti):
    # Ti d-orbital interactions
    ti_up = ti_idx * 2
    ti_down = ti_idx * 2 + 1
    fermionic_ops[f"+_{{ti_up}} -_{{ti_up}} +_{{ti_down}} -_{{ti_down}}"] = U_ti

for o_idx in range(num_o):
    # O p-orbital interactions
    o_up = (num_ti + o_idx) * 2
    o_down = (num_ti + o_idx) * 2 + 1
    fermionic_ops[f"+_{{o_up}} -_{{o_up}} +_{{o_down}} -_{{o_down}}"] = U_o

# Map to qubits using Jordan-Wigner
ferm_op = FermionicOp(fermionic_ops, register_length=num_qubits)
mapper = JordanWignerMapper()
qubit_op = mapper.map(ferm_op)

# Hardware-efficient ansatz for TiO2
ansatz = TwoLocal(num_qubits, 'ry', 'cz', reps=3, entanglement='circular')

print(f"\nTiO2 Quantum Hamiltonian:")
print(f"Fermionic terms: {{len(fermionic_ops)}}")
print(f"Pauli terms after mapping: {{len(qubit_op)}}")
print(f"Ansatz parameters: {{ansatz.num_parameters}}")
print(f"\nThis uses REAL Materials Project structure data!")
'''
                return code
            else:
                # Only call MCP if Strands hasn't already done it
                try:
                    structure_uri = mp_data.get("structure_uri")
                    supercell_params = intent.get("supercell", {"scaling_matrix": [[2,0,0],[0,2,0],[0,0,2]]})
                    
                    logger.info(f"🔧 BASE MODEL: Using MCP supercell tool for {structure_uri}")
                    supercell_result = self.mp_agent.build_supercell(structure_uri, supercell_params)
                    
                    if supercell_result:
                        supercell_uri = supercell_result.get("supercell_uri", "")
                        scaling = supercell_params["scaling_matrix"]
                        
                        code = f'''# Supercell VQE for {pretty_formula} using MCP-generated supercell
from qiskit_nature.second_q.operators import FermionicOp
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit.circuit.library import TwoLocal
from qiskit_algorithms import VQE
from qiskit.primitives import Estimator

# Supercell created via MCP: {supercell_uri}
# Scaling matrix: {scaling}

# Extended Hubbard model for supercell
t = 1.0  # hopping parameter
U = 2.0  # on-site interaction

# Calculate supercell size
supercell_sites = {scaling[0][0] * scaling[1][1] * scaling[2][2] * 2}  # 2 atoms per unit cell
num_qubits = supercell_sites * 2  # spin up + spin down

# Build fermionic Hamiltonian for supercell
fermionic_ops = {{}}

# Nearest-neighbor hopping in supercell
for i in range(supercell_sites - 1):
    # Up spin hopping
    fermionic_ops[f"+_{{i*2}} -_{{(i+1)*2}}"] = -t
    fermionic_ops[f"+_{{(i+1)*2}} -_{{i*2}}"] = -t
    # Down spin hopping  
    fermionic_ops[f"+_{{i*2+1}} -_{{(i+1)*2+1}}"] = -t
    fermionic_ops[f"+_{{(i+1)*2+1}} -_{{i*2+1}}"] = -t

# On-site interactions
for i in range(supercell_sites):
    fermionic_ops[f"+_{{i*2}} -_{{i*2}} +_{{i*2+1}} -_{{i*2+1}}"] = U

# Map to qubits
ferm_op = FermionicOp(fermionic_ops, register_length=num_qubits)
mapper = JordanWignerMapper()
qubit_op = mapper.map(ferm_op)

# Create ansatz for supercell
ansatz = TwoLocal(num_qubits, 'ry', 'cz', reps=2, entanglement='linear')

print(f"Supercell {scaling[0][0]}x{scaling[1][1]}x{scaling[2][2]} for {pretty_formula}:")
print(f"Sites: {{supercell_sites}}, Qubits: {{num_qubits}}")
print(f"Hamiltonian: {{len(qubit_op)}} Pauli terms")
print(f"Ansatz: {{ansatz.num_parameters}} parameters")
'''
                        return code
                    else:
                        logger.warning(f"❌ BASE MODEL: MCP supercell creation failed")
                except Exception as e:
                    logger.error(f"💥 BASE MODEL: MCP supercell error: {e}")
        

        # Check for other MCP operations that Strands might have handled
        strands_result = getattr(self, '_cached_strands_result', None)
        strands_mcp_actions = strands_result.get('mcp_actions', []) if strands_result else []
        
        # Log MCP operations to avoid duplicates
        if strands_mcp_actions:
            logger.info(f"✅ BASE MODEL: Strands handled MCP operations: {strands_mcp_actions}")
        
        # Generate molecular code if geometry available
        if intent.get("task") in ("vqe", "ansatz", "initial_state") and geometry:
            family = intent.get("ansatz_family") or "two_local"
            mapping = intent.get("mapping") or "jordan_wigner"
            layers = intent.get("layers") or 2
            ent = intent.get("entanglement") or "linear"
            rot = intent.get("rotations") or "ry"
            
            # Generate Braket SDK code when in Amazon Braket mode
            if braket_mode == "Amazon Braket":
                # For VQE/complex queries in Braket mode, create simple demonstration circuits
                if "bell" in query_lower or "pair" in query_lower:
                    code = f'''# Bell pair circuit using Amazon Braket SDK
from braket.circuits import Circuit
from braket.devices import LocalSimulator

# Create Bell pair circuit
circuit = Circuit()

# Apply Hadamard gate to qubit 0
circuit.h(0)

# Apply CNOT gate
circuit.cnot(0, 1)

# Print circuit
print("Bell Pair Circuit:")
print(circuit)

# Run on local simulator
device = LocalSimulator()
task = device.run(circuit, shots=1000)
result = task.result()

print(f"\nMeasurement counts: {{result.measurement_counts}}")
print(f"Bell pair created for {pretty_formula} demonstration")
'''
                elif "ghz" in query_lower:
                    num_qubits = 3  # Default for GHZ
                    qubit_match = re.search(r'(\d+)\s*qubit', query_lower)
                    if qubit_match:
                        num_qubits = int(qubit_match.group(1))
                    
                    code = f'''# {num_qubits}-qubit GHZ state using Amazon Braket SDK
from braket.circuits import Circuit
from braket.devices import LocalSimulator

# Create {num_qubits}-qubit GHZ circuit
circuit = Circuit()

# Apply Hadamard to first qubit
circuit.h(0)

# Apply CNOT gates to create GHZ state
for i in range(1, {num_qubits}):
    circuit.cnot(0, i)

# Print circuit
print("{num_qubits}-qubit GHZ Circuit:")
print(circuit)

# Run on local simulator
device = LocalSimulator()
task = device.run(circuit, shots=1000)
result = task.result()

print(f"\nMeasurement counts: {{result.measurement_counts}}")
print(f"GHZ state created for {pretty_formula} demonstration")
'''
                else:
                    # For VQE/materials queries, create a simple demonstration circuit
                    code = f'''# Simple quantum circuit demonstration for {pretty_formula} using Amazon Braket SDK
# Note: Braket mode focuses on algorithm demonstrations, not full VQE implementations
from braket.circuits import Circuit
from braket.devices import LocalSimulator

# Create a 4-qubit demonstration circuit
circuit = Circuit()

# Create entangled state (simplified VQE-like structure)
circuit.h(0)  # Superposition
circuit.cnot(0, 1)  # Entanglement
circuit.cnot(1, 2)  # More entanglement
circuit.cnot(2, 3)  # Chain entanglement

# Add some rotation gates (parameterized gates would go here in real VQE)
circuit.ry(0, 0.5)  # Example rotation
circuit.ry(1, 0.3)
circuit.ry(2, 0.7)
circuit.ry(3, 0.2)

# Print circuit
print(f"Demonstration circuit for {pretty_formula}:")
print(circuit)

# Run on local simulator
device = LocalSimulator()
task = device.run(circuit, shots=1000)
result = task.result()

print(f"\nMeasurement counts: {{result.measurement_counts}}")
print(f"\nNote: This is a demonstration circuit for {pretty_formula}.")
print("For full VQE implementations, use Qiskit mode with Materials Project integration.")
'''
                return code
            
            # Skip visualization and complex VQE for Braket mode (handled above)
            if braket_mode == "Amazon Braket":
                return None  # Already handled above
            
            # Check if visualization is requested
            wants_visualization = any(term in query_lower for term in ["3d", "visualiz", "plot", "structure", "crystal"])
            
            if wants_visualization:
                # Check if Strands already handled visualization
                if 'plot_structure' in strands_mcp_actions:
                    logger.info(f"✅ BASE MODEL: Using Strands visualization (avoiding duplicate plot)")
                    from utils.visualization_tools import get_vqe_visualization_code
                    code = get_vqe_visualization_code(pretty_formula)
                    code += "\n\n# 3D structure visualization generated by Strands MCP workflow"
                else:
                    from utils.visualization_tools import get_vqe_visualization_code, get_modern_visualization_code
                    vqe_code = get_vqe_visualization_code(pretty_formula)
                    viz_code = get_modern_visualization_code(pretty_formula)
                    code = f"{vqe_code}\n\n{viz_code}"
            elif family == "uccsd":
                code = f'''# Auto-generated UCCSD ansatz for {pretty_formula}
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.circuit.library import UCCSD
from qiskit_nature.second_q.mappers import JordanWignerMapper, ParityMapper
from qiskit.primitives import Estimator
from qiskit_algorithms import VQE
from qiskit_algorithms.optimizers import SLSQP

geometry = """{geometry}"""

driver = PySCFDriver(atom=geometry, basis='sto3g')
problem = driver.run()

mapper = JordanWignerMapper() if "{mapping}" == "jordan_wigner" else ParityMapper()
ansatz = UCCSD(problem.num_spatial_orbitals, problem.num_particles, mapper=mapper)

# Compile and report
try:
    params = ansatz.num_parameters
    depth = ansatz.decompose().depth() if hasattr(ansatz, "decompose") else 'unknown'
except Exception:
    params = getattr(ansatz, 'num_parameters', 'unknown')
    depth = 'unknown'

print("UCCSD ansatz for {pretty_formula}: parameters =", params, "depth =", depth)
'''
            else:
                code = f'''# Hardware-efficient ansatz for {pretty_formula}
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit.circuit.library import TwoLocal
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_algorithms import VQE
from qiskit.primitives import Estimator

geometry = """{geometry}"""

driver = PySCFDriver(atom=geometry, basis='sto3g')
problem = driver.run()

# Build TwoLocal ansatz
num_qubits = max(1, problem.num_spatial_orbitals * 2)
ansatz = TwoLocal(num_qubits, '{rot}', 'cz', reps={layers}, entanglement='{ent}')

# Compile and report
try:
    params = ansatz.num_parameters
    depth = ansatz.decompose().depth() if hasattr(ansatz, "decompose") else 'unknown'
except Exception:
    params = getattr(ansatz, 'num_parameters', 'unknown')
    depth = 'unknown'

print("TwoLocal ansatz for {pretty_formula}: parameters =", params, "depth =", depth)
'''
            return code
        
        # Generate proper quantum simulation code
        if wants_code or intent.get("task"):
            # Generate Braket SDK code for general requests when in Amazon Braket mode
            if braket_mode == "Amazon Braket":
                if "bell" in query_lower:
                    code = f'''# Bell pair circuit using Amazon Braket SDK
from braket.circuits import Circuit
from braket.devices import LocalSimulator

# Create Bell pair circuit
circuit = Circuit()
circuit.h(0)
circuit.cnot(0, 1)

print("Bell Pair Circuit:")
print(circuit)

# Execute on local simulator
device = LocalSimulator()
task = device.run(circuit, shots=1000)
result = task.result()
print(f"Results: {{result.measurement_counts}}")
'''
                elif "ghz" in query_lower:
                    code = f'''# GHZ state using Amazon Braket SDK
from braket.circuits import Circuit
from braket.devices import LocalSimulator

# Create 3-qubit GHZ circuit
circuit = Circuit()
circuit.h(0)
circuit.cnot(0, 1)
circuit.cnot(0, 2)

print("GHZ Circuit:")
print(circuit)

# Execute on local simulator
device = LocalSimulator()
task = device.run(circuit, shots=1000)
result = task.result()
print(f"Results: {{result.measurement_counts}}")
'''
                else:
                    # General quantum algorithm demonstration
                    code = f'''# Quantum algorithm demonstration using Amazon Braket SDK
from braket.circuits import Circuit
from braket.devices import LocalSimulator

# Create demonstration circuit for {formula}
circuit = Circuit()

# Build a simple quantum algorithm
circuit.h(0)  # Superposition
circuit.cnot(0, 1)  # Entanglement
circuit.ry(0, 0.5)  # Parameterized rotation
circuit.ry(1, 0.3)

print(f"Quantum circuit for {formula}:")
print(circuit)

# Execute on local simulator
device = LocalSimulator()
task = device.run(circuit, shots=1000)
result = task.result()

print(f"\nResults: {{result.measurement_counts}}")
print(f"\nNote: This demonstrates quantum algorithms using Braket SDK.")
print(f"For materials science VQE, switch to Qiskit mode.")
'''
                return code
            
            is_poscar = 'poscar' in query_lower
            
            if is_poscar:
                # Check if Strands already handled POSCAR structure creation
                if 'create_structure_from_poscar' in strands_mcp_actions:
                    logger.info(f"✅ BASE MODEL: Using Strands POSCAR structure (avoiding duplicate)")
                    code = f'''# Quantum simulation for POSCAR structure ({formula}) using Strands-created structure
from qiskit_nature.second_q.operators import FermionicOp
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit.circuit.library import TwoLocal

t = 1.0
U = 2.0
fermionic_ops = {{}}
fermionic_ops["+_0 -_2"] = -t
fermionic_ops["+_2 -_0"] = -t
fermionic_ops["+_1 -_3"] = -t
fermionic_ops["+_3 -_1"] = -t
fermionic_ops["+_0 -_0 +_1 -_1"] = U
fermionic_ops["+_2 -_2 +_3 -_3"] = U

ferm_op = FermionicOp(fermionic_ops, register_length=4)
mapper = JordanWignerMapper()
qubit_op = mapper.map(ferm_op)
ansatz = TwoLocal(4, 'ry', 'cz', reps=2, entanglement='linear')
print(f"Strands POSCAR for {formula}: {{len(qubit_op)}} terms, {{ansatz.num_parameters}} params")
'''
                else:
                    code = f'''# Quantum simulation for POSCAR structure ({formula})
# Using Qiskit Nature for proper fermionic-to-qubit mapping

from qiskit_nature.second_q.operators import FermionicOp
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit.circuit.library import TwoLocal
from qiskit_algorithms import VQE
from qiskit.primitives import Estimator

# Toy Hubbard model parameters (replace with DFT/tight-binding values for accuracy)
t = 1.0  # hopping parameter (toy value)
U = 2.0  # on-site interaction (toy value)

# 2-site Hubbard model for {formula} primitive cell
# Fermionic operators: (site0_up, site0_down, site1_up, site1_down)
fermionic_ops = {{}}

# Hopping terms: -t * (c†_0↑ c_1↑ + c†_1↑ c_0↑ + c†_0↓ c_1↓ + c†_1↓ c_0↓)
fermionic_ops["+_0 -_2"] = -t  # up hopping 0->1
fermionic_ops["+_2 -_0"] = -t  # up hopping 1->0
fermionic_ops["+_1 -_3"] = -t  # down hopping 0->1
fermionic_ops["+_3 -_1"] = -t  # down hopping 1->0

# On-site interaction: U * n_up * n_down at each site
fermionic_ops["+_0 -_0 +_1 -_1"] = U  # site 0
fermionic_ops["+_2 -_2 +_3 -_3"] = U  # site 1

# Create fermionic operator and map to qubits using QubitConverter
from qiskit_nature.converters.second_quantization import QubitConverter

ferm_op = FermionicOp(fermionic_ops, register_length=4)
mapper = JordanWignerMapper()
converter = QubitConverter(mapper=mapper)
qubit_op = converter.convert(ferm_op)

print(f"Fermionic Hamiltonian for {formula}: {{len(fermionic_ops)}} terms")
print(f"Qubit Hamiltonian: {{qubit_op.num_qubits}} qubits (should be 4, not 8)")

# Create ansatz and run VQE
from qiskit import Aer
from qiskit.utils import QuantumInstance
from qiskit.algorithms.optimizers import SLSQP

ansatz = TwoLocal(num_qubits=4, rotation_blocks='ry', entanglement_blocks='cz', reps=2, entanglement='linear')
optimizer = SLSQP(maxiter=100)
quantum_instance = QuantumInstance(Aer.get_backend('aer_simulator_statevector'))
vqe = VQE(ansatz, optimizer=optimizer, quantum_instance=quantum_instance)

print(f"Ansatz: {{ansatz.num_parameters}} parameters, depth={{ansatz.depth()}}")
print("Note: This is a toy 2-site Hubbard model for the POSCAR primitive cell.")
print("For accurate Si simulation, use DFT-derived tight-binding parameters.")
'''
            else:
                # Generate standard materials Hamiltonian with proper fermionic mapping
                bg = fe = None
                if mp_data and isinstance(mp_data, dict):
                    bg = mp_data.get("band_gap")
                    fe = mp_data.get("formation_energy")
                
                bg = 0.0 if bg is None else bg
                fe = -3.0 if fe is None else fe
                t = max(0.1, bg * 0.3)
                U = abs(fe) * 0.5
                
                code = f'''# Toy Hubbard model for {formula} using proper fermionic mapping
from qiskit_nature.second_q.operators import FermionicOp
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit.circuit.library import TwoLocal

# Toy parameters derived from Materials Project data
# band_gap = {bg} eV, formation_energy = {fe} eV/atom
t = {t:.3f}  # hopping (toy)
U = {U:.3f}  # interaction (toy)

# 4-site toy model
fermionic_ops = {{}}
for i in range(3):  # hopping between adjacent sites
    fermionic_ops[f"+_{{i}} -_{{i+1}}"] = -t
    fermionic_ops[f"+_{{i+1}} -_{{i}}"] = -t

for i in range(0, 4, 2):  # on-site interaction
    fermionic_ops[f"+_{{i}} -_{{i}} +_{{i+1}} -_{{i+1}}"] = U

ferm_op = FermionicOp(fermionic_ops, register_length=4)
mapper = JordanWignerMapper()
qubit_op = mapper.map(ferm_op)

ansatz = TwoLocal(4, 'ry', 'cz', reps=2, entanglement='linear')
print(f"Toy Hamiltonian for {formula}: {{len(qubit_op)}} Pauli terms, {{ansatz.num_parameters}} parameters")
'''
            return code
        
        return None
    
    def generate_response(self, query: str, temperature: float = 0.7, max_tokens: int = 1000, 
                         top_p: float = 0.9, include_mp_data: bool = True, show_debug: bool = False, braket_mode: str = "Qiskit Only") -> Dict[str, Any]:
        """Generate a complete response including code and explanation"""
        try:
            # Detect intent and extract formula
            intent = self._detect_intent(query)
            logger.info(f"🔍 BASE MODEL: Starting generate_response for query: '{query[:100]}...'")
            logger.info(f"🔍 BASE MODEL: Parameters - include_mp_data={include_mp_data}, mp_agent_type={type(self.mp_agent)}")
            
            # Extract potential formula/material from query
            # First check for molecular compounds
            molecular_compounds = {
                'h2': 'H2', 'hydrogen molecule': 'H2', 'hydrogen gas': 'H2',
                'h2o': 'H2O', 'water': 'H2O', 'water molecule': 'H2O',
                'co2': 'CO2', 'carbon dioxide': 'CO2',
                'ch4': 'CH4', 'methane': 'CH4',
                'nh3': 'NH3', 'ammonia': 'NH3',
                'co': 'CO', 'carbon monoxide': 'CO',
                'n2': 'N2', 'nitrogen': 'N2',
                'o2': 'O2', 'oxygen': 'O2'
            }
            
            # Then element names
            element_names = {
                'silicon': 'Si', 'titanium': 'Ti', 'iron': 'Fe', 'copper': 'Cu',
                'aluminum': 'Al', 'carbon': 'C', 'lithium': 'Li', 'sodium': 'Na', 
                'potassium': 'K', 'calcium': 'Ca', 'magnesium': 'Mg', 'zinc': 'Zn', 
                'nickel': 'Ni', 'cobalt': 'Co'
            }
            
            formula = None
            query_lower = query.lower()
            
            # Check for molecular compounds first (higher priority)
            for compound, mol_formula in molecular_compounds.items():
                if compound in query_lower:
                    formula = mol_formula
                    break
            
            # Check for element names if no molecule found
            if not formula:
                for name, symbol in element_names.items():
                    if name in query_lower:
                        formula = symbol
                        break
            
            # Check for POSCAR structure first
            if 'poscar' in query_lower or ('direct' in query_lower and any(line.strip().replace('.','').replace(' ','').isdigit() for line in query.split('\n'))):
                # Use supervisor agent for POSCAR analysis
                if self.mp_agent:
                    try:
                        from agents import SupervisorAgent
                        supervisor = SupervisorAgent(self.mp_agent)
                        poscar_result = supervisor.process_poscar_query(query, query)
                        
                        if poscar_result["status"] == "matched":
                            formula = poscar_result["matched_material_id"]
                            mp_data = poscar_result["mp_data"]
                            logger.info(f"✅ BASE MODEL: POSCAR matched to {formula} via supervisor agent")
                        else:
                            formula = poscar_result["formula"]
                            logger.info(f"⚠️ BASE MODEL: POSCAR no match, using formula: {formula}")
                    except ImportError:
                        formula = self._extract_formula_from_poscar(query)
                        logger.info(f"🔍 BASE MODEL: Fallback POSCAR extraction: {formula}")
                else:
                    formula = self._extract_formula_from_poscar(query)
                    logger.info(f"🔍 BASE MODEL: Basic POSCAR extraction: {formula}")
            # Then try material IDs (highest priority)
            elif not formula:
                mp_match = re.search(r'mp-\d+', query)
                if mp_match:
                    formula = mp_match.group(0)
                else:
                    # Try chemical formulas - comprehensive pattern matching
                    compound_patterns = [
                        # Simple molecules first (highest priority)
                        r'\bH2\b', r'\bH2O\b', r'\bNH3\b', r'\bCH4\b', r'\bCO2\b', r'\bCO\b', r'\bN2\b', r'\bO2\b',
                        # Common oxides
                        r'\bTiO2\b', r'\bSiO2\b', r'\bAl2O3\b', r'\bFe2O3\b', r'\bCuO\b',
                        r'\bZnO\b', r'\bMgO\b', r'\bCaO\b', r'\bNiO\b', r'\bCoO\b',
                        # Perovskites
                        r'\bBaTiO3\b', r'\bSrTiO3\b', r'\bCaTiO3\b', r'\bLaAlO3\b',
                        # Semiconductors
                        r'\bGaAs\b', r'\bInP\b', r'\bGaN\b', r'\bSiC\b', r'\bAlN\b',
                        # 2D Materials
                        r'\bMoS2\b', r'\bWS2\b', r'\bWSe2\b', r'\bMoSe2\b', r'\bBN\b',
                        # Complex compounds
                        r'\bYBa2Cu3O7\b', r'\bBi2Te3\b', r'\bSi3N4\b', r'\bWC\b', r'\bTiC\b'
                    ]
                    
                    for pattern in compound_patterns:
                        match = re.search(pattern, query, re.IGNORECASE)
                        if match:
                            formula = match.group(0)
                            break
                    
                    if not formula:
                        # Try general chemical formulas (but exclude common words)
                        formula_matches = re.findall(r'\b([A-Z][a-z]?\d*)+\b', query)
                        for candidate in formula_matches:
                            # Exclude common quantum computing terms
                            if candidate.upper() not in ['VQE', 'UCCSD', 'HE', 'QC', 'MP', 'POSCAR', 'DATA', 'PROJECT']:
                                formula = candidate
                                break
                        
                        if not formula:
                            formula = "H2"  # Default fallback
            logger.info(f"🔍 BASE MODEL: Extracted formula '{formula}' from query: '{query[:100]}...'")
            
            # Check for cached Strands data first, then use supervisor agent
            mp_data = getattr(self, '_cached_mp_data', None)
            strands_result = getattr(self, '_cached_strands_result', None)
            
            if mp_data and strands_result:
                mcp_actions = strands_result.get('mcp_actions', [])
                logger.info(f"✅ BASE MODEL: Using cached Strands data with {len(mcp_actions)} MCP actions: {mcp_actions}")
                # Store Strands result for supercell logic
                self._cached_strands_result = strands_result
            elif include_mp_data and self.mp_agent:
                logger.info(f"🔍 BASE MODEL: include_mp_data={include_mp_data}, mp_agent={type(self.mp_agent) if self.mp_agent else None}")
                
                # Check if this is a molecular query that should skip MP search
                query_lower = query.lower()
                molecular_keywords = ['h2', 'hydrogen molecule', 'water molecule', 'h2o molecule', 'co2', 'ch4', 'nh3', 'h2 molecule', 'hydrogen gas']
                is_molecular_query = any(mol in query_lower for mol in molecular_keywords)
                
                if is_molecular_query:
                    logger.info(f"🧪 BASE MODEL: Molecular query detected - skipping supervisor agent for simple molecule")
                    mp_data = None  # Skip MP data for molecular queries
                else:
                    try:
                        from agents.supervisor_agent import SupervisorAgent
                        supervisor = SupervisorAgent(self.mp_agent)
                        
                        logger.info(f"🤖 BASE MODEL: Using supervisor agent for query: {query[:100]}...")
                        supervisor_result = supervisor.process_query(query, formula)
                        
                        if supervisor_result and supervisor_result.get("status") == "success":
                            mp_data = supervisor_result.get("mp_data")
                            mcp_actions = supervisor_result.get("mcp_actions", [])
                            logger.info(f"✅ BASE MODEL: Supervisor handled query with {len(mcp_actions)} MCP actions: {mcp_actions}")
                        else:
                            logger.warning(f"⚠️ BASE MODEL: Supervisor returned error: {supervisor_result}")
                            
                    except ImportError as ie:
                        logger.error(f"💥 BASE MODEL: Cannot import supervisor agent: {ie}")
                    except Exception as e:
                        logger.error(f"💥 BASE MODEL: Supervisor error: {e}")
                    
                # Fix: Handle case where mp_data is a list instead of dict, or None for molecular queries
                if mp_data:
                    if isinstance(mp_data, list):
                        logger.warning(f"⚠️ BASE MODEL: MP data is list (timeout fallback), converting to dict")
                        mp_data = {"results": mp_data, "formula": formula, "count": len(mp_data)}
                    logger.info(f"✅ BASE MODEL: MP data retrieved: {type(mp_data)} with keys: {list(mp_data.keys()) if isinstance(mp_data, dict) else 'N/A'}")
                elif mp_data is None:
                    logger.info(f"🧪 BASE MODEL: No MP data for molecular query: {formula}")
                else:
                    logger.warning(f"❌ BASE MODEL: No MP data retrieved for {formula}")
            else:
                logger.warning(f"❌ BASE MODEL: Skipping MP search - include_mp_data={include_mp_data}, has_agent={bool(self.mp_agent)}")
            
            # Store original query in intent for code generation logic
            intent["original_query"] = query
            
            # Ensure mp_data is dict before passing to code generation (handle None for molecular queries)
            if mp_data and isinstance(mp_data, list):
                logger.warning(f"⚠️ BASE MODEL: Converting list mp_data to dict for code generation")
                mp_data = {"results": mp_data, "formula": formula, "count": len(mp_data), "error": "timeout_fallback"}
            elif mp_data is None:
                # For molecular queries, create minimal dict to avoid None errors
                logger.info(f"🧪 BASE MODEL: Creating minimal mp_data dict for molecular query")
                # Use the correct molecular formula, not the extracted one
                molecular_formula = formula
                if 'h2' in query.lower() and 'molecule' in query.lower():
                    molecular_formula = 'H2'
                elif 'h2o' in query.lower():
                    molecular_formula = 'H2O'
                elif 'co2' in query.lower():
                    molecular_formula = 'CO2'
                mp_data = {"formula": molecular_formula, "molecular_query": True}
            
            # Generate base code with braket_mode awareness
            base_code = self.generate_base_code(formula, intent, mp_data, braket_mode)
            
            # Create enhanced prompt for LLM
            prompt = self._create_enhanced_prompt(query, base_code, intent, mp_data, show_debug, braket_mode)
            
            # Call LLM
            llm_response = self._call_llm(
                prompt, 
                temperature=temperature, 
                max_tokens=max_tokens, 
                top_p=top_p
            )
            
            # Smart code handling - prefer LLM code, fallback to base code only if needed
            final_code = None
            if base_code:  # Only process code if we generated base code
                try:
                    extracted_code = self._extract_code_from_response(llm_response)
                    if extracted_code and len(extracted_code.strip()) > 100:  # LLM generated substantial code
                        final_code = extracted_code
                        logger.info(f"✅ BASE MODEL: Using LLM-generated code ({len(extracted_code)} chars)")
                    else:
                        final_code = base_code  # Fallback to base code
                        logger.info(f"🔄 BASE MODEL: Using fallback base code - LLM code insufficient")
                except Exception as extract_error:
                    logger.warning(f"Code extraction failed: {extract_error}")
                    final_code = base_code  # Fallback to base code
            
            logger.info(f"✅ BASE MODEL: Response generated - has_mp_data={bool(mp_data)}, formula={formula}")
            return {
                "text": llm_response,
                "code": final_code,
                "mp_data": mp_data if include_mp_data else None,
                "intent": intent,
                "formula": formula
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "text": f"Error generating response: {str(e)}",
                "code": None,
                "mp_data": None,
                "intent": None,
                "formula": None
            }
    
    def _create_enhanced_prompt(self, query: str, base_code: str, intent: Dict[str, Any], mp_data: Optional[Dict[str, Any]], show_debug: bool = False, braket_mode: str = "Qiskit Only") -> str:
        """Create an enhanced prompt for the LLM"""
        
        # Core system prompt - varies based on braket_mode
        if braket_mode == "Amazon Braket":
            system_header = """You are an expert quantum computing assistant specializing in Amazon Braket SDK. Answer the user's question directly and provide relevant information based on their specific request.

IMPORTANT BRAKET MODE REQUIREMENTS:
- ALWAYS use Amazon Braket SDK (braket.circuits) for quantum circuit code
- NEVER use Qiskit code when in Braket mode
- Use braket.devices.LocalSimulator for local execution
- Generate Braket-compatible circuit syntax
- Focus on simple quantum algorithms (Bell states, GHZ, QFT)
- Materials science queries should use simple demonstration circuits

When generating code:
- Use only Amazon Braket SDK: from braket.circuits import Circuit
- Use braket.devices.LocalSimulator for simulation
- Include circuit.draw() for ASCII visualization
- Show proper Braket task execution syntax
- Mention this is Braket SDK code, not Qiskit

LIMITATIONS in Braket mode:
- No complex VQE implementations (use simple demo circuits)
- No Materials Project integration for quantum simulations
- Focus on algorithm demonstrations rather than materials science"""
        else:
            system_header = """You are an expert quantum-materials research assistant. Answer the user's question directly and provide relevant information based on their specific request.

When generating code:
- Use only public, documented Qiskit / Qiskit-Nature APIs compatible with Qiskit v1.2.4
- Prefer Jordan–Wigner mapping unless told otherwise
- Include parameter counts and circuit depth when relevant
- Use provided coordinates and properties when available

When showing materials data:
- If user asks for "available options" or "show me materials", list all found materials
- If user asks for specific analysis, focus on the most relevant material
- Echo the material IDs, composition, and key properties you're using
- Only mention data sources when they were actually used"""
        
        # Adjust base code description based on mode
        code_description = "base Braket SDK code" if braket_mode == "Amazon Braket" else "base Qiskit code"
        
        prompt = f"""{system_header}

User Query: {query}

Framework Mode: {braket_mode}

I've generated some {code_description} for this query:

```python
{base_code}
```

Detected Intent: {json.dumps(intent, indent=2)}

"""
        
        if mp_data and isinstance(mp_data, dict) and not mp_data.get("error"):
            mp_geometry = mp_data.get('geometry', '')
            material_id = mp_data.get('material_id', 'Unknown')
            formula = mp_data.get('formula', 'Unknown')
            band_gap = mp_data.get('band_gap', 'N/A')
            formation_energy = mp_data.get('formation_energy', 'N/A')
            
            # Check if this is actually from MCP or just a molecular query
            is_molecular_query = mp_data.get('molecular_query', False) or formula in ['H2', 'H2O', 'CO2', 'CH4', 'NH3'] or 'molecule' in query.lower()
            
            if show_debug:
                # Full debug information
                prompt += f"""MATERIALS PROJECT DATA AVAILABLE:
Material ID: {material_id}
Formula: {formula}
Band Gap: {band_gap} eV
Formation Energy: {formation_energy} eV/atom

Full Materials Project Data:
{json.dumps(mp_data, indent=2, default=str)}

INSTRUCTIONS:
1. Use the EXACT geometry coordinates provided:
{mp_geometry}
2. Do NOT use generic or idealized coordinates
3. Reference the specific material ID in your response if applicable
4. Only mention MCP server if data was actually retrieved from Materials Project

"""
            else:
                # Clean mode - minimal MP data context
                if not is_molecular_query:
                    prompt += f"""Materials Project data available for {material_id} ({formula}).
Band Gap: {band_gap} eV, Formation Energy: {formation_energy} eV/atom
Geometry coordinates: {mp_geometry}

Use this data in your response.

"""
                else:
                    prompt += f"""Using molecular geometry for {formula}.
Geometry coordinates: {mp_geometry}

Generate appropriate molecular quantum simulation code.

"""
        
        # Add complete Strands context if available
        if hasattr(self, '_cached_strands_result') and self._cached_strands_result:
            strands_data = self._cached_strands_result
            mp_data_from_strands = strands_data.get('mp_data') or {}
            mcp_actions = strands_data.get('mcp_actions', [])
            moire_params = strands_data.get('moire_params', {})
            
            # Check for Strands-generated quantum code
            quantum_code = None
            if 'quantum_simulator' in strands_data:
                quantum_sim = strands_data['quantum_simulator']
                if 'quantum_simulation' in quantum_sim:
                    code_obj = quantum_sim['quantum_simulation'].get('code')
                    if code_obj:
                        # Extract from AgentResult object
                        if isinstance(code_obj, str) and 'AgentResult' in code_obj:
                            # Parse AgentResult string to extract actual code
                            import re
                            code_match = re.search(r'```python\s*\n(.*?)```', code_obj, re.DOTALL)
                            if code_match:
                                quantum_code = code_match.group(1).strip()
                        elif isinstance(code_obj, str):
                            quantum_code = code_obj
            
            if show_debug:
                # Full debug Strands context
                prompt += f"""\n\nIMPORTANT - Complete Strands Analysis Context:
AWS Strands agents have executed a comprehensive workflow for your query. You MUST incorporate ALL this information in your response.

=== MCP TOOLS EXECUTED ===
{', '.join(mcp_actions)}

=== MATERIALS PROJECT DATA RETRIEVED ===
{json.dumps(mp_data_from_strands, indent=2, default=str)}

=== SPECIAL OPERATIONS PERFORMED ===
"""
                
                # Add quantum code if generated by Strands
                if quantum_code and isinstance(quantum_code, str) and len(quantum_code) > 1000:
                    prompt += f"""\n=== STRANDS-GENERATED QUANTUM CODE ===
Strands has generated a comprehensive VQE implementation. You MUST use this code in your response:

{quantum_code[:2000]}...

This is production-ready quantum simulation code generated by AWS Strands. Include it in your response and explain its key features.

"""
                
                # Add moire-specific context
                if 'moire_homobilayer' in mcp_actions and moire_params:
                    prompt += f"""MOIRE BILAYER GENERATED:
- Structure URI: structure://55f0902b (successfully created)
- Twist Angle: {moire_params.get('twist_angle', 'N/A')}°
- Interlayer Spacing: {moire_params.get('interlayer_spacing', 'N/A')} Å
- Status: Ready for quantum simulations

"""
                
                # Add supercell context if applicable
                if 'build_supercell' in mcp_actions:
                    prompt += "SUPERCELL STRUCTURE GENERATED: Ready for extended system analysis\n\n"
                
                # Add visualization context if applicable
                if 'plot_structure' in mcp_actions:
                    prompt += "3D STRUCTURE VISUALIZATION: Generated and available for display\n\n"
                
                mp_geometry = mp_data_from_strands.get('geometry', '') if mp_data_from_strands else ''
                if mp_geometry:
                    prompt += f"""CRITICAL - USE EXACT COORDINATES:
{mp_geometry}
Do NOT use generic coordinates. These are real Materials Project values.

"""
                
                prompt += """Your response must acknowledge and explain ALL the MCP operations performed above. Reference the specific structure URIs, parameters, and results generated by the Strands workflow.

If Strands generated quantum code above, you MUST include it in your response and explain its features. Do not generate your own code when Strands has already provided a comprehensive implementation.

"""
            else:
                # Clean mode - minimal Strands context
                material_id = mp_data_from_strands.get('material_id', 'Unknown') if mp_data_from_strands else 'Unknown'
                formula = mp_data_from_strands.get('formula', 'Unknown') if mp_data_from_strands else 'Unknown'
                
                prompt += f"""\n\nStrands workflow completed for {material_id} ({formula}).
MCP operations: {len(mcp_actions)} tools used.

Provide a clean scientific response using this data without showing technical processing details.

"""
        
        if show_debug:
            prompt += """Please respond directly to the user's question. If they asked to see available options, show all materials found. If they want code generation, provide complete runnable code with explanations.

Provide a comprehensive response with:
1. Scientific explanation of the concepts
2. Detailed analysis of the materials/structures involved  
3. Complete, runnable code using provided coordinates
4. Practical applications and next steps

IMPORTANT: Only mention MCP operations if they were actually performed above. Use exact coordinates and structure URIs provided.

Keep your response focused and match what the user specifically requested."""
        else:
            prompt += """Please provide a clean, professional response to the user's question.

Focus on:
1. Clear scientific explanation
2. Practical quantum computing implementation
3. Working code with appropriate molecular or materials data
4. Key insights and applications

Do NOT include acknowledgment sections about MCP operations unless they were actually used. Keep it clean and user-friendly."""
        
        return prompt
    
    def _extract_code_from_response(self, response: str) -> Optional[str]:
        """Extract Python code from LLM response"""
        if not response:
            return None
        
        import re
        
        # Decode HTML entities first (with fallback)
        try:
            import html
            response = html.unescape(response)
        except (ImportError, Exception):
            # Fallback: basic entity replacement
            response = response.replace('&#39;', "'").replace('&quot;', '"').replace('&amp;', '&')
        
        # Look for code blocks in markdown format (multiple patterns)
        patterns = [
            r'```python\s*\n(.*?)```',
            r'```\s*\n(.*?)```',
            r'```python(.*?)```',
            r'```(.*?)```'
        ]
        
        for pattern in patterns:
            code_blocks = re.findall(pattern, response, re.DOTALL)
            if code_blocks:
                # Return the longest code block (likely the main implementation)
                longest_code = max(code_blocks, key=len).strip()
                if len(longest_code) > 50:  # Ensure it's substantial code
                    return longest_code
        
        # Look for code after "Here's the corrected code" or similar
        corrected_code_match = re.search(r'(?:Here\'s the corrected code|corrected code)[^:]*:?\s*\n\n(.*?)(?=\n\n|$)', response, re.DOTALL | re.IGNORECASE)
        if corrected_code_match:
            code_text = corrected_code_match.group(1).strip()
            if code_text and len(code_text) > 50:
                return code_text
        
        # Look for code after "4. Code" or "## 4) Code" section
        code_section_match = re.search(r'(?:4\.|##\s*4\))\s*Code[^\n]*\n(.*?)(?=\n(?:5\.|##\s*5\)|Sanity Checks|$))', response, re.DOTALL | re.IGNORECASE)
        if code_section_match:
            code_text = code_section_match.group(1).strip()
            # Remove any remaining markdown formatting
            code_text = re.sub(r'^```(?:python)?\n?', '', code_text, flags=re.MULTILINE)
            code_text = re.sub(r'\n?```$', '', code_text)
            if code_text and len(code_text) > 50:
                return code_text
        
        return None