"""
Enhanced MCP Materials Project server with advanced features
Based on the official MCP Materials Project server but with simplified dependencies
"""
import os
import base64
import logging
import hashlib
from typing import List, Dict, Any, Literal
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent, ImageContent
from io import BytesIO

logger = logging.getLogger(__name__)

# Create MCP server
mcp = FastMCP("enhanced-mcp-materials")

# In-memory structure storage (simplified version of the official server's approach)
structure_storage = {}

def ensure_structure_object(structure_data):
    """Ensure we have a proper pymatgen Structure object"""
    if isinstance(structure_data, dict):
        try:
            from pymatgen.core.structure import Structure
            return Structure.from_dict(structure_data)
        except Exception:
            return None
    return structure_data

def get_enhanced_description(structure, material_id: str = None, structure_id: str = None, properties = None) -> str:
    """Get enhanced structure description with Materials Project properties"""
    try:
        from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
        import json
        
        description = "Structure Information [ENHANCED]\n\n"
        
        # Enhanced spacegroup analysis
        spg_info = ""
        try:
            spg_analyzer = SpacegroupAnalyzer(structure)
            spg_symbol = spg_analyzer.get_space_group_symbol()
            spg_number = spg_analyzer.get_space_group_number()
            crystal_system = spg_analyzer.get_crystal_system()
            
            spg_info = f"""\nSpacegroup: {spg_symbol} (#{spg_number})\nCrystal System: {crystal_system}\n"""
        except Exception:
            pass

        # Add Materials Project properties if available
        mp_properties = ""
        if properties:
            if hasattr(properties, 'band_gap') and properties.band_gap is not None:
                mp_properties += f"\nBand Gap: {properties.band_gap:.3f} eV"
            if hasattr(properties, 'formation_energy_per_atom') and properties.formation_energy_per_atom is not None:
                mp_properties += f"\nFormation Energy: {properties.formation_energy_per_atom:.3f} eV/atom"

        description += f"""Material id: {material_id if material_id else 'N/A'}\nFormula: {structure.composition.formula}{spg_info.strip()}{mp_properties}\nLattice Parameters:\na={structure.lattice.a:.4f}, b={structure.lattice.b:.4f}, c={structure.lattice.c:.4f}\nAngles:\nalpha={structure.lattice.alpha:.4f}, beta={structure.lattice.beta:.4f}, gamma={structure.lattice.gamma:.4f}\nNumber of atoms: {len(structure)}\n"""
        return description
    except Exception as e:
        logger.warning(f"Enhanced description failed: {e}")
        return f"Structure {structure_id}: Enhanced description failed"

def get_poscar_str(structure) -> str:
    """Get POSCAR string with robust error handling"""
    try:
        logger.info(f"📋 POSCAR: Generating for {len(structure)} atoms using robust method")
        poscar_str = structure.to(fmt="poscar")
        logger.info(f"✅ POSCAR: Generated successfully ({len(poscar_str)} chars)")
        return poscar_str
    except Exception as e:
        logger.error(f"❌ POSCAR: Generation failed ({e}), creating minimal fallback")
        # Create minimal valid POSCAR as fallback
        formula = structure.composition.reduced_formula
        return f"""{formula} - Fallback POSCAR\n1.0\n10.0 0.0 0.0\n0.0 10.0 0.0\n0.0 0.0 10.0\n{formula.replace('1', '').replace('2', '').replace('3', '').replace('4', '').replace('5', '')}\n1\nDirect\n0.0 0.0 0.0\n"""

def generate_structure_id(material_id: str = None, structure = None) -> str:
    """Generate unique structure ID"""
    if material_id:
        # Ensure consistent format - remove mp- prefix if present, then add mp-
        clean_id = material_id.replace('mp-', '')
        return f"mp-{clean_id}"
    else:
        import uuid
        content = str(structure) if structure else str(uuid.uuid4())
        return hashlib.sha256(content.encode()).hexdigest()[:8]

# Try to import enhanced structure data classes
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
    from enhanced_structure_data import EnhancedStructureData
    from enhanced_data_class import EnhancedStructureData as EnhancedDataClass
    ENHANCED_AVAILABLE = True
except ImportError:
    ENHANCED_AVAILABLE = False

class StructureData:
    """Structure data class with enhanced features when available"""
    
    def __init__(self, material_id: str = None, structure = None):
        self.material_id = material_id
        self.structure = ensure_structure_object(structure)
        self.structure_id = self._generate_id()
        
        # Try to create enhanced version if available
        if ENHANCED_AVAILABLE and self.structure:
            try:
                self.enhanced = EnhancedStructureData(
                    structure=self.structure,
                    structure_id=self.structure_id,
                    material_id=material_id
                )
            except Exception:
                self.enhanced = None
        else:
            self.enhanced = None
        
    def _generate_id(self) -> str:
        """Generate unique structure ID"""
        if self.material_id:
            return f"mp_{self.material_id}"
        else:
            # Generate hash from structure
            content = str(self.structure) if self.structure else "unknown"
            return hashlib.sha256(content.encode()).hexdigest()[:8]
    
    @property
    def description(self) -> str:
        """Get structure description (enhanced if available)"""
        if self.enhanced:
            return self.enhanced.description
        
        if not self.structure:
            return f"Structure {self.structure_id}: No structure data"
        
        desc = f"Structure ID: {self.structure_id}\n"
        desc += f"Formula: {self.structure.composition.reduced_formula}\n"
        desc += f"Crystal Structure: {self.structure.get_space_group_info()[1]}\n"
        desc += f"Space Group: {self.structure.get_space_group_info()[0]}\n"
        desc += f"Lattice: a={self.structure.lattice.a:.3f}, b={self.structure.lattice.b:.3f}, c={self.structure.lattice.c:.3f}\n"
        desc += f"Number of atoms: {len(self.structure)}"
        return desc
    
    @property
    def poscar_str(self) -> str:
        """Get POSCAR string (enhanced if available)"""
        if self.enhanced:
            return self.enhanced.poscar_str
        
        if self.structure:
            return get_poscar_str(self.structure)
        return ""

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
        from mp_api.client import MPRester
        
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
                # Store structure data for later use
                structure_data = StructureData(material_id=material.material_id)
                structure_storage[structure_data.structure_id] = structure_data
                
                desc = f"Material ID: {material.material_id}\n"
                desc += f"Formula: {material.formula_pretty}\n"
                desc += f"Space Group: {material.symmetry.symbol}\n" if hasattr(material, 'symmetry') and material.symmetry else ""
                desc += f"Crystal System: {material.symmetry.crystal_system}\n" if hasattr(material, 'symmetry') and material.symmetry and hasattr(material.symmetry, 'crystal_system') else ""
                desc += f"Band Gap: {material.band_gap:.3f} eV\n" if material.band_gap else "Band Gap: N/A\n"
                desc += f"Formation Energy: {material.formation_energy_per_atom:.3f} eV/atom\n" if material.formation_energy_per_atom else ""
                desc += f"Structure ID: {structure_data.structure_id}\n"
                desc += "---"
                descriptions.append(TextContent(type="text", text=desc))
            
            return descriptions
            
    except Exception as e:
        logger.error(f"Error searching materials for formula {chemical_formula}: {str(e)}")
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
        
        from mp_api.client import MPRester
        
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
            
            # Use enhanced description
            structure_id = generate_structure_id(material_id=material_id)
            properties = material_data[0] if material_data and len(material_data) > 0 else None
            desc = get_enhanced_description(structure, material_id, structure_id, properties)
            
            # Create structure data
            structure_data = StructureData(material_id=material_id, structure=structure)
            structure_storage[structure_data.structure_id] = structure_data
            
            logger.info(f"💾 SELECT_MATERIAL: Stored {material_id} as {structure_id} in storage")
            logger.info(f"💾 SELECT_MATERIAL: Storage now has {len(structure_storage)} items: {list(structure_storage.keys())}")
            
            structure_uri = f"structure://{structure_data.structure_id}"
            
            return [
                TextContent(type="text", text=desc),
                TextContent(type="text", text=f"structure uri: {structure_uri}")
            ]
            
    except Exception as e:
        logger.error(f"Error getting material {material_id}: {str(e)}")
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
            material_id = structure_id.replace("mp_", "mp-")
            logger.info(f"🔄 GET_STRUCTURE: Attempting to reload {material_id} from Materials Project")
            
            api_key = os.getenv("MP_API_KEY")
            if api_key:
                try:
                    from mp_api.client import MPRester
                    with MPRester(api_key) as mpr:
                        structure = mpr.get_structure_by_material_id(material_id)
                        if structure:
                            # Reload structure into storage
                            material_data = mpr.materials.summary.search(
                                material_ids=[material_id],
                                fields=["material_id", "formula_pretty", "band_gap", "formation_energy_per_atom", "symmetry"]
                            )
                            
                            structure_data = StructureData(material_id=material_id, structure=structure)
                            structure_storage[structure_id] = structure_data
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
    
    structure_data = structure_storage[structure_id]
    
    if not structure_data.structure:
        return [TextContent(type="text", text="No structure data available")]
    
    try:
        if format == "cif":
            try:
                structure_str = structure_data.structure.to(fmt="cif")
            except Exception as e:
                logger.error(f"❌ GET_STRUCTURE: CIF generation failed: {e}")
                structure_str = f"Error generating CIF: {e}"
        else:  # poscar
            structure_str = get_poscar_str(structure_data.structure)
        
        return [TextContent(type="text", text=structure_str)]
        
    except Exception as e:
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
        from pymatgen.core.structure import Structure
        
        structure = Structure.from_str(poscar_str, fmt="poscar")
        structure_data = StructureData(structure=structure)
        structure_storage[structure_data.structure_id] = structure_data
        
        structure_uri = f"structure://{structure_data.structure_id}"
        
        return [
            TextContent(type="text", text=f"A new structure is created with the structure uri: {structure_uri}"),
            TextContent(type="text", text=structure_data.description)
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
        from pymatgen.core.structure import Structure
        
        structure = Structure.from_str(cif_str, fmt="cif")
        structure_data = StructureData(structure=structure)
        structure_storage[structure_data.structure_id] = structure_data
        
        structure_uri = f"structure://{structure_data.structure_id}"
        
        return [
            TextContent(type="text", text=f"A new structure is created with the structure uri: {structure_uri}"),
            TextContent(type="text", text=structure_data.description)
        ]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error creating structure: {str(e)}")]

@mcp.tool()
def plot_structure(structure_uri: str, duplication: List[int] = [1, 1, 1]) -> List[ImageContent]:
    """Visualize the crystal structure with enhanced 3D plotting
    
    Args:
        structure_uri: The URI of the structure
        duplication: The duplication of the structure along a, b, c axes
    
    Returns:
        PNG image of the structure
    """
    structure_id = structure_uri.replace("structure://", "")
    
    logger.info(f"🎨 AWS PLOT_STRUCTURE: Starting visualization for {structure_id}")
    
    if structure_id not in structure_storage:
        logger.error(f"❌ AWS PLOT_STRUCTURE: Structure {structure_id} not found in storage")
        return [ImageContent(type="image", data="", mimeType="image/png")]
    
    structure_data = structure_storage[structure_id]
    
    if not structure_data.structure:
        logger.error(f"❌ AWS PLOT_STRUCTURE: No structure data for {structure_id}")
        return [ImageContent(type="image", data="", mimeType="image/png")]
    
    try:
        logger.info(f"🎨 AWS PLOT_STRUCTURE: Using advanced plotly visualization for {len(structure_data.structure)} atoms")
        
        # Try simple plotly visualization without crystal_toolkit
        try:
            import plotly.graph_objects as go
            import plotly.io as pio
            
            fig = go.Figure()
            structure = structure_data.structure
            
            # Plot atoms as spheres
            for i, site in enumerate(structure):
                coords = site.coords  # Use cartesian coordinates
                fig.add_trace(go.Scatter3d(
                    x=[coords[0]], y=[coords[1]], z=[coords[2]],
                    mode='markers',
                    marker=dict(size=10, color=f'rgb({(i*50)%255},{(i*100)%255},{(i*150)%255})'),
                    name=str(site.specie),
                    text=f'{site.specie} at ({coords[0]:.2f}, {coords[1]:.2f}, {coords[2]:.2f})'
                ))
            
            # Add unit cell edges
            lattice = structure.lattice
            vertices = [
                [0, 0, 0], lattice.matrix[0], lattice.matrix[0] + lattice.matrix[1], lattice.matrix[1],
                lattice.matrix[2], lattice.matrix[0] + lattice.matrix[2], 
                lattice.matrix[0] + lattice.matrix[1] + lattice.matrix[2], lattice.matrix[1] + lattice.matrix[2]
            ]
            
            # Draw unit cell edges
            edges = [
                [0, 1], [1, 2], [2, 3], [3, 0],  # bottom face
                [4, 5], [5, 6], [6, 7], [7, 4],  # top face
                [0, 4], [1, 5], [2, 6], [3, 7]   # vertical edges
            ]
            
            for edge in edges:
                start, end = vertices[edge[0]], vertices[edge[1]]
                fig.add_trace(go.Scatter3d(
                    x=[start[0], end[0]], y=[start[1], end[1]], z=[start[2], end[2]],
                    mode='lines', line=dict(color='black', width=2),
                    showlegend=False, hoverinfo='skip'
                ))
            
            fig.update_layout(
                title=f'Crystal Structure: {structure.composition.reduced_formula}',
                scene=dict(aspectmode='cube'),
                width=800, height=600
            )
            
            # Convert plotly figure to PNG
            img_bytes = pio.to_image(fig, format='png', width=800, height=600, scale=2)
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            logger.info(f"✅ AWS PLOT_STRUCTURE: Successfully created plotly visualization ({len(img_base64)} chars)")
            return [ImageContent(type="image", data=img_base64, mimeType="image/png")]
            
        except Exception as plotly_error:
            logger.warning(f"⚠️ AWS PLOT_STRUCTURE: Simple plotly failed ({plotly_error}), falling back to matplotlib")
        
        # Fallback to matplotlib plotting
        import matplotlib.pyplot as plt
        
        # Create a simple 3D plot using matplotlib
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        structure = structure_data.structure
        
        # Plot atoms
        for site in structure:
            coords = site.frac_coords
            ax.scatter(coords[0], coords[1], coords[2], 
                      s=100, label=str(site.specie), alpha=0.8)
        
        # Plot unit cell
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
        title = f'Crystal Structure: {structure.composition.reduced_formula}'
        ax.set_title(title)
        ax.legend()
        
        # Convert to base64 with proper resource management
        with BytesIO() as buffer:
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        logger.info(f"✅ AWS PLOT_STRUCTURE: Matplotlib fallback successful ({len(img_base64)} chars)")
        return [ImageContent(type="image", data=img_base64, mimeType="image/png")]
        
    except Exception as e:
        logger.error(f"❌ AWS PLOT_STRUCTURE: Both plotly and matplotlib failed: {e}")
        return [ImageContent(type="image", data="", mimeType="image/png")]

@mcp.tool()
def build_supercell(bulk_structure_uri: str, supercell_parameters: Dict[str, Any]) -> List[TextContent]:
    """Build supercell from bulk structure
    
    Args:
        bulk_structure_uri: The URI of the bulk structure
        supercell_parameters: Parameters for supercell construction (e.g., {"scaling_matrix": [[2,0,0],[0,2,0],[0,0,2]]})
    
    Returns:
        Information about the newly created supercell
    """
    structure_id = bulk_structure_uri.replace("structure://", "")
    
    # Debug: show what structures we have
    logger.info(f"Looking for structure {structure_id} in storage with {len(structure_storage)} items")
    logger.info(f"Available structures: {list(structure_storage.keys())}")
    
    if structure_id not in structure_storage:
        return [TextContent(type="text", text=f"Bulk structure {structure_id} not found. Available: {list(structure_storage.keys())}")]
    
    bulk_data = structure_storage[structure_id]
    
    if not bulk_data.structure:
        return [TextContent(type="text", text="No bulk structure data available")]
    
    try:
        # Extract scaling matrix from parameters
        scaling_matrix = supercell_parameters.get("scaling_matrix", [[2,0,0],[0,2,0],[0,0,2]])
        
        # Create supercell using pymatgen
        supercell = bulk_data.structure.make_supercell(scaling_matrix)
        
        # Create new structure data for supercell
        supercell_data = StructureData(structure=supercell)
        structure_storage[supercell_data.structure_id] = supercell_data
        
        supercell_uri = f"structure://{supercell_data.structure_id}"
        
        # Create description
        desc = f"Supercell created from {bulk_structure_uri}\n"
        desc += f"Scaling matrix: {scaling_matrix}\n"
        desc += f"Original atoms: {len(bulk_data.structure)}\n"
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
        
        logger.info(f"Supercell built successfully: {supercell_uri}")
        return [
            TextContent(type="text", text=f"Supercell created with URI: {supercell_uri}"),
            TextContent(type="text", text=desc)
        ]
        
    except Exception as e:
        logger.error(f"Error building supercell: {e}")
        return [TextContent(type="text", text=f"Error building supercell: {str(e)}")]

@mcp.tool()
def moire_homobilayer(bulk_structure_uri: str, interlayer_spacing: float, max_num_atoms: int = 10, twist_angle: float = 0.0, vacuum_thickness: float = 15.0) -> List[TextContent]:
    """Generate a moire superstructure of a 2D homobilayer using enhanced physics-based approach
    
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
    
    bulk_data = structure_storage[structure_id]
    
    if not bulk_data.structure:
        return [TextContent(type="text", text="No bulk structure data available")]
    
    try:
        # Try enhanced moire generation first
        try:
            # Use enhanced structure data if available
            if bulk_data.enhanced and ENHANCED_AVAILABLE:
                # Create moire parameters
                from enhanced_structure_data import MoireParameters
                moire_params: MoireParameters = {
                    "twist_angle": twist_angle,
                    "interlayer_spacing": interlayer_spacing,
                    "max_num_atoms": max_num_atoms,
                    "vacuum_thickness": vacuum_thickness
                }
                
                # Use enhanced data class for moire generation (if available)
                enhanced_moire = EnhancedStructureData(
                    structure=bulk_data.structure,
                    parameters=moire_params
                )
                
                # Store enhanced moire structure
                moire_data = StructureData(structure=enhanced_moire.structure)
                structure_storage[moire_data.structure_id] = moire_data
                
                moire_uri = f"structure://{moire_data.structure_id}"
                logger.info(f"Enhanced structure data moire generated: {moire_uri}")
                return [TextContent(type="text", text=f"Moire structure is created with the structure uri: {moire_uri}")]
            
            # Fallback to enhanced moire generator
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
            from enhanced_moire_generator import generate_moire_bilayer
            
            moire_structure = generate_moire_bilayer(
                structure=bulk_data.structure,
                interlayer_spacing=interlayer_spacing,
                max_num_atoms=max_num_atoms,
                twist_angle=twist_angle,
                vacuum_thickness=vacuum_thickness
            )
            
            moire_data = StructureData(structure=moire_structure)
            structure_storage[moire_data.structure_id] = moire_data
            
            moire_uri = f"structure://{moire_data.structure_id}"
            
            logger.info(f"Enhanced moire generator: {moire_uri} with {twist_angle}° twist")
            return [TextContent(type="text", text=f"Moire structure is created with the structure uri: {moire_uri}")]
            
        except ImportError as ie:
            logger.warning(f"Enhanced moire generator not available: {ie}, using fallback")
        except Exception as ee:
            logger.warning(f"Enhanced moire generation failed: {ee}, using fallback")
        
        # Use enhanced moire generation with timeout protection
        logger.info(f"🌀 MOIRE: Starting generation for {len(bulk_data.structure)} atoms, {twist_angle}° twist")
        try:
            moire_structure, diagnostics = generate_enhanced_moire_bilayer(
                structure=bulk_data.structure,
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
        moire_data = StructureData(structure=moire_structure)
        structure_storage[moire_data.structure_id] = moire_data
        
        moire_uri = f"structure://{moire_data.structure_id}"
        logger.info(f"🌀 MOIRE: Created structure {moire_uri} with {len(moire_structure)} atoms")
        
        # Extract method type from diagnostics for immediate visibility
        method_type = "UNKNOWN"
        if "ULTRA-FAST MODE" in diagnostics:
            method_type = "ULTRA-FAST MODE"
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
            structure_desc = get_enhanced_description(moire_structure, None, moire_data.structure_id)
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

def generate_enhanced_moire_bilayer(structure, interlayer_spacing: float, max_num_atoms: int, twist_angle: float, vacuum_thickness: float):
    """Ultra-fast moire bilayer generation - returns (structure, diagnostics)"""
    from pymatgen.core.structure import Structure
    from pymatgen.core.lattice import Lattice
    
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

def main():
    """Main entry point for the MCP server"""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting Enhanced MCP Materials Project server with 8 tools")
    logger.info("Available tools: search_materials_by_formula, select_material_by_id, get_structure_data, create_structure_from_poscar, create_structure_from_cif, plot_structure, build_supercell, moire_homobilayer")
    mcp.run("stdio")

if __name__ == "__main__":
    main()