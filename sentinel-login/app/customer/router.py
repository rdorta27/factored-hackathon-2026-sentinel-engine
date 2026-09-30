"""Read-only customer data for the interface: transactions and demo context."""

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from app.auth.models import Session
from app.auth.roles import require_customer
from app.disputes.policy import reference_date
from app.gold.store import GoldTransactions, profile_for

router = APIRouter(prefix="/api/v1", tags=["customer"])


def get_gold(request: Request) -> GoldTransactions:
    return request.app.state.gold


@router.get("/transactions")
def list_transactions(
    request: Request, session: Session = Depends(require_customer)
) -> JSONResponse:
    """The session customer's charges. Isolation lives in the Gold seam."""
    rows = get_gold(request).list_for_customer(session.customer_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "transactions": [
                {
                    "reference": row.reference,
                    "amount": row.amount,
                    "currency": row.currency,
                    "merchant": row.merchant,
                    "date": row.date,
                    "status": row.status,
                }
                for row in rows
            ],
            "referenceDate": reference_date().isoformat(),
        },
    )


@router.get("/session/context")
def session_context(
    request: Request, session: Session = Depends(require_customer)
) -> JSONResponse:
    """Masked identity plus the country locale, so the UI can start in it."""
    profile = profile_for(session.customer_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "displayName": profile.display_name,
            "country": profile.country,
            "defaultLocale": profile.default_locale,
            "referenceDate": reference_date().isoformat(),
        },
    )
