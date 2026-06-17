from __future__ import annotations

import os
from dataclasses import replace
from functools import lru_cache
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import __version__
from .config import Settings
from .engine import UniFaceEngine
from .service import FaceAnalysisService


class ImageRequest(BaseModel):
    image: str


class CompareRequest(BaseModel):
    imageA: str | None = None
    imageB: str | None = None
    referenceImages: list[str] = Field(default_factory=list)
    probeImages: list[str] = Field(default_factory=list)
    enableLiveness: bool | None = None
    similarityThreshold: float | None = None
    livenessThreshold: float | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env(os.environ)


@lru_cache(maxsize=1)
def get_engine() -> UniFaceEngine:
    return UniFaceEngine(get_settings())


def _settings_for_request(request: CompareRequest) -> Settings:
    settings = get_settings()
    if request.enableLiveness is not None:
        settings = replace(settings, enable_liveness=request.enableLiveness)
    if request.similarityThreshold is not None:
        settings = replace(settings, similarity_threshold=request.similarityThreshold)
    if request.livenessThreshold is not None:
        settings = replace(settings, liveness_threshold=request.livenessThreshold)
    return settings


def _as_error(exc: Exception) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


def create_app() -> FastAPI:
    app = FastAPI(
        title="Casdoor Face ID Service",
        version=__version__,
        description="Stateless UniFace-backed face analysis service for Casdoor Face ID providers.",
    )

    @app.get("/health")
    def health() -> dict[str, Any]:
        settings = get_settings()
        return {
            "status": "ok",
            "service": "casdoor-faceid-service",
            "version": __version__,
            "device": settings.device,
            "providers": settings.providers,
            "livenessEnabled": settings.enable_liveness,
        }

    @app.post("/v1/detect")
    def detect(request: ImageRequest) -> dict[str, Any]:
        try:
            return {"faces": get_engine().detect(request.image)}
        except Exception as exc:
            raise _as_error(exc) from exc

    @app.post("/v1/anti-spoof")
    def anti_spoof(request: ImageRequest) -> dict[str, Any]:
        try:
            return get_engine().anti_spoof(request.image)
        except Exception as exc:
            raise _as_error(exc) from exc

    @app.post("/v1/parse")
    def parse(request: ImageRequest) -> dict[str, Any]:
        try:
            return get_engine().parse(request.image)
        except Exception as exc:
            raise _as_error(exc) from exc

    @app.post("/v1/compare")
    def compare(request: CompareRequest) -> dict[str, Any]:
        reference_images = list(request.referenceImages)
        probe_images = list(request.probeImages)
        if request.imageA is not None:
            probe_images.append(request.imageA)
        if request.imageB is not None:
            reference_images.append(request.imageB)

        try:
            service = FaceAnalysisService(get_engine(), _settings_for_request(request))
            return service.compare(reference_images, probe_images)
        except Exception as exc:
            raise _as_error(exc) from exc

    return app


app = create_app()
