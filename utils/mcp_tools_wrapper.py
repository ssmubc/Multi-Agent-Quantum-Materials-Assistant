# MCP Tools Wrapper for Strands Integration
# This module provides a simplified interface for Strands agents to call MCP tools

import logging
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MCPToolsWrapper:
    """Wrapper to make MCP tools easily accessible to Strands agents"""
    
    def __init__(self, mp_agent):
        self.mp_agent = mp_agent
        logger.info("🔧 MCP Tools Wrapper initialized")
    
    def search_material(self, formula: str) -> Dict[str, Any]:
        """Search for materials by formula using MCP"""
        try:
            logger.info(f"🔍 MCP WRAPPER: Searching for {formula}")
            # Call the MCP agent's search method which handles the MCP server call
            result = self.mp_agent.search(formula)
            
            if result and not result.get('error'):
                logger.info(f"✅ MCP WRAPPER: Found materials for {formula}")
                return {
                    "status": "success",
                    "data": result,
                    "mcp_action": "search_materials_by_formula"
                }
            else:
                logger.warning(f"⚠️ MCP WRAPPER: No materials found for {formula}")
                return {
                    "status": "not_found",
                    "message": f"No materials found for {formula}",
                    "mcp_action": "search_materials_by_formula"
                }
        except Exception as e:
            logger.error(f"💥 MCP WRAPPER: Search failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "mcp_action": "search_materials_by_formula"
            }
    
    def get_material_details(self, material_id: str) -> Dict[str, Any]:
        """Get detailed material data by ID using MCP"""
        try:
            logger.info(f"📋 MCP WRAPPER: Getting details for {material_id}")
            # Use the MCP agent's select_material_by_id method
            result = self.mp_agent.select_material_by_id(material_id)
            
            if result and not result.get('error'):
                logger.info(f"✅ MCP WRAPPER: Got details for {material_id}")
                return {
                    "status": "success",
                    "data": result,
                    "mcp_action": "select_material_by_id"
                }
            else:
                logger.warning(f"⚠️ MCP WRAPPER: Material {material_id} not found")
                return {
                    "status": "not_found",
                    "message": f"Material {material_id} not found",
                    "mcp_action": "select_material_by_id"
                }
        except Exception as e:
            logger.error(f"💥 MCP WRAPPER: Material details failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "mcp_action": "select_material_by_id"
            }
    
    def create_visualization(self, material_id: str) -> Dict[str, Any]:
        """Create structure visualization using MCP"""
        try:
            logger.info(f"📊 MCP WRAPPER: Creating visualization for {material_id}")
            
            # Ensure material is loaded first
            select_result = self.mp_agent.select_material_by_id(material_id)
            if not select_result or select_result.get('error'):
                return {
                    "status": "not_found",
                    "message": f"Material {material_id} not found",
                    "mcp_action": "plot_structure"
                }
            
            structure_uri = f"structure://mp_{material_id}"
            result = self.mp_agent.plot_structure(structure_uri, [1, 1, 1])
            
            logger.info(f"✅ MCP WRAPPER: Created visualization for {material_id}")
            return {
                "status": "success",
                "data": result,
                "mcp_action": "plot_structure"
            }
        except Exception as e:
            logger.error(f"💥 MCP WRAPPER: Visualization failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "mcp_action": "plot_structure"
            }
    
    def create_supercell(self, material_id: str, scaling_matrix: Optional[list] = None) -> Dict[str, Any]:
        """Create supercell using MCP"""
        try:
            logger.info(f"🏗️ MCP WRAPPER: Creating supercell for {material_id}")
            
            # Ensure material is loaded first
            select_result = self.mp_agent.select_material_by_id(material_id)
            if not select_result or select_result.get('error'):
                return {
                    "status": "not_found",
                    "message": f"Material {material_id} not found",
                    "mcp_action": "build_supercell"
                }
            
            structure_uri = f"structure://mp_{material_id}"
            
            if not scaling_matrix:
                scaling_matrix = [[2,0,0],[0,2,0],[0,0,2]]
            
            result = self.mp_agent.build_supercell(structure_uri, {"scaling_matrix": scaling_matrix})
            
            logger.info(f"✅ MCP WRAPPER: Created supercell for {material_id}")
            return {
                "status": "success",
                "data": result,
                "mcp_action": "build_supercell"
            }
        except Exception as e:
            logger.error(f"💥 MCP WRAPPER: Supercell creation failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "mcp_action": "build_supercell"
            }
    
    def create_moire_bilayer(self, material_id: str, twist_angle: float = 1.1, interlayer_spacing: float = 3.4) -> Dict[str, Any]:
        """Create moire bilayer using MCP"""
        try:
            logger.info(f"🌀 MCP WRAPPER: Creating moire bilayer for {material_id}")
            
            # Ensure material is loaded first
            select_result = self.mp_agent.select_material_by_id(material_id)
            if not select_result or select_result.get('error'):
                return {
                    "status": "not_found",
                    "message": f"Material {material_id} not found",
                    "mcp_action": "moire_homobilayer"
                }
            
            structure_uri = f"structure://mp_{material_id}"
            
            result = self.mp_agent.moire_homobilayer(structure_uri, interlayer_spacing, 10, twist_angle, 15.0)
            
            logger.info(f"✅ MCP WRAPPER: Created moire bilayer for {material_id}")
            return {
                "status": "success",
                "data": result,
                "mcp_action": "moire_homobilayer",
                "parameters": {
                    "twist_angle": twist_angle,
                    "interlayer_spacing": interlayer_spacing
                }
            }
        except Exception as e:
            logger.error(f"💥 MCP WRAPPER: Moire bilayer creation failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "mcp_action": "moire_homobilayer"
            }
    
    def get_structure_data(self, structure_uri: str, format: str = "poscar") -> Dict[str, Any]:
        """Get structure data in POSCAR/CIF format using MCP"""
        try:
            logger.info(f"📋 MCP WRAPPER: Getting {format} data for {structure_uri}")
            result = self.mp_agent.get_structure_data(structure_uri, format)
            
            if result:
                logger.info(f"✅ MCP WRAPPER: Got {format} data ({len(result)} chars)")
                return {
                    "status": "success",
                    "data": result,
                    "mcp_action": "get_structure_data",
                    "format": format
                }
            else:
                logger.warning(f"⚠️ MCP WRAPPER: No {format} data for {structure_uri}")
                return {
                    "status": "not_found",
                    "message": f"No {format} data available",
                    "mcp_action": "get_structure_data"
                }
        except Exception as e:
            logger.error(f"💥 MCP WRAPPER: Structure data failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "mcp_action": "get_structure_data"
            }
    
    def create_structure_from_poscar(self, poscar_str: str) -> Dict[str, Any]:
        """Create structure from POSCAR string using MCP"""
        try:
            logger.info(f"🏗️ MCP WRAPPER: Creating structure from POSCAR ({len(poscar_str)} chars)")
            result = self.mp_agent.create_structure_from_poscar(poscar_str)
            
            if result:
                logger.info(f"✅ MCP WRAPPER: Created structure from POSCAR")
                return {
                    "status": "success",
                    "data": result,
                    "mcp_action": "create_structure_from_poscar"
                }
            else:
                logger.warning(f"⚠️ MCP WRAPPER: Failed to create structure from POSCAR")
                return {
                    "status": "failed",
                    "message": "Could not create structure from POSCAR",
                    "mcp_action": "create_structure_from_poscar"
                }
        except Exception as e:
            logger.error(f"💥 MCP WRAPPER: POSCAR structure creation failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "mcp_action": "create_structure_from_poscar"
            }
    
    def create_structure_from_cif(self, cif_str: str) -> Dict[str, Any]:
        """Create structure from CIF string using MCP"""
        try:
            logger.info(f"🏗️ MCP WRAPPER: Creating structure from CIF ({len(cif_str)} chars)")
            result = self.mp_agent.create_structure_from_cif(cif_str)
            
            if result:
                logger.info(f"✅ MCP WRAPPER: Created structure from CIF")
                return {
                    "status": "success",
                    "data": result,
                    "mcp_action": "create_structure_from_cif"
                }
            else:
                logger.warning(f"⚠️ MCP WRAPPER: Failed to create structure from CIF")
                return {
                    "status": "failed",
                    "message": "Could not create structure from CIF",
                    "mcp_action": "create_structure_from_cif"
                }
        except Exception as e:
            logger.error(f"💥 MCP WRAPPER: CIF structure creation failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "mcp_action": "create_structure_from_cif"
            }
    
    def get_structure(self, material_id: str, format: str = "poscar") -> Dict[str, Any]:
        """Get structure for material ID (convenience method)"""
        try:
            logger.info(f"📋 MCP WRAPPER: Getting {format} structure for {material_id}")
            
            # First, select the material to ensure it's loaded
            select_result = self.mp_agent.select_material_by_id(material_id)
            if not select_result or select_result.get('error'):
                logger.warning(f"⚠️ MCP WRAPPER: Could not select material {material_id}")
                return {
                    "status": "not_found",
                    "message": f"Material {material_id} not found",
                    "mcp_action": "get_structure"
                }
            
            # Then get the structure data using the URI
            structure_uri = f"structure://mp_{material_id}"
            result = self.mp_agent.get_structure_data(structure_uri, format)
            
            if result:
                logger.info(f"✅ MCP WRAPPER: Got {format} structure for {material_id}")
                return {
                    "status": "success",
                    "data": result,
                    "mcp_action": "get_structure",
                    "material_id": material_id,
                    "format": format
                }
            else:
                logger.warning(f"⚠️ MCP WRAPPER: No structure for {material_id}")
                return {
                    "status": "not_found",
                    "message": f"No {format} structure for {material_id}",
                    "mcp_action": "get_structure"
                }
        except Exception as e:
            logger.error(f"💥 MCP WRAPPER: Get structure failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "mcp_action": "get_structure"
            }

    def get_all_available_tools(self) -> Dict[str, str]:
        """Get list of all available MCP tools"""
        return {
            "search_material": "Search for materials by formula",
            "get_material_details": "Get detailed material data by ID", 
            "create_visualization": "Create structure visualization",
            "create_supercell": "Create supercell structure",
            "create_moire_bilayer": "Create moire bilayer structure",
            "get_structure_data": "Get structure data (POSCAR/CIF)",
            "create_structure_from_poscar": "Create structure from POSCAR",
            "create_structure_from_cif": "Create structure from CIF", 
            "get_structure": "Get structure for material ID (convenience)"
        }

# Global wrapper instance - will be initialized by the app
mcp_wrapper = None

def initialize_mcp_wrapper(mp_agent):
    """Initialize the global MCP wrapper"""
    global mcp_wrapper
    mcp_wrapper = MCPToolsWrapper(mp_agent)
    logger.info(f"🔧 Global MCP wrapper initialized with {len(mcp_wrapper.get_all_available_tools())} tools")

def get_mcp_wrapper():
    """Get the global MCP wrapper instance"""
    return mcp_wrapper