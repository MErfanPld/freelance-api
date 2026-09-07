from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        async def send_with_headers(message: Message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))

                headers.extend(
                    [
                        (
                            b"x-content-type-options",
                            b"nosniff",
                        ),
                        (
                            b"x-frame-options",
                            b"DENY",
                        ),
                        (
                            b"referrer-policy",
                            b"strict-origin-when-cross-origin",
                        ),
                        (
                            b"permissions-policy",
                            b"camera=(), microphone=(), geolocation=()",
                        ),
                    ]
                )

                message["headers"] = headers

            await send(message)

        await self.app(scope, receive, send_with_headers)