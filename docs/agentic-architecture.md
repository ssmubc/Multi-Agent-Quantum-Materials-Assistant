# Agentic Architecture - AI Agents and MCP Servers

## What Are AI Agents?

Think of AI agents as specialized digital assistants, each with expertise in different areas. Instead of one large AI trying to handle everything, we use multiple focused agents that work together like a research team.

**Business Value**: This approach provides more accurate, specialized responses while maintaining system reliability. If one agent fails, others continue working.

## What is MCP (Model Context Protocol)?

MCP is a communication standard that allows AI agents to access external databases and tools. It's like giving the AI agents access to specialized libraries and research databases.

**Real-World Analogy**: Imagine a research team where each scientist can instantly access the world's largest materials database or quantum computing resources. That's what MCP provides for our AI agents.

## What is DFT (Density Functional Theory)?

DFT is a computational method used to calculate the electronic properties of materials. It helps predict how electrons behave in crystals, which is essential for understanding material properties like conductivity and magnetism.

**Why It Matters**: DFT parameters are needed to create accurate quantum simulations of real materials. Without them, quantum algorithms would be working with made-up numbers instead of real physics.

## What are POSCAR Files?

POSCAR files are text files that describe crystal structures - they contain information about:
- What atoms are in the material
- How the atoms are arranged in 3D space
- The size and shape of the crystal unit cell

**Think of it as**: A blueprint that tells you exactly how to build a crystal structure, atom by atom.

## How This Architecture Benefits You

This system transforms complex quantum computing and materials science into an accessible, intelligent assistant that:

- **Understands Context**: Knows the difference between asking about silicon vs. asking about quantum entanglement
- **Provides Real Data**: Uses actual materials databases instead of generating fictional properties
- **Explains Concepts**: Breaks down complex physics into understandable explanations
- **Generates Working Code**: Creates quantum circuits that actually work with real materials

## Overview

The Quantum Matter platform uses this advanced agentic architecture combining AI Strands Agents with Model Context Protocol (MCP) servers to provide intelligent quantum computing and materials science assistance.

## Core Components

### 1. Strands Agents ([AWS Blog Post on Strands Agents](https://aws.amazon.com/blogs/opensource/introducing-strands-agents-an-open-source-ai-agents-sdk/))

**What They Do**: These are specialized AI assistants that handle different aspects of quantum computing and materials science research. Each agent focuses on specific tasks to provide expert-level assistance.

**Business Impact**: Instead of generic responses, you get specialized expertise equivalent to having quantum physicists, materials scientists, and computational experts on your team.

The platform uses 5 specialized AI Strands Agents for different workflows:

#### Supervisor Agent ([`strands_supervisor.py`](../agents/strands_supervisor.py))
- **Role**: Main workflow coordinator and query router (like a research team leader)
- **What It Does for You**: 
  - Understands what type of help you need from your question
  - Connects you to the right specialist for your specific problem
  - Handles straightforward questions directly for fast responses
  - Ensures you always get an answer, even if some systems are down
- **Decision Making**:
  - Simple material lookup → Direct database search
  - Crystal structure analysis → Connects to structure specialist
  - Complex research question → Coordinates multiple experts

#### Coordinator Agent ([`strands_coordinator.py`](../agents/strands_coordinator.py))
- **Role**: Multi-agent task orchestration (like having a project coordinator)
- **What It Does for You**:
  - Manages complex research projects that need multiple specialists
  - Ensures different experts work together efficiently without conflicts
  - Combines results from multiple specialists into comprehensive reports
  - Handles parallel processing to get faster results
- **Research Applications**:
  - Comparative studies across multiple materials
  - Complex quantum simulation projects requiring multiple analysis steps
  - Large-scale batch processing of materials data

#### DFT Agent ([`strands_dft_agent.py`](../agents/strands_dft_agent.py))
- **Role**: Materials physics specialist (like having a computational physicist on your team)
- **What It Does for You**:
  - Finds the right physics parameters for your materials from research literature
  - Ensures quantum simulations use realistic, validated numbers
  - Converts complex physics data into usable quantum circuit parameters
  - Creates input files for professional materials simulation software
- **Expert Knowledge**:
  - Database of published research parameters for thousands of materials
  - Best practices for different types of materials calculations
  - Quality validation to ensure physically meaningful results

#### Structure Agent ([`strands_structure_agent.py`](../agents/strands_structure_agent.py))
- **Role**: Crystal structure specialist (like having a crystallographer on your team)
- **What It Does for You**:
  - Analyzes crystal structure files to understand material composition and arrangement
  - Identifies your material by comparing against 150,000+ known structures
  - Explains the symmetry and geometric properties of your crystal
  - Creates 3D visualizations so you can see how atoms are arranged
- **Professional Tools**:
  - Advanced crystallographic analysis software
  - Access to the world's largest materials structure database
  - Professional-grade structure visualization capabilities

#### Agentic Loop Agent ([`strands_agentic_loop.py`](../agents/strands_agentic_loop.py))
- **Role**: Research workflow coordinator (like having a research project manager)
- **What It Does for You**:
  - Handles complex research questions that require multiple steps
  - Compares multiple materials systematically
  - Refines and improves results through iterative analysis
  - Automates repetitive research tasks across many materials
- **Research Capabilities**:
  - Multi-material comparative studies
  - Complex optimization workflows
  - Automated research pipeline execution

### 2. MCP Servers (External Data Sources)

**What They Provide**: These are specialized data connectors that give the AI agents access to external databases and quantum computing resources.

**Business Value**: Instead of generating fictional data, the AI agents can access real materials databases with 150,000+ crystal structures and actual quantum computing hardware specifications.

The platform integrates two main MCP servers for external data access:

#### Enhanced Materials Project MCP Server ([`enhanced_mcp_materials/`](../enhanced_mcp_materials/))
- **What It Provides**: Direct access to the world's largest open materials database with 150,000+ crystal structures
- **Business Value**: Eliminates the need for expensive materials databases or manual literature searches - get instant access to validated experimental and computational data
- **Key Capabilities**:
  - **Instant Material Lookup**: Find any material by chemical formula (e.g., "TiO2", "LiFePO4")
  - **3D Visualization**: See exactly how atoms are arranged in your material
  - **Electronic Properties**: Get band gaps, formation energies, and stability data
  - **Structure Analysis**: Automatic crystal structure analysis and validation
  - **Advanced Features**: Supercell generation and 2D material bilayer creation
  - **Reliability**: Auto-recovery system ensures continuous access to data
- **Professional Impact**: Equivalent to having a materials science library and crystallography lab at your fingertips
- **8 Specialized Tools**: See [Materials Project MCP Integration Guide](materials-project-mcp-integration.md) for complete capabilities

#### Amazon Braket MCP Server ([`BraketMCP/`](../BraketMCP/))
- **What It Provides**: Educational quantum computing tools and real quantum hardware information
- **Business Value**: Learn quantum computing concepts with professional-grade tools without expensive quantum hardware access
- **Key Capabilities**:
  - **Interactive Learning**: Step-by-step quantum algorithm explanations with visual diagrams
  - **Circuit Visualization**: ASCII diagrams showing exactly how quantum gates work
  - **Real Hardware Info**: Access specifications of actual quantum computers (IonQ, Rigetti, etc.)
  - **Materials Integration**: VQE circuits optimized for real materials science applications
  - **Cost-Free Education**: Learn quantum computing without paying for quantum hardware execution
- **Educational Impact**: Equivalent to having a quantum computing textbook that generates working code examples
- **Complete Guide**: See [Braket Integration Guide](braket-integration.md) for setup and usage

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

**DFT Parameter Extraction**:
```
Query: "Generate tight-binding Hamiltonian for silicon mp-149 with DFT parameters"

Simple Process:
1. Supervisor routes to DFT Agent
2. DFT Agent gets material data and calculates physics parameters
3. System generates working quantum code with real values
```

**Structure Analysis**:
```
Query: "Analyze this POSCAR structure and match to Materials Project"

Simple Process:
1. Structure Agent reads your crystal structure file
2. Searches database to identify the material
3. Returns material properties and 3D visualization
```

**Multi-Material Comparison**:
```
Query: "Compare DFT parameters between silicon, germanium, and carbon"

Simple Process:
1. Agentic Loop processes each material in parallel
2. Extracts properties for Si, Ge, and C
3. Creates comparison table showing trends and differences
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

### AI Strands Integration
- **Strands Agents**: Real AI Strands Agents using Claude Sonnet 4.5 for intelligent reasoning
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