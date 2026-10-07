# Bulk Certificate Generator API

A production-ready asynchronous API for generating bulk PDF certificates securely and efficiently.

## 🚀 Features
- **Bulk Certificate Generation**: Process up to 1000 certificates per request asynchronously.
- **Robust Failure Isolation**: If one certificate fails (e.g. invalid data), remaining recipients continue generating successfully.
- **Real-Time Job Tracking**: Fetch precise completion progress, success counts, failure counts, and detailed error messages.
- **Premium PDF Template**: Dynamically generated certificates using ReportLab, featuring rich typography, multi-layered borders, and decorative seals.
- **Downloadable Archives**: Download all successfully generated certificates in a single ZIP file.
- **SQLite / PostgreSQL Dual Support**: Configured to run on SQLite instantly for easy local development, or switch to PostgreSQL using a simple connection string.

## 🛠️ Technology Stack
- **Framework**: FastAPI (Python 3.12+)
- **Database**: PostgreSQL (Primary) / SQLite (Fallback/Testing)
- **ORM**: SQLAlchemy 2.x
- **Validation**: Pydantic v2
- **Migrations**: Alembic
- **PDF Generation**: ReportLab
- **Testing**: Pytest

## 🏗️ Architecture & Background Processing
To avoid HTTP request timeouts on bulk jobs, the API leverages **FastAPI BackgroundTasks**.
When a bulk request is received, the API validates the payload, initializes a `Job` and `Pending` certificates in the database transactionally, and returns `202 Accepted` immediately.
A background worker then claims the job, generating PDFs one-by-one. The worker maintains real-time DB state so clients can poll for progress.

## 📂 Project Structure
```
app/
├── api/             # API Router definitions (v1)
├── core/            # Configuration, Exception Handlers, DB setup
├── models/          # SQLAlchemy 2.x declarative models
├── repositories/    # Clean DB query abstractions
├── schemas/         # Pydantic v2 Validation schemas
├── services/        # Core business logic (Jobs, Certificates, PDFGen)
└── workers/         # Background tasks execution layer
tests/               # Pytest suite
alembic/             # Migration configurations
```

## ⚙️ Setup Requirements
- Python 3.12 or 3.13
- PostgreSQL (Optional, runs on SQLite by default if unconfigured)

## 🔧 Installation & Running Locally

1. **Clone the repository and enter directory**:
```bash
git clone <url>
cd "BULK CERTIFICATE GENERATOR API"
```

2. **Install Dependencies**:
```bash
pip install -r requirements.txt
# Additionally, ensure pydantic[email] is installed if not already:
pip install "pydantic[email]"
```

3. **Environment Setup**:
Copy `.env.example` to `.env`.
```bash
cp .env.example .env
```
*(By default, `.env` is configured to use SQLite: `sqlite:///./certificate_generator.db`)*

4. **Run Database Migrations** (Creates tables):
```bash
alembic upgrade head
```

5. **Start the FastAPI Application**:
```bash
uvicorn app.main:app --reload
```
The API is now running at `http://127.0.0.1:8000`.

## 📚 API Endpoints

Explore the interactive Swagger documentation at: **`http://127.0.0.1:8000/docs`**

### 1. Create Job (`POST /api/v1/jobs`)
Creates a bulk generation job and starts background processing.
**Request**:
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/jobs' \
  -H 'Content-Type: application/json' \
  -d '{
  "event_name": "Python Workshop",
  "event_date": "2026-10-10",
  "organization_name": "Example Organization",
  "recipients": [
    {"name": "Snehal Patil", "email": "snehal@example.com"},
    {"name": "Rahul Sharma", "email": "rahul@example.com"}
  ]
}'
```
**Response (202 Accepted)**:
```json
{
  "job_id": "365c7b0c-e590-45f1-8d93-0c194b7e9384",
  "status": "queued",
  "total": 2
}
```

### 2. Check Job Status (`GET /api/v1/jobs/{job_id}`)
**Response**:
```json
{
  "job_id": "365c7b0c-e590-45f1-8d93-0c194b7e9384",
  "status": "completed",
  "total": 2,
  "successful": 2,
  "failed": 0,
  "progress_percentage": 100.0,
  "failures": [],
  "created_at": "2026-10-07T12:00:00Z"
}
```

### 3. Retrieve Certificate Files
- Single PDF Download: `GET /api/v1/certificates/{certificate_id}`
- Bulk ZIP Archive: `GET /api/v1/jobs/{job_id}/download`

## 🧪 Testing
Run the complete Pytest suite (tests run against an isolated SQLite test database):
```bash
pytest -v
```

## 🤔 Important Design Decisions & Limitations
- **Fault Isolation**: Handled via `try...except` at the individual certificate rendering loop level inside the worker. A failure is marked against that specific `Certificate` DB row, and the loop seamlessly proceeds to the next recipient.
- **Background Tasks over Celery**: Celery requires a message broker (Redis/RabbitMQ). For an internship assignment with strict "simple/maintainable" constraints, FastAPI's built-in `BackgroundTasks` executing within the ASGI event loop is infinitely simpler to deploy while fully satisfying the asynchronous bulk processing requirement.
- **File System Storage**: Certificates are stored locally in the `storage/` directory. 
- **Limitation - Horizontal Scaling**: The current `BackgroundTasks` approach runs locally on the app server instance. If deployed across a multi-node cluster (e.g. Kubernetes with 10 replicas), we would need a proper distributed queue (Celery + Redis) and shared block storage (AWS S3) rather than local file storage.
