"""
In-Memory ASGI Test Client for FastAPI.
Executes the full FastAPI ASGI pipeline without opening network ports or TCP sockets.
"""

import asyncio
import json
import urllib.parse
from typing import Any, Dict, Optional


class Response:
    def __init__(self, status_code: int, headers: list, body_bytes: bytes):
        self.status_code = status_code
        self.headers = {k.decode("latin1"): v.decode("latin1") for k, v in headers}
        self.content = body_bytes
        self.text = body_bytes.decode("utf-8", errors="replace")

    def json(self) -> Any:
        if not self.text.strip():
            return None
        return json.loads(self.text)

    def __repr__(self) -> str:
        return f"<Response [{self.status_code}]>"


class ASGIClient:
    def __init__(self, app):
        self.app = app

    async def _async_request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Any] = None,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Response:
        headers = headers or {}
        raw_headers = [[b"host", b"testserver"]]

        for k, v in headers.items():
            raw_headers.append([k.lower().encode("latin1"), str(v).encode("latin1")])

        body = b""
        if json_data is not None:
            body = json.dumps(json_data).encode("utf-8")
            raw_headers.append([b"content-type", b"application/json"])
        elif data is not None:
            if isinstance(data, dict):
                body = urllib.parse.urlencode(data).encode("ascii")
                raw_headers.append([b"content-type", b"application/x-www-form-urlencoded"])
            elif isinstance(data, (bytes, bytearray)):
                body = bytes(data)
            else:
                body = str(data).encode("utf-8")

        query_string = b""
        if "?" in path:
            path_part, query_part = path.split("?", 1)
            path = path_part
            query_string = query_part.encode("ascii")

        if params:
            encoded_params = urllib.parse.urlencode(params).encode("ascii")
            if query_string:
                query_string += b"&" + encoded_params
            else:
                query_string = encoded_params

        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": method.upper(),
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": query_string,
            "headers": raw_headers,
            "client": ("127.0.0.1", 50000),
            "server": ("testserver", 80),
            "scheme": "http",
        }

        status_code = [200]
        resp_headers = []
        resp_body = []

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(msg):
            if msg["type"] == "http.response.start":
                status_code[0] = msg["status"]
                resp_headers.extend(msg.get("headers", []))
            elif msg["type"] == "http.response.body":
                resp_body.append(msg.get("body", b""))

        await self.app(scope, receive, send)
        return Response(status_code[0], resp_headers, b"".join(resp_body))

    def request(self, method: str, path: str, **kwargs) -> Response:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(lambda: asyncio.run(self._async_request(method, path, **kwargs)))
                return future.result()
        else:
            return loop.run_until_complete(self._async_request(method, path, **kwargs))

    def get(self, path: str, **kwargs) -> Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> Response:
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs) -> Response:
        return self.request("DELETE", path, **kwargs)
