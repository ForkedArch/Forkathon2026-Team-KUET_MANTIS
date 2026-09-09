"""
CampusShare KUET ("The Borrowed Charger") - Item Log & Location Server
Zero-dependency Python HTTP Server for Team KUET_MANTIS.
Forkathon 2026 Deliverable.
"""

import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

DATA_FILE = os.path.join(BASE_DIR, "kuet_data", "kuet_landmarks.json")
INDEX_HTML = os.path.join(BASE_DIR, "index.html")

# In-memory store initialized from kuet_landmarks.json
LIVE_ITEMS = []
CAMPUS_METADATA = {}
CAMPUS_ZONES = []

def init_data():
    global LIVE_ITEMS, CAMPUS_METADATA, CAMPUS_ZONES
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                CAMPUS_METADATA = data.get("campus", {})
                CAMPUS_ZONES = data.get("zones", [])
                raw_items = list(data.get("sample_active_items", []))
                
                dept_rolls = {
                    "CSE": "2207",
                    "EEE": "2103",
                    "ME": "2005",
                    "Civil": "2201",
                    "ECE": "2205",
                    "BME": "2315"
                }
                LIVE_ITEMS = []
                for idx, it in enumerate(raw_items):
                    item = dict(it)
                    dept_key = item.get("dept", "CSE").split()[0]
                    roll_prefix = dept_rolls.get(dept_key, "2207")
                    item.setdefault("user_id", f"student_kuet_{item.get('batch', '2023')}_{idx+1:03d}")
                    item.setdefault("roll", f"{roll_prefix}{idx+10:03d}")
                    item.setdefault("karma", float(item.get("trust_rating", 4.8)))
                    LIVE_ITEMS.append(item)
                print(f"[Init] Loaded {len(CAMPUS_ZONES)} campus landmarks and {len(LIVE_ITEMS)} active items with student credentials.")
        except Exception as e:
            print(f"[Init Error] Could not parse {DATA_FILE}: {e}")

init_data()

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class CampusRequestHandler(BaseHTTPRequestHandler):

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            if os.path.exists(INDEX_HTML):
                with open(INDEX_HTML, "rb") as f:
                    content = f.read()
                self._set_headers(200, "text/html; charset=utf-8")
                self.wfile.write(content)
            else:
                self._set_headers(404, "text/plain")
                self.wfile.write(b"index.html not found")
            return

        elif path == "/api/landmarks":
            response_data = {
                "success": True,
                "campus": CAMPUS_METADATA,
                "zones": CAMPUS_ZONES
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
            return

        elif path == "/api/items":
            category = query.get("category", [None])[0]
            item_type = query.get("type", [None])[0]
            search_query = query.get("q", [None])[0]

            filtered = LIVE_ITEMS
            if category and category.upper() != "ALL":
                filtered = [i for i in filtered if i.get("category", "").lower() == category.lower()]

            if item_type and item_type.upper() != "ALL":
                filtered = [i for i in filtered if i.get("type", "").lower() == item_type.lower()]

            if search_query:
                sq = search_query.lower()
                filtered = [
                    i for i in filtered
                    if sq in i.get("title", "").lower()
                    or sq in i.get("specs", "").lower()
                    or sq in i.get("lender_name", "").lower()
                    or sq in i.get("dept", "").lower()
                ]

            response_data = {
                "success": True,
                "count": len(filtered),
                "items": filtered
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
            return

        elif path == "/api/auth/current":
            response_data = {
                "success": True,
                "authenticated": True,
                "demo_mode": True,
                "user": {
                    "id": "student_kuet_2207001",
                    "name": "Tanvir Rahman",
                    "dept": "CSE",
                    "batch": "2022",
                    "roll": "2207001",
                    "karma": 4.9,
                    "trust_rating": 4.9,
                    "total_exchanges": 38,
                    "badge": "Verified Student",
                    "avatar": "TR"
                }
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
            return

        elif path.startswith("/kuet_data/"):
            rel_path = path.lstrip("/")
            target_file = os.path.join(BASE_DIR, rel_path)
            if os.path.exists(target_file) and os.path.isfile(target_file):
                with open(target_file, "rb") as f:
                    content = f.read()
                self._set_headers(200, "application/json; charset=utf-8")
                self.wfile.write(content)
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "File not found"}).encode("utf-8"))
            return

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_length)

        try:
            payload = json.loads(post_body.decode("utf-8")) if post_body else {}
        except Exception:
            payload = {}

        if path == "/api/items":
            item_type = payload.get("type", "lend")
            status = "beacon" if item_type == "borrow" else "available"
            item_id = f"item_{len(LIVE_ITEMS) + 101}"

            new_item = {
                "id": item_id,
                "user_id": payload.get("user_id", "student_kuet_2207001"),
                "type": item_type,
                "title": payload.get("title", "Untitled Item"),
                "category": payload.get("category", "Other"),
                "lng": float(payload.get("lng")) if payload.get("lng") is not None else None,
                "lat": float(payload.get("lat")) if payload.get("lat") is not None else None,
                "lender_name": payload.get("lender_name", "Tanvir Rahman"),
                "dept": payload.get("dept", "CSE"),
                "batch": payload.get("batch", "2022"),
                "roll": str(payload.get("roll", "2207001")),
                "karma": float(payload.get("karma", payload.get("trust_rating", 4.9))),
                "trust_rating": float(payload.get("trust_rating", payload.get("karma", 4.9))),
                "total_exchanges": int(payload.get("total_exchanges", 1)),
                "user_badge": payload.get("user_badge", "KUET Student"),
                "status": status,
                "image": payload.get("image", ""),
                "condition": payload.get("condition", "Good"),
                "specs": payload.get("specs", ""),
                "tags": payload.get("tags", ["#CampusShare", "#KUET"])
            }
            LIVE_ITEMS.append(new_item)
            self._set_headers(201)
            self.wfile.write(json.dumps({"success": True, "item": new_item}).encode("utf-8"))
            return

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "POST Endpoint not found"}).encode("utf-8"))

    def log_message(self, format, *args):
        sys.stderr.write(f"[Server] {self.address_string()} - {format%args}\n")


def run(port=8000):
    server_address = ("127.0.0.1", port)
    httpd = ThreadedHTTPServer(server_address, CampusRequestHandler)
    print("\n" + "=" * 65)
    print("  🚀 KUET ITEM LOG & LOCATION SERVER LAUNCHED")
    print(f"  🌐 Dashboard: http://127.0.0.1:{port}")
    print(f"  📦 Items API: http://127.0.0.1:{port}/api/items")
    print(f"  🏛️ Landmarks API: http://127.0.0.1:{port}/api/landmarks")
    print("=" * 65 + "\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()


if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run(port)
