import streamlit as st
import os
import json
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import traceback

# Import our model classes
from models.nova_pro_model import NovaProModel
from models.llama4_model import Llama4Model
from models.llama3_model import Llama3Model
from models.openai_model import OpenAIModel
from utils.materials_project_agent import MaterialsProjectAgent
from utils.secrets_manager import get_mp_api_key
from demo_mode import get_demo_response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Quantum Matter LLM Testing Platform",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
            source = f"IAM Role via profile '{profile_name}'"
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
    
    # Option 1: Use AWS Secrets Manager
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
            st.session_state.mp_agent = MaterialsProjectAgent(api_key=mp_api_key)
            st.sidebar.success("✅ Materials Project API configured")
            
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
    if st.session_state.models_initialized:
        return
    
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
        }
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
    
    # Initialize demo_mode
    demo_mode = False
    
    # Initialize models if AWS is configured
    if aws_status:
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
        st.subheader("🎯 Select Model")
        if demo_mode:
            available_models = ["Nova Pro", "Llama 4 Scout", "Llama 3 70B", "OpenAI GPT OSS"]
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
                          "Llama 3 70B": "us-west-2", "OpenAI GPT OSS": "us-west-2"}
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
                generate_response(selected_model, query, temperature, max_tokens, top_p, include_mp_data, demo_mode)

def generate_response(model_name: str, query: str, temperature: float, max_tokens: int, top_p: float, include_mp_data: bool, demo_mode: bool = False):
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
                # Generate response
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
                    
                    # Code output (if any)
                    if "code" in response:
                        st.markdown("### 💻 Generated Code")
                        st.code(response["code"], language="python")
                    
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
                            "Response Length": len(response.get("text", "")),
                        }
                        st.json(metadata)
                
                else:
                    st.error("❌ No response generated")
                    
            except Exception as e:
                st.error(f"❌ Error generating response: {str(e)}")
                with st.expander("🐛 Error Details"):
                    st.code(traceback.format_exc())

if __name__ == "__main__":
    main()