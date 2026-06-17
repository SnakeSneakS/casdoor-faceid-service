from __future__ import annotations

from typing import Any, Protocol, Sequence

from .config import Settings


class FaceEngine(Protocol):
    def compare(self, reference_image: str, probe_image: str) -> float:
        ...

    def anti_spoof(self, image: str) -> dict[str, Any]:
        ...


class FaceAnalysisService:
    def __init__(self, engine: FaceEngine, settings: Settings):
        self.engine = engine
        self.settings = settings

    def compare(self, reference_images: Sequence[str], probe_images: Sequence[str]) -> dict[str, Any]:
        if len(reference_images) == 0:
            raise ValueError("referenceImages must contain at least one image")
        if len(probe_images) == 0:
            raise ValueError("probeImages must contain at least one image")

        best_score = -1.0
        best_reference_index = -1
        best_probe_index = -1
        best_liveness: dict[str, Any] | None = None
        best_overall_score = -1.0
        best_overall_reference_index = -1
        best_overall_probe_index = -1
        best_overall_liveness: dict[str, Any] | None = None

        for probe_index, probe_image in enumerate(probe_images):
            liveness = None
            liveness_passed = True
            if self.settings.enable_liveness:
                liveness = self.engine.anti_spoof(probe_image)
                liveness_passed = bool(liveness.get("isReal")) and float(liveness.get("confidence", 0.0)) >= self.settings.liveness_threshold

            for reference_index, reference_image in enumerate(reference_images):
                score = self.engine.compare(reference_image, probe_image)
                if score > best_overall_score:
                    best_overall_score = score
                    best_overall_reference_index = reference_index
                    best_overall_probe_index = probe_index
                    best_overall_liveness = liveness
                if liveness_passed and score > best_score:
                    best_score = score
                    best_reference_index = reference_index
                    best_probe_index = probe_index
                    best_liveness = liveness

        if self.settings.enable_liveness and best_reference_index == -1:
            return {
                "matched": False,
                "score": round(best_overall_score, 6),
                "threshold": self.settings.similarity_threshold,
                "referenceIndex": best_overall_reference_index,
                "probeIndex": best_overall_probe_index,
                "reason": "liveness_failed",
                "liveness": best_overall_liveness,
                "livenessThreshold": self.settings.liveness_threshold,
            }

        matched = best_score >= self.settings.similarity_threshold
        reason = "matched" if matched else "similarity_below_threshold"

        result = {
            "matched": matched,
            "score": round(best_score, 6),
            "threshold": self.settings.similarity_threshold,
            "referenceIndex": best_reference_index,
            "probeIndex": best_probe_index,
            "reason": reason,
        }
        if self.settings.enable_liveness:
            result["liveness"] = best_liveness
            result["livenessThreshold"] = self.settings.liveness_threshold
        return result
