from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.session.models import Session
from app.session.router import require_session
from app.tools.gold import GoldTransactions

router = APIRouter(tags=["transactions"])


@router.get("/transactions")
def list_transactions(
    request: Request,
    session: Session = Depends(require_session),
) -> dict:
    if "customer_id" in request.query_params:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="customer_id is not accepted")
    gold: GoldTransactions = request.app.state.gold
    rows = gold.list_for_customer(session.customer_id)
    return {
        "as_of": request.app.state.reference_date.isoformat(),
        "transactions": [
            {
                "reference": row.reference,
                "amount": row.amount,
                "currency": row.currency,
                "merchant": row.merchant,
                "date": row.date,
                "status": row.status,
                "as_of": row.as_of,
            }
            for row in rows
        ],
    }
