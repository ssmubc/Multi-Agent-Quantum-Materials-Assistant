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
            "requirements": []
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
        
        return intent
    
    def generate_base_code(self, formula: str, intent: Dict[str, Any], mp_data: Optional[Dict[str, Any]] = None) -> str:
        """Generate base Qiskit code based on formula and intent"""
        geometry = None
        pretty_formula = formula
        
        # Try to get geometry
        if self._is_small_molecule(formula):
            geometry = self.geometries[formula]
            pretty_formula = formula
        elif formula.lower().startswith("mp-") and mp_data and isinstance(mp_data, dict):
            geometry = mp_data.get("geometry")
            pretty_formula = mp_data.get("formula", formula)
        elif self.mp_agent:
            mp_result = mp_data or self.mp_agent.search(formula)
            if isinstance(mp_result, dict) and not mp_result.get("error"):
                geometry = mp_result.get("geometry")
                pretty_formula = mp_result.get("formula", formula)
                mp_data = mp_result
        
        # Generate molecular code if geometry available
        if intent.get("task") in ("vqe", "ansatz", "initial_state") and geometry:
            family = intent.get("ansatz_family") or "two_local"
            mapping = intent.get("mapping") or "jordan_wigner"
            layers = intent.get("layers") or 2
            ent = intent.get("entanglement") or "linear"
            rot = intent.get("rotations") or "ry"
            
            if family == "uccsd":
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
        
        # Generate materials Hamiltonian code
        ident = self._sanitize_ident(formula)
        bg = fe = None
        if isinstance(mp_data, dict):
            bg = mp_data.get("band_gap")
            fe = mp_data.get("formation_energy")
        elif self.mp_agent:
            mp_try = self.mp_agent.search(formula)
            if isinstance(mp_try, dict) and not mp_try.get("error"):
                bg = mp_try.get("band_gap")
                fe = mp_try.get("formation_energy")
        
        bg = 0.0 if bg is None else bg
        fe = -3.0 if fe is None else fe
        U = abs(fe) * 0.5
        t = max(0.0, bg) * 0.3
        
        code = f'''# Effective Hamiltonian for {formula} (toy Hubbard-like)
from qiskit.quantum_info import SparsePauliOp
from qiskit.circuit.library import TwoLocal

# Materials Project derived values
# band_gap = {bg}
# formation_energy = {fe}
U = {U:.6f}
t = {t:.6f}

num_qubits = 8  # toy active space
hopping_terms = []
for i in range(num_qubits-1):
    pauli_str = ['I'] * num_qubits
    pauli_str[i] = 'X'
    pauli_str[i+1] = 'X'
    hopping_terms.append((''.join(pauli_str), -t))

interaction_terms = []
for i in range(0, num_qubits, 2):
    pauli_str = ['I'] * num_qubits
    pauli_str[i] = 'Z'
    if i+1 < num_qubits:
        pauli_str[i+1] = 'Z'
    interaction_terms.append((''.join(pauli_str), U))

hamiltonian = SparsePauliOp.from_list(hopping_terms + interaction_terms)
ansatz = TwoLocal(num_qubits, 'ry', 'cz', reps=2, entanglement='linear')

print("Effective Hamiltonian for {formula}: qubits =", num_qubits, "terms =", len(hamiltonian))
'''
        return code
    
    def generate_response(self, query: str, temperature: float = 0.7, max_tokens: int = 1000, 
                         top_p: float = 0.9, include_mp_data: bool = True) -> Dict[str, Any]:
        """Generate a complete response including code and explanation"""
        try:
            # Detect intent and extract formula
            intent = self._detect_intent(query)
            
            # Extract potential formula/material from query
            formula_match = re.search(r'\b([A-Z][a-z]?\d*)+\b|mp-\d+', query)
            formula = formula_match.group(0) if formula_match else "H2"
            
            # Get Materials Project data if requested
            mp_data = None
            if include_mp_data and self.mp_agent:
                try:
                    mp_data = self.mp_agent.search(formula)
                except Exception as e:
                    logger.warning(f"MP API error: {e}")
            
            # Generate base code
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
            
            return {
                "text": llm_response,
                "code": base_code,
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
        prompt = f"""You are an expert in quantum computing and materials science. 

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
        
        prompt += """Please provide:
1. An explanation of the quantum computing concepts involved
2. How the generated code addresses the user's query
3. Any improvements or alternatives you would suggest
4. Relevant physics/chemistry background if applicable

Keep your response focused, technical, and educational."""
        
        return prompt