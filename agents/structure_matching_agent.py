# Structure Matching Agent for AWS Strands
from typing import Dict, Any, Optional
import logging
from pymatgen.core import Structure
from pymatgen.analysis.structure_matcher import StructureMatcher

logger = logging.getLogger(__name__)

class StructureMatchingAgent:
    """Agent responsible for matching POSCAR structures to Materials Project entries"""
    
    def __init__(self, mp_agent):
        self.mp_agent = mp_agent
        self.matcher = StructureMatcher(ltol=0.2, stol=0.3, angle_tol=5)
    
    def match_poscar_to_mp(self, poscar_text: str, formula: str) -> Optional[Dict[str, Any]]:
        """Match POSCAR structure to correct Materials Project entry"""
        try:
            # Parse POSCAR structure
            input_structure = Structure.from_str(poscar_text, fmt="poscar")
            input_primitive = input_structure.get_primitive_structure()
            
            logger.info(f"🔍 STRUCTURE AGENT: Matching POSCAR for {formula}")
            
            # Get all MP structures for formula
            search_results = self.mp_agent.client.search_materials(formula)
            
            best_match = None
            best_score = 0
            
            for result_text in search_results:
                # Extract material ID
                import re
                mp_match = re.search(r"Material ID: (mp-\d+)", result_text)
                if not mp_match:
                    continue
                    
                material_id = mp_match.group(1)
                
                # Get MP structure
                mp_data = self.mp_agent.client.get_material_by_id(material_id)
                if not mp_data or not mp_data.get("structure_uri"):
                    continue
                
                # Get POSCAR from MP
                mp_poscar = self.mp_agent.client.get_structure_data(mp_data["structure_uri"], "poscar")
                if not mp_poscar:
                    continue
                
                try:
                    mp_structure = Structure.from_str(mp_poscar, fmt="poscar")
                    mp_primitive = mp_structure.get_primitive_structure()
                    
                    # Check if structures match
                    if self.matcher.fit(input_primitive, mp_primitive):
                        # Calculate match quality score
                        rms_dist = self.matcher.get_rms_dist(input_primitive, mp_primitive)
                        score = 1.0 / (1.0 + rms_dist[0]) if rms_dist else 0
                        
                        if score > best_score:
                            best_score = score
                            best_match = {
                                "material_id": material_id,
                                "match_score": score,
                                "rms_distance": rms_dist[0] if rms_dist else None,
                                "mp_data": mp_data
                            }
                            
                except Exception as e:
                    logger.warning(f"⚠️ STRUCTURE AGENT: Failed to parse MP structure {material_id}: {e}")
                    continue
            
            if best_match:
                logger.info(f"✅ STRUCTURE AGENT: Found match {best_match['material_id']} (score: {best_match['match_score']:.3f})")
                return best_match
            else:
                logger.warning(f"❌ STRUCTURE AGENT: No structural match found for {formula}")
                return None
                
        except Exception as e:
            logger.error(f"💥 STRUCTURE AGENT: Structure matching failed: {e}")
            return None