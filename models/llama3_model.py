import json
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
from .base_model import BaseQiskitGenerator

logger = logging.getLogger(__name__)

class Llama3Model(BaseQiskitGenerator):
    """Llama 3 70B Instruct model implementation for us-west-2"""
    
    def __init__(self, mp_agent: Optional[Any] = None, region_name: str = "us-west-2"):
        super().__init__(mp_agent, region_name)
        self.model_name = "Llama 3 70B"
    
    def set_model(self, model_id: str = "meta.llama3-70b-instruct-v1:0"):
        """Initialize Llama 3 70B model"""
        if not boto3:
            raise ImportError("boto3 not available")
        
        self.model_id = model_id
        self.bedrock_client = boto3.client("bedrock-runtime", region_name=self.region_name)
        self.llm_enabled = True
        logger.info(f"Llama 3 70B enabled in {self.region_name}")
    
    def _call_llm(self, prompt: str, **kwargs) -> str:
        """Call Llama 3 70B via Bedrock"""
        if not self.llm_enabled or not self.bedrock_client:
            raise RuntimeError("Llama 3 70B not initialized")
        
        # Llama 3 request format
        request_body = {
            "prompt": prompt,
            "temperature": kwargs.get("temperature", 0.7),
            "max_gen_len": kwargs.get("max_tokens", 1000),
            "top_p": kwargs.get("top_p", 0.9)
        }
        
        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json"
            )
            
            response_body = json.loads(response["body"].read())
            
            # Extract text from Llama 3 response
            if "generation" in response_body:
                return response_body["generation"]
            elif "outputs" in response_body and len(response_body["outputs"]) > 0:
                return response_body["outputs"][0].get("text", "")
            elif "completion" in response_body:
                return response_body["completion"]
            
            return "No response generated"
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ValidationException":
                raise RuntimeError(f"Llama 3 validation error: {e}")
            elif error_code == "AccessDeniedException":
                raise RuntimeError("Access denied to Llama 3. Check IAM permissions.")
            elif error_code == "ModelNotReadyException":
                raise RuntimeError("Llama 3 model not ready. Try again later.")
            else:
                raise RuntimeError(f"Llama 3 error: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected Llama 3 error: {e}")