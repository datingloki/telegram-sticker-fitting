from pathlib import Path

from PIL import Image, ImageOps
from PIL.Image import UnidentifiedImageError


MAX_SIZE = 512
MAX_FILE_SIZE = 512 * 1024


def process_image(input_path: Path, output_path: Path) -> None:
    try:
        image = Image.open(input_path)
    except UnidentifiedImageError as error:
        raise ValueError("File is not a valid image") from error

    image = ImageOps.exif_transpose(image)

    image.thumbnail(
        (MAX_SIZE, MAX_SIZE),
        Image.Resampling.LANCZOS,
    )

    if image.mode != "RGBA":
        image = image.convert("RGBA")

    canvas = Image.new(
        "RGBA",
        (MAX_SIZE, MAX_SIZE),
        (0, 0, 0, 0),
    )

    x = (MAX_SIZE - image.width) // 2
    y = (MAX_SIZE - image.height) // 2

    canvas.alpha_composite(image, (x, y))

    canvas.save(
        output_path,
        format="WEBP",
        lossless=True,
        method=6,
    )

    if output_path.stat().st_size <= MAX_FILE_SIZE:
        return

    for quality in range(95, 0, -5):
        canvas.save(
            output_path,
            format="WEBP",
            quality=quality,
            method=6,
        )

        if output_path.stat().st_size <= MAX_FILE_SIZE:
            return

    raise ValueError("Image is too large to fit into 512 KB")