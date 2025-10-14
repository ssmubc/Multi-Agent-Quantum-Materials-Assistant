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
    }
}

def get_demo_response(model_name: str, query: str) -> str:
    """Get demo response based on model and query type"""
    model_key = model_name.lower().replace(" ", "_").replace("nova_pro", "nova_pro").replace("llama_4_scout", "llama4").replace("llama_3_70b", "llama3").replace("openai_gpt_oss", "openai")
    
    if "h2" in query.lower() or "vqe" in query.lower():
        return DEMO_RESPONSES.get(model_key, {}).get("vqe_h2", "Demo response not available")
    else:
        return DEMO_RESPONSES.get(model_key, {}).get("materials", "Demo response not available")