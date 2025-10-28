# Files to Include in Beanstalk Deployment ZIP

## Core Application Files
- `app.py` - Main Streamlit application
- `auth.py` - Simple authentication
- `demo_mode.py` - Demo responses for all 6 models
- `requirements.txt` - Python dependencies

## Model Classes (models/ folder)
- `models/__init__.py` - Empty file for Python package
- `models/base_model.py` - Base class with system prompt
- `models/nova_pro_model.py` - Nova Pro implementation
- `models/llama4_model.py` - Llama 4 Scout implementation  
- `models/llama3_model.py` - Llama 3 70B implementation
- `models/openai_model.py` - OpenAI GPT implementation
- `models/qwen_model.py` - Qwen 3-32B implementation
- `models/deepseek_model.py` - DeepSeek R1 implementation

## Utilities (utils/ folder)
- `utils/__init__.py` - Empty file for Python package
- `utils/materials_project_agent.py` - Materials Project API client
- `utils/secrets_manager.py` - AWS Secrets Manager utilities

## AWS Beanstalk Configuration
- `Dockerfile` - Container configuration
- `Dockerrun.aws.json` - Beanstalk Docker configuration
- `.ebextensions/01_streamlit.config` - Beanstalk environment config

## Optional Files (if you have them)
- `.gitignore` - Git ignore rules
- `README.md` - Documentation

## DO NOT INCLUDE
- `__pycache__/` folders
- `.git/` folder
- Virtual environment folders
- IDE configuration files
- Test files
- `deepseek_generator_fixed.py` (standalone test file)
- `test_deepseek.py` (test file)
- Any `.pyc` files

## ZIP Structure
```
quantum-matter-app-deepseek.zip
├── app.py
├── auth.py
├── demo_mode.py
├── requirements.txt
├── Dockerfile
├── Dockerrun.aws.json
├── .ebextensions/
│   └── 01_streamlit.config
├── models/
│   ├── __init__.py
│   ├── base_model.py
│   ├── nova_pro_model.py
│   ├── llama4_model.py
│   ├── llama3_model.py
│   ├── openai_model.py
│   ├── qwen_model.py
│   └── deepseek_model.py
└── utils/
    ├── __init__.py
    ├── materials_project_agent.py
    └── secrets_manager.py
```