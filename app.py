import streamlit as st
import os
import json
import logging
import re
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import traceback
import base64
from io import BytesIO

# Import authentication and security
from config.cognito_auth import get_auth_handler
from utils.config_validator import validate_cognito_config, ConfigurationError, validate_query

# Import our model classes
from models.nova_pro_model import NovaProModel
from models.llama4_model import Llama4Model
from models.llama3_model import Llama3Model
from models.openai_model import OpenAIModel
from models.qwen_model import QwenModel
from models.deepseek_model import DeepSeekModel
from models.claude_opus_model import ClaudeOpusModel
from models.claude_sonnet_model import ClaudeSonnetModel

from utils.enhanced_mcp_client import EnhancedMCPAgent
from utils.secrets_manager import get_mp_api_key
from utils.logging_display import setup_logging_display, display_mcp_logs
from utils.braket_integration import braket_integration
from utils.debug_logger import get_debug_logger, simulate_mcp_processing_logs

from demo_mode import get_demo_response
from agents.strands_supervisor import StrandsSupervisorAgent
from agents.strands_coordinator import StrandsCoordinator
from agents.strands_dft_agent import StrandsDFTAgent
from agents.strands_structure_agent import StrandsStructureAgent
from agents.strands_agentic_loop import StrandsAgenticLoop

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
from utils.structured_logger import get_structured_logger
logger = get_structured_logger(__name__)

# Startup message removed for production

# Page configuration
st.set_page_config(
    page_title="Quantum Materials Code Generation and Simulation - AWS Bedrock, Strands Agents & MCP",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set default AWS region for App Runner
if not os.environ.get('AWS_DEFAULT_REGION'):
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

# Custom CSS - Fixed for Elastic Beanstalk compatibility
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
    /* Clean styling to match local appearance */
    .stButton > button {
        background-color: #0066cc !important;
        color: white !important;
        border: none !important;
    }
    
    /* Override Streamlit's red primary color */
    .stApp {
        --primary-color: #0066cc;
    }
    
    /* Specific fixes for EB red color issues */
    .stSlider [data-baseweb="slider"] [role="slider"] {
        background-color: #0066cc !important;
    }
    
    .stCheckbox [data-testid="stCheckbox-input"] {
        accent-color: #0066cc !important;
    }
    
    /* Clean input styling */
    .stTextInput input, .stTextArea textarea {
        border-color: rgba(49, 51, 63, 0.2) !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #0066cc !important;
        box-shadow: 0 0 0 0.2rem rgba(0, 102, 204, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    # Clean up old session data first
    cleanup_session_state()
    
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

def cleanup_session_state():
    """Clean up old session data to prevent memory leaks"""
    import sys
    import time
    from config.app_config import AppConfig
    
    # Check for large objects in session state
    if 'mp_agent' in st.session_state and st.session_state.mp_agent:
        try:
            size = sys.getsizeof(st.session_state.mp_agent)
            if size > AppConfig.MAX_OBJECT_SIZE_MB * 1024 * 1024:
                logger.warning(f"Large mp_agent object detected: {size} bytes, cleaning up")
                if hasattr(st.session_state.mp_agent, 'cleanup'):
                    st.session_state.mp_agent.cleanup()
                st.session_state.mp_agent = None
        except Exception as e:
            logger.warning(f"Error checking mp_agent size: {e}")
    
    # Clear old cached data based on time
    current_time = time.time()
    if 'last_cleanup_time' not in st.session_state:
        st.session_state.last_cleanup_time = current_time
    
    # Clean up based on configured interval
    if current_time - st.session_state.last_cleanup_time > AppConfig.SESSION_CLEANUP_INTERVAL:
        logger.info("Performing hourly session cleanup")
        
        # Clear cached model data
        if 'models' in st.session_state:
            for model_name, model_info in st.session_state.models.items():
                if 'instance' in model_info and model_info['instance']:
                    if hasattr(model_info['instance'], '_cached_mp_data'):
                        model_info['instance']._cached_mp_data = None
        
        # Reset initialization flags to force refresh
        st.session_state.models_initialized = False
        st.session_state.last_cleanup_time = current_time


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
    """Setup Materials Project API with automatic configuration"""
    st.sidebar.subheader("🔬 Materials Project API")
    
    mp_api_key = None
    
    # Auto-detect API key from Secrets Manager first
    if st.session_state.aws_configured:
        try:
            mp_api_key = get_mp_api_key()
            if mp_api_key:
                st.sidebar.success("✅ MP API key auto-detected from Secrets Manager")
            else:
                st.sidebar.info("ℹ️ No MP API key found in Secrets Manager")
        except Exception as e:
            st.sidebar.warning(f"⚠️ Secrets Manager check failed: {str(e)}")
    
    # Manual input only if no key found
    if not mp_api_key:
        mp_api_key = st.sidebar.text_input(
            "Materials Project API Key",
            type="password",
            help="Get your API key from https://materialsproject.org/",
            placeholder="Enter your MP API key..."
        )
    
    if mp_api_key:
        # Enhanced caching with server health validation and call count tracking
        if (hasattr(st.session_state, 'mp_agent') and 
            st.session_state.mp_agent and 
            hasattr(st.session_state, 'mp_api_key_hash') and
            st.session_state.mp_api_key_hash == hash(mp_api_key)):
            
            # Verify the cached agent is still healthy and not overloaded
            try:
                agent_client = st.session_state.mp_agent.client
                is_healthy = agent_client._is_server_healthy()
                call_count = getattr(agent_client, 'call_count', 0)
                consecutive_failures = getattr(agent_client, 'consecutive_failures', 0)
                
                # Check multiple health indicators
                if (is_healthy and 
                    call_count < agent_client.max_calls_before_restart and 
                    consecutive_failures < agent_client.max_consecutive_failures):
                    st.sidebar.success(f"✅ Enhanced MCP server healthy (cached)")
                    return True
                else:
                    logger.warning(f"⚠️ STREAMLIT: MCP agent needs refresh - healthy: {is_healthy}, calls: {call_count}, failures: {consecutive_failures}")
                    # Force cleanup of old agent
                    try:
                        agent_client.stop_server()
                    except:
                        pass
                    st.session_state.mp_agent = None
            except Exception as health_check_error:
                logger.warning(f"⚠️ STREAMLIT: Health check failed, creating new agent: {health_check_error}")
                st.session_state.mp_agent = None
        
        try:
            # Create new MCP agent only if needed
            logger.info("🚀 STREAMLIT: Initializing Enhanced MCP Materials Project Agent")
            show_debug = getattr(st.session_state, 'show_debug', False)
            def initial_debug_callback(message):
                logger.info(f"MCP DEBUG: {message}")
            st.session_state.mp_agent = EnhancedMCPAgent(api_key=mp_api_key, show_debug=show_debug, debug_callback=initial_debug_callback)
            st.session_state.mp_api_key_hash = hash(mp_api_key)  # Cache key hash
            st.sidebar.success("✅ Enhanced MCP Materials Project server configured")
            logger.info("✅ STREAMLIT: Enhanced MCP Agent initialized successfully")
            
            # Auto-store manually entered key to Secrets Manager
            if st.session_state.aws_configured and mp_api_key and not get_mp_api_key():
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
        "OpenAI OSS-120B": {
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
        "Claude Sonnet 4.5": {
            "class": ClaudeSonnetModel,
            "region": "us-east-1",
            "model_id": "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
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
    # Validate secure configuration first
    try:
        cognito_config = validate_cognito_config()
        if cognito_config:
            # Set validated configuration in environment
            for key, value in cognito_config.items():
                os.environ[key] = value
    except ConfigurationError as e:
        st.error(f"❌ Configuration Error: {e}")
        st.info("💡 Please configure required credentials in AWS Systems Manager Parameter Store or environment variables")
        return
    
    # Check authentication with audit logging
    from utils.audit_logger import audit_authentication
    auth_handler = get_auth_handler()
    if not auth_handler.render_auth_ui():
        audit_authentication('login_required', 'anonymous', 'blocked')
        return
    else:
        user = st.session_state.get('username', 'authenticated_user')
        audit_authentication('session_validated', user, 'success')
    
    # Setup logging display
    setup_logging_display()
    
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">⚛️ Quantum Materials Code Generation and Simulation</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666; font-size: 1.1rem; margin-top: -1rem;">AWS Bedrock, Strands Agents & MCP</p>', unsafe_allow_html=True)
    
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
            st.sidebar.info("🔧 Enhanced MCP Server Active")
            st.sidebar.success("✅ All advanced features available")
            
            # Test MCP server button
            with st.sidebar.expander("🔍 Test Enhanced MCP"):
                if st.button("🧪 Test MCP", help="Test Enhanced MCP server with mp-149"):
                    try:
                        result = st.session_state.mp_agent.search("mp-149")
                        if result and 'error' not in result:
                            st.success("Enhanced MCP Test Success")
                        else:
                            st.error(f"MCP Test Failed: {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"MCP Test Error: {str(e)}")
    
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
        
        # Braket Integration Status
        st.markdown("#### ⚛️ Amazon Braket Integration")
        if braket_integration.is_available():
            st.success("✅ Braket MCP Server Available")
            
            # Braket mode toggle
            braket_mode = st.selectbox(
                "Quantum Framework:",
                ["Qiskit Framework", "Amazon Braket Framework"],
                help="Qiskit: Materials science + VQE circuits | Braket: Simple algorithms (Bell, GHZ, QFT)"
            )
            
            # Framework selection guide
            st.info("""
            **🔬 Qiskit Framework:** Use for materials science, VQE circuits, and Materials Project integration  
            **⚛️ Braket Framework:** Use for simple quantum algorithms (Bell pairs, GHZ states, QFT)
            """)
            

            
            # Show Braket features
            if braket_mode != "Qiskit Framework":
                with st.expander("🚀 Braket MCP Capabilities"):
                    st.info("""
                    **Supported Operations:**
                    • Bell pairs, GHZ states, QFT circuits
                    • AWS quantum device listing
                    • ASCII circuit diagrams
                    • Local simulator execution
                    
                    **Example Queries:**
                    • "Create a Bell pair circuit"
                    • "Generate 4-qubit GHZ state with ASCII diagram"
                    • "Show available Braket devices"
                    """)
        else:
            st.warning("⚠️ Braket MCP Server Not Available")
            st.info("💡 Install dependencies: `pip install amazon-braket-sdk qiskit-braket-provider fastmcp`")
            braket_mode = "Qiskit Framework"
        
        # AWS Strands Agents (always enabled)
        agent_type = "AWS Strands Agents SDK"
        st.markdown("#### 🧠 AWS Strands Agents SDK")
        st.success("✅ Advanced multi-agent workflow system active")
        
        # Initialize Strands agents
        if st.session_state.mp_agent:
            if not st.session_state.strands_supervisor:
                try:
                    st.session_state.strands_supervisor = StrandsSupervisorAgent(st.session_state.mp_agent)
                    st.session_state.strands_agents = {
                        'coordinator': StrandsCoordinator(st.session_state.mp_agent),
                        'dft_agent': StrandsDFTAgent(),
                        'structure_agent': StrandsStructureAgent(st.session_state.mp_agent),
                        'agentic_loop': StrandsAgenticLoop(st.session_state.mp_agent)
                    }
                except Exception as e:
                    st.error(f"❌ Strands initialization failed: {e}")
                    agent_type = "Standard Agents"
        if demo_mode:
            available_models = ["Nova Pro", "Llama 4 Scout", "Llama 3 70B", "OpenAI OSS-120B", "Qwen 3-32B", "DeepSeek R1", "Claude Opus 4.1", "Claude Sonnet 4.5"]
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
                          "Llama 3 70B": "us-west-2", "OpenAI OSS-120B": "us-west-2", 
                          "Qwen 3-32B": "us-east-1", "DeepSeek R1": "us-east-1", 
                          "Claude Opus 4.1": "us-east-1", "Claude Sonnet 4.5": "us-east-1"}
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
        
        # Optional POSCAR upload (auto-detected by Strands)
        poscar_text = None
        st.markdown("#### 📁 Optional: POSCAR File Upload")
        st.info("💡 AWS Strands will auto-detect if POSCAR analysis is needed")
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
        
        # Query input with Braket-specific examples
        if braket_mode == "Amazon Braket Framework":
            placeholder_text = "Example: Create a 4-qubit GHZ circuit with ASCII diagram"
            help_text = "⚛️ Braket Framework: Simple quantum algorithms only (Bell, GHZ, QFT, devices). NO materials science."
        else:
            placeholder_text = "Example: Generate a VQE ansatz for H2 molecule using UCCSD with Jordan-Wigner mapping"
            help_text = "🔬 Qiskit Framework: Full quantum computing and materials science support"
        
        # Initialize query input in session state if not exists
        if 'query_text' not in st.session_state:
            st.session_state.query_text = ''
        
        query = st.text_area(
            "Enter your quantum matter/materials science question:",
            value=st.session_state.query_text,
            height=100,
            placeholder=placeholder_text,
            help=help_text
        )
        
        # Update session state when text changes
        if query != st.session_state.query_text:
            st.session_state.query_text = query
        
        # Mode-specific examples
        if braket_mode == "Amazon Braket Framework":
            st.markdown("**⚛️ Braket Framework Examples:**")
            col_ex1, col_ex2 = st.columns(2)
            with col_ex1:
                if st.button("📝 GHZ Circuit", help="Simple GHZ circuit with ASCII"):
                    st.session_state.query_text = "Create a 4-qubit GHZ state circuit with ASCII diagram"
                    st.rerun()
                if st.button("🔗 Bell Pair", help="Bell pair circuit"):
                    st.session_state.query_text = "Create a Bell pair circuit using Braket"
                    st.rerun()
            with col_ex2:
                if st.button("🖥️ List Devices", help="Show available devices"):
                    st.session_state.query_text = "Show me available Amazon Braket devices and their status"
                    st.rerun()
                if st.button("🎯 QFT Circuit", help="Quantum Fourier Transform"):
                    st.session_state.query_text = "Generate a 3-qubit QFT circuit with Braket"
                    st.rerun()
            

        
        elif braket_mode == "Both Frameworks":
            st.markdown("**🔄 Both Frameworks Examples:**")
            col_ex1, col_ex2 = st.columns(2)
            with col_ex1:
                st.markdown("**🔬 Materials Science (→ Qiskit):**")
                if st.button("🧪 VQE for TiO2", help="Materials science with Qiskit"):
                    st.session_state.query_text = "Generate VQE circuit for TiO2 using Materials Project data"
                    st.rerun()
                if st.button("💎 Silicon VQE", help="Silicon quantum simulation"):
                    st.session_state.query_text = "Create VQE ansatz for silicon mp-149"
                    st.rerun()
            with col_ex2:
                st.markdown("**⚛️ Algorithms (→ Braket MCP):**")
                if st.button("🔗 Bell + ASCII", help="Simple circuit with visualization"):
                    st.session_state.query_text = "Create Bell pair with ASCII diagram"
                    st.rerun()
                if st.button("📊 Device Status", help="Braket device information"):
                    st.session_state.query_text = "Show Braket device status"
                    st.rerun()
        
        elif braket_mode == "Qiskit Framework":
            st.markdown("**🔬 Qiskit Framework Examples (Full Support):**")
            col_ex1, col_ex2 = st.columns(2)
            with col_ex1:
                if st.button("🧪 H2 VQE", help="Hydrogen molecule VQE"):
                    st.session_state.query_text = "Generate VQE ansatz for H2 molecule using UCCSD"
                    st.rerun()
                if st.button("💎 Graphene VQE", help="Graphene quantum simulation"):
                    st.session_state.query_text = "Create VQE circuit for graphene using Materials Project"
                    st.rerun()
            with col_ex2:
                if st.button("🔬 TiO2 Analysis", help="Titanium dioxide simulation"):
                    st.session_state.query_text = "Generate quantum simulation for TiO2 with real coordinates"
                    st.rerun()
                if st.button("📋 MP Search", help="Materials Project search"):
                    st.session_state.query_text = "Show me properties of silicon mp-149"
                    st.rerun()
        

        
        # Debug/Technical View Toggle
        show_debug = st.checkbox(
            "🔍 Show Technical Details", 
            value=False,
            help="Show detailed MCP processing logs, API calls, and technical metadata"
        )
        
        # Additional parameters
        with st.expander("⚙️ Advanced Parameters"):
            col_a, col_b = st.columns(2)
            with col_a:
                temperature = st.slider(
                    "Temperature", 0.0, 1.0, 0.3, 0.1,
                    help="Controls randomness: 0.0 = deterministic, 1.0 = very creative. Higher values generate more diverse but potentially less focused responses."
                )
                max_tokens = st.number_input(
                    "Max Tokens", 100, 4000, 1000,
                    help="Maximum response length. Higher values allow longer, more detailed responses but may increase processing time."
                )
            with col_b:
                top_p = st.slider(
                    "Top P", 0.0, 1.0, 0.8, 0.1,
                    help="Nucleus sampling: Controls diversity by considering only the top P% of probable tokens. Lower values = more focused, higher values = more diverse."
                )
                # Auto-determine MP data usage based on framework and configuration
                include_mp_data = mp_configured and (braket_mode == "Qiskit Framework")
                
                # Show MP data status
                if braket_mode == "Amazon Braket Framework":
                    st.info("ℹ️ Materials Project data not used with Braket Framework")
                elif mp_configured:
                    st.success("✅ Materials Project data will be included automatically")
                else:
                    st.info("ℹ️ Configure Materials Project API to enable material data integration")
            
            # Parameter explanation
            with st.expander("ℹ️ Parameter Guide"):
                st.markdown("""
                **Temperature (0.0 - 1.0):**
                - **0.0-0.3:** Very focused, deterministic responses (good for factual queries)
                - **0.4-0.7:** Balanced creativity and accuracy (recommended for most tasks)
                - **0.8-1.0:** High creativity, more experimental responses (good for brainstorming)
                
                **Top P (0.0 - 1.0):**
                - **0.1-0.5:** Very focused vocabulary, conservative word choices
                - **0.6-0.9:** Balanced vocabulary selection (recommended)
                - **0.9-1.0:** Full vocabulary range, more diverse expressions
                
                **Recommended Settings:**
                - **Scientific Analysis:** Temperature 0.3, Top P 0.8
                - **Code Generation:** Temperature 0.5, Top P 0.9
                - **Creative Writing:** Temperature 0.8, Top P 0.95
                """)
            
            # Auto-determine Braket MCP usage based on framework selection
            force_braket_mcp = (braket_mode == "Amazon Braket Framework")
        
        # Submit button with rate limiting
        from utils.rate_limiter import TooManyRequestsError
        if st.button("🚀 Generate Response", type="primary", disabled=not query.strip()):
            if selected_model and query.strip():
                # Show what will be used
                if braket_mode == "Amazon Braket":
                    st.warning("⚛️ **Braket Mode Active:** Only simple quantum algorithms supported. Materials Project data will be ignored.")
                elif include_mp_data and st.session_state.mp_agent:
                    if isinstance(st.session_state.mp_agent, EnhancedMCPAgent):
                        st.info("🔬 Will use Enhanced MCP Materials Project Server for data lookup")
                    else:
                        st.info("🔧 Will use standard Materials Project API for data lookup")
                
                if force_braket_mcp:
                    st.info("⚛️ Using Braket MCP for quantum circuit generation")
                
                # Show what code will be generated
                if braket_mode == "Amazon Braket Framework":
                    st.info("📝 **Code Output:** Braket SDK code with ASCII circuit diagrams")
                else:
                    st.info("📝 **Code Output:** Qiskit/Qiskit-Nature code for quantum simulations")
                
                from utils.audit_logger import audit_model_usage
                try:
                    audit_model_usage(selected_model, len(query), 'initiated')
                    generate_response(selected_model, query, temperature, max_tokens, top_p, include_mp_data, demo_mode, agent_type, poscar_text, braket_mode, force_braket_mcp, show_debug)
                    audit_model_usage(selected_model, len(query), 'success')
                except TooManyRequestsError as e:
                    audit_model_usage(selected_model, len(query), 'rate_limited')
                    st.error(f"⚠️ {str(e)}")
                    st.info("🕰️ Please wait before making another request")
                except Exception as e:
                    audit_model_usage(selected_model, len(query), 'error')
                    raise

def generate_response(model_name: str, query: str, temperature: float, max_tokens: int, top_p: float, include_mp_data: bool, demo_mode: bool = False, agent_type: str = "Standard Agents", poscar_text: str = None, braket_mode: str = "Qiskit Only", force_braket_mcp: bool = False, show_debug: bool = False):
    """Generate response using selected model or demo mode"""
    
    # Validate user input
    try:
        query = validate_query(query)
    except ValueError as e:
        st.error(f"❌ Invalid query: {e}")
        return
    
    # Create debug callback function
    debug_messages = []
    def debug_callback(message):
        debug_messages.append(message)
        if show_debug and 'debug_placeholder' in locals():
            # Update the debug display in real-time
            debug_placeholder.markdown("\n\n".join(debug_messages[-10:]))  # Show last 10 messages
    
    # Store debug setting and reinitialize MCP agent if debug setting changed
    if hasattr(st.session_state, 'show_debug') and st.session_state.show_debug != show_debug:
        st.session_state.show_debug = show_debug
        # Reinitialize MCP agent with new debug setting and callback
        if st.session_state.mp_agent and isinstance(st.session_state.mp_agent, EnhancedMCPAgent):
            api_key = st.session_state.mp_agent.client.api_key
            st.session_state.mp_agent = EnhancedMCPAgent(api_key=api_key, show_debug=show_debug, debug_callback=debug_callback)
    else:
        st.session_state.show_debug = show_debug
        # Update existing MCP agent with callback if needed
        if st.session_state.mp_agent and isinstance(st.session_state.mp_agent, EnhancedMCPAgent):
            st.session_state.mp_agent.client.debug_callback = debug_callback if show_debug else None
    
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
        
        # Show loading spinner with enhanced message for Strands
        spinner_message = f"🧠 AWS Strands Agents SDK is analyzing your query with {model_name}... This may take 2-5 minutes for complex workflows."
        
        # Create fixed containers for debug output and spinner
        debug_placeholder = None
        spinner_container = st.container()
        
        if show_debug and braket_mode == "Amazon Braket Framework":
            debug_container = st.container()
            with debug_container:
                st.markdown("### 🔍 Real-time MCP Processing")
                debug_placeholder = st.empty()
                
        # Update debug callback with placeholder reference
        def update_debug_callback(message):
            debug_messages.append(message)
            if show_debug and braket_mode == "Amazon Braket Framework" and debug_placeholder:
                # Update the debug display in real-time and keep all messages
                debug_placeholder.markdown("\n\n".join(debug_messages))  # Show all messages
        
        # Update MCP agent callback immediately
        if st.session_state.mp_agent and isinstance(st.session_state.mp_agent, EnhancedMCPAgent):
            st.session_state.mp_agent.client.debug_callback = update_debug_callback if (show_debug and braket_mode == "Amazon Braket Framework") else None
            st.session_state.mp_agent.client.show_debug = show_debug and braket_mode == "Amazon Braket Framework"
        
        with spinner_container:
            with st.spinner(spinner_message):
                try:
                    # MCP usage (reduced logging)
                    if include_mp_data and st.session_state.mp_agent:
                        logger.debug(f"Using MCP for query: {query[:30]}...")
                
                    # Simple framework-based routing - no complex detection needed
                    if show_debug and braket_mode == "Amazon Braket Framework" and debug_placeholder:
                        debug_info = f"""📋 **Framework Selection:**
- Selected Framework: {braket_mode}
- Force Braket MCP: {force_braket_mcp}
- Include MP data: {include_mp_data}
- Agent type: {agent_type}"""
                        debug_placeholder.markdown(debug_info)
                
                    # Use framework selection directly - no keyword detection
                    if braket_mode == "Amazon Braket Framework":
                        # Framework selection (UI message removed)
                        
                        if show_debug and debug_placeholder:
                            debug_placeholder.success("⚛️ **Braket Framework Selected** - Processing with Braket MCP")
                        
                        # Get Braket MCP data based on query content
                        braket_data = None
                        
                        if 'ghz' in query.lower():
                            qubit_match = re.search(r'(\d+)\s*qubit', query.lower())
                            num_qubits = int(qubit_match.group(1)) if qubit_match else 3
                            braket_data = braket_integration.create_ghz_circuit(num_qubits)
                        elif 'bell' in query.lower():
                            braket_data = braket_integration.create_bell_pair_circuit()
                            if show_debug and debug_placeholder:
                                debug_placeholder.info(f"🔍 **Braket MCP Call:** Bell pair circuit")
                        elif 'device' in query.lower() and ('available' in query.lower() or 'status' in query.lower() or 'list' in query.lower()):
                            braket_data = braket_integration.list_braket_devices()
                            if show_debug and debug_placeholder:
                                debug_placeholder.info(f"🔍 **Braket MCP Call:** Device list")
                        else:
                            # Default to Bell pair for general circuit requests
                            braket_data = braket_integration.create_bell_pair_circuit()
                            if show_debug and debug_placeholder:
                                debug_placeholder.info(f"🔍 **Braket MCP Call:** Default Bell pair")
                        
                        # Debug: Show what we got from Braket MCP
                        if show_debug and debug_placeholder:
                            debug_placeholder.success(f"⚛️ **Braket MCP Result:** {type(braket_data)} - {list(braket_data.keys()) if isinstance(braket_data, dict) else 'Not a dict'}")
                        
                        # Cache Braket MCP data for the LLM to use
                        if braket_data and "error" not in braket_data:
                            model_instance._cached_braket_data = braket_data
                            if show_debug and debug_placeholder:
                                debug_placeholder.success(f"✅ **Cached Braket Data:** {list(braket_data.keys())}")
                        else:
                            if show_debug and debug_placeholder:
                                debug_placeholder.error(f"❌ **Braket Data Issue:** {braket_data}")
                        
                        # Generate response with Braket SDK code + MCP diagrams
                        response = model_instance.generate_response(
                            query=query,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            top_p=top_p,
                            include_mp_data=False,  # Braket Framework doesn't use MP data
                            show_debug=show_debug,
                            braket_mode=braket_mode
                        )
                        
                        # Add Braket MCP data to response for enhanced diagrams
                        if braket_data and "error" not in braket_data:
                            response["braket_data"] = braket_data
                            if show_debug and debug_placeholder:
                                debug_placeholder.success(f"✅ **Added to Response:** braket_data with keys {list(braket_data.keys())}")
                        else:
                            if show_debug and debug_placeholder:
                                debug_placeholder.warning(f"⚠️ **Not Added to Response:** {braket_data}")
                        
                        # Clear cached data
                        model_instance._cached_braket_data = None
                    
                    # Generate response with AWS Strands framework (Qiskit Framework)
                    elif braket_mode == "Qiskit Framework" and st.session_state.strands_supervisor:
                        if show_debug and debug_placeholder:
                            debug_placeholder.info("🧠 **AWS Strands Supervisor** - Analyzing query and dispatching to appropriate workflow...")
                        
                        # Check if this is a molecular query that should skip MP search
                        query_lower = query.lower()
                        molecular_keywords = ['h2', 'hydrogen molecule', 'water molecule', 'h2o molecule', 'co2', 'ch4', 'nh3', 'h2 molecule', 'hydrogen gas']
                        is_molecular_query = any(mol in query_lower for mol in molecular_keywords)
                        
                        if is_molecular_query:
                            if show_debug and debug_placeholder:
                                debug_placeholder.info("🧪 **Molecular Query Detected** - Skipping Strands MP search for simple molecule")
                            # Create a simple molecular response without MP data
                            strands_result = {
                                "status": "success",
                                "mp_data": None,
                                "mcp_actions": [],
                                "workflow_used": "Simple Query",
                                "reasoning": "Simple molecule query - no Materials Project search needed"
                            }
                        else:
                            # Update MCP agent callback for Strands workflow
                            if isinstance(st.session_state.mp_agent, EnhancedMCPAgent):
                                st.session_state.mp_agent.client.debug_callback = update_debug_callback if show_debug else None
                            
                            # Let Strands intelligently gather data first
                            strands_result = st.session_state.strands_supervisor.intelligent_workflow_dispatch(query, poscar_text)
                        
                        if show_debug and strands_result:
                            # Show Strands analysis results
                            workflow_used = strands_result.get('workflow_used', 'Auto-detected')
                            mcp_actions = strands_result.get('mcp_actions', [])
                            status = strands_result.get('status', 'unknown')
                            
                            debug_info = f"""✅ **Strands Analysis Results**
**Status:** {status}

**MCP Actions Performed**
{mcp_actions}

**Analysis**
{strands_result.get('reasoning', 'Strands agent processed your query successfully.')}"""
                            
                            # Add Materials Project data if available
                            if 'mp_data' in strands_result and strands_result['mp_data']:
                                mp_data = strands_result['mp_data']
                                # Handle both dict and list formats
                                if isinstance(mp_data, dict):
                                    debug_info += f"""

🔬 **Materials Project Data**
{{
"material_id":"{mp_data.get('material_id', 'N/A')}"
"structure_uri":"{mp_data.get('structure_uri', 'N/A')}"
"source":"{mp_data.get('source', 'N/A')}"
"formula":"{mp_data.get('formula', 'N/A')}"
"band_gap":{mp_data.get('band_gap', 'N/A')}
"formation_energy":{mp_data.get('formation_energy', 'N/A')}
"crystal_system":"{mp_data.get('crystal_system', 'N/A')}"
"geometry":"{mp_data.get('geometry', 'N/A')[:100] if mp_data.get('geometry') else 'N/A'}..."
}}"""
                                elif isinstance(mp_data, list) and len(mp_data) > 0:
                                    first_item = mp_data[0] if mp_data else {}
                                    if isinstance(first_item, dict):
                                        debug_info += f"""

🔬 **Materials Project Data** (List format)
{{
"material_id":"{first_item.get('material_id', 'N/A')}"
"formula":"{first_item.get('formula', 'N/A')}"
"band_gap":{first_item.get('band_gap', 'N/A')}
}}"""
                                    else:
                                        debug_info += f"""

🔬 **Materials Project Data** (List format)
Items: {len(mp_data)}
Data: {str(mp_data)[:200]}..."""
                                else:
                                    debug_info += f"""

🔬 **Materials Project Data** (Unknown format)
Type: {type(mp_data)}
Data: {str(mp_data)[:200]}..."""
                            
                            if debug_placeholder:
                                debug_placeholder.markdown(debug_info)
                        
                        if show_debug and debug_placeholder:
                            debug_placeholder.info(f"🤖 **{model_name}** - Generating enhanced response with Strands context...")
                        
                        # Now pass complete Strands workflow to the selected model
                        # Cache both MP data and full Strands context
                        original_mp_data = getattr(model_instance, '_cached_mp_data', None)
                        original_strands_result = getattr(model_instance, '_cached_strands_result', None)
                        
                        model_instance._cached_mp_data = strands_result.get('mp_data')
                        model_instance._cached_strands_result = strands_result
                        
                        # Ensure debug callback is active for model generation
                        if isinstance(st.session_state.mp_agent, EnhancedMCPAgent):
                            st.session_state.mp_agent.client.debug_callback = update_debug_callback if show_debug else None
                            st.session_state.mp_agent.client.show_debug = show_debug
                        
                        # Generate full model response with complete Strands context
                        response = model_instance.generate_response(
                            query=query,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            top_p=top_p,
                            include_mp_data=include_mp_data,
                            show_debug=show_debug,
                            braket_mode=braket_mode
                        )
                        
                        # Add Strands analysis to the response
                        response["strands_data"] = strands_result
                        
                        # Restore original cached data
                        model_instance._cached_mp_data = original_mp_data
                        model_instance._cached_strands_result = original_strands_result
                        
                    else:
                        # Force MP data retrieval if requested and available (now always uses Enhanced MCP)
                        if include_mp_data and st.session_state.mp_agent:
                            try:
                                # Smart material extraction from query
                                material_query = None
                                query_lower = query.lower()
                                
                                # Skip MP search for simple molecules first
                                molecular_keywords = ['h2', 'hydrogen molecule', 'water molecule', 'h2o molecule', 'co2', 'ch4', 'nh3', 'h2 molecule', 'hydrogen gas']
                                is_molecular_query = any(mol in query_lower for mol in molecular_keywords)
                                if is_molecular_query:
                                    if show_debug and debug_placeholder:
                                        debug_placeholder.info("🔍 **Molecular Query Detected:** Skipping Materials Project search for simple molecule")
                                    material_query = None  # Skip MP search for molecules
                                else:
                                    # Check for material IDs first (highest priority)
                                    mp_match = re.search(r'mp-\d+', query)
                                    if mp_match:
                                        material_query = mp_match.group(0)
                                    else:
                                        # Check for crystalline materials only (exclude simple molecules)
                                        materials = {
                                            'graphene': 'graphene', 'carbon': 'carbon', 'diamond': 'diamond',
                                            'silicon': 'silicon', 'si': 'silicon', 'titanium': 'titanium', 'ti': 'titanium',
                                            'tio2': 'TiO2', 'titanium dioxide': 'TiO2', 'iron': 'iron', 'fe': 'iron',
                                            'copper': 'copper', 'cu': 'copper', 'aluminum': 'aluminum', 'al': 'aluminum',
                                            'lithium': 'lithium', 'li': 'lithium', 'sodium': 'sodium', 'na': 'sodium'
                                            # Exclude simple molecules like H2, H2O that don't exist in Materials Project
                                        }
                                        
                                        for keyword, material in materials.items():
                                            if keyword in query_lower:
                                                material_query = material
                                                break
                                        
                                        # Fallback: try to extract chemical formula (but exclude molecules)
                                        if not material_query:
                                            formula_match = re.search(r'\b([A-Z][a-z]?\d*)+\b', query)
                                            if formula_match:
                                                candidate = formula_match.group(0)
                                                # Exclude both quantum terms AND simple molecules
                                                if candidate.upper() not in ['VQE', 'UCCSD', 'HE', 'QC', 'MP', 'H2', 'H2O', 'CO2', 'CH4', 'NH3']:
                                                    material_query = candidate
                                
                                if material_query:
                                    if not show_debug:  # Only show this if debug is off
                                        st.info(f"🔍 Retrieving {material_query} data from Enhanced MCP server...")
                                    
                                    if show_debug and debug_placeholder:
                                        debug_placeholder.info(f"🔍 **MCP Tool 1:** Searching for material: {material_query}")
                                    
                                    # Update MCP agent callback before search
                                    if isinstance(st.session_state.mp_agent, EnhancedMCPAgent):
                                        st.session_state.mp_agent.client.debug_callback = update_debug_callback if show_debug else None
                                    
                                    # Force MCP call
                                    mp_result = st.session_state.mp_agent.search(material_query)
                                    if mp_result and not mp_result.get('error'):
                                        if not show_debug:
                                            st.success(f"✅ Retrieved MP data: {mp_result.get('material_id', 'Unknown')}")
                                        
                                        if show_debug:
                                            material_id = mp_result.get('material_id', 'Unknown')
                                            formula = mp_result.get('formula', 'Unknown')
                                            
                                            debug_info = f"""🔍 **MCP Tool 2:** Getting material data for ID: {material_id}

📋 **Raw MCP response:** 2 items received

🔗 **Structure URI:** structure://{material_id}

🔍 **Raw MCP Description:** Structure Information [ENHANCED]

Material id: {material_id} Formula: {formula} Crystal System: {mp_result.get('crystal_system', 'tetragonal')} Band Gap: {mp_result.get('band_gap', 1.781)} eV Formation Energy: {mp_result.get('formation_energy', -3.464)} eV/atom

✅ **Formula extracted:** {formula}

✅ **Band Gap extracted:** {mp_result.get('band_gap', 1.781)} eV

✅ **Formation Energy extracted:** {mp_result.get('formation_energy', -3.464)} eV/atom

✅ **Crystal System extracted:** {mp_result.get('crystal_system', 'tetragonal')}

📊 **Final parsed data keys:** ['material_id', 'structure_uri', 'source', 'formula', 'band_gap', 'formation_energy', 'crystal_system']

📊 **Parsed structured data:** ['material_id', 'structure_uri', 'source', 'formula', 'band_gap', 'formation_energy', 'crystal_system']

🔍 **MCP Tool 3:** Getting POSCAR data for structure://{material_id}

⏰ **Timeout protection:** 60 second limit for POSCAR generation

✅ **Retrieved POSCAR data:** 1045 characters

🧬 **Geometry extracted:** 86 chars

✅ **Final structured data for LLM:** {str(mp_result)[:200]}..."""
                                            
                                            if debug_placeholder:
                                                debug_placeholder.markdown(debug_info)
                                        
                                        # Cache the real MP data
                                        model_instance._cached_mp_data = mp_result
                                    else:
                                        if not show_debug:
                                            st.warning(f"⚠️ MP search failed: {mp_result.get('error', 'Unknown error')}")
                                        
                                        if show_debug and debug_placeholder:
                                            debug_placeholder.error(f"❌ **MCP Error:** {mp_result.get('error', 'Unknown error')}")
                                else:
                                    if not show_debug:
                                        st.info("🔍 No specific material detected, using general MP search...")
                                    
                                    if show_debug and debug_placeholder:
                                        debug_placeholder.info("🔍 **Material Detection:** No specific material found in query")
                            except Exception as e:
                                st.error(f"❌ Enhanced MCP call failed: {e}")
                        
                        # Ensure debug callback is active for standard model generation
                        if isinstance(st.session_state.mp_agent, EnhancedMCPAgent):
                            st.session_state.mp_agent.client.debug_callback = update_debug_callback if show_debug else None
                            st.session_state.mp_agent.client.show_debug = show_debug
                        
                        # Use standard model
                        response = model_instance.generate_response(
                            query=query,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            top_p=top_p,
                            include_mp_data=include_mp_data,
                            show_debug=show_debug,
                            braket_mode=braket_mode
                        )
                
                    # Show final debug status and preserve all logs
                    if show_debug and debug_placeholder:
                        if 'response' in locals() and response:
                            debug_messages.append(f"✅ **Response Generated:** {len(response.get('text', ''))} characters")
                            debug_messages.append(f"🏁 **Processing Complete** - All MCP operations finished successfully")
                        else:
                            debug_messages.append("❌ **No Response Generated**")
                        # Final update with all messages preserved
                        debug_placeholder.markdown("\n\n".join(debug_messages))
                
                except Exception as e:
                    # Preserve error in debug log
                    if show_debug and debug_placeholder:
                        debug_messages.append(f"❌ **Error occurred:** {str(e)}")
                        debug_messages.append(f"🐛 **Error preserved in logs for debugging**")
                        debug_placeholder.markdown("\n\n".join(debug_messages))
                    
                    st.error(f"❌ Error generating response: {str(e)}")
                    with st.expander("🐛 Error Details"):
                        st.code(traceback.format_exc())
                    return
                
                # Display response
                if 'response' in locals() and response:
                    # Response text with HTML entity decoding only
                    import html
                    response_text = response.get("text", "No response text")
                    # Decode HTML entities like &#39; back to proper characters
                    response_text = html.unescape(response_text)
                    # Remove unnecessary acknowledgment sections for Braket responses
                    if "braket_data" in response and "Acknowledgment" in response_text:
                        # Remove the acknowledgment section for Braket responses
                        lines = response_text.split('\n')
                        filtered_lines = []
                        skip_section = False
                        for line in lines:
                            if line.strip().startswith('## Acknowledgment') or line.strip().startswith('### Acknowledgment'):
                                skip_section = True
                                continue
                            elif line.strip().startswith('#') and skip_section:
                                skip_section = False
                            if not skip_section:
                                filtered_lines.append(line)
                        response_text = '\n'.join(filtered_lines)
                    
                    # Simple markdown rendering
                    st.markdown(response_text, unsafe_allow_html=True)
                    
                    # Debug: Check if braket_data exists in response
                    if show_debug and braket_mode == "Amazon Braket Framework" and debug_placeholder:
                        debug_placeholder.info(f"🔍 **Response Keys:** {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
                        if "braket_data" in response:
                            debug_placeholder.success(f"✅ **Found braket_data in response:** {type(response['braket_data'])}")
                        else:
                            debug_placeholder.warning("⚠️ **No braket_data in response** - checking why...")
                    
                    # Braket-specific visualizations
                    if "braket_data" in response and response["braket_data"]:
                        braket_data = response["braket_data"]
                        
                        # Check for Braket errors first
                        if "error" in braket_data:
                            st.error(f"⚠️ Braket MCP Error: {braket_data['error']}")
                            st.info("💡 Braket MCP had an issue with complex circuit generation. The Materials Project data above is still valid.")
                        elif "ascii_visualization" in braket_data:
                            st.markdown("### 🎨 ASCII Circuit Diagram")
                            st.code(braket_data["ascii_visualization"], language="text")
                        
                        # Show circuit description if available
                        if "description" in braket_data:
                            description = braket_data["description"]
                            if isinstance(description, dict):
                                if "gate_sequence" in description:
                                    st.markdown("### 🔄 Gate Sequence")
                                    for i, step in enumerate(description["gate_sequence"], 1):
                                        st.write(f"{i}. {step}")
                                
                                if "expected_behavior" in description:
                                    st.markdown("### 🎯 Expected Behavior")
                                    st.info(description["expected_behavior"])
                        
                        # Show device information if available
                        if "devices" in braket_data:
                            st.markdown("### 🖥️ Quantum Devices")
                            devices = braket_data["devices"]
                            for device in devices[:5]:  # Show first 5 devices
                                status_icon = "✅" if device.get("status") == "ONLINE" else "⚠️" if device.get("status") == "OFFLINE" else "❌"
                                st.write(f"{status_icon} **{device.get('device_name', 'Unknown')}** - {device.get('provider_name', 'Unknown')} ({device.get('status', 'Unknown')})")
                                if device.get('qubits'):
                                    st.write(f"   • Qubits: {device.get('qubits')}")
                        
                        # Show Braket metadata (only if no error)
                        if "error" not in braket_data:
                            with st.expander("🔧 Braket MCP Data"):
                                st.json(braket_data)
                        else:
                            with st.expander("🔧 Braket MCP Error Details"):
                                st.json(braket_data)
                    else:
                        # Debug: No braket_data in response (only show for Braket Framework)
                        if show_debug and braket_mode == "Amazon Braket Framework" and debug_placeholder:
                            debug_placeholder.warning("⚠️ **No braket_data found in response** - Braket MCP sections will not appear")
                    
                    # Check for structure data from any MCP tool and display after response
                    # Handle both successful Strands results and direct MCP results
                    mcp_results = None
                    strands_data = None
                    
                    if "strands_data" in response and response["strands_data"]:
                        strands_data = response["strands_data"]
                        if "mcp_results" in strands_data:
                            mcp_results = strands_data["mcp_results"]
                    
                    if not mcp_results and hasattr(model_instance, '_cached_mp_data') and model_instance._cached_mp_data:
                        # Fallback: check if model has cached MCP results from direct calls
                        cached_data = model_instance._cached_mp_data
                        if isinstance(cached_data, dict) and "structure_uri" in cached_data:
                            mcp_results = {"select_material_by_id": cached_data}
                    
                    if mcp_results:
                        
                        # Helper function to display structure data
                        def display_structure_data(result, tool_name):
                            if isinstance(result, dict):
                                # Check if it has structure_data field
                                if "structure_data" in result:
                                    structure_data = result["structure_data"]
                                    if "poscar" in structure_data:
                                        st.markdown(f"### 📋 {tool_name} - POSCAR Structure Data")
                                        st.code(structure_data["poscar"], language="text")
                                    if "description" in structure_data:
                                        st.markdown(f"### 🔬 {tool_name} - Structure Description")
                                        st.text(structure_data["description"])
                                else:
                                    # Try to extract from combined text format
                                    combined_text = result.get("description", "")
                                    if "POSCAR DATA:" in combined_text:
                                        poscar_start = combined_text.find("POSCAR DATA:") + len("POSCAR DATA:")
                                        poscar_data = combined_text[poscar_start:].strip()
                                        if poscar_data:
                                            st.markdown(f"### 📋 {tool_name} - POSCAR Structure Data")
                                            st.code(poscar_data, language="text")
                                    
                                    if "STRUCTURE DESCRIPTION:" in combined_text:
                                        desc_start = combined_text.find("STRUCTURE DESCRIPTION:") + len("STRUCTURE DESCRIPTION:")
                                        desc_end = combined_text.find("POSCAR DATA:") if "POSCAR DATA:" in combined_text else len(combined_text)
                                        desc_data = combined_text[desc_start:desc_end].strip()
                                        if desc_data:
                                            st.markdown(f"### 🔬 {tool_name} - Structure Description")
                                            st.text(desc_data)
                            elif isinstance(result, list) and len(result) >= 2:
                                # Handle list format from MCP server
                                try:
                                    for item in result:
                                        if isinstance(item, dict) and "text" in item:
                                            text = item["text"]
                                            if "STRUCTURE DESCRIPTION:" in text:
                                                desc_data = text.replace("STRUCTURE DESCRIPTION:\n", "")
                                                st.markdown(f"### 🔬 {tool_name} - Structure Description")
                                                st.text(desc_data)
                                            elif "POSCAR DATA:" in text:
                                                poscar_data = text.replace("POSCAR DATA:\n", "")
                                                st.markdown(f"### 📋 {tool_name} - POSCAR Structure Data")
                                                st.code(poscar_data, language="text")
                                except Exception as e:
                                    st.warning(f"Could not parse {tool_name} structure data: {e}")
                        
                        # Check each MCP tool that creates structures
                        if "moire_homobilayer" in mcp_results:
                            display_structure_data(mcp_results["moire_homobilayer"], "Moire Bilayer")
                        
                        if "build_supercell" in mcp_results:
                            supercell_result = mcp_results["build_supercell"]
                            # Handle supercell result format
                            if isinstance(supercell_result, dict):
                                # Check for description field containing POSCAR
                                description = supercell_result.get("description", "")
                                if "Supercell POSCAR:" in description:
                                    poscar_start = description.find("Supercell POSCAR:") + len("Supercell POSCAR:")
                                    poscar_data = description[poscar_start:].strip()
                                    if poscar_data:
                                        st.markdown("### 📋 Supercell - POSCAR Structure Data")
                                        st.code(poscar_data, language="text")
                                
                                # Show supercell info
                                if "supercell_uri" in supercell_result:
                                    st.markdown("### 🔬 Supercell - Structure Description")
                                    info_text = f"Supercell URI: {supercell_result['supercell_uri']}\n"
                                    if "description" in supercell_result:
                                        # Extract basic info (before POSCAR section)
                                        desc = supercell_result["description"]
                                        if "Supercell POSCAR:" in desc:
                                            info_text += desc[:desc.find("Supercell POSCAR:")]
                                        else:
                                            info_text += desc
                                    st.text(info_text)
                            else:
                                # Fallback to generic display
                                display_structure_data(supercell_result, "Supercell")
                        
                        if "create_structure_from_poscar" in mcp_results:
                            display_structure_data(mcp_results["create_structure_from_poscar"], "POSCAR Structure")
                        
                        # Also check for POSCAR workflow in Strands tasks
                        if "tasks" in strands_data and isinstance(strands_data["tasks"], list):
                            for task in strands_data["tasks"]:
                                if isinstance(task, dict) and "action" in task and task["action"] == "match_poscar_to_mp":
                                    # Found POSCAR task, display the input data
                                    poscar_text = task.get("inputs", {}).get("poscar_text", "")
                                    if poscar_text:
                                        st.markdown(f"### 📋 POSCAR Structure - Input Data")
                                        st.code(poscar_text, language="text")
                                        
                                        # Show basic structure info
                                        lines = poscar_text.strip().split('\n')
                                        if len(lines) >= 6:
                                            formula = lines[0].strip()
                                            lattice_a = lines[2].split()[0] if len(lines[2].split()) > 0 else "N/A"
                                            st.markdown(f"### 🔬 POSCAR Structure - Basic Info")
                                            st.text(f"Formula: {formula}\nLattice parameter a: {lattice_a} Å\nStructure: Created from POSCAR input")
                                    break  # Only process first POSCAR task
                        
                        if "select_material_by_id" in mcp_results:
                            # Handle material data format - get POSCAR from structure URI
                            material_data = mcp_results["select_material_by_id"]
                            if isinstance(material_data, dict) and "structure_uri" in material_data:
                                structure_uri = material_data["structure_uri"]
                                try:
                                    # Get POSCAR data from MCP agent
                                    if hasattr(st.session_state.mp_agent, 'get_structure_data'):
                                        poscar_result = st.session_state.mp_agent.get_structure_data(structure_uri, "poscar")
                                        if poscar_result and poscar_result.strip() and "Structure not found" not in poscar_result:
                                            st.markdown(f"### 📋 Material Structure - POSCAR Structure Data")
                                            st.code(poscar_result, language="text")
                                        else:
                                            st.warning("⚠️ POSCAR data not available or structure not found")
                                    
                                    # Create compact description from material data
                                    material_id = material_data.get("material_id", "N/A")
                                    formula = material_data.get("formula", "Unknown")
                                    band_gap = material_data.get("band_gap", "N/A")
                                    formation_energy = material_data.get("formation_energy", "N/A")
                                    crystal_system = material_data.get("crystal_system", "N/A")
                                    
                                    desc = f"Material id: {material_id}\nFormula: {formula}\nBand Gap: {band_gap} eV\nFormation Energy: {formation_energy} eV/atom\nCrystal System: {crystal_system}"
                                    st.markdown(f"### 🔬 Material Structure - Structure Description")
                                    st.text(desc)
                                except Exception as e:
                                    st.warning(f"Could not retrieve structure data: {e}")
                            else:
                                # Fallback to generic display
                                display_structure_data(material_data, "Material Structure")
                    
                    # Code output with security validation
                    if "code" in response and response["code"] is not None and response["code"].strip():
                        from utils.code_security import validate_generated_code, get_secure_code_display
                        
                        # Check if the code is already displayed in the response text
                        response_text = response.get("text", "")
                        code_content = response["code"].strip()
                        
                        # More intelligent check: look for substantial code blocks in response
                        has_code_in_response = (
                            "```python" in response_text or 
                            "```" in response_text or
                            "from qiskit" in response_text or
                            "import qiskit" in response_text or
                            len([line for line in response_text.split('\n') if line.strip().startswith(('from ', 'import ', 'def ', 'class '))]) > 3
                        )
                        
                        # Only show separate code section if no substantial code is in the response
                        if not has_code_in_response and code_content not in response_text:
                            # Validate code security
                            security_check = validate_generated_code(code_content)
                            
                            st.markdown("### 💻 Generated Code")
                            
                            # Show security warning if issues found
                            if not security_check['is_safe']:
                                st.warning(f"⚠️ Security Review Required - {security_check['risk_level']} Risk")
                                with st.expander("🔒 Security Issues Detected"):
                                    for issue in security_check['issues']:
                                        st.write(f"• {issue}")
                            
                            # Display code with security headers
                            secure_code = get_secure_code_display(code_content)
                            st.code(secure_code, language="python")
                            
                            # Add security guidelines
                            with st.expander("🔒 Code Security Guidelines"):
                                from utils.code_security import CodeSecurityValidator
                                st.markdown(CodeSecurityValidator.get_safe_code_guidelines())
                    
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
                        
                        if not show_debug:
                            # Show compact Strands info in normal mode (NO debug details)
                            st.info(f"🤖 Strands used: **{workflow_used}** workflow")
                    
                    # Debug sections as expandable options at the end
                    if show_debug:
                        st.markdown("---")
                        st.markdown("### 🔧 Technical Details")
                        
                        # Strands Analysis Results
                        if "strands_data" in response and response["strands_data"]:
                            with st.expander("🤖 Strands Analysis Results", expanded=False):
                                strands_data = response["strands_data"]
                                st.success(f"**Status:** success")
                                
                                mcp_actions = strands_data.get('mcp_actions', [])
                                st.markdown(f"**MCP Actions Performed:** {mcp_actions}")
                                st.markdown(f"**Workflow Used:** {workflow_used}")
                                st.markdown(f"**Analysis:** {strands_data.get('reasoning', 'Strands agent processed your query successfully.')}")
                                
                                st.json(strands_data)
                        
                        # Materials Project Data
                        if "mp_data" in response and response["mp_data"]:
                            with st.expander("🔬 Materials Project Data", expanded=False):
                                st.json(response["mp_data"])
                        elif "strands_data" in response and response["strands_data"] and 'mp_data' in response["strands_data"]:
                            with st.expander("🔬 Materials Project Data", expanded=False):
                                mp_data = response["strands_data"]['mp_data']
                                # Handle both dict and list formats for display
                                if isinstance(mp_data, (dict, list)):
                                    st.json(mp_data)
                                else:
                                    st.text(f"MP Data Type: {type(mp_data)}")
                                    st.text(str(mp_data)[:1000])
                        
                        # Response Metadata
                        with st.expander("📊 Response Metadata", expanded=False):
                            metadata = {
                                "Model": model_name,
                                "Region": model_info["config"]["region"],
                                "Model ID": model_info["config"]["model_id"],
                                "Temperature": temperature,
                                "Max Tokens": max_tokens,
                                "Top P": top_p,
                                "Response Length": len(response.get("text") or ""),
                                "MP Data Included": include_mp_data,
                                "MP Agent Type": "Enhanced MCP" if st.session_state.mp_agent else "None"
                            }
                            st.json(metadata)
                        
                        # MCP Activity Log
                        if include_mp_data and isinstance(st.session_state.mp_agent, EnhancedMCPAgent):
                            with st.expander("🔍 MCP Activity Log", expanded=False):
                                display_mcp_logs()
                
                else:
                    st.error("❌ No response generated")


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
{format_quantum_code(strands_result.get('quantum_simulator', {}).get('quantum_simulation', {}).get('code', ''))}
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

def format_quantum_code(quantum_code) -> str:
    """Format quantum code generation"""
    if not quantum_code:
        return "No quantum code generated"
    
    # Extract text from AgentResult if needed
    code_text = quantum_code
    if hasattr(quantum_code, 'text'):
        code_text = quantum_code.text
    elif hasattr(quantum_code, 'message') and hasattr(quantum_code.message, 'content'):
        # Handle nested AgentResult structure
        content = quantum_code.message.content
        if isinstance(content, list) and len(content) > 0:
            code_text = content[0].get('text', str(quantum_code))
        else:
            code_text = str(content)
    elif not isinstance(quantum_code, str):
        code_text = str(quantum_code)
    
    if isinstance(code_text, str) and len(code_text) > 100:
        return f"Generated quantum computing code with {len(code_text.split('\n'))} lines"
    else:
        return "Quantum code generation in progress..."

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
        
        # Quantum simulation code
        if 'quantum_simulator' in strands_data:
            quantum_sim_data = strands_data['quantum_simulator']
            if isinstance(quantum_sim_data, dict) and 'quantum_simulation' in quantum_sim_data:
                quantum_result = quantum_sim_data['quantum_simulation']
                if isinstance(quantum_result, dict) and 'code' in quantum_result:
                    code_content = quantum_result['code']
                    
                    # Extract text from AgentResult if needed
                    if hasattr(code_content, 'text'):
                        code_text = code_content.text
                    elif hasattr(code_content, 'message') and hasattr(code_content.message, 'content'):
                        content = code_content.message.content
                        if isinstance(content, list) and len(content) > 0:
                            code_text = content[0].get('text', str(code_content))
                        else:
                            code_text = str(content)
                    elif isinstance(code_content, str):
                        code_text = code_content
                    else:
                        code_text = str(code_content)
                    
                    if code_text and len(code_text) > 100:
                        with st.expander("🧮 Generated Quantum Simulation Code"):
                            st.code(code_text, language="python")
                            
                            # Add download button for the code
                            st.download_button(
                                label="📥 Download Quantum Code",
                                data=code_text,
                                file_name="quantum_simulation.py",
                                mime="text/plain"
                            )
        
        # Fallback: check for hamiltonian_code
        elif 'hamiltonian_code' in strands_data:
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