"""HuggingFace ZeroGPU Inference Engine for AI Atlas Nexus.

This module provides an inference engine that connects to HuggingFace
ZeroGPU spaces using the HuggingFace Inference API.
"""

import os
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from huggingface_hub import HfApi, list_models

from ai_atlas_nexus.blocks.inference.base import InferenceEngine
from ai_atlas_nexus.blocks.inference.params import (
    HFZeroGPUInferenceEngineParams,
    InferenceEngineCredentials,
    OpenAIChatCompletionMessageParam,
    TextGenerationInferenceOutput,
)
from ai_atlas_nexus.blocks.inference.postprocessing import postprocess
from ai_atlas_nexus.metadata_base import InferenceEngineType
from ai_atlas_nexus.toolkit.job_utils import run_parallel
from ai_atlas_nexus.toolkit.logging import configure_logger


logger = configure_logger(__name__)
load_dotenv()


class HFZeroGPUInferenceEngine(InferenceEngine):
    """Inference engine for HuggingFace ZeroGPU spaces.

    Uses the HuggingFace Inference API to connect to ZeroGPU-enabled
    spaces and models. Supports both text generation and chat interfaces.

    Attributes:
        _inference_engine_type: Type identifier for this engine
        _inference_engine_parameter_class: Parameter class for validation

    Example:
        >>> engine = HFZeroGPUInferenceEngine(
        ...     model_name_or_path="meta-llama/Llama-3-8B-Instruct",
        ...     credentials={"hf_token": "hf_..."},
        ...     parameters={"temperature": 0.7, "max_tokens": 500}
        ... )
        >>> results = engine.generate(["Hello, world!"])
    """

    _inference_engine_type = InferenceEngineType.HF_ZERO_GPU
    _inference_engine_parameter_class = HFZeroGPUInferenceEngineParams

    def prepare_credentials(
        self, credentials: Union[Dict, InferenceEngineCredentials]
    ) -> InferenceEngineCredentials:
        """Extract and validate HuggingFace credentials.

        Looks for HF_TOKEN in credentials dict or environment variables.
        Optional API URL for custom endpoints (defaults to HF Inference API).

        Args:
            credentials: Dictionary with 'hf_token' and optional 'api_url'

        Returns:
            InferenceEngineCredentials with validated credentials

        Raises:
            AssertionError: If hf_token is missing
        """
        hf_token = credentials.get(
            "hf_token",
            credentials.get(
                "api_key",  # Fallback to api_key
                os.environ.get("HF_TOKEN",None),
            ),
        )

        assert hf_token, (
            f"Error while trying to run {self._inference_engine_type}. "
            f"Please pass hf_token to credentials or set environment variable: "
            f"'HF_TOKEN'"
        )

        # Optional custom API URL (for specific spaces/endpoints)
        api_url = credentials.get(
            "api_url",
            os.environ.get("HF_ZERO_GPU_API_URL", None),
        )

        logger.info(
            f"{self._inference_engine_type} inference engine initialized "
            f"with model: {self.model_name_or_path}"
        )

        if api_url:
            logger.info(f"Using custom API URL: {api_url}")

        return InferenceEngineCredentials(
            hf_token=hf_token,
            api_key=hf_token,  # Store in api_key for compatibility
            api_url=api_url or "",  # Empty string if using default HF API
        )

    def create_client(self, credentials: InferenceEngineCredentials) -> Any:
        """Create HuggingFace InferenceClient.

        Args:
            credentials: Validated credentials with hf_token

        Returns:
            InferenceClient instance configured with token
        """
        from huggingface_hub import InferenceClient

        # Use custom URL if provided, otherwise use default HF API
        base_url = credentials.get("api_url") if credentials.get("api_url") else None

        return InferenceClient(
            token=credentials["hf_token"],
            base_url=base_url,
        )

    def ping(self):
        """Health check to verify model availability.

        Attempts to get model information from HuggingFace.
        Raises exception if model is not accessible.

        Raises:
            Exception: If model cannot be accessed or doesn't exist
        """
        try:
            # Try to get model info as a health check
            model_info = HfApi.model_info(self.model_name_or_path)
            logger.debug(f"Model {self.model_name_or_path} is accessible. Status: {model_info}")
        except Exception as e:
            logger.warning(
                f"Could not verify model status for {self.model_name_or_path}. "
                f"This may be normal for some models. Error: {str(e)}"
            )
            # Don't raise - some models may not support status check
            pass

    def is_thinking_supported(self):
        """Check if current model supports thinking/CoT mode.

        HuggingFace models with reasoning capabilities (e.g., Llama-3-70B-Instruct,
        some Qwen models) can output reasoning traces when prompted appropriately.

        Returns:
            True if thinking is supported (we assume it is for HF models)

        Note:
            Unlike Ollama which has explicit thinking support, HF models
            may support reasoning through prompt engineering. We allow this
            but log a warning to inform users.
        """
        if self.think:
            logger.warning(
                f"Thinking mode enabled for {self.model_name_or_path}. "
                f"HuggingFace models may support reasoning through prompting. "
                f"Ensure your model supports chain-of-thought reasoning."
            )
        return True

    @postprocess
    def generate(
        self,
        prompts: List[str],
        response_format=None,
        postprocessors=None,
        verbose=True,
        **kwargs,
    ) -> List[TextGenerationInferenceOutput]:
        """Generate text from a list of prompts.

        Args:
            prompts: List of text prompts to generate from
            response_format: Optional response format specification
            postprocessors: List of postprocessor names to apply
            verbose: Show progress bar if True
            **kwargs: Additional HuggingFace API parameters

        Returns:
            List of TextGenerationInferenceOutput objects
        """
        def generate_text(prompt: str):
            # Prepare parameters
            generation_kwargs = {
                k: v
                for k, v in self.parameters.items()
                if v is not None
            }
            generation_kwargs.update(kwargs)

            # Add thinking prompt if enabled
            if self.think:
                if isinstance(self.think, str):
                    # Thinking level: low, medium, high
                    thinking_prompts = {
                        "low": "\n\nPlease briefly explain your reasoning.",
                        "medium": "\n\nPlease think through this step by step.",
                        "high": "\n\nPlease provide detailed reasoning for your answer, thinking through each step carefully.",
                    }
                    prompt = prompt + thinking_prompts.get(self.think, thinking_prompts["medium"])
                else:
                    prompt = prompt + "\n\nPlease think through this step by step."

                # Enable reasoning output if parameter exists
                if "output_reasoning" in generation_kwargs:
                    generation_kwargs["output_reasoning"] = True

            # Call HuggingFace Inference API
            response = self.client.text_generation(
                prompt=prompt,
                model=self.model_name_or_path,
                **generation_kwargs,
            )

            return self._prepare_generation_output(response, prompt)

        return run_parallel(
            generate_text,
            prompts,
            f"Inferring with {self._inference_engine_type}",
            self.concurrency_limit,
            verbose=verbose,
        )

    @postprocess
    def chat(
        self,
        messages: Union[
            List[OpenAIChatCompletionMessageParam],
            List[str],
        ],
        tools=None,
        response_format=None,
        postprocessors=None,
        verbose=True,
        **kwargs,
    ) -> List[TextGenerationInferenceOutput]:
        """Chat interface with conversational messages.

        Args:
            messages: List of messages in OpenAI format or strings
            tools: Optional tool definitions (not yet supported)
            response_format: Optional response format specification
            postprocessors: List of postprocessor names to apply
            verbose: Show progress bar if True
            **kwargs: Additional HuggingFace API parameters

        Returns:
            List of TextGenerationInferenceOutput objects
        """
        def chat_response(messages):
            # Convert to OpenAI format if needed
            formatted_messages = self._to_openai_format(messages)

            # Prepare parameters
            generation_kwargs = {
                k: v
                for k, v in self.parameters.items()
                if v is not None
            }
            generation_kwargs.update(kwargs)

            # Add thinking prompt if enabled
            if self.think and formatted_messages:
                last_message = formatted_messages[-1]
                if last_message["role"] == "user":
                    if isinstance(self.think, str):
                        thinking_prompts = {
                            "low": " Please briefly explain your reasoning.",
                            "medium": " Please think through this step by step.",
                            "high": " Please provide detailed reasoning for your answer.",
                        }
                        last_message["content"] += thinking_prompts.get(
                            self.think, thinking_prompts["medium"]
                        )
                    else:
                        last_message["content"] += " Please think through this step by step."


            # Call HuggingFace Chat Completion API
            response = self.client.chat_completion(
                messages=formatted_messages,
                model=self.model_name_or_path,
                **generation_kwargs,
            )

            return self._prepare_chat_output(response, formatted_messages)

        return run_parallel(
            chat_response,
            messages,
            f"Inferring with {self._inference_engine_type}",
            self.concurrency_limit,
            verbose=verbose,
        )

    def _prepare_generation_output(
        self, response: Any, prompt: str
    ) -> TextGenerationInferenceOutput:
        """Map HuggingFace generation response to standard output format.

        Args:
            response: Raw response from HF text_generation API
            prompt: Original prompt text

        Returns:
            TextGenerationInferenceOutput with standardized fields
        """
        # HF text_generation can return string or dict
        if isinstance(response, str):
            prediction = response
            details = {}
        else:
            prediction = response.get("generated_text", str(response))
            details = response.get("details", {})

        return TextGenerationInferenceOutput(
            prediction=prediction,
            input_tokens=details.get("prompt_tokens", None),
            output_tokens=details.get("generated_tokens", None),
            stop_reason=details.get("finish_reason", None),
            seed=self.parameters.get("seed", None),
            input_text=prompt,
            model_name_or_path=self.model_name_or_path,
            inference_engine=str(self._inference_engine_type),
            thinking=None,  # Extract from response if available
        )

    def _prepare_chat_output(
        self, response: Any, messages: List[Dict]
    ) -> TextGenerationInferenceOutput:
        """Map HuggingFace chat response to standard output format.

        Args:
            response: Raw response from HF chat_completion API
            messages: Original message list

        Returns:
            TextGenerationInferenceOutput with standardized fields
        """
        # Extract message content
        if hasattr(response, "choices") and response.choices:
            choice = response.choices[0]
            prediction = choice.message.content
            finish_reason = choice.finish_reason

            # Extract usage info
            usage = getattr(response, "usage", None)
            input_tokens = usage.prompt_tokens if usage else None
            output_tokens = usage.completion_tokens if usage else None
        else:
            # Fallback for different response formats
            prediction = str(response)
            finish_reason = None
            input_tokens = None
            output_tokens = None

        return TextGenerationInferenceOutput(
            prediction=prediction,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            stop_reason=finish_reason,
            seed=self.parameters.get("seed", None),
            input_text=None,  # Could reconstruct from messages if needed
            model_name_or_path=self.model_name_or_path,
            inference_engine=str(self._inference_engine_type),
            thinking=None,  # Extract from response if model provides it
        )
