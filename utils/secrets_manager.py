import json
import logging
import boto3
import time
from botocore.exceptions import ClientError
from typing import Optional

logger = logging.getLogger(__name__)

def get_mp_api_key(secret_name: str = "materials-project/api-key", region_name: str = "us-east-1") -> Optional[str]:
    """
    Retrieve Materials Project API key from AWS Secrets Manager
    
    Args:
        secret_name: Name of the secret in Secrets Manager
        region_name: AWS region where the secret is stored
        
    Returns:
        API key string or None if not found
    """
    # Audit log secret access
    logger.info(f"Accessing secret {secret_name} from region {region_name} at {time.time()}")
    
    try:
        # Create Secrets Manager client
        secrets_client = boto3.client('secretsmanager', region_name=region_name)
        
        # Get the secret value
        response = secrets_client.get_secret_value(SecretId=secret_name)
        
        # Parse the secret
        if 'SecretString' in response:
            secret = response['SecretString']
            try:
                # Try to parse as JSON first
                secret_dict = json.loads(secret)
                # Look for common key names
                for key in ['api_key', 'apikey', 'key', 'MP_API_KEY']:
                    if key in secret_dict:
                        return secret_dict[key]
                # If no standard key found, return the first value
                if secret_dict:
                    return list(secret_dict.values())[0]
            except json.JSONDecodeError:
                # If not JSON, assume it's a plain string
                return secret.strip()
        
        logger.warning(f"No SecretString found in secret {secret_name}")
        return None
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'DecryptionFailureException':
            logger.error("Secrets Manager can't decrypt the protected secret text using the provided KMS key")
        elif error_code == 'InternalServiceErrorException':
            logger.error("An error occurred on the server side")
        elif error_code == 'InvalidParameterException':
            logger.error("Invalid parameter provided to Secrets Manager")
        elif error_code == 'InvalidRequestException':
            logger.error("Invalid request to Secrets Manager")
        elif error_code == 'ResourceNotFoundException':
            logger.error(f"Secret {secret_name} not found in Secrets Manager")
        else:
            logger.error(f"Unexpected error retrieving secret: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None

def store_mp_api_key(api_key: str, secret_name: str = "materials-project/api-key", 
                     region_name: str = "us-east-1") -> bool:
    """
    Store Materials Project API key in AWS Secrets Manager
    
    Args:
        api_key: The API key to store
        secret_name: Name for the secret in Secrets Manager
        region_name: AWS region to store the secret
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create Secrets Manager client
        secrets_client = boto3.client('secretsmanager', region_name=region_name)
        
        # Create secret value
        secret_value = json.dumps({"MP_API_KEY": api_key})
        
        try:
            # Try to create new secret
            response = secrets_client.create_secret(
                Name=secret_name,
                Description="Materials Project API Key for Quantum Matter App",
                SecretString=secret_value
            )
            logger.info(f"Created new secret {secret_name}")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceExistsException':
                # Secret already exists, update it
                response = secrets_client.update_secret(
                    SecretId=secret_name,
                    SecretString=secret_value
                )
                logger.info(f"Updated existing secret {secret_name}")
                return True
            else:
                raise e
                
    except ClientError as e:
        logger.error(f"Error storing secret: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error storing secret: {e}")
        return False