from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> None:
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    os.environ.setdefault("STREAMLIT_SERVER_PORT", "8501")

    process = subprocess.Popen(
        [
            "streamlit",
            "run",
            "src/dashboard/app.py",
            "--server.headless=true",
            "--server.port=8501",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        time.sleep(5)
        output_dir = Path("site")
        output_dir.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 720})
            page.goto("http://127.0.0.1:8501", wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            image_path = output_dir / "dashboard.png"
            page.screenshot(path=str(image_path), full_page=True)
            browser.close()

        (output_dir / "index.html").write_text(
            """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Dashboard Preview</title>
</head>
<body>
  <h1>Dashboard Preview</h1>
  <p>Static snapshot from GitHub Actions.</p>
  <img src=\"dashboard.png\" alt=\"Dashboard preview\" style=\"max-width: 100%; height: auto;\" />
</body>
</html>
""".strip()
        )
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    main()
