"""
Seed KshanBindu with sample event types and upcoming appointments.
Idempotent: run it as often as you like — existing data is never duplicated.

Usage:  python3 seed_appointments.py
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from app import IST, DB_PATH, get_db, init_db

EVENT_TYPES = [
    (
        "30-Min Tech Consultation",
        30,
        "A focused 30-minute call about your project, stack, and next steps.",
        "#4F46E5",
    ),
    (
        "Project Architecture Review",
        60,
        "Deep dive into system design, scalability, and deployment patterns.",
        "#0EA5E9",
    ),
    (
        "Cyber Security Audit",
        45,
        "Threat modelling, hardening checklist, and practical security fixes.",
        "#F59E0B",
    ),
]

SAMPLES = [
    # (event type id, days from today, HH:MM, client, email, status, notes)
    (1, 2, "09:30", "Aarav Sharma", "aarav.sharma@example.com", "approved", "Portfolio review and Flask deployment."),
    (2, 3, "11:00", "Neha Verma", "neha.verma@example.com", "pending", "Need a second opinion on microservice boundaries."),
    (1, 3, "15:30", "Rohit Kumar", "rohit.kumar@example.com", "approved", "API integration walkthrough."),
    (3, 5, "10:00", "Priya Singh", "priya.singh@example.com", "approved", "Audit of a small e-commerce backend."),
    (1, 7, "16:00", "Aditya Mishra", "aditya.mishra@example.com", "pending", "Linux CLI automation questions."),
    (2, 9, "13:00", "Sneha Patel", "sneha.patel@example.com", "approved", "Database indexing strategy."),
    (1, 12, "12:00", "Karan Yadav", "karan.yadav@example.com", "cancelled", "Rescheduled by client."),
]


def workday(offset: int) -> date:
    """Return a date ``offset`` days ahead, skipping Sundays (studio closed)."""
    day = datetime.now(IST).date() + timedelta(days=offset)
    while day.weekday() == 6:
        day += timedelta(days=1)
    return day


def main() -> None:
    init_db()
    conn = get_db()
    try:
        existing_types = conn.execute("SELECT COUNT(*) AS n FROM event_types").fetchone()["n"]
        existing_bookings = conn.execute("SELECT COUNT(*) AS n FROM appointments").fetchone()["n"]

        if existing_types == 0:
            conn.executemany(
                "INSERT INTO event_types (name, duration, description, accent) VALUES (?,?,?,?)",
                EVENT_TYPES,
            )
            print(f"✓ Inserted {len(EVENT_TYPES)} event types.")
        else:
            print(f"• Kept {existing_types} existing event types.")

        if existing_bookings == 0:
            count = 0
            for type_id, offset, start, client, email, status, notes in SAMPLES:
                jitsi = f"https://meet.jit.si/KshanBindu-Sample{count + 1}"
                conn.execute(
                    """
                    INSERT INTO appointments
                        (event_type_id, client_name, client_email, appointment_date,
                         start_time, status, notes, jitsi_link)
                    VALUES (?,?,?,?,?,?,?,?)
                    """,
                    (type_id, client, email, workday(offset).isoformat(),
                     start, status, notes, jitsi),
                )
                count += 1
            print(f"✓ Inserted {count} sample appointments.")
        else:
            print(f"• Kept {existing_bookings} existing appointments.")

        conn.commit()
        print(f"✓ Database ready at {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
