from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter()

@router.post("/slots", response_model=schemas.SlotResponse)
def create_slot(slot: schemas.SlotCreate, db: Session = Depends(get_db)):
    db_slot = models.Slot(
        start_time=slot.start_time,
        end_time=slot.end_time,
        location=slot.location,
        meet_link=slot.meet_link,
        cafe_id=slot.cafe_id,
        barista_id=slot.barista_id
    )

    db.add(db_slot)
    db.commit()
    db.refresh(db_slot)
    
    return db_slot

@router.put("/slots/{slot_id}/book", response_model=schemas.SlotResponse)
def book_slot(slot_id: int, booking: schemas.SlotBook, db: Session = Depends(get_db)):
    slot = db.query(models.Slot).filter(models.Slot.id == slot_id).first()

    if not slot:
        raise HTTPException(status_code=404, detail="Cafe not found")

    if slot.customer_id != None:
        raise HTTPException(status_code=400, detail="Slot booked")

    slot.customer_id = booking.customer_id
    db.commit()
    db.refresh(slot)

    return slot

@router.patch("/slots/{slot_id}/meet-link", response_model=schemas.SlotResponse)
def update_meet_link(slot_id: int, body: schemas.SlotMeetLink, db: Session = Depends(get_db)):
    slot = db.query(models.Slot).filter(models.Slot.id == slot_id).first()

    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    if slot.customer_id is None:
        raise HTTPException(status_code=400, detail="Cannot add a meet link to an unbooked slot")

    slot.meet_link = body.meet_link
    db.commit()
    db.refresh(slot)

    return slot