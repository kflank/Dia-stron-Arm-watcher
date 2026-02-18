"""State machine for freeze and recovery logic."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FreezeState:
    status: str = "MOVING"
    freeze_alert_sent_at: float | None = None
    last_motion_at: float | None = None
    recover_started_at: float | None = None


class FreezeStateMachine:
    """Tracks transitions between MOVING and FROZEN states."""

    def __init__(self, freeze_seconds: float, recover_seconds: float, cooldown_seconds: float):
        self.freeze_seconds = freeze_seconds
        self.recover_seconds = recover_seconds
        self.cooldown_seconds = cooldown_seconds
        self.state = FreezeState()

    def update(self, motion_present: bool, now: float) -> tuple[str, bool]:
        """Update state with current motion boolean.

        Returns tuple(status, should_alert).
        """
        should_alert = False

        if motion_present:
            self.state.last_motion_at = now
            if self.state.status == "FROZEN":
                if self.state.recover_started_at is None:
                    self.state.recover_started_at = now
                elif now - self.state.recover_started_at >= self.recover_seconds:
                    self.state.status = "MOVING"
                    self.state.recover_started_at = None
            else:
                self.state.recover_started_at = None
            return self.state.status, should_alert

        # no motion case
        if self.state.last_motion_at is None:
            self.state.last_motion_at = now

        no_motion_duration = now - self.state.last_motion_at

        if self.state.status != "FROZEN" and no_motion_duration >= self.freeze_seconds:
            if self.state.freeze_alert_sent_at is None or now - self.state.freeze_alert_sent_at >= self.cooldown_seconds:
                should_alert = True
                self.state.freeze_alert_sent_at = now
            self.state.status = "FROZEN"

        self.state.recover_started_at = None
        return self.state.status, should_alert
