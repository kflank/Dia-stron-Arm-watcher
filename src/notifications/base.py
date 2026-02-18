"""Base notification interface."""

from __future__ import annotations

from typing import Protocol


class Notifier(Protocol):
    def send(self, title: str, message: str) -> None:
        ...
