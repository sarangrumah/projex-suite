"""Redis-based rate limiter middleware using sliding window."""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# Paths exempt from rate limiting
_EXEMPT_PATHS = {"/health"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limit requests per IP using Redis sliding window counter."""

    def __init__(self, app, requests_per_minute: int = 1000) -> None:  # noqa: ANN001
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._redis = None

    async def _get_redis(self):  # noqa: ANN202
        """Lazy-init Redis connection."""
        if self._redis is None:
            try:
                from redis.asyncio import from_url

                from app.core.config import settings

                self._redis = from_url(settings.redis_url, decode_responses=True)
            except Exception:
                # Redis unavailable — allow requests through
                return None
        return self._redis

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in _EXEMPT_PATHS:
            return await call_next(request)

        redis = await self._get_redis()
        if redis is None:
            # If Redis is unavailable, allow the request (fail-open for dev)
            return await call_next(request)

        # Use client IP as rate limit key
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}"

        try:
            current = await redis.incr(key)
            if current == 1:
                await redis.expire(key, 60)

            if current > self.requests_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={
                        "data": None,
                        "meta": {},
                        "errors": [{"message": "Rate limit exceeded. Try again later."}],
                    },
                    headers={"Retry-After": "60"},
                )
        except Exception:
            # Redis error — fail open
            pass

        return await call_next(request)
