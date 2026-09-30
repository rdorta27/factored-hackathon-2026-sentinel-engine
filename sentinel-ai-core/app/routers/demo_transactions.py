"""
GET /transactions
GET /api/v1/transactions  (compatibility alias for the sentinel-login frontend)

Cookie-session-scoped listing of the customer's transactions from the in-memory
Gold store.  Used by the demo/test application created via create_app().

Field-name conventions exposed in the response body follow the sentinel-login
frontend contract:
  - "reference"   (Gold: transaction_id)
  - "merchant"    (Gold: merchant_name)
  - "referenceDate" is included alongside "as_of" so app.js can read the
    cutoff date with either key.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.session.models import Session
from app.session.router import require_session
from app.tools.gold import to_candidate

router = APIRouter(tags=["transactions"])


def _build_response(request: Request, session: Session) -> JSONResponse:
    """Build the transaction listing response shared by both route paths."""
    if "customer_id" in request.query_params:
        raise HTTPException(status_code=422, detail="customer_id is not an accepted parameter")

    gold = request.app.state.gold
    ref_date = request.app.state.reference_date
    ref_iso = ref_date.isoformat()
    rows = gold.list_for_customer(session.customer_id)
    transactions = [
        {
            "reference": row.reference,              # sentinel-login key (Gold: transaction_id)
            "date": row.date,
            "currency": row.currency,
            "amount": row.amount,
            "merchant": row.merchant,                # sentinel-login key (Gold: merchant_name)
            # Map raw Gold status through the candidate adapter so "Refunded"
            # becomes "Reversed" — raw Gold vocabulary never reaches the API.
            "status": to_candidate(row).status.value,
        }
        for row in rows
    ]
    return JSONResponse(
        content={
            "as_of": ref_iso,            # original key (kept for backward compat)
            "referenceDate": ref_iso,    # sentinel-login frontend key
            "transactions": transactions,
        }
    )


@router.get("/transactions")
def list_transactions(
    request: Request,
    session: Session = Depends(require_session),
) -> JSONResponse:
    return _build_response(request, session)


@router.get("/api/v1/transactions")
def list_transactions_v1(
    request: Request,
    session: Session = Depends(require_session),
) -> JSONResponse:
    """Compatibility alias — the sentinel-login app.js calls this path."""
    return _build_response(request, session)
