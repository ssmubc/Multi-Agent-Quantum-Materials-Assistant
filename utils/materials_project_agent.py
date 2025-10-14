import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Try to import mp-api
try:
    from mp_api.client import MPRester
    MPAPI_AVAILABLE = True
except ImportError:
    MPRester = None
    MPAPI_AVAILABLE = False

class MaterialsProjectAgent:
    """
    Materials Project API agent with fallback to dummy data
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MP_API_KEY")
        self.available = MPAPI_AVAILABLE and bool(self.api_key)
        
        if not MPAPI_AVAILABLE:
            logger.warning("mp-api not installed; using dummy responses")
        elif not self.api_key:
            logger.warning("No MP_API_KEY found; using dummy responses")
        else:
            logger.info("MaterialsProjectAgent using real mp-api")
    
    def _extract_geometry_from_doc(self, doc) -> Optional[str]:
        """Extract geometry string from Materials Project document"""
        try:
            if getattr(doc, "structure", None):
                return "\n".join(
                    f"{site.specie} {site.x:.6f} {site.y:.6f} {site.z:.6f}"
                    for site in doc.structure.sites
                )
        except Exception:
            logger.debug("Failed extracting geometry", exc_info=True)
        return None
    
    def search(self, query: str) -> Dict[str, Any]:
        """
        Search Materials Project database
        Returns structured dict with material properties
        """
        logger.info(f"Searching Materials Project for: {query}")
        
        if not self.available:
            # Return dummy data for common materials
            dummy_data = {
                "H2": {
                    "material_id": None,
                    "formula": "H2",
                    "band_gap": 0.0,
                    "formation_energy": 0.0,
                    "structure": None,
                    "geometry": "H 0 0 0\nH 0 0 0.735"
                },
                "LiH": {
                    "material_id": None,
                    "formula": "LiH", 
                    "band_gap": 4.5,
                    "formation_energy": -0.9,
                    "structure": None,
                    "geometry": "Li 0 0 0\nH 0 0 1.595"
                },
                "TiO2": {
                    "material_id": None,
                    "formula": "TiO2",
                    "band_gap": 3.2,
                    "formation_energy": -9.7,
                    "structure": None,
                    "geometry": "Ti 0 0 0\nO 1.59 0 0\nO -1.59 0 0"
                }
            }
            
            return dummy_data.get(query, {
                "material_id": None,
                "formula": query,
                "band_gap": 2.0,
                "formation_energy": -3.0,
                "structure": None,
                "geometry": None
            })
        
        # Real MP API call
        try:
            with MPRester(self.api_key) as mpr:
                if query.lower().startswith("mp-"):
                    # Material ID search
                    docs = mpr.materials.summary.search(
                        material_ids=[query],
                        fields=["material_id", "formula_pretty", "band_gap", 
                               "energy_above_hull", "structure"]
                    )
                else:
                    # Formula search
                    docs = mpr.materials.summary.search(
                        formula=query,
                        fields=["material_id", "formula_pretty", "band_gap",
                               "energy_above_hull", "structure"]
                    )
                
                if not docs:
                    return {"error": f"No materials found for '{query}'"}
                
                doc = docs[0]
                return {
                    "material_id": getattr(doc, "material_id", None),
                    "formula": getattr(doc, "formula_pretty", query),
                    "band_gap": getattr(doc, "band_gap", None),
                    "formation_energy": getattr(doc, "energy_above_hull", None),
                    "structure": getattr(doc, "structure", None),
                    "geometry": self._extract_geometry_from_doc(doc)
                }
                
        except Exception as e:
            logger.error(f"Materials Project API error: {e}")
            return {"error": f"Error querying Materials Project: {e}"}