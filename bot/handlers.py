import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, Message
from PIL import UnidentifiedImageError

from processors.image import process_image
from processors.video import process_video


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

    await message.answer("⏳ Получил файл! Обрабатываю его...")
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

        await bot.send_sticker(
            chat_id=message.chat.id,
            sticker=FSInputFile(output_path),
        )




async def process_video_message(
    message: Message,
    bot: Bot,
    file_id: str,
) -> None:
    await message.answer("⏳ Получил файл! Обрабатываю его...")
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        input_path = temp_path / "input"
        output_path = temp_path / "sticker.webm"

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
                process_video,
                input_path,
                output_path,
            )
        except (ValueError, RuntimeError):
            await message.answer(
                "Не получилось подготовить видео "
                "в формате стикера."
            )
            return

        await bot.send_sticker(
            chat_id=message.chat.id,
            sticker=FSInputFile(output_path),
        )

@router.message(F.photo)
async def photo_handler(
    message: Message,
    bot: Bot,
) -> None:
    if message.photo is None:
        return

    await process_image_message(
        message,
        bot,
        message.photo[-1].file_id,
    )


@router.message(F.animation)
async def animation_handler(
    message: Message,
    bot: Bot,
) -> None:
    if message.animation is None:
        return

    await process_video_message(
        message,
        bot,
        message.animation.file_id,
    )


@router.message(F.video)
async def video_handler(
    message: Message,
    bot: Bot,
) -> None:
    if message.video is None:
        return

    await process_video_message(
        message,
        bot,
        message.video.file_id,
    )


@router.message(F.document)
async def document_handler(
    message: Message,
    bot: Bot,
) -> None:
    if message.document is None:
        return

    mime_type = message.document.mime_type

    if mime_type == "image/gif":
        await process_video_message(
            message,
            bot,
            message.document.file_id,
        )
        return

    if mime_type is not None and mime_type.startswith("image/"):
        await process_image_message(
            message,
            bot,
            message.document.file_id,
        )
        return

    if mime_type is not None and mime_type.startswith("video/"):
        await process_video_message(
            message,
            bot,
            message.document.file_id,
        )