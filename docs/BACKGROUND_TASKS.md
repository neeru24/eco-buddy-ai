# Background Task Reliability

EcoBuddy AI uses `background_tasks.py` for long-running operations such as OCR,
AI-provider calls, report generation, and large imports.

## Task states

```text
pending
running
retry_scheduled
completed
failed
dead_letter
```

`failed` is used for a permanent or non-retryable error. `dead_letter` is used
when a retryable operation reaches its maximum attempt count.

## Retryable exceptions

Retries are opt-in. Raise `RetryableTaskError` for failures such as temporary
network unavailability or provider timeouts.

```python
from background_tasks import RetryableTaskError

def call_provider():
    try:
        ...
    except TimeoutError as exc:
        raise RetryableTaskError("provider timeout") from exc
```

Invalid input, unsupported file formats, and programming errors should remain
non-retryable. They fail immediately.

## Submitting with retries

```python
from background_tasks import (
    BackgroundTaskStore,
    RetryPolicy,
    RetryableTaskError,
    submit_background_task,
)

task = submit_background_task(
    "generate-report-42",
    generate_report,
    assessment_id=42,
    task_name="Generate report",
    task_type="pdf_report",
    retry_policy=RetryPolicy(
        max_attempts=4,
        base_delay_seconds=1,
        max_delay_seconds=20,
    ),
    retryable_exceptions=(RetryableTaskError,),
    idempotency_key="pdf-report:assessment:42",
    store=BackgroundTaskStore(),
)
```

The delay after each failed attempt is exponential and capped:

```text
1 second
2 seconds
4 seconds
8 seconds
... up to max_delay_seconds
```

## Idempotency

Use a stable key for operations that must not execute twice.

Good examples:

```text
email:user-12:weekly-summary:2026-08-03
pdf-report:assessment:42
import:user-8:file-sha256
```

The SQLite store enforces uniqueness for non-null idempotency keys.

Do not include passwords, tokens, or full sensitive payloads in keys.

## Dead-letter operations

List dead-letter tasks:

```python
from background_tasks import list_dead_letter_tasks

tasks = list_dead_letter_tasks(limit=50)
```

Reset a dead-letter record for an operator-approved retry:

```python
from background_tasks import retry_dead_letter_task

retry_dead_letter_task(task_id)
```

This resets metadata to `pending` but does not execute an arbitrary callable.
The caller must map the persisted `task_type` to a trusted registered handler
and submit it explicitly.

## Error safety

Stored errors are:

- converted to one line;
- truncated to 500 characters;
- scrubbed for common API-key, token, password, secret, and bearer patterns.

Do not put complete uploaded documents or sensitive provider responses in
exception messages.

## Persistence

Migration v9 creates:

```text
background_task_jobs
```

The table records task ID, key, type, state, attempts, retry limit, safe error
summary, next retry time, idempotency key, and lifecycle timestamps.

## Testing

```powershell
python -m pytest test_background_tasks.py -v
python -m pytest test_background_task_retries.py -v
```

The retry tests use a fake clock and fake sleeper. They do not wait in real
time.
