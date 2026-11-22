<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0F172A,4F46E5&height=190&section=header&text=KshanBindu&fontSize=62&fontColor=ffffff&animation=fadeIn&desc=Every%20Moment%20Scheduled%2C%20Every%20Reminder%20Delivered.&descAlignY=70&descAlign=50&fontAlignY=34" width="100%" alt="KshanBindu animated wave header" />

<br/>

<img src="static/assets/logo-kshanbindu.svg" width="340" alt="KshanBindu Scheduler logo" />

<br/>

<img src="static/assets/banner.jpg" width="100%" alt="KshanBindu hero banner" />

<br/>

<a href="https://readme-typing-svg.demolab.com">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=19&duration=3200&pause=1100&color=818CF8&center=true&vCenter=true&width=780&lines=Building%20KshanBindu%20with%20Python%20%26%20Flask;Every%20Moment%20Scheduled%2C%20Every%20Reminder%20Delivered.;Conflict-free%20slots%20%2B%20one-click%20.ics%20invites.;Zero%20phone%20numbers.%20Only%20clean%20booking%20flows.;Made%20in%20Jaunpur%2C%20Uttar%20Pradesh%20%E2%80%A2%20Raj%20Gautam" alt="KshanBindu typing animation" />
</a>

<br/>

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/Vanilla%20JS-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![Linux](https://img.shields.io/badge/Built%20on-Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![Video](https://img.shields.io/badge/Video-Jitsi%20Meet-1E3A8A?style=for-the-badge)
![Privacy](https://img.shields.io/badge/Contact-Email%20only-0F172A?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-4F46E5?style=for-the-badge)

**Smart Appointment Booking & Reminder Studio** · engineered by **Raj Gautam** · Jaunpur, Uttar Pradesh, India

*क्षणबिंदु — हर पल सूचीबद्ध, हर रिमाइंडर डिलीवर।*

</div>

---

## ✨ What is KshanBindu?

**KshanBindu** (क्षणबिंदु = "the precise point of a moment") is a full-stack appointment booking platform with a distinctive **Crisp Porcelain Daylight & Midnight Indigo 3-Pane Scheduler**. It replaces scattered DMs and double-booking chaos with one calm, fast workflow:

1. Pick a session type — *30-Min Tech Consultation*, *Project Architecture Review*, or *Cyber Security Audit*.
2. Pick a date on the custom vanilla-JS monthly calendar.
3. Lock an open slot — booked times are automatically disabled from SQLite.
4. Download a `.ics` invite that opens directly in Google Calendar, Apple Calendar or Outlook.
5. Host approves/cancels from a live dashboard with a countdown and browser reminder alerts.

> 🔒 **Zero phone numbers.** No phone field, no phone storage, no phone display — only email and a Jitsi meeting link.

---

## 🎬 Live Demo Preview

<div align="center">

<img src="static/assets/demo-preview.gif" alt="Animated KshanBindu demo — booking flow and host dashboard" width="92%" />

</div>

---

## 🖼️ Real UI Screenshots

| Booking Studio — `/` | Host Dashboard — `/dashboard` |
| :---: | :---: |
| ![KshanBindu 3-pane booking UI](static/assets/screenshot-booking.png) | ![KshanBindu host dashboard](static/assets/screenshot-dashboard.png) |
| Host + event card, monthly calendar, conflict-free slot picker, `.ics` download | Live countdown, audio/visual reminder toggle, approvals, event-type manager |

---

## 🧩 The 3-Pane Experience

| Pane | What it does |
| :--- | :--- |
| **🌙 Midnight Indigo Host Panel** | Host profile (Raj Gautam · Jaunpur, UP), event-type selector, duration badge, auto-generated Jitsi video-room badge. |
| **⚪ Porcelain Calendar** | Custom monthly grid with `‹ Prev` / `Next ›`, availability dots, Sunday closure, today marker — pure Vanilla JS, no date library. |
| **⚡ Smart Slot Studio** | Live open slots, **🔒 Booked** locks against double-booking, booking modal, one-click `.ics` invite, Jitsi link and confirmation. |

### Feature highlights

- **Conflict-free booking** — overlapping slots are blocked in a single SQLite write transaction (`BEGIN IMMEDIATE`).
- **Dynamic availability** — changing the event type recomputes open dates because longer sessions need longer free windows.
- **Real calendar invites** — RFC 5545 `.ics` with `VALARM` (30-minute before trigger) and Asia/Kolkata → UTC conversion.
- **Smart reminders** — live day/hour/min/sec countdown plus Web Audio chime + visual toast 5 minutes before the next appointment.
- **Host controls** — approve, cancel, filter bookings and create new event types from the dashboard.
- **Responsive** — 3 panes → 2 → 1 as the viewport narrows.
- **No external runtime dependencies** beyond Flask — no Node build step, no CDN JS.

---

## 🗺️ Data Flow Diagram

```mermaid
flowchart LR
    U["Visitor / Client"] -->|"event + date + slot"| B["Booking Studio (/)"]
    B -->|"GET /api/availability"| F["Flask App + REST APIs"]
    B -->|"GET /api/slots"| F
    B -->|"POST /api/book"| F
    F -->|"conflict check + insert"| DB[("SQLite<br/>event_types + appointments")]
    DB -->|"open / booked slots"| B
    F -->|"booking id"| ICS["GET /api/ics/&lt;id&gt;"]
    ICS -->|"download .ics"| CAL["Google / Apple / Outlook Calendar"]
    F -->|"meet.jit.si link"| J["Jitsi Video Room"]
    H["Host: Raj Gautam"] -->|"opens /dashboard"| D["Host Dashboard"]
    D -->|"GET /api/next"| F
    D -->|"approve / cancel / create event"| F
    F -->|"countdown payload"| D
    D -->|"Web Audio chime + toast"| H
```

---

## 🚀 Quick Start

> GitHub adds a **copy button** to every block below — pick your OS and paste.

### 🐧 Linux (Pop!_OS / Ubuntu / Debian)

```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git
git clone https://github.com/Rg100152/kshanbindu.git
cd kshanbindu
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 seed_appointments.py
python3 app.py
```

### 🍎 macOS (Terminal / Zsh)

```bash
xcode-select --install 2>/dev/null || true   # only if python3 is missing
git clone https://github.com/Rg100152/kshanbindu.git
cd kshanbindu
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 seed_appointments.py
python3 app.py
```

*Homebrew alternative:* `brew install python git` before the steps above.

### 🪟 Windows — PowerShell

```powershell
git clone https://github.com/Rg100152/kshanbindu.git
cd kshanbindu
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python seed_appointments.py
python app.py
```

If PowerShell blocks activation, allow it for this session only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 🪟 Windows — Command Prompt (cmd)

```bat
git clone https://github.com/Rg100152/kshanbindu.git
cd kshanbindu
py -m venv .venv
.\.venv\Scripts\activate.bat
pip install -r requirements.txt
python seed_appointments.py
python app.py
```

Then open:

| Page | URL |
| :--- | :--- |
| Booking Studio | <http://127.0.0.1:5000/> |
| Host Dashboard | <http://127.0.0.1:5000/dashboard> |
| Health check | <http://127.0.0.1:5000/health> |

> If port 5000 is busy, change the last line of `app.py` to `app.run(host="127.0.0.1", port=5001, debug=False)` and open `http://127.0.0.1:5001/`.

---

## 📁 Project Structure

```text
kshanbindu/
├── app.py                          # Flask routes, SQLite logic, .ics generator
├── seed_appointments.py            # Idempotent sample event types + appointments
├── requirements.txt                # Flask only
├── templates/
│   ├── base.html                   # Shared shell, nav and developer credits
│   ├── index.html                  # 3-pane booking studio
│   └── dashboard.html              # Host control room + countdown
├── static/
│   ├── css/kshanbindu.css          # Porcelain / Midnight Indigo design system
│   ├── js/scheduler.js             # Calendar, slots, modal, reminders, AJAX
│   └── assets/
│       ├── logo-kshanbindu.svg     # Custom calendar + moment dot + bell spark logo
│       ├── banner.jpg              # Hero banner
│       ├── avatar.jpg              # Host avatar
│       ├── screenshot-booking.png  # Real screenshot of /
│       ├── screenshot-dashboard.png# Real screenshot of /dashboard
│       └── demo-preview.gif        # Animated README preview
├── tools/make_demo_gif.py          # Regenerate the demo GIF from screenshots
├── .gitignore
└── README.md
```

---

## 🔌 API Reference

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `GET` | `/` | 3-pane booking studio |
| `GET` | `/dashboard` | Host dashboard |
| `GET` | `/api/event-types` | List event types |
| `POST` | `/api/event-types` | Create a custom event type |
| `GET` | `/api/availability?year=&month=&event_type_id=` | Dates with at least one open slot |
| `GET` | `/api/slots?date=YYYY-MM-DD&event_type_id=` | Slots with `available` / `booked` / `unavailable` status |
| `POST` | `/api/book` | Reserve a slot (conflict-checked transaction) |
| `GET` | `/api/bookings` | All bookings for the host queue |
| `POST` | `/api/bookings/<id>/approve` | Approve a request |
| `POST` | `/api/bookings/<id>/cancel` | Cancel a request |
| `GET` | `/api/next` | Next upcoming appointment + ISO start time |
| `GET` | `/api/ics/<id>` | Download the `.ics` calendar invite |
| `GET` | `/health` | JSON health probe |

Example booking payload:

```json
{
  "event_type_id": 1,
  "client_name": "Aarav Sharma",
  "client_email": "aarav@example.com",
  "notes": "Portfolio review and Flask deployment.",
  "date": "2026-11-24",
  "time": "09:30"
}
```

---

## 🧪 Regenerating Visual Assets

```bash
# 1. Start the app (in one terminal)
python3 seed_appointments.py && python3 app.py

# 2. Capture fresh headless screenshots (in another terminal)
google-chrome --headless=new --no-sandbox --disable-gpu --hide-scrollbars \
  --window-size=1440,1050 --virtual-time-budget=5000 \
  --screenshot=static/assets/screenshot-booking.png http://127.0.0.1:5000/
google-chrome --headless=new --no-sandbox --disable-gpu --hide-scrollbars \
  --window-size=1440,1050 --virtual-time-budget=5000 \
  --screenshot=static/assets/screenshot-dashboard.png http://127.0.0.1:5000/dashboard

# 3. Rebuild the animated GIF
pip install pillow
python3 tools/make_demo_gif.py
```

---

## 👨‍💻 Developer Profile Card

<table>
  <tr>
    <td align="center" width="180">
      <img src="static/assets/avatar.jpg" width="130" style="border-radius:22px" alt="Raj Gautam"><br/>
      <strong>Raj Gautam</strong><br/>
      <sub>Full-Stack Builder · Linux Enthusiast<br/>Ethical Hacking Learner</sub>
    </td>
    <td>
      <h3>क्षणबिंदु • KshanBindu</h3>
      <p>Building fast, lightweight and visually striking software from <strong>Jaunpur, Uttar Pradesh, India</strong>. Focus: Python, Flask, Go, CLI utilities and calm web engineering.</p>
      <p>
        <a href="mailto:graj13099@gmail.com">📧 graj13099@gmail.com</a><br/>
        <a href="https://instagram.com/linux.userraj" target="_blank" rel="noopener">📸 @linux.userraj</a><br/>
        <a href="https://github.com/Rg100152" target="_blank" rel="noopener">🐙 github.com/Rg100152</a>
      </p>
      <p><em>“Every Moment Scheduled, Every Reminder Delivered.”</em></p>
    </td>
  </tr>
</table>

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=4F46E5,0F172A&height=120&section=footer&text=KshanBindu%20%C2%B7%20Jaunpur%2C%20UP&fontSize=26&fontColor=ffffff&animation=twinkling" width="100%" alt="KshanBindu animated wave footer" />

<sub>Made with ♥ by Raj Gautam · No phone numbers, ever.</sub>

</div>
