# MCP Materials Project Server Test Prompts

## Test Prompt 1: Search Materials by Formula
**Tests**: `search_materials_by_formula` tool
```
Search for silicon dioxide materials in the Materials Project database and show me the available options.
```

## Test Prompt 2: Get Material by ID  
**Tests**: `select_material_by_id` tool
```
Get detailed information about material mp-149 including its structure and properties.
```

## Test Prompt 3: Get Structure Data
**Tests**: `get_structure_data` tool  
```
Generate a VQE ansatz for mp-149 and show me the POSCAR structure file format.
```

## Test Prompt 4: Create Structure from POSCAR
**Tests**: `create_structure_from_poscar` tool
```
Create a quantum simulation for this POSCAR structure:
Si
1.0
3.867 0.000 0.000
0.000 3.867 0.000  
0.000 0.000 3.867
Si
2
Direct
0.000 0.000 0.000
0.250 0.250 0.250
```

## Test Prompt 5: Plot Structure Visualization
**Tests**: `plot_structure` tool
```
Generate a VQE circuit for mp-149 and show me a 3D visualization of the crystal structure.
```

## Test Prompt 6: Build Supercell
**Tests**: `build_supercell` tool
```
Create a 2x2x2 supercell from mp-149 for quantum simulation and generate the corresponding VQE ansatz.
```

## Expected Streamlit Logs

For each test, you should see logs like:
- 🔍 **MCP Tool X**: [Tool description]
- 📋 Raw MCP response: [Response details]
- ✅ **Tool result**: [Success message]
- 📊 **Final structured data for LLM**: [Data passed to model]

## Verification Checklist

- [ ] Tool 1: Formula search returns material list
- [ ] Tool 2: Material ID returns structured data with band_gap, formation_energy
- [ ] Tool 3: Structure data returns POSCAR/CIF content
- [ ] Tool 4: POSCAR creation returns new structure URI
- [ ] Tool 5: Plot returns base64 image data
- [ ] Tool 6: Supercell returns new supercell URI

## Debug Tips

If any tool fails:
1. Check MCP server is running (look for "🚀 MCP SERVER: Starting...")
2. Verify Materials Project API key is set
3. Check tool response format in logs
4. Ensure structure URIs are valid format: `structure://[id]`