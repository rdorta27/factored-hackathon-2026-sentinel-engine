"""
GET /transactions

Cookie-session-scoped listing of the customer's transactions from the in-memory
Gold store.  Used by the demo/test application created via create_app().
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.session.models import Session
from app.session.router import require_session

router = APIRouter(tags=["transactions"])


@router.get("/transactions")
def list_transactions(request: Request, session: Session = Depends(require_session)) -> JSONResponse:
    # Reject any attempt to pass a customer_id query parameter.
    if "customer_id" in request.query_params:
        raise HTTPException(status_code=422, detail="customer_id is not an accepted parameter")

    gold = request.app.state.gold
    ref_date = request.app.state.reference_date
    rows = gold.list_for_customer(session.customer_id)
    transactions = [
        {
            "reference": row.reference,
            "date": row.date,
            "currency": row.currency,
            "amount": row.amount,
            "merchant": row.merchant,
        }
        for row in rows
    ]
    return JSONResponse(
        content={"as_of": ref_date.isoformat(), "transactions": transactions}
    )
