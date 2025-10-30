import asyncio
from types import SimpleNamespace

from app.bot.handlers import admin


class DummyMessage:
    def __init__(self, user_id: int) -> None:
        self.from_user = SimpleNamespace(id=user_id)
        self.answers: list[dict[str, object]] = []

    async def answer(self, text: str, reply_markup=None) -> None:
        self.answers.append({"text": text, "reply_markup": reply_markup})


def test_start_command_returns_menu() -> None:
    message = DummyMessage(user_id=1)

    asyncio.run(admin.cmd_start(message))

    assert message.answers, "Ответ не отправлен"
    response = message.answers[0]
    assert response["text"] == admin.WELCOME_TEXT
    markup = response["reply_markup"]
    button_texts = [button.text for row in markup.inline_keyboard for button in row]
    assert "🔑 Создать ключ" in button_texts
    assert "📋 Список ключей" in button_texts
