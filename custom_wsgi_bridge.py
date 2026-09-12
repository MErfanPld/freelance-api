import asyncio


def make_wsgi_app(asgi_app):
    def application(environ, start_response):
        headers = [
            (k[5:].lower().replace("_", "-").encode(), v.encode())
            for k, v in environ.items()
            if k.startswith("HTTP_")
        ]
        if environ.get("CONTENT_TYPE"):
            headers.append((b"content-type", environ["CONTENT_TYPE"].encode()))

        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": environ["REQUEST_METHOD"],
            "path": environ.get("PATH_INFO", ""),
            "raw_path": environ.get("PATH_INFO", "").encode(),
            "query_string": environ.get("QUERY_STRING", "").encode(),
            "headers": headers,
            "server": (environ.get("SERVER_NAME", ""), int(environ.get("SERVER_PORT") or 0)),
            "client": (environ.get("REMOTE_ADDR", ""), 0),
        }

        content_length = int(environ.get("CONTENT_LENGTH") or 0)
        body = environ["wsgi.input"].read(content_length) if content_length else b""

        result = {"status": 500, "headers": [], "body": b""}

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message):
            if message["type"] == "http.response.start":
                result["status"] = message["status"]
                result["headers"] = message["headers"]
            elif message["type"] == "http.response.body":
                result["body"] += message.get("body", b"")

        asyncio.run(asgi_app(scope, receive, send))

        status_line = f"{result['status']} OK"
        resp_headers = [(k.decode(), v.decode()) for k, v in result["headers"]]
        start_response(status_line, resp_headers)
        return [result["body"]]

    return application
