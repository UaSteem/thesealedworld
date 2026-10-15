from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate rift parallax background via project AIService.")
    parser.add_argument(
        "--prompt-file",
        type=Path,
        default=PROJECT_ROOT / "tmp" / "imagegen" / "rift_void_seamless_4k_prompt.txt",
        help="Text prompt file.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=PROJECT_ROOT / "output" / "imagegen" / "rift_void_seamless_4k.png",
        help="Output image path.",
    )
    parser.add_argument("--model", default=None, help="Gemini image model. Defaults to settings.gemini_image_model.")
    parser.add_argument("--aspect-ratio", default="16:9", help="Gemini image_config aspect_ratio.")
    parser.add_argument("--image-size", default=None, help="Optional Gemini image_config image_size.")
    parser.add_argument(
        "--no-image-config",
        action="store_true",
        help="Do not send image_config. Useful for flash image models that reject size hints.",
    )
    parser.add_argument("--mime-type", default="image/png", help="Requested response MIME type.")
    parser.add_argument("--dry-run", action="store_true", help="Print the request without calling Gemini.")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    prompt_path = args.prompt_file if args.prompt_file.is_absolute() else PROJECT_ROOT / args.prompt_file
    output_path = args.out if args.out.is_absolute() else PROJECT_ROOT / args.out

    prompt = prompt_path.read_text(encoding="utf-8").strip()
    if not prompt:
        raise SystemExit(f"Prompt file is empty: {prompt_path}")

    from src.backend.config.settings import settings
    from src.backend.core.ai import AIService

    model = args.model or settings.gemini_image_model
    image_config = None
    if not args.no_image_config:
        image_config = {"aspect_ratio": args.aspect_ratio}
        if args.image_size:
            image_config["image_size"] = args.image_size

    if args.dry_run:
        print("Rift background generation dry-run")
        print(f"model={model}")
        print(f"mime_type={args.mime_type}")
        print(f"image_config={image_config}")
        print(f"prompt_file={prompt_path}")
        print(f"out={output_path}")
        print(prompt)
        return

    ai = AIService()
    if ai.provider is None:
        raise SystemExit("Gemini provider is not configured. Check GEMINI_API_KEY in project settings/.env.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Generating rift background with model={model}, image_config={image_config} ...")
    content, content_type = await ai.generate_image_bytes(
        prompt=prompt,
        model=model,
        response_mime_type=args.mime_type,
        **({"image_config": image_config} if image_config else {}),
    )
    if not content:
        raise SystemExit("Gemini returned empty image content")

    output_path.write_bytes(content)
    print(f"Saved {output_path} ({len(content):,} bytes, {content_type})")


if __name__ == "__main__":
    asyncio.run(main())
