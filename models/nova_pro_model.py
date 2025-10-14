import json
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
from .base_model import BaseQiskitGenerator

logger = logging.getLogger(__name__)

class NovaProModel(BaseQiskitGenerator):
    """Nova Pro model implementation for us-east-1"""
    
    def __init__(self, mp_agent: Optional[Any] = None, region_name: str = "us-east-1"):
        super().__init__(mp_agent, region_name)
        self.model_name = "Nova Pro"
    
    def set_model(self, model_id: str = "amazon.nova-pro-v1:0"):
        """Initialize Nova Pro model"""
        if not boto3:
            raise ImportError("boto3 not available")
        
        self.model_id = model_id
        self.bedrock_client = boto3.client("bedrock-runtime", region_name=self.region_name)
        self.llm_enabled = True
        logger.info(f"Nova Pro enabled in {self.region_name}")
    
    def _call_llm(self, prompt: str, **kwargs) -> str:
        """Call Nova Pro via Bedrock"""
        if not self.llm_enabled or not self.bedrock_client:
            raise RuntimeError("Nova Pro not initialized")
        
        # Nova Pro request format
        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            "inferenceConfig": {
                "temperature": kwargs.get("temperature", 0.7),
                "maxTokens": kwargs.get("max_tokens", 1000),
                "topP": kwargs.get("top_p", 0.9)
            }
        }
        
        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json"
            )
            
            response_body = json.loads(response["body"].read())
            
            # Extract text from Nova Pro response
            if "output" in response_body and "message" in response_body["output"]:
                content = response_body["output"]["message"]["content"]
                if content and len(content) > 0:
                    return content[0].get("text", "")
            
            return "No response generated"
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ValidationException":
                raise RuntimeError(f"Nova Pro validation error: {e}")
            elif error_code == "AccessDeniedException":
                raise RuntimeError("Access denied to Nova Pro. Check IAM permissions.")
            else:
                raise RuntimeError(f"Nova Pro error: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected Nova Pro error: {e}")