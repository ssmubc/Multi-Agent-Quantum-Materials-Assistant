import logging
import json

logger = logging.getLogger(__name__)

# Mock classes for local testing
class MockAgent:
    def __init__(self, model=None, tools=None, system_prompt=None):
        self.model = model
        self.tools = tools
        self.system_prompt = system_prompt
    
    def __call__(self, prompt):
        return type('Response', (), {'text': f"Mock response to: {prompt[:50]}..."})() 

# Set defaults
Agent = MockAgent
use_aws = None
retrieve = None

try:
    from strands_agents import Agent as RealAgent
    from strands_agents_tools import use_aws as real_use_aws, retrieve as real_retrieve
    Agent = RealAgent
    use_aws = real_use_aws
    retrieve = real_retrieve
except ImportError as e:
    logger.warning(f"Strands not available locally: {e}")

class StrandsDFTAgent:
    """Strands-based DFT parameter extraction agent"""
    
    def __init__(self):
        if use_aws:
            self.agent = Agent(
                model="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
                tools=[use_aws, retrieve]
            )
        else:
            self.agent = MockAgent()
        
        # Literature DFT parameters for validation (from original dft_parameter_agent)
        self.dft_database = {
            "mp-149": {  # Diamond Silicon
                "t_hopping": 2.8,  # eV (nearest neighbor hopping)
                "U_onsite": 0.5,   # eV (Hubbard U)
                "band_gap_dft": 0.61,  # eV (DFT band gap)
                "lattice_constant": 5.43,  # Å
                "source": "DFT_literature"
            },
            "mp-66": {   # Diamond Carbon
                "t_hopping": 3.2,
                "U_onsite": 0.8, 
                "band_gap_dft": 5.5,
                "lattice_constant": 3.57,
                "source": "DFT_literature"
            },
            "mp-72": {   # Germanium
                "t_hopping": 2.4,
                "U_onsite": 0.4,
                "band_gap_dft": 0.74,
                "lattice_constant": 5.66,
                "source": "DFT_literature"
            }
        }
    
    def extract_dft_parameters(self, material_id: str, mp_data: dict) -> dict:
        """Extract DFT parameters using Strands agent intelligence"""
        
        prompt = f"""
        Extract realistic DFT parameters for material {material_id}.
        
        Materials Project data: {json.dumps(mp_data, indent=2)}
        
        Known literature values for reference:
        {json.dumps(self.dft_database, indent=2)}
        
        Extract/estimate these parameters with physical reasoning:
        - t_hopping (eV): nearest-neighbor hopping parameter
        - U_onsite (eV): Hubbard interaction parameter  
        - band_gap_dft (eV): DFT-calculated band gap
        - lattice_constant (Å): lattice parameter if available
        
        Use empirical correlations:
        - For semiconductors (band_gap > 0.1 eV): t_hopping = max(1.0, band_gap * 4.5)
        - For metals: t_hopping = 3.0
        - U_onsite from formation energy: max(0.2, abs(formation_energy) * 0.3)
        
        Return JSON: {{"t_hopping": float, "U_onsite": float, "band_gap_dft": float, "lattice_constant": float, "source": "literature|estimated", "reasoning": "explanation"}}
        """
        
        try:
            response = self.agent(prompt)
            params = self._parse_parameters(response)
            
            # Validate parameters
            if self._validate_parameters(params):
                logger.info(f"✅ STRANDS DFT: Extracted parameters for {material_id}")
                return params
            else:
                logger.warning(f"⚠️ STRANDS DFT: Invalid parameters, using fallback")
                return self._fallback_parameters(material_id, mp_data)
                
        except Exception as e:
            logger.error(f"💥 STRANDS DFT: Error: {e}")
            return self._fallback_parameters(material_id, mp_data)
    
    def _parse_parameters(self, response: str) -> dict:
        """Parse DFT parameters from Strands response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback parsing
        return {"t_hopping": 2.0, "U_onsite": 1.0, "band_gap_dft": 1.0, "source": "fallback"}
    
    def _validate_parameters(self, params: dict) -> bool:
        """Validate physical reasonableness"""
        try:
            t = params.get("t_hopping", 0)
            U = params.get("U_onsite", 0)
            return 0 < t < 10 and 0 <= U < 5 and U <= 2 * t
        except:
            return False
    
    def validate_parameters(self, params: dict) -> bool:
        """Validate extracted parameters are physically reasonable (from original agent)"""
        try:
            t = params.get("t_hopping", 0)
            U = params.get("U_onsite", 0)
            
            # Basic physical constraints
            if t <= 0 or t > 10:  # Hopping should be positive, < 10 eV
                return False
            if U < 0 or U > 5:    # U should be positive, < 5 eV
                return False
            if U > 2 * t:         # U shouldn't be much larger than t
                return False
                
            return True
            
        except Exception:
            return False
    
    def get_tight_binding_hamiltonian(self, material_id: str, params: dict) -> str:
        """Generate tight-binding Hamiltonian code with realistic parameters (from original agent)"""
        
        t = params.get("t_hopping", 2.0)
        U = params.get("U_onsite", 1.0)
        source = params.get("source", "unknown")
        
        code = f'''# Realistic tight-binding Hamiltonian for {material_id}
# Parameters from: {source}

from qiskit_nature.second_q.operators import FermionicOp
from qiskit_nature.converters.second_quantization import QubitConverter
from qiskit_nature.mappers.second_quantization import JordanWignerMapper
from qiskit.circuit.library import TwoLocal

# DFT-derived parameters
t_hopping = {t:.2f}  # eV (nearest-neighbor hopping)
U_onsite = {U:.2f}   # eV (Hubbard interaction)

# 2-site tight-binding model
fermionic_ops = {{}}

# Kinetic energy (hopping terms)
fermionic_ops["+_0 -_2"] = -t_hopping  # up spin
fermionic_ops["+_2 -_0"] = -t_hopping
fermionic_ops["+_1 -_3"] = -t_hopping  # down spin
fermionic_ops["+_3 -_1"] = -t_hopping

# Coulomb interaction (on-site repulsion)
fermionic_ops["+_0 -_0 +_1 -_1"] = U_onsite  # site 0
fermionic_ops["+_2 -_2 +_3 -_3"] = U_onsite  # site 1

# Map to qubits
ferm_op = FermionicOp(fermionic_ops, register_length=4)
mapper = JordanWignerMapper()
converter = QubitConverter(mapper=mapper)
qubit_op = converter.convert(ferm_op)

# Variational ansatz
ansatz = TwoLocal(4, 'ry', 'cz', reps=3, entanglement='linear')

print(f"Tight-binding Hamiltonian: {{len(qubit_op)}} Pauli terms")
print(f"Parameters: t={{t_hopping}} eV, U={{U_onsite}} eV")
print(f"Source: {source}")
'''
        
        return code
    
    def _fallback_parameters(self, material_id: str, mp_data: dict) -> dict:
        """Generate fallback parameters"""
        if material_id in self.dft_database:
            return {**self.dft_database[material_id], "source": "literature"}
        
        band_gap = mp_data.get("band_gap", 1.0)
        # Use original dft_parameter_agent estimation logic
        band_gap = mp_data.get("band_gap", 1.0)
        formation_energy = mp_data.get("formation_energy", 0.0)
        
        # Empirical correlations (from original agent)
        if band_gap > 0.1:  # Semiconductor
            t_hopping = max(1.0, band_gap * 4.5)  # Rough correlation
        else:  # Metal
            t_hopping = 3.0  # Default metallic hopping
        
        # U_onsite from formation energy (very rough estimate)
        U_onsite = max(0.2, abs(formation_energy) * 0.3)
        
        return {
            "t_hopping": round(t_hopping, 2),
            "U_onsite": round(U_onsite, 2),
            "band_gap_dft": band_gap,
            "band_gap_mp": band_gap,
            "formation_energy_mp": formation_energy,
            "lattice_constant": mp_data.get("lattice_constant", 5.0),
            "source": "MP_estimated"
        }