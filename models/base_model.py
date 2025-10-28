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
    
    def generate_base_code(self, formula: str, intent: Dict[str, Any], mp_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
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
        if intent.get("task") == "supercell_vqe" and self.mp_agent and mp_data:
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
        

        # Generate molecular code if geometry available
        if intent.get("task") in ("vqe", "ansatz", "initial_state") and geometry:
            family = intent.get("ansatz_family") or "two_local"
            mapping = intent.get("mapping") or "jordan_wigner"
            layers = intent.get("layers") or 2
            ent = intent.get("entanglement") or "linear"
            rot = intent.get("rotations") or "ry"
            
            # Check if visualization is requested
            wants_visualization = any(term in query_lower for term in ["3d", "visualiz", "plot", "structure", "crystal"])
            
            if wants_visualization:
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
            is_poscar = 'poscar' in query_lower
            
            if is_poscar:
                # Generate proper POSCAR-based quantum simulation
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
                if isinstance(mp_data, dict):
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
                         top_p: float = 0.9, include_mp_data: bool = True) -> Dict[str, Any]:
        """Generate a complete response including code and explanation"""
        try:
            # Detect intent and extract formula
            intent = self._detect_intent(query)
            logger.info(f"🔍 BASE MODEL: Starting generate_response for query: '{query[:100]}...'")
            logger.info(f"🔍 BASE MODEL: Parameters - include_mp_data={include_mp_data}, mp_agent_type={type(self.mp_agent)}")
            
            # Extract potential formula/material from query
            # First try element names
            element_names = {
                'silicon': 'Si', 'titanium': 'Ti', 'iron': 'Fe', 'copper': 'Cu',
                'aluminum': 'Al', 'carbon': 'C', 'oxygen': 'O', 'hydrogen': 'H',
                'lithium': 'Li', 'sodium': 'Na', 'potassium': 'K', 'calcium': 'Ca',
                'magnesium': 'Mg', 'zinc': 'Zn', 'nickel': 'Ni', 'cobalt': 'Co'
            }
            
            formula = None
            query_lower = query.lower()
            
            # Check for element names first
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
                    # Try chemical formulas (but exclude common words)
                    formula_match = re.search(r'\b([A-Z][a-z]?\d*)+\b', query)
                    if formula_match:
                        candidate = formula_match.group(0)
                        # Exclude common quantum computing terms
                        if candidate.upper() not in ['VQE', 'UCCSD', 'HE', 'QC', 'MP', 'POSCAR']:
                            formula = candidate
                        else:
                            formula = "H2"  # Default fallback
                    else:
                        formula = "H2"
            logger.info(f"🔍 BASE MODEL: Extracted formula '{formula}' from query: '{query[:100]}...'")
            
            # Use supervisor agent to handle MCP tool selection and data retrieval
            mp_data = None
            logger.info(f"🔍 BASE MODEL: include_mp_data={include_mp_data}, mp_agent={type(self.mp_agent) if self.mp_agent else None}")
            if include_mp_data and self.mp_agent:
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
                    
                if mp_data:
                    logger.info(f"✅ BASE MODEL: MP data retrieved: {type(mp_data)} with keys: {list(mp_data.keys()) if isinstance(mp_data, dict) else 'N/A'}")
                else:
                    logger.warning(f"❌ BASE MODEL: No MP data retrieved for {formula}")
            else:
                logger.warning(f"❌ BASE MODEL: Skipping MP search - include_mp_data={include_mp_data}, has_agent={bool(self.mp_agent)}")
            
            # Store original query in intent for code generation logic
            intent["original_query"] = query
            
            # Generate base code only if needed
            base_code = self.generate_base_code(formula, intent, mp_data)
            
            # Create enhanced prompt for LLM
            prompt = self._create_enhanced_prompt(query, base_code, intent, mp_data)
            
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
    
    def _create_enhanced_prompt(self, query: str, base_code: str, intent: Dict[str, Any], mp_data: Optional[Dict[str, Any]]) -> str:
        """Create an enhanced prompt for the LLM"""
        
        # Core system prompt for all models
        system_header = """You are an expert quantum-materials research assistant. Answer the user's question directly and provide relevant information based on their specific request.

When generating code:
- Use only public, documented Qiskit / Qiskit-Nature APIs compatible with Qiskit v1.2.4
- Prefer Jordan–Wigner mapping unless told otherwise
- Include parameter counts and circuit depth when relevant

When showing materials data:
- If user asks for "available options" or "show me materials", list all found materials
- If user asks for specific analysis, focus on the most relevant material
- Always echo the material IDs, composition, and key properties you're using"""
        
        prompt = f"""{system_header}

User Query: {query}

I've generated some base Qiskit code for this query:

```python
{base_code}
```

Detected Intent: {json.dumps(intent, indent=2)}

"""
        
        if mp_data and not mp_data.get("error"):
            prompt += f"""Materials Project Data:
{json.dumps(mp_data, indent=2, default=str)}

"""
        
        prompt += """Please respond directly to the user's question. If they asked to see available options, show all materials found. If they want code generation, provide complete runnable code with explanations.

Keep your response focused and match what the user specifically requested."""
        
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