import datetime
import io
from unittest.mock import AsyncMock, patch

import pytest
from aiogram.enums import ParseMode
from aiogram.types import (
    PhotoSize,
)

from src.handlers import Repo, kb
from src.main import dp

from .conftest import Client, MockedBot

with open("tests/images/example.jpg", "rb") as f:
    mock_file = io.BytesIO(f.read())


client = Client(dp)


@pytest.mark.asyncio
@patch.object(Repo, "get_entry_id")
async def test_recieve_with_no_qrcode_message_sends_answer(mockrepo: AsyncMock):
    answer = await client.send_message(
        request_kwargs={
            "message_id": 11,
            "text": "hello",
            "date": datetime.datetime.now(),
        }
    )
    mockrepo.assert_not_awaited()
    assert answer.text == "Отправьте *__фото__* QR кода для сканирования"
    assert answer.parse_mode == ParseMode.MARKDOWN_V2


@pytest.mark.asyncio
@patch.object(Repo, "get_entry_id", return_value=11)
@patch.object(MockedBot, "download", return_value=mock_file)
async def test_recieve_with_existing_qrcode_sends_two_answers(
    mockbot: AsyncMock, mockrepo: AsyncMock
):
    responses = await client.send_message(
        expected_replies_from_bot=2,
        request_kwargs={
            "message_id": 11,
            "text": "",
            "date": datetime.datetime.now(),
            "photo": [
                PhotoSize(
                    file_id="123123",
                    file_unique_id="123123",
                    width=12,
                    height=13,
                )
            ],
        },
    )
    mockbot.assert_awaited_once()
    mockrepo.assert_awaited_once()

    assert len(responses) == 2
    resp1, resp2 = responses
    assert resp1.text == "Идет обработка QR кода..."
    assert resp1.reply_markup is None

    assert (
        resp2.text
        == "Полученный QR код уже существует в базе данных. Желаете его удалить?"
    )
    assert resp2.reply_markup == kb.as_markup()
