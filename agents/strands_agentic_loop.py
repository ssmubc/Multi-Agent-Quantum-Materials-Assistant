from strands import Agent
from strands_tools import use_aws, retrieve, batch
import logging
import json

logger = logging.getLogger(__name__)

class StrandsAgenticLoop:
    """Enable agentic loops for iterative problem solving"""
    
    def __init__(self, mp_agent):
        self.mp_agent = mp_agent
        self.agent = Agent(
            model="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
            tools=[use_aws, retrieve, batch]
        )
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
        
        current_query = initial_query
        iteration = 0
        results = {"iterations": []}
        
        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"🔄 AGENTIC LOOP: Iteration {iteration}")
            
            # Enhanced agent decision with access to improved agents
            decision_prompt = f"""
            Iteration {iteration} of quantum materials analysis.
            
            Current query: {current_query}
            Previous results: {json.dumps(results.get("iterations", []), indent=2)}
            
            Available enhanced capabilities:
            - StrandsCoordinator: Multi-agent workflow orchestration
            - StrandsDFTAgent: Intelligent DFT parameter extraction with validation
            - StrandsStructureAgent: Hybrid pymatgen + AI structure matching
            - MCP Tools: search, plot_structure, build_supercell, moire_homobilayer
            
            Analyze the current state and decide:
            1. Is the problem solved? (yes/no)
            2. What's the next action needed?
            3. Which agent/tool should handle it? (coordinator/dft_agent/structure_agent/mcp_tool)
            4. What parameters to use?
            5. Should we use batch processing for multiple operations?
            
            Return JSON: {{"solved": bool, "next_action": "string", "agent_type": "string", "tool_name": "string", "params": {{}}, "use_batch": bool, "reasoning": "string"}}
            """
            
            try:
                response = self.agent(decision_prompt)
                decision = self._parse_decision(response)
                
                # Execute the decided action with improved agents
                action_result = self._execute_enhanced_action(decision, current_query, results)
                
                # Store iteration result
                iteration_data = {
                    "iteration": iteration,
                    "decision": decision,
                    "action_result": action_result,
                    "query": current_query
                }
                results["iterations"].append(iteration_data)
                
                # Check if problem is solved
                if decision.get("solved", False):
                    logger.info(f"✅ AGENTIC LOOP: Problem solved in {iteration} iterations")
                    results["status"] = "solved"
                    break
                
                # Update query for next iteration based on results
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
                return self.mp_agent.search(formula)
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
            return {"status": "error", "message": str(e)}
    
    def _generate_next_query(self, decision: dict, action_result: dict, current_query: str) -> str:
        """Generate next iteration query based on results"""
        
        next_query_prompt = f"""
        Based on the current analysis results, what should be the next query?
        
        Current query: {current_query}
        Last action: {decision.get("next_action")}
        Action result: {json.dumps(action_result, indent=2)}
        
        Generate a refined query for the next iteration that addresses any gaps or builds on the results.
        """
        
        try:
            response = self.agent(next_query_prompt)
            
            # Enhanced query refinement based on action results
            if "error" in str(action_result):
                refined_query = f"Fix the error in: {current_query}. Error: {action_result.get('message', 'Unknown error')}"
            elif "batch_completed" in str(action_result):
                refined_query = f"Analyze batch results for: {current_query}"
            elif "dft_parameters" in str(action_result):
                refined_query = f"Generate quantum simulation using DFT parameters for: {current_query}"
            else:
                refined_query = response.strip()
            
            return refined_query
        except:
            return current_query  # Fallback to current query