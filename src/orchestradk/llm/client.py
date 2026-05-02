"""
LLM client wrapper for OrchestrADK.

This module provides a unified interface for interacting with LLMs,
specifically watsonx.ai.
"""

from typing import Dict, Any, Optional, List
import logging
from ibm_watsonx_ai.foundation_models import Model
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

from ..utils.exceptions import LLMError, ConfigurationError

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Wrapper for LLM interactions with watsonx.ai.
    
    Provides a simplified interface for generating text using IBM watsonx.ai
    foundation models.
    """
    
    def __init__(
        self,
        api_key: str,
        project_id: str,
        url: str = "https://us-south.ml.cloud.ibm.com",
        model_id: str = "ibm/granite-13b-chat-v2"
    ):
        """
        Initialize the LLM client.
        
        Args:
            api_key: IBM Cloud API key
            project_id: watsonx.ai project ID
            url: watsonx.ai service URL
            model_id: Model identifier to use
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not api_key or not project_id:
            raise ConfigurationError(
                "API key and project ID are required",
                {"api_key_present": bool(api_key), "project_id_present": bool(project_id)}
            )
        
        self.api_key = api_key
        self.project_id = project_id
        self.url = url
        self.model_id = model_id
        self._model: Optional[Model] = None
        
        logger.info(f"LLM client initialized with model: {model_id}")
    
    def _get_model(self, parameters: Optional[Dict[str, Any]] = None) -> Model:
        """
        Get or create the watsonx.ai model instance.
        
        Args:
            parameters: Optional generation parameters
            
        Returns:
            Configured Model instance
        """
        default_params = {
            GenParams.DECODING_METHOD: "greedy",
            GenParams.MAX_NEW_TOKENS: 2048,
            GenParams.TEMPERATURE: 0.7,
            GenParams.TOP_P: 0.9,
            GenParams.TOP_K: 50,
        }
        
        if parameters:
            default_params.update(parameters)
        
        credentials = {
            "url": self.url,
            "apikey": self.api_key
        }
        
        return Model(
            model_id=self.model_id,
            params=default_params,
            credentials=credentials,
            project_id=self.project_id
        )
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> str:
        """
        Generate text using the LLM.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            parameters: Optional generation parameters
            max_retries: Number of retry attempts on failure
            
        Returns:
            Generated text
            
        Raises:
            LLMError: If generation fails after retries
        """
        full_prompt = self._format_prompt(prompt, system_prompt)
        
        for attempt in range(max_retries):
            try:
                model = self._get_model(parameters)
                response = model.generate_text(prompt=full_prompt)
                
                if not response:
                    raise LLMError(
                        "Empty response from LLM",
                        {"attempt": attempt + 1, "prompt_length": len(full_prompt)}
                    )
                
                logger.info(f"Successfully generated text (attempt {attempt + 1})")
                return response.strip()
                
            except Exception as e:
                logger.warning(f"LLM generation attempt {attempt + 1} failed: {str(e)}")
                
                if attempt == max_retries - 1:
                    raise LLMError(
                        f"Failed to generate text after {max_retries} attempts",
                        {"error": str(e), "prompt_length": len(full_prompt)}
                    )
        
        raise LLMError("Unexpected error in generate method")
    
    async def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate structured output (JSON) using the LLM.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            schema: Optional JSON schema for validation
            parameters: Optional generation parameters
            
        Returns:
            Parsed JSON response
            
        Raises:
            LLMError: If generation or parsing fails
        """
        import json
        
        # Add JSON formatting instruction to prompt
        json_prompt = f"{prompt}\n\nRespond with valid JSON only."
        
        response = await self.generate(
            prompt=json_prompt,
            system_prompt=system_prompt,
            parameters=parameters
        )
        
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            
            parsed = json.loads(json_str)
            
            # TODO: Validate against schema if provided
            
            return parsed
            
        except json.JSONDecodeError as e:
            raise LLMError(
                "Failed to parse JSON response",
                {"error": str(e), "response": response[:200]}
            )
    
    def _format_prompt(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Format the prompt with optional system context.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            Formatted prompt string
        """
        if system_prompt:
            return f"{system_prompt}\n\n{prompt}"
        return prompt
    
    async def batch_generate(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Generate text for multiple prompts.
        
        Args:
            prompts: List of prompts
            system_prompt: Optional system prompt
            parameters: Optional generation parameters
            
        Returns:
            List of generated texts
        """
        results = []
        for prompt in prompts:
            result = await self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                parameters=parameters
            )
            results.append(result)
        
        return results

# Made with Bob
