import csv
import io
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import require_owner, require_barista

router = APIRouter()


@router.get("/cafes/join/{code}", response_model=schemas.PublicCafeResponse)
def get_cafe_by_participant_code(code: str, db: Session = Depends(get_db)):
    cafe = db.query(models.Cafe).filter(models.Cafe.participant_code == code).first()
    if not cafe:
        raise HTTPException(status_code=404, detail="Cafe not found — check your participant link")
    return cafe


@router.get("/cafes/host-join/{code}", response_model=schemas.CafeResponse)
def get_cafe_by_host_code(code: str, db: Session = Depends(get_db)):
    cafe = db.query(models.Cafe).filter(models.Cafe.join_code == code).first()
    if not cafe:
        raise HTTPException(status_code=404, detail="Cafe not found — check your host code")
    return cafe


@router.get("/cafes/{cafe_id}", response_model=schemas.CafeResponse)
def get_cafe(cafe_id: int, db: Session = Depends(get_db)):
    cafe = db.query(models.Cafe).filter(models.Cafe.id == cafe_id).first()
    if not cafe:
        raise HTTPException(status_code=404, detail="Cafe not found")
    return cafe


@router.get("/cafes/{cafe_id}/slots", response_model=list[schemas.SlotResponse])
def get_slots(cafe_id: int, db: Session = Depends(get_db)):
    """Public endpoint — customer email omitted from response."""
    cafe = db.query(models.Cafe).filter(models.Cafe.id == cafe_id).first()
    if not cafe:
        raise HTTPException(status_code=404, detail="Cafe not found")
    return db.query(models.Slot).filter(models.Slot.cafe_id == cafe_id).all()


@router.get("/cafes/{cafe_id}/host-slots", response_model=list[schemas.SlotResponseFull])
def get_slots_for_host(
    cafe_id: int,
    user: dict = Depends(require_barista),
    db: Session = Depends(get_db),
):
    """Authenticated endpoint for hosts/owners — includes customer email."""
    cafe = db.query(models.Cafe).filter(models.Cafe.id == cafe_id).first()
    if not cafe:
        raise HTTPException(status_code=404, detail="Cafe not found")
    # Owners must own this cafe; baristas must belong to it
    if user.get("role") == "owner":
        if cafe.owner_id != int(user["sub"]):
            raise HTTPException(status_code=403, detail="Not authorized")
    else:
        barista = db.query(models.Barista).filter(
            models.Barista.id == int(user["sub"]),
            models.Barista.cafe_id == cafe_id,
        ).first()
        if not barista:
            raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(models.Slot).filter(models.Slot.cafe_id == cafe_id).all()


@router.get("/cafes/{cafe_id}/baristas", response_model=list[schemas.BaristaResponse])
def get_cafe_baristas(cafe_id: int, db: Session = Depends(get_db)):
    cafe = db.query(models.Cafe).filter(models.Cafe.id == cafe_id).first()
    if not cafe:
        raise HTTPException(status_code=404, detail="Cafe not found")
    return db.query(models.Barista).filter(models.Barista.cafe_id == cafe_id).all()


@router.get("/cafes/{cafe_id}/customers", response_model=list[schemas.CustomerResponse])
def get_cafe_customers(
    cafe_id: int,
    owner: dict = Depends(require_owner),
    db: Session = Depends(get_db),
):
    cafe = db.query(models.Cafe).filter(
        models.Cafe.id == cafe_id,
        models.Cafe.owner_id == int(owner["sub"]),
    ).first()
    if not cafe:
        raise HTTPException(status_code=404, detail="Cafe not found or not authorized")
    return db.query(models.Customer).filter(models.Customer.cafe_id == cafe_id).all()


@router.get("/cafes/{cafe_id}/export")
def export_cafe_data(
    cafe_id: int,
    owner: dict = Depends(require_owner),
    db: Session = Depends(get_db),
):
    cafe = db.query(models.Cafe).filter(
        models.Cafe.id == cafe_id,
        models.Cafe.owner_id == int(owner["sub"]),
    ).first()
    if not cafe:
        raise HTTPException(status_code=404, detail="Cafe not found or not authorized")

    slots = db.query(models.Slot).filter(models.Slot.cafe_id == cafe_id).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Section 1: Bookings
    writer.writerow(["=== BOOKINGS ==="])
    writer.writerow(["Date", "Start Time", "End Time", "Location", "Status", "Virtual Meeting Link",
                     "Host Name", "Host Email", "Participant Name", "Participant Email"])
    for slot in sorted(slots, key=lambda s: s.start_time):
        writer.writerow([
            slot.start_time.strftime("%Y-%m-%d"),
            slot.start_time.strftime("%H:%M"),
            slot.end_time.strftime("%H:%M"),
            slot.location or "",
            slot.status,
            slot.meet_link or "",
            slot.barista.name if slot.barista else "",
            slot.barista.email if slot.barista else "",
            slot.customer.name if slot.customer else "",
            slot.customer.email if slot.customer else "",
        ])

    writer.writerow([])

    # Section 2: Hosts
    writer.writerow(["=== HOSTS ==="])
    writer.writerow(["Name", "Email", "Phone", "Bio"])
    baristas = db.query(models.Barista).filter(models.Barista.cafe_id == cafe_id).all()
    for b in baristas:
        writer.writerow([b.name, b.email, b.phone_number or "", b.bio or ""])

    writer.writerow([])

    # Section 3: Participants
    writer.writerow(["=== PARTICIPANTS ==="])
    writer.writerow(["Name", "Email"])
    customers = db.query(models.Customer).filter(models.Customer.cafe_id == cafe_id).all()
    for c in customers:
        writer.writerow([c.name, c.email])

    output.seek(0)
    filename = f"{cafe.name.replace(' ', '_')}_{cafe.start_date}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/cafes", response_model=schemas.CafeResponse)
def create_cafe(
    cafe: schemas.CafeCreate,
    owner: dict = Depends(require_owner),
    db: Session = Depends(get_db),
):
    if cafe.end_date < cafe.start_date:
        raise HTTPException(status_code=400, detail="End date must be on or after start date")
    if cafe.start_date < date.today():
        raise HTTPException(status_code=400, detail="Start date cannot be in the past")

    owner_id = int(owner["sub"])
    db_owner = db.query(models.Owner).filter(models.Owner.id == owner_id).first()
    if not db_owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    db_cafe = models.Cafe(
        name=cafe.name,
        start_date=cafe.start_date,
        end_date=cafe.end_date,
        owner_id=owner_id,
        one_slot=cafe.one_slot,
        description=cafe.description or None,
    )
    db.add(db_cafe)
    db.commit()
    db.refresh(db_cafe)
    return db_cafe


@router.put("/cafes/{cafe_id}", response_model=schemas.CafeResponse)
def update_cafe(
    cafe_id: int,
    updates: schemas.CafeUpdate,
    owner: dict = Depends(require_owner),
    db: Session = Depends(get_db),
):
    cafe = db.query(models.Cafe).filter(
        models.Cafe.id == cafe_id,
        models.Cafe.owner_id == int(owner["sub"]),
    ).first()
    if not cafe:
        raise HTTPException(status_code=404, detail="Cafe not found or not authorized")

    if updates.name is not None:
        cafe.name = updates.name
    if updates.start_date is not None:
        cafe.start_date = updates.start_date
    if updates.end_date is not None:
        cafe.end_date = updates.end_date
    if updates.one_slot is not None:
        cafe.one_slot = updates.one_slot
    if updates.description is not None:
        cafe.description = updates.description or None

    if cafe.end_date < cafe.start_date:
        raise HTTPException(status_code=400, detail="End date must be on or after start date")

    db.commit()
    db.refresh(cafe)
    return cafe
