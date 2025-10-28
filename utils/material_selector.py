# Universal material selection for correct phase matching
from typing import List, Dict, Any, Optional
import re

def select_best_material_match(search_results: List[str], formula: str) -> Optional[str]:
    """Select the best material structure match using universal criteria"""
    
    materials = [parse_material_result(result) for result in search_results]
    materials = [m for m in materials if m]  # Filter None results
    
    if not materials:
        return None
    
    # Known stable phases for common materials
    preferred_phases = {
        "Si": {"space_groups": ["Fd-3m", "227"], "crystal_system": "Cubic"},
        "C": {"space_groups": ["Fd-3m", "227"], "crystal_system": "Cubic"},  # Diamond
        "Ge": {"space_groups": ["Fd-3m", "227"], "crystal_system": "Cubic"},
        "GaAs": {"space_groups": ["F-43m", "216"], "crystal_system": "Cubic"},
        "TiO2": {"space_groups": ["P42/mnm", "136"], "crystal_system": "Tetragonal"},  # Rutile
        "Al2O3": {"space_groups": ["R-3c", "167"], "crystal_system": "Trigonal"},  # Corundum
    }
    
    # Priority 1: Known preferred phase
    if formula in preferred_phases:
        pref = preferred_phases[formula]
        for material in materials:
            sg = material.get("space_group", "")
            if any(target_sg in sg for target_sg in pref["space_groups"]):
                return material["material_id"]
        
        # Priority 2: Preferred crystal system
        for material in materials:
            cs = material.get("crystal_system", "")
            if pref["crystal_system"] in cs:
                return material["material_id"]
    
    # Priority 3: Most stable (lowest formation energy)
    stable_materials = [m for m in materials if m.get("formation_energy") is not None]
    if stable_materials:
        most_stable = min(stable_materials, key=lambda x: x["formation_energy"])
        return most_stable["material_id"]
    
    # Priority 4: Highest symmetry (prefer cubic > tetragonal > orthorhombic > triclinic)
    symmetry_order = ["Cubic", "Tetragonal", "Hexagonal", "Trigonal", "Orthorhombic", "Monoclinic", "Triclinic"]
    for preferred_system in symmetry_order:
        for material in materials:
            if preferred_system in material.get("crystal_system", ""):
                return material["material_id"]
    
    # Fallback: First result
    return materials[0]["material_id"]

def parse_material_result(result_text: str) -> Optional[Dict[str, Any]]:
    """Parse a single material result string"""
    try:
        data = {}
        
        # Extract material ID
        id_match = re.search(r"Material ID: (mp-\d+)", result_text)
        if id_match:
            data["material_id"] = id_match.group(1)
        
        # Extract space group
        sg_match = re.search(r"Space Group: ([^\n]+)", result_text)
        if sg_match:
            data["space_group"] = sg_match.group(1).strip()
        
        # Extract crystal system
        cs_match = re.search(r"Crystal System: ([^\n]+)", result_text)
        if cs_match:
            data["crystal_system"] = cs_match.group(1).strip()
        
        # Extract formation energy
        fe_match = re.search(r"Formation Energy: ([\-\d\.]+)", result_text)
        if fe_match:
            data["formation_energy"] = float(fe_match.group(1))
        
        return data if "material_id" in data else None
        
    except Exception:
        return None

def get_known_stable_phase(formula: str, mp_client) -> Optional[Dict[str, Any]]:
    """Get known stable phase for common materials"""
    
    # Known stable MP IDs for common materials
    stable_phases = {
        "Si": "mp-149",      # Diamond silicon
        "C": "mp-66",       # Diamond carbon
        "Ge": "mp-32",      # Diamond germanium
        "GaAs": "mp-2534",  # Zinc blende GaAs
        "TiO2": "mp-2657",  # Rutile TiO2
        "Al2O3": "mp-1143", # Corundum Al2O3
        "SiO2": "mp-6930",  # Quartz SiO2
    }
    
    if formula in stable_phases:
        try:
            result = mp_client.get_material_by_id(stable_phases[formula])
            if result:
                return result
        except Exception:
            pass
    
    return None