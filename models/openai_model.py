import json
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
from .base_model import BaseQiskitGenerator

logger = logging.getLogger(__name__)

class OpenAIModel(BaseQiskitGenerator):
    """OpenAI GPT OSS model implementation for us-west-2"""
    
    def __init__(self, mp_agent: Optional[Any] = None, region_name: str = "us-west-2"):
        super().__init__(mp_agent, region_name)
        self.model_name = "OpenAI GPT OSS"
    
    def set_model(self, model_id: str = "openai.gpt-oss-20b-1:0"):
        """Initialize OpenAI GPT OSS model"""
        if not boto3:
            raise ImportError("boto3 not available")
        
        self.model_id = model_id
        self.bedrock_client = boto3.client("bedrock-runtime", region_name=self.region_name)
        self.llm_enabled = True
        logger.info(f"OpenAI GPT OSS enabled in {self.region_name}")
    
    def _call_llm(self, prompt: str, **kwargs) -> str:
        """Call OpenAI GPT OSS via Bedrock"""
        if not self.llm_enabled or not self.bedrock_client:
            raise RuntimeError("OpenAI GPT OSS not initialized")
        
        # OpenAI GPT OSS request format - prompt already contains system instructions
        request_body = {
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "top_p": kwargs.get("top_p", 0.9)
        }
        
        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json"
            )
            
            response_body = json.loads(response["body"].read())
            
            # Extract text from OpenAI response
            if "choices" in response_body and len(response_body["choices"]) > 0:
                choice = response_body["choices"][0]
                if "message" in choice:
                    return choice["message"].get("content", "")
                else:
                    return choice.get("text", "")
            elif "completion" in response_body:
                return response_body["completion"]
            elif "generated_text" in response_body:
                return response_body["generated_text"]
            
            return "No response generated"
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ValidationException":
                raise RuntimeError(f"OpenAI GPT validation error: {e}")
            elif error_code == "AccessDeniedException":
                raise RuntimeError("Access denied to OpenAI GPT. Check IAM permissions.")
            elif error_code == "ModelNotReadyException":
                raise RuntimeError("OpenAI GPT model not ready. Try again later.")
            else:
                raise RuntimeError(f"OpenAI GPT error: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected OpenAI GPT error: {e}")