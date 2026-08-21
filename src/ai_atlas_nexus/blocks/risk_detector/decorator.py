from abc import ABC, abstractmethod
from typing import Any, List, Protocol

from ai_atlas_nexus.blocks.inference.base import InferenceEngine
from ai_atlas_nexus.blocks.risk_detector.generic import DetectionRun


class Detector(Protocol):
    """The detector protocol
    """

    @property
    def inference_engine(self) -> InferenceEngine: ...

    def detect(self, usecases: List[str]) -> Any: ...

    def _run_inference(self, usecases: List[str]) -> DetectionRun[Any]: ...


class RiskDetectorDecorator(ABC):
    """Base for detectors that add one feature on top of another detector.

    Subclasses return a different type from `detect`.
    """

    def __init__(self, detector: Detector):
        """
        Args:
            detector: The detector to wrap.
        """
        self._detector = detector

    @property
    def detector(self) -> Detector:
        """The wrapped detector"""
        return self._detector

    @property
    def inference_engine(self) -> InferenceEngine:
        """The engine the wrapped detector runs on."""
        return self._detector.inference_engine

    @abstractmethod
    def detect(self, usecases: List[str]) -> Any:
        """Identify risks from usecases, adding this decorator's feature."""
        raise NotImplementedError

    def _run_inference(self, usecases: List[str]) -> DetectionRun[Any]:
        """Delegate to the wrapped detector.

        Decorators depend on `GenericRiskDetector._run_inference`: it returns the raw
        inference outputs that `detect` discards. A decorator needing to influence the
        inference itself overrides this, as `RiskDetectorWithExplanation` does to ask
        for a response schema carrying explanations.
        """
        return self._detector._run_inference(usecases)
