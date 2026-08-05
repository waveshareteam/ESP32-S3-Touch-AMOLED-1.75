#!/usr/bin/env python3
"""Generate synthetic media fixtures for ESP32-S3-Touch-AMOLED-1.75 SD tests."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import shutil
import struct
import sys
import wave
from array import array
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PHOTO_WIDE = (320, 240)
PHOTO_SQUARE = (360, 360)
VIDEO_SIZE = (320, 240)
VIDEO_FPS = 10
VIDEO_SECONDS = 5
VIDEO_AUDIO_RATE = 24_000
DOCUMENT_NAMES = {"media_manifest.json", "README.txt", "MEDIA_GUIDE.md"}
SD_README_TEMPLATE = Path(__file__).with_name("SD_CARD_README.txt")
MEDIA_GUIDE_SOURCE = Path(__file__).resolve().parents[2] / "MEDIA_GUIDE.md"
MUSIC_TRACKS = (
    ("01-left-440Hz-right-880Hz.wav", 440.0, 880.0, 5),
    ("02-left-330Hz-right-660Hz.wav", 330.0, 660.0, 2),
    ("03-left-392Hz-right-784Hz.wav", 392.0, 784.0, 2),
    ("04-left-523Hz-right-1046Hz.wav", 523.0, 1046.0, 2),
    ("05-left-262Hz-right-524Hz.wav", 262.0, 524.0, 2),
    ("06-left-659Hz-right-988Hz.wav", 659.0, 988.0, 2),
)


def pcm_stereo(
    sample_rate: int,
    sample_count: int,
    start_sample: int = 0,
    left_frequency: float = 440.0,
    right_frequency: float = 880.0,
) -> bytes:
    samples = array("h")
    for index in range(start_sample, start_sample + sample_count):
        time_s = index / sample_rate
        envelope = min(1.0, index / max(1, sample_rate // 20))
        left = int(10_000 * envelope * math.sin(2 * math.pi * left_frequency * time_s))
        right = int(10_000 * envelope * math.sin(2 * math.pi * right_frequency * time_s))
        samples.extend((left, right))
    if sys.byteorder != "little":
        samples.byteswap()
    return samples.tobytes()


def write_wav(
    path: Path,
    sample_rate: int = 44_100,
    seconds: int = 5,
    left_frequency: float = 440.0,
    right_frequency: float = 880.0,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(
            pcm_stereo(
                sample_rate,
                sample_rate * seconds,
                left_frequency=left_frequency,
                right_frequency=right_frequency,
            )
        )


def draw_test_pattern(size: tuple[int, int], frame: int, total: int) -> Image.Image:
    width, height = size
    image = Image.new("RGB", size, (18, 23, 34))
    draw = ImageDraw.Draw(image)
    colors = (
        (239, 68, 68),
        (245, 158, 11),
        (34, 197, 94),
        (14, 165, 233),
        (99, 102, 241),
        (217, 70, 239),
    )
    bar_width = max(1, width // len(colors))
    for index, color in enumerate(colors):
        left = index * bar_width
        right = width if index == len(colors) - 1 else (index + 1) * bar_width
        draw.rectangle((left, 0, right, height // 3), fill=color)

    margin = max(12, min(width, height) // 16)
    draw.rectangle((margin, margin, width - margin - 1, height - margin - 1), outline="white", width=3)
    draw.line((width // 2, margin, width // 2, height - margin), fill=(255, 255, 255), width=1)
    draw.line((margin, height // 2, width - margin, height // 2), fill=(255, 255, 255), width=1)

    progress = 0 if total <= 1 else frame / (total - 1)
    box_size = max(24, min(width, height) // 7)
    box_x = margin + int(progress * max(0, width - 2 * margin - box_size))
    box_y = height * 2 // 3 - box_size // 2
    draw.rounded_rectangle(
        (box_x, box_y, box_x + box_size, box_y + box_size),
        radius=max(3, box_size // 6),
        fill=(255, 255, 255),
        outline=(0, 0, 0),
        width=2,
    )

    font = ImageFont.load_default()
    label = f"Waveshare SD test  {frame + 1:02d}/{total:02d}"
    draw.rectangle((margin, height - margin - 22, width - margin, height - margin), fill=(0, 0, 0))
    draw.text((margin + 6, height - margin - 18), label, fill=(255, 255, 255), font=font)
    return image


def jpeg_bytes(image: Image.Image, quality: int = 82) -> bytes:
    output = io.BytesIO()
    image.save(
        output,
        format="JPEG",
        quality=quality,
        progressive=False,
        optimize=False,
        subsampling=2,
    )
    data = output.getvalue()
    if b"\xff\xc0" not in data:
        raise RuntimeError("Pillow did not emit a baseline SOF0 JPEG")
    return data


def write_photos(photo_dir: Path) -> None:
    photo_dir.mkdir(parents=True, exist_ok=True)
    (photo_dir / "01-wide-color-bars.jpg").write_bytes(
        jpeg_bytes(draw_test_pattern(PHOTO_WIDE, 0, 1), quality=88)
    )
    (photo_dir / "02-square-navigation.jpg").write_bytes(
        jpeg_bytes(draw_test_pattern(PHOTO_SQUARE, 1, 2), quality=88)
    )


def riff_chunk(chunk_id: bytes, payload: bytes) -> bytes:
    if len(chunk_id) != 4:
        raise ValueError("RIFF chunk id must be four bytes")
    padding = b"\x00" if len(payload) & 1 else b""
    return chunk_id + struct.pack("<I", len(payload)) + payload + padding


def riff_list(list_type: bytes, payload: bytes) -> bytes:
    return riff_chunk(b"LIST", list_type + payload)


def stream_header(
    stream_type: bytes,
    codec: bytes,
    scale: int,
    rate: int,
    length: int,
    suggested_buffer: int,
    sample_size: int,
    width: int = 0,
    height: int = 0,
) -> bytes:
    return struct.pack(
        "<4s4sIHHIIIIIIIIhhhh",
        stream_type,
        codec,
        0,
        0,
        0,
        0,
        scale,
        rate,
        0,
        length,
        suggested_buffer,
        0xFFFFFFFF,
        sample_size,
        0,
        0,
        width,
        height,
    )


def write_mjpeg_pcm_avi(path: Path) -> None:
    width, height = VIDEO_SIZE
    frame_count = VIDEO_FPS * VIDEO_SECONDS
    audio_samples_per_frame = VIDEO_AUDIO_RATE // VIDEO_FPS
    audio_block_align = 4
    audio_bytes_per_second = VIDEO_AUDIO_RATE * audio_block_align

    frames = [
        jpeg_bytes(draw_test_pattern(VIDEO_SIZE, frame, frame_count), quality=76)
        for frame in range(frame_count)
    ]
    maximum_frame = max(map(len, frames))

    avih = struct.pack(
        "<14I",
        1_000_000 // VIDEO_FPS,
        maximum_frame * VIDEO_FPS + audio_bytes_per_second,
        0,
        0,
        frame_count,
        0,
        2,
        maximum_frame,
        width,
        height,
        0,
        0,
        0,
        0,
    )

    video_strh = stream_header(
        b"vids",
        b"MJPG",
        1,
        VIDEO_FPS,
        frame_count,
        maximum_frame,
        0,
        width,
        height,
    )
    video_strf = struct.pack(
        "<IiiHH4sIiiII",
        40,
        width,
        height,
        1,
        24,
        b"MJPG",
        width * height * 3,
        0,
        0,
        0,
        0,
    )
    video_stream = riff_list(
        b"strl",
        riff_chunk(b"strh", video_strh) + riff_chunk(b"strf", video_strf),
    )

    audio_strh = stream_header(
        b"auds",
        b"\x00\x00\x00\x00",
        audio_block_align,
        audio_bytes_per_second,
        VIDEO_AUDIO_RATE * VIDEO_SECONDS,
        audio_samples_per_frame * audio_block_align,
        audio_block_align,
    )
    audio_strf = struct.pack(
        "<HHIIHH",
        1,
        2,
        VIDEO_AUDIO_RATE,
        audio_bytes_per_second,
        audio_block_align,
        16,
    )
    audio_stream = riff_list(
        b"strl",
        riff_chunk(b"strh", audio_strh) + riff_chunk(b"strf", audio_strf),
    )

    header = riff_list(
        b"hdrl",
        riff_chunk(b"avih", avih) + video_stream + audio_stream,
    )
    movi_parts: list[bytes] = []
    for frame_index, frame in enumerate(frames):
        audio = pcm_stereo(
            VIDEO_AUDIO_RATE,
            audio_samples_per_frame,
            frame_index * audio_samples_per_frame,
        )
        movi_parts.append(riff_chunk(b"01wb", audio))
        movi_parts.append(riff_chunk(b"00dc", frame))
    movi = riff_list(b"movi", b"".join(movi_parts))
    avi_payload = b"AVI " + header + movi
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"RIFF" + struct.pack("<I", len(avi_payload)) + avi_payload)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_manifest(root: Path) -> None:
    media_files = sorted(
        path for path in root.rglob("*")
        if path.is_file() and path.name not in DOCUMENT_NAMES
    )
    manifest = {
        "purpose": "ESP32-S3-Touch-AMOLED-1.75 SD hardware validation",
        "files": [
            {
                "path": path.relative_to(root).as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in media_files
        ],
        "video": {
            "codec": "MJPEG",
            "width": VIDEO_SIZE[0],
            "height": VIDEO_SIZE[1],
            "fps": VIDEO_FPS,
            "seconds": VIDEO_SECONDS,
            "audio": "PCM S16LE stereo 24000 Hz",
        },
    }
    (root / "media_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


def generate(root: Path) -> None:
    directories = (
        root / "music",
        root / "photos",
        root / "video",
        root / "Waveshare" / "Recordings",
        root / "Waveshare" / "AIChats",
        root / "Waveshare" / "Diagnostics",
    )
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    for filename, left_frequency, right_frequency, seconds in MUSIC_TRACKS:
        write_wav(
            root / "music" / filename,
            seconds=seconds,
            left_frequency=left_frequency,
            right_frequency=right_frequency,
        )
    write_photos(root / "photos")
    write_mjpeg_pcm_avi(root / "video" / "01-mjpeg-320x240-10fps-pcm24k.avi")
    if not SD_README_TEMPLATE.is_file():
        raise FileNotFoundError(f"SD README template is missing: {SD_README_TEMPLATE}")
    if not MEDIA_GUIDE_SOURCE.is_file():
        raise FileNotFoundError(f"Media guide is missing: {MEDIA_GUIDE_SOURCE}")
    shutil.copyfile(SD_README_TEMPLATE, root / "README.txt")
    shutil.copyfile(MEDIA_GUIDE_SOURCE, root / "MEDIA_GUIDE.md")
    write_manifest(root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Output directory representing the SD-card root")
    args = parser.parse_args()
    generate(args.output.resolve())
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
