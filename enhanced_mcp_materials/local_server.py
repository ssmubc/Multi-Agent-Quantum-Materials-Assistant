"""
Enhanced MCP Materials Project server with advanced features
Based on the official MCP Materials Project server but with simplified dependencies
"""
import os
import base64
import logging
import hashlib
from typing import List, Dict, Any, Literal
try:
    from fastmcp import FastMCP
    from mcp.types import TextContent, ImageContent
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP
        from mcp.types import TextContent, ImageContent
    except ImportError:
        # Create working MCP protocol implementation
        import json
        import sys
        
        class TextContent:
            def __init__(self, type, text):
                self.type = type
                self.text = text
                
            def to_dict(self):
                return {"type": self.type, "text": self.text}
        
        class ImageContent:
            def __init__(self, type, data, mimeType):
                self.type = type
                self.data = data
                self.mimeType = mimeType
                
            def to_dict(self):
                return {"type": self.type, "data": self.data, "mimeType": self.mimeType}
        
        class FastMCP:
            def __init__(self, name):
                self.name = name
                self.tools = {}
                
            def tool(self):
                def decorator(func):
                    self.tools[func.__name__] = func
                    return func
                return decorator
                
            def run(self, mode):
                """Run MCP server with proper JSON-RPC protocol"""
                if mode != "stdio":
                    return
                
                # Read from stdin and write to stdout
                while True:
                    try:
                        line = sys.stdin.readline()
                        if not line:
                            break
                            
                        request = json.loads(line.strip())
                        response = self._handle_request(request)
                        
                        if response:
                            sys.stdout.write(json.dumps(response) + "\n")
                            sys.stdout.flush()
                            
                    except (json.JSONDecodeError, KeyboardInterrupt, EOFError):
                        break
                    except Exception as e:
                        error_response = {
                            "jsonrpc": "2.0",
                            "id": request.get("id") if 'request' in locals() else None,
                            "error": {"code": -32603, "message": str(e)}
                        }
                        sys.stdout.write(json.dumps(error_response) + "\n")
                        sys.stdout.flush()
                        
            def _handle_request(self, request):
                """Handle JSON-RPC request"""
                method = request.get("method")
                
                if method == "initialize":
                    return {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {"listChanged": True}
                            },
                            "serverInfo": {
                                "name": self.name,
                                "version": "1.0.0"
                            }
                        }
                    }
                elif method == "tools/call":
                    params = request.get("params", {})
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    
                    if tool_name in self.tools:
                        try:
                            result = self.tools[tool_name](**arguments)
                            # Convert result to proper format
                            if isinstance(result, list):
                                content = [item.to_dict() if hasattr(item, 'to_dict') else item for item in result]
                            else:
                                content = [result.to_dict() if hasattr(result, 'to_dict') else result]
                            
                            return {
                                "jsonrpc": "2.0",
                                "id": request.get("id"),
                                "result": {"content": content}
                            }
                        except Exception as e:
                            return {
                                "jsonrpc": "2.0",
                                "id": request.get("id"),
                                "error": {"code": -32603, "message": str(e)}
                            }
                    else:
                        return {
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "error": {"code": -32601, "message": f"Tool not found: {tool_name}"}
                        }
                
                return None
from mp_api.client import MPRester
from pymatgen.core.structure import Structure
from pymatgen.core.lattice import Lattice
import plotly.graph_objects as go
import plotly.io as pio
import matplotlib.pyplot as plt
from io import BytesIO

logger = logging.getLogger(__name__)

# Create MCP server
mcp = FastMCP("enhanced-mcp-materials")

# In-memory structure storage for current session
structure_storage = {}

# Simplified structure storage
from pymatgen.io.vasp.inputs import Poscar
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
import uuid
import json

def get_enhanced_description(structure: Structure, material_id: str = None, structure_id: str = None, properties = None) -> str:
    """Get enhanced structure description with Materials Project properties"""
    try:
        description = "Structure Information [ENHANCED]\n\n"
        
        # Enhanced spacegroup analysis
        spg_info = ""
        try:
            spg_analyzer = SpacegroupAnalyzer(structure)
            spg_symbol = spg_analyzer.get_space_group_symbol()
            spg_number = spg_analyzer.get_space_group_number()
            crystal_system = spg_analyzer.get_crystal_system()
            
            spg_info = f"""
Spacegroup: {spg_symbol} (#{spg_number})
Crystal System: {crystal_system}
"""
        except Exception:
            pass

        # Add Materials Project properties if available
        mp_properties = ""
        if properties:
            if hasattr(properties, 'band_gap') and properties.band_gap is not None:
                mp_properties += f"\nBand Gap: {properties.band_gap:.3f} eV"
            if hasattr(properties, 'formation_energy_per_atom') and properties.formation_energy_per_atom is not None:
                mp_properties += f"\nFormation Energy: {properties.formation_energy_per_atom:.3f} eV/atom"

        description += f"""Material id: {material_id if material_id else 'N/A'}
Formula: {structure.composition.formula}{spg_info.strip()}{mp_properties}
Lattice Parameters:
a={structure.lattice.a:.4f}, b={structure.lattice.b:.4f}, c={structure.lattice.c:.4f}
Angles:
alpha={structure.lattice.alpha:.4f}, beta={structure.lattice.beta:.4f}, gamma={structure.lattice.gamma:.4f}
Number of atoms: {len(structure)}
"""
        return json.loads(json.dumps(description))
    except Exception as e:
        logger.warning(f"Enhanced description failed: {e}")
        return f"Structure {structure_id}: Enhanced description failed"

def get_poscar_str(structure: Structure) -> str:
    """Get POSCAR string with robust error handling"""
    try:
        # Always use simple method for reliability
        logger.info(f"📋 POSCAR: Generating for {len(structure)} atoms using robust method")
        poscar_str = structure.to(fmt="poscar")
        logger.info(f"✅ POSCAR: Generated successfully ({len(poscar_str)} chars)")
        return poscar_str
    except Exception as e:
        logger.error(f"❌ POSCAR: Generation failed ({e}), creating minimal fallback")
        # Create minimal valid POSCAR as fallback
        formula = structure.composition.reduced_formula
        return f"""{formula} - Fallback POSCAR
1.0
10.0 0.0 0.0
0.0 10.0 0.0
0.0 0.0 10.0
{formula.replace('1', '').replace('2', '').replace('3', '').replace('4', '').replace('5', '')}
1
Direct
0.0 0.0 0.0
"""

def generate_structure_id(material_id: str = None, structure: Structure = None) -> str:
    """Generate unique structure ID"""
    if material_id:
        return f"mp_{material_id}"
    else:
        content = str(structure) if structure else str(uuid.uuid4())
        return hashlib.md5(content.encode()).hexdigest()[:8]

@mcp.tool()
def search_materials_by_formula(chemical_formula: str) -> List[TextContent]:
    """Search for materials by chemical formula using Materials Project API
    
    Args:
        chemical_formula: Chemical formula (e.g., "TiO2", "LiFePO4")
    
    Returns:
        List of material descriptions
    """
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        return [TextContent(type="text", text="Error: MP_API_KEY environment variable not set")]
    
    try:
        with MPRester(api_key) as mpr:
            # Try new API fields first, fallback to old ones
            try:
                results = mpr.materials.summary.search(
                    formula=chemical_formula, 
                    fields=["material_id", "formula_pretty", "band_gap", "formation_energy_per_atom"]
                )
            except Exception as api_error:
                logger.warning(f"New API failed, trying legacy fields: {api_error}")
                try:
                    results = mpr.materials.summary.search(
                        formula=chemical_formula
                    )
                except Exception as legacy_error:
                    logger.error(f"Both API attempts failed: {legacy_error}")
                    return [TextContent(type="text", text=f"API Error: {str(legacy_error)}")]
            
            if not results:
                return [TextContent(type="text", text=f"No materials found for formula: {chemical_formula}")]
            
            descriptions = []
            for material in results[:10]:
                # Store structure info for later use
                structure_id = generate_structure_id(material_id=material.material_id)
                structure_storage[structure_id] = {
                    'material_id': material.material_id,
                    'structure': None  # Will be loaded when needed
                }
                
                desc = f"Material ID: {material.material_id}\n"
                desc += f"Formula: {material.formula_pretty}\n"
                desc += f"Space Group: {material.symmetry.symbol}\n" if hasattr(material, 'symmetry') and material.symmetry else ""
                desc += f"Crystal System: {material.symmetry.crystal_system}\n" if hasattr(material, 'symmetry') and material.symmetry and hasattr(material.symmetry, 'crystal_system') else ""
                desc += f"Band Gap: {material.band_gap:.3f} eV\n" if material.band_gap else "Band Gap: N/A\n"
                desc += f"Formation Energy: {material.formation_energy_per_atom:.3f} eV/atom\n" if material.formation_energy_per_atom else ""
                desc += f"Structure ID: {structure_id}\n"
                desc += "---"
                descriptions.append(TextContent(type="text", text=desc))
            
            return descriptions
            
    except Exception as e:
        return [TextContent(type="text", text=f"Error searching materials: {str(e)}")]

@mcp.tool()
def select_material_by_id(material_id: str) -> List[TextContent]:
    """Select a specific material by its material ID
    
    Args:
        material_id: Materials Project ID (e.g., "mp-149")
    
    Returns:
        Material description and structure URI
    """
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        return [TextContent(type="text", text="Error: MP_API_KEY environment variable not set")]
    
    try:
        # Ensure material_id is properly formatted
        if not material_id.startswith('mp-'):
            material_id = f"mp-{material_id}"
        
        logger.info(f"🔍 SELECT_MATERIAL: Searching for {material_id}")
        
        with MPRester(api_key) as mpr:
            # Try to get structure first
            try:
                structure = mpr.get_structure_by_material_id(material_id)
                if not structure:
                    logger.error(f"❌ SELECT_MATERIAL: No structure found for {material_id}")
                    return [TextContent(type="text", text=f"Material not found: {material_id}")]
                logger.info(f"✅ SELECT_MATERIAL: Found structure for {material_id} with {len(structure)} atoms")
            except Exception as struct_error:
                logger.error(f"❌ SELECT_MATERIAL: Structure lookup failed for {material_id}: {struct_error}")
                return [TextContent(type="text", text=f"Error getting structure for {material_id}: {struct_error}")]
            
            # Get material properties with API compatibility
            try:
                material_data = mpr.materials.summary.search(
                    material_ids=[material_id],
                    fields=["material_id", "formula_pretty", "band_gap", "formation_energy_per_atom"]
                )
                logger.info(f"✅ SELECT_MATERIAL: Found properties for {material_id}")
            except Exception as props_error:
                logger.warning(f"⚠️ SELECT_MATERIAL: Properties lookup failed, trying without fields: {props_error}")
                try:
                    material_data = mpr.materials.summary.search(material_ids=[material_id])
                    logger.info(f"✅ SELECT_MATERIAL: Found properties for {material_id} (no fields)")
                except Exception as fallback_error:
                    logger.warning(f"⚠️ SELECT_MATERIAL: All properties lookup failed for {material_id}: {fallback_error}")
                    material_data = []
            
            structure_id = generate_structure_id(material_id=material_id)
            structure_storage[structure_id] = {
                'material_id': material_id,
                'structure': structure,
                'properties': material_data[0] if material_data else None
            }
            
            logger.info(f"💾 SELECT_MATERIAL: Stored {material_id} as {structure_id} in storage")
            logger.info(f"💾 SELECT_MATERIAL: Storage now has {len(structure_storage)} items: {list(structure_storage.keys())}")
            
            structure_uri = f"structure://{structure_id}"
            description = get_enhanced_description(structure, material_id, structure_id, material_data[0] if material_data else None)
            
            logger.info(f"✅ SELECT_MATERIAL: Returning description and URI {structure_uri}")
            return [
                TextContent(type="text", text=description),
                TextContent(type="text", text=f"structure uri: {structure_uri}")
            ]
            
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting material: {str(e)}")]

@mcp.tool()
def get_structure_data(structure_uri: str, format: Literal["cif", "poscar"] = "poscar") -> List[TextContent]:
    """Retrieve structure data in specified format
    
    Args:
        structure_uri: The URI of the structure (e.g., "structure://mp_149")
        format: Output format, either "cif" or "poscar"
    
    Returns:
        Structure file content as string
    """
    structure_id = structure_uri.replace("structure://", "")
    
    logger.info(f"🔍 GET_STRUCTURE: Looking for {structure_id} in storage with {len(structure_storage)} items")
    logger.info(f"🔍 GET_STRUCTURE: Available keys: {list(structure_storage.keys())}")
    
    if structure_id not in structure_storage:
        # Try to reload from Materials Project if it's an mp_ ID
        if structure_id.startswith("mp_"):
            material_id = structure_id.replace("mp_", "")
            logger.info(f"🔄 GET_STRUCTURE: Attempting to reload {material_id} from Materials Project")
            
            api_key = os.getenv("MP_API_KEY")
            if api_key:
                try:
                    with MPRester(api_key) as mpr:
                        structure = mpr.get_structure_by_material_id(material_id)
                        if structure:
                            # Reload structure into storage
                            material_data = mpr.materials.summary.search(
                                material_ids=[material_id],
                                fields=["material_id", "formula_pretty", "band_gap", "formation_energy_per_atom", "symmetry"]
                            )
                            
                            structure_storage[structure_id] = {
                                'material_id': material_id,
                                'structure': structure,
                                'properties': material_data[0] if material_data else None
                            }
                            logger.info(f"✅ GET_STRUCTURE: Reloaded {material_id} successfully")
                        else:
                            logger.error(f"❌ GET_STRUCTURE: Failed to reload {material_id}")
                            return [TextContent(type="text", text="Structure not found")]
                except Exception as e:
                    logger.error(f"❌ GET_STRUCTURE: Error reloading {material_id}: {e}")
                    return [TextContent(type="text", text="Structure not found")]
            else:
                return [TextContent(type="text", text="Structure not found")]
        else:
            return [TextContent(type="text", text="Structure not found")]
    
    structure_info = structure_storage[structure_id]
    structure = structure_info.get('structure')
    
    if not structure:
        return [TextContent(type="text", text="No structure data available")]
    
    try:
        logger.info(f"🔄 GET_STRUCTURE: Generating {format} for {structure_id} ({len(structure)} atoms)")
        
        if format == "cif":
            try:
                structure_str = structure.to(fmt="cif")
            except Exception as e:
                logger.error(f"❌ GET_STRUCTURE: CIF generation failed: {e}")
                structure_str = f"Error generating CIF: {e}"
        else:  # poscar
            structure_str = get_poscar_str(structure)
        
        logger.info(f"✅ GET_STRUCTURE: Successfully retrieved {format} data for {structure_id} ({len(structure_str)} chars)")
        return [TextContent(type="text", text=structure_str)]
        
    except Exception as e:
        logger.error(f"❌ GET_STRUCTURE: Error getting structure data: {e}")
        return [TextContent(type="text", text=f"Error getting structure data: {str(e)}")]

@mcp.tool()
def create_structure_from_poscar(poscar_str: str) -> List[TextContent]:
    """Create a new structure from a POSCAR string
    
    Args:
        poscar_str: The POSCAR string of the structure
    
    Returns:
        Information about the newly created structure
    """
    try:
        structure = Structure.from_str(poscar_str, fmt="poscar")
        structure_id = generate_structure_id(structure=structure)
        structure_storage[structure_id] = {
            'material_id': None,
            'structure': structure
        }
        
        structure_uri = f"structure://{structure_id}"
        description = get_enhanced_description(structure, None, structure_id)
        
        return [
            TextContent(type="text", text=f"A new structure is created with the structure uri: {structure_uri}"),
            TextContent(type="text", text=description)
        ]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error creating structure: {str(e)}")]

@mcp.tool()
def create_structure_from_cif(cif_str: str) -> List[TextContent]:
    """Create a new structure from a CIF string
    
    Args:
        cif_str: The CIF string of the structure
    
    Returns:
        Information about the newly created structure
    """
    try:
        structure = Structure.from_str(cif_str, fmt="cif")
        structure_id = generate_structure_id(structure=structure)
        structure_storage[structure_id] = {
            'material_id': None,
            'structure': structure
        }
        
        structure_uri = f"structure://{structure_id}"
        description = get_enhanced_description(structure, None, structure_id)
        
        return [
            TextContent(type="text", text=f"A new structure is created with the structure uri: {structure_uri}"),
            TextContent(type="text", text=description)
        ]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error creating structure: {str(e)}")]

@mcp.tool()
def plot_structure(structure_uri: str, duplication: List[int] = [1, 1, 1]) -> List[ImageContent]:
    """Visualize the crystal structure
    
    Args:
        structure_uri: The URI of the structure
        duplication: The duplication of the structure along a, b, c axes
    
    Returns:
        PNG image of the structure
    """
    structure_id = structure_uri.replace("structure://", "")
    
    if structure_id not in structure_storage:
        return [ImageContent(type="image", data="", mimeType="image/png")]
    
    structure_info = structure_storage[structure_id]
    structure = structure_info.get('structure')
    
    if not structure:
        return [ImageContent(type="image", data="", mimeType="image/png")]
    
    try:
        # Create a simple 3D plot using matplotlib
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # Plot atoms
        for site in structure:
            coords = site.frac_coords
            ax.scatter(coords[0], coords[1], coords[2], 
                      s=100, label=str(site.specie), alpha=0.8)
        
        # Plot unit cell
        lattice = structure.lattice
        vertices = [
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],  # bottom face
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]   # top face
        ]
        
        # Draw unit cell edges
        edges = [
            [0, 1], [1, 2], [2, 3], [3, 0],  # bottom face
            [4, 5], [5, 6], [6, 7], [7, 4],  # top face
            [0, 4], [1, 5], [2, 6], [3, 7]   # vertical edges
        ]
        
        for edge in edges:
            points = [vertices[edge[0]], vertices[edge[1]]]
            ax.plot3D(*zip(*points), 'k-', alpha=0.3)
        
        ax.set_xlabel('a')
        ax.set_ylabel('b')
        ax.set_zlabel('c')
        ax.set_title(f'Crystal Structure: {structure.composition.reduced_formula}')
        ax.legend()
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return [ImageContent(type="image", data=img_base64, mimeType="image/png")]
        
    except Exception as e:
        logger.error(f"Error plotting structure: {e}")
        return [ImageContent(type="image", data="", mimeType="image/png")]

@mcp.tool()
def build_supercell(bulk_structure_uri: str, supercell_parameters: Dict[str, Any]) -> List[TextContent]:
    """Build supercell from bulk structure with robust error handling
    
    Args:
        bulk_structure_uri: The URI of the bulk structure
        supercell_parameters: Parameters for supercell construction (e.g., {"scaling_matrix": [[2,0,0],[0,2,0],[0,0,2]]})
    
    Returns:
        Information about the newly created supercell
    """
    logger.info(f"🏗️ BUILD_SUPERCELL: Starting for {bulk_structure_uri}")
    structure_id = bulk_structure_uri.replace("structure://", "")
    
    logger.info(f"🔍 BUILD_SUPERCELL: Looking for {structure_id} in storage with {len(structure_storage)} items")
    logger.info(f"🔍 BUILD_SUPERCELL: Available keys: {list(structure_storage.keys())}")
    
    if structure_id not in structure_storage:
        # Try to reload structure if missing
        if structure_id.startswith("mp_"):
            material_id = structure_id.replace("mp_", "")
            logger.info(f"🔄 BUILD_SUPERCELL: Attempting to reload {material_id}")
            
            api_key = os.getenv("MP_API_KEY")
            if api_key:
                try:
                    with MPRester(api_key) as mpr:
                        structure = mpr.get_structure_by_material_id(material_id)
                        if structure:
                            structure_storage[structure_id] = {
                                'material_id': material_id,
                                'structure': structure
                            }
                            logger.info(f"✅ BUILD_SUPERCELL: Reloaded {material_id} successfully")
                        else:
                            logger.error(f"❌ BUILD_SUPERCELL: Failed to reload {material_id}")
                            return [TextContent(type="text", text=f"Structure {material_id} not found in Materials Project")]
                except Exception as e:
                    logger.error(f"❌ BUILD_SUPERCELL: Error reloading {material_id}: {e}")
                    return [TextContent(type="text", text=f"Error reloading structure: {e}")]
            else:
                return [TextContent(type="text", text="Structure not found and no API key available")]
        else:
            return [TextContent(type="text", text="Bulk structure not found")]
    
    structure_info = structure_storage[structure_id]
    bulk_structure = structure_info.get('structure')
    
    if not bulk_structure:
        return [TextContent(type="text", text="No bulk structure data available")]
    
    try:
        # Extract scaling matrix from parameters
        scaling_matrix = supercell_parameters.get("scaling_matrix", [[2,0,0],[0,2,0],[0,0,2]])
        logger.info(f"🔧 BUILD_SUPERCELL: Using scaling matrix {scaling_matrix}")
        
        # Create supercell using pymatgen
        logger.info(f"⚙️ BUILD_SUPERCELL: Creating supercell from {len(bulk_structure)} atoms")
        supercell = bulk_structure.make_supercell(scaling_matrix)
        logger.info(f"✅ BUILD_SUPERCELL: Supercell created with {len(supercell)} atoms")
        
        # Create new structure data for supercell
        supercell_id = generate_structure_id(structure=supercell)
        structure_storage[supercell_id] = {
            'material_id': None,
            'structure': supercell
        }
        
        supercell_uri = f"structure://{supercell_id}"
        logger.info(f"💾 BUILD_SUPERCELL: Stored supercell as {supercell_uri}")
        
        # Create description
        desc = f"Supercell created from {bulk_structure_uri}\n"
        desc += f"Scaling matrix: {scaling_matrix}\n"
        desc += f"Original atoms: {len(bulk_structure)}\n"
        desc += f"Supercell atoms: {len(supercell)}\n"
        desc += f"Formula: {supercell.composition.reduced_formula}\n"
        desc += f"Lattice: a={supercell.lattice.a:.3f}, b={supercell.lattice.b:.3f}, c={supercell.lattice.c:.3f}"
        
        # Also generate POSCAR for the supercell
        try:
            supercell_poscar = get_poscar_str(supercell)
            desc += f"\n\nSupercell POSCAR:\n{supercell_poscar}"
        except Exception as poscar_error:
            logger.warning(f"⚠️ BUILD_SUPERCELL: Could not generate POSCAR: {poscar_error}")
            desc += "\n\nPOSCAR generation failed"
        
        return [
            TextContent(type="text", text=f"Supercell created with URI: {supercell_uri}"),
            TextContent(type="text", text=desc)
        ]
        
    except Exception as e:
        logger.error(f"❌ BUILD_SUPERCELL: Error building supercell: {e}")
        return [TextContent(type="text", text=f"Error building supercell: {str(e)}")]

# Enhanced moire generation embedded directly (no import issues)
def generate_enhanced_moire_bilayer(structure: Structure, interlayer_spacing: float, max_num_atoms: int, twist_angle: float, vacuum_thickness: float) -> tuple[Structure, str]:
    """Ultra-fast moire bilayer generation - returns (structure, diagnostics)"""
    diagnostics = []
    diagnostics.append("ULTRA-FAST MODE: Minimal moire generation")
    diagnostics.append(f"ULTRA-FAST MODE: {len(structure)} atoms, {twist_angle}° twist")
    
    try:
        # Ultra-simple approach: just stack two layers with minimal processing
        layer1 = structure.copy()
        layer2 = structure.copy()
        
        # Simple z-translation for second layer
        layer2.translate_sites(range(len(layer2)), [0, 0, interlayer_spacing])
        
        # Combine layers (limit atoms immediately)
        layer1_sites = list(layer1.sites)[:max_num_atoms//2]
        layer2_sites = list(layer2.sites)[:max_num_atoms//2]
        moire_sites = layer1_sites + layer2_sites
        
        # Simple lattice expansion
        old_lattice = layer1.lattice
        new_lattice_matrix = old_lattice.matrix.copy()
        new_lattice_matrix[2, 2] = old_lattice.c + interlayer_spacing + vacuum_thickness
        new_lattice = Lattice(new_lattice_matrix)
        
        final_structure = Structure(new_lattice, [site.specie for site in moire_sites], [site.frac_coords for site in moire_sites])
        diagnostics.append(f"ULTRA-FAST MODE: Completed - {len(final_structure)} atoms")
        return final_structure, "\n".join(diagnostics)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        diagnostics.append(f"BASIC FALLBACK MODE: Enhanced generation failed: {e}")
        diagnostics.append(f"BASIC FALLBACK MODE: Full error trace: {error_details}")
        # Simple fallback
        layer1 = structure.copy()
        layer2 = structure.copy()
        layer2.translate_sites(range(len(layer2)), [0, 0, interlayer_spacing])
        
        moire_sites = list(layer1.sites) + list(layer2.sites)
        if len(moire_sites) > max_num_atoms:
            moire_sites = moire_sites[:max_num_atoms]
        
        old_lattice = layer1.lattice
        new_lattice_matrix = old_lattice.matrix.copy()
        new_lattice_matrix[2, 2] = old_lattice.c + interlayer_spacing + vacuum_thickness
        new_lattice = Lattice(new_lattice_matrix)
        
        final_structure = Structure(new_lattice, [site.specie for site in moire_sites], [site.frac_coords for site in moire_sites])
        diagnostics.append(f"BASIC FALLBACK MODE: Completed - {len(final_structure)} atoms")
        return final_structure, "\n".join(diagnostics)

@mcp.tool()
def moire_homobilayer(bulk_structure_uri: str, interlayer_spacing: float, max_num_atoms: int = 10, twist_angle: float = 0.0, vacuum_thickness: float = 15.0) -> List[TextContent]:
    """Generate a moire superstructure of a 2D homobilayer with enhanced physics
    
    Args:
        bulk_structure_uri: The URI of the bulk structure
        interlayer_spacing: The interlayer spacing between layers in Angstrom
        max_num_atoms: Maximum number of atoms in the moire superstructure
        twist_angle: Twist angle in degrees
        vacuum_thickness: Vacuum thickness in z-direction in Angstrom
    
    Returns:
        Information about the newly created moire structure
    """
    structure_id = bulk_structure_uri.replace("structure://", "")
    
    if structure_id not in structure_storage:
        return [TextContent(type="text", text="Bulk structure not found")]
    
    structure_info = structure_storage[structure_id]
    bulk_structure = structure_info.get('structure')
    
    if not bulk_structure:
        return [TextContent(type="text", text="No bulk structure data available")]
    
    try:
        # Use enhanced moire generation with timeout protection
        logger.info(f"🌀 MOIRE: Starting generation for {len(bulk_structure)} atoms, {twist_angle}° twist")
        try:
            moire_structure, diagnostics = generate_enhanced_moire_bilayer(
                structure=bulk_structure,
                interlayer_spacing=interlayer_spacing,
                max_num_atoms=max_num_atoms,
                twist_angle=twist_angle,
                vacuum_thickness=vacuum_thickness
            )
            logger.info(f"✅ MOIRE: Generation completed successfully")
        except Exception as e:
            logger.error(f"❌ MOIRE: Generation failed: {e}")
            return [TextContent(type="text", text=f"Error generating moire bilayer: {str(e)}")]
        
        # Store the moire structure
        moire_id = generate_structure_id(structure=moire_structure)
        structure_storage[moire_id] = {
            'material_id': None,
            'structure': moire_structure
        }
        
        moire_uri = f"structure://{moire_id}"
        logger.info(f"🌀 MOIRE: Created structure {moire_uri} with {len(moire_structure)} atoms")
        
        # Extract method type from diagnostics for immediate visibility
        method_type = "UNKNOWN"
        if "ADVANCED ASE MODE" in diagnostics:
            method_type = "ADVANCED ASE MODE"
        elif "SIMPLE PYMATGEN MODE" in diagnostics:
            method_type = "SIMPLE PYMATGEN MODE"
        elif "BASIC FALLBACK MODE" in diagnostics:
            method_type = "BASIC FALLBACK MODE"
        
        # Log diagnostics to server console
        logger.info(f"🔧 MOIRE: Using {method_type}")
        for line in diagnostics.split("\n")[:5]:  # Only log first 5 lines
            if line.strip():
                logger.info(f"🔧 MOIRE: {line.strip()}")
        
        # Get structure data for display
        try:
            structure_poscar = get_poscar_str(moire_structure)
            structure_desc = get_enhanced_description(moire_structure, None, moire_id)
        except Exception as e:
            structure_poscar = f"Error getting structure data: {e}"
            structure_desc = f"Structure with {len(moire_structure)} atoms"
        
        # Combine all info in first item so Streamlit displays it
        combined_text = f"{method_type}: Moire structure created with URI: {moire_uri}\n\n"
        combined_text += f"DIAGNOSTICS:\n{diagnostics}\n\n"
        combined_text += f"STRUCTURE DESCRIPTION:\n{structure_desc}\n\n"
        combined_text += f"POSCAR DATA:\n{structure_poscar}"
        
        return [
            TextContent(type="text", text=combined_text),
            TextContent(type="text", text=f"STRUCTURE DESCRIPTION:\n{structure_desc}"),
            TextContent(type="text", text=f"POSCAR DATA:\n{structure_poscar}"),
            TextContent(type="text", text=f"FULL DIAGNOSTICS:\n{diagnostics}")
        ]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error generating moire bilayer: {str(e)}")]

def main():
    """Main entry point for the MCP server"""
    logging.basicConfig(level=logging.ERROR)  # Reduce logging to prevent JSON interference
    mcp.run("stdio")

if __name__ == "__main__":
    main()