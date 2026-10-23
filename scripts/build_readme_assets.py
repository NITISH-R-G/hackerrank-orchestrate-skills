"""Regenerate the README screenshots from real command output and the real site page.

    python scripts/build_readme_assets.py

Every terminal image is the captured stdout of a real command run in this repository.
The site image is a headless-browser screenshot of the generated site/index.html.
Nothing is drawn by hand, so the images cannot drift from the code without this script
being run again. The designed SVG graphics (hero, features, architecture, workflow, results,
tech-stack, divider) are hand-authored sources kept in the same folder. Requires Pillow (already used by the repo's tooling) and, for the site
image, Microsoft Edge or Google Chrome installed locally.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "readme"
FONT_CANDIDATES = [r"C:\Windows\Fonts\consola.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]

CAPTURES = [
    ("orchestrate-selftest.png", "orchestrate selftest (tail)",
     [sys.executable, "-m", "orchestrate_kit", "selftest"], 22),
    ("orchestrate-score-audit.png", "orchestrate score --audit (tail)",
     [sys.executable, "-m", "orchestrate_kit", "score", "--audit"], 18),
    ("research-data-check.png", "scripts/build_research_data.py --check",
     [sys.executable, "scripts/build_research_data.py", "--check"], 6),
]

BROWSERS = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]


def font(size: int):
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def render(lines: list[str], title: str, dest: Path) -> None:
    f = font(15)
    width = 980
    line_h = 21
    height = 56 + line_h * (len(lines) + 1) + 20
    img = Image.new("RGB", (width, height), (24, 27, 36))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, width, 34], fill=(40, 44, 56))
    for i, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([12 + i * 20, 10, 24 + i * 20, 22], fill=color)
    d.text((86, 8), title, fill=(200, 205, 215), font=f)
    y = 46
    for line in lines:
        d.text((16, y), line[:120], fill=(220, 225, 235), font=f)
        y += line_h
    img.save(dest, optimize=True)


def run(cmd: list[str]) -> list[str]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (proc.stdout + proc.stderr).rstrip().splitlines()


def site_screenshot(dest: Path) -> bool:
    browser = next((b for b in BROWSERS if Path(b).exists()), None)
    if browser is None:
        print("no Chrome or Edge found; site screenshot skipped")
        return False
    page = (ROOT / "site" / "index.html").resolve().as_uri()
    subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--window-size=1100,1500", f"--screenshot={dest}", page],
                   capture_output=True, timeout=120)
    if dest.exists():
        with Image.open(dest) as im:
            im.convert("RGB").save(dest, optimize=True)
        return True
    return False


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, title, cmd, tail in CAPTURES:
        lines = run(cmd)
        render(lines[-tail:], title, OUT / name)
        print("wrote", (OUT / name).relative_to(ROOT))
    if site_screenshot(OUT / "site-landing.png"):
        print("wrote", (OUT / "site-landing.png").relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
