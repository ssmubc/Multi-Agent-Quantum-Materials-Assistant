import json
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
from .base_model import BaseQiskitGenerator

logger = logging.getLogger(__name__)

class ClaudeOpusModel(BaseQiskitGenerator):
    """Claude Opus 4 model implementation using cross-region inference profile"""
    
    def __init__(self, mp_agent: Optional[Any] = None, region_name: str = "us-east-1"):
        super().__init__(mp_agent, region_name)
        self.model_name = "Claude Opus 4.1"
    
    def set_model(self, model_id: str = "us.anthropic.claude-opus-4-1-20250805-v1:0"):
        """Initialize Claude Opus 4 model using inference profile"""
        if not boto3:
            raise ImportError("boto3 not available")
        
        self.model_id = model_id
        self.bedrock_client = boto3.client("bedrock-runtime", region_name=self.region_name)
        self.llm_enabled = True
        logger.info(f"Claude Opus 4.1 enabled in {self.region_name}")
    
    def _call_llm(self, prompt: str, **kwargs) -> str:
        """Call Claude Opus 4.1 via Bedrock"""
        if not self.llm_enabled or not self.bedrock_client:
            raise RuntimeError("Claude Opus 4.1 not initialized")
        
        # Claude Opus 4.1 request format for inference profile
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": kwargs.get("max_tokens", 2000),
            "temperature": kwargs.get("temperature", 0.15),
            "top_p": kwargs.get("top_p", 0.9)
        }
        
        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response["body"].read())
            
            # Debug: Log the raw response
            logger.info(f"Claude Opus 4.1 raw response: {json.dumps(response_body, indent=2)}")
            
            # Extract text from Claude Opus 4.1 response
            if "content" in response_body and response_body["content"]:
                content = response_body["content"][0].get("text", "")
                if content:
                    return content.strip()
            elif "completion" in response_body:
                return response_body["completion"].strip()
            elif "text" in response_body:
                return response_body["text"].strip()
            
            return "No response generated"
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            
            # Show detailed error information for debugging
            detailed_error = f"AWS Error: {error_code} - {error_message}"
            

        except Exception as e:
            raise RuntimeError(f"Unexpected Claude Opus 4.1 error: {e}")