"""Background scheduler that sends reminder emails to participants whose
booked slot is starting within one of the cafe's configured offsets.

Polls the DB once a minute. For each (slot, customer, minutes_before) tuple
that is due now and hasn't been recorded in `sent_reminders`, fires the
email and inserts the dedup row. Single-process safe; multi-worker
deployments would need a lock or a job queue."""
import logging
import threading
import time
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError

from database import SessionLocal
import models
from email_service import send_reminder_email

_log = logging.getLogger("reminder-scheduler")

POLL_SECONDS = 60
# Window the scheduler considers "now" — we look slightly into the past so a
# reminder isn't missed when polling falls between two minute boundaries.
LOOKBACK_SECONDS = 120


def _parse_offsets(s: str | None) -> list[int]:
    if not s:
        return []
    out = set()
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            n = int(part)
            if n >= 0:
                out.add(n)
        except ValueError:
            continue
    return sorted(out)


def _tick():
    """One pass: find due reminders and send them."""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        # Slots starting in the future window we care about (up to the largest
        # configured offset across all cafes — but we don't know that without
        # querying first; cap at 7 days to bound the scan).
        future_horizon = now + timedelta(days=7)
        slots = (
            db.query(models.Slot)
            .filter(models.Slot.start_time >= now - timedelta(seconds=LOOKBACK_SECONDS))
            .filter(models.Slot.start_time <= future_horizon)
            .all()
        )

        for slot in slots:
            cafe = slot.cafe
            if not cafe:
                continue
            offsets = _parse_offsets(cafe.reminder_minutes_before)
            if not offsets:
                continue
            if not slot.bookings:
                continue

            for minutes in offsets:
                fire_at = slot.start_time - timedelta(minutes=minutes)
                # Eligible window: starting at fire_at, ending LOOKBACK_SECONDS
                # later. We don't fire arbitrarily late — sending a "60-minute
                # reminder" 50 minutes after the moment would mislead the
                # participant (the chat would be 10 minutes away).
                window_end = fire_at + timedelta(seconds=LOOKBACK_SECONDS)
                if not (fire_at <= now <= window_end):
                    continue
                # Belt-and-suspenders: never fire after the slot has started.
                if now >= slot.start_time:
                    continue

                for booking in list(slot.bookings):
                    if not booking.customer:
                        continue
                    # Dedup check
                    already = db.query(models.SentReminder).filter(
                        models.SentReminder.slot_id == slot.id,
                        models.SentReminder.customer_id == booking.customer_id,
                        models.SentReminder.minutes_before == minutes,
                    ).first()
                    if already:
                        continue

                    # Insert dedup row first; if another worker beat us the
                    # UNIQUE constraint will trip and we skip the send.
                    record = models.SentReminder(
                        slot_id=slot.id,
                        customer_id=booking.customer_id,
                        minutes_before=minutes,
                    )
                    db.add(record)
                    try:
                        db.commit()
                    except IntegrityError:
                        db.rollback()
                        continue

                    threading.Thread(
                        target=send_reminder_email,
                        kwargs={
                            "customer_name": booking.customer.name,
                            "customer_email": booking.customer.email,
                            "start_time": slot.start_time,
                            "end_time": slot.end_time,
                            "location": slot.location or "",
                            "meet_link": slot.meet_link or "",
                            "host_name": slot.barista.name if slot.barista else "",
                            "minutes_before": minutes,
                            "notes": slot.notes or "",
                            "participant_code": cafe.participant_code or "",
                        },
                        daemon=True,
                    ).start()
    finally:
        db.close()


def _loop():
    while True:
        try:
            _tick()
        except Exception as e:
            _log.exception("reminder tick failed: %s", e)
        time.sleep(POLL_SECONDS)


_started = False


def start_scheduler():
    """Idempotent — safe to call multiple times in dev reload."""
    global _started
    if _started:
        return
    _started = True
    t = threading.Thread(target=_loop, daemon=True, name="reminder-scheduler")
    t.start()
    _log.info("reminder scheduler started (poll every %ds)", POLL_SECONDS)
