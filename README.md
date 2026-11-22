# AI-Assisted Examination Integrity Management System

An academic learning prototype for examination identity verification, attendance management, and invigilator review.

> **Project status:** Working academic prototype. Core authentication, role guards, records, enrollment UI, attendance rules, dashboards, and tests are implemented. Hardware fingerprint integration and production-grade facial recognition remain future adapters.

## Technology stack

- **Backend:** Python and Django
- **Frontend:** Django templates, HTML5, CSS3, and Vanilla JavaScript
- **Database:** SQLite for local academic development
- **Image processing:** OpenCV (planned)
- **Biometrics:** Simulated fingerprint workflow initially; compatible fingerprint hardware integration is a later phase
- **Version control:** Git and GitHub

No React, Node.js, Bootstrap, or frontend framework is part of the planned core stack.

## Project principles

1. Biometric results are decision-support signals, not proof of examination malpractice.
2. A failed or inconclusive check must be referred for human review.
3. An accessible manual identity-verification route must remain available.
4. The browser captures and submits evidence; trusted backend services perform verification.
5. Do not commit real student photographs, biometric samples/templates, credentials, local databases, or private records.
6. Use consenting volunteers and synthetic records during development.

## Planned capabilities

- Role-based administrator, invigilator, and student access
- Student and invigilator records
- Examination scheduling and student registration
- Biometric enrollment workflows
- Simulated fingerprint verification in the first prototype
- Facial enrollment and comparison using an appropriate recognition model
- Combined verification outcomes and manual review
- Attendance, audit history, and reports

## Repository layout

```text
.
├── config/                 # Django project configuration
├── integrity/              # Core domain app
│   ├── migrations/
│   ├── services/            # Biometric, verification, attendance services
│   └── tests/
├── templates/               # Django HTML templates by feature
├── static/
│   ├── css/                 # Feature-specific stylesheets
│   ├── js/                  # Vanilla JavaScript modules
│   └── images/              # Non-sensitive static assets
├── media/
│   └── student_photos/      # Local uploads; ignored by Git
├── docs/                    # Architecture, API contract, collaboration notes
├── .env.example
├── .gitignore
├── manage.py                # Added when Django project setup begins
└── requirements.txt
```

## Team responsibilities

### Samuel — backend

- Django configuration, data models, authentication, permissions, and server-side views/API
- Biometric service interfaces and verification logic
- Attendance, audit logging, validation, and backend tests
- Security and integration support

### Frontend developer — interface

- Django templates and page layouts
- Responsive HTML and CSS
- Vanilla JavaScript interactions and webcam capture
- API integration, validation feedback, loading states, and accessibility

### Shared work

Agree on model fields, URL names, request/response formats, permissions, and integration milestones before connecting modules. Coordinate changes to shared configuration and base templates.

## Development setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. The custom user model supports `admin`, `invigilator`, and `student` roles. Never place a password in source control.

Run validation with:

```powershell
python manage.py check
python manage.py test
```

## Prototype biometric limitations

The fingerprint workflow is deliberately a backend-controlled simulation and is labelled as such in the interface; a browser cannot read an arbitrary USB scanner. The face adapter validates images, detects one face with OpenCV, and compares a normalized face crop. This is an educational adapter, not a certified biometric identification system: it does not provide reliable liveness detection, anti-spoofing, or forensic identity proof. Mismatches and inconclusive results always remain manual-review cases.

The application should be used only with consenting volunteers and synthetic records. Keep `.env`, local databases, uploads, and biometric templates out of public repositories. Production deployment requires key management, encrypted template storage, retention/deletion controls, consent records, TLS, rate limiting, and an independently evaluated recognition model.

## Verification outcome policy

| Fingerprint | Face | System outcome |
|---|---|---|
| Match | Match | Eligible for verified status, subject to backend rules |
| Match | Mismatch | Manual review |
| Mismatch | Match | Manual review |
| Mismatch | Mismatch | Manual review |
| Unavailable / inconclusive | Any result | Manual review |

The system must not automatically accuse or penalize a student based on a biometric mismatch.

## Security and privacy

Biometric information is highly sensitive. Before implementing enrollment, define informed consent, purpose limitation, retention/deletion, access controls, encryption, and a manual alternative. Prefer protected templates over retaining raw biometric images or fingerprint data. Never use real biometric data in public repository commits.

## Collaboration workflow

- Use feature branches for individual tasks.
- Keep commits small and descriptive.
- Open pull requests for review before merging.
- Do not commit `.env`, `db.sqlite3`, uploaded media, virtual environments, or generated secrets.
- Document API contracts before frontend/backend integration.

See [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md), [docs/API_CONTRACT.md](docs/API_CONTRACT.md), and [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).







## How the project works

This is a Django web app for managing exam access, identity checks, attendance, and incidents. Users sign in with one of three roles: **administrator**, **invigilator**, or **student**. The role controls which pages they can access.

### 1. Student account creation and approval

1. A student opens the sign-in page and selects **Request access**.
2. On **Create your account**, they enter a username, email, password, admission number, name, course, and department.
3. The app creates a student account that is **inactive** and saves the student’s profile. It checks that the username and admission number are not already in use and that the passwords match.
4. The student sees a request-received page and must wait for approval.
5. An administrator opens **Account approvals** and approves the request. The app activates the account and records an audit entry.
6. The student can then sign in and reach their dashboard.

These steps are implemented in the registration form and views: [forms.py](integrity/forms.py) and [views.py](integrity/views.py).

**Administrator-created student accounts work differently:** the Students page lets an administrator create a student account with a temporary password. That path does not use the same inactive-account approval flow. The public registration form creates student accounts; it does not create invigilator accounts.

### 2. Sign-in and navigation

The site root redirects to **Sign in**. Django checks the credentials, and inactive accounts cannot sign in. Once signed in, users see navigation links based on their role. Page access is also checked on the server, so hiding a link alone is not the security control.

The shared navigation and sign-out form are in [base.html](templates/base.html). The route list is in [urls.py](integrity/urls.py).

## What each page does

| Page | Who can use it | Purpose |
|---|---|---|
| **Sign in** | Everyone | Sign in to an active account. Links to student access requests. |
| **Create your account** | Prospective students | Submit a student account request for administrator approval. |
| **Request received** | New student registrants | Confirms the request is awaiting approval. |
| **Overview / dashboard** | All signed-in users | Shows a role-specific landing page. Admins see counts, notifications, and upcoming exams; students see attendance and upcoming-exam counts plus an enrollment link. |
| **Account approvals** | Administrator | List pending student/invigilator accounts and approve them. The public registration page itself only creates student requests. |
| **Students** | Administrator | List student records and open the student registration form. |
| **Register student** | Administrator | Create a student record, including a username and temporary password. |
| **Examinations** | Administrator | List exams with code, title, date, venue, and status. |
| **Create examination** | Administrator | Add an exam with its schedule, course, venue, and status. |
| **Biometric enrollment** | Student or administrator | Enroll a student’s simulated fingerprint reference and capture a face image using the camera. |
| **Verification desk** | Administrator or invigilator | Select an active exam and student, capture a face image, and run the server-side biometric checks. |
| **Operations desk** | Administrator or invigilator | Review notifications and monitoring events, view room/seat information, and submit incidents for human follow-up. |
| **Attendance** | Administrator or invigilator | View recorded attendance entries. |
| **Reports** | Administrator or invigilator | View attendance totals and pending-review count; download attendance as CSV. |
| **Django Admin** | Staff with Django admin access | Manage underlying records such as rooms, seats, registrations, and other models. It is available at `/admin/`. |

The page templates are under [templates/](templates), and the page behavior is mainly handled by [views.py](integrity/views.py).

## Examination-day flow

1. An administrator creates an examination and manages student, room, seat, and exam-registration records.
2. A student enrolls their biometrics. The enrollment page requests camera access for the face capture.
3. An invigilator opens the Verification desk, selects the active exam and candidate, captures a face image, and submits it.
4. Django runs the fingerprint and face checks and saves a verification log.
5. A result of **verified** displays a success message. Any other result creates a notification requiring review.
6. An invigilator can review notifications and submit an incident from the Operations desk.

The intended system policy is that uncertain or mismatched biometric results lead to human review, not an automatic misconduct finding. The project’s overview of this policy is in [README.md](README.md) and [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Current prototype limitations to know

- Fingerprint enrollment and checking are **simulated**; the browser does not read a USB fingerprint scanner.
- The face feature detects a face and compares a simple image-derived representation. It is an educational prototype, not production-grade identity recognition or liveness detection.
- The verification view writes a verification log, but in the current implementation it does **not** call the attendance-recording service. So a successful verification does not automatically create an attendance row.
- The access-check and monitoring-event endpoints exist, but the Operations page does not currently provide a full live monitoring or exam-entry workflow.
- Room and seat data are viewed on Operations, with a note to create rooms in Django Admin.
- The Reports page is a small summary plus CSV export; it is not a full analytics dashboard.
- Enrollment and verification depend on the browser allowing camera access.

The project describes itself as a working academic prototype, with hardware fingerprint integration and production-grade facial recognition still future work, in [README.md](README.md).







