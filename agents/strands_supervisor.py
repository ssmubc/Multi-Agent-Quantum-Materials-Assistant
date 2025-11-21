import logging
import json
import re
from typing import Dict, Any

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
STRANDS_AVAILABLE = False

try:
    from strands_agents import Agent as RealAgent
    from strands_agents_tools import use_aws as real_use_aws
    Agent = RealAgent
    use_aws = real_use_aws
    STRANDS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Strands not available locally: {e}")
    STRANDS_AVAILABLE = False
from .strands_coordinator import StrandsCoordinator
from .strands_dft_agent import StrandsDFTAgent
from .strands_structure_agent import StrandsStructureAgent
from .strands_agentic_loop import StrandsAgenticLoop
from utils.braket_integration import braket_integration
from utils.mcp_tools_wrapper import initialize_mcp_wrapper, get_mcp_wrapper

class StrandsSupervisorAgent:
    """AWS Strands-based supervisor for quantum materials analysis"""
    
    def __init__(self, mp_agent):
        self.mp_agent = mp_agent
        
        # Initialize MCP wrapper for easier tool access
        initialize_mcp_wrapper(mp_agent)
        
        # Test Strands framework availability
        logger.info("🚀 STRANDS: Initializing Strands supervisor with Claude Sonnet 4.5...")
        
        try:
            # Create Strands agent with AWS tools and MCP integration
            self.agent = Agent(
                model="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
                tools=[use_aws],
                system_prompt="You are a quantum materials analysis agent with access to Materials Project MCP tools through AWS. Always use the available tools to call MCP services when analyzing materials."
            )
            logger.info("✅ STRANDS: Agent created successfully")
            
            # Test Claude model availability
            test_response = self.agent("Test: Return 'OK' if Claude Sonnet 4.5 is working")
            response_text = getattr(test_response, 'text', str(test_response))
            logger.info(f"✅ STRANDS: Claude test successful: {response_text[:50]}...")
            
        except Exception as e:
            logger.error(f"💥 STRANDS: Initialization failed: {e}")
            logger.error(f"💥 STRANDS: Error type: {type(e).__name__}")
            import traceback
            logger.error(f"💥 STRANDS: Full traceback: {traceback.format_exc()}")
            raise
        
        # Initialize specialized agents and coordinator
        try:
            logger.info("🔧 STRANDS: Initializing specialized agents...")
            self.coordinator = StrandsCoordinator(mp_agent)
            self.dft_agent = StrandsDFTAgent()
            self.structure_agent = StrandsStructureAgent(mp_agent)
            self.agentic_loop = StrandsAgenticLoop(mp_agent)
            logger.info("✅ STRANDS: All specialized agents initialized")
        except Exception as e:
            logger.error(f"💥 STRANDS: Specialized agent initialization failed: {e}")
            raise
    
    def process_query(self, query: str, formula: str = "") -> dict:
        """Process query using Strands agent with MCP integration"""
        # Check for Braket-specific queries first (but NOT Materials Project VQE)
        if self._is_braket_query(query):
            logger.info("⚛️ STRANDS: Pure Braket query detected, routing to Braket MCP")
            return self._handle_braket_query(query)
        
        # Extract formula from query if not provided
        if not formula:
            formula = self._extract_formula_from_query(query)
        
        # Check if this is a molecular query that should skip MP search
        if formula is None:
            logger.info("🧪 STRANDS: Molecular query detected - providing response without Materials Project data")
            return {
                "status": "success",
                "mp_data": None,
                "mcp_actions": [],
                "workflow_used": "Simple Query",
                "reasoning": "Simple molecule query - no Materials Project search needed"
            }
        
        logger.info(f"🤖 STRANDS: Processing query for formula='{formula}'")
        
        # Validate formula before proceeding
        if not formula or formula.strip() == "":
            logger.warning("⚠️ STRANDS: No formula detected, using fallback")
            formula = "Si"  # Safe fallback
        
        # First try direct MCP call, then let Strands agent enhance if needed
        mcp_wrapper = get_mcp_wrapper()
        if mcp_wrapper:
            logger.info(f"🔧 STRANDS: Using direct MCP wrapper for {formula}")
            
            # Determine action based on query
            query_lower = query.lower()
            if "moire" in query_lower or "bilayer" in query_lower:
                # For moire queries, search first then create moire
                search_result = mcp_wrapper.search_material(formula)
                if search_result["status"] == "success":
                    # Extract material ID and create moire
                    import re
                    results_text = str(search_result["data"])
                    material_id_match = re.search(r'Material ID: (mp-\d+)', results_text)
                    if material_id_match:
                        material_id = material_id_match.group(1)
                        moire_result = mcp_wrapper.create_moire_bilayer(material_id)
                        return {
                            "status": "success",
                            "mp_data": search_result["data"],
                            "mcp_actions": ["search_materials_by_formula", "moire_homobilayer"],
                            "mcp_results": {"search": search_result, "moire": moire_result}
                        }
            elif "supercell" in query_lower:
                # For supercell queries
                search_result = mcp_wrapper.search_material(formula)
                if search_result["status"] == "success":
                    import re
                    results_text = str(search_result["data"])
                    material_id_match = re.search(r'Material ID: (mp-\d+)', results_text)
                    if material_id_match:
                        material_id = material_id_match.group(1)
                        supercell_result = mcp_wrapper.create_supercell(material_id)
                        return {
                            "status": "success",
                            "mp_data": search_result["data"],
                            "mcp_actions": ["search_materials_by_formula", "build_supercell"],
                            "mcp_results": {"search": search_result, "supercell": supercell_result}
                        }
            elif "plot" in query_lower or "visualiz" in query_lower:
                # For visualization queries
                search_result = mcp_wrapper.search_material(formula)
                if search_result["status"] == "success":
                    import re
                    results_text = str(search_result["data"])
                    material_id_match = re.search(r'Material ID: (mp-\d+)', results_text)
                    if material_id_match:
                        material_id = material_id_match.group(1)
                        viz_result = mcp_wrapper.create_visualization(material_id)
                        return {
                            "status": "success",
                            "mp_data": search_result["data"],
                            "mcp_actions": ["search_materials_by_formula", "plot_structure"],
                            "mcp_results": {"search": search_result, "visualization": viz_result}
                        }
            else:
                # Default: just search
                search_result = mcp_wrapper.search_material(formula)
                if search_result["status"] == "success":
                    return {
                        "status": "success",
                        "mp_data": search_result["data"],
                        "mcp_actions": ["search_materials_by_formula"],
                        "mcp_results": {"search": search_result}
                    }
        
        # Fallback: Create context-aware prompt for Strands agent
        prompt = f"""
        You are a quantum materials analysis agent. Analyze this query: "{query}"
        Material formula: {formula}
        
        Provide analysis and recommendations for this material and query.
        """
        
        try:
            # Let Strands agent call MCP tools directly through AWS tools
            response = self.agent(prompt)
            
            # Get response text
            response_text = getattr(response, 'text', str(response))
            logger.info(f"🤖 STRANDS: Agent response: {response_text[:200]}...")
            
            # Check if agent actually called tools
            if hasattr(response, 'tool_calls') and response.tool_calls:
                logger.info(f"✅ STRANDS: Agent made {len(response.tool_calls)} tool calls")
                # Return the tool call results
                return {
                    "status": "success",
                    "mp_data": response_text,
                    "mcp_actions": ["strands_analysis"],
                    "tool_results": response_text,
                    "workflow_used": "Strands Agent with Tools"
                }
            else:
                logger.info("📝 STRANDS: Agent provided analysis without tool calls")
                # Return the analysis
                return {
                    "status": "success",
                    "mp_data": {"analysis": response_text, "formula": formula},
                    "mcp_actions": ["strands_analysis"],
                    "workflow_used": "Strands Agent Analysis"
                }
            
        except Exception as e:
            logger.error(f"💥 STRANDS: Error: {e}")
            return {"status": "error", "message": str(e)}
    
    def _parse_agent_response(self, response: str) -> dict:
        """Extract action from Strands agent response"""
        try:
            # Try to find JSON in response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # Fallback: simple keyword detection
            response_lower = response.lower()
            if "moire" in response_lower or "bilayer" in response_lower:
                return {"action": "moire_homobilayer", "params": {}}
            elif "supercell" in response_lower:
                return {"action": "build_supercell", "params": {}}
            elif "plot" in response_lower or "visualiz" in response_lower:
                return {"action": "plot_structure", "params": {}}
            elif "search" in response_lower:
                return {"action": "search_materials_by_formula", "params": {}}
            else:
                return {"action": "search", "params": {}}
                
        except Exception as e:
            logger.warning(f"⚠️ STRANDS: Parse error, using fallback: {e}")
            return {"action": "search", "params": {}}
    
    def _execute_mcp_action(self, action_data: dict, formula: str, query: str) -> dict:
        """Execute the determined MCP action"""
        action = action_data.get("action", "search")
        
        try:
            if action == "moire_homobilayer":
                return self._handle_moire(formula, query)
            elif action == "build_supercell":
                return self._handle_supercell(formula, query)
            elif action == "create_structure_from_poscar":
                return self._handle_poscar_creation(query)
            elif action == "plot_structure":
                return self._handle_visualization(formula)
            elif action == "search_materials_by_formula":
                return self._handle_formula_search(formula)
            else:
                return self._handle_standard_lookup(formula)
                
        except Exception as e:
            logger.error(f"💥 STRANDS: MCP execution error: {e}")
            return {"status": "error", "message": str(e)}
    
    def _handle_moire(self, formula: str, query: str) -> dict:
        """Handle moire bilayer requests with enhanced MCP tools"""
        # Override formula for 2D material moire queries
        query_lower = query.lower()
        moire_materials = {
            "graphene": "C",
            "bn": "BN", "boron nitride": "BN", "h-bn": "BN",
            "mos2": "MoS2", "molybdenum disulfide": "MoS2",
            "ws2": "WS2", "tungsten disulfide": "WS2",
            "mose2": "MoSe2", "molybdenum diselenide": "MoSe2",
            "wse2": "WSe2", "tungsten diselenide": "WSe2",
            "phosphorene": "P", "black phosphorus": "P",
            "silicene": "Si", "germanene": "Ge",
            "stanene": "Sn", "plumbene": "Pb"
        }
        
        # Force graphite for graphene queries
        if "graphene" in query_lower:
            logger.info(f"🌀 STRANDS: Forcing graphite (mp-48) for graphene moire request")
            try:
                detailed_data = self.mp_agent.select_material_by_id("mp-48")
                if detailed_data and "error" not in str(detailed_data):
                    structure_uri = "structure://mp_mp-48"
                    logger.info(f"✅ STRANDS: Using graphite mp-48 for moire generation")
                else:
                    logger.warning(f"⚠️ STRANDS: mp-48 not available, falling back to search")
                    detailed_data = None
            except Exception as e:
                logger.error(f"❌ STRANDS: Failed to get mp-48: {e}")
                detailed_data = None
            
            if detailed_data:
                # Skip search, use mp-48 directly
                twist_angle = 1.1  # magic angle default
                interlayer_spacing = 3.4  # default for graphene
                
                angle_match = re.search(r'(\d+\.?\d*)\s*degree', query_lower)
                if angle_match:
                    twist_angle = float(angle_match.group(1))
                
                moire_result = self.mp_agent.moire_homobilayer(structure_uri, interlayer_spacing, 10, twist_angle, 15.0)
                
                return {
                    "status": "success",
                    "mp_data": detailed_data,
                    "mcp_actions": ["select_material_by_id", "moire_homobilayer"],
                    "moire_params": {"twist_angle": twist_angle, "interlayer_spacing": interlayer_spacing},
                    "mcp_results": {"moire_homobilayer": moire_result}
                }
        
        original_formula = formula
        for material_name, material_formula in moire_materials.items():
            if material_name in query_lower:
                formula = material_formula
                logger.info(f"🌀 STRANDS: Overriding formula '{original_formula}' → '{formula}' for {material_name} moire request")
                break
        
        # If no specific material found but it's a moire request with H2/H, default to graphene
        if formula == original_formula and original_formula in ["H2", "H"]:
            formula = "C"
            logger.info(f"🌀 STRANDS: Generic moire request detected, defaulting to graphene (C)")
        
        # Continue with search for non-graphene materials
        logger.info(f"🌀 STRANDS: Using enhanced search for moire material {formula}")
        search_results = self.mp_agent.search_materials_by_formula(formula)
        
        if not search_results:
            return {"status": "error", "message": "Material not found"}
        
        # Extract material ID from search results
        results_text = str(search_results)
        material_id_match = re.search(r'Material ID: (mp-\d+)', results_text)
        if not material_id_match:
            return {"status": "error", "message": "No material ID found"}
        
        material_id = material_id_match.group(1)
        detailed_data = self.mp_agent.select_material_by_id(material_id)
        structure_uri = f"structure://mp_{material_id}"
        
        # Extract moire parameters from query
        twist_angle = 1.1  # magic angle default
        interlayer_spacing = 3.4  # default for graphene-like
        
        angle_match = re.search(r'(\d+\.?\d*)\s*degree', query_lower)
        if angle_match:
            twist_angle = float(angle_match.group(1))
            logger.info(f"🌀 STRANDS: Extracted twist angle: {twist_angle}°")
        
        spacing_match = re.search(r'(\d+\.?\d*)\s*[åa]', query_lower)
        if spacing_match:
            interlayer_spacing = float(spacing_match.group(1))
            logger.info(f"🌀 STRANDS: Extracted interlayer spacing: {interlayer_spacing} Å")
        
        # Call enhanced moire generation
        moire_result = self.mp_agent.moire_homobilayer(structure_uri, interlayer_spacing, 10, twist_angle, 15.0)
        logger.info(f"🌀 STRANDS: Called enhanced moire_homobilayer with {twist_angle}° twist")
        
        return {
            "status": "success",
            "mp_data": detailed_data,
            "mcp_actions": ["search_materials_by_formula", "select_material_by_id", "get_structure_data", "moire_homobilayer"],
            "moire_params": {"twist_angle": twist_angle, "interlayer_spacing": interlayer_spacing},
            "mcp_results": {"moire_homobilayer": moire_result}
        }
    
    def _handle_poscar_creation(self, query: str) -> dict:
        """Handle POSCAR structure creation requests"""
        # Extract POSCAR data from query if provided
        poscar_data = None
        if "POSCAR" in query or "poscar" in query:
            # Try to extract POSCAR from query text
            lines = query.split('\n')
            poscar_lines = []
            in_poscar = False
            for line in lines:
                if "POSCAR" in line or "poscar" in line or in_poscar:
                    in_poscar = True
                    if line.strip() and not "POSCAR" in line:
                        poscar_lines.append(line)
            if poscar_lines:
                poscar_data = '\n'.join(poscar_lines)
        
        if not poscar_data:
            # Use a simple example POSCAR for demonstration
            poscar_data = """Si
1.0
5.43 0 0
0 5.43 0
0 0 5.43
Si
2
Direct
0.0 0.0 0.0
0.25 0.25 0.25"""
        
        logger.info(f"📋 STRANDS: Creating structure from POSCAR data")
        poscar_result = self.mp_agent.create_structure_from_poscar(poscar_data)
        
        return {
            "status": "success",
            "mp_data": {"source": "POSCAR creation", "formula": "Custom structure"},
            "mcp_actions": ["create_structure_from_poscar"],
            "mcp_results": {"create_structure_from_poscar": poscar_result}
        }
    
    def _handle_supercell(self, formula: str, query: str) -> dict:
        """Handle supercell requests using enhanced MCP tools"""
        logger.info(f"🏗️ STRANDS: Using enhanced search for supercell material {formula}")
        search_results = self.mp_agent.search_materials_by_formula(formula)
        
        if not search_results:
            return {"status": "error", "message": "Material not found"}
        
        # Extract material ID and get detailed data
        results_text = str(search_results)
        material_id_match = re.search(r'Material ID: (mp-\d+)', results_text)
        if not material_id_match:
            return {"status": "error", "message": "No material ID found"}
        
        material_id = material_id_match.group(1)
        detailed_data = self.mp_agent.select_material_by_id(material_id)
        structure_uri = f"structure://mp_{material_id}"
        
        # Call enhanced supercell building
        supercell_result = self.mp_agent.build_supercell(structure_uri, {"scaling_matrix": [[2,0,0],[0,2,0],[0,0,2]]})
        logger.info(f"🏗️ STRANDS: Called enhanced build_supercell for {material_id}")
        
        return {
            "status": "success", 
            "mp_data": detailed_data, 
            "mcp_actions": ["search_materials_by_formula", "select_material_by_id", "get_structure_data", "build_supercell"],
            "mcp_results": {"build_supercell": supercell_result}
        }
    
    def _handle_visualization(self, formula: str) -> dict:
        """Handle visualization requests using enhanced MCP tools"""
        logger.info(f"📊 STRANDS: Using enhanced search for visualization of {formula}")
        search_results = self.mp_agent.search_materials_by_formula(formula)
        
        if not search_results:
            return {"status": "error", "message": "Material not found"}
        
        # Extract material ID and get detailed data
        results_text = str(search_results)
        material_id_match = re.search(r'Material ID: (mp-\d+)', results_text)
        if not material_id_match:
            return {"status": "error", "message": "No material ID found"}
        
        material_id = material_id_match.group(1)
        detailed_data = self.mp_agent.select_material_by_id(material_id)
        structure_uri = f"structure://mp_{material_id}"
        
        # Call enhanced plotting
        plot_result = self.mp_agent.plot_structure(structure_uri, [1, 1, 1])
        logger.info(f"📊 STRANDS: Called enhanced plot_structure for {material_id}")
        
        return {
            "status": "success", 
            "mp_data": detailed_data, 
            "mcp_actions": ["search_materials_by_formula", "select_material_by_id", "get_structure_data", "plot_structure"],
            "mcp_results": {"plot_structure": plot_result}
        }
    
    def _handle_formula_search(self, formula: str) -> dict:
        """Handle formula search requests using enhanced MCP tools"""
        logger.info(f"🔍 STRANDS: Enhanced formula search for {formula}")
        search_results = self.mp_agent.search_materials_by_formula(formula)
        
        # Get detailed data for first result if available
        if search_results:
            results_text = str(search_results)
            material_id_match = re.search(r'Material ID: (mp-\d+)', results_text)
            if material_id_match:
                material_id = material_id_match.group(1)
                detailed_data = self.mp_agent.select_material_by_id(material_id)
                return {
                    "status": "success", 
                    "mp_data": detailed_data, 
                    "mcp_actions": ["search_materials_by_formula", "select_material_by_id", "get_structure_data"],
                    "mcp_results": {"select_material_by_id": detailed_data}
                }
        
        return {"status": "success", "mp_data": search_results, "mcp_actions": ["search_materials_by_formula"]}
    
    def _handle_standard_lookup(self, formula: str) -> dict:
        """Handle standard material lookup using enhanced MCP tools"""
        # Check if formula is actually a material ID
        if formula.startswith("mp-"):
            logger.info(f"🔍 STRANDS: Using enhanced material ID lookup for {formula}")
            try:
                detailed_data = self.mp_agent.select_material_by_id(formula)
                if detailed_data and "error" not in detailed_data:
                    return {
                        "status": "success", 
                        "mp_data": detailed_data, 
                        "mcp_actions": ["select_material_by_id", "get_structure_data"],
                        "mcp_results": {"select_material_by_id": detailed_data}
                    }
                else:
                    return {"status": "error", "message": f"Material {formula} not found"}
            except Exception as e:
                logger.error(f"💥 STRANDS: Material ID lookup failed: {e}")
                return {"status": "error", "message": f"Material lookup failed: {str(e)}"}
        
        # Try search_materials_by_formula first, but handle failures gracefully
        try:
            logger.info(f"🔍 STRANDS: Using enhanced search_materials_by_formula for {formula}")
            search_results = self.mp_agent.search_materials_by_formula(formula)
            
            # Check if search_results is valid (could be dict or list)
            if search_results and "error" not in str(search_results).lower():
                # Extract material ID from search results to get enhanced data
                results_text = str(search_results)
                material_id_match = re.search(r'Material ID: (mp-\d+)', results_text)
                if material_id_match:
                    material_id = material_id_match.group(1)
                    logger.info(f"🔍 STRANDS: Getting enhanced data for {material_id}")
                    try:
                        detailed_data = self.mp_agent.select_material_by_id(material_id)
                        return {
                            "status": "success", 
                            "mp_data": detailed_data, 
                            "mcp_actions": ["select_material_by_id", "get_structure_data"],
                            "mcp_results": {"select_material_by_id": detailed_data}
                        }
                    except Exception as e:
                        logger.error(f"💥 STRANDS: Enhanced data retrieval failed: {e}")
                        # Fall through to basic search results
                
                # Return basic search results if enhanced lookup fails
                return {
                    "status": "success", 
                    "mp_data": {"results": search_results, "formula": formula, "count": len(search_results) if isinstance(search_results, list) else 1}, 
                    "mcp_actions": ["search_materials_by_formula"]
                }
            else:
                logger.warning(f"⚠️ STRANDS: Search by formula failed or returned error for {formula}")
                
        except Exception as e:
            logger.error(f"💥 STRANDS: Search by formula failed: {e}")
        
        # Fallback: try basic search if formula search fails
        try:
            logger.info(f"🔄 STRANDS: Falling back to basic search for {formula}")
            basic_results = self.mp_agent.search(formula)
            if basic_results and "error" not in str(basic_results).lower():
                return {
                    "status": "success", 
                    "mp_data": basic_results, 
                    "mcp_actions": ["search"]
                }
        except Exception as e:
            logger.error(f"💥 STRANDS: Basic search also failed: {e}")
        
        # Final fallback: return error but don't crash
        return {
            "status": "error", 
            "message": f"Material not found for {formula}", 
            "mcp_actions": [],
            "workflow_used": "Simple Query",
            "formula_searched": formula
        }
    
    def process_poscar_workflow(self, poscar_text: str, query: str) -> dict:
        """Process complete POSCAR workflow using Strands coordination"""
        logger.info("🎯 STRANDS SUPERVISOR: Starting POSCAR workflow")
        
        try:
            # Use Strands coordinator for complete workflow
            result = self.coordinator.execute_poscar_workflow(poscar_text, query)
            
            # Enhance with additional analysis if needed
            if "structure_analysis" in result and "dft_parameters" in result:
                material_id = result["structure_analysis"].get("material_id")
                if material_id:
                    # Add quantum code generation
                    quantum_prompt = f"Generate VQE code for {material_id} using extracted DFT parameters"
                    quantum_analysis = self.agent(quantum_prompt)
                    result["quantum_code"] = quantum_analysis
            
            logger.info("✅ STRANDS SUPERVISOR: POSCAR workflow completed")
            return result
            
        except Exception as e:
            logger.error(f"💥 STRANDS SUPERVISOR: POSCAR workflow failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def process_complex_query(self, query: str) -> dict:
        """Process complex queries using agentic loops"""
        logger.info(f"🔄 STRANDS SUPERVISOR: Starting agentic loop for complex query")
        
        # Check if query needs iterative solving
        complexity_check = f"""Is this query complex enough to need iterative solving? 
        Query: {query}
        
        Complex queries involve: multiple materials, optimization, parameter tuning, multi-step analysis.
        Return JSON: {{"complex": bool, "reasoning": "string"}}"""
        
        try:
            response = self.agent(complexity_check)
            # Handle different response types
            if hasattr(response, 'text'):
                response_text = response.text
            elif hasattr(response, 'message') and hasattr(response.message, 'content'):
                content = response.message.content
                if isinstance(content, list) and len(content) > 0:
                    response_text = content[0].get('text', str(response))
                else:
                    response_text = str(content)
            else:
                response_text = str(response)
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                complexity = json.loads(json_match.group())
                if complexity.get("complex", False):
                    return self.agentic_loop.iterative_solve(query)
            
            # Fall back to standard processing
            return self.process_query(query, "")
            
        except Exception as e:
            logger.error(f"💥 STRANDS SUPERVISOR: Complexity check failed: {e}")
            return self.process_query(query, "")
    
    def intelligent_workflow_dispatch(self, query: str, poscar_text: str = None) -> dict:
        """Intelligently dispatch to appropriate workflow based on query and context"""
        logger.info(f"🤖 STRANDS: Intelligent workflow dispatch for query: '{query[:50]}...'")
        
        try:
            # Check for POSCAR analysis
            if poscar_text and poscar_text.strip():
                logger.info("📁 STRANDS: POSCAR provided, using POSCAR analysis workflow")
                result = self.process_poscar_workflow(poscar_text, query)
                result['workflow_used'] = 'POSCAR Analysis'
                return result
            
            # Check for complex query indicators using Strands intelligence
            # Check for specialized agent workflows
            query_lower = query.lower()
            
            # DFT parameter extraction
            dft_keywords = ['dft parameter', 'hopping parameter', 'hubbard u', 'tight binding', 'extract dft', 'dft calculation', 'hamiltonian']
            if any(keyword in query_lower for keyword in dft_keywords):
                logger.info("🔬 STRANDS: DFT parameter extraction detected, using specialized workflow")
                result = self.process_complex_query(query)
                result['workflow_used'] = 'DFT Parameter Extraction'
                return result
            
            # Structure analysis (POSCAR matching)
            structure_keywords = ['poscar', 'structure match', 'crystal structure', 'lattice parameter', 'space group', 'structure analysis']
            if any(keyword in query_lower for keyword in structure_keywords):
                logger.info("🔍 STRANDS: Structure analysis detected, using specialized workflow")
                result = self.process_complex_query(query)
                result['workflow_used'] = 'Structure Analysis'
                return result
            
            # Multi-material comparison
            comparison_keywords = ['compare', 'versus', 'vs', 'difference between', 'multiple materials', 'batch analysis']
            if any(keyword in query_lower for keyword in comparison_keywords):
                logger.info("🔄 STRANDS: Multi-material comparison detected, using agentic loop")
                result = self.process_complex_query(query)
                result['workflow_used'] = 'Multi-Material Analysis'
                return result
            
            # Quick check for simple material ID queries (only if not DFT-related)
            if re.search(r'mp-\d+', query.lower()):
                logger.info("📝 STRANDS: Material ID detected, using simple workflow")
                result = self.process_query(query, "")
                result['workflow_used'] = 'Simple Query'
                return result
            
            complexity_prompt = f"""Analyze this query and determine which specialized agent to use: "{query}"
            
            Available specialized agents:
            - DFT Agent: Extract hopping parameters, Hubbard U values, tight-binding models
            - Structure Agent: POSCAR analysis, structure matching, crystal analysis
            - Agentic Loop: Multi-material comparisons, optimization, iterative analysis
            - Simple Query: Basic material lookup, single VQE circuits
            
            Keywords for each agent:
            - DFT: "dft parameter", "hopping", "hubbard u", "tight binding", "hamiltonian"
            - Structure: "poscar", "structure match", "crystal structure", "lattice"
            - Agentic: "compare", "optimize", "multiple materials", "batch"
            - Simple: material IDs (mp-149), basic searches
            
            Return JSON: {{"agent_type": "dft|structure|agentic|simple", "reasoning": "string"}}"""
            
            logger.info("🧠 STRANDS: Calling Claude Sonnet 4.5 for complexity analysis...")
            try:
                response = self.agent(complexity_prompt)
                # Handle different response types
                if hasattr(response, 'text'):
                    response_text = response.text
                elif hasattr(response, 'message') and hasattr(response.message, 'content'):
                    content = response.message.content
                    if isinstance(content, list) and len(content) > 0:
                        response_text = content[0].get('text', str(response))
                    else:
                        response_text = str(content)
                else:
                    response_text = str(response)
                logger.info(f"✅ STRANDS: Claude response received: {len(response_text)} chars")
                
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                    logger.info(f"📊 STRANDS: Agent analysis: {analysis}")
                    agent_type = analysis.get("agent_type", "simple")
                    
                    if agent_type == "dft":
                        logger.info(f"🔬 STRANDS: DFT agent selected: {analysis.get('reasoning')}")
                        result = self._execute_dft_workflow(query)
                        result['workflow_used'] = 'DFT Parameter Extraction'
                        return result
                    elif agent_type == "structure":
                        logger.info(f"🏗️ STRANDS: Structure agent selected: {analysis.get('reasoning')}")
                        result = self._execute_structure_workflow(query)
                        result['workflow_used'] = 'Structure Analysis'
                        return result
                    elif agent_type == "agentic":
                        logger.info(f"🔄 STRANDS: Agentic loop selected: {analysis.get('reasoning')}")
                        result = self.process_complex_query(query)
                        result['workflow_used'] = 'Multi-Agent Analysis'
                        return result
                else:
                    logger.warning("⚠️ STRANDS: No JSON found in Claude response")
            except Exception as e:
                logger.error(f"💥 STRANDS: Claude call failed: {e}")
                logger.error(f"💥 STRANDS: Error type: {type(e).__name__}")
                import traceback
                logger.error(f"💥 STRANDS: Traceback: {traceback.format_exc()}")
            
            # Default to simple query workflow
            logger.info("💬 STRANDS: Using simple query workflow")
            result = self.process_query(query, "")
            result['workflow_used'] = 'Simple Query'
            return result
            
        except Exception as e:
            logger.error(f"💥 STRANDS: Workflow dispatch failed: {e}")
            return {"status": "error", "message": str(e), "workflow_used": "Error"}
    
    def _extract_formula_from_query(self, query: str) -> str:
        """Extract chemical formula from query text - check for material IDs first"""
        try:
            # Check for material IDs first (mp-XXXX)
            mp_match = re.search(r'(mp-\d+)', query.lower())
            if mp_match:
                material_id = mp_match.group(1)
                logger.info(f"🔍 STRANDS: Detected material ID: {material_id} - will use direct lookup")
                # For material ID queries, return the ID but mark as simple
                return material_id  # Return the material ID instead of formula
            
            # Skip MP search for simple molecules that don't exist in Materials Project
            query_lower = query.lower()
            molecular_keywords = ['h2', 'hydrogen molecule', 'water molecule', 'h2o molecule', 'co2', 'ch4', 'nh3']
            is_molecular_query = any(mol in query_lower for mol in molecular_keywords)
            if is_molecular_query:
                logger.info("🔍 STRANDS: Molecular query detected - skipping Materials Project search for simple molecule")
                return None  # Signal to skip MP search
            
            # Common materials mentioned in queries
            materials_map = {
                "graphene": "C", "carbon": "C", "diamond": "C",
                "silicon": "Si", "germanium": "Ge",
                "water": "H2O", "methane": "CH4",
                "mos2": "MoS2", "ws2": "WS2", "bn": "BN",
                "gan": "GaN", "gaas": "GaAs", "inp": "InP",
                "tio2": "TiO2", "sio2": "SiO2", "al2o3": "Al2O3"
            }
            
            for material, formula in materials_map.items():
                if material in query_lower:
                    logger.info(f"🔍 STRANDS: Detected {material} → {formula}")
                    return formula
            
            # Try to find chemical formulas in the text
            formula_pattern = r'\b[A-Z][a-z]?(?:\d+)?(?:[A-Z][a-z]?\d*)*\b'
            matches = re.findall(formula_pattern, query)
            if matches:
                # Filter out common English words
                chemical_formulas = [m for m in matches if len(m) <= 10 and not m.lower() in ['VQE', 'UCCSD', 'DFT', 'MP']]
                if chemical_formulas:
                    logger.info(f"🔍 STRANDS: Found formula pattern: {chemical_formulas[0]}")
                    return chemical_formulas[0]
            
            logger.info("🔍 STRANDS: No formula detected, using Si as default")
            return "Si"
            
        except Exception as e:
            logger.error(f"💥 STRANDS: Formula extraction failed: {e}")
            return "Si"
    
    def _is_braket_query(self, query: str) -> bool:
        """Detect if query is Braket-specific (NOT Materials Project)"""
        query_lower = query.lower()
        
        # High priority Braket indicators (always route to Braket)
        high_priority_keywords = [
            'braket', 'amazon braket', 'aws braket', 'braket mcp',
            'list devices', 'quantum device', 'quantum simulator',
            'sv1', 'dm1', 'braket server'
        ]
        
        # Pure algorithm keywords (no materials)
        pure_algorithm_keywords = [
            'bell pair', 'bell state', 'bell circuit',
            'ghz state', 'ghz circuit', 'ghz',
            'ascii diagram', 'ascii circuit', 'circuit diagram',
            'quantum fourier transform', 'qft circuit'
        ]
        
        # Check high priority first
        if any(keyword in query_lower for keyword in high_priority_keywords):
            return True
        
        # Check pure algorithm keywords (no materials mentioned)
        if any(keyword in query_lower for keyword in pure_algorithm_keywords):
            return True
        
        # IMPORTANT: VQE + Materials Project should NOT go to Braket
        # Only route VQE to Braket if NO materials are mentioned
        if 'vqe' in query_lower or 'variational quantum eigensolver' in query_lower:
            # Check if Materials Project materials are mentioned
            mp_materials = ['graphene', 'materials project', 'mp-', 'tio2', 'sio2', 'diamond', 'silicon', 'using materials project']
            if any(material in query_lower for material in mp_materials):
                return False  # Route to Materials Project, not Braket
            else:
                return True   # Pure VQE without materials -> Braket
        
        return False
    
    def _handle_braket_query(self, query: str) -> dict:
        """Handle Braket-specific queries using Braket MCP integration"""
        if not braket_integration.is_available():
            return {
                "status": "error", 
                "message": "Braket MCP not available. Install dependencies: pip install amazon-braket-sdk qiskit-braket-provider fastmcp"
            }
        
        query_lower = query.lower()
        
        try:
            # VQE circuits (only for pure algorithm requests, not Materials Project)
            if 'vqe' in query_lower or ('variational' in query_lower and 'quantum' in query_lower):
                logger.info("⚙️ STRANDS: Creating pure VQE circuit (no Materials Project data)")
                # Use simple material data for pure algorithm
                material_data = {'formula': 'H2', 'band_gap': 8.0, 'formation_energy': 0.0}
                result = braket_integration.create_vqe_circuit(material_data)
                return {
                    "status": "success",
                    "braket_data": result,
                    "mcp_actions": ["create_vqe_circuit"],
                    "workflow_used": "Braket MCP",
                    "reasoning": "Pure VQE circuit generation using Amazon Braket MCP (no Materials Project data)"
                }
            
            # Bell pair circuits
            elif 'bell' in query_lower and ('pair' in query_lower or 'state' in query_lower or 'circuit' in query_lower):
                logger.info("🔔 STRANDS: Creating Bell pair circuit with Braket MCP")
                result = braket_integration.create_bell_pair_circuit()
                return {
                    "status": "success",
                    "braket_data": result,
                    "mcp_actions": ["create_bell_pair_circuit"],
                    "workflow_used": "Braket MCP",
                    "reasoning": "Bell state circuit generation using Amazon Braket MCP"
                }
            
            # GHZ circuits
            elif 'ghz' in query_lower:
                # Extract number of qubits if specified
                qubit_match = re.search(r'(\d+)\s*qubit', query_lower)
                num_qubits = int(qubit_match.group(1)) if qubit_match else 3
                
                logger.info(f"🌀 STRANDS: Creating {num_qubits}-qubit GHZ circuit with Braket MCP")
                result = braket_integration.create_ghz_circuit(num_qubits)
                return {
                    "status": "success",
                    "braket_data": result,
                    "mcp_actions": ["create_ghz_circuit"],
                    "workflow_used": "Braket MCP",
                    "reasoning": f"{num_qubits}-qubit GHZ state circuit generation using Amazon Braket MCP"
                }
            
            # Device listing
            elif 'device' in query_lower and ('list' in query_lower or 'available' in query_lower or 'status' in query_lower):
                logger.info("🖥️ STRANDS: Listing Braket devices")
                result = braket_integration.list_braket_devices()
                return {
                    "status": "success",
                    "braket_data": result,
                    "mcp_actions": ["list_braket_devices"],
                    "workflow_used": "Braket MCP",
                    "reasoning": "Amazon Braket device listing and status check"
                }
            
            # Simple circuit creation (no materials)
            elif 'circuit' in query_lower and ('create' in query_lower or 'build' in query_lower or 'generate' in query_lower):
                # Only handle if no Materials Project materials mentioned
                mp_materials = ['graphene', 'materials project', 'mp-', 'tio2', 'sio2', 'diamond', 'silicon']
                if not any(material in query_lower for material in mp_materials):
                    logger.info("🔧 STRANDS: Creating simple circuit with Braket MCP")
                    result = braket_integration.create_bell_pair_circuit()
                    return {
                        "status": "success",
                        "braket_data": result,
                        "mcp_actions": ["create_simple_circuit"],
                        "workflow_used": "Braket MCP",
                        "reasoning": "Simple quantum circuit generation using Amazon Braket MCP"
                    }
                else:
                    # This should go to Materials Project, not Braket
                    return {"status": "error", "message": "Material-specific circuits should use Materials Project workflow"}
            

            
            # General Braket status
            else:
                logger.info("📊 STRANDS: Getting Braket status and capabilities")
                result = braket_integration.get_braket_status()
                return {
                    "status": "success",
                    "braket_data": result,
                    "mcp_actions": ["get_braket_status"],
                    "workflow_used": "Braket MCP",
                    "reasoning": "Amazon Braket MCP status and capabilities check"
                }
                
        except Exception as e:
            logger.error(f"💥 STRANDS: Braket query failed: {e}")
            return {"status": "error", "message": f"Braket query failed: {str(e)}"}
    
    def _execute_dft_workflow(self, query: str) -> dict:
        """Execute DFT parameter extraction workflow"""
        try:
            # Extract material ID from query
            material_id = self._extract_formula_from_query(query)
            
            # Get MP data first
            mcp_wrapper = get_mcp_wrapper()
            if mcp_wrapper:
                search_result = mcp_wrapper.search_material(material_id)
                if search_result["status"] == "success":
                    # Use DFT agent to extract parameters
                    dft_result = self.dft_agent.extract_dft_parameters(material_id, search_result["data"])
                    
                    # Generate Hamiltonian code if requested
                    if "hamiltonian" in query.lower() or "tight binding" in query.lower():
                        hamiltonian_code = self.dft_agent.get_tight_binding_hamiltonian(material_id, dft_result)
                        dft_result["hamiltonian_code"] = hamiltonian_code
                    
                    return {
                        "status": "success",
                        "mp_data": search_result["data"],
                        "dft_parameters": dft_result,
                        "mcp_actions": ["search_materials_by_formula", "extract_dft_parameters"]
                    }
            
            return {"status": "error", "message": "Failed to get material data"}
        except Exception as e:
            logger.error(f"💥 STRANDS: DFT workflow failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def _execute_structure_workflow(self, query: str) -> dict:
        """Execute structure analysis workflow"""
        try:
            # Check if POSCAR is provided in query
            if "poscar" in query.lower():
                # Extract POSCAR from query or use example
                poscar_text = self._extract_poscar_from_query(query)
                formula = self._extract_formula_from_poscar(poscar_text)
                
                # Use structure agent for matching
                match_result = self.structure_agent.match_poscar_to_mp(poscar_text, formula)
                
                return {
                    "status": "success",
                    "structure_analysis": match_result,
                    "mcp_actions": ["poscar_structure_matching"]
                }
            else:
                # General structure analysis
                material_id = self._extract_formula_from_query(query)
                mcp_wrapper = get_mcp_wrapper()
                if mcp_wrapper:
                    search_result = mcp_wrapper.search_material(material_id)
                    return {
                        "status": "success",
                        "mp_data": search_result["data"],
                        "mcp_actions": ["search_materials_by_formula"]
                    }
            
            return {"status": "error", "message": "No structure data found"}
        except Exception as e:
            logger.error(f"💥 STRANDS: Structure workflow failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def _extract_poscar_from_query(self, query: str) -> str:
        """Extract POSCAR text from query or return example"""
        # Simple POSCAR example for testing
        return """Si2
1.0
   3.3335729999999999    0.0000000000000000    1.9246390000000000
   1.1111910000000000    3.1429239999999998    1.9246390000000000
   0.0000000000000000    0.0000000000000000    3.8492780000000000
Si
2
Direct
0.0000000000000000  0.0000000000000000  0.0000000000000000
0.2500000000000000  0.2500000000000000  0.2500000000000000"""
    
    def _extract_material_context(self, query: str) -> Dict[str, Any]:
        """Extract material information from query for Braket circuit generation."""
        query_lower = query.lower()
        
        # Material mapping
        material_map = {
            'graphene': {'formula': 'C', 'band_gap': 0.0, 'formation_energy': 0.0, 'crystal_system': 'hexagonal'},
            'diamond': {'formula': 'C', 'band_gap': 5.5, 'formation_energy': 0.0, 'crystal_system': 'cubic'},
            'h2': {'formula': 'H2', 'band_gap': 8.0, 'formation_energy': 0.0, 'crystal_system': 'molecular'},
            'hydrogen': {'formula': 'H2', 'band_gap': 8.0, 'formation_energy': 0.0, 'crystal_system': 'molecular'},
            'tio2': {'formula': 'TiO2', 'band_gap': 3.2, 'formation_energy': -2.5, 'crystal_system': 'tetragonal'},
            'sio2': {'formula': 'SiO2', 'band_gap': 9.0, 'formation_energy': -1.8, 'crystal_system': 'hexagonal'},
            'silicon': {'formula': 'Si', 'band_gap': 1.1, 'formation_energy': 0.0, 'crystal_system': 'cubic'}
        }
        
        # Check for material mentions
        for material, data in material_map.items():
            if material in query_lower:
                logger.info(f"🧬 STRANDS: Detected material {material} in query")
                return data
        
        # Default to H2 for VQE queries
        return {'formula': 'H2', 'band_gap': 8.0, 'formation_energy': 0.0, 'crystal_system': 'molecular'}
    
    def _extract_formula_from_poscar(self, poscar_text: str) -> str:
        """Extract chemical formula from POSCAR (from original supervisor)"""
        try:
            lines = poscar_text.strip().split('\n')
            for i, line in enumerate(lines[:10]):
                line = line.strip()
                if re.match(r'^[A-Z][a-z]?(?:\s+[A-Z][a-z]?)*$', line):
                    elements = line.split()
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
                    return elements[0]
            return "Si"  # fallback
        except Exception:
            return "Si"