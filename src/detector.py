"""Motion detection utilities for a selected ROI."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from src.config import DetectionConfig


@dataclass
class MotionResult:
    score: float
    mask: np.ndarray


class MotionDetector:
    """Detect motion based on frame differencing and morphology."""

    def __init__(self, cfg: DetectionConfig):
        self.cfg = cfg
        self.previous_gray: np.ndarray | None = None

    def compute(self, frame_bgr: np.ndarray, roi: tuple[int, int, int, int]) -> MotionResult:
        x, y, w, h = roi
        roi_frame = frame_bgr[y : y + h, x : x + w]

        gray = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (self.cfg.blur_kernel_size, self.cfg.blur_kernel_size), 0)

        if self.previous_gray is None:
            self.previous_gray = blur
            mask = np.zeros_like(blur, dtype=np.uint8)
            return MotionResult(score=1.0, mask=mask)

        diff = cv2.absdiff(self.previous_gray, blur)
        _, thresholded = cv2.threshold(diff, self.cfg.min_pixel_threshold, 255, cv2.THRESH_BINARY)
        thresholded = cv2.erode(thresholded, None, iterations=self.cfg.erode_iterations)
        thresholded = cv2.dilate(thresholded, None, iterations=self.cfg.dilate_iterations)

        motion_pixels = np.count_nonzero(thresholded)
        total_pixels = max(1, w * h)
        score = motion_pixels / float(total_pixels)

        self.previous_gray = blur
        return MotionResult(score=score, mask=thresholded)
