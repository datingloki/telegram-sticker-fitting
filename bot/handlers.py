import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, Message
from PIL import UnidentifiedImageError

from processors.image import process_image


router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        "Привет! 👋\n\n"
        "Пришли мне картинку, GIF или видео, "
        "и я подготовлю его в формате Telegram-стикера."
    )


async def process_image_message(
    message: Message,
    bot: Bot,
    file_id: str,
) -> None:
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        input_path = temp_path / "input"
        output_path = temp_path / "sticker.webp"

        telegram_file = await bot.get_file(file_id)

        if telegram_file is None:
            await message.answer("Не удалось получить файл.")
            return

        await bot.download(
            telegram_file,
            destination=input_path,
        )

        try:
            await asyncio.to_thread(
                process_image,
                input_path,
                output_path,
            )
        except (ValueError, UnidentifiedImageError):
            await message.answer(
                "Не получилось подготовить эту картинку."
            )
            return

        await bot.send_document(
            chat_id=message.chat.id,
            document=FSInputFile(output_path),
        )


@router.message(F.photo)
async def photo_handler(message: Message, bot: Bot) -> None:
    if message.photo is None:
        return

    file_id = message.photo[-1].file_id

    await process_image_message(
        message,
        bot,
        file_id,
    )


@router.message(F.document)
async def document_handler(message: Message, bot: Bot) -> None:
    if message.document is None:
        return

    if message.document.mime_type is None:
        return

    if not message.document.mime_type.startswith("image/"):
        return

    await process_image_message(
        message,
        bot,
        message.document.file_id,
    )