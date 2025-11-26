# Agentic Architecture - AI Agents and MCP Servers

## Overview

The Quantum Matter platform uses an advanced agentic architecture combining AWS Strands agents with Model Context Protocol (MCP) servers to provide intelligent quantum computing and materials science assistance.

## Architecture Diagram

[Placeholder for draw.io diagram - will show agent workflow and MCP server interactions]

## Core Components

### 1. AWS Strands Agents

The platform uses 5 specialized AWS Strands agents for different workflows:

#### Supervisor Agent ([`strands_supervisor.py`](../agents/strands_supervisor.py))
- **Role**: Main workflow coordinator and query router
- **Functionality**: 
  - Analyzes incoming queries to determine workflow type
  - Routes to appropriate specialized agents
  - Handles simple queries directly via MCP
  - Manages fallback to basic responses when needed
- **Workflow Detection**:
  - Simple Query → Direct MCP interaction
  - POSCAR Analysis → Structure matching workflow
  - Complex Query → Multi-agent coordination

#### Coordinator Agent ([`strands_coordinator.py`](../agents/strands_coordinator.py))
- **Role**: Multi-agent task orchestration
- **Functionality**:
  - Manages dependencies between agents
  - Creates task definitions for complex workflows
  - Coordinates parallel agent execution
  - Aggregates results from multiple agents
- **Use Cases**:
  - Multi-material analysis
  - Complex quantum simulation workflows
  - Batch processing tasks

#### DFT Agent ([`strands_dft_agent.py`](../agents/strands_dft_agent.py))
- **Role**: Density Functional Theory parameter extraction
- **Functionality**:
  - Extracts DFT parameters from literature and databases
  - Validates computational parameters
  - Provides empirical correlations for unknown materials
  - Generates VASP/Quantum ESPRESSO input files
- **Knowledge Base**:
  - Literature DFT parameter database
  - Exchange-correlation functional recommendations
  - K-point mesh and cutoff energy guidelines

#### Structure Agent ([`strands_structure_agent.py`](../agents/strands_structure_agent.py))
- **Role**: Crystal structure analysis and matching
- **Functionality**:
  - Analyzes POSCAR files and crystal structures
  - Matches structures to Materials Project database
  - Provides symmetry analysis and space group identification
  - Generates structure visualizations
- **Integration**:
  - Pymatgen for structure manipulation
  - Materials Project API for database matching
  - Crystallographic analysis tools

#### Agentic Loop Agent ([`strands_agentic_loop.py`](../agents/strands_agentic_loop.py))
- **Role**: Iterative problem solving for complex queries
- **Functionality**:
  - Breaks down complex problems into subtasks
  - Iteratively refines solutions based on feedback
  - Handles multi-step quantum simulation workflows
  - Provides batch processing for multiple materials
- **Use Cases**:
  - Complex multi-material queries
  - Iterative optimization problems
  - Research workflow automation

### 2. MCP Servers

The platform integrates two main MCP servers for external data access:

#### Enhanced Materials Project MCP Server ([`enhanced_mcp_materials/`](../enhanced_mcp_materials/))
- **Purpose**: Robust access to Materials Project database with 8 specialized tools
- **Functionality**:
  - Material search by chemical formula
  - Crystal structure retrieval and visualization
  - 3D structure plotting with unit cell wireframes
  - Supercell generation with customizable scaling
  - Moiré bilayer creation for 2D materials
  - POSCAR/CIF structure creation and analysis
  - Electronic properties lookup (band gaps, formation energies)
  - Auto-recovery and fallback mechanisms
- **8 MCP Tools**: See [Materials Project MCP Integration Guide](materials-project-mcp-integration.md) for complete tool documentation

#### Amazon Braket MCP Server ([`BraketMCP/`](../BraketMCP/))
- **Purpose**: Educational quantum circuit analysis and visualization
- **Functionality**:
  - Quantum circuit creation (Bell, GHZ, VQE demonstrations)
  - Circuit analysis and ASCII visualization
  - Educational quantum algorithm examples
  - Device information and capabilities
- **Integration**: See [Braket Integration Guide](braket-integration.md) for complete setup and usage documentation

## Agent Workflow Patterns

### 1. Simple Query Workflow
```
User Query → Supervisor Agent → Enhanced MCP Tools → Direct Response with Visualization
```
- Used for straightforward material lookups
- Direct MCP interaction with 8 specialized tools
- Automatic 3D visualization when requested
- Fast response time with rich material data

### 2. POSCAR Analysis Workflow
```
User Query + POSCAR → Supervisor Agent → Coordinator Agent → Structure Matching → DFT Analysis → Response
```
- Triggered by POSCAR file uploads or structure queries
- Complete workflow coordination through Coordinator Agent
- Materials Project structure matching
- DFT parameter extraction and analysis

### 3. Complex Multi-Material Workflow
```
User Query → Supervisor Agent → Agentic Loop Agent → Iterative Material Analysis → Aggregated Response
```
- Used for multi-material comparisons
- Iterative processing of multiple materials
- Comprehensive comparative analysis
- Batch processing capabilities

### 4. Specialized MCP Tool Workflows
```
User Query → Supervisor Agent → Direct MCP Tool Execution → Enhanced Response
```
- **Moiré Bilayer**: Automatic 2D material detection and twist angle extraction
- **Supercell Generation**: Intelligent scaling matrix application
- **3D Visualization**: Real-time crystal structure plotting
- **DFT Parameter Extraction**: Literature-based parameter lookup

## Framework Integration

### Qiskit Framework Path
```
User Query → Strands Agents → Materials Project MCP → Qiskit Code Generation
```
- Uses Materials Project data for real material properties
- Generates Qiskit quantum circuits
- Provides 3D crystal structure visualizations

### Braket Framework Path
```
User Query → Braket MCP → Amazon Braket Code Generation
```
- Direct integration with Braket MCP server
- Generates Amazon Braket quantum circuits
- Provides local simulator execution

## Agent Communication

### Inter-Agent Communication
- **Message Passing**: Agents communicate via structured messages
- **Task Coordination**: Coordinator manages agent dependencies
- **Result Aggregation**: Multiple agent outputs combined intelligently
- **Error Handling**: Graceful fallback when agents fail

### Enhanced MCP Integration
- **8 Specialized Tools**: Direct access to Materials Project MCP tools (see [Materials Project MCP Integration](materials-project-mcp-integration.md))
- **Auto-Recovery**: MCP server automatically restarts on failures
- **Smart Caching**: In-memory structure storage for session persistence
- **Fallback Mechanisms**: Multiple API endpoints and dummy data modes
- **Real-time Health Monitoring**: MCP server status indicators in UI

## Specialized Agent Capabilities

### DFT Agent Features
**Purpose**: Extract and validate DFT parameters for quantum Hamiltonian construction

**Technical Process**:
1. **Literature Parameter Lookup**: Searches curated database of published DFT parameters
2. **Materials Project Integration**: Extracts band gaps and formation energies from MP data
3. **Parameter Validation**: Applies physics-based rules to ensure reasonable values
4. **Tight-Binding Generation**: Converts DFT data to Hubbard model parameters
5. **Code Generation**: Creates executable Qiskit VQE circuits with real parameters

**Example Query**: `"Generate tight-binding Hamiltonian for silicon mp-149 with DFT parameters"`
**Workflow**: Supervisor → DFT Agent → MP lookup (mp-149) → Parameter extraction → Hamiltonian code

### Structure Agent Features  
**Purpose**: Analyze crystal structures and match to Materials Project database

**Technical Process**:
1. **POSCAR Parsing**: Extracts lattice vectors, atomic positions, and composition
2. **Symmetry Analysis**: Identifies space groups using pymatgen SpacegroupAnalyzer
3. **Structure Matching**: Compares against 150,000+ MP structures using similarity metrics
4. **Crystallographic Validation**: Verifies structure consistency and physical validity
5. **3D Visualization**: Generates interactive structure plots with unit cells

**Example Query**: `"Analyze this POSCAR structure and match to Materials Project"`
**Workflow**: Supervisor → Structure Agent → POSCAR analysis → MP matching → Symmetry report

### Agentic Loop Features
**Purpose**: Handle complex multi-material queries through iterative problem solving

**Technical Process**:
1. **Query Decomposition**: Breaks complex requests into individual material lookups
2. **Batch Processing**: Uses Strands `batch` tool for parallel material searches
3. **Iterative Refinement**: Improves results through multiple analysis cycles with `retrieve` tool
4. **AWS Integration**: Leverages `use_aws` tool for MCP server coordination
5. **Progress Monitoring**: Tracks completion status and handles failures gracefully

**Strands Tools Used**:
- `batch` - Processes multiple materials simultaneously (e.g., [Si, Ge, C] in parallel)
- `retrieve` - Augments analysis with additional knowledge retrieval
- `use_aws` - Coordinates with Materials Project MCP server

**Example Query**: `"Compare DFT parameters between silicon, germanium, and carbon"`
**Workflow**: Supervisor → Agentic Loop → `batch([Si, Ge, C])` → Parameter comparison → Comparative analysis

### Multi-Agent Coordination Examples

**Complex Query Processing**:
```
Query: "Generate tight-binding Hamiltonian for silicon mp-149 with DFT parameters"

Workflow:
1. Supervisor Agent: Detects DFT parameter extraction need
2. DFT Agent: 
   - Calls select_material_by_id("mp-149")
   - Extracts band gap (1.17 eV) and formation energy (-5.425 eV/atom)
   - Applies literature correlations: U = 2 * |formation_energy|, t = band_gap/4
   - Generates Hubbard model: U = 10.85 eV, t = 0.29 eV
3. Code Generation: Creates Qiskit VQE ansatz with extracted parameters
4. Response: Complete Hamiltonian code with real DFT values
```

**POSCAR Analysis Workflow**:
```
Query: "Analyze this POSCAR structure and match to Materials Project"

Workflow:
1. Supervisor Agent: Detects POSCAR analysis need
2. Coordinator Agent: Orchestrates complete workflow
3. Structure Agent:
   - Parses POSCAR: extracts Si2 with diamond structure
   - Calculates lattice parameters: a=5.43 Å
   - Identifies space group: Fd-3m (#227)
4. Materials Project Matching:
   - Searches MP database for similar Si structures
   - Finds match: mp-149 (silicon, diamond structure)
   - Validates structural similarity
5. DFT Agent: Extracts electronic properties for matched material
6. Response: Complete structure analysis with MP match and properties
```

**Multi-Material Comparison**:
```
Query: "Compare DFT parameters between silicon, germanium, and carbon"

Workflow:
1. Supervisor Agent: Detects multi-material comparison
2. Agentic Loop Agent: Manages iterative processing
3. Iteration 1: Process Silicon
   - search_materials_by_formula("Si") → mp-149
   - Extract: Band gap 1.17 eV, Formation energy -5.425 eV/atom
4. Iteration 2: Process Germanium  
   - search_materials_by_formula("Ge") → mp-32
   - Extract: Band gap 0.744 eV, Formation energy -3.85 eV/atom
5. Iteration 3: Process Carbon
   - search_materials_by_formula("C") → mp-66 (diamond)
   - Extract: Band gap 5.48 eV, Formation energy 0.0 eV/atom
6. Comparative Analysis:
   - Band gap trend: C > Si > Ge (expected for group IV)
   - Stability: Si most stable, C least stable in diamond form
   - Tight-binding parameters calculated for each
7. Response: Comprehensive comparison table with DFT parameters
```

## Performance Optimization

### Agent Caching
- **Response Caching**: Frequently used agent responses cached
- **MCP Client Reuse**: Avoid recreating MCP connections
- **Lazy Loading**: Agents loaded only when needed
- **Memory Management**: Efficient cleanup of agent resources

### Parallel Processing
- **Concurrent Agents**: Multiple agents can run simultaneously
- **Task Queuing**: Efficient task distribution
- **Resource Management**: Prevents agent resource conflicts
- **Load Balancing**: Distributes work across available agents

## Error Handling and Fallbacks

### Agent Failure Handling
- **Graceful Degradation**: System continues with reduced functionality
- **Fallback Chains**: Multiple fallback options for each agent
- **Error Reporting**: Clear error messages for debugging
- **Recovery Mechanisms**: Automatic retry and recovery

### MCP Server Fallbacks
- **Server Unavailable**: Falls back to basic API calls
- **Timeout Handling**: Graceful timeout with alternative responses
- **Data Unavailable**: Provides dummy data or alternative sources
- **Connection Issues**: Automatic retry with exponential backoff

## Development and Testing

### AWS Strands Integration
- **Production Agents**: Real AWS Strands agents using Claude Sonnet 4.5 for intelligent reasoning
- **Strands Tools Integration**: Multiple tools from `strands-agents-tools`:
  - `use_aws` - AWS service integration for MCP calls and resource access
  - `retrieve` - Information retrieval for knowledge augmentation
  - `batch` - Batch processing for multi-material analysis (used by Agentic Loop)
- **Automatic Fallback**: Mock agents used locally when Strands packages unavailable
- **Agent Framework**: Built on `strands-agents` SDK with `strands-agents-tools` for AWS integration
- **Testing Framework**: Comprehensive agent testing capabilities
- **Debug Logging**: Detailed logging for agent interactions and Claude responses

### MCP Server Testing
- **Local Testing**: Full MCP server testing in local environment
- **Integration Tests**: End-to-end workflow testing
- **Performance Tests**: Load testing for MCP servers
- **Fallback Testing**: Verify fallback mechanisms work correctly

## Future Enhancements

### Planned Agent Features
- **Learning Capabilities**: Agents learn from user interactions
- **Custom Workflows**: User-defined agent workflows
- **External Integrations**: Additional MCP servers for new data sources
- **Advanced Reasoning**: Enhanced problem-solving capabilities

### Scalability Improvements
- **Agent Clustering**: Distribute agents across multiple instances
- **Load Balancing**: Intelligent agent load distribution
- **Caching Layers**: Multi-level caching for improved performance
- **Monitoring**: Advanced agent performance monitoring

## Security Considerations

### Agent Security
- **Sandboxing**: Agents run in isolated environments
- **Permission Management**: Least privilege access for agents
- **Input Validation**: Sanitize all agent inputs
- **Output Filtering**: Validate agent outputs before display

### MCP Security
- **Authentication**: Secure MCP server authentication
- **Encryption**: All MCP communications encrypted
- **Access Control**: Role-based access to MCP servers
- **Audit Logging**: Complete audit trail of MCP interactions

This agentic architecture provides a sophisticated, scalable platform for quantum computing and materials science research, combining the power of specialized AI agents with comprehensive external data access through MCP servers.