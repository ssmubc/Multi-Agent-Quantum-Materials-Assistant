import logging
from .strands_dft_agent import StrandsDFTAgent
from .strands_structure_agent import StrandsStructureAgent

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
batch = None
retrieve = None

try:
    from strands_agents import Agent as RealAgent
    from strands_agents_tools import use_aws as real_use_aws, batch as real_batch, retrieve as real_retrieve
    Agent = RealAgent
    use_aws = real_use_aws
    batch = real_batch
    retrieve = real_retrieve
except ImportError as e:
    logger.warning(f"Strands not available locally: {e}")
import json
import re

class StrandsCoordinator:
    """Strands-based multi-agent coordinator replacing aws_strands_coordinator"""
    
    def __init__(self, mp_agent):
        self.mp_agent = mp_agent
        if use_aws:
            self.coordinator = Agent(
                model="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
                tools=[use_aws, batch, retrieve]
            )
        else:
            self.coordinator = MockAgent()
        
        # Initialize specialized agents with capabilities
        self.agents = {
            "structure_matcher": {
                "instance": StrandsStructureAgent(mp_agent),
                "capabilities": ["pymatgen_analysis", "structure_comparison"],
                "type": "specialist"
            },
            "dft_extractor": {
                "instance": StrandsDFTAgent(),
                "capabilities": ["parameter_extraction", "dft_analysis"],
                "type": "specialist"
            },
            "quantum_simulator": {
                "instance": None,  # Generated via coordinator
                "capabilities": ["qiskit_code", "hamiltonian_construction"],
                "type": "generator"
            }
        }
        self.workflow_state = {}
    
    def execute_poscar_workflow(self, poscar_text: str, query: str) -> dict:
        """Execute complete POSCAR analysis workflow using Strands coordination"""
        
        workflow_prompt = f"""
        Coordinate a multi-agent POSCAR analysis workflow.
        
        POSCAR content:
        {poscar_text}
        
        User query: {query}
        
        Available agents:
        1. Structure Agent: Match POSCAR to Materials Project entries
        2. DFT Agent: Extract realistic DFT parameters
        3. Quantum Agent: Generate quantum simulation code
        
        Plan the workflow execution order and dependencies:
        1. Which agents to use?
        2. What sequence/dependencies?
        3. How to combine results?
        
        Return JSON workflow plan: {{"agents": ["agent1", "agent2"], "sequence": "parallel|sequential", "reasoning": "explanation"}}
        """
        
        try:
            # Get workflow plan from coordinator
            response = self.coordinator(workflow_prompt)
            workflow_plan = self._parse_workflow_plan(response)
            
            # Execute the planned workflow
            results = self._execute_workflow(workflow_plan, poscar_text, query)
            
            logger.info("✅ STRANDS COORDINATOR: Workflow completed")
            return results
            
        except Exception as e:
            logger.error(f"💥 STRANDS COORDINATOR: Error: {e}")
            return {"status": "error", "message": str(e)}
    
    def _parse_workflow_plan(self, response: str) -> dict:
        """Parse workflow plan from coordinator response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Default workflow plan
        return {
            "agents": ["structure", "dft", "quantum"],
            "sequence": "sequential",
            "reasoning": "Standard POSCAR analysis pipeline"
        }
    
    def _execute_workflow(self, plan: dict, poscar_text: str, query: str) -> dict:
        """Execute workflow with dependency management like aws_strands_coordinator"""
        workflow_id = f"poscar_analysis_{hash(poscar_text) % 10000}"
        
        # Create task definitions with dependencies
        tasks = self._create_task_definitions(plan, poscar_text, query)
        
        results = {
            "workflow_id": workflow_id,
            "workflow_plan": plan,
            "tasks": tasks
        }
        
        # Execute with dependency resolution
        completed_tasks = set()
        task_results = {}
        
        while len(completed_tasks) < len(tasks):
            for task in tasks:
                task_id = task["agent"]
                
                if task_id in completed_tasks:
                    continue
                
                # Check dependencies
                deps_met = all(dep in completed_tasks for dep in task.get("dependencies", []))
                
                if deps_met:
                    # Execute task
                    task_result = self._execute_task(task, task_results, poscar_text)
                    task_results[task_id] = task_result
                    completed_tasks.add(task_id)
                    logger.info(f"✅ STRANDS COORDINATOR: Task '{task_id}' completed")
        
        results.update(task_results)
        
        # Set execution mode based on plan
        if plan.get("sequence") == "parallel":
            results["execution_mode"] = "parallel_batch"
            results["performance"] = "optimized"
        else:
            results["execution_mode"] = "sequential"
        
        return results
    
    def _create_task_definitions(self, plan: dict, poscar_text: str, query: str) -> list:
        """Create task definitions with dependencies like aws_strands_coordinator"""
        formula = self._extract_formula(poscar_text)
        
        tasks = [
            {
                "agent": "structure_matcher",
                "action": "match_poscar_to_mp",
                "inputs": {"poscar_text": poscar_text, "formula": formula},
                "dependencies": []
            },
            {
                "agent": "dft_extractor",
                "action": "extract_parameters",
                "inputs": {"material_id": "${structure_matcher.material_id}"},
                "dependencies": ["structure_matcher"]
            },
            {
                "agent": "quantum_simulator",
                "action": "generate_simulation",
                "inputs": {
                    "poscar_text": poscar_text,
                    "material_data": "${structure_matcher.mp_data}",
                    "dft_parameters": "${dft_extractor.parameters}"
                },
                "dependencies": ["structure_matcher", "dft_extractor"]
            }
        ]
        
        # Filter tasks based on plan
        requested_agents = plan.get("agents", ["structure", "dft", "quantum"])
        agent_mapping = {
            "structure": "structure_matcher",
            "dft": "dft_extractor", 
            "quantum": "quantum_simulator"
        }
        
        filtered_tasks = []
        for task in tasks:
            for req_agent in requested_agents:
                if agent_mapping.get(req_agent) == task["agent"]:
                    filtered_tasks.append(task)
                    break
        
        return filtered_tasks
    
    def _execute_task(self, task: dict, context: dict, poscar_text: str) -> dict:
        """Execute individual task with context resolution"""
        agent_name = task["agent"]
        action = task["action"]
        inputs = task["inputs"]
        
        # Resolve variable references like ${structure_matcher.material_id}
        resolved_inputs = self._resolve_inputs(inputs, context)
        
        if agent_name == "structure_matcher":
            agent_instance = self.agents["structure_matcher"]["instance"]
            # Extract string from AgentResult if needed
            poscar_str = resolved_inputs["poscar_text"]
            if hasattr(poscar_str, 'text'):
                poscar_str = poscar_str.text
            elif not isinstance(poscar_str, str):
                poscar_str = str(poscar_str)
            
            result = agent_instance.match_poscar_to_mp(poscar_str, resolved_inputs["formula"])
            return {"structure_analysis": result}
            
        elif agent_name == "dft_extractor":
            agent_instance = self.agents["dft_extractor"]["instance"]
            material_id = resolved_inputs.get("material_id", "mp-149")
            mp_data = context.get("structure_matcher", {}).get("structure_analysis", {}).get("mp_data", {})
            result = agent_instance.extract_dft_parameters(material_id, mp_data)
            return {"dft_parameters": result}
            
        elif agent_name == "quantum_simulator":
            material_id = resolved_inputs.get("material_id", "mp-149")
            mp_data = resolved_inputs.get("material_data", {})
            dft_params = resolved_inputs.get("dft_parameters", {})
            result = self._generate_quantum_code(material_id, mp_data, dft_params)
            return {"quantum_simulation": result}
        
        return {"status": "completed"}
    
    def _resolve_inputs(self, inputs: dict, context: dict) -> dict:
        """Resolve variable references in inputs"""
        resolved = {}
        for key, value in inputs.items():
            if isinstance(value, str) and value.startswith("${"):
                # Parse ${agent.field} references
                ref = value[2:-1]  # Remove ${ and }
                parts = ref.split(".")
                if len(parts) == 2:
                    agent_name, field = parts
                    resolved[key] = context.get(agent_name, {}).get(field, value)
                else:
                    resolved[key] = value
            else:
                resolved[key] = value
        return resolved
    
    def _generate_quantum_code(self, material_id: str, mp_data: dict, dft_params: dict) -> dict:
        """Generate quantum simulation code using coordinator"""
        
        prompt = f"""
        Generate quantum simulation code for material {material_id}.
        
        Materials data: {json.dumps(mp_data, indent=2)}
        DFT parameters: {json.dumps(dft_params, indent=2)}
        
        Generate complete Qiskit VQE code with:
        - Realistic Hamiltonian using DFT parameters
        - Appropriate ansatz selection
        - Parameter optimization
        - Measurement and expectation values
        
        Focus on physical accuracy and computational efficiency.
        """
        
        try:
            response = self.coordinator(prompt)
            
            # Extract text from AgentResult if needed
            code_text = response
            if hasattr(response, 'text'):
                code_text = response.text
            elif hasattr(response, 'message') and hasattr(response.message, 'content'):
                # Handle nested AgentResult structure
                content = response.message.content
                if isinstance(content, list) and len(content) > 0:
                    code_text = content[0].get('text', str(response))
                else:
                    code_text = str(content)
            elif not isinstance(response, str):
                code_text = str(response)
            
            return {
                "status": "success",
                "code": code_text,
                "parameters_used": dft_params,
                "material_id": material_id
            }
            
        except Exception as e:
            logger.error(f"💥 STRANDS COORDINATOR: Quantum code generation failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def _extract_formula(self, poscar_text: str) -> str:
        """Extract chemical formula from POSCAR"""
        try:
            lines = poscar_text.strip().split('\n')
            for i, line in enumerate(lines[:10]):
                if re.match(r'^[A-Z][a-z]?(?:\s+[A-Z][a-z]?)*$', line.strip()):
                    return line.strip().split()[0]
            return "Si"
        except:
            return "Si"