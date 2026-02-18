"""Main application entrypoint.

Run with:
    python -m src.app
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import cv2
from dotenv import load_dotenv
import os

from src.config import load_config
from src.detector import MotionDetector
from src.logger_setup import configure_logging
from src.notifications.base import Notifier
from src.notifications.email_notifier import EmailNotifier
from src.notifications.pushover_notifier import PushoverNotifier
from src.roi_selector import ROISelector
from src.state_machine import FreezeStateMachine


def build_notifiers(enabled_methods: list[str] | None, logger) -> list[Notifier]:
    methods = [m.lower() for m in (enabled_methods or [])]
    notifiers: list[Notifier] = []

    if "email" in methods:
        required = ["SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "ALERT_EMAIL_FROM", "ALERT_EMAIL_TO"]
        if all(os.getenv(k) for k in required):
            notifiers.append(
                EmailNotifier(
                    smtp_host=os.environ["SMTP_HOST"],
                    smtp_port=int(os.environ["SMTP_PORT"]),
                    username=os.environ["SMTP_USERNAME"],
                    password=os.environ["SMTP_PASSWORD"],
                    sender=os.environ["ALERT_EMAIL_FROM"],
                    recipient=os.environ["ALERT_EMAIL_TO"],
                )
            )
        else:
            logger.warning("Email notifier not enabled: missing environment variables.")

    if "pushover" in methods:
        if os.getenv("PUSHOVER_APP_TOKEN") and os.getenv("PUSHOVER_USER_KEY"):
            notifiers.append(PushoverNotifier(os.environ["PUSHOVER_APP_TOKEN"], os.environ["PUSHOVER_USER_KEY"]))
        else:
            logger.warning("Pushover notifier not enabled: missing PUSHOVER_APP_TOKEN or PUSHOVER_USER_KEY.")

    return notifiers


def save_evidence(frame, evidence_dir: str) -> str:
    Path(evidence_dir).mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    path = Path(evidence_dir) / f"freeze_{stamp}.jpg"
    cv2.imwrite(str(path), frame)
    return str(path)


def clamp_roi(roi: tuple[int, int, int, int], frame_shape: tuple[int, int, int]) -> tuple[int, int, int, int]:
    h, w = frame_shape[:2]
    x, y, rw, rh = roi
    x = max(0, min(x, w - 1))
    y = max(0, min(y, h - 1))
    rw = max(1, min(rw, w - x))
    rh = max(1, min(rh, h - y))
    return (x, y, rw, rh)


def run(config_path: str):
    load_dotenv()
    config = load_config(config_path)
    logger = configure_logging(config.log_file)

    camera = cv2.VideoCapture(config.camera.index)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, config.camera.width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config.camera.height)
    camera.set(cv2.CAP_PROP_FPS, config.camera.fps)

    if not camera.isOpened():
        raise RuntimeError(f"Could not open camera index {config.camera.index}")

    ok, frame = camera.read()
    if not ok:
        raise RuntimeError("Could not read initial frame from camera")

    roi = config.detection.roi
    if roi is None:
        print("No ROI set in config. Please draw ROI now.")
        selected = ROISelector().select(frame)
        if selected is None:
            raise RuntimeError("ROI selection canceled. Set detection.roi in config to continue.")
        roi = selected
        print(f"Selected ROI: {roi}")

    roi = clamp_roi(roi, frame.shape)

    detector = MotionDetector(config.detection)
    machine = FreezeStateMachine(
        freeze_seconds=config.detection.freeze_seconds,
        recover_seconds=config.detection.recover_seconds,
        cooldown_seconds=config.alerts.cooldown_seconds,
    )
    notifiers = build_notifiers(config.alerts.enabled_methods, logger)

    logger.info("Arm watcher started.")

    while True:
        ok, frame = camera.read()
        if not ok:
            logger.warning("Failed to read frame from camera.")
            time.sleep(0.1)
            continue

        now = time.time()
        result = detector.compute(frame, roi)
        motion_present = result.score >= config.detection.motion_threshold
        status, should_alert = machine.update(motion_present, now)

        x, y, w, h = roi
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        if config.detection.show_mask_overlay:
            color_mask = cv2.cvtColor(result.mask, cv2.COLOR_GRAY2BGR)
            frame[y : y + h, x : x + w] = cv2.addWeighted(frame[y : y + h, x : x + w], 0.65, color_mask, 0.35, 0)

        cv2.putText(frame, f"Motion score: {result.score:.4f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        cv2.putText(frame, f"Status: {status}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255) if status == "FROZEN" else (0, 255, 0), 2)
        cv2.putText(frame, "Press q to quit", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

        if should_alert:
            msg = f"Dia-Stron watcher detected no motion for {config.detection.freeze_seconds:.0f}s. Status: {status}."
            logger.warning(msg)
            if config.detection.evidence_on_freeze:
                evidence_path = save_evidence(frame, config.evidence_dir)
                logger.warning("Evidence saved: %s", evidence_path)
                msg += f" Evidence: {evidence_path}"

            for notifier in notifiers:
                try:
                    notifier.send("Dia-Stron arm freeze detected", msg)
                    logger.info("Alert sent via %s", notifier.__class__.__name__)
                except Exception as exc:  # pylint: disable=broad-except
                    logger.exception("Failed to send alert via %s: %s", notifier.__class__.__name__, exc)

        cv2.imshow("Dia-Stron Arm Watcher", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            logger.info("Quit requested by user.")
            break

    camera.release()
    cv2.destroyAllWindows()
    logger.info("Arm watcher stopped.")


def main():
    parser = argparse.ArgumentParser(description="Monitor robotic arm motion and alert on freeze.")
    parser.add_argument("--config", default="configs/settings.yaml", help="Path to YAML config file")
    args = parser.parse_args()
    run(args.config)


if __name__ == "__main__":
    main()
