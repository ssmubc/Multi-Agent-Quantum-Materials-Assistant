from strands import Agent
from strands_tools import use_aws
from .strands_coordinator import StrandsCoordinator
from .strands_dft_agent import StrandsDFTAgent
from .strands_structure_agent import StrandsStructureAgent
from .strands_agentic_loop import StrandsAgenticLoop
import logging
import json

logger = logging.getLogger(__name__)

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
            import re
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
        """Handle moire bilayer requests with intelligent material mapping"""
        # Override formula for 2D material moire queries (from original supervisor)
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
        
        mp_data = self.mp_agent.search(formula)
        if not mp_data or mp_data.get("error"):
            return {"status": "error", "message": "Material not found"}
        
        structure_uri = mp_data.get("structure_uri")
        if structure_uri:
            # Extract moire parameters from query (from original supervisor)
            twist_angle = 1.1  # magic angle default
            interlayer_spacing = 3.4  # default for graphene-like
            
            # Try to extract twist angle from query
            import re
            angle_match = re.search(r'(\d+\.?\d*)\s*degree', query_lower)
            if angle_match:
                twist_angle = float(angle_match.group(1))
                logger.info(f"🌀 STRANDS: Extracted twist angle: {twist_angle}°")
            
            # Try to extract interlayer spacing
            spacing_match = re.search(r'(\d+\.?\d*)\s*[åa]', query_lower)
            if spacing_match:
                interlayer_spacing = float(spacing_match.group(1))
                logger.info(f"🌀 STRANDS: Extracted interlayer spacing: {interlayer_spacing} Å")
            
            moire_result = self.mp_agent.moire_homobilayer(structure_uri, interlayer_spacing, 10, twist_angle, 15.0)
            logger.info(f"🌀 STRANDS: Called moire_homobilayer tool with {twist_angle}° twist, {interlayer_spacing} Å spacing")
            
            return {
                "status": "success",
                "mp_data": mp_data,
                "mcp_actions": ["select_material_by_id", "get_structure_data", "moire_homobilayer"],
                "moire_params": {"twist_angle": twist_angle, "interlayer_spacing": interlayer_spacing}
            }
        return {"status": "error", "message": "No structure URI"}
    
    def _handle_supercell(self, formula: str, query: str) -> dict:
        """Handle supercell requests"""
        mp_data = self.mp_agent.search(formula)
        if not mp_data or mp_data.get("error"):
            return {"status": "error", "message": "Material not found"}
        
        structure_uri = mp_data.get("structure_uri")
        if structure_uri:
            supercell_result = self.mp_agent.build_supercell(structure_uri, {"scaling_matrix": [[2,0,0],[0,2,0],[0,0,2]]})
            return {"status": "success", "mp_data": mp_data, "mcp_actions": ["build_supercell"]}
        return {"status": "error", "message": "No structure URI"}
    
    def _handle_visualization(self, formula: str) -> dict:
        """Handle visualization requests"""
        mp_data = self.mp_agent.search(formula)
        if not mp_data or mp_data.get("error"):
            return {"status": "error", "message": "Material not found"}
        
        structure_uri = mp_data.get("structure_uri")
        if structure_uri:
            plot_result = self.mp_agent.plot_structure(structure_uri, [1, 1, 1])
            return {"status": "success", "mp_data": mp_data, "mcp_actions": ["plot_structure"]}
        return {"status": "error", "message": "No structure URI"}
    
    def _handle_formula_search(self, formula: str) -> dict:
        """Handle formula search requests"""
        search_results = self.mp_agent.search_materials_by_formula(formula)
        return {"status": "success", "mp_data": {"formula": formula}, "mcp_actions": ["search_materials_by_formula"]}
    
    def _handle_standard_lookup(self, formula: str) -> dict:
        """Handle standard material lookup"""
        mp_data = self.mp_agent.search(formula)
        return {"status": "success" if mp_data and not mp_data.get("error") else "error", "mp_data": mp_data, "mcp_actions": ["search"]}
    
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
            import re
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
            complexity_prompt = f"""Analyze this query for complexity: "{query}"
            
            Complex indicators:
            - Multiple materials or comparisons
            - Optimization or parameter tuning requests  
            - Multi-step analysis requirements
            - "compare", "optimize", "find best", "analyze multiple"
            
            Return JSON: {{"complex": bool, "reasoning": "string"}}"""
            
            logger.info("🧠 STRANDS: Calling Claude Sonnet 4.5 for complexity analysis...")
            try:
                response = self.agent(complexity_prompt)
                response_text = getattr(response, 'text', str(response))
                logger.info(f"✅ STRANDS: Claude response received: {len(response_text)} chars")
                
                import re
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
        """Extract chemical formula from query text"""
        try:
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
            import re
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
    
    def _extract_formula_from_poscar(self, poscar_text: str) -> str:
        """Extract chemical formula from POSCAR (from original supervisor)"""
        try:
            lines = poscar_text.strip().split('\n')
            for i, line in enumerate(lines[:10]):
                line = line.strip()
                import re
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