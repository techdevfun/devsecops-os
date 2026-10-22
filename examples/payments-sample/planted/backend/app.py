"""payments-sample — minimal payments API, the demo workload for devsecops-os.

Endpoints:
  GET  /health                  liveness/readiness probe target
  GET  /api/payments            list sample payments (in-memory)
  GET  /api/payments/{id}       one payment
  POST /api/payments            record a payment (provider call is stubbed)

Run locally:
  pip install -r requirements.txt
  PORT=8000 python app.py
"""

import os

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route

from config import settings

# In-memory sample data. This is a gate-testing workload, not a real ledger.
PAYMENTS = [
    {
        "id": 1,
        "amount": 125000,
        "currency": "VND",
        "status": "settled",
        "description": "Invoice INV-1001",
    },
    {
        "id": 2,
        "amount": 4999,
        "currency": "USD",
        "status": "pending",
        "description": "Subscription renewal",
    },
]
_next_id = 3
SUPPORTED_CURRENCIES = ("USD", "EUR", "VND")


async def health(request):
    return JSONResponse({"status": "ok", "service": "payments-sample"})


async def list_payments(request):
    return JSONResponse({"payments": PAYMENTS, "count": len(PAYMENTS)})


async def get_payment(request):
    payment_id = request.path_params["payment_id"]
    for payment in PAYMENTS:
        if payment["id"] == payment_id:
            return JSONResponse(payment)
    return JSONResponse({"detail": "payment not found"}, status_code=404)


async def create_payment(request):
    global _next_id
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"detail": "invalid JSON body"}, status_code=400)

    amount = body.get("amount")
    currency = body.get("currency", "USD")
    if (
        not isinstance(amount, (int, float))
        or isinstance(amount, bool)
        or amount <= 0
    ):
        return JSONResponse(
            {"detail": "amount must be a positive number"}, status_code=422
        )
    if currency not in SUPPORTED_CURRENCIES:
        return JSONResponse({"detail": "unsupported currency"}, status_code=422)

    payment = {
        "id": _next_id,
        "amount": amount,
        "currency": currency,
        # The provider call is stubbed in this sample. Whether a provider
        # key is configured changes only the recorded status label — the
        # key value itself is never returned or logged.
        "status": (
            "authorized-stub" if settings.PAYMENT_PROVIDER_API_KEY else "recorded"
        ),
        "description": str(body.get("description", ""))[:200],
    }
    _next_id += 1
    PAYMENTS.append(payment)
    return JSONResponse(payment, status_code=201)


app = Starlette(
    routes=[
        Route("/health", health, methods=["GET"]),
        Route("/api/payments", list_payments, methods=["GET"]),
        Route("/api/payments", create_payment, methods=["POST"]),
        Route("/api/payments/{payment_id:int}", get_payment, methods=["GET"]),
    ],
    middleware=[
        # Local-demo convenience only: the static frontend is served from a
        # different localhost port during development. Behind the ALB the
        # frontend and API share an origin and this is unnecessary.
        Middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type"],
        )
    ],
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
