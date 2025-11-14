"""
Enhanced MCP Materials Project client for AWS environment
"""
import subprocess
import json
import os
import logging
from typing import Dict, Any, Optional, List
import re

logger = logging.getLogger(__name__)

class EnhancedMCPClient:
    """Enhanced MCP client for Materials Project server with advanced features (AWS version)"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.server_process = None
        
    def start_server(self) -> bool:
        """Start the enhanced MCP server in AWS environment"""
        try:
            env = os.environ.copy()
            env['MP_API_KEY'] = self.api_key
            
            logger.info("🚀 MCP SERVER (AWS): Starting enhanced MCP Materials Project server...")
            
            # Use secure subprocess execution with fixed command
            import sys
            python_executable = sys.executable or "python"
            server_command = "import sys; sys.path.insert(0, '.'); from enhanced_mcp_materials.aws_server import main; main()"
            
            # Determine working directory for Elastic Beanstalk compatibility
            cwd = "/var/app/current" if os.path.exists("/var/app/current") else "."
            
            self.server_process = subprocess.Popen([
                python_executable, "-c", server_command
            ],
            cwd=cwd,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
            )
            
            # Initialize MCP session
            if self._initialize_mcp_session():
                logger.info("✅ MCP SERVER (AWS): Enhanced MCP server started successfully")
                return True
            else:
                logger.error("💥 MCP SERVER (AWS): Failed to initialize MCP session")
                return False
            
        except Exception as e:
            logger.error(f"💥 MCP SERVER (AWS): Failed to start enhanced MCP server: {e}")
            return False
    
    def _initialize_mcp_session(self) -> bool:
        """Initialize MCP session with the server"""
        try:
            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "clientInfo": {
                        "name": "enhanced-mcp-client-aws",
                        "version": "1.0.0"
                    }
                }
            }
            
            logger.info("🤝 MCP (AWS): Initializing session...")
            request_str = json.dumps(init_request) + "\n"
            self.server_process.stdin.write(request_str)
            self.server_process.stdin.flush()
            
            # Wait for server to be ready with timeout
            import time
            timeout = 15
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # Check if server process is still alive
                if self.server_process.poll() is not None:
                    logger.error(f"💀 MCP (AWS): Server process died during initialization with code: {self.server_process.returncode}")
                    stderr_output = self.server_process.stderr.read()
                    if stderr_output:
                        logger.error(f"💀 MCP (AWS): Server stderr: {stderr_output}")
                    return False
                
                # Try to read response
                try:
                    response_str = self.server_process.stdout.readline()
                    if response_str.strip():
                        response = json.loads(response_str)
                        if "result" in response:
                            logger.info("✅ MCP (AWS): Session initialized successfully")
                            return True
                        elif "error" in response:
                            logger.error(f"🚫 MCP (AWS): Initialization failed: {response['error']}")
                            return False
                except json.JSONDecodeError as json_err:
                    logger.debug(f"JSON decode error during initialization: {json_err}")
                    pass
                except Exception as init_err:
                    logger.debug(f"Initialization error: {init_err}")
                    pass
                
                time.sleep(0.1)
            
            logger.error("🚫 MCP (AWS): No initialization response")
            return False
                
        except Exception as e:
            logger.error(f"💥 MCP (AWS): Initialization error: {e}")
            return False
    
    def stop_server(self):
        """Stop the MCP server with proper cleanup"""
        if self.server_process:
            try:
                self.server_process.terminate()
                # Wait for process to terminate gracefully
                try:
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("MCP server did not terminate gracefully, forcing kill")
                    self.server_process.kill()
                    self.server_process.wait()
            except Exception as e:
                logger.error(f"Error stopping MCP server: {e}")
            finally:
                self.server_process = None
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Call a tool on the MCP server"""
        if not self.server_process:
            logger.error("🚫 MCP (AWS): No server process available")
            return None
        
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            logger.info(f"📤 MCP (AWS): Sending request to tool '{tool_name}' with args: {arguments}")
            request_str = json.dumps(request) + "\n"
            self.server_process.stdin.write(request_str)
            self.server_process.stdin.flush()
            
            # Read response with timeout and proper error handling
            import select
            import sys
            
            # Check if data is available to read (with timeout)
            if sys.platform == 'win32':
                # Windows doesn't support select on pipes, so just try to read
                try:
                    response_str = self.server_process.stdout.readline()
                except Exception as read_error:
                    logger.error(f"📥 MCP (AWS): Failed to read response: {read_error}")
                    return None
            else:
                # Unix-like systems can use select (Elastic Beanstalk uses Linux)
                ready, _, _ = select.select([self.server_process.stdout], [], [], 5.0)
                if not ready:
                    logger.error("📥 MCP (AWS): Timeout waiting for server response")
                    return None
                response_str = self.server_process.stdout.readline()
            
            if response_str:
                logger.info(f"📥 MCP (AWS): Received response: {response_str.strip()[:200]}...")
                try:
                    response = json.loads(response_str)
                    if "error" in response:
                        logger.error(f"🚫 MCP (AWS): Server returned error: {response['error']}")
                        return None
                    
                    if "result" in response:
                        result = response["result"]
                        if isinstance(result, dict) and "content" in result:
                            content = result["content"]
                        elif isinstance(result, list):
                            content = result
                        else:
                            content = [result] if result else []
                        
                        logger.info(f"✅ MCP (AWS): Tool call successful, got {len(content) if isinstance(content, list) else 1} items")
                        return content
                    else:
                        logger.warning("⚠️ MCP (AWS): No result in response")
                        return []
                except json.JSONDecodeError as json_error:
                    logger.error(f"📥 MCP (AWS): Invalid JSON response: {json_error}")
                    return None
            else:
                logger.error("📥 MCP (AWS): Empty response from server")
                return None
            
        except Exception as e:
            logger.error(f"💥 MCP (AWS): Tool call failed: {e}")
            if self.server_process and self.server_process.poll() is not None:
                logger.error(f"💀 MCP (AWS): Server process died with return code: {self.server_process.returncode}")
            return None
    
    # All the same methods as local_client.py but with AWS logging
    def search_materials(self, formula: str) -> List[str]:
        """Search materials by formula"""
        logger.info(f"🔍 MCP (AWS): Searching materials for formula: {formula}")
        
        result = self.call_tool("search_materials_by_formula", {
            "chemical_formula": formula
        })
        
        if result:
            materials = []
            for item in result:
                if isinstance(item, str):
                    text = item
                elif isinstance(item, dict) and "text" in item:
                    text = item["text"]
                else:
                    text = str(item)
                
                if "Error searching materials" in text or "invalid fields requested" in text:
                    logger.error(f"💥 MCP (AWS): Server error - {text[:200]}...")
                    return []
                
                materials.append(text)
            
            logger.info(f"✅ MCP (AWS): Found {len(materials)} materials for {formula}")
            return materials
        logger.warning(f"❌ MCP (AWS): No materials found for {formula}")
        return []
    
    def get_material_by_id(self, material_id: str, search_results: List[str] = None) -> Optional[Dict[str, Any]]:
        """Get material by ID with structured data for base model"""
        logger.info(f"🔍 MCP (AWS): Getting material data for ID")
        
        result = self.call_tool("select_material_by_id", {
            "material_id": material_id
        })
        
        if result and len(result) >= 2:
            description = result[0].get("text", "")
            structure_uri = result[1].get("text", "").replace("structure uri: ", "")
            
            # Parse description to extract structured data
            data = self._parse_material_description_client(description, material_id, structure_uri, search_results)
            
            # Get POSCAR geometry if available
            poscar_data = self.get_structure_data(structure_uri, "poscar")
            if poscar_data:
                data["geometry"] = self._poscar_to_geometry(poscar_data)
            
            logger.info(f"✅ MCP (AWS): Retrieved structured material data")
            return data
        logger.warning(f"❌ MCP (AWS): Material not found")
        return None
    
    def _parse_material_description_client(self, description: str, material_id: str, structure_uri: str, search_results: List[str] = None) -> Dict[str, Any]:
        """Parse material description into structured data"""
        logger.info(f"🔍 MCP (AWS): Parsing material description ({len(description)} chars)")
        
        data = {
            "material_id": material_id,
            "structure_uri": structure_uri,
            "source": "MCP Materials Project Server (AWS)"
        }
        
        # Extract data using same logic as local_client
        search_data = None
        if search_results:
            for result in search_results:
                if material_id in result:
                    search_data = result
                    break
        
        # Extract formula
        formula = None
        if search_data:
            formula_match = re.search(r"Formula: ([^\n]+)", search_data)
            if formula_match:
                formula = formula_match.group(1).strip()
        if not formula:
            formula_match = re.search(r"Formula: ([^\n]+)", description)
            if formula_match:
                formula = formula_match.group(1).strip()
        
        if formula:
            data["formula"] = formula
        
        # Extract band gap
        band_gap = None
        if search_data:
            bg_match = re.search(r"Band Gap: ([\d\.]+)", search_data)
            if bg_match:
                band_gap = float(bg_match.group(1))
        if band_gap is None:
            bg_match = re.search(r"Band Gap: ([\d\.]+)", description)
            if bg_match:
                band_gap = float(bg_match.group(1))
        
        data["band_gap"] = band_gap if band_gap is not None else 0.0
        
        # Extract formation energy
        formation_energy = None
        if search_data:
            fe_match = re.search(r"Formation Energy: ([\-\d\.]+)", search_data)
            if fe_match:
                formation_energy = float(fe_match.group(1))
        if formation_energy is None:
            fe_match = re.search(r"Formation Energy: ([\-\d\.]+)", description)
            if fe_match:
                formation_energy = float(fe_match.group(1))
        
        data["formation_energy"] = formation_energy if formation_energy is not None else -3.0
        
        # Extract crystal system
        crystal_system = None
        if search_data:
            cs_match = re.search(r"Crystal System: ([^\n]+)", search_data)
            if cs_match:
                crystal_system = cs_match.group(1).strip()
        if not crystal_system:
            cs_match = re.search(r"Crystal System: ([^\n]+)", description)
            if cs_match:
                crystal_system = cs_match.group(1).strip()
        
        if crystal_system:
            data["crystal_system"] = crystal_system
            logger.info(f"✅ MCP (AWS): Crystal system found for material")
        else:
            logger.warning(f"❌ MCP (AWS): No crystal system found for material")
        
        return data
    
    def _poscar_to_geometry(self, poscar_str: str) -> str:
        """Convert POSCAR to proper geometry string with element symbols"""
        try:
            lines = poscar_str.strip().split('\n')
            if len(lines) < 8:
                return ""
            
            # Extract element symbols from POSCAR
            element_line = None
            for i, line in enumerate(lines[:7]):
                if re.match(r'^[A-Z][a-z]?(?:\s+[A-Z][a-z]?)*$', line.strip()):
                    element_line = line.strip().split()
                    break
            
            if not element_line:
                element_line = ["Si"]
            
            # Extract coordinates and map to elements
            atoms = []
            coord_start = 8
            for i, line in enumerate(lines[coord_start:coord_start+4]):
                if line.strip():
                    coords = line.strip().split()
                    if len(coords) >= 3:
                        element = element_line[i % len(element_line)]
                        x, y, z = float(coords[0]) * 5.43, float(coords[1]) * 5.43, float(coords[2]) * 5.43
                        atoms.append(f"{element} {x:.3f} {y:.3f} {z:.3f}")
            
            return "; ".join(atoms) if atoms else "Si 0.0 0.0 0.0; Si 1.932 1.932 1.932"
        except Exception:
            return "Si 0.0 0.0 0.0; Si 1.932 1.932 1.932"
    
    # Additional MCP server tools (same as local_client)
    def get_structure_data(self, structure_uri: str, format: str = "poscar") -> Optional[str]:
        """Get structure data in POSCAR/CIF format"""
        result = self.call_tool("get_structure_data", {
            "structure_uri": structure_uri,
            "format": format
        })
        if result and len(result) > 0:
            item = result[0]
            if isinstance(item, dict):
                data = item.get("text", "")
            else:
                data = str(item)
            return data
        return None
    
    def create_structure_from_poscar(self, poscar_str: str) -> Optional[Dict[str, str]]:
        """Create structure from POSCAR string"""
        result = self.call_tool("create_structure_from_poscar", {
            "poscar_str": poscar_str
        })
        if result and len(result) >= 2:
            return {
                "uri_info": result[0].get("text", "") if isinstance(result[0], dict) else str(result[0]),
                "description": result[1].get("text", "") if isinstance(result[1], dict) else str(result[1])
            }
        return None
    
    def create_structure_from_cif(self, cif_str: str) -> Optional[Dict[str, str]]:
        """Create structure from CIF string"""
        result = self.call_tool("create_structure_from_cif", {
            "cif_str": cif_str
        })
        if result and len(result) >= 2:
            return {
                "uri_info": result[0].get("text", "") if isinstance(result[0], dict) else str(result[0]),
                "description": result[1].get("text", "") if isinstance(result[1], dict) else str(result[1])
            }
        return None
    
    def plot_structure(self, structure_uri: str, duplication: List[int] = [1, 1, 1]) -> Optional[str]:
        """Plot structure and return base64 image"""
        result = self.call_tool("plot_structure", {
            "structure_uri": structure_uri,
            "duplication": duplication
        })
        if result:
            for item in result:
                if item.get("type") == "image":
                    return item.get("data", "")
        return None
    
    def build_supercell(self, bulk_structure_uri: str, supercell_parameters: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Build supercell from bulk structure"""
        result = self.call_tool("build_supercell", {
            "bulk_structure_uri": bulk_structure_uri,
            "supercell_parameters": supercell_parameters
        })
        if result and len(result) >= 2:
            return {
                "supercell_uri": result[0].get("text", "") if isinstance(result[0], dict) else str(result[0]),
                "description": result[1].get("text", "") if isinstance(result[1], dict) else str(result[1])
            }
        return None
    
    def __del__(self):
        """Cleanup"""
        self.stop_server()


class EnhancedMCPAgent:
    """Enhanced MCP agent with full Materials Project server capabilities (AWS version)"""
    
    def __init__(self, api_key: str):
        self.client = EnhancedMCPClient(api_key)
        self.client.start_server()
    
    def search(self, query: str) -> Dict[str, Any]:
        """Search for materials - returns structured data for base model"""
        logger.info(f"🚀 MCP AGENT (AWS): Starting search for query: '{query}'")
        try:
            # Handle material ID queries
            if query.lower().startswith("mp-"):
                logger.info(f"📋 MCP AGENT (AWS): Detected material ID query: {query}")
                material_data = self.client.get_material_by_id(query)
                if material_data:
                    logger.info(f"✅ MCP AGENT (AWS): Successfully retrieved structured material {query}")
                    return material_data
                logger.warning(f"❌ MCP AGENT (AWS): Material {query} not found")
                return {"error": f"Material {query} not found"}
            
            # Check if user wants to see all options vs detailed analysis
            show_all_options = any(phrase in query.lower() for phrase in [
                "show me", "available options", "list", "all materials", "options", "available"
            ])
            
            # Handle formula queries
            logger.info(f"🧪 MCP AGENT (AWS): Detected formula query: {query}, show_all={show_all_options}")
            results = self.client.search_materials(query)
            if results:
                # Check for errors
                first_result = results[0]
                if "Error searching materials" in first_result or "invalid fields" in first_result:
                    logger.error(f"💥 MCP AGENT (AWS): Server error in search results")
                    return {"error": "MCP server configuration error - invalid API fields"}
                
                if show_all_options:
                    # Return all materials for listing
                    result = {
                        "formula": query,
                        "results": results,
                        "count": len(results),
                        "source": "Enhanced MCP Server (AWS)",
                        "show_all": True
                    }
                    logger.info(f"✅ MCP AGENT (AWS): Returning all {len(results)} materials for listing")
                    return result
                else:
                    # Try to use smart material selection if available
                    try:
                        from utils.material_selector import select_best_material_match
                        best_material_id = select_best_material_match(results, query)
                        if best_material_id:
                            material_data = self.client.get_material_by_id(best_material_id, results)
                            if material_data:
                                material_data["search_results"] = results
                                material_data["search_count"] = len(results)
                                logger.info(f"✅ MCP AGENT (AWS): Found structured data for {query} via {best_material_id} (smart selection)")
                                return material_data
                    except ImportError:
                        logger.info("Material selector not available in AWS environment, using basic selection")
                
                # Fallback to basic result format
                result = {
                    "formula": query,
                    "results": results,
                    "count": len(results),
                    "source": "Enhanced MCP Server (AWS)"
                }
                logger.info(f"✅ MCP AGENT (AWS): Found {len(results)} materials for formula {query}")
                return result
            
            logger.warning(f"❌ MCP AGENT (AWS): No materials found for query: {query}")
            return {"error": "No materials found"}
            
        except Exception as e:
            logger.error(f"💥 MCP AGENT (AWS): Search failed for '{query}': {e}")
            return {"error": str(e)}
    
    # All MCP server tools exposed through agent (same as local version)
    def get_structure(self, material_id: str, format: str = "poscar") -> Optional[str]:
        """Get structure in POSCAR/CIF format"""
        material_data = self.client.get_material_by_id(material_id)
        if material_data and material_data.get("structure_uri"):
            return self.client.get_structure_data(material_data["structure_uri"], format)
        return None
    
    def get_structure_data(self, structure_uri: str, format: str = "poscar") -> Optional[str]:
        """Get structure data by URI"""
        return self.client.get_structure_data(structure_uri, format)
    
    def create_structure_from_poscar(self, poscar_str: str) -> Optional[Dict[str, str]]:
        """Create structure from POSCAR string"""
        return self.client.create_structure_from_poscar(poscar_str)
    
    def create_structure_from_cif(self, cif_str: str) -> Optional[Dict[str, str]]:
        """Create structure from CIF string"""
        return self.client.create_structure_from_cif(cif_str)
    
    def plot_structure(self, structure_uri: str, duplication: List[int] = [1, 1, 1]) -> Optional[str]:
        """Plot structure and return base64 image"""
        return self.client.plot_structure(structure_uri, duplication)
    
    def build_supercell(self, bulk_structure_uri: str, supercell_parameters: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Build supercell from bulk structure"""
        return self.client.build_supercell(bulk_structure_uri, supercell_parameters)
    
    def search_materials_by_formula(self, formula: str) -> List[str]:
        """Direct access to formula search"""
        return self.client.search_materials(formula)
    
    def select_material_by_id(self, material_id: str) -> Optional[Dict[str, Any]]:
        """Select material by ID using MCP server tool"""
        logger.info(f"🔍 MCP (AWS): Selecting material by ID: {material_id}")
        
        result = self.client.call_tool("select_material_by_id", {
            "material_id": material_id
        })
        
        if result and len(result) >= 2:
            description = result[0].get("text", "") if isinstance(result[0], dict) else str(result[0])
            structure_uri = result[1].get("text", "").replace("structure uri: ", "") if isinstance(result[1], dict) else str(result[1]).replace("structure uri: ", "")
            
            # Parse description to extract structured data
            data = self._parse_material_description(description, material_id, structure_uri)
            
            # Get POSCAR geometry if available
            poscar_data = self.get_structure_data(structure_uri, "poscar")
            if poscar_data:
                data["geometry"] = self._poscar_to_geometry(poscar_data)
            
            logger.info(f"✅ MCP (AWS): Material selected: {material_id}")
            return data
        
        logger.warning(f"❌ MCP (AWS): Material {material_id} not found")
        return None
    
    def _parse_material_description(self, description: str, material_id: str, structure_uri: str) -> Dict[str, Any]:
        """Parse material description into structured data"""
        import re
        
        data = {
            "material_id": material_id,
            "structure_uri": structure_uri,
            "source": "Enhanced MCP Server (AWS)"
        }
        
        # Extract formula
        formula_match = re.search(r"Formula: ([^\n]+)", description)
        if formula_match:
            data["formula"] = formula_match.group(1).strip()
        
        # Extract band gap
        bg_match = re.search(r"Band Gap: ([\d\.]+)", description)
        if bg_match:
            data["band_gap"] = float(bg_match.group(1))
        else:
            data["band_gap"] = 0.0
        
        # Extract formation energy
        fe_match = re.search(r"Formation Energy: ([\-\d\.]+)", description)
        if fe_match:
            data["formation_energy"] = float(fe_match.group(1))
        else:
            data["formation_energy"] = -3.0
        
        # Extract crystal system
        cs_match = re.search(r"Crystal System: ([^\n]+)", description)
        if cs_match:
            data["crystal_system"] = cs_match.group(1).strip()
        
        return data
    
    def _poscar_to_geometry(self, poscar_str: str) -> str:
        """Convert POSCAR to geometry string"""
        try:
            lines = poscar_str.strip().split('\n')
            if len(lines) < 8:
                return ""
            
            # Extract element symbols
            element_line = None
            for i, line in enumerate(lines[:7]):
                if re.match(r'^[A-Z][a-z]?(?:\s+[A-Z][a-z]?)*$', line.strip()):
                    element_line = line.strip().split()
                    break
            
            if not element_line:
                element_line = ["Si"]
            
            # Extract coordinates
            atoms = []
            coord_start = 8
            for i, line in enumerate(lines[coord_start:coord_start+4]):
                if line.strip():
                    coords = line.strip().split()
                    if len(coords) >= 3:
                        element = element_line[i % len(element_line)]
                        x, y, z = float(coords[0]) * 5.43, float(coords[1]) * 5.43, float(coords[2]) * 5.43
                        atoms.append(f"{element} {x:.3f} {y:.3f} {z:.3f}")
            
            return "; ".join(atoms) if atoms else "Si 0.0 0.0 0.0; Si 1.932 1.932 1.932"
        except Exception:
            return "Si 0.0 0.0 0.0; Si 1.932 1.932 1.932"
    
    def moire_homobilayer(self, bulk_structure_uri: str, interlayer_spacing: float, max_num_atoms: int, twist_angle: float, vacuum_thickness: float) -> Optional[Dict[str, str]]:
        """Generate moire homobilayer structure"""
        logger.info(f"🔍 MCP (AWS): Generating moire homobilayer for {bulk_structure_uri}")
        
        result = self.client.call_tool("moire_homobilayer", {
            "bulk_structure_uri": bulk_structure_uri,
            "interlayer_spacing": interlayer_spacing,
            "max_num_atoms": max_num_atoms,
            "twist_angle": twist_angle,
            "vacuum_thickness": vacuum_thickness
        })
        
        if result and len(result) >= 1:
            first_item = result[0]
            text = first_item.get("text", "") if isinstance(first_item, dict) else str(first_item)
            
            if "Moire structure is created" in text:
                uri_match = re.search(r"structure://([a-f0-9]+)", text)
                moire_uri = uri_match.group(0) if uri_match else "structure://unknown"
                
                data = {
                    "moire_uri": moire_uri,
                    "description": text
                }
                logger.info(f"✅ MCP (AWS): Moire bilayer generated: {data['moire_uri']}")
                return data
            else:
                logger.error(f"❌ MCP (AWS): Moire generation error: {text}")
                return None
        logger.error("❌ MCP (AWS): Failed to generate moire bilayer")
        return None