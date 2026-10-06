import subprocess
from pathlib import Path


MAX_FILE_SIZE = 256 * 1024


def process_video(input_path: Path, output_path: Path) -> None:
    crf_values = [30, 35, 40, 45, 50]
    fps_values = [30, 24, 20, 15]

    for fps in fps_values:
        for crf in crf_values:
            command = [
                "ffmpeg",
                "-y",
                "-i",
                str(input_path),
                "-t",
                "3",
                "-vf",
                (
                    "scale=512:512:"
                    "force_original_aspect_ratio=decrease,"
                    "pad=512:512:(ow-iw)/2:(oh-ih)/2:color=black@0,"
                    "setsar=1"
                ),
                "-r",
                str(fps),
                "-an",
                "-c:v",
                "libvpx-vp9",
                "-pix_fmt",
                "yuva420p",
                "-auto-alt-ref",
                "0",
                "-b:v",
                "0",
                "-crf",
                str(crf),
                str(output_path),
            ]

            result = subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"FFmpeg error:\n{result.stderr}"
                )

            if output_path.stat().st_size <= MAX_FILE_SIZE:
                return

    raise ValueError(
        "Не удалось уложить видео в 256 КБ."
    )