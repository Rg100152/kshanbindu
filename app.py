"""
KshanBindu — Smart Appointment Booking & Reminder Studio.
Engineered by Raj Gautam • Jaunpur, Uttar Pradesh, India.
Tagline: Every Moment Scheduled, Every Reminder Delivered.

No phone numbers are stored, requested, or displayed anywhere in this project.
"""

from __future__ import annotations

import re
import secrets
import sqlite3
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

from flask import (
    Flask,
    Response,
    abort,
    jsonify,
    render_template,
    request,
    send_file,
)
from werkzeug.exceptions import BadRequest

try:
    from zoneinfo import ZoneInfo

    IST = ZoneInfo("Asia/Kolkata")
except Exception:  # pragma: no cover - fallback for very old Python builds
    IST = timezone(timedelta(hours=5, minutes=30))

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "instance"
DB_PATH = DATA_DIR / "kshanbindu.db"

OPEN_HOUR = 9 * 60   # 09:00 IST
CLOSE_HOUR = 18 * 60  # 18:00 IST
SLOT_STEP = 30       # minutes
MAX_DAYS_AHEAD = 90

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

app = Flask(__name__)
app.config.update(
    JSON_SORT_KEYS=False,
    MAX_CONTENT_LENGTH=64 * 1024,
)


# --------------------------------------------------------------------------- #
# Database helpers
# --------------------------------------------------------------------------- #
def get_db() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS event_types (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT    NOT NULL,
                duration      INTEGER NOT NULL DEFAULT 30,
                description   TEXT    NOT NULL DEFAULT '',
                accent        TEXT    NOT NULL DEFAULT '#4F46E5',
                created_at    TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS appointments (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type_id INTEGER NOT NULL,
                client_name   TEXT    NOT NULL,
                client_email  TEXT    NOT NULL,
                appointment_date TEXT NOT NULL,
                start_time    TEXT    NOT NULL,
                status        TEXT    NOT NULL DEFAULT 'pending',
                notes         TEXT    NOT NULL DEFAULT '',
                jitsi_link    TEXT    NOT NULL DEFAULT '',
                created_at    TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_type_id) REFERENCES event_types(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_appointments_date
                ON appointments(appointment_date, start_time);
            CREATE INDEX IF NOT EXISTS idx_appointments_status
                ON appointments(status);
            """
        )


init_db()


def row_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row is not None else None


def today_ist() -> date:
    return datetime.now(IST).date()


def parse_date(value: str) -> date:
    if not DATE_RE.match(value or ""):
        raise BadRequest("Date must be in YYYY-MM-DD format.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise BadRequest("Invalid calendar date.") from exc


def to_minutes(hhmm: str) -> int:
    hour, minute = (int(part) for part in hhmm.split(":"))
    return hour * 60 + minute


def to_hhmm(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def event_types() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM event_types ORDER BY id ASC"
        ).fetchall()
    return [row_dict(r) for r in rows]


def event_type_or_404(conn: sqlite3.Connection, event_type_id: int) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM event_types WHERE id = ?", (event_type_id,)
    ).fetchone()
    if row is None:
        abort(404, "Event type not found.")
    return row


def booked_entries(conn: sqlite3.Connection, day: str) -> list[dict]:
    """All bookings that occupy time on ``day`` (pending bookings block too)."""
    rows = conn.execute(
        """
        SELECT a.start_time, a.status, COALESCE(e.duration, 30) AS duration
        FROM appointments a
        LEFT JOIN event_types e ON e.id = a.event_type_id
        WHERE a.appointment_date = ? AND a.status IN ('approved', 'pending')
        """,
        (day,),
    ).fetchall()
    return [row_dict(r) for r in rows]


def build_slots(day: date, duration: int, bookings: list[dict]) -> list[dict]:
    """Generate conflict-free slots for a single date."""
    now = datetime.now(IST)
    is_today = day == now.date()
    is_past = day < now.date()
    is_sunday = day.weekday() == 6
    too_far = day > now.date() + timedelta(days=MAX_DAYS_AHEAD)

    slots: list[dict] = []
    start = OPEN_HOUR
    while start + duration <= CLOSE_HOUR:
        end = start + duration
        label = f"{to_hhmm(start)} – {to_hhmm(end)}"

        if is_past or too_far:
            status, reason = "unavailable", "Outside booking window"
        elif is_sunday:
            status, reason = "unavailable", "Sunday — studio closed"
        elif is_today and start <= now.hour * 60 + now.minute:
            status, reason = "unavailable", "Time has passed"
        else:
            clash = next(
                (
                    b for b in bookings
                    if to_minutes(b["start_time"]) < end
                    and to_minutes(b["start_time"]) + int(b["duration"]) > start
                ),
                None,
            )
            if clash:
                status = "booked"
                reason = "Booked — locked to prevent double-booking"
            else:
                status, reason = "available", "Open for booking"

        slots.append(
            {
                "time": to_hhmm(start),
                "end_time": to_hhmm(end),
                "label": label,
                "status": status,
                "reason": reason,
            }
        )
        start += SLOT_STEP
    return slots


def slots_for(day: date, event_type_id: int, conn: sqlite3.Connection) -> list[dict]:
    et = event_type_or_404(conn, event_type_id)
    return build_slots(day, int(et["duration"]), booked_entries(conn, day.isoformat()))


# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #
@app.route("/")
def index():
    return render_template(
        "index.html",
        event_types=event_types(),
        tagline="Every Moment Scheduled, Every Reminder Delivered.",
    )


@app.route("/dashboard")
def dashboard():
    now_iso = datetime.now(IST).isoformat()
    with get_db() as conn:
        upcoming = conn.execute(
            """
            SELECT COUNT(*) AS n FROM appointments
            WHERE status IN ('approved','pending')
              AND appointment_date || 'T' || start_time >= ?
            """,
            (now_iso[:16],),
        ).fetchone()["n"]
        pending = conn.execute(
            "SELECT COUNT(*) AS n FROM appointments WHERE status = 'pending'"
        ).fetchone()["n"]
        approved = conn.execute(
            "SELECT COUNT(*) AS n FROM appointments WHERE status = 'approved'"
        ).fetchone()["n"]
        total = conn.execute("SELECT COUNT(*) AS n FROM appointments").fetchone()["n"]
    stats = {
        "upcoming": upcoming,
        "pending": pending,
        "approved": approved,
        "total": total,
    }
    return render_template("dashboard.html", stats=stats, event_types=event_types())


# --------------------------------------------------------------------------- #
# JSON APIs
# --------------------------------------------------------------------------- #
@app.get("/api/event-types")
def api_event_types():
    return jsonify(event_types())


@app.post("/api/event-types")
def api_create_event_type():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()[:80]
    description = str(payload.get("description", "")).strip()[:240]
    accent = str(payload.get("accent", "#4F46E5")).strip()[:16]
    try:
        duration = int(payload.get("duration", 30))
    except (TypeError, ValueError):
        raise BadRequest("Duration must be a number of minutes.")

    if not name:
        raise BadRequest("Event type name is required.")
    if not 15 <= duration <= 480:
        raise BadRequest("Duration must be between 15 and 480 minutes.")
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", accent):
        accent = "#4F46E5"

    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO event_types (name, duration, description, accent) VALUES (?,?,?,?)",
            (name, duration, description, accent),
        )
        new_id = cur.lastrowid
        created = conn.execute(
            "SELECT * FROM event_types WHERE id = ?", (new_id,)
        ).fetchone()
    return jsonify(row_dict(created)), 201


@app.get("/api/availability")
def api_availability():
    """Dates in a month that still have at least one open slot."""
    year = int(request.args.get("year", today_ist().year))
    month = int(request.args.get("month", today_ist().month))
    if not 1 <= month <= 12 or not 2000 <= year <= 2200:
        raise BadRequest("Invalid month request.")

    event_type_id = int(request.args.get("event_type_id", 1))
    first = date(year, month, 1)
    last = date(year + (month == 12), (month % 12) + 1, 1) - timedelta(days=1)
    start = max(first, today_ist())
    end = min(last, today_ist() + timedelta(days=MAX_DAYS_AHEAD))

    available: list[str] = []
    with get_db() as conn:
        et = event_type_or_404(conn, event_type_id)
        duration = int(et["duration"])
        cursor = start
        while cursor <= end:
            if cursor.weekday() != 6:
                slots = build_slots(cursor, duration, booked_entries(conn, cursor.isoformat()))
                if any(s["status"] == "available" for s in slots):
                    available.append(cursor.isoformat())
            cursor += timedelta(days=1)
    return jsonify({"dates": available})


@app.get("/api/slots")
def api_slots():
    day = parse_date(request.args.get("date", ""))
    event_type_id = int(request.args.get("event_type_id", 1))
    with get_db() as conn:
        et = event_type_or_404(conn, event_type_id)
        slots = slots_for(day, event_type_id, conn)
    return jsonify(
        {
            "date": day.isoformat(),
            "pretty_date": day.strftime("%A, %d %B %Y"),
            "event_type": row_dict(et),
            "slots": slots,
        }
    )


@app.post("/api/book")
def api_book():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("client_name", "")).strip()[:100]
    email = str(payload.get("client_email", "")).strip()[:160].lower()
    notes = str(payload.get("notes", "")).strip()[:500]
    day = parse_date(str(payload.get("date", "")))
    start_time = str(payload.get("time", "")).strip()

    try:
        event_type_id = int(payload.get("event_type_id", 0))
    except (TypeError, ValueError):
        raise BadRequest("Choose an event type.")

    if not name or not EMAIL_RE.match(email):
        raise BadRequest("A valid name and email address are required.")
    if not TIME_RE.match(start_time):
        raise BadRequest("Invalid time slot.")

    conn = get_db()
    try:
        conn.execute("BEGIN IMMEDIATE")
        et = event_type_or_404(conn, event_type_id)
        duration = int(et["duration"])
        slot = next(
            (s for s in build_slots(day, duration, booked_entries(conn, day.isoformat()))
             if s["time"] == start_time),
            None,
        )
        if slot is None or slot["status"] != "available":
            raise BadRequest("That slot was just taken. Please choose another moment.")

        jitsi = "https://meet.jit.si/KshanBindu-" + secrets.token_hex(4)
        cur = conn.execute(
            """
            INSERT INTO appointments
                (event_type_id, client_name, client_email, appointment_date,
                 start_time, status, notes, jitsi_link)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (event_type_id, name, email, day.isoformat(), start_time,
             "pending", notes, jitsi),
        )
        booking_id = cur.lastrowid
        conn.commit()
        row = conn.execute(
            "SELECT * FROM appointments WHERE id = ?", (booking_id,)
        ).fetchone()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return jsonify(
        {
            "ok": True,
            "booking": row_dict(row),
            "event_type": row_dict(et),
            "end_time": slot["end_time"],
            "message": "Your moment is reserved. Raj will confirm it shortly.",
            "ics_url": f"/api/ics/{booking_id}",
        }
    ), 201


@app.get("/api/bookings")
def api_bookings():
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT a.*, e.name AS event_name, e.duration AS duration, e.accent
            FROM appointments a
            LEFT JOIN event_types e ON e.id = a.event_type_id
            ORDER BY a.appointment_date DESC, a.start_time DESC, a.id DESC
            LIMIT 100
            """
        ).fetchall()
    return jsonify([row_dict(r) for r in rows])


@app.post("/api/bookings/<int:booking_id>/<action>")
def api_booking_action(booking_id: int, action: str):
    if action not in {"approve", "cancel"}:
        abort(404)
    status = "approved" if action == "approve" else "cancelled"
    with get_db() as conn:
        cur = conn.execute(
            "UPDATE appointments SET status = ? WHERE id = ?", (status, booking_id)
        )
        if cur.rowcount == 0:
            abort(404, "Booking not found.")
    return jsonify({"ok": True, "id": booking_id, "status": status})


@app.get("/api/next")
def api_next():
    now = datetime.now(IST)
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT a.*, e.name AS event_name, e.duration AS duration
            FROM appointments a
            LEFT JOIN event_types e ON e.id = a.event_type_id
            WHERE a.status IN ('approved','pending')
              AND (a.appointment_date > ? OR
                   (a.appointment_date = ? AND a.start_time >= ?))
            ORDER BY a.appointment_date ASC, a.start_time ASC
            LIMIT 1
            """,
            (now.date().isoformat(), now.date().isoformat(), now.strftime("%H:%M")),
        ).fetchone()
    if row is None:
        return jsonify({"appointment": None})
    item = row_dict(row)
    start = datetime.combine(
        date.fromisoformat(item["appointment_date"]),
        time.fromisoformat(item["start_time"]),
        tzinfo=IST,
    )
    item["starts_at"] = start.isoformat()
    item["ends_at"] = (start + timedelta(minutes=int(item["duration"]))).isoformat()
    return jsonify({"appointment": item})


# --------------------------------------------------------------------------- #
# .ics calendar invite
# --------------------------------------------------------------------------- #
def _escape(value: object) -> str:
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r", "")
        .replace("\n", "\\n")
    )


def _fold(line: str) -> str:
    """Fold long ICS lines at 75 bytes per RFC 5545."""
    parts: list[str] = []
    current = ""
    for char in line:
        if len((current + char).encode("utf-8")) > 75:
            parts.append(current)
            current = " " + char
        else:
            current += char
    parts.append(current)
    return "\r\n".join(parts)


@app.get("/api/ics/<int:booking_id>")
def api_ics(booking_id: int):
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT a.*, e.name AS event_name, e.duration AS duration
            FROM appointments a
            LEFT JOIN event_types e ON e.id = a.event_type_id
            WHERE a.id = ?
            """,
            (booking_id,),
        ).fetchone()
    if row is None or row["status"] == "cancelled":
        abort(404, "Invite not found.")

    start_local = datetime.combine(
        date.fromisoformat(row["appointment_date"]),
        time.fromisoformat(row["start_time"]),
        tzinfo=IST,
    )
    end_local = start_local + timedelta(minutes=int(row["duration"]))
    stamp = lambda d: d.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    description = (
        f"KshanBindu appointment with {row['client_name']} ({row['client_email']}). "
        f"Host: Raj Gautam, Jaunpur, Uttar Pradesh, India. "
        f"Status: {row['status']}. Notes: {row['notes'] or '—'}"
    )
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//KshanBindu//Smart Appointment Scheduler//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:kshanbindu-{booking_id}@kshanbindu.local",
        f"DTSTAMP:{stamp(datetime.now(IST))}",
        f"DTSTART:{stamp(start_local)}",
        f"DTEND:{stamp(end_local)}",
        f"SUMMARY:{_escape(row['event_name'] + ' — Raj Gautam x ' + row['client_name'])}",
        f"DESCRIPTION:{_escape(description)}",
        f"LOCATION:{_escape(row['jitsi_link'])}",
        f"STATUS:{'CONFIRMED' if row['status'] == 'approved' else 'TENTATIVE'}",
        "BEGIN:VALARM",
        "TRIGGER:-PT30M",
        "ACTION:DISPLAY",
        f"DESCRIPTION:{_escape('KshanBindu reminder: ' + row['event_name'])}",
        "END:VALARM",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    content = "\r\n".join(_fold(line) for line in lines) + "\r\n"
    return Response(
        content,
        mimetype="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="kshanbindu-{booking_id}.ics"'
        },
    )


@app.get("/health")
def health():
    return jsonify({"status": "ok", "app": "KshanBindu", "timezone": "Asia/Kolkata"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
