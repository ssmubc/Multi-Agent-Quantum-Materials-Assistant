import json
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
from .base_model import BaseQiskitGenerator

logger = logging.getLogger(__name__)

class ClaudeSonnetModel(BaseQiskitGenerator):
    """Claude Sonnet 4.5 model implementation for us-east-1"""
    
    def __init__(self, mp_agent: Optional[Any] = None, region_name: str = "us-east-1"):
        super().__init__(mp_agent, region_name)
        self.model_name = "Claude Sonnet 4.5"
    
    def set_model(self, model_id: str = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"):
        """Initialize Claude Sonnet 4.5 model"""
        if not boto3:
            raise ImportError("boto3 not available")
        
        self.model_id = model_id
        self.bedrock_client = boto3.client("bedrock-runtime", region_name=self.region_name)
        self.llm_enabled = True
        logger.info(f"Claude Sonnet 4.5 enabled in {self.region_name}")
    
    def _call_llm(self, prompt: str, **kwargs) -> str:
        """Call Claude Sonnet 4.5 via Bedrock"""
        if not self.llm_enabled or not self.bedrock_client:
            raise RuntimeError("Claude Sonnet 4.5 not initialized")
        
        # Claude Sonnet request format - use Anthropic Messages API format
        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}]
                }
            ],
            "max_tokens": kwargs.get("max_tokens", 1000),
            "temperature": kwargs.get("temperature", 0.7),
            "anthropic_version": "bedrock-2023-05-31"
        }
        
        # Claude models don't allow both temperature and top_p
        # Use temperature by default, but allow top_p override
        if "top_p" in kwargs and kwargs["top_p"] != 0.9:
            del request_body["temperature"]
            request_body["top_p"] = kwargs["top_p"]
        
        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json"
            )
            
            response_body = json.loads(response["body"].read())
            
            # Extract text from Claude Sonnet response (Anthropic format)
            if "content" in response_body:
                content = response_body["content"]
                if content and len(content) > 0:
                    return content[0].get("text", "")
            
            return "No response generated"
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ValidationException":
                raise RuntimeError(f"Claude Sonnet 4.5 validation error: {e}")
            elif error_code == "AccessDeniedException":
                raise RuntimeError("Access denied to Claude Sonnet 4.5. Check IAM permissions.")
            else:
                raise RuntimeError(f"Claude Sonnet 4.5 error: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected Claude Sonnet 4.5 error: {e}")