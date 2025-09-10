"""
Service for testing LLM provider API keys and functionality.
"""
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class ProviderTestService:
    """Service to test different LLM providers with their API keys."""
    
    # Simple test message for provider validation
    TEST_MESSAGES = [
        {"role": "user", "content": "Say 'Hello' in one word only."}
    ]
    
    @classmethod
    def test_provider(cls, provider: str, model_name: str, api_key: str) -> Tuple[bool, str, Dict]:
        """
        Test if the provider API key and model work correctly.
        
        Args:
            provider: Provider name (openai, gemini, deepseek)
            model_name: Model name to test
            api_key: API key to test
            
        Returns:
            Tuple of (success: bool, message: str, details: dict)
        """
        try:
            logger.info(f"Testing {provider} provider with model {model_name}")
            
            if provider == "openai":
                return cls._test_openai(model_name, api_key)
            elif provider == "gemini":
                # add logs
                logger.info(f"Testing {provider} provider with model {model_name}")
                return cls._test_gemini(model_name, api_key)
            elif provider == "deepseek":
                return cls._test_deepseek(model_name, api_key)
            else:
                return False, f"Unsupported provider: {provider}", {}
                
        except Exception as e:
            logger.error(f"Error testing {provider} provider: {str(e)}")
            return False, f"Provider test failed: {str(e)}", {"error": str(e)}
    
    @classmethod
    def _test_openai(cls, model_name: str, api_key: str) -> Tuple[bool, str, Dict]:
        """Test OpenAI API key and model."""
        try:
            from common.llm.openai_client import OpenAIChat
            
            client = OpenAIChat(model=model_name, api_key=api_key)
            response, usage, actual_model = client.chat(
                messages=cls.TEST_MESSAGES,
                max_tokens=10,
                temperature=0.1,
                timeout_s=30
            )
            
            if response and len(response.strip()) > 0:
                return True, "OpenAI API key and model are working correctly", {
                    "response": response.strip(),
                    "usage": usage,
                    "model_used": actual_model
                }
            else:
                return False, "OpenAI API returned empty response", {"usage": usage}
                
        except Exception as e:
            error_msg = str(e).lower()
            if "unauthorized" in error_msg or "invalid" in error_msg or "401" in error_msg:
                return False, "Invalid OpenAI API key", {"error": str(e)}
            elif "not found" in error_msg or "does not exist" in error_msg or "404" in error_msg:
                return False, f"Model '{model_name}' not found or not accessible", {"error": str(e)}
            elif "quota" in error_msg or "billing" in error_msg or "429" in error_msg:
                return False, "OpenAI quota exceeded or billing issue", {"error": str(e)}
            else:
                return False, f"OpenAI API error: {str(e)}", {"error": str(e)}
    
    @classmethod
    def _test_gemini(cls, model_name: str, api_key: str) -> Tuple[bool, str, Dict]:
        """Test Gemini API key and model."""
        try:
            from common.llm.gemini_client import GeminiChat
            
            client = GeminiChat(model=model_name, api_key=api_key)
            
            response, usage, actual_model = client.chat(
                messages=cls.TEST_MESSAGES,
                max_tokens=10,
                temperature=0.1,
                timeout_s=30
            )
            
            if response and len(response.strip()) > 0:
                return True, "Gemini API key and model are working correctly", {
                    "response": response.strip(),
                    "usage": usage,
                    "model_used": actual_model
                }
            else:
                return False, "Gemini API returned empty response", {"usage": usage}
                
        except Exception as e:
            error_msg = str(e).lower()
            if "unauthorized" in error_msg or "forbidden" in error_msg or "401" in error_msg or "403" in error_msg:
                return False, "Invalid Gemini API key", {"error": str(e)}
            elif "not found" in error_msg or "does not exist" in error_msg or "404" in error_msg:
                return False, f"Model '{model_name}' not found or not accessible", {"error": str(e)}
            elif "quota" in error_msg or "limit" in error_msg or "429" in error_msg:
                return False, "Gemini quota exceeded or rate limit hit", {"error": str(e)}
            else:
                return False, f"Gemini API error: {str(e)}", {"error": str(e)}
    
    @classmethod
    def _test_deepseek(cls, model_name: str, api_key: str) -> Tuple[bool, str, Dict]:
        """Test DeepSeek API key and model."""
        try:
            from common.llm.deepseek_client import DeepSeekChat
            
            client = DeepSeekChat(model=model_name, api_key=api_key)
            response, usage, actual_model = client.chat(
                messages=cls.TEST_MESSAGES,
                max_tokens=10,
                temperature=0.1,
                timeout_s=30
            )
            
            if response and len(response.strip()) > 0:
                return True, "DeepSeek API key and model are working correctly", {
                    "response": response.strip(),
                    "usage": usage,
                    "model_used": actual_model
                }
            else:
                return False, "DeepSeek API returned empty response", {"usage": usage}
                
        except Exception as e:
            error_msg = str(e).lower()
            if "unauthorized" in error_msg or "invalid" in error_msg or "401" in error_msg:
                return False, "Invalid DeepSeek API key", {"error": str(e)}
            elif "not found" in error_msg or "does not exist" in error_msg or "404" in error_msg:
                return False, f"Model '{model_name}' not found or not accessible", {"error": str(e)}
            elif "quota" in error_msg or "billing" in error_msg or "429" in error_msg:
                return False, "DeepSeek quota exceeded or billing issue", {"error": str(e)}
            else:
                return False, f"DeepSeek API error: {str(e)}", {"error": str(e)}
