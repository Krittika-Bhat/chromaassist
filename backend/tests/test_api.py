"""
test_api.py
===========
Integration tests for the FastAPI endpoints.

We call the ASGI app directly in-process via httpx.AsyncClient +
httpx.ASGITransport, wrapped in asyncio.run() so each test gets a
clean, independent event loop (no pytest-anyio / starlette-TestClient
threading conflicts).

Covered
-------
- GET  /api/health
- POST /api/process  (simulate, correct, pseudocolor modes)
- POST /api/compare
- File-type rejection (non-PNG/JPG)  → HTTP 400
- File-size rejection (> 10 MB)      → HTTP 413
- Metrics keys present and valid
- Identity at severity=0 through the API
"""

import asyncio
import io
import base64
import sys
import os

import numpy as np
import pytest
import httpx
from PIL import Image

# Ensure the backend root is importable when running from /tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_png_bytes(h: int = 60, w: int = 60) -> bytes:
    """Create a small synthetic vivid red/green PNG in memory."""
    img_arr = np.zeros((h, w, 3), dtype=np.uint8)
    img_arr[:, : w // 2] = [220, 30, 30]
    img_arr[:, w // 2 :] = [30, 200, 30]
    pil_img = Image.fromarray(img_arr, mode="RGB")
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return buf.getvalue()


def _make_jpeg_bytes() -> bytes:
    """Create a small synthetic JPEG in memory."""
    img_arr = np.full((40, 40, 3), [100, 150, 200], dtype=np.uint8)
    pil_img = Image.fromarray(img_arr, mode="RGB")
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _is_valid_base64_png(b64str: str) -> bool:
    """Return True if the string decodes to a valid image."""
    try:
        raw = base64.b64decode(b64str)
        Image.open(io.BytesIO(raw)).verify()
        return True
    except Exception:
        return False


def _call(coro):
    """Run an async coroutine in a fresh event loop (sync helper)."""
    return asyncio.run(coro)


async def _post(path: str, data: dict, file_tuple: tuple) -> httpx.Response:
    """POST multipart form data to the ASGI app in-process."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        return await ac.post(path, data=data, files={"file": file_tuple})


async def _get(path: str) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        return await ac.get(path)


EXPECTED_METRIC_KEYS = {
    "original_vs_simulated_delta_e",
    "corrected_vs_its_simulation_delta_e",
    "delta_e_note",
    "deficiency",
    "severity",
    "pair_discriminability",
    "pair_delta_e_simulated_original",
    "pair_delta_e_simulated_corrected",
    "pair_discriminability_gain_pct",
}

# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

def test_health():
    resp = _call(_get("/api/health"))
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# /api/process – simulate mode
# ---------------------------------------------------------------------------

def test_process_simulate():
    png = _make_png_bytes()
    resp = _call(_post(
        "/api/process",
        {"mode": "simulate", "deficiency": "deuteranopia",
         "severity": "1.0", "method": "global"},
        ("test.png", png, "image/png"),
    ))
    assert resp.status_code == 200
    data = resp.json()
    assert "processed_image_b64" in data
    assert _is_valid_base64_png(data["processed_image_b64"])
    assert EXPECTED_METRIC_KEYS.issubset(data["metrics"].keys())


# ---------------------------------------------------------------------------
# /api/process – correct mode (global)
# ---------------------------------------------------------------------------

def test_process_correct_global():
    png = _make_png_bytes()
    resp = _call(_post(
        "/api/process",
        {"mode": "correct", "deficiency": "protanopia",
         "severity": "1.0", "method": "global"},
        ("test.png", png, "image/png"),
    ))
    assert resp.status_code == 200
    data = resp.json()
    assert _is_valid_base64_png(data["processed_image_b64"])
    metrics = data["metrics"]
    assert EXPECTED_METRIC_KEYS.issubset(metrics.keys())
    assert metrics["original_vs_simulated_delta_e"] >= 0
    assert metrics["corrected_vs_its_simulation_delta_e"] >= 0


# ---------------------------------------------------------------------------
# /api/process – correct mode (targeted)
# ---------------------------------------------------------------------------

def test_process_correct_targeted():
    png = _make_png_bytes()
    resp = _call(_post(
        "/api/process",
        {"mode": "correct", "deficiency": "deuteranopia",
         "severity": "1.0", "method": "targeted"},
        ("test.png", png, "image/png"),
    ))
    assert resp.status_code == 200
    assert _is_valid_base64_png(resp.json()["processed_image_b64"])


# ---------------------------------------------------------------------------
# /api/process – pseudocolor mode
# ---------------------------------------------------------------------------

def test_process_pseudocolor():
    png = _make_png_bytes()
    resp = _call(_post(
        "/api/process",
        {"mode": "pseudocolor", "deficiency": "deuteranopia",
         "severity": "1.0", "method": "global", "colormap": "cividis"},
        ("test.png", png, "image/png"),
    ))
    assert resp.status_code == 200
    assert _is_valid_base64_png(resp.json()["processed_image_b64"])


# ---------------------------------------------------------------------------
# /api/process – JPEG accepted
# ---------------------------------------------------------------------------

def test_process_accepts_jpeg():
    jpg = _make_jpeg_bytes()
    resp = _call(_post(
        "/api/process",
        {"mode": "simulate", "deficiency": "tritanopia",
         "severity": "0.5", "method": "global"},
        ("photo.jpg", jpg, "image/jpeg"),
    ))
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# /api/compare
# ---------------------------------------------------------------------------

def test_compare_returns_four_images():
    png = _make_png_bytes()
    resp = _call(_post(
        "/api/compare",
        {"deficiency": "deuteranopia", "severity": "1.0", "method": "global"},
        ("test.png", png, "image/png"),
    ))
    assert resp.status_code == 200
    data = resp.json()
    for key in ("original_b64", "simulated_b64", "corrected_b64", "corrected_simulated_b64"):
        assert key in data, f"Missing key: {key}"
        assert _is_valid_base64_png(data[key]), f"Invalid image for key: {key}"
    assert EXPECTED_METRIC_KEYS.issubset(data["metrics"].keys())


# ---------------------------------------------------------------------------
# File-type rejection  →  HTTP 400
# ---------------------------------------------------------------------------

def test_reject_non_image_file():
    """Uploading a plain-text file must return HTTP 400 with a JSON error."""
    resp = _call(_post(
        "/api/process",
        {"mode": "simulate", "deficiency": "deuteranopia",
         "severity": "1.0", "method": "global"},
        ("document.txt", b"not an image at all", "text/plain"),
    ))
    assert resp.status_code == 400
    detail = resp.json()["detail"]
    assert detail["error"] == "unsupported_file_type"
    assert "PNG" in detail["message"] or "JPEG" in detail["message"]


def test_reject_gif_file():
    """GIF files are not supported → HTTP 400."""
    gif_bytes = (
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff"
        b"\x00\x00\x00!\xf9\x04\x00\x00\x00\x00\x00,"
        b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    )
    resp = _call(_post(
        "/api/process",
        {"mode": "simulate", "deficiency": "deuteranopia",
         "severity": "1.0", "method": "global"},
        ("anim.gif", gif_bytes, "image/gif"),
    ))
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"] == "unsupported_file_type"


# ---------------------------------------------------------------------------
# File-size rejection  →  HTTP 413
# ---------------------------------------------------------------------------

def test_reject_oversized_file():
    """A file larger than 10 MB must return HTTP 413 with a clear JSON error."""
    big_data = b"\x00" * (11 * 1024 * 1024)   # 11 MB
    resp = _call(_post(
        "/api/process",
        {"mode": "simulate", "deficiency": "deuteranopia",
         "severity": "1.0", "method": "global"},
        ("huge.png", big_data, "image/png"),
    ))
    assert resp.status_code == 413
    detail = resp.json()["detail"]
    assert detail["error"] == "file_too_large"
    assert "10 MB" in detail["message"]


# ---------------------------------------------------------------------------
# Identity at severity=0 through the API
# ---------------------------------------------------------------------------

def test_api_identity_severity_zero():
    """
    Via the API: simulate at severity=0 must return an image pixel-identical
    (within ±1 rounding) to the input.
    """
    png_bytes = _make_png_bytes()
    resp = _call(_post(
        "/api/process",
        {"mode": "simulate", "deficiency": "deuteranopia",
         "severity": "0.0", "method": "global"},
        ("test.png", png_bytes, "image/png"),
    ))
    assert resp.status_code == 200
    b64 = resp.json()["processed_image_b64"]
    result_img = np.array(Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB"))
    original_img = np.array(Image.open(io.BytesIO(png_bytes)).convert("RGB"))
    max_diff = np.abs(result_img.astype(np.int16) - original_img.astype(np.int16)).max()
    assert max_diff <= 1, f"severity=0 output differs from input by {max_diff} LSB"
