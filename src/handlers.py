from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db import Repo, sessionmaker
from qr import decode_file
from utils import run_in_executor

router = Router(name=__name__)

kb = InlineKeyboardBuilder(
    [
        [
            InlineKeyboardButton(text="Удалить", callback_data="confirm_delete"),
            InlineKeyboardButton(text="Не удалять", callback_data="abort_delete"),
        ]
    ]
)


@router.message.middleware()
@router.callback_query.middleware()
async def repo_middleware(handler, event, data):
    async with sessionmaker() as session:
        data["repo"] = Repo(session)
        return await handler(event, data)


class QRCodeState(StatesGroup):
    do_delete = State()


@router.message()
async def qrcode_receive(message: Message, state: FSMContext, repo: Repo) -> None:
    if not message.photo:
        await message.answer(
            "Отправьте *__фото__* QR кода для сканирования",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    await message.answer("Идет обработка QR кода...")
    file = await message.bot.download(message.photo[-1].file_id)
    val = await run_in_executor(decode_file, file)
    if not val:
        await message.answer(
            "Не удалось распознать ссылку в вашем QR коде.\nВот некоторые причины, по "
            "которым такое могло произойти:\n1) Плохое качество фото.\n"
            "2) Плохое/малое/нечеткое изображения QR кода на фото.\n3) Фото не "
            "содержит QR код.\nПопробуйте загрузить новое фото."
        )
        return

    entry_id = await repo.get_entry_id(val)
    if not entry_id:
        entry_id = await repo.add(val)
        await message.answer(
            f"QR код успешно добавлен. Вы можете перейти по ссылке: {val}."
        )
        return

    await message.answer(
        "Полученный QR код уже существует в базе данных. Желаете его удалить?",
        reply_markup=kb.as_markup(),
    )
    await state.update_data(qrcode_id=entry_id)
    await state.set_state(QRCodeState.do_delete)


@router.callback_query(QRCodeState.do_delete, F.data == "abort_delete")
async def qrcode_delete_abort(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer("QR код оставлен без изменений. Операция завершена.")
    await state.clear()
    await callback.answer()


@router.callback_query(QRCodeState.do_delete, F.data == "confirm_delete")
async def qrcode_delete_confirm(
    callback: CallbackQuery, state: FSMContext, repo: Repo
) -> None:
    qrcode_id = (await state.get_data())["qrcode_id"]
    deleted = await repo.delete(qrcode_id)

    if deleted == 0:
        await callback.message.answer(
            "При удалении QR кода возникла ошибка. Попробуйте повторить операцию позже."
        )
    else:
        await callback.message.answer("Выбранный QR код был успешно удален.")

    await state.clear()
    await callback.answer()
