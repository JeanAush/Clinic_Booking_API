# Clinic Appointment Booking API

A production-oriented REST API for managing clinic appointments, built with **Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic, Docker, and pytest**.

The system supports doctor availability, appointment booking, cancellation, rescheduling, patient appointment history, authentication, role-based access control, and protection against concurrent double-booking.

---

## 1. System Overview

The system is designed for a small clinic with five doctors. Doctors have defined working hours and appointments are scheduled in 30-minute slots.

Patients can:

* View available appointment slots for a doctor on a specific date.
* Book an available appointment.
* Cancel an appointment.
* Reschedule an appointment.
* View their upcoming appointments.

The architecture is designed to support additional doctors, patients, and future clinic functionality without requiring significant changes to the core booking logic.

---

## 2. Technology Stack

| Technology     | Purpose                           |
| -------------- | --------------------------------- |
| Python         | Backend language                  |
| FastAPI        | REST API framework                |
| PostgreSQL     | Relational database               |
| SQLAlchemy     | ORM and database access           |
| Alembic        | Database migrations               |
| Pydantic       | Request/response validation       |
| pytest         | Automated testing                 |
| Docker         | Containerization                  |
| Docker Compose | Local multi-container development |
| GitHub Actions | CI/CD                             |
| Render         | Cloud deployment                  |
| JWT            | Authentication                    |
| bcrypt         | Password hashing                  |

---

# 3. Architecture

The application follows a modular layered architecture.

```text
app/
├── main.py
├── core/
│   ├── config.py
│   ├── dependencies.py
│   ├── exceptions.py
│   └── security.py
├── database/
│   ├── connection.py
│   └── base.py
├── models/
│   ├── doctor.py
│   ├── patient.py
│   ├── appointment.py
│   └── user.py
├── schemas/
│   ├── doctor.py
│   ├── patient.py
│   ├── appointment.py
│   └── auth.py
├── routers/
│   ├── doctors.py
│   ├── patients.py
│   ├── appointments.py
│   └── auth.py
├── services/
│   ├── availability.py
│   ├── appointments.py
│   ├── authentication.py
│   └── authorization.py
└── repositories/
    ├── doctors.py
    ├── patients.py
    ├── appointments.py
    └── users.py
```

### Architectural responsibilities

**Routers**

Handle HTTP requests, responses, authentication dependencies, and schema validation. Business logic is kept outside route handlers.

**Services**

Contain business rules such as appointment validation, availability calculation, booking, cancellation, rescheduling, authentication, and authorization.

**Repositories**

Encapsulate database queries and persistence operations.

**Models**

Represent database entities, relationships, indexes, and database-level constraints.

**Schemas**

Define API request and response structures using Pydantic.

**Core**

Contains application configuration, security functionality, shared dependencies, and application-level exceptions.

This separation keeps the system easier to test, maintain, and extend.

---

# 4. Data Model

The main entities are:

### Doctor

* `id`
* `name`
* `email`
* `working_start`
* `working_end`
* `created_at`

### Patient

* `id`
* `name`
* `email`
* `created_at`

### Appointment

* `id`
* `doctor_id`
* `patient_id`
* `start_time`
* `end_time`
* `status`
* `cancellation_reason`
* `created_at`
* `updated_at`

Appointment statuses currently include:

```text
BOOKED
CANCELLED
```

### User

Authentication accounts are separated from the existing doctor and patient profile records.

A user has:

* `id`
* `email`
* password hash
* role
* optional doctor profile
* optional patient profile

Supported roles:

```text
ADMIN
DOCTOR
PATIENT
```

This allows authentication and authorization to evolve independently from the existing clinic profile data.

---

# 5. Appointment Booking Flow

When a patient books an appointment, the API validates:

1. The doctor exists.
2. The patient exists.
3. The appointment is not in the past.
4. The appointment is at least one hour from the current time.
5. The start time falls on a valid 30-minute boundary.
6. The appointment duration is exactly 30 minutes.
7. The appointment falls completely within the doctor's working hours.
8. The requested slot is not already occupied.

The booking operation also relies on **database-level protection against overlapping appointments**.

A simple application-level check such as:

```text
check availability
        ↓
insert appointment
```

is not sufficient under concurrent requests because two requests could perform the check before either inserts its appointment.

The database therefore provides the final concurrency guarantee, while the application performs the normal business validation.

---

# 6. Availability

The availability endpoint generates the doctor's valid 30-minute working-hour slots for a requested date.

The calculation:

1. Retrieves the doctor's working hours.
2. Generates 30-minute slots.
3. Retrieves active appointments.
4. Removes occupied slots.
5. Removes slots that violate the one-hour booking rule.
6. Returns the remaining slots.

Cancelled appointments do not occupy a slot, so their time becomes available again.

---

# 7. Cancellation

Appointments can be cancelled through:

```http
PATCH /appointments/{id}/cancel
```

A cancellation:

* Changes the appointment status to `CANCELLED`.
* Stores the cancellation reason.
* Releases the appointment slot.
* Prevents the same appointment from being cancelled again.

Attempting to cancel an already cancelled appointment returns a conflict response.

---

# 8. Rescheduling

Appointments can be moved through:

```http
PATCH /appointments/{id}/reschedule
```

The new time is validated using the same booking rules as a new appointment.

The operation is transactional so that:

* The original appointment remains associated with the same record.
* The new slot becomes occupied.
* The original slot becomes available.
* A cancelled appointment cannot be rescheduled.

---

# 9. Authentication and Authorization

Authentication is implemented using JWT bearer tokens.

```http
POST /auth/login
```

Successful authentication returns a bearer token that can be supplied to protected endpoints.

Role-based access is centralized around:

```text
ADMIN
DOCTOR
PATIENT
```

### Admin

Administrators have full access to the system and can manage doctor and patient profiles.

### Doctor

Doctors can access and manage appointments assigned to them.

### Patient

Patients can book and access their own appointments.

Ownership checks are enforced in the service layer rather than relying only on route-level role checks.

Health checks and doctor availability remain publicly accessible.

---

# 10. API Endpoints

## Authentication

### Login

```http
POST /auth/login
```

Authenticates a user and returns a JWT bearer token.

---

## Doctors

### Create doctor

```http
POST /doctors
```

Admin access required.

### List doctors

```http
GET /doctors
```

Admin access required.

### Get doctor

```http
GET /doctors/{doctor_id}
```

Admin access required.

### Get availability

```http
GET /doctors/{doctor_id}/availability?date=YYYY-MM-DD
```

Returns available 30-minute appointment slots.

---

## Patients

### Create patient

```http
POST /patients
```

Admin access required.

### List patients

```http
GET /patients
```

Admin access required.

### Get patient

```http
GET /patients/{patient_id}
```

Admin access required.

### Get patient appointments

```http
GET /patients/{patient_id}/appointments
```

Returns upcoming appointments sorted chronologically.

---

## Appointments

### Book appointment

```http
POST /appointments
```

Creates a new appointment after validating the requested slot.

### Cancel appointment

```http
PATCH /appointments/{appointment_id}/cancel
```

Cancels an appointment and records the cancellation reason.

### Reschedule appointment

```http
PATCH /appointments/{appointment_id}/reschedule
```

Moves an appointment to a new validated slot.

---

# 11. Error Handling

The API uses meaningful HTTP status codes for different failure scenarios.

Examples include:

| Status | Meaning                                                     |
| ------ | ----------------------------------------------------------- |
| `200`  | Successful request                                          |
| `201`  | Resource successfully created                               |
| `400`  | Invalid request                                             |
| `401`  | Authentication required/invalid                             |
| `403`  | Insufficient permissions                                    |
| `404`  | Resource not found                                          |
| `409`  | Conflict such as duplicate resource or occupied appointment |
| `422`  | Request validation failure                                  |

Application-level exceptions are centralized where appropriate to avoid repeating large error-handling blocks throughout the routers.

---

# 12. Time and Scheduling Rules

Appointment times are timezone-aware.

The application uses a configurable clinic timezone:

```env
CLINIC_TIMEZONE=Africa/Nairobi
```

The booking rules include:

* 30-minute appointment duration.
* Valid 30-minute boundaries.
* Doctor working-hour boundaries.
* No appointments in the past.
* Minimum one-hour notice before booking.
* No overlapping active appointments.

These rules are shared across booking, availability, and rescheduling to avoid inconsistent behavior.

---

# 13. Database Design and Concurrency

PostgreSQL is used as the system of record.

The database includes:

* Foreign-key relationships.
* Appropriate indexes.
* Appointment status constraints.
* User/profile relationship constraints.
* Database-level protection against overlapping active appointments.

The database-level constraint is particularly important for preventing race-condition-based double bookings.

Application validation provides user-friendly errors, while PostgreSQL provides the final integrity guarantee.

---

# 14. Local Development

## Prerequisites

Install:

* Python 3.12+
* PostgreSQL
* Docker Desktop
* Git

---

## Environment configuration

Copy the example environment file:

```text
.env.example
```

Create a local `.env` file and configure the database connection and application secrets.

At minimum, configure:

```env
CLINIC_DATABASE_URL=postgresql://...
CLINIC_TIMEZONE=Africa/Nairobi
CLINIC_JWT_SECRET=...
```

Secrets should never be committed to the repository.

---

# 15. Running Locally

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run database migrations:

```powershell
alembic upgrade head
```

Seed development data:

```powershell
python -m app.seed
```

Start the API:

```powershell
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

Swagger/OpenAPI:

```text
http://localhost:8000/docs
```

---

# 16. Docker

The project includes Docker and Docker Compose configuration for running the API together with PostgreSQL.

Start the services:

```powershell
docker compose up --build
```

The API should then be available at:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

Stop the services:

```powershell
docker compose down
```

---

# 17. Database Migrations

Alembic manages schema changes.

Apply migrations:

```powershell
alembic upgrade head
```

Create a migration when required:

```powershell
alembic revision --autogenerate -m "describe change"
```

Migrations should be reviewed before applying them to shared or production databases.

---

# 18. Testing

The project uses pytest for automated testing.

Run the complete test suite:

```powershell
python -m pytest -q
```

The test suite covers:

* Appointment booking
* Booking validation
* Double-booking prevention
* Doctor availability
* Cancellation
* Rescheduling
* Patient appointments
* Doctor management
* Patient management
* Authentication
* Authorization
* Ownership rules

Additional checks can be run with:

```powershell
python -m compileall -q app tests
```

and:

```powershell
git diff --check
```

---

# 19. CI/CD

GitHub Actions is used for continuous integration.

The CI pipeline runs the automated test suite for pull requests.

The intended deployment flow is:

```text
Developer
   ↓
Feature branch
   ↓
Pull Request
   ↓
GitHub Actions
   ↓
Tests
   ↓
Code Review
   ↓
Merge into main
   ↓
Render deployment
   ↓
Production API
```

The deployment workflow is configured to deploy changes merged into the designated production branch.

Production secrets and configuration are stored as environment variables rather than in the repository.

---

# 20. Deployment

The application is configured for deployment on Render with Render Postgres. The
root [`render.yaml`](render.yaml) Blueprint defines the web service and its
database. Link the repository to a Render Blueprint, provide the requested
secret during setup, and Render deploys commits on `main` only. Pull-request
preview environments are disabled.

### Production configuration

Production environment variables should include values such as:

```text
CLINIC_DATABASE_URL
CLINIC_TIMEZONE
CLINIC_JWT_SECRET
```

`CLINIC_DATABASE_URL` is supplied from the Blueprint-managed Render Postgres
database. Set `CLINIC_JWT_SECRET` as a Render secret when the Blueprint prompts
for it; do not commit its value. The Blueprint sets the non-secret production
defaults, including `CLINIC_TIMEZONE`, and pins the Python runtime version.

---

# 21. Design Decisions

### PostgreSQL instead of an in-memory or file-based database

PostgreSQL provides reliable transactions, constraints, indexing, and concurrency control suitable for appointment scheduling.

### Database-level double-booking protection

Application-level availability checks alone cannot guarantee correctness under concurrent requests. The database therefore provides the final protection against overlapping appointments.

### Service/repository separation

Business rules are kept in services while database operations are organized in repositories. This keeps routers thin and makes the application easier to test and extend.

### Shared booking validation

Booking, availability, and rescheduling use shared business rules instead of maintaining separate implementations that could eventually disagree.

### JWT authentication

JWT provides a lightweight stateless authentication mechanism suitable for a REST API.

### Role and ownership checks

Authorization is handled independently from authentication. Roles determine broad permissions while ownership checks determine whether a doctor or patient may operate on a specific appointment.

---

# 22. Trade-offs

### JWT vs server-side sessions

JWT was selected because the API is stateless and can be scaled horizontally without maintaining session state.

The trade-off is that token revocation requires additional infrastructure if immediate invalidation becomes necessary.

### Database-level concurrency protection

A database constraint adds complexity compared with a simple availability query, but the additional complexity is justified because appointment integrity is more important than relying solely on application-level checks.

### Layered architecture

The service/repository structure introduces more files than placing all logic in route handlers. The trade-off is intentional: the additional separation improves testability and maintainability as the system grows.

### Current clinic timezone

The application uses a configurable clinic timezone rather than assuming the server's local timezone. This makes scheduling behavior explicit and easier to deploy consistently.

---

# 23. API Documentation

FastAPI automatically generates OpenAPI documentation.

Local Swagger UI:

```text
http://localhost:8000/docs
```

Local ReDoc:

```text
http://localhost:8000/redoc
```

The OpenAPI specification is also available at:

```text
http://localhost:8000/openapi.json
```

---

# 24. Project Structure

```text
Clinic_Booking_API/
├── app/
│   ├── core/
│   ├── database/
│   ├── models/
│   ├── repositories/
│   ├── routers/
│   ├── schemas/
│   ├── services/
│   ├── utils/
│   ├── main.py
│   └── seed.py
├── alembic/
│   └── versions/
├── tests/
├── .github/
│   └── workflows/
├── Dockerfile
├── docker-compose.yml
├── render.yaml
├── requirements.txt
├── .env.example
├── .env.docker.example
├── .gitignore
└── README.md
```

---

# 25. Assessment Alignment

This project addresses the four sections of the take-home assessment:

### Section 1: System Design

The README documents the architecture, data model, booking flow, technical decisions, concurrency strategy, and trade-offs.

### Section 2: API Implementation

The REST API implements appointment booking, availability, cancellation, rescheduling, and patient appointment retrieval, with validation, authentication, authorization, and automated tests.

### Section 3: Deployment & CI/CD

The project includes Docker, GitHub Actions, and Render deployment configuration.

### Section 4: AI Reflection

AI was used as a development tool throughout the project while implementation decisions, testing, validation, and final engineering review remained part of the development process.

## AI Reflection

### 1. What did I use AI for across the four sections?

I used AI primarily as a development assistant throughout the assessment. It helped me explore system design options, structure the FastAPI application, reason about database relationships and constraints, generate implementation ideas, write and improve tests, troubleshoot development issues, and review code for maintainability.

During API development, I used AI to accelerate implementation of endpoints and supporting services while reviewing the resulting code and validating the behavior through automated tests.

For deployment and CI/CD, AI was useful for working through Docker configuration, GitHub Actions workflows, environment configuration, and deployment considerations.

I also used AI during documentation and code review to identify areas that could be simplified, separated into clearer responsibilities, or made easier for another developer to understand.

### 2. An example where AI improved the work

One useful example was the handling of concurrent appointment bookings.

An initial application-level approach could check whether a slot was available before creating the appointment. AI helped identify the concurrency weakness in this approach and led to considering database-level protection in PostgreSQL.

I then incorporated a database constraint alongside application validation. This means the application can provide meaningful validation responses while PostgreSQL provides the final integrity guarantee against overlapping bookings.

This resulted in a stronger design than relying solely on an application-level availability check.

### 3. An example where AI output required refinement

AI-generated implementation suggestions sometimes needed to be adjusted to fit the existing architecture and test behavior.

Rather than treating generated code as final, I validated changes against the existing test suite and the application's business rules. Where a suggestion introduced unnecessary coupling, duplicated validation, or did not fit the existing structure, I refined the implementation before continuing.

This reinforced the importance of treating AI output as a starting point for engineering work rather than as a replacement for testing and review.

### 4. Two decisions made through my own technical judgment

**Database-level protection for appointment conflicts**

I chose to make PostgreSQL responsible for the final protection against overlapping appointments because appointment integrity is a critical requirement. An application-only check would not be sufficient under concurrent requests.

**Separation of business logic from API routes**

I chose to keep routers thin and move business rules into services and database operations into repositories. This adds some structure compared with placing everything in route handlers, but it makes the codebase easier to test, understand, and extend as the clinic grows.

---

# 26. Security Considerations

* Passwords are stored as bcrypt hashes rather than plaintext.
* JWT secrets are provided through environment variables.
* Database credentials are provided through environment variables.
* Production secrets are not stored in source control.
* Role-based access control protects administrative functionality.
* Appointment ownership is enforced at the service layer.
* Database constraints protect appointment integrity.
* Configuration differs between local, Docker, and production environments.

---

# 27. Future Improvements

Possible future extensions include:

* Email/SMS appointment notifications.
* Doctor-specific schedules for different days of the week.
* Holiday and leave management.
* Appointment reminders.
* Pagination for larger datasets.
* Audit logging.
* Refresh tokens and token revocation.
* Administrative reporting.
* Rate limiting.
* More granular permissions.
* Multiple clinic locations.
* Recurring availability schedules.

---

## License

This project was developed as part of a backend developer take-home assessment.
