from setuptools import setup, find_packages

setup(
    name="enhanced_mcp_materials",
    version="1.0.0",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "mcp",
        "pymatgen", 
        "mp-api",
        "matplotlib",
        "numpy"
    ],
    description="Enhanced MCP Materials Project server",
    entry_points={
        "console_scripts": [
            "enhanced-mcp-materials=enhanced_mcp_materials.server:main",
        ],
    },
)