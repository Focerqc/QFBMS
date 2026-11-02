#!/usr/bin/env python3
"""Progress dashboard. Reads the live PCB through KiCad's Python.

  python server.py
  http://localhost:5181
"""
import datetime
import json
import os
import subprocess
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 5181
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(TOOL_DIR, "..", ".."))
KICAD_PYTHON = r"C:\Program Files\KiCad\10.0\bin\python.exe"
AUDIT = os.path.join(TOOL_DIR, "audit.py")
DEFAULT_BOARD = "qfbms32.kicad_pcb"

_cache = {}


def safe_path(rel):
    rel = urllib.parse.unquote(rel or DEFAULT_BOARD).lstrip("/\\")
    full = os.path.normpath(os.path.join(REPO_ROOT, rel))
    if not full.startswith(REPO_ROOT):
        raise PermissionError("path outside repo")
    return full


def read_progress(full):
    mtime = os.path.getmtime(full)
    cached = _cache.get(full)
    if cached and cached[0] == mtime:
        data = cached[1]
    else:
        proc = subprocess.run(
            [KICAD_PYTHON, AUDIT, full],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
        )
        out = proc.stdout
        idx = out.find("@@JSON@@")
        if idx < 0:
            raise RuntimeError((proc.stderr or out or "audit failed")[-2000:])
        data = json.loads(out[idx + len("@@JSON@@"):])
        _cache[full] = (mtime, data)
    data = dict(data)
    data["path"] = os.path.relpath(full, REPO_ROOT).replace("\\", "/")
    data["mtime"] = datetime.datetime.fromtimestamp(mtime).strftime("%b %d, %I:%M %p")
    return data


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def send_json(self, obj, code=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, name):
        path = os.path.join(TOOL_DIR, name)
        if not os.path.isfile(path):
            self.send_error(404)
            return
        ext = os.path.splitext(name)[1]
        mime = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8"}.get(ext, "text/plain")
        with open(path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        try:
            if u.path == "/api/progress":
                return self.send_json(read_progress(safe_path(q.get("path", [DEFAULT_BOARD])[0])))
        except Exception as e:  # noqa: BLE001
            return self.send_json({"error": str(e)}, 500)
        if u.path in ("/", "/index.html"):
            return self.send_file("index.html")
        if u.path in ("/app.js", "/style.css"):
            return self.send_file(u.path.lstrip("/"))
        self.send_error(404)


def main():
    ThreadingHTTPServer.allow_reuse_address = True
    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Progress dashboard -> http://localhost:{PORT}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
