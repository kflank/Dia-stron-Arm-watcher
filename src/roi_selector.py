"""Interactive ROI selector with mouse drag support."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class ROISelection:
    x: int
    y: int
    w: int
    h: int


class ROISelector:
    def __init__(self, window_name: str = "ROI Selector"):
        self.window_name = window_name
        self.start = None
        self.end = None
        self.done = False

    def _mouse_callback(self, event, x, y, _flags, _param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.start = (x, y)
            self.end = (x, y)
        elif event == cv2.EVENT_MOUSEMOVE and self.start is not None:
            self.end = (x, y)
        elif event == cv2.EVENT_LBUTTONUP:
            self.end = (x, y)
            self.done = True

    def select(self, frame: np.ndarray) -> tuple[int, int, int, int] | None:
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self._mouse_callback)

        while True:
            display = frame.copy()
            if self.start and self.end:
                x1, y1 = self.start
                x2, y2 = self.end
                cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)

            cv2.putText(display, "Drag ROI. Press S to save, Q to cancel.", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.imshow(self.window_name, display)

            key = cv2.waitKey(20) & 0xFF
            if key == ord("q"):
                cv2.destroyWindow(self.window_name)
                return None
            if key == ord("s") and self.done and self.start and self.end:
                x1, y1 = self.start
                x2, y2 = self.end
                x = min(x1, x2)
                y = min(y1, y2)
                w = abs(x2 - x1)
                h = abs(y2 - y1)
                cv2.destroyWindow(self.window_name)
                if w == 0 or h == 0:
                    return None
                return (x, y, w, h)
