import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.backend.core.ai import AIService  # noqa: E402

THEMES_FILE = ROOT / "tools" / "tileset_builder" / "themes.json"
ASSETS_DIR = ROOT / "assets" / "tilesets" / "raw"

def load_prompt(theme_name: str) -> str:
    if not THEMES_FILE.exists():
        raise FileNotFoundError(f"Missing themes file: {THEMES_FILE}")

    with open(THEMES_FILE, encoding="utf-8") as f:
        data = json.load(f)

    master = data.get("master_prompt", "")
    themes = data.get("themes", {})

    if theme_name not in themes:
        raise ValueError(f"Theme '{theme_name}' not found in {THEMES_FILE}")

    theme_data = themes[theme_name]

    parts = [
        master,
        "\nTheme Specifics:",
        f"Theme: {theme_data.get('theme_description', '')}",
        f"Blocker Nodes: {theme_data.get('blocker_nodes', '')}",
        f"Movement Nodes: {theme_data.get('movement_nodes', '')}",
        f"Level Transition Nodes: {theme_data.get('level_transition_nodes', '')}",
        f"Event Nodes: {theme_data.get('event_nodes', '')}",
        f"Mood / Floor Variant Nodes: {theme_data.get('mood_nodes', '')}",
        f"Colors: {theme_data.get('colors', '')}",
    ]
    return "\n".join(parts)

async def main():
    parser = argparse.ArgumentParser(description="Clean tileset generation script.")
    parser.add_argument("--theme", required=True, help="Theme to generate (e.g. void_temple)")
    args = parser.parse_args()

    try:
        prompt = load_prompt(args.theme)
    except Exception as e:
        print(f"Error loading prompt: {e}")
        sys.exit(1)

    ai = AIService()
    if ai.provider is None:
        print("ERROR: Gemini API key not configured. Set GEMINI_API_KEY in .env")
        sys.exit(1)

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"hex_tileset_{args.theme}_{timestamp}.png"
    output_path = ASSETS_DIR / output_filename

    print(f"Ordering 4K tileset for theme: {args.theme}...")
    print("This might take a minute...")

    # Load the master template mask
    mask_path = ROOT / "ai_master_template.png"
    if not mask_path.exists():
        mask_path = ROOT / "assets" / "ai_templates" / "ai_master_template.png"

    if not mask_path.exists():
        print(f"ERROR: Could not find mask image at {mask_path}")
        sys.exit(1)

    mask_bytes = mask_path.read_bytes()
    print(f"Loaded master template mask: {mask_path.name} ({len(mask_bytes):,} bytes)")

    content, content_type = await ai.generate_image_bytes(
        prompt,
        model="gemini-3-pro-image-preview",
        response_mime_type="image/png",
        image_config={
            "aspect_ratio": "1:1",
            "image_size": "4K",
        },
        input_images=[{"data": mask_bytes, "mime_type": "image/png"}],
    )

    output_path.write_bytes(content)
    print(f"Success! Image saved to: {output_path} ({len(content):,} bytes, {content_type})")

if __name__ == "__main__":
    asyncio.run(main())
