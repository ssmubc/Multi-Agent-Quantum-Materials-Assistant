"""
Demo mode responses for users without AWS credentials
"""

DEMO_RESPONSES = {
    "nova_pro": {
        "vqe_h2": """This is a demo response from Nova Pro for H2 VQE:

The H2 molecule VQE implementation uses the UCCSD ansatz with Jordan-Wigner mapping. The generated code creates a PySCF driver with the H2 geometry, constructs the electronic structure problem, and applies the UCCSD ansatz.

Key points:
- H2 has 2 electrons in 2 orbitals, requiring 4 qubits after Jordan-Wigner mapping
- UCCSD ansatz provides chemically accurate results for small molecules
- The circuit depth scales with the number of excitation operators

The base code shows proper Qiskit-Nature integration with PySCF for real molecular Hamiltonians.""",
        
        "materials": """This is a demo response from Nova Pro for materials:

For materials like TiO2, we construct effective Hamiltonians using Hubbard-like models. The approach:

1. Extract band gap and formation energy from Materials Project
2. Map to Hubbard parameters (U for interaction, t for hopping)
3. Build Pauli operator representation
4. Use hardware-efficient ansatz for optimization

This provides a quantum simulation pathway for materials properties."""
    },
    
    "llama4": {
        "vqe_h2": """Demo Llama 4 Scout response for H2 VQE:

The UCCSD (Unitary Coupled Cluster Singles and Doubles) ansatz is ideal for H2 because:

- Captures electron correlation effects
- Maintains particle number conservation
- Provides systematic improvability

The Jordan-Wigner transformation maps fermionic operators to Pauli strings, enabling quantum circuit implementation. For H2, this results in a compact circuit with high fidelity.""",
        
        "materials": """Demo Llama 4 Scout response for materials:

Materials simulation requires mapping from DFT-level descriptions to quantum circuits. The effective Hamiltonian approach:

- Uses Materials Project data as input
- Constructs simplified models (Hubbard, Heisenberg)
- Enables quantum advantage for strongly correlated systems

This bridges classical materials science with quantum computing."""
    },
    
    "llama3": {
        "vqe_h2": """Demo Llama 3 70B response for H2 VQE:

The variational quantum eigensolver (VQE) for H2 demonstrates several key quantum computing concepts:

1. **Ansatz Design**: UCCSD provides a chemically motivated parameterization
2. **Mapping Strategy**: Jordan-Wigner preserves fermionic anticommutation
3. **Optimization**: Classical optimizer minimizes energy expectation value

The generated code implements these concepts using Qiskit-Nature's integrated workflow.""",
        
        "materials": """Demo Llama 3 70B response for materials:

Quantum simulation of materials requires careful model reduction:

- **Active Space**: Focus on relevant orbitals/sites
- **Effective Models**: Hubbard model captures essential physics
- **Parameter Mapping**: DFT data → model parameters

The approach enables quantum simulation of phenomena like high-Tc superconductivity."""
    },
    
    "openai": {
        "vqe_h2": """Demo OpenAI GPT response for H2 VQE:

H2 VQE implementation showcases quantum chemistry on quantum computers:

The UCCSD ansatz systematically includes electron correlation through single and double excitations. Jordan-Wigner mapping transforms the fermionic Hamiltonian into qubit operators suitable for quantum circuits.

Key advantages:
- Polynomial scaling with system size
- Chemical accuracy for ground states
- Natural integration with classical quantum chemistry""",
        
        "materials": """Demo OpenAI GPT response for materials:

Materials quantum simulation bridges condensed matter physics and quantum computing:

The effective Hamiltonian approach reduces complex materials to tractable quantum models. Using Materials Project data provides realistic parameters for Hubbard-type models.

Applications include:
- Strongly correlated electron systems
- Magnetic materials
- Superconductor modeling"""
    },
    
    "qwen_3-32b": {
        "vqe_h2": """Demo Qwen 3-32B response for H2 VQE:

## 1) Parsed Inputs
- Material: H2 molecule
- Geometry: H 0 0 0; H 0 0 0.735 (Angstrom)
- Basis: STO-3G
- Mapping: Jordan-Wigner
- Ansatz: UCCSD

## 2) Modeling Choices
- Active space: Full molecular orbitals (2 electrons, 2 orbitals)
- Qubit count: 4 qubits after Jordan-Wigner mapping
- Symmetry: Could apply Z2 tapering (reduces to 2 qubits)

## 3) Ansatz Rationale
- UCCSD captures electron correlation systematically
- Single and double excitations sufficient for H2
- Maintains particle number and spin conservation

## 4) Code Verification
- PySCF driver generates molecular Hamiltonian
- Qiskit-Nature handles fermionic-to-qubit mapping
- Circuit parameters: ~2-4 for H2 UCCSD

## 5) Sanity Checks
- Parameter count: Matches excitation operators
- Circuit depth: Reasonable for NISQ devices
- Energy convergence: Should reach chemical accuracy""",
        
        "materials": """Demo Qwen 3-32B response for materials:

## 1) Parsed Inputs
- Material: Generic solid (e.g., TiO2)
- Data source: Materials Project database
- Model: Effective Hubbard Hamiltonian
- Active space: 8-qubit toy model

## 2) Modeling Choices
- Hubbard parameters from DFT data
- U (interaction) ∝ formation energy
- t (hopping) ∝ band gap
- Nearest-neighbor approximation

## 3) Ansatz Rationale
- TwoLocal ansatz for materials simulation
- RY rotations + CZ entanglement
- Circular connectivity for periodic systems

## 4) Code Structure
- SparsePauliOp for Hamiltonian representation
- Systematic parameter construction
- Hardware-efficient ansatz design

## 5) Sanity Checks
- Hamiltonian terms: Hopping + interaction
- Parameter scaling: Linear with system size
- Physical limits: Reasonable energy scales"""
    },
    
    "deepseek_r1": {
        "vqe_h2": """Demo DeepSeek R1 response for H2 VQE:

<thinking>
The user wants a VQE implementation for H2. Let me think through this systematically:

1. H2 has 2 electrons in 2 molecular orbitals
2. Jordan-Wigner mapping gives 4 qubits
3. UCCSD ansatz is chemically motivated
4. Need PySCF for molecular Hamiltonian
</thinking>

For H2 molecule VQE with UCCSD ansatz:

**System Analysis:**
- H2: 2 electrons, 2 molecular orbitals → 4 qubits (Jordan-Wigner)
- Ground state energy: ~-1.137 Hartree (exact)
- Bond length: 0.735 Å (equilibrium)

**UCCSD Ansatz:**
- Single excitations: σ → σ* transitions
- Double excitations: σσ → σ*σ* transitions  
- Parameter count: ~2-4 for H2
- Maintains particle number conservation

**Implementation Strategy:**
- PySCF driver for molecular integrals
- Qiskit-Nature for fermionic operators
- Jordan-Wigner transformation to Pauli operators
- VQE optimization loop

The generated code provides a complete workflow from molecular geometry to quantum circuit.""",
        
        "materials": """Demo DeepSeek R1 response for materials:

<thinking>
For materials simulation, I need to consider:
1. How to map DFT data to quantum models
2. Effective Hamiltonians for materials
3. Hubbard model parameters
4. Quantum circuit representation
</thinking>

**Materials Quantum Simulation Approach:**

**Model Construction:**
- Extract band gap (Eg) and formation energy (Ef) from Materials Project
- Map to Hubbard parameters: U ∝ |Ef|, t ∝ Eg
- Build effective Hamiltonian: H = -t∑⟨i,j⟩(c†ᵢcⱼ + h.c.) + U∑ᵢnᵢ↑nᵢ↓

**Quantum Circuit Design:**
- Qubit encoding: Each site → qubit (simplified)
- Hopping terms → XX interactions
- Interaction terms → ZZ interactions
- Hardware-efficient ansatz for optimization

**Physical Insights:**
- Strong correlations when U >> t (Mott insulators)
- Metallic behavior when t >> U
- Quantum phase transitions accessible

This approach enables quantum simulation of phenomena beyond classical reach, like high-temperature superconductivity."""
    },
    
    "claude_opus_4_1": {
        "vqe_h2": """Demo Claude Opus 4.1 response for H2 VQE:

## Parsed Inputs
- **Molecule**: H₂ (hydrogen molecule)
- **Method**: Variational Quantum Eigensolver (VQE)
- **Ansatz**: UCCSD (Unitary Coupled Cluster Singles and Doubles)
- **Mapping**: Jordan-Wigner transformation
- **Objective**: Find ground state energy

## Modeling Choices
- **Basis Set**: STO-3G (minimal basis for demonstration)
- **Active Space**: Full molecular orbital space (2 electrons, 2 orbitals)
- **Qubit Mapping**: Jordan-Wigner for direct spin-to-qubit correspondence
- **Optimizer**: COBYLA for noise-resilient optimization

## Ansatz Rationale
UCCSD provides chemically accurate results by:
- Capturing electron correlation through coupled cluster theory
- Maintaining particle number conservation
- Providing systematic improvability
- Offering physical interpretability of excitation amplitudes

## Code
```python
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_nature.second_q.circuit.library import UCCSD
from qiskit.algorithms.optimizers import COBYLA
from qiskit.algorithms import VQE
from qiskit.primitives import Estimator

# Define H2 molecule
geometry = "H 0 0 0; H 0 0 0.735"
driver = PySCFDriver(atom=geometry, basis='sto3g')
problem = driver.run()

# Setup qubit mapping
mapper = JordanWignerMapper()
qubit_op = mapper.map(problem.hamiltonian.second_q_op())

# Create UCCSD ansatz
ansatz = UCCSD(
    qubit_converter=mapper,
    num_particles=problem.num_particles,
    num_spin_orbitals=problem.num_spin_orbitals
)

# Setup VQE
optimizer = COBYLA(maxiter=100)
estimator = Estimator()
vqe = VQE(estimator, ansatz, optimizer)

# Run calculation
result = vqe.compute_minimum_eigenvalue(qubit_op)
print(f"Ground state energy: {result.eigenvalue:.6f} Ha")
```

## Sanity Checks
- **Qubit Count**: 4 qubits for H₂ (2 spin orbitals × 2 spins)
- **Parameter Count**: 2 (one single, one double excitation)
- **Energy Range**: Should be around -1.137 Ha for H₂ at 0.735 Å
- **Convergence**: Monitor optimizer iterations for proper convergence
- **Physical Validity**: Energy should be lower than Hartree-Fock reference
""",
        
        "materials": """Demo Claude Opus 4.1 response for materials:

## Parsed Inputs
- **Material**: Generic solid (e.g., TiO₂)
- **Data Source**: Materials Project database
- **Model**: Effective Hubbard Hamiltonian
- **Target**: Quantum simulation of electronic properties

## Modeling Choices
- **Effective Model**: Hubbard Hamiltonian for strongly correlated electrons
- **Parameter Extraction**: Band gap and formation energy from DFT
- **Mapping Strategy**: U ∝ |formation_energy|, t ∝ band_gap
- **Qubit Encoding**: One qubit per lattice site (simplified)

## Ansatz Rationale
Hardware-efficient ansatz chosen for:
- Compatibility with NISQ devices
- Parameterized quantum circuits with physical motivation
- Systematic entanglement generation
- Variational flexibility for ground state preparation

## Code
```python
from qiskit import QuantumCircuit
from qiskit.circuit.library import TwoLocal
from qiskit.quantum_info import SparsePauliOp
from qiskit.algorithms.optimizers import COBYLA
from qiskit.algorithms import VQE

# Materials Project data (example)
band_gap = 3.2  # eV
formation_energy = -9.7  # eV/atom

# Map to Hubbard parameters
t = band_gap * 0.1  # Hopping parameter
U = abs(formation_energy) * 0.5  # Interaction parameter

# Build Hubbard Hamiltonian (4-site example)
pauli_list = []
for i in range(4):
    # Hopping terms
    j = (i + 1) % 4
    pauli_list.append((f"X{i}X{j}", -t))
    pauli_list.append((f"Y{i}Y{j}", -t))
    # Interaction terms
    pauli_list.append((f"Z{i}", U/2))

hamiltonian = SparsePauliOp.from_list(pauli_list)

# Hardware-efficient ansatz
ansatz = TwoLocal(4, 'ry', 'cz', reps=3, entanglement='circular')

# VQE optimization
optimizer = COBYLA(maxiter=200)
vqe = VQE(estimator, ansatz, optimizer)
result = vqe.compute_minimum_eigenvalue(hamiltonian)
```

## Sanity Checks
- **Parameter Scaling**: U and t values physically reasonable
- **Hamiltonian Terms**: Proper hopping and interaction structure
- **Circuit Depth**: Manageable for NISQ devices
- **Energy Scale**: Results consistent with DFT reference
- **Convergence**: Optimizer reaches stable minimum
"""
    },
    

}

def get_demo_response(model_name: str, query: str) -> str:
    """Get demo response based on model and query type"""
    # Fix model key mapping
    model_key = model_name.lower().replace(" ", "_")
    if "nova" in model_key:
        model_key = "nova_pro"
    elif "llama_4" in model_key or "llama4" in model_key:
        model_key = "llama4"
    elif "llama_3" in model_key or "llama3" in model_key:
        model_key = "llama3"
    elif "openai" in model_key:
        model_key = "openai"
    elif "qwen" in model_key:
        model_key = "qwen_3-32b"
    elif "deepseek" in model_key:
        model_key = "deepseek_r1"
    elif "claude" in model_key:
        model_key = "claude_opus_4_1"

    
    if "h2" in query.lower() or "vqe" in query.lower():
        return DEMO_RESPONSES.get(model_key, {}).get("vqe_h2", "Demo response not available")
    else:
        return DEMO_RESPONSES.get(model_key, {}).get("materials", "Demo response not available")