import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import timezone

EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS", "")
EMAIL_APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD", "")


def _build_ics(slot, customer_name: str) -> str:
    """Generate a .ics calendar invite string."""
    def fmt(dt):
        utc = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
        return utc.strftime("%Y%m%dT%H%M%SZ")

    host_name = slot.barista.name if slot.barista else "Your Host"
    location = slot.location or ""
    meet_link = slot.meet_link or ""
    description = f"Coffee chat with {host_name}"
    if meet_link:
        description += f"\\nMeet link: {meet_link}"

    return "\r\n".join([
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//CoffeeMeet//EN",
        "METHOD:REQUEST",
        "BEGIN:VEVENT",
        f"DTSTART:{fmt(slot.start_time)}",
        f"DTEND:{fmt(slot.end_time)}",
        f"SUMMARY:Coffee Chat with {host_name}",
        f"DESCRIPTION:{description}",
        f"LOCATION:{location}",
        f"ORGANIZER:mailto:{EMAIL_ADDRESS}",
        f"ATTENDEE:mailto:{slot.barista.email}" if slot.barista else "",
        "STATUS:CONFIRMED",
        "END:VEVENT",
        "END:VCALENDAR",
    ])


def _build_html(slot, customer_name: str) -> str:
    host_name = slot.barista.name if slot.barista else "Your Host"
    date_str = slot.start_time.strftime("%A, %B %-d, %Y")
    start_str = slot.start_time.strftime("%-I:%M %p")
    end_str = slot.end_time.strftime("%-I:%M %p")
    location = slot.location or "TBD"
    meet_link_html = ""
    if slot.meet_link:
        meet_link_html = f"""
        <tr>
          <td style="padding:8px 0;color:#888;font-size:14px;">Meet Link</td>
          <td style="padding:8px 0;font-size:14px;">
            <a href="{slot.meet_link}" style="color:#c8773a;">{slot.meet_link}</a>
          </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f0eb;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f0eb;padding:40px 0;">
    <tr><td align="center">
      <table width="520" cellpadding="0" cellspacing="0"
             style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">

        <!-- Header -->
        <tr>
          <td style="background:#3b1f0f;padding:32px 40px;text-align:center;">
            <div style="font-size:32px;">☕</div>
            <div style="color:#f5e6d3;font-size:22px;font-weight:700;margin-top:8px;">CoffeeMeet</div>
            <div style="color:#c8a882;font-size:13px;margin-top:4px;">You're booked!</div>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:36px 40px;">
            <p style="margin:0 0 8px;font-size:16px;color:#3b1f0f;">Hi {customer_name},</p>
            <p style="margin:0 0 28px;font-size:15px;color:#555;line-height:1.6;">
              Your coffee chat with <strong style="color:#3b1f0f;">{host_name}</strong> is confirmed.
              A calendar invite is attached — add it to your calendar so you don't miss it.
            </p>

            <!-- Details card -->
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="background:#fdf8f4;border-radius:8px;border:1px solid #ede0d4;padding:20px 24px;">
              <tr>
                <td style="padding:8px 0;color:#888;font-size:14px;width:90px;">Date</td>
                <td style="padding:8px 0;font-size:14px;font-weight:600;color:#3b1f0f;">{date_str}</td>
              </tr>
              <tr>
                <td style="padding:8px 0;color:#888;font-size:14px;">Time</td>
                <td style="padding:8px 0;font-size:14px;font-weight:600;color:#3b1f0f;">{start_str} – {end_str}</td>
              </tr>
              <tr>
                <td style="padding:8px 0;color:#888;font-size:14px;">Location</td>
                <td style="padding:8px 0;font-size:14px;color:#3b1f0f;">{location}</td>
              </tr>
              <tr>
                <td style="padding:8px 0;color:#888;font-size:14px;">Host</td>
                <td style="padding:8px 0;font-size:14px;color:#3b1f0f;">{host_name}</td>
              </tr>
              {meet_link_html}
            </table>

            <p style="margin:28px 0 0;font-size:13px;color:#aaa;text-align:center;">
              Sent by CoffeeMeet &middot; Add the .ics attachment to your calendar
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def send_booking_confirmation(slot, customer_name: str, customer_email: str):
    """Send a booking confirmation email with .ics attachment. Silently no-ops if not configured."""
    if not EMAIL_ADDRESS or not EMAIL_APP_PASSWORD:
        return

    msg = MIMEMultipart("mixed")
    msg["From"] = f"CoffeeMeet <{EMAIL_ADDRESS}>"
    msg["To"] = customer_email
    msg["Subject"] = f"Your coffee chat is confirmed ☕"

    msg.attach(MIMEText(_build_html(slot, customer_name), "html"))

    ics_content = _build_ics(slot, customer_name)
    ics_part = MIMEBase("text", "calendar", method="REQUEST", name="invite.ics")
    ics_part.set_payload(ics_content.encode("utf-8"))
    encoders.encode_base64(ics_part)
    ics_part.add_header("Content-Disposition", "attachment", filename="invite.ics")
    msg.attach(ics_part)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, customer_email, msg.as_string())
        print(f"[email] Confirmation sent to {customer_email}")
    except Exception as e:
        print(f"[email] Failed to send to {customer_email}: {e}")
