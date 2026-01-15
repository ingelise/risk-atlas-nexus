"""Tests for HFZeroGPUInferenceEngine."""

import os

import pytest

from src.ai_atlas_nexus.blocks.inference import HFZeroGPUInferenceEngine


class TestHFZeroGPUInferenceEngine:
    """Test suite for HFZeroGPUInferenceEngine."""

    @pytest.fixture
    def hf_token(self):
        """Get HF token from environment or skip test."""
        token = os.environ.get("HF_TOKEN")
        if not token:
            pytest.skip("HF_TOKEN not set")
        return token

    def test_initialization(self, hf_token):
        """Test engine initialization."""
        engine = HFZeroGPUInferenceEngine(
            model_name_or_path="Qwen/Qwen2.5-3B-Instruct",
            credentials={"hf_token": hf_token},
            parameters={"temperature": 0.7, "max_new_tokens": 50},
        )
        assert engine is not None
        assert engine.model_name_or_path == "Qwen/Qwen2.5-3B-Instruct"

    def test_generate(self, hf_token):
        """Test text generation."""
        engine = HFZeroGPUInferenceEngine(
            model_name_or_path="Qwen/Qwen2.5-3B-Instruct",
            credentials={"hf_token": hf_token},
            parameters={"temperature": 0.7, "max_new_tokens": 50},
        )
        results = engine.generate(["Hello, what is AI?"])
        assert len(results) == 1
        assert results[0].prediction is not None
        assert len(results[0].prediction) > 0

    def test_chat(self, hf_token):
        """Test chat interface."""


        engine = HFZeroGPUInferenceEngine(
            model_name_or_path="Qwen/Qwen2.5-3B-Instruct",
            credentials={"hf_token": hf_token},
            parameters={"temperature": 0.7},
        )

        messages = [
            {
                "role": "user",
                "content": "What is 1 plus 1?",
            }
        ]

        results = engine.chat(messages=[messages], verbose=False)
        assert len(results) == 1
        assert results[0].prediction is not None

    def test_thinking_mode(self, hf_token):
        """Test thinking/CoT mode."""
        engine = HFZeroGPUInferenceEngine(
            model_name_or_path="Qwen/Qwen2.5-3B-Instruct",
            credentials={"hf_token": hf_token},
            parameters={"temperature": 0.7, "max_new_tokens": 100},
            think="medium",
        )
        results = engine.generate(["Solve: What is 15 * 7?"])
        assert len(results) == 1
        # Thinking prompts should encourage step-by-step reasoning
        assert results[0].prediction is not None
