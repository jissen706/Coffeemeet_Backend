import os
import base64
from datetime import timezone

BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
EMAIL_ADDRESS  = os.environ.get("EMAIL_ADDRESS", "")
FRONTEND_URL   = os.environ.get("FRONTEND_URL", "https://coffeemeet-frontend.vercel.app")


def _build_ics(start_time, end_time, location, meet_link, host_name, host_email) -> str:
    def fmt(dt):
        utc = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
        return utc.strftime("%Y%m%dT%H%M%SZ")

    description = f"Coffee chat with {host_name}"
    if meet_link:
        description += f"\\nMeet link: {meet_link}"

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//CoffeeMeet//EN",
        "METHOD:REQUEST",
        "BEGIN:VEVENT",
        f"DTSTART:{fmt(start_time)}",
        f"DTEND:{fmt(end_time)}",
        f"SUMMARY:Coffee Chat with {host_name}",
        f"DESCRIPTION:{description}",
        f"LOCATION:{location or ''}",
        f"ORGANIZER:mailto:{EMAIL_ADDRESS}",
        "STATUS:CONFIRMED",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    if host_email:
        lines.insert(-2, f"ATTENDEE:mailto:{host_email}")
    return "\r\n".join(lines)


def _slot_table(date_str, start_str, end_str, location, host_name, meet_link, notes=None) -> str:
    meet_row = ""
    if meet_link:
        meet_row = f"""
              <tr>
                <td style="padding:8px 0;color:#888;font-size:14px;">Meeting</td>
                <td style="padding:8px 0;font-size:14px;">
                  <a href="{meet_link}" style="color:#c8773a;">Join virtual meeting ↗</a>
                </td>
              </tr>"""
    notes_row = ""
    if notes:
        notes_row = f"""
              <tr>
                <td style="padding:8px 0;color:#888;font-size:14px;vertical-align:top;">Notes</td>
                <td style="padding:8px 0;font-size:14px;color:#3b1f0f;line-height:1.5;">{notes}</td>
              </tr>"""
    return f"""
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
              {meet_row}
              {notes_row}
            </table>"""


def _cancel_link_html(participant_code: str) -> str:
    url = f"{FRONTEND_URL}/booking/{participant_code}"
    return f"""
            <div style="text-align:center;margin-top:28px;">
              <a href="{url}"
                 style="display:inline-block;padding:11px 28px;background:#c8773a;color:#fff;
                        border-radius:8px;font-size:14px;font-weight:600;text-decoration:none;">
                Manage my booking ↗
              </a>
              <p style="margin:10px 0 0;font-size:12px;color:#bbb;">
                View details or cancel your booking.
              </p>
            </div>"""


def _email_wrapper(header_label: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f0eb;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f0eb;padding:40px 0;">
    <tr><td align="center">
      <table width="520" cellpadding="0" cellspacing="0"
             style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
        <tr>
          <td style="background:#3b1f0f;padding:32px 40px;text-align:center;">
            <div style="font-size:32px;">☕</div>
            <div style="color:#f5e6d3;font-size:22px;font-weight:700;margin-top:8px;">CoffeeMeet</div>
            <div style="color:#c8a882;font-size:13px;margin-top:4px;">{header_label}</div>
          </td>
        </tr>
        <tr><td style="padding:36px 40px;">{body_html}</td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _build_html(customer_name, host_name, start_time, end_time, location, meet_link, notes=None, participant_code="") -> str:
    date_str  = start_time.strftime("%A, %B %-d, %Y")
    start_str = start_time.strftime("%-I:%M %p")
    end_str   = end_time.strftime("%-I:%M %p")
    location  = location or "TBD"
    body = f"""
            <p style="margin:0 0 8px;font-size:16px;color:#3b1f0f;">Hi {customer_name},</p>
            <p style="margin:0 0 28px;font-size:15px;color:#555;line-height:1.6;">
              Your coffee chat with <strong style="color:#3b1f0f;">{host_name}</strong> is confirmed.
              A calendar invite is attached — add it to your calendar so you don't miss it.
            </p>
            {_slot_table(date_str, start_str, end_str, location, host_name, meet_link, notes)}
            {_cancel_link_html(participant_code) if participant_code else ""}
            <p style="margin:28px 0 0;font-size:13px;color:#aaa;text-align:center;">
              Sent by CoffeeMeet &middot; Add the .ics attachment to your calendar
            </p>"""
    return _email_wrapper("You're booked!", body)


def _build_cancellation_html(customer_name, host_name, start_time, end_time, participant_code="") -> str:
    date_str  = start_time.strftime("%A, %B %-d, %Y")
    start_str = start_time.strftime("%-I:%M %p")
    end_str   = end_time.strftime("%-I:%M %p")
    rebook_url = f"{FRONTEND_URL}/booking/{participant_code}" if participant_code else FRONTEND_URL
    body = f"""
            <p style="margin:0 0 8px;font-size:16px;color:#3b1f0f;">Hi {customer_name},</p>
            <p style="margin:0 0 24px;font-size:15px;color:#555;line-height:1.6;">
              Your coffee chat with <strong style="color:#3b1f0f;">{host_name}</strong> on
              <strong>{date_str}</strong> at <strong>{start_str} – {end_str}</strong> has been cancelled.
            </p>
            <div style="text-align:center;margin-top:8px;">
              <a href="{rebook_url}"
                 style="display:inline-block;padding:11px 28px;background:#c8773a;color:#fff;
                        border-radius:8px;font-size:14px;font-weight:600;text-decoration:none;">
                Book a new slot ↗
              </a>
            </div>
            <p style="margin:20px 0 0;font-size:13px;color:#aaa;text-align:center;">
              Sent by CoffeeMeet
            </p>"""
    return _email_wrapper("Booking cancelled", body)


def _build_update_html(customer_name, host_name, start_time, end_time, location, meet_link, notes=None, participant_code="") -> str:
    date_str  = start_time.strftime("%A, %B %-d, %Y")
    start_str = start_time.strftime("%-I:%M %p")
    end_str   = end_time.strftime("%-I:%M %p")
    location  = location or "TBD"
    body = f"""
            <p style="margin:0 0 8px;font-size:16px;color:#3b1f0f;">Hi {customer_name},</p>
            <p style="margin:0 0 28px;font-size:15px;color:#555;line-height:1.6;">
              Your upcoming coffee chat with <strong style="color:#3b1f0f;">{host_name}</strong>
              has been updated. Here are the latest details:
            </p>
            {_slot_table(date_str, start_str, end_str, location, host_name, meet_link, notes)}
            {_cancel_link_html(participant_code) if participant_code else ""}
            <p style="margin:28px 0 0;font-size:13px;color:#aaa;text-align:center;">
              Sent by CoffeeMeet
            </p>"""
    return _email_wrapper("Booking updated", body)


def _brevo_api():
    import sib_api_v3_sdk
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = BREVO_API_KEY
    return sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))


def _send(to_email: str, to_name: str, subject: str, html: str, attachment_ics: bytes = None):
    import sib_api_v3_sdk
    attachments = []
    if attachment_ics:
        attachments = [{"name": "invite.ics", "content": base64.b64encode(attachment_ics).decode()}]
    msg = sib_api_v3_sdk.SendSmtpEmail(
        sender={"name": "CoffeeMeet", "email": EMAIL_ADDRESS},
        to=[{"email": to_email, "name": to_name}],
        subject=subject,
        html_content=html,
        attachment=attachments or None,
    )
    response = _brevo_api().send_transac_email(msg)
    print(f"[email] Sent '{subject}' to {to_email} — messageId {response.message_id}")


def send_booking_confirmation(
    customer_name: str,
    customer_email: str,
    start_time,
    end_time,
    location: str,
    meet_link: str,
    host_name: str,
    host_email: str,
    notes: str = "",
    participant_code: str = "",
):
    if not BREVO_API_KEY or not EMAIL_ADDRESS:
        print("[email] Skipped — BREVO_API_KEY or EMAIL_ADDRESS not set")
        return
    try:
        ics = _build_ics(start_time, end_time, location, meet_link, host_name, host_email).encode()
        html = _build_html(customer_name, host_name, start_time, end_time, location, meet_link, notes or None, participant_code)
        _send(customer_email, customer_name, "Your coffee chat is confirmed ☕", html, ics)
    except Exception as e:
        print(f"[email] Failed to send to {customer_email}: {e}")


def send_cancellation_email(
    customer_name: str,
    customer_email: str,
    start_time,
    end_time,
    host_name: str,
    participant_code: str = "",
):
    if not BREVO_API_KEY or not EMAIL_ADDRESS:
        return
    try:
        html = _build_cancellation_html(customer_name, host_name, start_time, end_time, participant_code)
        _send(customer_email, customer_name, "Your coffee chat has been cancelled", html)
    except Exception as e:
        print(f"[email] Failed cancellation email to {customer_email}: {e}")


def send_update_email(
    customer_name: str,
    customer_email: str,
    start_time,
    end_time,
    location: str,
    meet_link: str,
    host_name: str,
    notes: str = "",
    participant_code: str = "",
):
    if not BREVO_API_KEY or not EMAIL_ADDRESS:
        return
    try:
        html = _build_update_html(customer_name, host_name, start_time, end_time, location, meet_link, notes or None, participant_code)
        _send(customer_email, customer_name, "Your coffee chat details have been updated ☕", html)
    except Exception as e:
        print(f"[email] Failed update email to {customer_email}: {e}")
