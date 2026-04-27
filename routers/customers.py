import threading
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import create_token, require_owner
from email_service import send_cancellation_email

router = APIRouter()


@router.post("/customers/{cafe_id}", response_model=schemas.TokenResponse)
def register_or_login_customer(
    cafe_id: int,
    customer: schemas.CustomerCreate,
    db: Session = Depends(get_db),
):
    cafe = db.query(models.Cafe).filter(models.Cafe.id == cafe_id).first()
    if not cafe:
        raise HTTPException(status_code=404, detail="Cafe not found")

    # If this email already belongs to a customer in this cafe, treat as login
    existing = db.query(models.Customer).filter(
        models.Customer.email == customer.email,
        models.Customer.cafe_id == cafe_id,
    ).first()

    if existing:
        db_customer = existing
    else:
        db_customer = models.Customer(name=customer.name, email=customer.email, cafe_id=cafe_id)
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)

    token = create_token({
        "sub": str(db_customer.id),
        "role": "customer",
        "name": db_customer.name,
        "cafe_id": db_customer.cafe_id,
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": db_customer.id,
            "name": db_customer.name,
            "role": "customer",
            "cafe_id": db_customer.cafe_id,
        },
    }


@router.post("/customers/lookup/{cafe_id}", response_model=schemas.TokenResponse)
def lookup_customer_by_email(
    cafe_id: int,
    body: schemas.CustomerLookup,
    db: Session = Depends(get_db),
):
    """Email-only login for returning participants (e.g. from email links)."""
    cafe = db.query(models.Cafe).filter(models.Cafe.id == cafe_id).first()
    if not cafe:
        raise HTTPException(status_code=404, detail="Cafe not found")

    customer = db.query(models.Customer).filter(
        models.Customer.email == body.email,
        models.Customer.cafe_id == cafe_id,
    ).first()

    if not customer:
        raise HTTPException(status_code=404, detail="No booking found for this email")

    token = create_token({
        "sub": str(customer.id),
        "role": "customer",
        "name": customer.name,
        "cafe_id": customer.cafe_id,
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": customer.id,
            "name": customer.name,
            "role": "customer",
            "cafe_id": customer.cafe_id,
        },
    }


@router.delete("/customers/{customer_id}", status_code=204)
def remove_customer(
    customer_id: int,
    owner: dict = Depends(require_owner),
    db: Session = Depends(get_db),
):
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    cafe = db.query(models.Cafe).filter(
        models.Cafe.id == customer.cafe_id,
        models.Cafe.owner_id == int(owner["sub"]),
    ).first()
    if not cafe:
        raise HTTPException(status_code=403, detail="Not authorized to modify this cafe")

    # Snapshot booking details for cancellation emails BEFORE we delete the
    # bookings — the customer relation goes with them.
    cancel_targets = []
    for b in customer.bookings:
        if not b.slot:
            continue
        cancel_targets.append({
            "customer_name": customer.name,
            "customer_email": customer.email,
            "start_time": b.slot.start_time,
            "end_time": b.slot.end_time,
            "host_name": b.slot.barista.name if b.slot.barista else "",
            "participant_code": cafe.participant_code or "",
        })

    # Unbook any slots this customer has booked — meet_link is preserved for the barista.
    # Cascade on the customer relationship would delete the bookings, but we also need to
    # roll the slot back to "open" if removing this customer drops it below capacity.
    affected_slot_ids = {b.slot_id for b in customer.bookings}
    for b in list(customer.bookings):
        db.delete(b)
    db.flush()

    if affected_slot_ids:
        slots = db.query(models.Slot).filter(models.Slot.id.in_(affected_slot_ids)).all()
        for slot in slots:
            cap = slot.cafe.max_participants if slot.cafe else 1
            slot.status = "booked" if len(slot.bookings) >= cap else "open"

    db.delete(customer)
    db.commit()

    for data in cancel_targets:
        if data["customer_email"]:
            threading.Thread(
                target=send_cancellation_email,
                kwargs=data,
                daemon=True,
            ).start()
