"""Quick endpoint smoke-test against the running uvicorn server."""
import urllib.request, json, io
import numpy as np
from PIL import Image

# --- /api/health ---
r = urllib.request.urlopen("http://localhost:8000/api/health")
health = json.loads(r.read())
print("GET /api/health ->", health)
assert health["status"] == "ok"

# --- build a tiny test PNG ---
arr = np.zeros((40, 40, 3), dtype=np.uint8)
arr[:, :20] = [220, 30, 30]
arr[:, 20:] = [30, 200, 30]
buf = io.BytesIO()
Image.fromarray(arr).save(buf, format="PNG")
png = buf.getvalue()

# multipart/form-data helper
def multipart(fields, file_bytes, filename="test.png"):
    sep = b"BND"
    parts = b""
    for name, val in fields.items():
        parts += (b"--" + sep + b"\r\nContent-Disposition: form-data; name=\"" +
                  name.encode() + b"\"\r\n\r\n" + val.encode() + b"\r\n")
    parts += (b"--" + sep + b"\r\nContent-Disposition: form-data; name=\"file\"; filename=\"" +
              filename.encode() + b"\"\r\nContent-Type: image/png\r\n\r\n" +
              file_bytes + b"\r\n")
    parts += b"--" + sep + b"--\r\n"
    return parts, "multipart/form-data; boundary=BND"

# --- /api/process simulate ---
body, ct = multipart({"mode": "simulate", "deficiency": "deuteranopia",
                       "severity": "1.0", "method": "global"}, png)
req = urllib.request.Request("http://localhost:8000/api/process", data=body,
                              headers={"Content-Type": ct})
d = json.loads(urllib.request.urlopen(req).read())
print("POST /api/process (simulate) -> metrics:", d["metrics"])
assert "original_vs_simulated_delta_e" in d["metrics"]
assert "corrected_vs_its_simulation_delta_e" in d["metrics"]
assert len(d["processed_image_b64"]) > 100

# --- /api/compare ---
body2, ct2 = multipart({"deficiency": "deuteranopia", "severity": "1.0",
                         "method": "global"}, png)
req2 = urllib.request.Request("http://localhost:8000/api/compare", data=body2,
                               headers={"Content-Type": ct2})
d2 = json.loads(urllib.request.urlopen(req2).read())
print("POST /api/compare -> keys:", list(d2.keys()))
for k in ("original_b64", "simulated_b64", "corrected_b64", "corrected_simulated_b64"):
    assert k in d2 and len(d2[k]) > 100, f"Missing or empty: {k}"

print()
print("All endpoint checks PASSED")
