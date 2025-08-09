#!/usr/bin/env python3
import asyncio
import argparse
import os
import re
from io import BytesIO
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional
from pathlib import Path
import webbrowser

from PIL import Image

# Playwright is async
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


def sanitize_filename(text: str) -> str:
    # Keep letters, numbers, dash and underscore
    text = re.sub(r"[^a-zA-Z0-9\-_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "screenshot"


def derive_default_output_path(url: str, fmt: str) -> str:
    parsed = urlparse(url)
    host = sanitize_filename(parsed.netloc)
    path = sanitize_filename(parsed.path or "home")
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = f"{host}_{path}_{ts}.{fmt}"
    return os.path.abspath(base)


async def capture_fullpage_png_bytes(
    url: str,
    viewport_width: int,
    wait_networkidle_ms: int,
    auto_scroll: bool,
    hide_scrollbars: bool,
    timeout_ms: int,
    wait_until: str,
) -> bytes:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": viewport_width, "height": 1080},
            device_scale_factor=1,
        )
        page = await context.new_page()

        # Navigare configurabilă
        await page.goto(url, wait_until=wait_until, timeout=timeout_ms)

        # Încercare scurtă de "liniște" în rețea dacă nu am așteptat deja networkidle
        if wait_until != "networkidle":
            try:
                await page.wait_for_load_state("networkidle", timeout=min(2000, timeout_ms))
            except PlaywrightTimeoutError:
                pass

        if auto_scroll:
            # Trigger lazy-loaded content
            await page.evaluate(
                """
                async () => {
                  await new Promise(resolve => {
                    let totalHeight = 0;
                    const distance = 500;
                    const delay = 100;
                    const timer = setInterval(() => {
                      const { scrollHeight } = document.documentElement;
                      window.scrollBy(0, distance);
                      totalHeight += distance;
                      if (totalHeight + window.innerHeight >= scrollHeight) {
                        clearInterval(timer);
                        resolve();
                      }
                    }, delay);
                  });
                }
                """
            )
            # Dă timp layout-ului să se stabilizeze după autoscroll
            await page.wait_for_timeout(wait_networkidle_ms)
            if wait_until != "networkidle":
                try:
                    await page.wait_for_load_state("networkidle", timeout=1000)
                except PlaywrightTimeoutError:
                    pass

        # Întoarce-te sus înainte de captură ca header-ul să fie la începutul imaginii
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(150)

        if hide_scrollbars:
            await page.add_style_tag(
                content=(
                    "html,body{scrollbar-width:none !important;} ::-webkit-scrollbar{display:none !important;}"
                )
            )

        png_bytes = await page.screenshot(full_page=True, type="png")
        await browser.close()
        return png_bytes


def compress_and_resize(
    png_bytes: bytes,
    target_width: int,
    fmt: str,
    quality: int,
    max_bytes: Optional[int],
    target_height: Optional[int] = None,
) -> bytes:
    fmt = fmt.lower()
    with Image.open(BytesIO(png_bytes)) as im:
        # Convert to RGB if needed for lossy formats
        if fmt in ("jpeg", "jpg", "webp") and im.mode not in ("RGB", "L"):
            im = im.convert("RGB")

        # Downscale if larger than target_width
        if target_width and im.width > target_width:
            new_height = int(im.height * (target_width / im.width))
            im = im.resize((target_width, new_height), Image.LANCZOS)

        # Crop vertical dacă se cere o înălțime maximă
        if target_height and im.height > target_height:
            im = im.crop((0, 0, im.width, target_height))

        def save_to_bytes(current_quality: int) -> bytes:
            buffer = BytesIO()
            if fmt == "png":
                im.save(buffer, format="PNG", optimize=True, compress_level=9)
            elif fmt in ("jpeg", "jpg"):
                im.save(
                    buffer,
                    format="JPEG",
                    quality=current_quality,
                    optimize=True,
                    progressive=True,
                )
            elif fmt == "webp":
                im.save(
                    buffer,
                    format="WEBP",
                    quality=current_quality,
                    method=6,
                )
            else:
                raise ValueError(f"Format neacceptat: {fmt}")
            return buffer.getvalue()

        # Initial save
        out = save_to_bytes(quality)

        # If a max_bytes constraint is given, reduce quality iterativ până încape
        if max_bytes is not None and fmt in ("jpeg", "jpg", "webp"):
            current_quality = quality
            while len(out) > max_bytes and current_quality > 30:
                current_quality = max(30, current_quality - 5)
                out = save_to_bytes(current_quality)

        return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Face screenshot full-page la un URL și îl salvează optimizat pentru web."
        )
    )
    parser.add_argument("url", help="Adresa paginii web (ex: https://exemplu.com)")
    parser.add_argument(
        "--output",
        "-o",
        help="Calea fișierului de ieșire (extensia va dicta formatul). Dacă lipsește, se generează automat.",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["webp", "jpeg", "jpg", "png"],
        default="webp",
        help="Formatul imaginii finale (implicit: webp)",
    )
    parser.add_argument(
        "--capture-width",
        type=int,
        default=1280,
        help="Lățimea viewport-ului folosită pentru captură (implicit: 1280)",
    )
    parser.add_argument(
        "--output-width",
        type=int,
        default=800,
        help="Lățimea finală a imaginii pentru web (implicit: 800)",
    )
    parser.add_argument(
        "--output-height",
        type=int,
        default=None,
        help="Înălțimea maximă a imaginii. Dacă e depășită, se cropează de sus (opțional)",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=70,
        help="Calitatea imaginii pentru formatele cu pierderi (webp/jpeg). 1-100 (implicit: 70)",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=None,
        help="Mărimea maximă a fișierului (în bytes). Se ajustează calitatea pentru a se încadra (opțional)",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=60000,
        help="Timeout încărcare pagină în milisecunde (implicit: 60000)",
    )
    parser.add_argument(
        "--wait-ms",
        type=int,
        default=800,
        help="Pauză după auto-scroll înainte de captură (ms, implicit: 800)",
    )
    parser.add_argument(
        "--wait-until",
        choices=["domcontentloaded", "load", "networkidle"],
        default="load",
        help="Momentul de așteptare înainte de captură (implicit: load)",
    )
    parser.add_argument(
        "--no-autoscroll",
        action="store_true",
        help="Dezactivează auto-scroll pentru a încărca conținutul lazy",
    )
    parser.add_argument(
        "--show-scrollbars",
        action="store_true",
        help="Nu ascunde scrollbars în captura finală",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Deschide imaginea salvată în browserul implicit",
    )
    return parser.parse_args()


def ensure_output_path(path: Optional[str], url: str, fmt: str) -> str:
    if path:
        root, ext = os.path.splitext(path)
        if ext.lower() not in (".webp", ".jpg", ".jpeg", ".png"):
            path = f"{path}.{fmt}"
        return os.path.abspath(path)
    else:
        return derive_default_output_path(url, fmt)


async def main_async():
    args = parse_args()

    fmt = args.format.lower()
    output_path = ensure_output_path(args.output, args.url, fmt)

    png_bytes = await capture_fullpage_png_bytes(
        url=args.url,
        viewport_width=args.capture_width,
        wait_networkidle_ms=args.wait_ms,
        auto_scroll=not args.no_autoscroll,
        hide_scrollbars=not args.show_scrollbars,
        timeout_ms=args.timeout_ms,
        wait_until=args.wait_until,
    )

    optimized_bytes = compress_and_resize(
        png_bytes=png_bytes,
        target_width=args.output_width,
        fmt=fmt,
        quality=args.quality,
        max_bytes=args.max_bytes,
        target_height=args.output_height,
    )

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(optimized_bytes)

    size_kb = len(optimized_bytes) / 1024
    print(f"Salvat: {output_path} ({size_kb:.1f} KB)")

    if args.open:
        uri = Path(output_path).resolve().as_uri()
        webbrowser.open(uri)


def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main() 