# Interview Explanation Notes

This document is a study guide to help explain the architecture, design choices, and behavior of the Bulk Certificate Generator API during an engineering interview.

### 1. Why FastAPI?
FastAPI is highly performant, explicitly supports asynchronous programming, and provides automatic OpenAPI (Swagger) documentation. Its seamless integration with Pydantic makes request validation robust and type-safe. It's the modern standard for Python API development.

### 2. Why PostgreSQL?
PostgreSQL is a robust, ACID-compliant relational database ideal for maintaining strong data integrity. It handles concurrent connections gracefully, which is crucial for systems with background workers rapidly updating states. For local development/testing, the codebase seamlessly defaults to SQLite without changing any application logic.

### 3. Why SQLAlchemy?
SQLAlchemy 2.x provides a powerful ORM and a secure query builder that protects against SQL injection. Using `DeclarativeBase` models allows us to map python objects to database rows cleanly. It also abstracts away the differences between PostgreSQL and SQLite, letting us switch dialects purely via configuration.

### 4. Why background processing?
Generating PDFs is a CPU-intensive and I/O-bound task. Generating 1000 certificates sequentially during a standard HTTP request would cause the client to timeout (HTTP timeouts typically occur around 30-60s). Background processing allows the API to acknowledge receipt instantly (`202 Accepted`) and process the heavy workload asynchronously.

### 5. Why not Celery/Redis?
Celery and Redis are excellent for distributed, multi-node enterprise systems. However, they introduce significant infrastructure overhead (managing a message broker and worker clusters). For this specific assignment, FastAPI's built-in `BackgroundTasks` achieves the required asynchronous behavior securely and efficiently within the same process. Adding Celery would unnecessarily violate the "keep it simple and maintainable" constraint unless explicitly required for horizontal scaling.

### 6. How bulk processing works
1. Client POSTs a payload with e.g. 500 recipients.
2. Pydantic validates the entire payload shape.
3. The API creates a single `Job` row and 500 `Certificate` rows (status `PENDING`) in one quick database transaction.
4. The API queues `process_certificate_job(job_id)` in `BackgroundTasks` and returns `202 Accepted`.
5. The background worker queries the 500 pending certificates and iterates through them, generating PDFs one-by-one.

### 7. How job status is tracked
The `Job` table holds counters (`total_count`, `success_count`, `failure_count`) and a `status` Enum. As the background worker finishes each certificate, it atomically increments the success or failure count. The GET `/jobs/{job_id}` endpoint simply reads these counters to calculate real-time `progress_percentage`.

### 8. How individual failures are handled
Inside the worker's processing loop, the PDF generation function is wrapped in a `try...except` block. If a specific recipient causes an exception (e.g. invalid rendering characters):
1. The exception is caught.
2. The specific `Certificate` row is marked as `FAILED` and the `error_message` is saved.
3. The `Job.failure_count` is incremented.
4. **Crucially**, the loop continues gracefully to the next recipient in the list.

### 9. How database transactions are handled
FastAPI handles the API endpoints using a dependency `get_db()` that yields a database session and safely closes it per-request. For the background worker, we use a custom context manager `get_db_session_context()` which yields a fresh Session, commits automatically if successful, rolls back on critical system exceptions, and safely closes the connection preventing connection leaks.

### 10. How certificates are generated
Certificates are generated using the `ReportLab` library by drawing onto a virtual canvas. The system defines a landscape page, draws styled vector borders (navy and gold), applies typography for the header/name, and saves the file to a designated local storage folder (`storage/certificates/{job_id}/`).

### 11. How the API is structured
The codebase follows a standard multi-layer architecture:
- **Routers** (`api/v1/`): Handle HTTP parsing and status codes.
- **Services** (`services/`): Handle business logic, orchestrating between models and PDF generation.
- **Repositories** (`repositories/`): Abstract away complex SQLAlchemy queries.
- **Workers** (`workers/`): Manage background task execution.

### 12. How validation works
Pydantic v2 schemas rigorously check the request. For example, `RecipientSchema` uses `Field` and `@field_validator` to ensure names aren't empty whitespace and emails conform to standard formats (`EmailStr`). 

### 13. How tests work
Pytest uses an isolated SQLite file-based database for tests. The `client` fixture overrides the API's database dependency to inject the test database session. Tests cover validation edge cases, ensure endpoints return correct statuses, invoke the background task logic to prove fault-isolation works (using `unittest.mock.patch` to intercept PDF generation and simulate intentional failures for specific recipients), and assert that the ReportLab logic actually generates physical files.

### 14. What happens if 1 certificate out of 100 fails?
The 1 failed certificate is marked as `FAILED` in the database, while the remaining 99 generate successfully. The overall job status transitions to `COMPLETED_WITH_ERRORS`. The client can fetch the job status to see exactly which recipient failed and why, and can download a ZIP of the 99 successful PDFs.

### 15. What would you change if the system had 1 million recipients?
If we had 1 million recipients:
- We could not use a simple background thread; we'd need **Celery + Redis/RabbitMQ** to distribute the workload across multiple worker servers.
- The single bulk insert of 1,000,000 rows would lock the database; we'd need to **chunk inserts** or use streaming endpoints.
- Local file storage would exhaust server disk space; we'd need to stream PDF files directly to an object store like **AWS S3**.
- A single ZIP file of 1 million PDFs is impossible to download via HTTP; we would need to generate signed S3 URLs or provide batch retrieval options.

### 16. What are the current limitations?
1. Storage is local. If the server is restarted or deployed in a stateless container (Docker), files might be lost unless a volume is mounted.
2. Synchronous PDF rendering in a single worker thread per job. (Can be slow for very large batches, e.g. 500+).

### 17. How would you scale the system in production?
- Migrate local file storage to **Cloud Object Storage (AWS S3 / GCS)**.
- Migrate FastAPI `BackgroundTasks` to **Celery + Redis** to allow distributed horizontal scaling of worker nodes.
- Containerize the application using **Docker** and deploy it via **Kubernetes** with autoscaling based on the Celery queue length.
