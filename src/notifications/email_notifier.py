"""SMTP email notifier."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage


class EmailNotifier:
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str, sender: str, recipient: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.sender = sender
        self.recipient = recipient

    def send(self, title: str, message: str) -> None:
        msg = EmailMessage()
        msg["Subject"] = title
        msg["From"] = self.sender
        msg["To"] = self.recipient
        msg.set_content(message)

        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=20) as smtp:
            smtp.starttls()
            smtp.login(self.username, self.password)
            smtp.send_message(msg)
