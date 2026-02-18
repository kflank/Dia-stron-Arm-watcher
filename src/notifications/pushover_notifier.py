"""Pushover notifier integration."""

from __future__ import annotations

import requests


class PushoverNotifier:
    def __init__(self, app_token: str, user_key: str):
        self.app_token = app_token
        self.user_key = user_key

    def send(self, title: str, message: str) -> None:
        response = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": self.app_token,
                "user": self.user_key,
                "title": title,
                "message": message,
            },
            timeout=20,
        )
        response.raise_for_status()
