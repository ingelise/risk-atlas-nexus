"""Tests for token usage metadata exposure in GenericRiskDetector."""

from types import SimpleNamespace
from typing import List

from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import Risk
from ai_atlas_nexus.blocks.inference.params import (
    DetectionResult,
    ExplanationType,
    InferenceMetadata,
    RiskWithExplanation,
    TextGenerationInferenceOutput,
    TokenUsage,
)
from ai_atlas_nexus.blocks.risk_detector import GenericRiskDetector


def _risk(rid, name, description, taxonomy="ibm-risk-atlas"):
    return Risk(
        id=rid, name=name, description=description, isDefinedByTaxonomy=taxonomy
    )


class _FakeEngine:
    """Engine stub returning TextGenerationInferenceOutput with token metrics."""

    def __init__(self, predictions_with_tokens):
        """
        Args:
            predictions_with_tokens: List of tuples (prediction, input_tokens, output_tokens)
        """
        self._predictions_with_tokens = predictions_with_tokens
        self.model_name_or_path = "fake-model"
        self._inference_engine_type = "FAKE"

    def generate(self, prompts, response_format=None, postprocessors=None):
        outputs = []
        for i, (pred, in_tok, out_tok) in enumerate(
            self._predictions_with_tokens[: len(prompts)]
        ):
            outputs.append(
                TextGenerationInferenceOutput(
                    prediction=pred,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    inference_engine="FAKE",
                    model_name_or_path="fake-model",
                )
            )
        return outputs


class _FakeEngineWithStopReasons:
    """Engine stub with stop_reason support."""

    def __init__(self, predictions_with_tokens):
        self._predictions_with_tokens = predictions_with_tokens
        self.model_name_or_path = "fake-model"
        self._inference_engine_type = "FAKE"

    def generate(self, prompts, response_format=None, postprocessors=None):
        outputs = []
        stop_reasons = ["eos", "eos", "max_tokens"]
        for i, (pred, in_tok, out_tok) in enumerate(
            self._predictions_with_tokens[: len(prompts)]
        ):
            outputs.append(
                TextGenerationInferenceOutput(
                    prediction=pred,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    stop_reason=stop_reasons[i] if i < len(stop_reasons) else "eos",
                    inference_engine="FAKE",
                    model_name_or_path="fake-model",
                )
            )
        return outputs


class _FakeEngineWithSeeds:
    """Engine stub with seed support."""

    def __init__(self, predictions_with_tokens_and_seeds):
        """
        Args:
            predictions_with_tokens_and_seeds: List of tuples (prediction, input_tokens, output_tokens, seed)
        """
        self._predictions = predictions_with_tokens_and_seeds
        self.model_name_or_path = "fake-model"
        self._inference_engine_type = "FAKE"

    def generate(self, prompts, response_format=None, postprocessors=None):
        outputs = []
        for i, (pred, in_tok, out_tok, seed) in enumerate(
            self._predictions[: len(prompts)]
        ):
            outputs.append(
                TextGenerationInferenceOutput(
                    prediction=pred,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    seed=seed,
                    inference_engine="FAKE",
                    model_name_or_path="fake-model",
                )
            )
        return outputs


class _FakeEngineWithThinking:
    """Engine stub with thinking support."""

    def __init__(self, predictions_with_thinking):
        """
        Args:
            predictions_with_thinking: List of tuples (prediction, input_tokens, output_tokens, seed, stop_reason, has_thinking)
        """
        self._predictions = predictions_with_thinking
        self.model_name_or_path = "fake-model"
        self._inference_engine_type = "FAKE"

    def generate(self, prompts, response_format=None, postprocessors=None):
        outputs = []
        for i, (pred, in_tok, out_tok, seed, stop_reason, has_thinking) in enumerate(
            self._predictions[: len(prompts)]
        ):
            outputs.append(
                TextGenerationInferenceOutput(
                    prediction=pred,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    seed=seed,
                    stop_reason=stop_reason,
                    thinking="<thinking>...</thinking>" if has_thinking else None,
                    inference_engine="FAKE",
                    model_name_or_path="fake-model",
                )
            )
        return outputs


class _FakeEnginePerRisk:
    """Engine stub for the per-risk path (batch_inference=False).

    `answers` is one list of "yes"/"no" per usecase, with one entry per risk. Each
    response's thinking is tagged with its own usecase and risk index, so an explanation
    landing on the wrong risk is visible in the assertion rather than silently plausible.
    """

    def __init__(self, answers):
        self._answers = answers
        self._usecase_idx = 0
        self.model_name_or_path = "fake-model"
        self._inference_engine_type = "FAKE"

    def generate(self, prompts, response_format=None, postprocessors=None):
        usecase_idx = self._usecase_idx
        self._usecase_idx += 1
        return [
            TextGenerationInferenceOutput(
                prediction={"answer": answer},
                input_tokens=10,
                output_tokens=5,
                thinking=f"thinking-u{usecase_idx}-r{risk_idx}",
                inference_engine="FAKE",
                model_name_or_path="fake-model",
            )
            for risk_idx, answer in enumerate(self._answers[usecase_idx])
        ]


def _detector(engine, risks):
    return GenericRiskDetector(
        risks=risks, inference_engine=engine, cot_examples=None, batch_inference=True
    )


def _detector_per_risk(engine, risks):
    return GenericRiskDetector(
        risks=risks, inference_engine=engine, cot_examples=None, batch_inference=False
    )


RISKS = [
    _risk("risk-a", "Risk A", "Description of risk A"),
    _risk("risk-b", "Risk B", "Description of risk B"),
]


class TestMetadataAggregation:
    """Test token usage aggregation across multiple inference calls."""

    def test_detect_batch_without_metadata_returns_bare_list(self):
        """Default behavior: return_metadata=False returns bare list."""
        engine = _FakeEngine([
            (["Risk A", "Risk B"], 100, 50),
        ])
        detector = _detector(engine, RISKS)
        result = detector.detect(["usecase 1"], return_metadata=False)

        assert isinstance(result, list)
        assert not isinstance(result, DetectionResult)
        assert len(result) == 1
        assert len(result[0]) == 2
        assert result[0][0].name == "Risk A"

    def test_detect_batch_with_metadata_returns_wrapped_result(self):
        """With return_metadata=True, return DetectionResult wrapper."""
        engine = _FakeEngine([
            (["Risk A"], 100, 50),
        ])
        detector = _detector(engine, RISKS)
        result = detector.detect(["usecase 1"], return_metadata=True)

        assert isinstance(result, DetectionResult)
        assert isinstance(result.data, list)
        assert len(result.data) == 1
        assert result.data[0][0].name == "Risk A"

    def test_metadata_aggregates_tokens_correctly(self):
        """Token usage aggregation sums across all calls."""
        engine = _FakeEngine([
            (["Risk A"], 100, 50),
            (["Risk B"], 120, 60),
        ])
        detector = _detector(engine, RISKS)
        result = detector.detect(["usecase 1", "usecase 2"], return_metadata=True)

        assert result.metadata.token_usage.input_tokens == 220  # 100 + 120
        assert result.metadata.token_usage.output_tokens == 110  # 50 + 60
        assert result.metadata.token_usage.total_tokens == 330  # 220 + 110

    def test_metadata_includes_model_and_engine_info(self):
        """Metadata includes model name and inference engine type."""
        engine = _FakeEngine([(["Risk A"], 100, 50)])
        detector = _detector(engine, RISKS)
        result = detector.detect(["usecase 1"], return_metadata=True)

        assert result.metadata.model == "fake-model"
        assert result.metadata.inference_engine == "FAKE"
        assert result.metadata.num_calls == 1
        assert result.metadata.seed is None
        assert result.metadata.stop_reason_summary == {}
        assert result.metadata.has_thinking is False

    def test_metadata_num_calls_reflects_inference_count(self):
        """num_calls field tracks number of underlying LLM calls."""
        engine = _FakeEngine([
            (["Risk A"], 100, 50),
            (["Risk B"], 120, 60),
            (["Risk A", "Risk B"], 150, 70),
        ])
        detector = _detector(engine, RISKS)
        result = detector.detect(
            ["usecase 1", "usecase 2", "usecase 3"], return_metadata=True
        )

        assert result.metadata.num_calls == 3

    def test_metadata_with_none_tokens_handled_gracefully(self):
        """Handles responses with missing token counts."""
        engine = _FakeEngine([
            (["Risk A"], None, 50),  # Missing input_tokens
            (["Risk B"], 100, None),  # Missing output_tokens
        ])
        detector = _detector(engine, RISKS)
        result = detector.detect(["usecase 1", "usecase 2"], return_metadata=True)

        # Should treat None as 0 for aggregation
        assert result.metadata.token_usage.input_tokens == 100
        assert result.metadata.token_usage.output_tokens == 50
        assert result.metadata.token_usage.total_tokens == 150

    def test_backward_compatibility_default_return_metadata_false(self):
        """Bare list returned by default (backward compatibility)."""
        engine = _FakeEngine([(["Risk A"], 100, 50)])
        detector = _detector(engine, RISKS)

        # Call without return_metadata parameter
        result = detector.detect(["usecase 1"])

        # Should return bare list, not wrapped
        assert isinstance(result, list)
        assert not isinstance(result, DetectionResult)

    def test_stop_reason_aggregation(self):
        """Stop reasons are counted across all inference calls."""
        # Create engine that returns different stop reasons
        predictions = [
            (["Risk A"], 100, 50),  # Will have stop_reason="eos"
            (["Risk B"], 120, 60),  # Will have stop_reason="eos"
            (["Risk C"], 90, 45),   # Will have stop_reason="max_tokens"
        ]
        engine = _FakeEngineWithStopReasons(predictions)
        detector = _detector(engine, RISKS)
        result = detector.detect(["u1", "u2", "u3"], return_metadata=True)

        assert result.metadata.stop_reason_summary == {"eos": 2, "max_tokens": 1}

    def test_seed_extracted_when_consistent(self):
        """Seed is stored only when all calls use the same seed."""
        predictions_with_seeds = [
            (["Risk A"], 100, 50, 42),
            (["Risk B"], 120, 60, 42),
        ]
        engine = _FakeEngineWithSeeds(predictions_with_seeds)
        detector = _detector(engine, RISKS)
        result = detector.detect(["u1", "u2"], return_metadata=True)

        assert result.metadata.seed == 42

    def test_seed_none_when_inconsistent(self):
        """Seed is None when calls use different seeds."""
        predictions_with_seeds = [
            (["Risk A"], 100, 50, 42),
            (["Risk B"], 120, 60, 99),  # Different seed
        ]
        engine = _FakeEngineWithSeeds(predictions_with_seeds)
        detector = _detector(engine, RISKS)
        result = detector.detect(["u1", "u2"], return_metadata=True)

        assert result.metadata.seed is None

    def test_thinking_flag_set_when_present(self):
        """has_thinking is True if any response has thinking content."""
        predictions_with_thinking = [
            (["Risk A"], 100, 50, None, None, False),  # No thinking
            (["Risk B"], 120, 60, None, None, True),   # Has thinking
        ]
        engine = _FakeEngineWithThinking(predictions_with_thinking)
        detector = _detector(engine, RISKS)
        result = detector.detect(["u1", "u2"], return_metadata=True)

        assert result.metadata.has_thinking is True


class TestExplanationTypes:
    """Test different explanation type options."""

    def test_no_explanation_by_default(self):
        """Default returns bare risks without explanations."""
        engine = _FakeEngine([(["Risk A"], 100, 50)])
        detector = _detector(engine, RISKS)
        result = detector.detect(["usecase 1"])

        assert isinstance(result, list)
        assert not isinstance(result[0][0], RiskWithExplanation)
        assert isinstance(result[0][0], Risk)

    def test_explanation_none_returns_bare_risks(self):
        """Explicit ExplanationType.NONE returns bare risks."""
        engine = _FakeEngine([(["Risk A"], 100, 50)])
        detector = _detector(engine, RISKS)
        result = detector.detect(
            ["usecase 1"], explanation_type=ExplanationType.NONE
        )

        assert isinstance(result[0][0], Risk)

    def test_explanation_description_includes_risk_description(self):
        """DESCRIPTION type includes risk.description."""
        engine = _FakeEngine([(["Risk A"], 100, 50)])
        detector = _detector(engine, RISKS)
        result = detector.detect(
            ["usecase 1"], explanation_type=ExplanationType.DESCRIPTION
        )

        assert isinstance(result[0][0], RiskWithExplanation)
        assert result[0][0].risk.name == "Risk A"
        assert result[0][0].explanation == "Description of risk A"

    def test_explanation_reasoning_extracts_thinking(self):
        """REASONING type extracts model thinking."""
        predictions = [(["Risk A"], 100, 50, None, None, True)]
        engine = _FakeEngineWithThinking(predictions)
        detector = _detector(engine, RISKS)
        result = detector.detect(
            ["usecase 1"], explanation_type=ExplanationType.REASONING
        )

        assert isinstance(result[0][0], RiskWithExplanation)
        assert result[0][0].explanation == "<thinking>...</thinking>"

    def test_explanation_reasoning_none_when_no_thinking(self):
        """REASONING type returns None if no thinking available."""
        engine = _FakeEngine([(["Risk A"], 100, 50)])
        detector = _detector(engine, RISKS)
        result = detector.detect(
            ["usecase 1"], explanation_type=ExplanationType.REASONING
        )

        assert isinstance(result[0][0], RiskWithExplanation)
        assert result[0][0].explanation is None


    def test_explanation_self_explanation_none_for_string_prediction(self):
        """SELF_EXPLANATION type returns None if prediction is string (no explanation field)."""
        engine = _FakeEngine([(["Risk A"], 100, 50)])
        detector = _detector(engine, RISKS)
        result = detector.detect(
            ["usecase 1"], explanation_type=ExplanationType.SELF_EXPLANATION
        )

        assert isinstance(result[0][0], RiskWithExplanation)
        assert result[0][0].explanation is None


THREE_RISKS = [
    _risk("risk-a", "Risk A", "Description of risk A"),
    _risk("risk-b", "Risk B", "Description of risk B"),
    _risk("risk-c", "Risk C", "Description of risk C"),
]


class TestPerRiskExplanations:
    """Explanations on the per-risk path (batch_inference=False).

    This path had no coverage, which is how an off-by-one in the response mapping
    survived: explanations were assigned by a counter that only advanced for identified
    risks, with no per-usecase offset.
    """

    def test_explanation_matches_the_response_that_identified_the_risk(self):
        """Each risk gets the reasoning from its own response, not a neighbour's."""
        # Risk A rejected, so a naive counter would shift B and C down by one.
        engine = _FakeEnginePerRisk([["no", "yes", "yes"]])
        detector = _detector_per_risk(engine, THREE_RISKS)
        result = detector.detect(
            ["usecase 1"], explanation_type=ExplanationType.REASONING
        )

        assert [r.risk.name for r in result[0]] == ["Risk B", "Risk C"]
        assert result[0][0].explanation == "thinking-u0-r1"
        assert result[0][1].explanation == "thinking-u0-r2"

    def test_explanations_do_not_leak_across_usecases(self):
        """Usecase 2's explanations come from usecase 2's responses."""
        engine = _FakeEnginePerRisk([["no", "yes", "yes"], ["yes", "no", "yes"]])
        detector = _detector_per_risk(engine, THREE_RISKS)
        result = detector.detect(
            ["usecase 1", "usecase 2"], explanation_type=ExplanationType.REASONING
        )

        assert [r.risk.name for r in result[1]] == ["Risk A", "Risk C"]
        assert result[1][0].explanation == "thinking-u1-r0"
        assert result[1][1].explanation == "thinking-u1-r2"

    def test_per_risk_bare_risks_by_default(self):
        """Default path still returns bare Risk objects."""
        engine = _FakeEnginePerRisk([["no", "yes", "no"]])
        detector = _detector_per_risk(engine, THREE_RISKS)
        result = detector.detect(["usecase 1"])

        assert [r.name for r in result[0]] == ["Risk B"]
        assert isinstance(result[0][0], Risk)

    def test_per_risk_metadata_counts_every_call(self):
        """One inference call per risk per usecase."""
        engine = _FakeEnginePerRisk([["no", "yes", "yes"], ["yes", "no", "yes"]])
        detector = _detector_per_risk(engine, THREE_RISKS)
        result = detector.detect(["u1", "u2"], return_metadata=True)

        assert result.metadata.num_calls == 6  # 3 risks x 2 usecases
        assert result.metadata.token_usage.input_tokens == 60
        assert result.metadata.token_usage.output_tokens == 30


class TestStringPredictionFallback:
    """Raw-string predictions still resolve risks when postprocessing is skipped."""

    def test_substring_match_on_raw_string_prediction(self):
        engine = _FakeEngine([('["Risk A", "Risk C"]', 100, 50)])
        detector = _detector(engine, THREE_RISKS)
        result = detector.detect(["usecase 1"])

        assert [r.name for r in result[0]] == ["Risk A", "Risk C"]

    def test_unnamed_risk_does_not_raise(self):
        """`Risk.name` is Optional; `None in str` would raise TypeError."""
        risks = THREE_RISKS + [
            Risk(id="risk-unnamed", description="no name", isDefinedByTaxonomy="ibm-risk-atlas")
        ]
        engine = _FakeEngine([('["Risk A"]', 100, 50)])
        detector = _detector(engine, risks)
        result = detector.detect(["usecase 1"])

        assert [r.name for r in result[0]] == ["Risk A"]


class TestTokenUsageAggregation:
    """Test TokenUsage dataclass aggregation behavior."""

    def test_token_usage_addition(self):
        """TokenUsage + operator correctly sums fields."""
        usage1 = TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150)
        usage2 = TokenUsage(input_tokens=120, output_tokens=60, total_tokens=180)

        result = usage1 + usage2

        assert result.input_tokens == 220
        assert result.output_tokens == 110
        assert result.total_tokens == 330

    def test_token_usage_sum_with_none_values(self):
        """TokenUsage addition handles None values as 0."""
        usage1 = TokenUsage(input_tokens=100, output_tokens=None, total_tokens=100)
        usage2 = TokenUsage(input_tokens=None, output_tokens=60, total_tokens=60)

        result = usage1 + usage2

        assert result.input_tokens == 100
        assert result.output_tokens == 60
        assert result.total_tokens == 160

    def test_unreported_usage_stays_none_not_zero(self):
        """Summing two unreported usages must not fabricate a zero."""
        result = TokenUsage() + TokenUsage()

        assert result.input_tokens is None
        assert result.output_tokens is None
        assert result.total_tokens is None

    def test_engine_without_usage_reports_none(self):
        """An engine that reports no token counts yields None, not a misleading 0."""
        engine = _FakeEngine([(["Risk A"], None, None)])
        detector = _detector(engine, RISKS)
        result = detector.detect(["usecase 1"], return_metadata=True)

        assert result.metadata.token_usage.input_tokens is None
        assert result.metadata.token_usage.output_tokens is None
        assert result.metadata.token_usage.total_tokens is None

    def test_token_usage_sum_empty_usage(self):
        """Summing with empty TokenUsage (all None) treats as 0."""
        usage1 = TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150)
        usage_empty = TokenUsage()

        result = usage1 + usage_empty

        assert result.input_tokens == 100
        assert result.output_tokens == 50
        assert result.total_tokens == 150
