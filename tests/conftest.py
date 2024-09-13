from collections import deque
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Deque,
    Dict,
    Optional,
    Type,
)

from aiogram import Bot, Dispatcher
from aiogram.client.session.base import BaseSession
from aiogram.methods import SendMessage, TelegramMethod
from aiogram.methods.base import Response, TelegramType
from aiogram.types import (
    UNSET_PARSE_MODE,
    Chat,
    Message,
    ResponseParameters,
    TelegramObject,
    Update,
    User,
)
from pydantic.alias_generators import to_snake


class MockedSession(BaseSession):
    def __init__(self):
        super(MockedSession, self).__init__()
        self.responses: Deque[Response[TelegramType]] = deque()
        self.requests: Deque[TelegramMethod[TelegramType]] = deque()
        self.closed = True

    def add_result(self, response: Response[TelegramType]) -> Response[TelegramType]:
        self.responses.append(response)
        return response

    def get_request(self) -> TelegramMethod[TelegramType]:
        return self.requests.pop()

    async def close(self):
        self.closed = True

    async def make_request(
        self,
        bot: Bot,
        method: TelegramMethod[TelegramType],
        timeout: Optional[int] = UNSET_PARSE_MODE,
    ) -> TelegramType:
        self.closed = False
        self.requests.append(method)
        response: Response[TelegramType] = self.responses.pop()
        self.check_response(
            bot=bot,
            method=method,
            status_code=response.error_code,
            content=response.model_dump_json(),
        )
        return response.result  # type: ignore

    async def stream_content(
        self,
        url: str,
        headers: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        chunk_size: int = 65536,
        raise_for_status: bool = True,
    ) -> AsyncGenerator[bytes, None]:  # pragma: no cover
        yield b""


class MockedBot(Bot):
    if TYPE_CHECKING:
        session: MockedSession

    def __init__(self, **kwargs):
        super(MockedBot, self).__init__(
            kwargs.pop("token", "42:TEST"), session=MockedSession(), **kwargs
        )
        self._me = User(
            id=self.id,
            is_bot=True,
            first_name="FirstName",
            last_name="LastName",
            username="tbot",
            language_code="ru",
        )

    def add_result_for(
        self,
        method: Type[TelegramMethod[TelegramType]],
        ok: bool,
        result: TelegramType = None,
        description: Optional[str] = None,
        error_code: int = 200,
        migrate_to_chat_id: Optional[int] = None,
        retry_after: Optional[int] = None,
    ) -> Response[TelegramType]:
        response = Response[method.__returning__](  # type: ignore
            ok=ok,
            result=result,
            description=description,
            error_code=error_code,
            parameters=ResponseParameters(
                migrate_to_chat_id=migrate_to_chat_id,
                retry_after=retry_after,
            ),
        )
        self.session.add_result(response)
        return response

    def get_request(self) -> TelegramMethod[TelegramType]:
        return self.session.get_request()


class Client:
    def __init__(self, dispatcher: Dispatcher) -> None:
        self.dp = dispatcher
        self.bot = MockedBot()
        self.user = User(id=42, is_bot=False, first_name="Test")
        self.chat = Chat(id=42, type="private")

    def _create_update(
        self, update_type: TelegramObject, update_id: int = 11, **update_kwargs: Any
    ) -> Update:
        update = update_type(**update_kwargs)
        update_name = to_snake(update.__repr_name__().lower())
        update_data = {update_name: update}
        return Update(update_id=update_id, **update_data)

    async def send_message(
        self,
        update_id: int = 11,
        expected_replies_from_bot: int = 1,
        request_kwargs: dict[str, Any] | None = None,
    ) -> Message:
        for _ in range(expected_replies_from_bot):
            self.bot.add_result_for(SendMessage, ok=True)
        await self.dp.feed_update(
            bot=self.bot,
            update=self._create_update(
                update_type=Message,
                update_id=update_id,
                chat=self.chat,
                from_user=self.user,
                **(request_kwargs or {}),
            ),
        )

        return self.bot.session.requests
