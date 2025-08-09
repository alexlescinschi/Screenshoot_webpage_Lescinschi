#!/usr/bin/env python3
import asyncio
import re
from datetime import datetime
from urllib.parse import urlparse
from io import BytesIO
import base64
import time
import sys
import traceback
import subprocess
import tempfile
import os
from pathlib import Path

from flask import Flask, render_template, request

# Importăm utilitare non-async din screenshot doar dacă avem nevoie
import screenshot as sc

app = Flask(__name__)


def ensure_scheme(url: str) -> str:
    if not re.match(r"^https?://", url, flags=re.IGNORECASE):
        return "https://" + url
    return url


def build_filename(url: str, fmt: str) -> str:
    parsed = urlparse(url)
    host = re.sub(r"[^a-zA-Z0-9\-_]+", "-", parsed.netloc).strip("-") or "site"
    path = re.sub(r"[^a-zA-Z0-9\-_]+", "-", parsed.path or "home").strip("-") or "home"
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    ext = fmt.lower()
    return f"{host}_{path}_{ts}.{ext}"


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/shot")
def shot():
    url = (request.form.get("url") or "").strip()
    if not url:
        return render_template("index.html", error="Te rugăm să introduci o adresă validă.")

    url = ensure_scheme(url)

    fmt = (request.form.get("format") or "webp").lower()
    if fmt not in ("webp", "jpeg", "jpg", "png"):
        fmt = "webp"

    def to_int(name: str, default_value: int) -> int:
        try:
            return int(request.form.get(name) or default_value)
        except ValueError:
            return default_value

    output_width = to_int("output_width", 800)
    output_height = request.form.get("output_height")
    output_height_int = int(output_height) if output_height and output_height.isdigit() else None
    quality = to_int("quality", 70)
    capture_width = to_int("capture_width", 1280)
    wait_ms = to_int("wait_ms", 800)
    timeout_ms = to_int("timeout_ms", 60000)
    wait_until = (request.form.get("wait_until") or "load").lower()
    if wait_until not in ("domcontentloaded", "load", "networkidle"):
        wait_until = "load"

    print(f"[SHOT] START url={url} fmt={fmt} outW={output_width} outH={output_height_int} capW={capture_width} waitMs={wait_ms} timeoutMs={timeout_ms} waitUntil={wait_until}")
    sys.stdout.flush()
    t0 = time.time()

    # Rulează screenshot.py ca proces separat pentru a evita blocaje event loop în Flask
    scr_path = str(Path(__file__).with_name("screenshot.py"))
    with tempfile.TemporaryDirectory() as td:
        out_path = os.path.join(td, f"out.{fmt}")
        cmd = [
            sys.executable,
            scr_path,
            url,
            "-o",
            out_path,
            "-f",
            fmt,
            "--capture-width",
            str(capture_width),
            "--output-width",
            str(output_width),
            "--quality",
            str(quality),
            "--timeout-ms",
            str(timeout_ms),
            "--wait-ms",
            str(wait_ms),
            "--wait-until",
            wait_until,
        ]
        if output_height_int is not None:
            cmd += ["--output-height", str(output_height_int)]
        print(f"[SHOT] RUN: {' '.join(cmd)}")
        sys.stdout.flush()
        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            print(f"[SHOT] SUBPROC STDOUT:\n{proc.stdout}")
            if proc.stderr:
                print(f"[SHOT] SUBPROC STDERR:\n{proc.stderr}")
            sys.stdout.flush()
        except subprocess.CalledProcessError as exc:
            # Log complet în consolă
            print("[SHOT] ERROR (subprocess):")
            print(exc.stdout)
            print(exc.stderr)
            sys.stdout.flush()
            # Trimite un extras util în UI
            stdout_snip = (exc.stdout or "").strip()
            stderr_snip = (exc.stderr or "").strip()
            def tail(txt: str, n: int = 30) -> str:
                lines = txt.splitlines()
                return "\n".join(lines[-n:])
            details = tail(stdout_snip, 20)
            if stderr_snip:
                details += ("\n" if details else "") + tail(stderr_snip, 20)
            if not details:
                details = "Subprocesul a eșuat fără mesaje. Încearcă din nou cu alt URL sau mărește timeout."
            return render_template("index.html", error=f"Eroare la generare (subprocess):\n{details}")

        # Citește fișierul rezultat
        try:
            with open(out_path, "rb") as f:
                optimized = f.read()
        except FileNotFoundError:
            return render_template("index.html", error="Nu s-a produs fișierul de ieșire.")

    t1 = time.time()
    print(f"[SHOT] DONE total={(t1 - t0):.2f}s size={len(optimized)/1024:.1f} KB")
    sys.stdout.flush()

    filename = build_filename(url, fmt)
    mime = {
        "webp": "image/webp",
        "jpeg": "image/jpeg",
        "jpg": "image/jpeg",
        "png": "image/png",
    }.get(fmt, "application/octet-stream")
    data_uri = f"data:{mime};base64," + base64.b64encode(optimized).decode("ascii")
    size_kb = len(optimized) / 1024

    return render_template(
        "index.html",
        preview_data_uri=data_uri,
        filename=filename,
        size_kb=f"{size_kb:.1f}",
    )


if __name__ == "__main__":
    # Pornire server dezvoltare
    app.run(host="127.0.0.1", port=5000, debug=False) 