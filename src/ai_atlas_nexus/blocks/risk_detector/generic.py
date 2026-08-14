import json
from typing import Any, List, Literal, Optional, Union, overload

from pydantic import create_model

from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import Risk
from ai_atlas_nexus.blocks.inference import TextGenerationInferenceOutput
from ai_atlas_nexus.blocks.inference.params import (
    DetectionResult,
    ExplanationType,
    InferenceMetadata,
    RiskWithExplanation,
    TokenUsage,
)
from ai_atlas_nexus.blocks.prompt_response_schema import (
    LIST_OF_STR_SCHEMA,
    AIRiskPresence,
    RiskListWithExplanations,
)
from ai_atlas_nexus.blocks.prompt_templates import (
    RISK_IDENTIFICATION_BATCH_TEMPLATE,
    RISK_IDENTIFICATION_PER_RISK_DSPY_TEMPLATES,
    RISK_IDENTIFICATION_PER_RISK_TEMPLATE,
)
from ai_atlas_nexus.blocks.risk_detector import RiskDetector
from ai_atlas_nexus.toolkit.logging import configure_logger


logger = configure_logger(__name__)


class GenericRiskDetector(RiskDetector):

    @overload
    def detect(
        self,
        usecases: List[str],
        return_metadata: Literal[False] = ...,
        explanation_type: Literal[ExplanationType.NONE] = ...,
    ) -> List[List[Risk]]: ...

    @overload
    def detect(
        self,
        usecases: List[str],
        return_metadata: Literal[False],
        explanation_type: Literal[ExplanationType.DESCRIPTION, ExplanationType.REASONING, ExplanationType.SELF_EXPLANATION],
    ) -> List[List[RiskWithExplanation]]: ...

    @overload
    def detect(
        self,
        usecases: List[str],
        return_metadata: Literal[True],
        explanation_type: Literal[ExplanationType.NONE] = ...,
    ) -> DetectionResult[List[List[Risk]]]: ...

    @overload
    def detect(
        self,
        usecases: List[str],
        return_metadata: Literal[True],
        explanation_type: Literal[ExplanationType.DESCRIPTION, ExplanationType.REASONING, ExplanationType.SELF_EXPLANATION],
    ) -> DetectionResult[List[List[RiskWithExplanation]]]: ...

    # General case, kept last so the literal overloads above win when they apply. Without
    # it, callers forwarding plain `bool`/`ExplanationType` variables (as `library.py`
    # does) match no overload at all.
    @overload
    def detect(
        self,
        usecases: List[str],
        return_metadata: bool = ...,
        explanation_type: ExplanationType = ...,
    ) -> Union[
        List[List[Risk]],
        List[List[RiskWithExplanation]],
        DetectionResult[List[List[Risk]]],
        DetectionResult[List[List[RiskWithExplanation]]],
    ]: ...

    def detect(
        self,
        usecases: List[str],
        return_metadata: bool = False,
        explanation_type: ExplanationType = ExplanationType.NONE,
    ) -> Union[
        List[List[Risk]],
        List[List[RiskWithExplanation]],
        DetectionResult[List[List[Risk]]],
        DetectionResult[List[List[RiskWithExplanation]]],
    ]:
        """Identify risks from usecases with optional explanations and metadata.

        Args:
            usecases: List of usecase descriptions to analyze.
            return_metadata: If True, wrap results in DetectionResult with token usage metrics.
                           Defaults to False for backward compatibility.
            explanation_type: Type of explanation to pair with each risk:
                - NONE (default): No explanations, bare Risk objects
                - DESCRIPTION: Includes risk description from ontology
                - REASONING: Extracts model thinking/reasoning if available
                - SELF_EXPLANATION: Extracts explanations from model's response

        Returns:
            Exact type depends on parameters (see overload signatures):
            - (return_metadata=False, explanation_type=NONE): List[List[Risk]]
            - (return_metadata=False, explanation_type!=NONE): List[List[RiskWithExplanation]]
            - (return_metadata=True, explanation_type=NONE): DetectionResult[List[List[Risk]]]
            - (return_metadata=True, explanation_type!=NONE): DetectionResult[List[List[RiskWithExplanation]]]

        Examples:
            Bare risks (default, backward compatible):
            >>> result = detector.detect(["my system"])
            >>> for risks in result:
            ...     for risk in risks: print(risk.name)

            Risks with descriptions:
            >>> result = detector.detect(["my system"], explanation_type=ExplanationType.DESCRIPTION)
            >>> for risks in result:
            ...     for risk_exp in risks: print(f"{risk_exp.risk.name}: {risk_exp.explanation}")

            With token usage tracking:
            >>> result = detector.detect(["my system"], return_metadata=True)
            >>> print(f"Tokens used: {result.metadata.token_usage.total_tokens}")
        """
        return (
            self.detect_one(usecases, return_metadata=return_metadata, explanation_type=explanation_type)
            if self.use_dspy_prompt or not self.batch_inference
            else self.detect_batch(usecases, return_metadata=return_metadata, explanation_type=explanation_type)
        )

    def detect_batch(
        self,
        usecases: List[str],
        return_metadata: bool = False,
        explanation_type: ExplanationType = ExplanationType.NONE,
    ) -> Union[
        List[List[Risk]],
        List[List[RiskWithExplanation]],
        DetectionResult[List[List[Risk]]],
        DetectionResult[List[List[RiskWithExplanation]]],
    ]:
        prompts = [
            self.prompt_builder(
                prompt_template=RISK_IDENTIFICATION_BATCH_TEMPLATE
            ).build(
                cot_examples=self._examples,
                usecase=usecase,
                risks=json.dumps(
                    [
                        {"category": risk.name, "description": risk.description}
                        for risk in self._risks
                    ],
                    indent=4,
                ),
                max_risk=self.max_risk,
            )
            for usecase in usecases
        ]

        # Choose schema based on whether self-explanations are requested
        if explanation_type == ExplanationType.SELF_EXPLANATION:
            # Use schema with explanation field for self-explanation mode
            schema = create_model(
                "RiskListWithExplanations",
                risks=(
                    List[
                        create_model(
                            "RiskWithExplanationItem",
                            risk_name=(
                                Literal[tuple(risk.name for risk in self._risks)],
                                ...,
                            ),
                            explanation=(str, ...),
                            __base__=None,
                        )
                    ],
                    ...,
                ),
                __base__=None,
            )
            postprocessor = "json_object"
        else:
            # Use simple list schema for other explanation types
            schema = dict(LIST_OF_STR_SCHEMA)
            schema["items"]["enum"] = [risk.name for risk in self._risks]
            postprocessor = "list_of_str"

        # Invoke inference service
        inference_responses: List[TextGenerationInferenceOutput] = (
            self.inference_engine.generate(
                prompts,
                response_format=schema,
                postprocessors=[postprocessor],
            )
        )

        risks_data = []
        for inference_response in inference_responses:
            # Resolve the predicted risk names once per response, not once per risk.
            predicted_risk_names = self._extract_risk_predictions(
                inference_response.prediction
            )
            risks_data.append(
                [risk for risk in self._risks if risk.name in predicted_risk_names][
                    : self.max_risk
                ]
            )

        # Apply explanation wrapping if requested
        if explanation_type != ExplanationType.NONE:
            risks_data = self._apply_explanations_batch(
                risks_data, inference_responses, explanation_type
            )

        if return_metadata:
            return self._wrap_with_metadata(risks_data, inference_responses)
        return risks_data

    def detect_one(
        self,
        usecases: List[str],
        return_metadata: bool = False,
        explanation_type: ExplanationType = ExplanationType.NONE,
    ) -> Union[
        List[List[Risk]],
        List[List[RiskWithExplanation]],
        DetectionResult[List[List[Risk]]],
        DetectionResult[List[List[RiskWithExplanation]]],
    ]:
        all_risks = []
        all_responses = []

        prompt_template = RISK_IDENTIFICATION_PER_RISK_TEMPLATE
        if self.use_dspy_prompt:
            for (
                model_ids,
                template,
            ) in RISK_IDENTIFICATION_PER_RISK_DSPY_TEMPLATES.items():
                if self.inference_engine.model_name_or_path in model_ids:
                    prompt_template = template
                    break

        for usecase in usecases:
            prompts = [
                self.prompt_builder(prompt_template=prompt_template).build(
                    cot_examples=self._examples,
                    usecase=usecase,
                    risk_name=risk.name,
                    risk_description=risk.description,
                )
                for risk in self._risks
            ]

            # Invoke inference service
            inference_responses: List[TextGenerationInferenceOutput] = (
                self.inference_engine.generate(
                    prompts,
                    response_format=AIRiskPresence,
                    postprocessors=["json_object"],
                )
            )
            all_responses.extend(inference_responses)

            # Keep each identified risk paired with the response that identified it so
            # explanations cannot drift onto the wrong risk.
            identified_risks = []
            for index, response in enumerate(inference_responses):
                if (
                    isinstance(response.prediction, dict)
                    and "answer" in response.prediction
                ):
                    if response.prediction["answer"].lower() == "yes":
                        identified_risks.append((self._risks[index], response))
                elif (
                    isinstance(response.prediction, str)
                    and "yes" in response.prediction.lower()
                ):
                    identified_risks.append((self._risks[index], response))

            if explanation_type != ExplanationType.NONE:
                all_risks.append(
                    [
                        RiskWithExplanation(
                            risk=risk,
                            explanation=self._get_explanation(
                                risk, response, explanation_type
                            ),
                        )
                        for risk, response in identified_risks
                    ]
                )
            else:
                all_risks.append([risk for risk, _ in identified_risks])

        if return_metadata:
            return self._wrap_with_metadata(all_risks, all_responses)
        return all_risks

    def _extract_risk_predictions(
        self, prediction: Union[str, List[dict], dict, None]
    ) -> List[Any]:
        """Extract risk names from prediction, handling list, dict and raw string formats."""
        if isinstance(prediction, dict):
            # Handle dict format with "risks" or similar key
            risks = prediction.get("risks")
            if isinstance(risks, list):
                # Check if this is a list of risk items with explanations
                if risks and isinstance(risks[0], dict) and "risk_name" in risks[0]:
                    # Extract just the risk names for now; explanations are handled separately
                    return [item["risk_name"] for item in risks]
                return risks
            return []
        elif isinstance(prediction, list):
            return prediction
        elif isinstance(prediction, str):
            # Postprocessing can be skipped or fail (see `postprocessing.postprocess`,
            # which swallows errors), leaving the raw model output. Fall back to
            # substring matching so those responses still yield risks. `Risk.name` is
            # Optional, and `None in str` raises TypeError, so skip unnamed risks.
            return [
                risk.name
                for risk in self._risks
                if risk.name and risk.name in prediction
            ]
        return []

    def _get_explanation(
        self,
        risk: Risk,
        inference_response: TextGenerationInferenceOutput,
        explanation_type: ExplanationType,
    ) -> Optional[str]:
        """Get explanation for a risk based on the explanation type."""
        if explanation_type == ExplanationType.NONE:
            return None
        elif explanation_type == ExplanationType.DESCRIPTION:
            return risk.description
        elif explanation_type == ExplanationType.REASONING:
            return inference_response.thinking
        elif explanation_type == ExplanationType.SELF_EXPLANATION:
            return self._extract_self_explanation(inference_response)
        return None

    def _extract_self_explanation(
        self, inference_response: TextGenerationInferenceOutput
    ) -> Optional[str]:
        """Extract explanation from model's response.

        Some models produce explanations along with their predictions (e.g., in JSON
        responses with an 'explanation' field or in structured outputs). This method
        extracts such self-explanations from the model's response.
        """
        if not inference_response.prediction:
            return None

        if isinstance(inference_response.prediction, dict):
            return inference_response.prediction.get("explanation")
        elif isinstance(inference_response.prediction, str):
            return None

        return None

    def _apply_explanations_batch(
        self,
        risks_data: List[List[Risk]],
        inference_responses: List[TextGenerationInferenceOutput],
        explanation_type: ExplanationType,
    ) -> List[List[RiskWithExplanation]]:
        """Wrap batch risks with explanations. One response maps to one risk list."""
        wrapped_risks = []
        for risk_list, response in zip(risks_data, inference_responses):
            # For SELF_EXPLANATION mode, build a mapping from risk names to explanations
            explanation_map = {}
            if explanation_type == ExplanationType.SELF_EXPLANATION:
                if (
                    isinstance(response.prediction, dict)
                    and "risks" in response.prediction
                ):
                    risks_with_explanations = response.prediction["risks"]
                    if isinstance(risks_with_explanations, list):
                        explanation_map = {
                            item.get("risk_name"): item.get("explanation")
                            for item in risks_with_explanations
                            if isinstance(item, dict)
                            and "risk_name" in item
                            and "explanation" in item
                        }

            wrapped_list = []
            for risk in risk_list:
                if explanation_type == ExplanationType.SELF_EXPLANATION:
                    # Get the specific explanation for this risk from the map
                    explanation = explanation_map.get(risk.name)
                else:
                    explanation = self._get_explanation(risk, response, explanation_type)

                wrapped_list.append(
                    RiskWithExplanation(risk=risk, explanation=explanation)
                )

            wrapped_risks.append(wrapped_list)
        return wrapped_risks

    def _wrap_with_metadata(
        self,
        risks_data: Union[List[List[Risk]], List[List[RiskWithExplanation]]],
        inference_responses: List[TextGenerationInferenceOutput],
    ) -> DetectionResult[Any]:
        """Aggregate token usage and prediction metadata from inference responses."""
        token_usage = TokenUsage()
        stop_reason_summary = {}
        seeds = set()
        has_thinking = False

        for response in inference_responses:
            # Aggregate token usage
            response_usage = TokenUsage(
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                total_tokens=(response.input_tokens or 0) + (response.output_tokens or 0)
                if response.input_tokens is not None or response.output_tokens is not None
                else None,
            )
            token_usage = token_usage + response_usage

            # Count stop reasons
            if response.stop_reason:
                stop_reason_summary[response.stop_reason] = stop_reason_summary.get(response.stop_reason, 0) + 1

            # Track seeds (if consistent)
            if response.seed is not None:
                seeds.add(response.seed)

            # Track if thinking was used
            if response.thinking:
                has_thinking = True

        # Use seed only if all calls used the same seed
        seed = seeds.pop() if len(seeds) == 1 else None

        metadata = InferenceMetadata(
            token_usage=token_usage,
            inference_engine=str(self.inference_engine._inference_engine_type),
            model=self.inference_engine.model_name_or_path,
            num_calls=len(inference_responses),
            seed=seed,
            stop_reason_summary=stop_reason_summary,
            has_thinking=has_thinking,
        )
        return DetectionResult(data=risks_data, metadata=metadata)
