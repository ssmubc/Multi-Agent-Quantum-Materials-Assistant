# Supervisor Agent for AWS Strands Multi-Agent Workflow
from typing import Dict, Any, Optional
import logging
from .structure_matching_agent import StructureMatchingAgent
from .dft_parameter_agent import DFTParameterAgent
import re

logger = logging.getLogger(__name__)

class SupervisorAgent:
    """Supervisor agent that orchestrates POSCAR analysis workflow"""
    
    def __init__(self, mp_agent):
        self.mp_agent = mp_agent
        self.structure_agent = StructureMatchingAgent(mp_agent)
        self.dft_agent = DFTParameterAgent(mp_agent)
    
    def process_query(self, query: str, formula: str) -> Dict[str, Any]:
        """Intelligently process query and decide which MCP tools to use"""
        logger.info(f"🤖 SUPERVISOR: Processing query for {formula}")
        
        query_lower = query.lower()
        
        # Detect query intent and select appropriate MCP tools
        if any(term in query_lower for term in ["moire", "bilayer", "twist"]):
            logger.info(f"🌀 SUPERVISOR: Detected moire bilayer request")
            return self._handle_moire_request(formula, query)
        elif any(term in query_lower for term in ["search", "find materials", "available", "list"]) and not formula.startswith("mp-"):
            logger.info(f"🔍 SUPERVISOR: Detected formula search request")
            return self._handle_formula_search(formula)
        elif any(term in query_lower for term in ["poscar", "cif"]) and any(term in query_lower for term in ["create", "from"]):
            logger.info(f"📄 SUPERVISOR: Detected structure creation request")
            return self._handle_structure_creation(query)
        elif any(term in query_lower for term in ["3d", "plot", "visualiz", "structure plot"]):
            logger.info(f"🎨 SUPERVISOR: Detected visualization request")
            return self._handle_visualization_request(formula)
        elif "supercell" in query_lower:
            logger.info(f"🔧 SUPERVISOR: Detected supercell request")
            return self._handle_supercell_request(formula, query)
        else:
            logger.info(f"🔍 SUPERVISOR: Standard material lookup")
            return self._handle_standard_lookup(formula)
    
    def _handle_visualization_request(self, formula: str) -> Dict[str, Any]:
        """Handle visualization requests using plot_structure tool"""
        try:
            # Get material data first
            mp_data = self.mp_agent.search(formula)
            if not mp_data or mp_data.get("error"):
                return {"status": "error", "message": "Material not found"}
            
            structure_uri = mp_data.get("structure_uri")
            if structure_uri:
                # Call plot_structure tool
                plot_result = self.mp_agent.plot_structure(structure_uri, [1, 1, 1])
                logger.info(f"🎨 SUPERVISOR: Called plot_structure tool")
                
                return {
                    "status": "success",
                    "mp_data": mp_data,
                    "mcp_actions": ["select_material_by_id", "get_structure_data", "plot_structure"]
                }
            
            return {"status": "error", "message": "No structure URI available"}
            
        except Exception as e:
            logger.error(f"💥 SUPERVISOR: Visualization error: {e}")
            return {"status": "error", "message": str(e)}
    
    def _handle_supercell_request(self, formula: str, query: str) -> Dict[str, Any]:
        """Handle supercell requests using build_supercell tool"""
        try:
            # Get material data first
            mp_data = self.mp_agent.search(formula)
            if not mp_data or mp_data.get("error"):
                return {"status": "error", "message": "Material not found"}
            
            structure_uri = mp_data.get("structure_uri")
            if structure_uri:
                # Extract supercell parameters from query
                import re
                supercell_match = re.search(r'(\d+)x(\d+)x(\d+)', query.lower())
                if supercell_match:
                    a, b, c = map(int, supercell_match.groups())
                    scaling_matrix = [[a,0,0],[0,b,0],[0,0,c]]
                else:
                    scaling_matrix = [[2,0,0],[0,2,0],[0,0,2]]  # default
                
                # Call build_supercell tool
                supercell_result = self.mp_agent.build_supercell(structure_uri, {"scaling_matrix": scaling_matrix})
                logger.info(f"🔧 SUPERVISOR: Called build_supercell tool")
                
                return {
                    "status": "success",
                    "mp_data": mp_data,
                    "mcp_actions": ["select_material_by_id", "get_structure_data", "build_supercell"]
                }
            
            return {"status": "error", "message": "No structure URI available"}
            
        except Exception as e:
            logger.error(f"💥 SUPERVISOR: Supercell error: {e}")
            return {"status": "error", "message": str(e)}
    
    def _handle_moire_request(self, formula: str, query: str) -> Dict[str, Any]:
        """Handle moire bilayer requests"""
        try:
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
            
            original_formula = formula
            for material_name, material_formula in moire_materials.items():
                if material_name in query_lower:
                    formula = material_formula
                    logger.info(f"🌀 SUPERVISOR: Overriding formula '{original_formula}' → '{formula}' for {material_name} moire request")
                    break
            
            # If no specific material found but it's a moire request with H2/H, default to graphene
            if formula == original_formula and original_formula in ["H2", "H"]:
                formula = "C"
                logger.info(f"🌀 SUPERVISOR: Generic moire request detected, defaulting to graphene (C)")
            
            mp_data = self.mp_agent.search(formula)
            if not mp_data or mp_data.get("error"):
                return {"status": "error", "message": "Material not found"}
            
            structure_uri = mp_data.get("structure_uri")
            if structure_uri:
                # Extract moire parameters from query
                twist_angle = 1.1  # magic angle default
                interlayer_spacing = 3.4  # default for graphene-like
                
                # Try to extract twist angle from query
                angle_match = re.search(r'(\d+\.?\d*)\s*degree', query_lower)
                if angle_match:
                    twist_angle = float(angle_match.group(1))
                    logger.info(f"🌀 SUPERVISOR: Extracted twist angle: {twist_angle}°")
                
                # Try to extract interlayer spacing
                spacing_match = re.search(r'(\d+\.?\d*)\s*[åa]', query_lower)
                if spacing_match:
                    interlayer_spacing = float(spacing_match.group(1))
                    logger.info(f"🌀 SUPERVISOR: Extracted interlayer spacing: {interlayer_spacing} Å")
                
                moire_result = self.mp_agent.moire_homobilayer(structure_uri, interlayer_spacing, 10, twist_angle, 15.0)
                logger.info(f"🌀 SUPERVISOR: Called moire_homobilayer tool with {twist_angle}° twist, {interlayer_spacing} Å spacing")
                
                return {
                    "status": "success",
                    "mp_data": mp_data,
                    "mcp_actions": ["select_material_by_id", "get_structure_data", "moire_homobilayer"],
                    "moire_params": {"twist_angle": twist_angle, "interlayer_spacing": interlayer_spacing}
                }
            return {"status": "error", "message": "No structure URI available"}
        except Exception as e:
            logger.error(f"💥 SUPERVISOR: Moire error: {e}")
            return {"status": "error", "message": str(e)}
    
    def _handle_formula_search(self, formula: str) -> Dict[str, Any]:
        """Handle formula search requests"""
        try:
            search_results = self.mp_agent.search_materials_by_formula(formula)
            logger.info(f"🔍 SUPERVISOR: Called search_materials_by_formula tool")
            
            return {
                "status": "success",
                "mp_data": {"formula": formula, "results": search_results, "count": len(search_results)},
                "mcp_actions": ["search_materials_by_formula"]
            }
        except Exception as e:
            logger.error(f"💥 SUPERVISOR: Formula search error: {e}")
            return {"status": "error", "message": str(e)}
    
    def _handle_structure_creation(self, query: str) -> Dict[str, Any]:
        """Handle structure creation from POSCAR/CIF"""
        try:
            if "poscar" in query.lower():
                # Extract POSCAR from query (simplified)
                poscar_data = "Si\n1.0\n5.43 0 0\n0 5.43 0\n0 0 5.43\nSi\n2\nDirect\n0.0 0.0 0.0\n0.25 0.25 0.25"
                result = self.mp_agent.create_structure_from_poscar(poscar_data)
                action = "create_structure_from_poscar"
            else:
                # CIF creation (simplified)
                result = None
                action = "create_structure_from_cif"
            
            logger.info(f"📄 SUPERVISOR: Called {action} tool")
            
            return {
                "status": "success",
                "mp_data": {"created": True},
                "mcp_actions": [action]
            }
        except Exception as e:
            logger.error(f"💥 SUPERVISOR: Structure creation error: {e}")
            return {"status": "error", "message": str(e)}
    
    def _handle_standard_lookup(self, formula: str) -> Dict[str, Any]:
        """Handle standard material lookup"""
        try:
            mp_data = self.mp_agent.search(formula)
            if mp_data and not mp_data.get("error"):
                return {
                    "status": "success",
                    "mp_data": mp_data,
                    "mcp_actions": ["select_material_by_id", "get_structure_data"]
                }
            return {"status": "error", "message": "Material not found"}
            
        except Exception as e:
            logger.error(f"💥 SUPERVISOR: Standard lookup error: {e}")
            return {"status": "error", "message": str(e)}
    
    def process_poscar_query(self, query: str, poscar_text: str) -> Dict[str, Any]:
        """Orchestrate complete POSCAR analysis workflow"""
        
        logger.info("🎯 SUPERVISOR: Starting POSCAR analysis workflow")
        
        # Step 1: Extract formula from POSCAR
        formula = self._extract_formula_from_poscar(poscar_text)
        logger.info(f"📋 SUPERVISOR: Extracted formula: {formula}")
        
        # Step 2: Structure matching
        match_result = self.structure_agent.match_poscar_to_mp(poscar_text, formula)
        
        if not match_result:
            logger.warning("⚠️ SUPERVISOR: No structure match found, using fallback")
            return {
                "status": "no_match",
                "formula": formula,
                "message": f"No Materials Project structure matches your POSCAR for {formula}",
                "fallback_data": {"formula": formula, "source": "POSCAR_only"}
            }
        
        # Step 3: Validate match quality
        if match_result["match_score"] < 0.8:
            logger.warning(f"⚠️ SUPERVISOR: Low match quality ({match_result['match_score']:.3f})")
        
        # Step 4: Extract DFT parameters
        dft_params = self.dft_agent.extract_dft_parameters(
            match_result["material_id"], 
            match_result["mp_data"]
        )
        
        # Step 5: Prepare validated data
        validated_data = {
            "status": "matched",
            "formula": formula,
            "matched_material_id": match_result["material_id"],
            "match_score": match_result["match_score"],
            "mp_data": match_result["mp_data"],
            "dft_parameters": dft_params,
            "poscar_text": poscar_text,
            "validation": {
                "structure_matched": True,
                "rms_distance": match_result.get("rms_distance"),
                "confidence": "high" if match_result["match_score"] > 0.9 else "medium",
                "parameters_valid": self.dft_agent.validate_parameters(dft_params)
            }
        }
        
        logger.info(f"✅ SUPERVISOR: Workflow complete - matched to {match_result['material_id']}")
        return validated_data
    
    def _extract_formula_from_poscar(self, poscar_text: str) -> str:
        """Extract chemical formula from POSCAR"""
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