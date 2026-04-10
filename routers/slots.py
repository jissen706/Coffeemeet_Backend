import threading
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import require_barista, get_optional_user
from email_service import send_booking_confirmation, send_cancellation_email, send_update_email

router = APIRouter()


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
    # Use SELECT FOR UPDATE to prevent double-booking race condition
    slot = db.query(models.Slot).filter(models.Slot.id == slot_id).with_for_update().first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    if slot.customer_id is not None:
        raise HTTPException(status_code=400, detail="Slot is already booked")

    customer = db.query(models.Customer).filter(models.Customer.id == booking.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    cafe = db.query(models.Cafe).filter(models.Cafe.id == slot.cafe_id).first()
    if cafe and cafe.one_slot:
        already_booked = db.query(models.Slot).filter(
            models.Slot.cafe_id == slot.cafe_id,
            models.Slot.customer_id == booking.customer_id,
            models.Slot.status == "booked",
        ).first()
        if already_booked:
            raise HTTPException(status_code=400, detail="You already have a booking in this cafe")

    slot.customer_id = booking.customer_id
    slot.status = "booked"
    db.commit()
    db.refresh(slot)

    # Snapshot all data needed for the email before the session closes
    cafe = db.query(models.Cafe).filter(models.Cafe.id == slot.cafe_id).first()
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
        "participant_code": cafe.participant_code if cafe else "",
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

    if slot.customer_id is None:
        raise HTTPException(status_code=400, detail="Slot is not booked")

    if user.get("role") == "owner":
        cafe = db.query(models.Cafe).filter(
            models.Cafe.id == slot.cafe_id,
            models.Cafe.owner_id == int(user["sub"]),
        ).first()
        if not cafe:
            raise HTTPException(status_code=403, detail="Not authorized")
    elif user.get("role") == "customer":
        if slot.customer_id != int(user["sub"]):
            raise HTTPException(status_code=403, detail="You can only unbook your own slot")
    elif user.get("role") == "barista":
        if slot.barista_id != int(user["sub"]):
            raise HTTPException(status_code=403, detail="You can only unbook slots you created")
    else:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Snapshot before clearing
    customer = db.query(models.Customer).filter(models.Customer.id == slot.customer_id).first()
    cafe = db.query(models.Cafe).filter(models.Cafe.id == slot.cafe_id).first()
    cancel_data = {
        "customer_name": customer.name if customer else "",
        "customer_email": customer.email if customer else "",
        "start_time": slot.start_time,
        "end_time": slot.end_time,
        "host_name": slot.barista.name if slot.barista else "",
        "participant_code": cafe.participant_code if cafe else "",
    }

    slot.customer_id = None
    slot.status = "open"
    slot.meet_link = None
    db.commit()
    db.refresh(slot)

    if cancel_data["customer_email"]:
        threading.Thread(
            target=send_cancellation_email,
            kwargs=cancel_data,
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

    # Notify booked participant of the update
    if slot.customer_id and slot.customer:
        cafe = db.query(models.Cafe).filter(models.Cafe.id == slot.cafe_id).first()
        update_data = {
            "customer_name": slot.customer.name,
            "customer_email": slot.customer.email,
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

    if slot.customer_id is None:
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
