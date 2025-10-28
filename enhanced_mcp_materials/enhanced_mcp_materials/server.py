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

# In-memory structure storage (simplified version of the official server's approach)
structure_storage = {}

class StructureData:
    """Simplified structure data class"""
    
    def __init__(self, material_id: str = None, structure: Structure = None):
        self.material_id = material_id
        self.structure = structure
        self.structure_id = self._generate_id()
        
    def _generate_id(self) -> str:
        """Generate unique structure ID"""
        if self.material_id:
            return f"mp_{self.material_id}"
        else:
            # Generate hash from structure
            content = str(self.structure) if self.structure else "unknown"
            return hashlib.md5(content.encode()).hexdigest()[:8]
    
    @property
    def description(self) -> str:
        """Get structure description"""
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
        """Get POSCAR string"""
        if self.structure:
            return self.structure.to(fmt="poscar")
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
        with MPRester(api_key) as mpr:
            results = mpr.materials.summary.search(
                formula=chemical_formula, 
                fields=["material_id", "formula_pretty", "band_gap", "formation_energy_per_atom", "symmetry"]
            )
            
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
        with MPRester(api_key) as mpr:
            # Get both structure and material properties
            structure = mpr.get_structure_by_material_id(material_id)
            if not structure:
                return [TextContent(type="text", text=f"Material not found: {material_id}")]
            
            # Get material properties
            material_data = mpr.materials.summary.search(
                material_ids=[material_id],
                fields=["material_id", "formula_pretty", "band_gap", "formation_energy_per_atom", "symmetry"]
            )
            
            # Create enhanced description with properties
            desc = f"Structure ID: mp_{material_id}\n"
            desc += f"Formula: {structure.composition.reduced_formula}\n"
            desc += f"Crystal Structure: {structure.get_space_group_info()[1]}\n"
            desc += f"Space Group: {structure.get_space_group_info()[0]}\n"
            
            # Add materials project data if available
            if material_data:
                mat = material_data[0]
                if hasattr(mat, 'band_gap') and mat.band_gap is not None:
                    desc += f"Band Gap: {mat.band_gap:.3f} eV\n"
                if hasattr(mat, 'formation_energy_per_atom') and mat.formation_energy_per_atom is not None:
                    desc += f"Formation Energy: {mat.formation_energy_per_atom:.3f} eV/atom\n"
                if hasattr(mat, 'symmetry') and mat.symmetry and hasattr(mat.symmetry, 'crystal_system'):
                    desc += f"Crystal System: {mat.symmetry.crystal_system}\n"
            
            desc += f"Lattice: a={structure.lattice.a:.3f}, b={structure.lattice.b:.3f}, c={structure.lattice.c:.3f}\n"
            desc += f"Number of atoms: {len(structure)}"
            
            # Create structure data
            structure_data = StructureData(material_id=material_id, structure=structure)
            structure_storage[structure_data.structure_id] = structure_data
            
            structure_uri = f"structure://{structure_data.structure_id}"
            
            return [
                TextContent(type="text", text=desc),
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
    
    if structure_id not in structure_storage:
        return [TextContent(type="text", text="Structure not found")]
    
    structure_data = structure_storage[structure_id]
    
    if not structure_data.structure:
        return [TextContent(type="text", text="No structure data available")]
    
    try:
        if format == "cif":
            structure_str = structure_data.structure.to(fmt="cif")
        else:  # poscar
            structure_str = structure_data.poscar_str
        
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
    
    structure_data = structure_storage[structure_id]
    
    if not structure_data.structure:
        return [ImageContent(type="image", data="", mimeType="image/png")]
    
    try:
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
    """Build supercell from bulk structure
    
    Args:
        bulk_structure_uri: The URI of the bulk structure
        supercell_parameters: Parameters for supercell construction (e.g., {"scaling_matrix": [[2,0,0],[0,2,0],[0,0,2]]})
    
    Returns:
        Information about the newly created supercell
    """
    structure_id = bulk_structure_uri.replace("structure://", "")
    
    if structure_id not in structure_storage:
        return [TextContent(type="text", text="Bulk structure not found")]
    
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
        
        return [
            TextContent(type="text", text=f"Supercell created with URI: {supercell_uri}"),
            TextContent(type="text", text=desc)
        ]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error building supercell: {str(e)}")]

@mcp.tool()
def moire_homobilayer(bulk_structure_uri: str, interlayer_spacing: float, max_num_atoms: int = 10, twist_angle: float = 0.0, vacuum_thickness: float = 15.0) -> List[TextContent]:
    """Generate a moire superstructure of a 2D homobilayer
    
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
        # Simplified moire bilayer generation
        bulk_structure = bulk_data.structure
        
        # Create two layers with twist
        import numpy as np
        
        # Get the original structure
        layer1 = bulk_structure.copy()
        layer2 = bulk_structure.copy()
        
        # Apply twist to second layer (rotation around z-axis)
        angle_rad = np.radians(twist_angle)
        rotation_matrix = np.array([
            [np.cos(angle_rad), -np.sin(angle_rad), 0],
            [np.sin(angle_rad), np.cos(angle_rad), 0],
            [0, 0, 1]
        ])
        
        # Rotate layer2 coordinates
        for i, site in enumerate(layer2):
            new_coords = np.dot(rotation_matrix, site.coords)
            layer2[i] = site.specie, new_coords
        
        # Shift layer2 up by interlayer_spacing
        layer2.translate_sites(range(len(layer2)), [0, 0, interlayer_spacing])
        
        # Combine layers
        moire_sites = list(layer1.sites) + list(layer2.sites)
        
        # Limit number of atoms
        if len(moire_sites) > max_num_atoms:
            moire_sites = moire_sites[:max_num_atoms]
        
        # Create new lattice with vacuum
        old_lattice = layer1.lattice
        new_lattice_matrix = old_lattice.matrix.copy()
        new_lattice_matrix[2, 2] = old_lattice.c + interlayer_spacing + vacuum_thickness
        new_lattice = Lattice(new_lattice_matrix)
        
        # Create moire structure
        moire_structure = Structure(new_lattice, [site.specie for site in moire_sites], [site.frac_coords for site in moire_sites])
        
        # Store the moire structure
        moire_data = StructureData(structure=moire_structure)
        structure_storage[moire_data.structure_id] = moire_data
        
        moire_uri = f"structure://{moire_data.structure_id}"
        
        return [TextContent(type="text", text=f"Moire structure is created with the structure uri: {moire_uri}")]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error generating moire bilayer: {str(e)}")]

def main():
    """Main entry point for the MCP server"""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting Enhanced MCP Materials Project server with 8 tools")
    logger.info("Available tools: search_materials_by_formula, select_material_by_id, get_structure_data, create_structure_from_poscar, create_structure_from_cif, plot_structure, build_supercell, moire_homobilayer")
    mcp.run("stdio")