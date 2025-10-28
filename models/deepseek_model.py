import json
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
from .base_model import BaseQiskitGenerator

logger = logging.getLogger(__name__)

class DeepSeekModel(BaseQiskitGenerator):
    """DeepSeek R1 model implementation for us-east-1 (cross-region inference profile)"""
    
    def __init__(self, mp_agent: Optional[Any] = None, region_name: str = "us-east-1"):
        super().__init__(mp_agent, region_name)
        self.model_name = "DeepSeek R1"
    
    def set_model(self, model_id: str = "us.deepseek.r1-v1:0"):
        """Initialize DeepSeek R1 model"""
        if not boto3:
            raise ImportError("boto3 not available")
        
        self.model_id = model_id
        self.bedrock_client = boto3.client("bedrock-runtime", region_name=self.region_name)
        self.llm_enabled = True
        logger.info(f"DeepSeek R1 enabled in {self.region_name}")
    
    def _call_llm(self, prompt: str, **kwargs) -> str:
        """Call DeepSeek R1 via Bedrock"""
        if not self.llm_enabled or not self.bedrock_client:
            raise RuntimeError("DeepSeek R1 not initialized")
        
        # DeepSeek R1 request format - prompt already contains system instructions
        request_body = {
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
            
            
            # Extract text from DeepSeek R1 response - handle reasoning format
            if "choices" in response_body and response_body["choices"]:
                message = response_body["choices"][0].get("message", {})
                # DeepSeek R1 puts response in reasoning_content when content is None
                content = message.get("content")
                if content:
                    return content.strip()
                # Fallback to reasoning_content for DeepSeek R1's thinking process
                reasoning_content = message.get("reasoning_content")
                if reasoning_content:
                    return reasoning_content.strip()
            elif "content" in response_body:
                return response_body["content"].strip()
            elif "text" in response_body:
                return response_body["text"].strip()
            elif "output" in response_body:
                return response_body["output"].strip()
            elif "generation" in response_body:
                return response_body["generation"].strip()
            
            return "No response generated"
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ValidationException":
                raise RuntimeError(f"DeepSeek R1 validation error: {e}")
            elif error_code == "AccessDeniedException":
                raise RuntimeError("Access denied to DeepSeek R1. Check IAM permissions.")
            elif error_code == "ModelNotReadyException":
                raise RuntimeError("DeepSeek R1 model not ready. Try again later.")
            else:
                raise RuntimeError(f"DeepSeek R1 error: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected DeepSeek R1 error: {e}")