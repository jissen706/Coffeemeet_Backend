import threading
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import require_barista, get_optional_user
from email_service import send_booking_confirmation, send_cancellation_email, send_update_email

router = APIRouter()


def _customer_already_booked_in_cafe(db: Session, cafe_id: int, customer_id: int) -> bool:
    """True if this customer holds a booking on any slot in this cafe."""
    return db.query(models.SlotBooking).join(
        models.Slot, models.Slot.id == models.SlotBooking.slot_id
    ).filter(
        models.Slot.cafe_id == cafe_id,
        models.SlotBooking.customer_id == customer_id,
    ).first() is not None


def _refresh_slot_status(slot: models.Slot, cafe: models.Cafe) -> None:
    """Set slot.status to 'booked' iff the slot is at capacity."""
    cap = cafe.max_participants if cafe else 1
    slot.status = "booked" if len(slot.bookings) >= cap else "open"


@router.post("/slots", response_model=schemas.SlotResponse)
def create_slot(
    slot: schemas.SlotCreate,
    user: dict = Depends(require_barista),
    db: Session = Depends(get_db),
):
    # Baristas may only create slots for themselves; owners can create for any barista
    if user.get("role") == "barista" and slot.barista_id != int(user["sub"]):
        raise HTTPException(status_code=403, detail="You can only create slots for yourself")

    if slot.start_time >= slot.end_time:
        raise HTTPException(status_code=400, detail="start_time must be before end_time")

    cafe = db.query(models.Cafe).filter(models.Cafe.id == slot.cafe_id).first()
    if not cafe:
        raise HTTPException(status_code=404, detail="Cafe not found")

    # Verify the barista actually belongs to this cafe
    barista = db.query(models.Barista).filter(
        models.Barista.id == slot.barista_id,
        models.Barista.cafe_id == slot.cafe_id,
    ).first()
    if not barista:
        raise HTTPException(status_code=400, detail="Barista does not belong to this cafe")

    cafe_start = datetime.combine(cafe.start_date, datetime.min.time())
    cafe_end = datetime.combine(cafe.end_date, datetime.max.time())
    if slot.start_time < cafe_start or slot.end_time > cafe_end:
        raise HTTPException(
            status_code=400,
            detail=f"Slot must fall within the cafe's dates ({cafe.start_date} – {cafe.end_date})",
        )

    db_slot = models.Slot(
        start_time=slot.start_time,
        end_time=slot.end_time,
        location=slot.location,
        meet_link=slot.meet_link,
        notes=slot.notes,
        cafe_id=slot.cafe_id,
        barista_id=slot.barista_id,
        status="open",
    )
    db.add(db_slot)
    db.commit()
    db.refresh(db_slot)
    return db_slot


@router.put("/slots/{slot_id}/book", response_model=schemas.SlotResponse)
def book_slot(slot_id: int, booking: schemas.SlotBook, db: Session = Depends(get_db)):
    # Use SELECT FOR UPDATE to prevent racing past capacity
    slot = db.query(models.Slot).filter(models.Slot.id == slot_id).with_for_update().first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    cafe = db.query(models.Cafe).filter(models.Cafe.id == slot.cafe_id).first()
    if not cafe:
        raise HTTPException(status_code=404, detail="Cafe not found")

    cap = cafe.max_participants or 1
    if len(slot.bookings) >= cap:
        raise HTTPException(status_code=400, detail="Slot is already booked")

    customer = db.query(models.Customer).filter(models.Customer.id == booking.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Reject if this customer is already on this slot
    if any(b.customer_id == booking.customer_id for b in slot.bookings):
        raise HTTPException(status_code=400, detail="You're already booked on this slot")

    if cafe.one_slot and _customer_already_booked_in_cafe(db, cafe.id, booking.customer_id):
        raise HTTPException(status_code=400, detail="You already have a booking in this cafe")

    db.add(models.SlotBooking(slot_id=slot.id, customer_id=booking.customer_id))
    db.flush()
    db.refresh(slot)
    _refresh_slot_status(slot, cafe)
    db.commit()
    db.refresh(slot)

    email_data = {
        "customer_name": customer.name,
        "customer_email": customer.email,
        "start_time": slot.start_time,
        "end_time": slot.end_time,
        "location": slot.location,
        "meet_link": slot.meet_link,
        "host_name": slot.barista.name if slot.barista else "Your Host",
        "host_email": slot.barista.email if slot.barista else "",
        "notes": slot.notes or "",
        "participant_code": cafe.participant_code or "",
    }
    threading.Thread(
        target=send_booking_confirmation,
        kwargs=email_data,
        daemon=True,
    ).start()

    return slot


@router.patch("/slots/{slot_id}/unbook", response_model=schemas.SlotResponse)
def unbook_slot(
    slot_id: int,
    user: dict = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    slot = db.query(models.Slot).filter(models.Slot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    if not slot.bookings:
        raise HTTPException(status_code=400, detail="Slot is not booked")

    cafe = db.query(models.Cafe).filter(models.Cafe.id == slot.cafe_id).first()

    # Determine which booking(s) we're cancelling.
    # Customers cancel only their own; hosts/owners cancel everyone on the slot.
    role = user.get("role")
    user_id = int(user["sub"])

    if role == "owner":
        if not cafe or cafe.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        bookings_to_cancel = list(slot.bookings)
    elif role == "customer":
        bookings_to_cancel = [b for b in slot.bookings if b.customer_id == user_id]
        if not bookings_to_cancel:
            raise HTTPException(status_code=403, detail="You can only unbook your own slot")
    elif role == "barista":
        if slot.barista_id != user_id:
            raise HTTPException(status_code=403, detail="You can only unbook slots you created")
        bookings_to_cancel = list(slot.bookings)
    else:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Snapshot emails before deletion
    cancel_targets = []
    for b in bookings_to_cancel:
        if b.customer:
            cancel_targets.append({
                "customer_name": b.customer.name,
                "customer_email": b.customer.email,
                "start_time": slot.start_time,
                "end_time": slot.end_time,
                "host_name": slot.barista.name if slot.barista else "",
                "participant_code": cafe.participant_code if cafe else "",
            })
        db.delete(b)

    db.flush()
    db.refresh(slot)

    # Clear meet link if everyone left
    if not slot.bookings:
        slot.meet_link = None

    _refresh_slot_status(slot, cafe)
    db.commit()
    db.refresh(slot)

    for data in cancel_targets:
        if data["customer_email"]:
            threading.Thread(
                target=send_cancellation_email,
                kwargs=data,
                daemon=True,
            ).start()

    return slot


@router.delete("/slots/{slot_id}", status_code=204)
def delete_slot(
    slot_id: int,
    user: dict = Depends(require_barista),
    db: Session = Depends(get_db),
):
    slot = db.query(models.Slot).filter(models.Slot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    if user.get("role") == "owner":
        cafe = db.query(models.Cafe).filter(
            models.Cafe.id == slot.cafe_id,
            models.Cafe.owner_id == int(user["sub"]),
        ).first()
        if not cafe:
            raise HTTPException(status_code=403, detail="Not authorized")
    else:
        if slot.barista_id != int(user["sub"]):
            raise HTTPException(status_code=403, detail="You can only delete your own slots")

    db.delete(slot)
    db.commit()


@router.patch("/slots/{slot_id}/edit", response_model=schemas.SlotResponse)
def edit_slot(
    slot_id: int,
    body: schemas.SlotEdit,
    user: dict = Depends(require_barista),
    db: Session = Depends(get_db),
):
    slot = db.query(models.Slot).filter(models.Slot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    if user.get("role") == "owner":
        cafe = db.query(models.Cafe).filter(
            models.Cafe.id == slot.cafe_id,
            models.Cafe.owner_id == int(user["sub"]),
        ).first()
        if not cafe:
            raise HTTPException(status_code=403, detail="Not authorized")
    else:
        if slot.barista_id != int(user["sub"]):
            raise HTTPException(status_code=403, detail="You can only edit your own slots")

    if body.location is not None:
        slot.location = body.location
    if body.meet_link is not None:
        slot.meet_link = body.meet_link
    if body.notes is not None:
        slot.notes = body.notes

    db.commit()
    db.refresh(slot)

    # Notify every booked participant of the update
    if slot.bookings:
        cafe = db.query(models.Cafe).filter(models.Cafe.id == slot.cafe_id).first()
        for b in slot.bookings:
            if not b.customer:
                continue
            update_data = {
                "customer_name": b.customer.name,
                "customer_email": b.customer.email,
                "start_time": slot.start_time,
                "end_time": slot.end_time,
                "location": slot.location,
                "meet_link": slot.meet_link,
                "host_name": slot.barista.name if slot.barista else "",
                "notes": slot.notes or "",
                "participant_code": cafe.participant_code if cafe else "",
            }
            threading.Thread(
                target=send_update_email,
                kwargs=update_data,
                daemon=True,
            ).start()

    return slot


@router.patch("/slots/{slot_id}/meet-link", response_model=schemas.SlotResponse)
def update_meet_link(
    slot_id: int,
    body: schemas.SlotMeetLink,
    user: dict = Depends(require_barista),
    db: Session = Depends(get_db),
):
    slot = db.query(models.Slot).filter(models.Slot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    if not slot.bookings:
        raise HTTPException(status_code=400, detail="Cannot add a meet link to an unbooked slot")

    # Owners can update any slot in their cafe; baristas only their own slots
    if user.get("role") == "owner":
        cafe = db.query(models.Cafe).filter(
            models.Cafe.id == slot.cafe_id,
            models.Cafe.owner_id == int(user["sub"]),
        ).first()
        if not cafe:
            raise HTTPException(status_code=403, detail="Not authorized")
    else:
        if slot.barista_id != int(user["sub"]):
            raise HTTPException(status_code=403, detail="You can only update meet links for your own slots")

    slot.meet_link = body.meet_link
    db.commit()
    db.refresh(slot)
    return slot
