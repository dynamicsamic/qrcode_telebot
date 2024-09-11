from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db import Repo
from qrcode import decode_qrcode
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


class QRCodeState(StatesGroup):
    do_delete = State()


@router.message()
async def qrcode_receive(message: Message, state: FSMContext) -> None:
    if not message.photo:
        await message.answer("Отправьте фото QR кода для сканирования")
        return

    await message.answer("Подождите пока завершится обработка QR кода.")
    file_id = await message.bot.get_file(message.photo[-1].file_id)
    file = await message.bot.download(file_id)
    val = await run_in_executor(decode_qrcode, file)

    if not val:
        await message.answer(
            "Не удалось распознать ссылку в вашем QR коде. Одной из причин может быть "
            "плохое качество фото или слишком малое/нечеткое изображения QR кода на фото. "
            "Попробуйте сделать новое фото. Также возможно, что вам предоставили QR код, "
            "который не содержит ссылку. В таком случае бот не сможет распознать ваш код."
        )
        return

    repo = Repo()

    entry_id = repo.get_entry_id(val)
    if not entry_id:
        entry_id = await repo.add(val)
        await message.answer(
            f"QR код успешно добавлен. Вы можете перейти по ссылке: {val}."
        )
        return

    await message.answer(
        "Полученный QR уже существует в базе данных. Желаете его удалить,",
        reply_markup=kb.as_markup(),
    )
    await state.update_data(qrcode_id=entry_id)
    await state.set_state(QRCodeState.do_delete)


@router.callback_query(QRCodeState.do_delete, F.data == "abort_delete")
async def qrcode_delete_abort(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("QR код оставлен без изменений. Операция завершена.")
    await state.clear()
    await callback.answer()


@router.callback_query(QRCodeState.do_delete, F.data == "confirm_delete")
async def qrcode_delete_confirm(callback: CallbackQuery, state: FSMContext):
    qrcode_id = (await state.get_data())["qrcode_id"]
    repo = Repo()
    deleted = await repo.delete(qrcode_id)

    if deleted == 0:
        await callback.message.answer(
            "При удалении QR кода возникла ошибка. Попробуйте повторить операцию позже."
        )
    else:
        await callback.message.answer("Выбранный QR код был успешно удален.")

    await state.clear()
    await callback.answer()
