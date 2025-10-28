"""
Enhanced MCP Materials Project client for Streamlit
"""
import subprocess
import json
import os
import logging
from typing import Dict, Any, Optional, List
import re

logger = logging.getLogger(__name__)

class EnhancedMCPClient:
    """Enhanced MCP client for Materials Project server with advanced features"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.server_process = None
        
    def start_server(self) -> bool:
        """Start the enhanced MCP server"""
        try:
            env = os.environ.copy()
            env['MP_API_KEY'] = self.api_key
            
            logger.info("🚀 MCP SERVER: Starting enhanced MCP Materials Project server...")
            # Find uv executable dynamically
            import shutil
            uv_path = shutil.which("uv") or "uv"
            
            self.server_process = subprocess.Popen([
                uv_path,
                "run", 
                "enhanced-mcp-materials"
            ],
            cwd="enhanced_mcp_materials",
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
            )
            
            # Initialize MCP session
            if self._initialize_mcp_session():
                logger.info("✅ MCP SERVER: Enhanced MCP server started successfully")
                return True
            else:
                logger.error("💥 MCP SERVER: Failed to initialize MCP session")
                return False
            
        except Exception as e:
            logger.error(f"💥 MCP SERVER: Failed to start enhanced MCP server: {e}")
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
                        "name": "enhanced-mcp-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            logger.info("🤝 MCP: Initializing session...")
            request_str = json.dumps(init_request) + "\n"
            self.server_process.stdin.write(request_str)
            self.server_process.stdin.flush()
            
            # Read initialization response
            response_str = self.server_process.stdout.readline()
            if response_str:
                response = json.loads(response_str)
                if "result" in response:
                    logger.info("✅ MCP: Session initialized successfully")
                    return True
                else:
                    logger.error(f"🚫 MCP: Initialization failed: {response}")
                    return False
            else:
                logger.error("🚫 MCP: No initialization response")
                return False
                
        except Exception as e:
            logger.error(f"💥 MCP: Initialization error: {e}")
            return False
    
    def stop_server(self):
        """Stop the MCP server"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process = None
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Call a tool on the MCP server"""
        if not self.server_process:
            logger.error("🚫 MCP: No server process available")
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
            
            logger.info(f"📤 MCP: Sending request to tool '{tool_name}' with args: {arguments}")
            request_str = json.dumps(request) + "\n"
            self.server_process.stdin.write(request_str)
            self.server_process.stdin.flush()
            
            # Read response with timeout
            import select
            import sys
            
            # Check if data is available to read (with timeout)
            if sys.platform == 'win32':
                # Windows doesn't support select on pipes, so just try to read
                try:
                    response_str = self.server_process.stdout.readline()
                except Exception as read_error:
                    logger.error(f"📥 MCP: Failed to read response: {read_error}")
                    return None
            else:
                # Unix-like systems can use select
                ready, _, _ = select.select([self.server_process.stdout], [], [], 5.0)  # 5 second timeout
                if not ready:
                    logger.error("📥 MCP: Timeout waiting for server response")
                    return None
                response_str = self.server_process.stdout.readline()
            
            if response_str:
                logger.info(f"📥 MCP: Received response: {response_str.strip()[:200]}...")
                try:
                    response = json.loads(response_str)
                    if "error" in response:
                        logger.error(f"🚫 MCP: Server returned error: {response['error']}")
                        return None
                    # Handle different response formats
                    if "result" in response:
                        result = response["result"]
                        # Check if it's the expected format
                        if isinstance(result, dict) and "content" in result:
                            content = result["content"]
                        elif isinstance(result, list):
                            content = result
                        else:
                            content = [result] if result else []
                        
                        logger.info(f"✅ MCP: Tool call successful, got {len(content) if isinstance(content, list) else 1} items")
                        return content
                    else:
                        logger.warning("⚠️ MCP: No result in response")
                        return []
                except json.JSONDecodeError as json_error:
                    logger.error(f"📥 MCP: Invalid JSON response: {json_error}")
                    return None
            else:
                logger.error("📥 MCP: Empty response from server")
                return None
            
        except Exception as e:
            logger.error(f"💥 MCP: Tool call failed: {e}")
            # Check if server process is still alive
            if self.server_process and self.server_process.poll() is not None:
                logger.error(f"💀 MCP: Server process died with return code: {self.server_process.returncode}")
            return None
    
    def search_materials(self, formula: str) -> List[str]:
        """Search materials by formula"""
        import streamlit as st
        logger.info(f"🔍 MCP: Searching materials for formula: {formula}")
        st.write(f"🔍 **MCP Tool 1**: Searching materials for formula: {formula}")
        
        result = self.call_tool("search_materials_by_formula", {
            "chemical_formula": formula
        })
        
        if result:
            # Handle both string and TextContent responses
            materials = []
            for item in result:
                if isinstance(item, str):
                    text = item
                elif isinstance(item, dict) and "text" in item:
                    text = item["text"]
                else:
                    text = str(item)
                
                # Check for error messages
                if "Error searching materials" in text or "invalid fields requested" in text:
                    st.error(f"❌ **MCP Server Error**: {text[:300]}...")
                    logger.error(f"💥 MCP: Server error - {text[:200]}...")
                    return []
                
                materials.append(text)
            
            st.write(f"✅ **Found {len(materials)} materials for {formula}**")
            st.write(f"📋 First result preview: {materials[0][:200]}..." if materials else "No results")
            logger.info(f"✅ MCP: Found {len(materials)} materials for {formula}")
            return materials
        st.write(f"❌ No materials found for {formula}")
        logger.warning(f"❌ MCP: No materials found for {formula}")
        return []
    
    def get_material_by_id(self, material_id: str, search_results: List[str] = None) -> Optional[Dict[str, Any]]:
        """Get material by ID with structured data for base model"""
        import streamlit as st
        logger.info(f"🔍 MCP: Getting material data for ID: {material_id}")
        st.write(f"🔍 **MCP Tool 2**: Getting material data for ID: {material_id}")
        
        result = self.call_tool("select_material_by_id", {
            "material_id": material_id
        })
        
        if result and len(result) >= 2:
            description = result[0].get("text", "")
            structure_uri = result[1].get("text", "").replace("structure uri: ", "")
            st.write(f"📋 Raw MCP response: {len(result)} items received")
            st.write(f"🔗 Structure URI: {structure_uri}")
            
            # Parse description to extract structured data
            data = self._parse_material_description(description, material_id, structure_uri, search_results)
            st.write(f"📊 Parsed structured data: {list(data.keys())}")
            
            # Get POSCAR geometry if available
            poscar_data = self.get_structure_data(structure_uri, "poscar")
            if poscar_data:
                data["geometry"] = self._poscar_to_geometry(poscar_data)
                st.write(f"🧬 Geometry extracted: {len(data['geometry'])} chars")
            
            st.write(f"✅ **Final structured data for LLM**: {data}")
            logger.info(f"✅ MCP: Retrieved structured material data for {material_id}")
            return data
        st.write(f"❌ Material {material_id} not found")
        logger.warning(f"❌ MCP: Material {material_id} not found")
        return None
    
    def _parse_material_description(self, description: str, material_id: str, structure_uri: str, search_results: List[str] = None) -> Dict[str, Any]:
        """Parse material description into structured data"""
        import streamlit as st
        
        # Log the raw description for debugging
        st.write(f"🔍 **Raw MCP Description**: {description[:500]}...")
        logger.info(f"🔍 MCP: Raw description for {material_id}: {description[:200]}...")
        
        data = {
            "material_id": material_id,
            "structure_uri": structure_uri,
            "source": "MCP Materials Project Server"
        }
        
        # First try to get data from search results (more complete)
        search_data = None
        if search_results:
            for result in search_results:
                if material_id in result:
                    search_data = result
                    st.write(f"🔍 **Found in search results**: {search_data[:200]}...")
                    break
        
        # Extract formula (try search results first, then description)
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
            st.write(f"✅ **Formula extracted**: {data['formula']}")
        else:
            st.write("❌ **Formula not found**")
        
        # Extract band gap (try search results first)
        band_gap = None
        if search_data:
            bg_match = re.search(r"Band Gap: ([\d\.]+)", search_data)
            if bg_match:
                band_gap = float(bg_match.group(1))
        if band_gap is None:
            bg_match = re.search(r"Band Gap: ([\d\.]+)", description)
            if bg_match:
                band_gap = float(bg_match.group(1))
        
        if band_gap is not None:
            data["band_gap"] = band_gap
            st.write(f"✅ **Band Gap extracted**: {data['band_gap']} eV")
        else:
            data["band_gap"] = 0.0
            st.write(f"❌ **Band Gap not found**, using default: {data['band_gap']}")
        
        # Extract formation energy (try search results first)
        formation_energy = None
        if search_data:
            fe_match = re.search(r"Formation Energy: ([\-\d\.]+)", search_data)
            if fe_match:
                formation_energy = float(fe_match.group(1))
        if formation_energy is None:
            fe_match = re.search(r"Formation Energy: ([\-\d\.]+)", description)
            if fe_match:
                formation_energy = float(fe_match.group(1))
        
        if formation_energy is not None:
            data["formation_energy"] = formation_energy
            st.write(f"✅ **Formation Energy extracted**: {data['formation_energy']} eV/atom")
        else:
            data["formation_energy"] = -3.0
            st.write(f"❌ **Formation Energy not found**, using default: {data['formation_energy']}")
        
        # Extract crystal system (try search results first)
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
            st.write(f"✅ **Crystal System extracted**: {data['crystal_system']}")
            logger.info(f"✅ MCP: Crystal system found for {material_id}: {data['crystal_system']}")
        else:
            st.write("❌ **Crystal System not found in description or search results**")
            logger.warning(f"❌ MCP: No crystal system found for {material_id}")
            
            # Try alternative patterns
            alt_patterns = [
                r"Space Group: ([^\n]+)",
                r"Crystal Structure: ([^\n]+)",
                r"Symmetry: ([^\n]+)"
            ]
            for pattern in alt_patterns:
                alt_match = re.search(pattern, description) or (search_data and re.search(pattern, search_data))
                if alt_match:
                    data["space_group_info"] = alt_match.group(1).strip()
                    st.write(f"ℹ️ **Alternative info found**: {pattern.split(':')[0]} = {data['space_group_info']}")
                    break
        
        st.write(f"📊 **Final parsed data keys**: {list(data.keys())}")
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
                element_line = ["Si"]  # Default fallback
            
            # Extract coordinates and map to elements
            atoms = []
            coord_start = 8
            for i, line in enumerate(lines[coord_start:coord_start+4]):
                if line.strip():
                    coords = line.strip().split()
                    if len(coords) >= 3:
                        # Use appropriate element (cycle through if needed)
                        element = element_line[i % len(element_line)]
                        # Convert fractional to approximate Cartesian (toy conversion)
                        x, y, z = float(coords[0]) * 5.43, float(coords[1]) * 5.43, float(coords[2]) * 5.43
                        atoms.append(f"{element} {x:.3f} {y:.3f} {z:.3f}")
            
            return "; ".join(atoms) if atoms else "Si 0.0 0.0 0.0; Si 1.932 1.932 1.932"
        except Exception:
            return "Si 0.0 0.0 0.0; Si 1.932 1.932 1.932"
    
    # Additional MCP server tools
    def get_structure_data(self, structure_uri: str, format: str = "poscar") -> Optional[str]:
        """Get structure data in POSCAR/CIF format"""
        import streamlit as st
        st.write(f"🔍 **MCP Tool 3**: Getting {format.upper()} data for {structure_uri}")
        
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
            st.write(f"✅ **Retrieved {format.upper()} data**: {len(data)} characters")
            # Log first few lines for debugging
            lines = data.split('\n')[:5]
            logger.info(f"📋 MCP: First 5 lines of {format.upper()}: {lines}")
            return data
        st.write(f"❌ Failed to get {format.upper()} data")
        return None
    
    def create_structure_from_poscar(self, poscar_str: str) -> Optional[Dict[str, str]]:
        """Create structure from POSCAR string"""
        import streamlit as st
        st.write(f"🔍 **MCP Tool 4**: Creating structure from POSCAR ({len(poscar_str)} chars)")
        
        result = self.call_tool("create_structure_from_poscar", {
            "poscar_str": poscar_str
        })
        if result and len(result) >= 2:
            data = {
                "uri_info": result[0].get("text", "") if isinstance(result[0], dict) else str(result[0]),
                "description": result[1].get("text", "") if isinstance(result[1], dict) else str(result[1])
            }
            st.write(f"✅ **Structure created**: {data['uri_info']}")
            return data
        st.write("❌ Failed to create structure from POSCAR")
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
        import streamlit as st
        st.write(f"🔍 **MCP Tool 5**: Plotting structure {structure_uri}")
        
        result = self.call_tool("plot_structure", {
            "structure_uri": structure_uri,
            "duplication": duplication
        })
        if result:
            for item in result:
                if item.get("type") == "image":
                    image_data = item.get("data", "")
                    st.write(f"✅ **Structure plot generated**: {len(image_data)} chars base64")
                    return image_data
        st.write("❌ Failed to generate structure plot")
        return None
    
    def build_supercell(self, bulk_structure_uri: str, supercell_parameters: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Build supercell from bulk structure"""
        import streamlit as st
        st.write(f"🔍 **MCP Tool 6**: Building supercell from {bulk_structure_uri}")
        
        result = self.call_tool("build_supercell", {
            "bulk_structure_uri": bulk_structure_uri,
            "supercell_parameters": supercell_parameters
        })
        if result and len(result) >= 2:
            data = {
                "supercell_uri": result[0].get("text", "") if isinstance(result[0], dict) else str(result[0]),
                "description": result[1].get("text", "") if isinstance(result[1], dict) else str(result[1])
            }
            st.write(f"✅ **Supercell built**: {data['supercell_uri']}")
            return data
        st.write("❌ Failed to build supercell")
        return None
    
    def __del__(self):
        """Cleanup"""
        self.stop_server()


class EnhancedMCPAgent:
    """Enhanced MCP agent with full Materials Project server capabilities"""
    
    def __init__(self, api_key: str):
        self.client = EnhancedMCPClient(api_key)
        self.client.start_server()
    
    def search(self, query: str) -> Dict[str, Any]:
        """Search for materials - returns structured data for base model"""
        logger.info(f"🚀 MCP AGENT: Starting search for query: '{query}'")
        try:
            # Handle material ID queries
            if query.lower().startswith("mp-"):
                logger.info(f"📋 MCP AGENT: Detected material ID query: {query}")
                material_data = self.client.get_material_by_id(query)
                if material_data:
                    logger.info(f"✅ MCP AGENT: Successfully retrieved structured material {query}")
                    return material_data  # Already structured by get_material_by_id
                logger.warning(f"❌ MCP AGENT: Material {query} not found")
                return {"error": f"Material {query} not found"}
            
            # Special handling for common materials to find stable phases
            from utils.material_selector import get_known_stable_phase, select_best_material_match
            
            # Try to get known stable phase first
            stable_data = get_known_stable_phase(query, self.client)
            if stable_data:
                logger.info(f"✅ MCP AGENT: Found known stable phase for {query}")
                return stable_data
            
            # Check if user wants to see all options vs detailed analysis
            show_all_options = any(phrase in query.lower() for phrase in [
                "show me", "available options", "list", "all materials", "options", "available"
            ])
            
            # Handle formula queries
            logger.info(f"🧪 MCP AGENT: Detected formula query: {query}, show_all={show_all_options}")
            results = self.client.search_materials(query)
            if results:
                # Check if results contain errors
                first_result = results[0]
                if "Error searching materials" in first_result or "invalid fields" in first_result:
                    logger.error(f"💥 MCP AGENT: Server error in search results")
                    return {"error": "MCP server configuration error - invalid API fields"}
                
                if show_all_options:
                    # Return all materials for listing
                    result = {
                        "formula": query,
                        "results": results,
                        "count": len(results),
                        "source": "Enhanced MCP Server",
                        "show_all": True
                    }
                    logger.info(f"✅ MCP AGENT: Returning all {len(results)} materials for listing")
                    return result
                else:
                    # Use smart material selection instead of first result
                    best_material_id = select_best_material_match(results, query)
                    if best_material_id:
                        material_data = self.client.get_material_by_id(best_material_id, results)
                        if material_data:
                            material_data["search_results"] = results
                            material_data["search_count"] = len(results)
                            logger.info(f"✅ MCP AGENT: Found structured data for {query} via {best_material_id} (smart selection)")
                            return material_data
                
                # Fallback to basic result format
                result = {
                    "formula": query,
                    "results": results,
                    "count": len(results),
                    "source": "Enhanced MCP Server"
                }
                logger.info(f"✅ MCP AGENT: Found {len(results)} materials for formula {query}")
                return result
            
            logger.warning(f"❌ MCP AGENT: No materials found for query: {query}")
            return {"error": "No materials found"}
            
        except Exception as e:
            logger.error(f"💥 MCP AGENT: Search failed for '{query}': {e}")
            return {"error": str(e)}
    
    # All MCP server tools exposed through agent
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
    
    def moire_homobilayer(self, bulk_structure_uri: str, interlayer_spacing: float, max_num_atoms: int, twist_angle: float, vacuum_thickness: float) -> Optional[Dict[str, str]]:
        """Generate moire homobilayer structure"""
        import streamlit as st
        st.write(f"🔍 **MCP Tool 8**: Generating moire homobilayer for {bulk_structure_uri}")
        st.write(f"📊 **Parameters**: {twist_angle}° twist, {interlayer_spacing} Å spacing, max {max_num_atoms} atoms")
        
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
                # Extract URI from success message
                uri_match = re.search(r"structure://([a-f0-9]+)", text)
                moire_uri = uri_match.group(0) if uri_match else "structure://unknown"
                
                data = {
                    "moire_uri": moire_uri,
                    "description": text
                }
                st.write(f"✅ **Moire bilayer generated**: {data['moire_uri']}")
                return data
            else:
                st.write(f"❌ **Moire generation error**: {text}")
                return None
        st.write("❌ Failed to generate moire bilayer")
        return None