import asyncio
from types import SimpleNamespace

from app.bot.handlers import help as help_handler


class DummyHelpMessage:
    def __init__(self) -> None:
        self.answers: list[str] = []

    async def answer(self, text: str) -> None:
        self.answers.append(text)


def test_help_command_returns_text(monkeypatch) -> None:
    message = DummyHelpMessage()

    monkeypatch.setattr(
        help_handler,
        "get_settings",
        lambda: SimpleNamespace(
            xray_host="vpn.example.com",
            xray_port=443,
            xray_network="tcp",
            xray_security="none",
            xray_service_name="",
            xray_flow="",
        ),
    )

    asyncio.run(help_handler.cmd_help(message))

    assert message.answers
    assert "vpn.example.com" in message.answers[0]
