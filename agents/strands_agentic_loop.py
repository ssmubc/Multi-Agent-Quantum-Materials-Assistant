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
batch = None

try:
    from strands_agents import Agent as RealAgent
    from strands_agents_tools import use_aws as real_use_aws, retrieve as real_retrieve, batch as real_batch
    Agent = RealAgent
    use_aws = real_use_aws
    retrieve = real_retrieve
    batch = real_batch
except ImportError as e:
    logger.warning(f"Strands not available locally: {e}")

class StrandsAgenticLoop:
    """Enable agentic loops for iterative problem solving"""
    
    def __init__(self, mp_agent):
        self.mp_agent = mp_agent
        if use_aws:
            self.agent = Agent(
                model="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
                tools=[use_aws, retrieve, batch]
            )
        else:
            self.agent = MockAgent()
        self.max_iterations = 5
        self.conversation_history = []
        
        # Initialize improved agents for iterative workflows
        from .strands_coordinator import StrandsCoordinator
        from .strands_dft_agent import StrandsDFTAgent
        from .strands_structure_agent import StrandsStructureAgent
        
        self.coordinator = StrandsCoordinator(mp_agent)
        self.dft_agent = StrandsDFTAgent()
        self.structure_agent = StrandsStructureAgent(mp_agent)
    
    def iterative_solve(self, initial_query: str) -> dict:
        """Solve complex problems through iterative agent loops"""
        
        # Extract materials from query dynamically
        materials_to_process = self._extract_materials_from_query(initial_query)
        logger.info(f"🔄 AGENTIC LOOP: Detected materials: {materials_to_process}")
        
        current_query = initial_query
        iteration = 0
        results = {"iterations": [], "materials_data": {}, "materials_to_process": materials_to_process}
        
        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"🔄 AGENTIC LOOP: Iteration {iteration}")
            
            # Check progress and determine next action
            progress_status = self._assess_progress(results, materials_to_process, current_query)
            
            if progress_status["solved"]:
                logger.info(f"✅ AGENTIC LOOP: Problem solved in {iteration-1} iterations")
                results["status"] = "solved"
                break
            
            # Get next action based on progress
            decision = progress_status["next_decision"]
            
            try:
                # Execute the decided action
                action_result = self._execute_enhanced_action(decision, current_query, results)
                
                # Store material data if this was a search
                if decision.get("agent_type") == "mcp_tool" and decision.get("tool_name") == "search":
                    formula = decision.get("params", {}).get("formula")
                    if formula and action_result.get("status") != "error":
                        results["materials_data"][formula] = action_result
                        logger.info(f"✅ AGENTIC LOOP: Stored data for {formula}")
                
                # Store iteration result
                iteration_data = {
                    "iteration": iteration,
                    "decision": decision,
                    "action_result": action_result,
                    "query": current_query
                }
                results["iterations"].append(iteration_data)
                
                # Update query for next iteration
                current_query = self._generate_next_query(decision, action_result, current_query)
                
            except Exception as e:
                logger.error(f"💥 AGENTIC LOOP: Iteration {iteration} failed: {e}")
                results["status"] = "error"
                results["error"] = str(e)
                break
        
        if iteration >= self.max_iterations:
            results["status"] = "max_iterations_reached"
        
        return results
    
    def _parse_decision(self, response: str) -> dict:
        """Parse agent decision from response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "solved": False,
            "next_action": "search",
            "mcp_tool": "search",
            "params": {},
            "reasoning": "Fallback decision"
        }
    
    def _execute_enhanced_action(self, decision: dict, query: str, context: dict) -> dict:
        """Execute action using improved agents and batch processing"""
        agent_type = decision.get("agent_type", "mcp_tool")
        tool_name = decision.get("tool_name", "search")
        params = decision.get("params", {})
        use_batch = decision.get("use_batch", False)
        
        try:
            if agent_type == "coordinator":
                # Use coordinator for complex workflows
                if "poscar" in query.lower():
                    poscar_text = params.get("poscar_text", "Si\n1.0\n5.43 0 0\n0 5.43 0\n0 0 5.43\nSi\n2\nDirect\n0.0 0.0 0.0\n0.25 0.25 0.25")
                    return self.coordinator.execute_poscar_workflow(poscar_text, query)
                else:
                    return {"status": "coordinator_ready", "message": "Coordinator available for complex workflows"}
            
            elif agent_type == "dft_agent":
                # Use DFT agent for parameter extraction
                material_id = params.get("material_id", "mp-149")
                mp_data = context.get("iterations", [{}])[-1].get("action_result", {})
                result = self.dft_agent.extract_dft_parameters(material_id, mp_data)
                
                # Also generate Hamiltonian if requested
                if "hamiltonian" in query.lower():
                    hamiltonian_code = self.dft_agent.get_tight_binding_hamiltonian(material_id, result)
                    result["hamiltonian_code"] = hamiltonian_code
                
                return result
            
            elif agent_type == "structure_agent":
                # Use structure agent for POSCAR matching
                poscar_text = params.get("poscar_text", "")
                formula = params.get("formula", "Si")
                if poscar_text:
                    return self.structure_agent.match_poscar_to_mp(poscar_text, formula)
                else:
                    return {"status": "error", "message": "POSCAR text required for structure matching"}
            
            elif agent_type == "mcp_tool":
                # Enhanced MCP tool execution
                if use_batch:
                    return self._execute_batch_mcp_actions(decision, params)
                else:
                    return self._execute_single_mcp_action(tool_name, params)
            
            return {"status": "unknown_agent_type", "agent_type": agent_type}
            
        except Exception as e:
            logger.error(f"💥 AGENTIC LOOP: Enhanced action execution failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def _execute_batch_mcp_actions(self, decision: dict, params: dict) -> dict:
        """Execute multiple MCP actions in batch using Strands batch tool"""
        try:
            # Create batch invocations for multiple materials or operations
            materials = params.get("materials", ["Si", "C", "GaN"])
            tool_name = decision.get("tool_name", "search")
            
            invocations = []
            for material in materials:
                if tool_name == "search":
                    # Batch material searches
                    invocations.append({
                        "name": "use_aws",
                        "arguments": {
                            "service_name": "custom",
                            "operation_name": "mp_search",
                            "parameters": {"formula": material},
                            "label": f"Search {material}"
                        }
                    })
            
            if invocations:
                batch_result = self.agent.tool.batch(invocations=invocations)
                return {"status": "batch_completed", "results": batch_result, "materials": materials}
            else:
                return {"status": "no_batch_operations", "message": "No valid batch operations created"}
                
        except Exception as e:
            logger.error(f"💥 AGENTIC LOOP: Batch execution failed: {e}")
            return {"status": "batch_error", "message": str(e)}
    
    def _execute_single_mcp_action(self, tool_name: str, params: dict) -> dict:
        """Execute single MCP action with enhanced parameter handling"""
        try:
            if tool_name == "search":
                formula = params.get("formula", "Si")
                logger.info(f"🔍 AGENTIC LOOP: Searching for material {formula}")
                # Use search_materials_by_formula for better results
                result = self.mp_agent.search_materials_by_formula(formula)
                if result:
                    return {"status": "success", "data": result, "formula": formula}
                else:
                    return {"status": "error", "message": f"No results for {formula}"}
            elif tool_name == "moire_homobilayer":
                structure_uri = params.get("structure_uri")
                twist_angle = params.get("twist_angle", 1.1)
                interlayer_spacing = params.get("interlayer_spacing", 3.4)
                if structure_uri:
                    return self.mp_agent.moire_homobilayer(structure_uri, interlayer_spacing, 10, twist_angle, 15.0)
            elif tool_name == "plot_structure":
                structure_uri = params.get("structure_uri")
                dimensions = params.get("dimensions", [1, 1, 1])
                if structure_uri:
                    return self.mp_agent.plot_structure(structure_uri, dimensions)
            elif tool_name == "build_supercell":
                structure_uri = params.get("structure_uri")
                scaling_matrix = params.get("scaling_matrix", [[2,0,0],[0,2,0],[0,0,2]])
                if structure_uri:
                    return self.mp_agent.build_supercell(structure_uri, {"scaling_matrix": scaling_matrix})
            
            return {"status": "action_executed", "tool": tool_name}
            
        except Exception as e:
            logger.error(f"💥 AGENTIC LOOP: MCP action {tool_name} failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def _extract_materials_from_query(self, query: str) -> list:
        """Extract materials from query dynamically"""
        import re
        
        # Material name to formula mapping
        material_map = {
            'silicon': 'Si', 'germanium': 'Ge', 'carbon': 'C', 'graphene': 'C',
            'diamond': 'C', 'tin': 'Sn', 'lead': 'Pb', 'gallium arsenide': 'GaAs',
            'gallium nitride': 'GaN', 'indium phosphide': 'InP', 'titanium dioxide': 'TiO2',
            'silicon dioxide': 'SiO2', 'aluminum oxide': 'Al2O3', 'molybdenum disulfide': 'MoS2',
            'tungsten disulfide': 'WS2', 'boron nitride': 'BN', 'h-bn': 'BN'
        }
        
        query_lower = query.lower()
        materials = []
        
        # Check for material names
        for name, formula in material_map.items():
            if name in query_lower and formula not in materials:
                materials.append(formula)
        
        # Check for chemical formulas directly
        formula_pattern = r'\b[A-Z][a-z]?(?:\d+)?(?:[A-Z][a-z]?\d*)*\b'
        formula_matches = re.findall(formula_pattern, query)
        for formula in formula_matches:
            if len(formula) <= 10 and formula not in ['VQE', 'DFT', 'MP'] and formula not in materials:
                materials.append(formula)
        
        return materials if materials else ['Si']  # Default fallback
    
    def _assess_progress(self, results: dict, materials_to_process: list, current_query: str) -> dict:
        """Assess current progress and determine next action"""
        materials_data = results.get("materials_data", {})
        processed_materials = list(materials_data.keys())
        
        # Check if all materials have been processed
        unprocessed = [m for m in materials_to_process if m not in processed_materials]
        
        if not unprocessed:
            # All materials processed, ready for comparison/analysis
            if "compare" in current_query.lower() or "dft" in current_query.lower():
                return {
                    "solved": True,
                    "next_decision": {
                        "agent_type": "comparison",
                        "reasoning": f"All {len(materials_to_process)} materials processed, ready for comparison"
                    }
                }
            else:
                return {"solved": True, "next_decision": {}}
        
        # Process next material
        next_material = unprocessed[0]
        return {
            "solved": False,
            "next_decision": {
                "agent_type": "mcp_tool",
                "tool_name": "search",
                "params": {"formula": next_material},
                "reasoning": f"Processing material {next_material} ({len(processed_materials)+1}/{len(materials_to_process)})"
            }
        }
    
    def _generate_next_query(self, decision: dict, action_result: dict, current_query: str) -> str:
        """Generate next iteration query based on results"""
        
        # Enhanced query refinement based on action results
        if "error" in str(action_result):
            return f"Fix the error in: {current_query}. Error: {action_result.get('message', 'Unknown error')}"
        elif "comparison" in decision.get("agent_type", ""):
            return f"Complete comparison analysis for: {current_query}"
        else:
            return current_query  # Keep current query for material processing