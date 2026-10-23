"""example-service — devsecops-os golden-path API skeleton.

Minimal skeleton for a new API service: /health for probes, and a sample
resource (items, in-memory) for the team to replace with real business
logic. All default security controls (no secrets in code, configuration
via the environment, running non-root in the container) come from the
template itself — see ../README.md.

Run locally:
  pip install -r requirements.txt
  PORT=8000 python app.py
"""

import os

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from config import settings

ITEMS = [{"id": 1, "name": "example-item", "status": "active"}]
_next_id = 2


async def health(request):
    return JSONResponse({"status": "ok", "service": settings.SERVICE_NAME})


async def list_items(request):
    return JSONResponse({"items": ITEMS, "count": len(ITEMS)})


async def create_item(request):
    global _next_id
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"detail": "invalid JSON body"}, status_code=400)
    name = str(body.get("name", "")).strip()
    if not name:
        return JSONResponse({"detail": "name is required"}, status_code=422)
    item = {"id": _next_id, "name": name[:200], "status": "active"}
    _next_id += 1
    ITEMS.append(item)
    return JSONResponse(item, status_code=201)


app = Starlette(
    routes=[
        Route("/health", health, methods=["GET"]),
        Route("/api/items", list_items, methods=["GET"]),
        Route("/api/items", create_item, methods=["POST"]),
    ]
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
