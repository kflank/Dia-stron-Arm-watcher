"""Configuration loading utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class CameraConfig:
    index: int = 0
    width: int = 1280
    height: int = 720
    fps: int = 20


@dataclass
class DetectionConfig:
    freeze_seconds: float = 30.0
    recover_seconds: float = 2.0
    motion_threshold: float = 0.015
    blur_kernel_size: int = 11
    min_pixel_threshold: int = 25
    erode_iterations: int = 1
    dilate_iterations: int = 2
    roi: tuple[int, int, int, int] | None = None
    show_mask_overlay: bool = True
    evidence_on_freeze: bool = True


@dataclass
class AlertConfig:
    cooldown_seconds: float = 300.0
    enabled_methods: list[str] | None = None


@dataclass
class AppConfig:
    camera: CameraConfig
    detection: DetectionConfig
    alerts: AlertConfig
    log_file: str = "logs/monitor.log"
    evidence_dir: str = "evidence"


def _merge(default: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(default)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(path: str | Path) -> AppConfig:
    """Load YAML configuration into typed dataclasses."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        config_data = yaml.safe_load(handle) or {}

    defaults: dict[str, Any] = {
        "camera": CameraConfig().__dict__,
        "detection": DetectionConfig().__dict__,
        "alerts": AlertConfig(enabled_methods=["email", "pushover"]).__dict__,
        "log_file": "logs/monitor.log",
        "evidence_dir": "evidence",
    }

    merged = _merge(defaults, config_data)
    return AppConfig(
        camera=CameraConfig(**merged["camera"]),
        detection=DetectionConfig(**merged["detection"]),
        alerts=AlertConfig(**merged["alerts"]),
        log_file=merged["log_file"],
        evidence_dir=merged["evidence_dir"],
    )
