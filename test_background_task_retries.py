"""Tests for background task retry and dead-letter handling."""

from __future__ import annotations

import sqlite3

from background_tasks import (
    BackgroundTask,
    BackgroundTaskStore,
    PermanentTaskError,
    RetryableTaskError,
    RetryPolicy,
    TaskStatus,
    execute_task_with_retry,
    list_dead_letter_tasks,
    retry_dead_letter_task,
    sanitize_error_summary,
    submit_background_task,
    clear_background_task,
)


class FakeClock:
    def __init__(self, start=1_700_000_000.0):
        self.current = start
        self.delays = []

    def time(self):
        return self.current

    def sleep(self, delay):
        self.delays.append(delay)
        self.current += delay


def make_task(clock, max_attempts=3):
    return BackgroundTask(
        task_id="task-1",
        task_key="task-key",
        name="Test Task",
        task_type="test",
        retry_policy=RetryPolicy(
            max_attempts=max_attempts,
            base_delay_seconds=1,
            max_delay_seconds=5,
        ),
        clock=clock.time,
    )


def test_retry_policy_uses_bounded_exponential_backoff():
    policy = RetryPolicy(
        max_attempts=5,
        base_delay_seconds=2,
        max_delay_seconds=5,
    )

    assert policy.delay_for_attempt(1) == 2
    assert policy.delay_for_attempt(2) == 4
    assert policy.delay_for_attempt(3) == 5
    assert policy.delay_for_attempt(4) == 5


def test_temporary_failure_retries_then_completes():
    clock = FakeClock()
    task = make_task(clock)
    attempts = 0

    def operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RetryableTaskError("provider temporarily unavailable")
        return "success"

    result = execute_task_with_retry(
        task,
        operation,
        sleep_fn=clock.sleep,
    )

    assert result == "success"
    assert task.status == TaskStatus.COMPLETED
    assert task.attempt_count == 3
    assert clock.delays == [1, 2]


def test_non_retryable_failure_stops_immediately():
    clock = FakeClock()
    task = make_task(clock)
    attempts = 0

    def operation():
        nonlocal attempts
        attempts += 1
        raise PermanentTaskError("invalid document")

    result = execute_task_with_retry(
        task,
        operation,
        sleep_fn=clock.sleep,
    )

    assert result is None
    assert attempts == 1
    assert task.status == TaskStatus.FAILED
    assert task.attempt_count == 1
    assert clock.delays == []


def test_unlisted_exception_is_non_retryable():
    clock = FakeClock()
    task = make_task(clock)
    attempts = 0

    def operation():
        nonlocal attempts
        attempts += 1
        raise ValueError("bad input")

    execute_task_with_retry(
        task,
        operation,
        sleep_fn=clock.sleep,
    )

    assert attempts == 1
    assert task.status == TaskStatus.FAILED


def test_exhausted_retries_move_task_to_dead_letter():
    clock = FakeClock()
    task = make_task(clock, max_attempts=3)

    def operation():
        raise RetryableTaskError("network timeout")

    execute_task_with_retry(
        task,
        operation,
        sleep_fn=clock.sleep,
    )

    assert task.status == TaskStatus.DEAD_LETTER
    assert task.attempt_count == 3
    assert clock.delays == [1, 2]
    assert "network timeout" in task.error


def test_error_summary_redacts_secrets_and_is_truncated():
    summary = sanitize_error_summary(
        "Authorization: Bearer abc.def.ghi "
        "api_key=super-secret password=hunter2 "
        + ("x" * 800),
        max_length=120,
    )

    assert "abc.def.ghi" not in summary
    assert "super-secret" not in summary
    assert "hunter2" not in summary
    assert "[REDACTED]" in summary
    assert len(summary) <= 120


def test_store_persists_dead_letter_and_lists_it(tmp_path):
    store = BackgroundTaskStore(str(tmp_path / "tasks.db"))
    clock = FakeClock()
    task = make_task(clock, max_attempts=2)

    assert store.create(task)

    def operation():
        raise RetryableTaskError("temporary provider error")

    execute_task_with_retry(
        task,
        operation,
        store=store,
        sleep_fn=clock.sleep,
    )

    rows = list_dead_letter_tasks(store=store)
    assert len(rows) == 1
    assert rows[0]["task_id"] == "task-1"
    assert rows[0]["status"] == TaskStatus.DEAD_LETTER
    assert rows[0]["attempt_count"] == 2


def test_manual_retry_resets_dead_letter_metadata(tmp_path):
    store = BackgroundTaskStore(str(tmp_path / "tasks.db"))
    clock = FakeClock()
    task = make_task(clock, max_attempts=1)
    assert store.create(task)

    execute_task_with_retry(
        task,
        lambda: (_ for _ in ()).throw(
            RetryableTaskError("timeout")
        ),
        store=store,
        sleep_fn=clock.sleep,
    )

    assert retry_dead_letter_task(
        task.task_id,
        store=store,
    )

    with sqlite3.connect(store.database_path) as connection:
        row = connection.execute(
            """
            SELECT status, attempt_count, last_error, completed_at
            FROM background_task_jobs
            WHERE task_id = ?
            """,
            (task.task_id,),
        ).fetchone()

    assert row == (TaskStatus.PENDING, 0, None, None)


def test_manual_retry_rejects_non_dead_letter_task(tmp_path):
    store = BackgroundTaskStore(str(tmp_path / "tasks.db"))
    task = BackgroundTask("task-2", "Pending")
    assert store.create(task)

    assert not retry_dead_letter_task(
        task.task_id,
        store=store,
    )


def test_idempotency_key_prevents_duplicate_execution(tmp_path):
    store = BackgroundTaskStore(str(tmp_path / "tasks.db"))
    executions = 0

    def operation():
        nonlocal executions
        executions += 1
        return "done"

    first = submit_background_task(
        "idempotent-one",
        operation,
        idempotency_key="report:user-7:assessment-3",
        store=store,
    )
    first.future.result(timeout=2)

    second = submit_background_task(
        "idempotent-two",
        operation,
        idempotency_key="report:user-7:assessment-3",
        store=store,
    )

    assert second.task_id == first.task_id
    assert executions == 1

    clear_background_task("idempotent-one")
    clear_background_task("idempotent-two")


def test_different_idempotency_keys_execute_independently(tmp_path):
    store = BackgroundTaskStore(str(tmp_path / "tasks.db"))
    executions = []

    first = submit_background_task(
        "independent-one",
        lambda: executions.append("one"),
        idempotency_key="one",
        store=store,
    )
    second = submit_background_task(
        "independent-two",
        lambda: executions.append("two"),
        idempotency_key="two",
        store=store,
    )

    first.future.result(timeout=2)
    second.future.result(timeout=2)

    assert sorted(executions) == ["one", "two"]

    clear_background_task("independent-one")
    clear_background_task("independent-two")
