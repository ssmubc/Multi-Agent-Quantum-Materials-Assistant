import streamlit as st
import os
import json
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import traceback
import base64
from io import BytesIO

# Import authentication
from auth_module import require_auth

# Import our model classes
from models.nova_pro_model import NovaProModel
from models.llama4_model import Llama4Model
from models.llama3_model import Llama3Model
from models.openai_model import OpenAIModel
from models.qwen_model import QwenModel
from models.deepseek_model import DeepSeekModel
from models.claude_opus_model import ClaudeOpusModel

from utils.materials_project_agent import MaterialsProjectAgent
from utils.enhanced_mcp_client import EnhancedMCPAgent
from utils.secrets_manager import get_mp_api_key
from utils.logging_display import setup_logging_display, display_mcp_logs
from demo_mode import get_demo_response
from agents.strands_supervisor import StrandsSupervisorAgent
from agents.strands_coordinator import StrandsCoordinator
from agents.strands_dft_agent import StrandsDFTAgent
from agents.strands_structure_agent import StrandsStructureAgent
from agents.strands_agentic_loop import StrandsAgenticLoop

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Print startup message to console
print("\n" + "="*60)
print("🚀 QUANTUM MATTER STREAMLIT APP STARTING")
print("📋 MCP logging is enabled - watch for [MCP LOG] messages")
print("="*60 + "\n")

# Page configuration
st.set_page_config(
    page_title="Quantum Matter LLM Testing Platform",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set default AWS region for App Runner
if not os.environ.get('AWS_DEFAULT_REGION'):
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .model-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #f9f9f9;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'models_initialized' not in st.session_state:
        st.session_state.models_initialized = False
    if 'mp_agent' not in st.session_state:
        st.session_state.mp_agent = None
    if 'models' not in st.session_state:
        st.session_state.models = {}
    if 'aws_configured' not in st.session_state:
        st.session_state.aws_configured = False
    if 'strands_supervisor' not in st.session_state:
        st.session_state.strands_supervisor = None
    if 'strands_agents' not in st.session_state:
        st.session_state.strands_agents = {}


def check_aws_credentials():
    """Check if AWS credentials are available"""
    try:
        # Try multiple credential sources
        session = boto3.Session()
        
        # Check for credentials
        credentials = session.get_credentials()
        if credentials is None:
            return False, "No AWS credentials found"
        
        # Test actual access with STS call
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        # Determine credential source
        profile_name = session.profile_name or "default"
        if 'assumed-role' in identity.get('Arn', ''):
            source = f"IAM Role (App Runner)"
        elif os.environ.get('AWS_PROFILE'):
            source = f"AWS Profile '{os.environ.get('AWS_PROFILE')}'"
        elif profile_name != "default":
            source = f"AWS Profile '{profile_name}'"
        elif os.environ.get('AWS_ACCESS_KEY_ID'):
            source = "Environment variables"
        else:
            source = "AWS credentials"
            
        return True, f"{source} configured successfully"
        
    except NoCredentialsError:
        return False, "AWS credentials not configured"
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'TokenRefreshRequired':
            return False, "SSO token expired - run 'aws sso login'"
        elif error_code == 'UnauthorizedOperation':
            return False, "AWS credentials found but insufficient permissions"
        else:
            return False, f"AWS credential error: {error_code}"
    except Exception as e:
        error_msg = str(e)
        if 'SSO' in error_msg or 'sso' in error_msg:
            return False, "SSO token expired or invalid - run 'aws sso login'"
        return False, f"AWS credential error: {error_msg}"

def setup_materials_project():
    """Setup Materials Project API"""
    st.sidebar.subheader("🔬 Materials Project API")
    
    # Option 1: Use MCP Materials Project server
    use_mcp = st.sidebar.checkbox(
        "Use MCP Materials Project Server",
        help="Use advanced MCP server for Materials Project access"
    )
    
    # Option 2: Use AWS Secrets Manager
    use_secrets_manager = st.sidebar.checkbox(
        "Use AWS Secrets Manager for MP API Key",
        help="Retrieve MP API key from AWS Secrets Manager"
    )
    
    mp_api_key = None
    
    if use_secrets_manager:
        if st.session_state.aws_configured:
            try:
                mp_api_key = get_mp_api_key()
                if mp_api_key:
                    st.sidebar.success("✅ MP API key retrieved from Secrets Manager")
                else:
                    st.sidebar.error("❌ Failed to retrieve MP API key from Secrets Manager")
            except Exception as e:
                st.sidebar.error(f"❌ Secrets Manager error: {str(e)}")
        else:
            st.sidebar.warning("⚠️ AWS credentials required for Secrets Manager")
    
    # Option 2: Manual input
    if not mp_api_key:
        mp_api_key = st.sidebar.text_input(
            "Materials Project API Key",
            type="password",
            help="Get your API key from https://materialsproject.org/",
            placeholder="Enter your MP API key..."
        )
    
    if mp_api_key:
        try:
            if use_mcp:
                logger.info("🚀 STREAMLIT: Initializing Enhanced MCP Materials Project Agent")
                st.session_state.mp_agent = EnhancedMCPAgent(api_key=mp_api_key)
                st.sidebar.success("✅ Enhanced MCP Materials Project server configured")
                logger.info("✅ STREAMLIT: Enhanced MCP Agent initialized successfully")
            else:
                logger.info("🔧 STREAMLIT: Initializing standard Materials Project Agent")
                st.session_state.mp_agent = MaterialsProjectAgent(api_key=mp_api_key)
                st.sidebar.success("✅ Materials Project API configured")
                logger.info("✅ STREAMLIT: Standard MP Agent initialized successfully")
            
            # Auto-store manually entered key to Secrets Manager
            if st.session_state.aws_configured and not use_secrets_manager:
                from utils.secrets_manager import store_mp_api_key
                if store_mp_api_key(mp_api_key):
                    st.sidebar.info("💾 API key saved to AWS Secrets Manager for future use")
            
            return True
        except Exception as e:
            st.sidebar.error(f"❌ MP API error: {str(e)}")
            return False
    else:
        st.sidebar.info("ℹ️ MP API key required for material lookups")
        return False

def initialize_models():
    """Initialize all LLM models"""
    # Check if we need to reinitialize due to MP agent change
    current_mp_agent = st.session_state.mp_agent
    if (st.session_state.models_initialized and 
        hasattr(st.session_state, 'last_mp_agent') and 
        st.session_state.last_mp_agent == current_mp_agent):
        return
    
    logger.info(f"🔄 STREAMLIT: Initializing models with MP agent: {type(current_mp_agent)}")
    st.session_state.last_mp_agent = current_mp_agent
    
    st.session_state.models = {}
    
    # Model configurations with regions
    model_configs = {
        "Nova Pro": {
            "class": NovaProModel,
            "region": "us-east-1",
            "model_id": "amazon.nova-pro-v1:0"
        },
        "Llama 4 Scout": {
            "class": Llama4Model,
            "region": "us-east-1", 
            "model_id": "us.meta.llama4-scout-17b-instruct-v1:0"
        },
        "Llama 3 70B": {
            "class": Llama3Model,
            "region": "us-west-2",
            "model_id": "meta.llama3-70b-instruct-v1:0"
        },
        "OpenAI GPT": {
            "class": OpenAIModel,
            "region": "us-west-2",
            "model_id": "openai.gpt-oss-20b-1:0"
        },
        "Qwen 3-32B": {
            "class": QwenModel,
            "region": "us-east-1",
            "model_id": "qwen.qwen3-32b-v1:0"
        },
        "DeepSeek R1": {
            "class": DeepSeekModel,
            "region": "us-east-1",
            "model_id": "us.deepseek.r1-v1:0"
        },
        "Claude Opus 4.1": {
            "class": ClaudeOpusModel,
            "region": "us-east-1",
            "model_id": "us.anthropic.claude-opus-4-1-20250805-v1:0"
        },

    }
    
    # Initialize each model
    for model_name, config in model_configs.items():
        try:
            model_instance = config["class"](
                mp_agent=st.session_state.mp_agent,
                region_name=config["region"]
            )
            model_instance.set_model(config["model_id"])
            st.session_state.models[model_name] = {
                "instance": model_instance,
                "config": config,
                "status": "ready"
            }
        except Exception as e:
            st.session_state.models[model_name] = {
                "instance": None,
                "config": config,
                "status": f"error: {str(e)}"
            }
    
    st.session_state.models_initialized = True

def display_model_status():
    """Display status of all models"""
    st.sidebar.subheader("🤖 Model Status")
    
    for model_name, model_info in st.session_state.models.items():
        config = model_info["config"]
        status = model_info["status"]
        
        with st.sidebar.expander(f"{model_name} ({config['region']})"):
            st.write(f"**Model ID:** `{config['model_id']}`")
            st.write(f"**Region:** `{config['region']}`")
            
            if status == "ready":
                st.markdown('<p class="status-success">✅ Ready</p>', unsafe_allow_html=True)
            else:
                st.markdown(f'<p class="status-error">❌ {status}</p>', unsafe_allow_html=True)

def main():
    """Main application"""
    # Check authentication first
    if not require_auth():
        return
    
    # Setup logging display
    setup_logging_display()
    
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">⚛️ Quantum Matter LLM Testing Platform</h1>', unsafe_allow_html=True)
    
    # Sidebar configuration
    st.sidebar.title("🔧 Configuration")
    
    # AWS Credentials Check
    st.sidebar.subheader("☁️ AWS Configuration")
    aws_status, aws_message = check_aws_credentials()
    st.session_state.aws_configured = aws_status
    
    if aws_status:
        st.sidebar.success(f"✅ {aws_message}")
    else:
        st.sidebar.error(f"❌ {aws_message}")
        if 'SSO' in aws_message or 'sso' in aws_message:
            st.sidebar.warning("💡 Run `aws sso login` to refresh your SSO token")
        else:
            st.sidebar.info("💡 Configure AWS credentials using SSO, AWS CLI, environment variables, or IAM roles")
    

    # Materials Project Setup
    mp_configured = setup_materials_project()
    
    # Show MCP status in sidebar
    if st.session_state.mp_agent:
        st.sidebar.subheader("🔬 MCP Status")
        if isinstance(st.session_state.mp_agent, EnhancedMCPAgent):
            st.sidebar.success("✅ Enhanced MCP Server Active")
            st.sidebar.info("📊 Advanced Materials Project features available")
            
            # Show recent MCP activity
            with st.sidebar.expander("🔍 Recent MCP Activity"):
                handler = setup_logging_display()
                mcp_logs = handler.get_mcp_logs()
                
                if mcp_logs:
                    # Show last 3 MCP logs
                    for log in reversed(mcp_logs[-3:]):
                        if '✅' in log['message'] or '🚀' in log['message']:
                            st.success(log['message'])
                        elif '❌' in log['message'] or '💥' in log['message']:
                            st.error(log['message'])
                        else:
                            st.info(log['message'])
                else:
                    st.info("No MCP activity yet")
                
                # Test MCP button
                if st.button("🧪 Test MCP", help="Test MCP server with mp-149 (Silicon)"):
                    if isinstance(st.session_state.mp_agent, EnhancedMCPAgent):
                        try:
                            result = st.session_state.mp_agent.search("mp-149")
                            if result and 'error' not in result:
                                st.success(f"MCP Test Success: {result.get('material_id', 'Found material')}")
                            else:
                                st.error(f"MCP Test Failed: {result.get('error', 'Unknown error')}")
                        except Exception as e:
                            st.error(f"MCP Test Error: {str(e)}")
                    else:
                        st.warning("MCP server not active")
        else:
            st.sidebar.info("🔧 Standard MP API Active")
            st.sidebar.warning("⚠️ Limited to basic MP features")
            
            # Test standard API button
            with st.sidebar.expander("🔍 Test Standard API"):
                if st.button("🧪 Test API", help="Test standard MP API with mp-149"):
                    try:
                        result = st.session_state.mp_agent.search("mp-149")
                        if result and 'error' not in result:
                            st.success("Standard API Test Success")
                        else:
                            st.error(f"API Test Failed: {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"API Test Error: {str(e)}")
    
    # Initialize demo_mode
    demo_mode = False
    
    # Initialize models if AWS is configured
    if aws_status:
        # Force re-initialization if MP agent changed
        if mp_configured and not st.session_state.models_initialized:
            st.session_state.models_initialized = False
        initialize_models()
        display_model_status()
    elif demo_mode:
        st.sidebar.info("🎭 Demo Mode Active - Sample responses only")
    else:
        st.sidebar.warning("⚠️ AWS credentials required to initialize models")
    
    # Demo mode option
    if not aws_status:
        st.warning("⚠️ AWS credentials not configured")
        demo_mode = st.checkbox(
            "🎭 Enable Demo Mode", 
            help="Try the app with sample responses (no AWS required)"
        )
        
        if not demo_mode:
            st.info("""
            **Configure AWS credentials to use real models:**
            1. **AWS SSO:** Run `aws configure sso` then `aws sso login`
            2. **AWS CLI:** Run `aws configure` for access keys
            3. **Environment Variables:** Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
            4. **AWS Profile:** Set `AWS_PROFILE` environment variable
            5. **IAM Roles:** If on EC2, attach IAM role with Bedrock permissions
            """)
            return
    
    # Model selection
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🎯 Select Agent & Model")
        
        # Agent type selection
        agent_type = st.selectbox(
            "Agent Framework:",
            ["Standard Agents", "AWS Strands"],
            help="Choose between custom agents or AWS Strands framework"
        )
        
        # Initialize Strands agents if selected
        if agent_type == "AWS Strands" and st.session_state.mp_agent:
            if not st.session_state.strands_supervisor:
                try:
                    st.session_state.strands_supervisor = StrandsSupervisorAgent(st.session_state.mp_agent)
                    st.session_state.strands_agents = {
                        'coordinator': StrandsCoordinator(st.session_state.mp_agent),
                        'dft_agent': StrandsDFTAgent(),
                        'structure_agent': StrandsStructureAgent(st.session_state.mp_agent),
                        'agentic_loop': StrandsAgenticLoop(st.session_state.mp_agent)
                    }
                    st.success("✅ AWS Strands agents initialized")
                except Exception as e:
                    st.error(f"❌ Strands initialization failed: {e}")
                    agent_type = "Standard Agents"
        if demo_mode:
            available_models = ["Nova Pro", "Llama 4 Scout", "Llama 3 70B", "OpenAI GPT OSS", "Qwen 3-32B", "DeepSeek R1", "Claude Opus 4.1"]
        else:
            available_models = [name for name, info in st.session_state.models.items() 
                              if info["status"] == "ready"]
            
            if not available_models:
                st.error("❌ No models are available. Check the model status in the sidebar.")
                return
        
        selected_model = st.selectbox(
            "Choose a model to test:",
            available_models,
            help="Select which LLM model to use for your query"
        )
        
        # Display selected model info
        if selected_model:
            if demo_mode:
                regions = {"Nova Pro": "us-east-1", "Llama 4 Scout": "us-east-1", 
                          "Llama 3 70B": "us-west-2", "OpenAI GPT OSS": "us-west-2", 
                          "Qwen 3-32B": "us-east-1", "DeepSeek R1": "us-east-1", 
                          "Claude Opus 4.1": "us-east-1"}
                st.info(f"""
                **Selected Model:** {selected_model} (Demo Mode)  
                **Region:** {regions.get(selected_model, "N/A")}  
                **Status:** Sample responses only
                """)
            else:
                model_info = st.session_state.models[selected_model]
                config = model_info["config"]
                
                st.info(f"""
                **Selected Model:** {selected_model}  
                **Region:** {config['region']}  
                **Model ID:** `{config['model_id']}`
                """)
    
    with col2:
        st.subheader("💬 Query Interface")
        
        # Optional POSCAR upload for Strands (auto-detected)
        poscar_text = None
        if agent_type == "AWS Strands":
            st.markdown("#### 📁 Optional: POSCAR File Upload")
            st.info("💡 Strands will auto-detect if POSCAR analysis is needed")
            uploaded_file = st.file_uploader("Upload POSCAR file (optional)", type=['txt', 'poscar', 'POSCAR'])
            if uploaded_file:
                poscar_text = uploaded_file.read().decode('utf-8')
                st.text_area("POSCAR Content:", poscar_text, height=150, disabled=True)
            else:
                poscar_text = st.text_area(
                    "Or paste POSCAR content (optional):",
                    height=100,
                    placeholder="Si\n1.0\n5.43 0 0\n0 5.43 0\n0 0 5.43\nSi\n2\nDirect\n0.0 0.0 0.0\n0.25 0.25 0.25"
                )
        
        # Query input
        query = st.text_area(
            "Enter your quantum matter/materials science question:",
            height=100,
            placeholder="Example: Generate a VQE ansatz for H2 molecule using UCCSD with Jordan-Wigner mapping",
            help="Ask questions about quantum computing, materials science, or request code generation"
        )
        
        # Additional parameters
        with st.expander("⚙️ Advanced Parameters"):
            col_a, col_b = st.columns(2)
            with col_a:
                temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
                max_tokens = st.number_input("Max Tokens", 100, 4000, 1000)
            with col_b:
                top_p = st.slider("Top P", 0.0, 1.0, 0.9, 0.1)
                include_mp_data = st.checkbox("Include Materials Project data", value=mp_configured)
        
        # Submit button
        if st.button("🚀 Generate Response", type="primary", disabled=not query.strip()):
            if selected_model and query.strip():
                # Show what will be used
                if include_mp_data and st.session_state.mp_agent:
                    if isinstance(st.session_state.mp_agent, EnhancedMCPAgent):
                        st.info("🔬 Will use Enhanced MCP Materials Project Server for data lookup")
                    else:
                        st.info("🔧 Will use standard Materials Project API for data lookup")
                
                generate_response(selected_model, query, temperature, max_tokens, top_p, include_mp_data, demo_mode, agent_type, poscar_text)

def generate_response(model_name: str, query: str, temperature: float, max_tokens: int, top_p: float, include_mp_data: bool, demo_mode: bool = False, agent_type: str = "Standard Agents", poscar_text: str = None):
    """Generate response using selected model or demo mode"""
    
    if demo_mode:
        # Use demo responses
        demo_response = get_demo_response(model_name, query)
        
        # Create response container
        response_container = st.container()
        
        with response_container:
            st.subheader(f"🎭 Demo Response from {model_name}")
            st.info("📝 This is a sample response. Enable AWS credentials for real model responses.")
            
            # Display demo response
            st.markdown("### 📝 Generated Response")
            st.markdown(demo_response)
            
            # Show sample code
            st.markdown("### 💻 Sample Generated Code")
            sample_code = '''# Sample VQE code for H2 molecule
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit.circuit.library import TwoLocal

geometry = "H 0 0 0; H 0 0 0.735"
driver = PySCFDriver(atom=geometry, basis='sto3g')
problem = driver.run()

ansatz = TwoLocal(4, 'ry', 'cz', reps=2, entanglement='linear')
print("Sample ansatz created with", ansatz.num_parameters, "parameters")'''
            st.code(sample_code, language="python")
            
            # Demo metadata
            with st.expander("📊 Demo Metadata"):
                metadata = {
                    "Mode": "Demo",
                    "Model": model_name,
                    "Query Length": len(query),
                    "Response Type": "Sample"
                }
                st.json(metadata)
        return
    
    model_info = st.session_state.models[model_name]
    model_instance = model_info["instance"]
    
    if not model_instance:
        st.error(f"❌ Model {model_name} is not available")
        return
    
    # Create response container
    response_container = st.container()
    
    with response_container:
        st.subheader(f"🤖 Response from {model_name}")
        
        # Show loading spinner
        with st.spinner(f"Generating response using {model_name}..."):
            try:
                # Log MCP usage
                if include_mp_data and st.session_state.mp_agent:
                    if isinstance(st.session_state.mp_agent, EnhancedMCPAgent):
                        logger.info(f"🔬 STREAMLIT: Using Enhanced MCP server for Materials Project data with query: '{query}'")
                    else:
                        logger.info(f"🔧 STREAMLIT: Using standard MP API for Materials Project data with query: '{query}'")
                
                # Generate response with agent framework
                if agent_type == "AWS Strands" and st.session_state.strands_supervisor:
                    # Let Strands intelligently gather data first
                    strands_result = st.session_state.strands_supervisor.intelligent_workflow_dispatch(query, poscar_text)
                    
                    # Now pass complete Strands workflow to the selected model
                    # Cache both MP data and full Strands context
                    original_mp_data = getattr(model_instance, '_cached_mp_data', None)
                    original_strands_result = getattr(model_instance, '_cached_strands_result', None)
                    
                    model_instance._cached_mp_data = strands_result.get('mp_data')
                    model_instance._cached_strands_result = strands_result
                    
                    # Generate full model response with complete Strands context
                    response = model_instance.generate_response(
                        query=query,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=top_p,
                        include_mp_data=include_mp_data
                    )
                    
                    # Add Strands analysis to the response
                    response["strands_data"] = strands_result
                    
                    # Restore original cached data
                    model_instance._cached_mp_data = original_mp_data
                    model_instance._cached_strands_result = original_strands_result
                    
                else:
                    # Use standard model
                    response = model_instance.generate_response(
                        query=query,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=top_p,
                        include_mp_data=include_mp_data
                    )
                
                # Display response
                if response:
                    # Response text
                    st.markdown("### 📝 Generated Response")
                    st.markdown(response.get("text", "No response text"))
                    
                    # Code output (only if there is actual code and it's different from what's in the text)
                    if "code" in response and response["code"] is not None and response["code"].strip():
                        # Check if the code is already displayed in the response text
                        response_text = response.get("text", "")
                        code_content = response["code"].strip()
                        
                        # Only show separate code section if code isn't already in the response
                        if code_content not in response_text:
                            st.markdown("### 💻 Generated Code")
                            st.code(response["code"], language="python")
                    
                    # 3D Structure Plot (if MCP generated one)
                    if (include_mp_data and isinstance(st.session_state.mp_agent, EnhancedMCPAgent) and 
                        ("3d" in query.lower() or "plot" in query.lower() or "visualiz" in query.lower())):
                        try:
                            # Get the most recent plot result from MCP agent
                            formula = response.get("formula", "TiO2")
                            mp_data = response.get("mp_data", {})
                            
                            st.markdown("### 🎨 3D Structure Visualization")
                            st.info(f"🔍 Generating 3D plot for {formula}...")
                            
                            # First try to get plot from Strands data (avoid double MCP call)
                            plot_result = None
                            if "strands_data" in response and response["strands_data"]:
                                strands_data = response["strands_data"]
                                mcp_results = strands_data.get('mcp_results', {})
                                if 'plot_structure' in mcp_results:
                                    plot_result = mcp_results['plot_structure']
                                    st.success(f"🎆 Using cached plot from Strands workflow ({len(plot_result)} chars)")
                            
                            # Display the plot if we have it
                            if plot_result and len(plot_result) > 100:
                                try:
                                    # Clean the base64 data
                                    image_data = plot_result.strip()
                                    if image_data.startswith('data:image'):
                                        image_data = image_data.split(',')[1]
                                    
                                    # Remove whitespace
                                    image_data = ''.join(image_data.split())
                                    
                                    # Decode and display
                                    image_bytes = base64.b64decode(image_data)
                                    st.image(image_bytes, caption=f"3D Crystal Structure: {formula}", use_container_width=True)
                                    st.success(f"✅ Enhanced 3D visualization for {formula}")
                                    
                                    # Download button
                                    st.download_button(
                                        label="📥 Download Structure Image",
                                        data=image_bytes,
                                        file_name=f"{formula}_structure.png",
                                        mime="image/png"
                                    )
                                    
                                except Exception as e:
                                    st.error(f"❌ Failed to display plot: {e}")
                                    with st.expander("🔍 Debug Info"):
                                        st.text(f"Plot data length: {len(plot_result)}")
                                        st.text(f"First 50 chars: {plot_result[:50]}")
                            else:
                                st.warning("⚠️ No plot data available or data too small")
                                
                        except Exception as plot_error:
                            st.error(f"❌ Plot generation failed: {str(plot_error)}")
                            logger.error(f"Plot display error: {plot_error}")
                    
                    # Strands-specific results
                    if "strands_data" in response and response["strands_data"]:
                        workflow_used = response["strands_data"].get('workflow_used', 'Auto-detected')
                        st.info(f"🤖 Strands used: **{workflow_used}** workflow")
                        
                        # Show formatted Strands response
                        strands_formatted = format_strands_response(response["strands_data"], workflow_used)
                        st.markdown(strands_formatted)
                        
                        # Show detailed results in expandable sections
                        display_strands_results(response["strands_data"], workflow_used)
                    
                    # Materials Project data (if included)
                    if "mp_data" in response and response["mp_data"]:
                        st.markdown("### 🔬 Materials Project Data")
                        st.json(response["mp_data"])
                    
                    # Model metadata
                    with st.expander("📊 Response Metadata"):
                        metadata = {
                            "Model": model_name,
                            "Region": model_info["config"]["region"],
                            "Model ID": model_info["config"]["model_id"],
                            "Temperature": temperature,
                            "Max Tokens": max_tokens,
                            "Top P": top_p,
                            "Response Length": len(response.get("text") or ""),
                            "MP Data Included": include_mp_data,
                            "MP Agent Type": "Enhanced MCP" if isinstance(st.session_state.mp_agent, EnhancedMCPAgent) else "Standard API" if st.session_state.mp_agent else "None"
                        }
                        st.json(metadata)
                    
                    # Show MCP activity logs if MCP was used
                    if include_mp_data and isinstance(st.session_state.mp_agent, EnhancedMCPAgent):
                        with st.expander("🔍 MCP Activity Log"):
                            display_mcp_logs()
                
                else:
                    st.error("❌ No response generated")
                    
            except Exception as e:
                st.error(f"❌ Error generating response: {str(e)}")
                with st.expander("🐛 Error Details"):
                    st.code(traceback.format_exc())


# Helper functions for Strands response formatting
def format_strands_response(strands_result: dict, workflow_type: str) -> str:
    """Format Strands agent response for display"""
    if not strands_result:
        return "No Strands analysis result available"
    
    status = strands_result.get('status', 'unknown')
    
    if workflow_type == "POSCAR Analysis":
        return f"""
## 🎯 Strands POSCAR Analysis Results

**Status:** {status}

### Structure Analysis
{format_structure_analysis(strands_result.get('structure_analysis', {}))}

### DFT Parameters
{format_dft_parameters(strands_result.get('dft_parameters', {}))}

### Quantum Code Generation
{format_quantum_code(strands_result.get('quantum_code', ''))}
"""
    
    elif workflow_type == "Complex Query":
        iterations = strands_result.get('iterations', [])
        return f"""
## 🔄 Strands Iterative Analysis Results

**Status:** {status}
**Iterations:** {len(iterations)}

### Analysis Summary
{format_iterative_summary(iterations)}

### Final Result
{strands_result.get('final_result', 'Analysis in progress...')}
"""
    
    else:  # Simple Query
        mcp_actions = strands_result.get('mcp_actions', [])
        moire_params = strands_result.get('moire_params', {})
        
        result_text = f"""
## 🤖 Strands Analysis Results

**Status:** {status}

### MCP Actions Performed
{mcp_actions}

### Analysis
{strands_result.get('reasoning', 'Strands agent processed your query successfully.')}
"""
        
        # Add moire-specific results
        if 'moire_homobilayer' in mcp_actions and moire_params:
            twist_angle = moire_params.get('twist_angle', 'N/A')
            interlayer_spacing = moire_params.get('interlayer_spacing', 'N/A')
            result_text += f"""

### 🌀 Moire Bilayer Structure Generated
- **Twist Angle:** {twist_angle}°
- **Interlayer Spacing:** {interlayer_spacing} Å
- **Structure Created:** ✅ Successfully generated moire bilayer
- **Status:** Ready for quantum simulations
"""
        
        return result_text

def format_structure_analysis(structure_data: dict) -> str:
    """Format structure analysis results"""
    if not structure_data:
        return "No structure analysis available"
    
    material_id = structure_data.get('material_id', 'Unknown')
    match_score = structure_data.get('match_score', 0)
    
    return f"""
- **Material ID:** {material_id}
- **Match Score:** {match_score:.3f}
- **Method:** {structure_data.get('reasoning', 'Strands analysis')}
"""

def format_dft_parameters(dft_data: dict) -> str:
    """Format DFT parameters"""
    if not dft_data:
        return "No DFT parameters extracted"
    
    return f"""
- **Hopping Parameter (t):** {dft_data.get('t_hopping', 'N/A')} eV
- **Hubbard U:** {dft_data.get('U_onsite', 'N/A')} eV
- **Band Gap:** {dft_data.get('band_gap_dft', 'N/A')} eV
- **Source:** {dft_data.get('source', 'Strands estimation')}
"""

def format_quantum_code(quantum_code: str) -> str:
    """Format quantum code generation"""
    if not quantum_code:
        return "No quantum code generated"
    
    return f"Generated quantum computing code with {len(quantum_code.split('\\n'))} lines"

def format_iterative_summary(iterations: list) -> str:
    """Format iterative analysis summary"""
    if not iterations:
        return "No iterations completed"
    
    summary = []
    for i, iteration in enumerate(iterations, 1):
        decision = iteration.get('decision', {})
        action = decision.get('next_action', 'Unknown action')
        summary.append(f"**Iteration {i}:** {action}")
    
    return "\\n".join(summary)

def display_strands_results(strands_data: dict, workflow_type: str):
    """Display detailed Strands results in expandable sections"""
    
    if workflow_type == "POSCAR Analysis":
        # Structure matching results
        if 'structure_analysis' in strands_data:
            with st.expander("🔍 Structure Matching Details"):
                st.json(strands_data['structure_analysis'])
        
        # DFT parameters
        if 'dft_parameters' in strands_data:
            with st.expander("⚛️ DFT Parameters Details"):
                st.json(strands_data['dft_parameters'])
        
        # Hamiltonian code
        if 'hamiltonian_code' in strands_data:
            with st.expander("🧮 Generated Hamiltonian Code"):
                st.code(strands_data['hamiltonian_code'], language="python")
    
    elif workflow_type == "Complex Query":
        # Iteration details
        iterations = strands_data.get('iterations', [])
        if iterations:
            with st.expander(f"🔄 Iteration Details ({len(iterations)} iterations)"):
                for i, iteration in enumerate(iterations, 1):
                    st.markdown(f"**Iteration {i}:**")
                    st.json(iteration)
                    st.markdown("---")
    
    elif workflow_type == "Simple Query":
        # Moire bilayer specific results
        mcp_actions = strands_data.get('mcp_actions', [])
        if 'moire_homobilayer' in mcp_actions:
            with st.expander("🌀 Moire Bilayer Generation Details"):
                moire_params = strands_data.get('moire_params', {})
                st.success("✅ Moire bilayer structure successfully generated!")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Twist Angle", f"{moire_params.get('twist_angle', 'N/A')}°")
                with col2:
                    st.metric("Interlayer Spacing", f"{moire_params.get('interlayer_spacing', 'N/A')} Å")
                
                st.info("💡 The moire bilayer structure has been created and is ready for quantum simulations. You can now use this structure for VQE calculations, band structure analysis, or other quantum computing applications.")
                
                # Show MCP actions performed
                st.markdown("**MCP Actions Performed:**")
                for i, action in enumerate(mcp_actions, 1):
                    st.write(f"{i}. {action}")
    
    # Always show raw Strands data
    with st.expander("🔧 Raw Strands Data"):
        st.json(strands_data)

if __name__ == "__main__":
    main()