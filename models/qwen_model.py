import json
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
from .base_model import BaseQiskitGenerator

logger = logging.getLogger(__name__)

class QwenModel(BaseQiskitGenerator):
    """Qwen 3-32B model implementation for us-east-1"""
    
    def __init__(self, mp_agent: Optional[Any] = None, region_name: str = "us-east-1"):
        super().__init__(mp_agent, region_name)
        self.model_name = "Qwen 3-32B"
        self.bedrock_client_dict = None  # Store as dict for tested pattern
    
    def set_model(self, model_id: str = "qwen.qwen3-32b-v1:0"):
        """Initialize Qwen 3-32B using tested notebook pattern"""
        if not boto3:
            raise ImportError("boto3 not available")
        
        # Use session pattern from tested notebook
        session = boto3.Session(region_name=self.region_name)
        client = session.client("bedrock-runtime")
        
        # Store as dict like in notebook (critical for Qwen)
        self.bedrock_client_dict = {
            "client": client,
            "model_id": model_id
        }
        self.llm_enabled = True
        logger.info(f"Qwen 3-32B enabled in {self.region_name}")
    
    def _call_llm(self, prompt: str, **kwargs) -> str:
        """Call Qwen 3-32B using tested notebook pattern"""
        if not self.llm_enabled or not self.bedrock_client_dict:
            raise RuntimeError("Qwen 3-32B not initialized")
        
        # Qwen-specific message format - prompt already contains system instructions
        body = {
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": kwargs.get("temperature", 0.15),
            "max_tokens": kwargs.get("max_tokens", 2000)
        }
        
        try:
            # Critical: modelId as top-level parameter (NOT in body) for Qwen
            response = self.bedrock_client_dict["client"].invoke_model(
                modelId=self.bedrock_client_dict["model_id"],
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body)
            )
        
            # Parse Qwen response format
            raw_body = response["body"].read()
            parsed = json.loads(raw_body)
            completion = parsed["choices"][0]["message"]["content"].strip()
            
            # Clean up code blocks
            completion = completion.replace("```python", "").replace("```", "").strip()
            return completion if completion else "No response generated"
    
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ValidationException":
                raise RuntimeError(f"Qwen validation error: {e}")
            elif error_code == "AccessDeniedException":
                raise RuntimeError("Access denied to Qwen. Check IAM permissions.")
            elif error_code == "ModelNotReadyException":
                raise RuntimeError("Qwen model not ready. Try again later.")
            else:
                raise RuntimeError(f"Qwen error: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected Qwen error: {e}")