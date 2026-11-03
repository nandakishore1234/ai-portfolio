from fastapi import APIRouter, HTTPException

from app.mail import mail_configured, send_contact_email
from app.schemas import ContactRequest, ContactResponse

router = APIRouter()


@router.post("/contact", response_model=ContactResponse)
def contact(body: ContactRequest):
    if not mail_configured():
        raise HTTPException(
            status_code=503,
            detail="Email is not configured yet. Add RESEND_API_KEY or SMTP settings in backend/.env.",
        )
    try:
        send_contact_email(
            name=body.name,
            email=body.email,
            subject=body.subject,
            message=body.message,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not send the message: {exc}") from exc
    return ContactResponse(ok=True, detail="Message sent. I'll get back to you soon.")
