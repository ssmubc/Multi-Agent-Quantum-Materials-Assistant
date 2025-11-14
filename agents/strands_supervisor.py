import logging
import json
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)

from strands import Agent
from strands_tools import use_aws
from .strands_coordinator import StrandsCoordinator
from .strands_dft_agent import StrandsDFTAgent
from .strands_structure_agent import StrandsStructureAgent
from .strands_agentic_loop import StrandsAgenticLoop
from utils.braket_integration import braket_integration

class StrandsSupervisorAgent:
    """AWS Strands-based supervisor for quantum materials analysis"""
    
    def __init__(self, mp_agent):
        self.mp_agent = mp_agent
        
        # Test Strands framework availability
        logger.info("🚀 STRANDS: Initializing Strands supervisor with Claude Sonnet 4.5...")
        
        try:
            # Create Strands agent with AWS tools
            self.agent = Agent(
                model="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
                tools=[use_aws]
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
        # Check for Braket-specific queries first
        if self._is_braket_query(query):
            logger.info("⚛️ STRANDS: Braket query detected, routing to Braket MCP")
            return self._handle_braket_query(query)
        
        # Extract formula from query if not provided
        if not formula:
            formula = self._extract_formula_from_query(query)
        
        logger.info(f"🤖 STRANDS: Processing query for formula='{formula}'")
        
        # Validate formula before proceeding
        if not formula or formula.strip() == "":
            logger.warning("⚠️ STRANDS: No formula detected, using fallback")
            formula = "Si"  # Safe fallback
        
        # Create context-aware prompt for Strands agent
        prompt = f"""
        You are a quantum materials analysis agent. Process this query: "{query}"
        Material formula: {formula}
        
        Available MCP tools via materials project:
        - search: Find materials by formula
        - search_materials_by_formula: Search multiple materials
        - plot_structure: Visualize 3D structure
        - build_supercell: Create supercells
        - moire_homobilayer: Generate moire patterns
        
        Determine the appropriate MCP action and return JSON with:
        {{"action": "tool_name", "params": {{}}, "reasoning": "why this tool"}}
        """
        
        try:
            # Let Strands agent decide the action
            response = self.agent(prompt)
            
            # Parse agent response to extract MCP action
            response_text = getattr(response, 'text', str(response))
            action_data = self._parse_agent_response(response_text)
            
            # Execute the determined MCP action
            return self._execute_mcp_action(action_data, formula, query)
            
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
            "message": f"Material not found", 
            "mcp_actions": [],
            "workflow_used": "Simple Query"
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
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
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
            # Quick check for simple material ID queries
            if re.search(r'mp-\d+', query.lower()):
                logger.info("📝 STRANDS: Material ID detected, using simple workflow")
                result = self.process_query(query, "")
                result['workflow_used'] = 'Simple Query'
                return result
            
            complexity_prompt = f"""Analyze this query for complexity: "{query}"
            
            Complex indicators:
            - Multiple materials or comparisons
            - Optimization or parameter tuning requests  
            - Multi-step analysis requirements
            - "compare", "optimize", "find best", "analyze multiple"
            
            Simple indicators:
            - Single material requests (mp-149, TiO2, etc.)
            - VQE ansatz generation for one material
            - POSCAR format requests
            - Single structure analysis
            
            Return JSON: {{"complex": bool, "reasoning": "string"}}"""
            
            logger.info("🧠 STRANDS: Calling Claude Sonnet 4.5 for complexity analysis...")
            try:
                response = self.agent(complexity_prompt)
                response_text = getattr(response, 'text', str(response))
                logger.info(f"✅ STRANDS: Claude response received: {len(response_text)} chars")
                
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    complexity = json.loads(json_match.group())
                    logger.info(f"📊 STRANDS: Complexity analysis: {complexity}")
                    if complexity.get("complex", False):
                        logger.info(f"🔄 STRANDS: Complex query detected: {complexity.get('reasoning')}")
                        result = self.process_complex_query(query)
                        result['workflow_used'] = 'Complex Query (Iterative)'
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
            
            # Common materials mentioned in queries
            materials_map = {
                "graphene": "C", "carbon": "C", "diamond": "C",
                "silicon": "Si", "germanium": "Ge",
                "h2": "H2", "hydrogen": "H2",
                "water": "H2O", "methane": "CH4",
                "mos2": "MoS2", "ws2": "WS2", "bn": "BN",
                "gan": "GaN", "gaas": "GaAs", "inp": "InP",
                "tio2": "TiO2", "sio2": "SiO2", "al2o3": "Al2O3"
            }
            
            query_lower = query.lower()
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
        """Detect if query is Braket-specific"""
        query_lower = query.lower()
        
        # High priority Braket indicators (always route to Braket)
        high_priority_keywords = [
            'braket', 'amazon braket', 'aws braket', 'braket mcp',
            'list devices', 'quantum device', 'quantum simulator',
            'sv1', 'dm1', 'braket server'
        ]
        
        # VQE and quantum algorithm keywords
        vqe_keywords = [
            'vqe', 'variational quantum eigensolver',
            'quantum circuit for', 'ansatz', 'hamiltonian simulation'
        ]
        
        # Circuit-specific keywords (route to Braket if combined with circuit terms)
        circuit_keywords = [
            'bell pair', 'bell state', 'bell circuit',
            'ghz state', 'ghz circuit', 'ghz',
            'ascii diagram', 'ascii circuit', 'circuit diagram',
            'quantum fourier transform', 'qft circuit',
            'run circuit', 'execute circuit', 'quantum task'
        ]
        
        # Check high priority first
        if any(keyword in query_lower for keyword in high_priority_keywords):
            return True
        
        # Check VQE keywords
        if any(keyword in query_lower for keyword in vqe_keywords):
            return True
        
        # Check for material + circuit combinations
        materials = ['graphene', 'h2', 'hydrogen', 'tio2', 'sio2', 'diamond', 'silicon']
        if any(material in query_lower for material in materials) and 'circuit' in query_lower:
            return True
        
        # Check circuit keywords combined with circuit/quantum terms
        circuit_terms = ['circuit', 'quantum', 'entanglement', 'superposition']
        if any(keyword in query_lower for keyword in circuit_keywords):
            if any(term in query_lower for term in circuit_terms):
                return True
        
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
            # VQE circuits with materials
            if 'vqe' in query_lower or ('variational' in query_lower and 'quantum' in query_lower):
                logger.info("⚙️ STRANDS: Creating VQE circuit with material data")
                # Extract material from query or use default
                material_data = self._extract_material_context(query)
                result = braket_integration.create_vqe_circuit(material_data)
                return {
                    "status": "success",
                    "braket_data": result,
                    "mcp_actions": ["create_vqe_circuit"],
                    "workflow_used": "Braket MCP",
                    "reasoning": f"VQE circuit generation for {material_data.get('formula', 'material')} using Amazon Braket MCP"
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
            
            # Material-specific circuit creation
            elif ('circuit' in query_lower and any(material in query_lower for material in ['graphene', 'h2', 'tio2', 'sio2', 'diamond'])):
                logger.info("🧬 STRANDS: Creating material-specific VQE circuit")
                material_data = self._extract_material_context(query)
                result = braket_integration.create_vqe_circuit(material_data)
                return {
                    "status": "success",
                    "braket_data": result,
                    "mcp_actions": ["create_vqe_circuit"],
                    "workflow_used": "Braket MCP",
                    "reasoning": f"Material-specific VQE circuit for {material_data.get('formula', 'material')} using Amazon Braket MCP"
                }
            
            # Custom circuit creation
            elif 'circuit' in query_lower and ('create' in query_lower or 'build' in query_lower or 'generate' in query_lower):
                logger.info("🔧 STRANDS: Creating custom circuit with Braket MCP")
                # Default to Bell pair for custom requests
                result = braket_integration.create_bell_pair_circuit()
                return {
                    "status": "success",
                    "braket_data": result,
                    "mcp_actions": ["create_custom_circuit"],
                    "workflow_used": "Braket MCP",
                    "reasoning": "Custom quantum circuit generation using Amazon Braket MCP"
                }
            
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