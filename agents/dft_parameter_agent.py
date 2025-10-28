# DFT Parameter Extraction Agent
from typing import Dict, Any, Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)

class DFTParameterAgent:
    """Agent for extracting realistic DFT-derived parameters"""
    
    def __init__(self, mp_agent):
        self.mp_agent = mp_agent
        
        # Literature DFT parameters for common materials
        self.dft_parameters = {
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
    
    def extract_dft_parameters(self, material_id: str, mp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract realistic DFT parameters for material"""
        
        logger.info(f"🔬 DFT AGENT: Extracting parameters for {material_id}")
        
        # Check if we have literature DFT parameters
        if material_id in self.dft_parameters:
            params = self.dft_parameters[material_id].copy()
            logger.info(f"✅ DFT AGENT: Found literature parameters for {material_id}")
            return params
        
        # Estimate parameters from Materials Project data
        estimated_params = self._estimate_from_mp_data(mp_data)
        logger.info(f"📊 DFT AGENT: Estimated parameters from MP data")
        return estimated_params
    
    def _estimate_from_mp_data(self, mp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate DFT parameters from Materials Project properties"""
        
        try:
            band_gap = mp_data.get("band_gap", 0.0)
            formation_energy = mp_data.get("formation_energy", 0.0)
            
            # Empirical correlations (simplified)
            # t_hopping scales with band gap for semiconductors
            if band_gap > 0.1:  # Semiconductor
                t_hopping = max(1.0, band_gap * 4.5)  # Rough correlation
            else:  # Metal
                t_hopping = 3.0  # Default metallic hopping
            
            # U_onsite from formation energy (very rough estimate)
            U_onsite = max(0.2, abs(formation_energy) * 0.3)
            
            return {
                "t_hopping": round(t_hopping, 2),
                "U_onsite": round(U_onsite, 2),
                "band_gap_mp": band_gap,
                "formation_energy_mp": formation_energy,
                "source": "MP_estimated"
            }
            
        except Exception as e:
            logger.warning(f"⚠️ DFT AGENT: Parameter estimation failed: {e}")
            return {
                "t_hopping": 2.0,  # Default values
                "U_onsite": 1.0,
                "source": "default_fallback"
            }
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate extracted parameters are physically reasonable"""
        
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
    
    def get_tight_binding_hamiltonian(self, material_id: str, params: Dict[str, Any]) -> str:
        """Generate tight-binding Hamiltonian code with realistic parameters"""
        
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