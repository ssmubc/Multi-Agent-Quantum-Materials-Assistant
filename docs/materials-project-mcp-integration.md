# Materials Project MCP Integration

## Overview

The Materials Project MCP (Model Context Protocol) server provides seamless integration with the Materials Project database, enabling intelligent material search, structure visualization, and advanced crystallographic analysis. This integration combines real-time Materials Project data with enhanced local processing capabilities for comprehensive materials science research.

## Key Features

- **Real-time Materials Project Data**: Direct access to 150,000+ materials with properties
- **Enhanced Structure Processing**: Advanced crystallographic analysis and visualization
- **Intelligent Caching**: Auto-recovery and fallback mechanisms for reliability
- **3D Visualization**: Interactive crystal structure plots with unit cell wireframes
- **Supercell Generation**: Automated supercell construction with customizable parameters
- **Moiré Bilayer Creation**: Advanced 2D material stacking with twist angle control
- **Multiple File Formats**: Support for POSCAR, CIF, and custom structure formats

## MCP Tools Available

### Core Material Search Tools

#### `search_materials_by_formula`
Search for materials in the Materials Project database by chemical formula.

**Parameters:**
- `chemical_formula` (string): Chemical formula (e.g., "TiO2", "LiFePO4", "graphene")

**Returns:**
- List of material descriptions with IDs, properties, and structure URIs

#### `select_material_by_id`
Select a specific material by its Materials Project ID.

**Parameters:**
- `material_id` (string): Materials Project ID (e.g., "mp-149", "mp-1143")

**Returns:**
- Detailed material description and structure URI for further processing

### Structure Data Tools

#### `get_structure_data`
Retrieve crystal structure data in specified format.

**Parameters:**
- `structure_uri` (string): Structure URI from previous operations
- `format` (string, optional): Output format - "poscar" (default) or "cif"

**Returns:**
- Complete structure file content ready for quantum simulations

#### `create_structure_from_poscar`
Create new structure from POSCAR string for custom materials.

**Parameters:**
- `poscar_str` (string): Valid POSCAR format structure data

**Returns:**
- New structure URI and enhanced description with symmetry analysis

#### `create_structure_from_cif`
Create new structure from CIF string for imported materials.

**Parameters:**
- `cif_str` (string): Valid CIF format structure data

**Returns:**
- New structure URI and crystallographic analysis

### Visualization Tools

#### `plot_structure`
Generate 3D crystal structure visualizations.

**Parameters:**
- `structure_uri` (string): Structure URI to visualize
- `duplication` (list of 3 integers, optional): Supercell expansion [a, b, c] (default: [1, 1, 1])

**Returns:**
- High-resolution PNG image with 3D structure, unit cell, and atom labels

### Advanced Structure Manipulation

#### `build_supercell`
Create supercells from bulk structures for large-scale simulations.

**Parameters:**
- `bulk_structure_uri` (string): Base structure URI
- `supercell_parameters` (dict): Scaling matrix and parameters
  ```json
  {
    "scaling_matrix": [[2,0,0],[0,2,0],[0,0,2]]
  }
  ```

**Returns:**
- New supercell structure URI, POSCAR data, and scaling information

#### `moire_homobilayer`
Generate moiré superstructures for 2D materials research.

**Parameters:**
- `bulk_structure_uri` (string): 2D material structure URI
- `interlayer_spacing` (float): Layer separation in Ångström
- `max_num_atoms` (int, optional): Atom limit for computational efficiency (default: 10)
- `twist_angle` (float, optional): Twist angle in degrees (default: 0.0)
- `vacuum_thickness` (float, optional): Z-direction vacuum in Ångström (default: 15.0)

**Returns:**
- Moiré structure with detailed physics diagnostics and POSCAR data

## Enhanced Capabilities

### Intelligent Material Properties
- **Band Gap Analysis**: Direct access to DFT-calculated electronic properties
- **Formation Energy**: Thermodynamic stability data for phase analysis
- **Symmetry Analysis**: Automatic spacegroup and crystal system identification
- **Composition Analysis**: Chemical formula normalization and element analysis

### Robust Error Handling
- **Auto-Recovery**: Automatic server restart on API failures
- **Fallback Mechanisms**: Multiple API endpoints and caching strategies
- **Graceful Degradation**: Continues operation with reduced functionality if needed
- **Consistent Structure IDs**: Standardized mp-123 format across all operations

### Advanced Physics Integration
- **DFT Parameter Extraction**: Real formation energies and band gaps for Hamiltonian modeling
- **Crystal Structure Validation**: Automatic symmetry verification and correction
- **Supercell Optimization**: Intelligent scaling for computational efficiency
- **Moiré Physics**: Advanced bilayer stacking with twist angle calculations

## Example Queries and Use Cases

### Basic Material Search
```
Search for titanium dioxide materials and show their properties
```
**Expected Flow:**
1. `search_materials_by_formula("TiO2")`
2. Returns multiple TiO2 polymorphs with band gaps and formation energies
3. User can select specific material ID for detailed analysis

### Quantum Circuit Generation
```
Get the crystal structure of silicon (mp-149) and generate VQE parameters
```
**Expected Flow:**
1. `select_material_by_id("mp-149")`
2. `get_structure_data(structure_uri, "poscar")`
3. Extract lattice parameters for Hubbard model construction
4. Generate quantum circuit with real DFT parameters

### Advanced Materials Analysis
```
Create a 2x2x1 supercell of graphene and analyze its electronic properties
```
**Expected Flow:**
1. `search_materials_by_formula("C")` → Find graphene
2. `select_material_by_id("mp-48")` → Get graphene structure
3. `build_supercell(structure_uri, {"scaling_matrix": [[2,0,0],[0,2,0],[0,0,1]]})`
4. `plot_structure(supercell_uri)` → Visualize expanded structure

### Moiré Bilayer Research
```
Generate a twisted bilayer graphene structure with 1.1° twist angle
```
**Expected Flow:**
1. `select_material_by_id("mp-48")` → Get graphene
2. `moire_homobilayer(structure_uri, interlayer_spacing=3.35, twist_angle=1.1, max_num_atoms=50)`
3. Returns moiré structure with physics diagnostics and POSCAR for DFT calculations

### Materials Comparison
```
Compare the band gaps of different TiO2 polymorphs and visualize their structures
```
**Expected Flow:**
1. `search_materials_by_formula("TiO2")` → Get all polymorphs
2. Multiple `select_material_by_id()` calls for each polymorph
3. `plot_structure()` for each to compare crystal structures
4. Band gap comparison from Materials Project data

### Custom Structure Analysis
```
Analyze a custom POSCAR structure and determine its spacegroup
```
**Expected Flow:**
1. `create_structure_from_poscar(custom_poscar_string)`
2. Returns enhanced description with automatic symmetry analysis
3. `plot_structure()` for visualization
4. Structure available for further supercell or moiré operations

## Integration with Quantum Computing

### VQE Circuit Generation
The MCP server provides real DFT parameters that can be directly used for:
- **Hubbard Model Construction**: Formation energies → on-site interaction parameters
- **Tight-Binding Parameters**: Crystal structure → hopping integrals
- **Active Space Selection**: Band gap data → relevant orbital selection
- **Ansatz Optimization**: Symmetry information → circuit depth reduction

### Materials Hamiltonian Modeling
```python
# Example integration with quantum circuits
structure_data = get_structure_data(mp_149_uri, "poscar")
band_gap = 1.17  # eV from Materials Project
formation_energy = -5.425  # eV/atom from Materials Project

# Generate Hubbard model parameters
U_onsite = abs(formation_energy) * 2  # Simplified correlation
t_hopping = band_gap / 4  # Simplified hopping

# Use in VQE ansatz construction
ansatz = create_hubbard_vqe_ansatz(
    structure=structure_data,
    U=U_onsite,
    t=t_hopping,
    num_qubits=calculate_active_space(structure_data)
)
```

## Performance and Reliability

### Caching Strategy
- **Structure Storage**: In-memory caching for current session
- **API Response Caching**: Reduces redundant Materials Project calls
- **Fallback Data**: Pre-loaded common materials for offline operation

### Error Recovery
- **Automatic Retry**: Failed API calls retry with exponential backoff
- **Server Restart**: MCP server auto-restarts on critical failures
- **Graceful Degradation**: Switches to cached data when API unavailable
- **User Notification**: Clear status indicators in application interface

### Scalability
- **Concurrent Requests**: Handles multiple simultaneous material lookups
- **Memory Management**: Automatic cleanup of old structure data
- **API Rate Limiting**: Respects Materials Project API limits
- **Efficient Serialization**: Optimized structure data transfer

## Troubleshooting

### Common Issues

**MCP Server Not Responding:**
- Check Materials Project API key configuration
- Verify network connectivity to materialsproject.org
- Restart application to reset MCP server
- Check application logs for detailed error messages

**Structure Not Found:**
- Verify Materials Project ID format (mp-123)
- Check if material exists in Materials Project database
- Try alternative search by chemical formula
- Use fallback dummy data mode for testing

**Visualization Failures:**
- Ensure matplotlib backend compatibility
- Check structure data validity
- Try simpler 2D visualization fallback
- Verify sufficient memory for large structures

**API Rate Limiting:**
- Reduce frequency of API calls
- Use cached structure data when possible
- Implement request queuing for batch operations
- Consider Materials Project API tier upgrade

### Debug Mode
Enable detailed logging for troubleshooting:
```python
import logging
logging.basicConfig(level=logging.INFO)

# Check MCP server status
from utils.enhanced_mcp_client import EnhancedMCPClient
client = EnhancedMCPClient()
status = client.check_server_health()
print(f"MCP Server Status: {status}")
```

## Future Enhancements

### Planned Features
- **Machine Learning Integration**: Property prediction for custom structures
- **High-Throughput Screening**: Automated material discovery workflows
- **Advanced Visualization**: Interactive 3D structures with WebGL
- **Collaborative Features**: Shared structure libraries and annotations
- **Extended File Formats**: Support for XYZ, PDB, and other structure formats

### Research Applications
- **Quantum Materials Discovery**: Automated screening for topological materials
- **Battery Materials**: Lithium-ion conductor analysis and optimization
- **Catalysis Research**: Surface structure generation and active site analysis
- **2D Materials**: Comprehensive moiré pattern and stacking analysis
- **Phase Diagram Construction**: Automated thermodynamic stability analysis

## Credits and License

This Materials Project MCP integration builds upon:
- **Materials Project API**: Open materials database by Lawrence Berkeley National Laboratory
- **MCP.Science Framework**: Model Context Protocol implementation by Path Integral Institute
- **Pymatgen Library**: Python materials analysis toolkit
- **Enhanced Local Server**: Custom reliability and performance improvements

**License**: MIT License - See [LICENSE](../LICENSE) for details

**Citation**: If using this MCP integration in research, please cite:

1. **MCP.Science Framework**:
   ```
   Path Integral Institute. (2025). MCP.Science (Version 0.1.0) [Computer software]. 
   https://github.com/pathintegral-institute/mcp.science
   ```

2. **Materials Project Database**:
   ```
   Jain, A., Ong, S. P., Hautier, G., Chen, W., Richards, W. D., Dacek, S., ... & Persson, K. A. (2013). 
   Commentary: The Materials Project: A materials genome approach to accelerating materials innovation. 
   APL materials, 1(1), 011002.
   ```

3. **MCP.Science Materials Project Server**: As described in [CITATION.cff](https://github.com/pathintegral-institute/mcp.science/blob/main/servers/materials-project/CITATION.cff)